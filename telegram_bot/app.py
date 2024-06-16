import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.absolute()))


import json
import requests
# from functools import wraps
from PIL import Image
import tempfile
import telebot
from telebot import types
from io import BytesIO
import requests
import emoji
import base64
import hashlib
from datetime import datetime

import io


from config import Config

cfg = Config.load()
bot = telebot.TeleBot(cfg.api_token)


periodru2e = {
    'месяц': "month",
    'квартал': "quarter",
    'год': "year"
}

md5_hash = hashlib.md5()

# Placeholder functions for API calls
def search_product_api(product_name):
    # Return top 3 relevant products
    response = requests.get(
		url='http://hack_statistics_server:5000/search_contracts', 
		data=json.dumps({'text': product_name, 'k': 100}),
	)
    rows = json.loads(response.content)
    response_list = []
    seen = set([])
    for row in rows:
        if not row['spgz_name'] in seen and len(response_list) < 5 and row['spgz_name']:
            response_list.append({
                'spgz_name': row['spgz_name']
                })
            seen.add(row['spgz_name'])
    return response_list

def get_restrictions_api(product_name):
    response = requests.get(
		url='http://hack_statistics_server:5000/search_restrictions', 
		data=json.dumps({'text': product_name, "k": 1}),
	)
    return [d['restrictions'] for d in json.loads(response.content)]

def get_forecast_period_api(product_name, period):
    images = {}
    response = requests.get(
		url='http://hack_statistics_server:5000/grafic_dynamics_financial_quantity', 
		data=json.dumps({'spgz_name': product_name, 'date_grain': 'month'}),
	)
    if response.status_code == 200:
        val = json.loads(response.content)['img']
        try:
            images['grafic_dynamics_financial_quantity'] = Image.open(io.BytesIO(base64.b64decode(val.encode())))
        except:
            pass
    response = requests.get(
		url='http://hack_statistics_server:5000/grafic_dynamics_financial_price', 
		data=json.dumps({'spgz_name': product_name, 'date_grain': 'month'}),
	)
    if response.status_code == 200:
        val = json.loads(response.content)['img']
        try:
            images['grafic_dynamics_financial_price'] = Image.open(io.BytesIO(base64.b64decode(val.encode())))
        except:
            pass
    response = requests.get(
		url='http://hack_statistics_server:5000/grafic_dynamics_financial_prognoze', 
		data=json.dumps({'spgz_name': product_name, 'date_grain': periodru2e[period]}),
	)
    if response.text:
        val = json.loads(response.content)['img']
        try:
            images['grafic_dynamics_financial_prognoze'] = Image.open(io.BytesIO(base64.b64decode(val.encode())))
        except:
            pass
    response = requests.get(
		url='http://hack_statistics_server:5000/grafic_dynamics_contracts_prognoze', 
		data=json.dumps({'spgz_name': product_name, 'date_grain': periodru2e[period]}),
	)
    if response.text:
        val = json.loads(response.content)['img']
        try:
            images['grafic_dynamics_contracts_prognoze'] = Image.open(io.BytesIO(base64.b64decode(val.encode())))
        except:
            pass

    response = requests.get(
		url='http://hack_statistics_server:5000/prognoze_financial_quarter', 
		data=json.dumps({'spgz_name': product_name, 'date_grain': periodru2e[period]}),
	)
    financial = json.loads(response.content)
    financial_str = "\n".join(f"{financial_en2ru[k]}: {v}" for k, v in financial.items())
    response = requests.get(
		url='http://hack_statistics_server:5000/prognoze_contracts', 
		data=json.dumps({'spgz_name': product_name, 'date_grain': periodru2e[period]}),
	)
    contracts = json.loads(response.content)
    contracts_str = ''
    for d in contracts:
        contracts_str_lst = []
        for k, v in d.items():
            
            if k in ['contract_date']:
                date_time_obj = datetime.strptime(v, '%Y-%m-%d %H:%M:%S')
                contracts_str_lst += [f"{contracts_en2ru[k]}: {date_time_obj.strftime('%Y-%m-%d')}"]
            else:
                contracts_str_lst += [f"{contracts_en2ru[k]}: {v}"]
            
        contracts_str += "\n".join(contracts_str_lst) + "\n"*2
    return {
         "forecast":  f"""Прогноз по финансовым данным\n{financial_str}\n
Прогноз по контрактам\n{contracts_str}\n
Для полной полной аналитики перейдите по ссылке: http://5.35.7.187:8088/superset/dashboard/4/?native_filters_key=S0QB-jpejvRie2R4JIK9qpwTyNwhWEESdZ9oWMo4T7BVDB6FFRIEKNygtHn6tJIP""",
         "images": images
	}


# Начальная структура JSON
data = {
    "id": None,
    "lotEntityId": None,
    "CustomerId": None,
    "rows": [
        {
            "DeliverySchedule": {
                "dates": {
                    "end_date": "",
                    "start_date": ""
                },
                "deliveryAmount": None,
                "deliveryConditions": "",
                "year": None
            },
            "address": {
                "gar_id": "",
                "text": ""
            },
            "entityId": None,
            "id": None,
            "nmc": None,
            "okei_code": "",
            "purchaseAmount": None,
            "spgzCharacteristics": [
                {
                    "characteristicName": " ",
                    "characteristicSpgzEnums": [
                        {  "value": " "
                        }
                    ],
                    "conditionTypeId": "" ,
                    "kpgzCharacteristicId":""  ,
                    "okei_id": "" ,
                    "selectType": "" ,
                    "typeId": "" ,
                    "value1": "" ,
                    "value2": "" 
                },
            ]
           
        }
    ]
}


financial_en2ru = {
  'start_quarter': 'Начало прогноза',
  'end_quarter': 'Конец прогноза',
  'spgz_name': 'СПГЗ',
  'saldo_start_debit_quantity': 'Кол-во товара',
  'saldo_start_debit_price': 'Стоимость товара',
  'turnovers_debit_quantity': 'Кол-во закупленного товара',
  'turnovers_debit_price': 'Цена закупленного товара',
  'turnovers_credit_quantity': 'Кол-во потроченного товара',
  'turnovers_credit_price': 'Цена потраченного товара',
  'saldo_end_debit_quantity': 'Кол-во оставшегося товара',
  'saldo_end_debit_price': 'Цена оставшегося товара',
  'regularity': 'Регулярность',
}
contracts_en2ru = {
  'contract_date': 'Дата заключения контракта',
  'contract_price': 'Цена контракта',
  'next_contract_delta': 'Дельта следующего контракта',
  'regularity': 'Регулярность контрактов',
}

current_search = {}
user_sessions = {}
current_data = {}


# Main menu handler
@bot.message_handler(commands=['start'])
def send_welcome(message):
    current_search.pop(message.chat.id, None)  # Clear the search history for the user
    user_sessions.pop(message.chat.id, None)  # Clear the session for the user
    current_data.pop(message.chat.id, None)
    markup = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
    itembtn1 = types.KeyboardButton('Авторизоваться 🔐')
    markup.add(itembtn1)
    bot.send_message(message.chat.id, "Добро пожаловать! Пожалуйста, авторизуйтесь для продолжения.", reply_markup=markup)
    bot.register_next_step_handler(message, request_login)

def request_login(message):
    message = bot.send_message(message.chat.id, "Введите логин:")
    bot.register_next_step_handler(message, request_password)

def request_password(message):
    login = message.text.strip()
    response = requests.get(
		url='http://hack_statistics_server:5000/user', 
		data=json.dumps({'username': login}),
	)

    if json.loads(response.content) != {"result": "User not found"}:
        user_sessions[message.chat.id] = {'login': login}
        current_data[message.chat.id] = {}
        message = bot.send_message(message.chat.id, "Введите пароль:")
        bot.register_next_step_handler(message, process_login)
    else:
        bot.send_message(message.chat.id, "Логин не найден. Попробуйте снова.")
        send_welcome(message)

def process_login(message):
    password = message.text.strip()
    login = user_sessions[message.chat.id]['login']

    response = requests.get(
		url='http://hack_statistics_server:5000/user', 
		data=json.dumps({'username': login}),
	)
    user_data = json.loads(response.content)
    my_password_bytes = password.encode('utf-8')
    md5_hash = hashlib.md5()
    md5_hash.update(my_password_bytes)

    if user_data['password'] == md5_hash.hexdigest():
        user_sessions[message.chat.id]['permission_admin'] = int(user_data['permission_admin'])
        send_main_menu(message)
    else:
        bot.send_message(message.chat.id, "Неправильный пароль. Попробуйте снова.")
        send_welcome(message)

def send_main_menu(message):
    current_search.pop(message.chat.id, None)
    username = user_sessions[message.chat.id]['login']
    current_data[message.chat.id] = {}
    response = requests.get(
		url='http://hack_statistics_server:5000/user', 
		data=json.dumps({'username': username}),
	)
    user_data = json.loads(response.content)
    permission_admin = int(user_data['permission_admin'])

    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    itembtn1 = types.KeyboardButton('Поиск товара 📦')
    markup.add(itembtn1)
    if int(user_data['permission_forecast']):
        markup.add(types.KeyboardButton('Просмотр остатков и прогноз 📊'))
    if int(user_data['permission_json']):
        markup.add(types.KeyboardButton('Проведение закупки и создание JSON 🛒'))
    
    if permission_admin:
        itembtn4 = types.KeyboardButton('Управление пользователями 👥')
        markup.add(itembtn4)
    bot.send_message(message.chat.id, "Выберите действие из кнопок ниже:", reply_markup=markup)



# Handlers for each option
@bot.message_handler(func=lambda message: emoji.replace_emoji(message.text.lower(), replace='').strip() in \
    ["поиск товара", "поиск", "товар", "найти", "найти товар"])
def search_product(message):
    markup = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
    markup.add(types.KeyboardButton('Назад 🔙'))
    message = bot.send_message(message.chat.id, """Введите название товара 📦:
Если выбранный вариант не очень точен, вы можете потом вручную его скорректировать""", reply_markup=markup)
    bot.register_next_step_handler(message, process_search_product)

def process_search_product(message, results=None):
    text = emoji.replace_emoji(message.text.lower(), replace='').strip()
    if text in ['назад', 'начало']:
        send_main_menu(message)
    else:  
        product_name = text
        if not results:
            results = search_product_api(product_name)
        
        if results:
            markup = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
            bot.send_message(message.chat.id, "\n".join([f"📌{i+1}. {r['spgz_name']}" for i, r in enumerate(results)]))
            for i in range(len(results)):
                markup.add(types.KeyboardButton(f"📌 {str(i+1)}"))

            markup.add(types.KeyboardButton('Ни один из этих товаров'))
            markup.add(types.KeyboardButton('Задать товар вручную ✏️'))
            markup.add(types.KeyboardButton('Назад 🔙'))
            bot.send_message(message.chat.id, """Наиболее релевантные товары:
Выберите число от 1 до 5, чтобы определить подходящий""", reply_markup=markup)
            bot.register_next_step_handler(message, handle_search_selection, results)
        else:
            bot.send_message(message.chat.id, "Релевантных товаров не найдено. Пожалуйста, проверьте написание.")
            send_main_menu(message)

def handle_search_selection(message, results):
    text = emoji.replace_emoji(message.text.lower(), replace='').strip()
    if text == 'ни один из этих товаров':
        message = bot.send_message(message.chat.id, """Введите название товара 📦.\n
Если выбранный вариант не очень точен, вы можете потом вручную его скорректировать""")
        bot.register_next_step_handler(message, process_search_product)
    elif text in ['назад', 'начало'] :
        send_main_menu(message)
    elif str.isdigit(text) and 1 <= int(text) <= len(results):
        selected_product = results[int(text)-1]['spgz_name']
        current_search[message.chat.id] = selected_product
        username = user_sessions[message.chat.id]['login']
        response = requests.get(
            url='http://hack_statistics_server:5000/user', 
            data=json.dumps({'username': username}),
        )
        user_data = json.loads(response.content)
        markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
        if int(user_data['permission_forecast']):
            markup.add(types.KeyboardButton('Просмотр остатков и прогноз 📊'))
        if int(user_data['permission_json']):
            markup.add(types.KeyboardButton('Проведение закупки и создание JSON 🛒'))
        markup.add(types.KeyboardButton('Посмотреть ограничения 📊'))
        markup.add(types.KeyboardButton('Назад 🔙'))
        bot.send_message(message.chat.id, f"Вы выбрали {selected_product}. Что дальше?", reply_markup=markup)
        bot.register_next_step_handler(message, handle_post_search_actions)
    else:
        process_search_product(message, results)

def handle_post_search_actions(message):
    text = emoji.replace_emoji(message.text.lower(), replace='').strip()
    if text == 'просмотр остатков и прогноз':
        view_stock_and_forecast(message)
    elif text == 'посмотреть ограничения':
        view_restrictions(message)
    elif text == 'проведение закупки и создание json':
        
        initiate_purchase_and_create_json(message)

    elif text in ['назад', 'начало']:
        send_main_menu(message)
    else:
        send_main_menu(message)

def view_restrictions(message):
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    markup.add(types.KeyboardButton('Назад 🔙'))
    restrictions = get_restrictions_api(current_search[message.chat.id])
    if not restrictions:
        restictions_str = 'Ограничения небыли найдены'
    else:
        restictions_str = restrictions[0]
    # for d in restictions:
    #     restictions_str += "\n".join(f"{k}: {v}" for k, v in d.items())
    #     restictions_str += "\n"*2
    bot.send_message(message.chat.id, restictions_str, reply_markup=markup)
    send_main_menu(message)
    

def edit_selected_product(message):
    

    new_product_name = message.text
    current_search[message.chat.id] = new_product_name
    login = user_sessions[message.chat.id]['login']
    response = requests.get(
            url='http://hack_statistics_server:5000/user', 
            data=json.dumps({'username': login}),
        )
    user_data = json.loads(response.content)
    bot.send_message(message.chat.id, f"Товар изменён на {new_product_name}.")
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    if int(user_data['permission_forecast']):
            markup.add(types.KeyboardButton('Просмотр остатков и прогноз 📊'))
    if int(user_data['permission_json']):
        markup.add(types.KeyboardButton('Проведение закупки и создание JSON 🛒'))
    markup.add(types.KeyboardButton('Назад 🔙'))
    bot.send_message(message.chat.id, "Выберите действие 🔽:", reply_markup=markup)
    bot.register_next_step_handler(message, handle_post_search_actions)

        

@bot.message_handler(func=lambda message: emoji.replace_emoji(message.text.lower(), replace='').strip() \
    in ["просмотр остатков и прогноз", "остатки", "прогноз"])
def view_stock_and_forecast(message):
    if message.chat.id in current_search:
        product_name = current_search[message.chat.id]
        process_view_stock_and_forecast(message, product_name)
    else:
        markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
        markup.add(types.KeyboardButton('Поиск товара 📦'))
        markup.add(types.KeyboardButton('Назад 🔙'))
        bot.send_message(message.chat.id, "Выберите действие 🔽:", reply_markup=markup)
        bot.register_next_step_handler(message, handle_stock_or_forecast_selection)

def handle_stock_or_forecast_selection(message):
    text = emoji.replace_emoji(message.text.lower(), replace='').strip()

    if text in ['поиск товара', 'поиск', 'товар', 'найти', 'найти товар']:
        search_product(message)
    elif text in ['назад', 'начало']:
        send_main_menu(message)
    else:
        handle_unrecognized(message)

def process_view_stock_and_forecast(message, product_name=None):
    if not product_name:
        product_name = message.text
    current_search[message.chat.id] = product_name
    bot.send_message(message.chat.id, f"Вы выбрали {product_name}")
    markup = types.ReplyKeyboardMarkup(row_width=3, resize_keyboard=True)
    markup.add(types.KeyboardButton('Месяц 📅'), types.KeyboardButton('Квартал 📅📅'), types.KeyboardButton('Год 📅📅📅'))
    markup.add(types.KeyboardButton('Назад 🔙'))
    bot.send_message(message.chat.id, "На какой период 📅 вас интересует прогноз?", reply_markup=markup)
    bot.register_next_step_handler(message, handle_forecast_period, product_name)


def handle_forecast_period(message, product_name):
    text = emoji.replace_emoji(message.text.lower(), replace='').strip()
    if text in ['назад', 'начало']:
        send_main_menu(message)
    elif text in ['месяц', 'квартал', 'год']:
        period = text
        data = get_forecast_period_api(product_name, period)
        forecast_data = data['forecast']
        images = data['images']
        login = user_sessions[message.chat.id]['login']
        bot.send_message(message.chat.id, f"Остатки на складе")
        if 'grafic_dynamics_financial_quantity' in images:
            bot.send_photo(message.chat.id, images['grafic_dynamics_financial_quantity'])
        if 'grafic_dynamics_financial_price' in images:
            bot.send_photo(message.chat.id, images['grafic_dynamics_financial_price'])
        bot.send_message(message.chat.id, f"Прогноз на начало {period}: {forecast_data}")
        if 'grafic_dynamics_financial_prognoze' in images:
            bot.send_photo(message.chat.id, images['grafic_dynamics_financial_prognoze'])
        if 'grafic_dynamics_contracts_prognoze' in images:
            bot.send_photo(message.chat.id, images['grafic_dynamics_contracts_prognoze'])
        markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)

        response = requests.get(
            url='http://hack_statistics_server:5000/user', 
            data=json.dumps({'username': login}),
        )
        user_data = json.loads(response.content)

        if int(user_data['permission_json']):
            markup.add(types.KeyboardButton('Проведение закупки и создание JSON 🛒'))
        markup.add(types.KeyboardButton('Выбрать другой интервал 📅'))
        markup.add(types.KeyboardButton('Назад 🔙'))
        bot.send_message(message.chat.id, "Теперь Вы можете провести закупку 🛍️. ", reply_markup=markup)
        bot.register_next_step_handler(message, handle_post_forecast_actions, product_name)


    else:
        bot.send_message(message.chat.id, "Пожалуйста, выберите правильный период: 'Месяц', 'Квартал' или 'Год'.")
        bot.register_next_step_handler(message, handle_forecast_period, product_name)

def handle_post_forecast_actions(message, product_name):
    text = emoji.replace_emoji(message.text.lower(), replace='').strip()
    if text in ['назад', 'начало']:
        send_main_menu(message)
    elif text in ['проведение закупки и создание json']:
        markup = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
        markup.add(types.KeyboardButton('Назад 🔙'))
        message = bot.send_message(message.chat.id, "Процедура закупки начата 🛍️.", reply_markup=markup)
        
        initiate_purchase_and_create_json(message, product_name)
    elif text in ['выбрать другой интервал']:
        process_view_stock_and_forecast(message, product_name)
    else:
        handle_unrecognized(message)


def send_final_json(message):
    try:
        search = current_search[message.chat.id]
        final_json = {
            "id": '1',
            "lotEntityId": '1',
            "CustomerId": '1',
            "rows": [
                {
                    "DeliverySchedule": {
                        "dates": {
                            "end_date":  "",
                            "start_date":  ""
                        },
                        "deliveryAmount": "",
                        "deliveryConditions":  "",
                        "year":  ""
                    },
                    "address": {
                        "gar_id": '1',
                        "text": '1'
                    },
                    "entityId": "",
                    "id":  "",
                    "nmc": '12345',
                    "okei_code":  "",
                    "purchaseAmount":  "",
                    "spgzCharacteristics": [
                    {
                        "characteristicName": search,
                        "characteristicSpgzEnums": [
                            {  "value": " "
                            }
                        ],
                        "conditionTypeId": "" ,
                        "kpgzCharacteristicId":""  ,
                        "okei_id": "" ,
                        "selectType": "" ,
                        "typeId": "" ,
                        "value1": "" ,
                        "value2": "" 
                    },
                ]
                }
            ]
        }
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file.write(json.dumps(final_json, ensure_ascii=False, indent=4).encode('utf-8'))
            temp_file.close()
            bot.send_document(message.chat.id, open(temp_file.name, 'rb'), caption="Финальный JSON:")
        send_main_menu(message)

    except Exception as e:
        bot.reply_to(message, f"Произошла ошибка: {e}")

# Handlers for purchase initiation and JSON creation
@bot.message_handler(func=lambda message: emoji.replace_emoji(message.text.lower(), replace='').strip() in \
    ["проведение закупки и создание json", "закупка"])
def initiate_purchase_and_create_json(message, product_name=None):
    if not product_name and message.chat.id in current_search:
        product_name = current_search[message.chat.id]
    if product_name:
        # Simulate purchase process
        message = bot.send_message(message.chat.id, "Формируем Json? Да - для продолжить.")
        bot.register_next_step_handler(message, send_final_json)
        
    else:
        markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
        markup.add(types.KeyboardButton('Поиск товара 📦'))
        markup.add(types.KeyboardButton('Назад 🔙'))
        message = bot.send_message(message.chat.id, "Выберите действие 🔽:", reply_markup=markup)
        bot.register_next_step_handler(message, handle_purchase_selection)

def handle_purchase_selection(message):
    text = emoji.replace_emoji(message.text.lower(), replace='').strip()

    if text in ['поиск товара', 'поиск', 'товар', 'найти', 'найти товар']:
        search_product(message)
    elif text in ['назад', 'начало']:
        send_main_menu(message)
    else:
        handle_unrecognized(message)

@bot.message_handler(func=lambda message: emoji.replace_emoji(message.text.lower(), replace='').strip() == 'управление пользователями')
def manage_users(message):
    login = user_sessions[message.chat.id]['login']
    response = requests.get(
            url='http://hack_statistics_server:5000/user', 
            data=json.dumps({'username': login}),
        )
    user_data = json.loads(response.content)
    permission_admin = int(user_data['permission_admin'])
    if permission_admin:
        markup = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
        markup.add(types.KeyboardButton('Добавить пользователя 👤'))
        markup.add(types.KeyboardButton('Удалить пользователя 🗑️'))
        markup.add(types.KeyboardButton('Назад 🔙'))
        bot.send_message(message.chat.id, "Выберите действие для управления пользователями:", reply_markup=markup)
        bot.register_next_step_handler(message, handle_user_management)
    else:
        bot.send_message(message.chat.id, "У вас нет прав на управление пользователями.")
        send_main_menu(message)

def handle_user_management(message):
    text = emoji.replace_emoji(message.text.lower(), replace='').strip()
    if text == 'добавить пользователя':
        markup = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
        markup.add(types.KeyboardButton('Назад 🔙'))
        message = bot.send_message(message.chat.id, "Введите имя нового пользователя:" , reply_markup=markup)
        bot.register_next_step_handler(message, add_user_name)
    elif text == 'удалить пользователя':
        markup = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
        markup.add(types.KeyboardButton('Назад 🔙'))
        message = bot.send_message(message.chat.id, "Введите имя пользователя для удаления:", reply_markup=markup)
        bot.register_next_step_handler(message, delete_user_name)
    elif text in ['назад', 'начало']:
        send_main_menu(message)
    else:
        bot.send_message(message.chat.id, "Неправильный выбор.")
        manage_users(message)


def delete_user_name(message):
    username = emoji.replace_emoji(message.text.lower(), replace='').strip()
    response = requests.get(
            url='http://hack_statistics_server:5000/user', 
            data=json.dumps({'username': username}),
        )

    if username in ['назад', 'начало']:
        send_main_menu(message)
    elif json.loads(response.content) == {'result': 'User not found'}:
        bot.send_message(message.chat.id, "Пользователь не существует. Попробуйте другое имя.")
        manage_users(message)
    else:
        user_data = {'username': username}
        markup = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
        markup.add(types.KeyboardButton('Назад 🔙'))
        message = bot.send_message(message.chat.id, "Введите пароль для пользователя, которого удаляем:", reply_markup=markup)
        bot.register_next_step_handler(message, delete_user_password, user_data)


def delete_user_password(message, user_data):
    password = emoji.replace_emoji(message.text.lower(), replace='').strip()

    if password in ['назад', 'начало']:
        send_main_menu(message)
    else: 
        my_password_bytes = password.encode('utf-8')
        md5_hash = hashlib.md5()
        md5_hash.update(my_password_bytes)

        user_data['password'] = md5_hash.hexdigest()
        response = requests.delete(
            url='http://hack_statistics_server:5000/user', 
            data=json.dumps(user_data),
        )
        if response.content and json.loads(response.content) == {'error': f'Incorrect password'}:
            bot.send_message(message.chat.id, "Пароль не подошел.")
            manage_users(message)
        else:
            bot.send_message(message.chat.id, f"Пользователь {user_data['username']} успешно удален.")

            send_main_menu(message)


def add_user_name(message):
    new_username = emoji.replace_emoji(message.text.lower(), replace='').strip()
    response = requests.get(
            url='http://hack_statistics_server:5000/user', 
            data=json.dumps({'username': new_username}),
        )

    if new_username in ['назад', 'начало']:
        send_main_menu(message)
    elif json.loads(response.content) != {'result': 'User not found'}:
        bot.send_message(message.chat.id, "Пользователь уже существует. Попробуйте другое имя.")
        manage_users(message)
    else:
        user_data = {'username': new_username}
        markup = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
        markup.add(types.KeyboardButton('Назад 🔙'))
        message = bot.send_message(message.chat.id, "Введите пароль для нового пользователя:", reply_markup=markup)
        bot.register_next_step_handler(message, add_user_password, user_data)

def add_user_password(message, user_data):
    new_password = emoji.replace_emoji(message.text.lower(), replace='').strip()
    if new_password in ['назад', 'начало']:
        send_main_menu(message)
    else:
        my_password_bytes = new_password.encode('utf-8')
        md5_hash = hashlib.md5()
        md5_hash.update(my_password_bytes)

        user_data['password'] = md5_hash.hexdigest()
        markup = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
        markup.add(types.KeyboardButton('Назад 🔙'))
        bot.send_message(message.chat.id, f"В каком подразделении находится пользователь?", reply_markup=markup)
        bot.register_next_step_handler(message, add_user_department, user_data)

def add_user_department(message, user_data):
    department = emoji.replace_emoji(message.text.lower(), replace='').strip()
    if department in ['назад', 'начало']:
        send_main_menu(message)
    else:
        user_data['department'] = department
        bot.send_message(message.chat.id, f"Дать пользователю админ-права? да/нет")
        bot.register_next_step_handler(message, add_user_permission_admin, user_data)

def add_user_permission_admin(message, user_data):
    perm = emoji.replace_emoji(message.text.lower(), replace='').strip()
    if perm in ['да', 'нет']:
        if perm == 'да':
            user_data['permission_admin'] = 1
        elif perm == 'нет':
            user_data['permission_admin'] = 0
        markup = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
        markup.add(types.KeyboardButton('Назад 🔙'))
        bot.send_message(message.chat.id, f"Разрешить просматривать остатки и делать прогнозы для нового пользователя? да/нет", reply_markup=markup)
        bot.register_next_step_handler(message, add_user_permission_view_forecasts, user_data)
    elif perm in ['назад', 'начало']:
        send_main_menu(message)
    else:
        bot.send_message(message.chat.id, f"Вы должны ввести да/нет")
        bot.register_next_step_handler(message, add_user_permission_admin, user_data)
   

def add_user_permission_view_forecasts(message, user_data):
    perm = emoji.replace_emoji(message.text.lower(), replace='').strip()
    if perm in ['да', 'нет']:
        if perm == 'да':
            user_data['permission_forecast'] = 1
        elif perm == 'нет':
            user_data['permission_forecast'] = 0
        markup = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
        markup.add(types.KeyboardButton('Назад 🔙'))
        bot.send_message(message.chat.id, f"Разрешить создавать закупку и json для нового пользователя? да/нет", reply_markup=markup)
        bot.register_next_step_handler(message, add_user_permission_create_json, user_data)
    elif perm in ['назад', 'начало']:
        send_main_menu(message)
    else:
        bot.send_message(message.chat.id, f"Вы должны ввести да/нет")
        bot.register_next_step_handler(message, add_user_permission_view_forecasts, user_data)

def add_user_permission_create_json(message, user_data):
    perm = emoji.replace_emoji(message.text.lower(), replace='').strip()
    if perm in ['да', 'нет']:
        if perm == 'да':
            user_data['permission_json'] = 1
        elif perm == 'нет':
            user_data['permission_json'] = 0

        response = requests.put(
            url='http://hack_statistics_server:5000/user', 
            data=json.dumps(user_data),
        )
        
        if response.status_code != 200:
            bot.send_message(message.chat.id, f"""Пользователь {user_data['username']} не добавлен, 
возникли ошибки. {response.contentjson.loads(response.content)}""")
        else:
            bot.send_message(message.chat.id, f"Пользователь {user_data['username']} успешно добавлен.")

        send_main_menu(message)
    elif perm in ['назад', 'начало']:
        send_main_menu(message)
    else:
        bot.send_message(message.chat.id, f"Вы должны ввести да/нет")
        bot.register_next_step_handler(message, add_user_permission_create_json, user_data)


# Handler for unrecognized commands
@bot.message_handler(func=lambda message: True)
def handle_unrecognized(message):
    bot.send_message(message.chat.id, "Команда не распознана ❓. Пожалуйста, выберите действие из меню 🔽.")

if __name__ == '__main__':
    
	bot.infinity_polling()
