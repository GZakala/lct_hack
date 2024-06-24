import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.absolute()))

import io
import json
import requests
import requests
import emoji
import base64
import re
import tempfile
from datetime import datetime, timedelta

import jwt
from PIL import Image
import telebot
from telebot import types
from keycloak import KeycloakOpenID


from config import Config

cfg = Config.load()
bot = telebot.TeleBot(cfg.api_token)

# Создание экземпляра KeycloakOpenID
keycloak_openid = KeycloakOpenID(
    server_url=cfg.keycloak_server_url,
    client_id=cfg.keycloak_client_id,
    realm_name=cfg.keycloak_realm_name,
    client_secret_key=cfg.keycloak_client_secret
)


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

def last_contract_api(spgz_name):
    # Return top 3 relevant products
    response = requests.get(
		url='http://hack_statistics_server:5000/last_contract', 
		data=json.dumps({'spgz_name': spgz_name}),
	)
    rows = json.loads(response.content)
    return rows

def get_restrictions_api(product_name):
    response = requests.get(
		url='http://hack_statistics_server:5000/search_restrictions', 
		data=json.dumps({'text': product_name, "k": 1}),
	)
    return [d['restrictions'] for d in json.loads(response.content)]

def get_forecast_period_api(product_name, period):
    periodru2e = {
        'месяц': "month",
        'квартал': "quarter",
        'год': "year"
    }
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
    financial_en2ru = {
        'start_quarter': '📅 Начало прогноза',
        'end_quarter': '📅 Конец прогноза',
        'spgz_name': '🏷️ СПГЗ',
        'saldo_start_debit_quantity': '🔢 Кол-во товара',
        'saldo_start_debit_price': '💰 Стоимость товара',
        'turnovers_debit_quantity': '🏷️ Кол-во закупленного товара',
        'turnovers_debit_price': '💰 Цена закупленного товара',
        'turnovers_credit_quantity': '🏷️ Кол-во потраченного товара',
        'turnovers_credit_price': '💰 Цена потраченного товара',
        'saldo_end_debit_quantity': '🏷️ Кол-во оставшегося товара',
        'saldo_end_debit_price': '💰 Цена оставшегося товара',
        'regularity': '🔄 Регулярность',
    }
    def split_decimal_number_with_spaces(number):
        number_str = str(number)
        if '.' in number_str:
            # Split the number into integer and decimal parts
            integer_part, decimal_part = number_str.split('.')
        else:
            # If there is no decimal part
            integer_part, decimal_part = number_str, ''
        
        # Reverse the integer part to start grouping from the end
        reversed_int_part = integer_part[::-1]
        
        # Group the digits of the integer part into groups of three
        int_groups = [reversed_int_part[i:i+3] for i in range(0, len(reversed_int_part), 3)]
        
        # Join the groups with spaces and reverse the result
        formatted_int_part = ' '.join(int_groups)[::-1]
        
        # Combine the formatted integer part with the decimal part
        if decimal_part:
            return f"{formatted_int_part}.{decimal_part}"
        else:
            return formatted_int_part

    financial_str = ''
    n = 0
    for k, v in financial.items():
        if k in ['start_quarter', 'end_quarter']:
            date_time_obj = datetime.strptime(v, '%Y-%m-%d %H:%M:%S')
            financial_str += f"{financial_en2ru[k]}: {date_time_obj.strftime('%Y-%m-%d')}\n" 
        elif "Кол-во" in k:
            financial_str += f"{financial_en2ru[k]}: {int(v)}\n" 
        elif isinstance(v, float):
            financial_str += f"{financial_en2ru[k]}: {split_decimal_number_with_spaces(round(v, 2))} руб.\n" 
        else:
            financial_str += f"{financial_en2ru[k]}: {v}\n" 
        if n == 3:
            financial_str += '\n'
        n += 1

    response = requests.get(
		url='http://hack_statistics_server:5000/prognoze_contracts', 
		data=json.dumps({'spgz_name': product_name, 'date_grain': periodru2e[period]}),
	)
    contracts = json.loads(response.content)

    contracts_en2ru = {
        'contract_date': '📅 Дата заключения контракта',
        'contract_price': '💰 Цена контракта',
        'next_contract_delta': '📅 Дельта следующего контракта',
        'regularity': '🔄 Регулярность контрактов',
    }


    contracts_str = ''
    for d in contracts:
        contracts_str_lst = []
        for k, v in d.items():
            
            if k in ['contract_date']:
                date_time_obj = datetime.strptime(v, '%Y-%m-%d %H:%M:%S')
                contracts_str_lst += [f"{contracts_en2ru[k]}: {date_time_obj.strftime('%Y-%m-%d')}"]
            elif k in ['contract_price']:
                contracts_str_lst += [f"{contracts_en2ru[k]}: {split_decimal_number_with_spaces(round(v, 2))} руб."]
            else:
                contracts_str_lst += [f"{contracts_en2ru[k]}: {v}"]
            
        contracts_str += "\n".join(contracts_str_lst) + "\n"*2
    return {
         "forecast":  f"""Прогноз по финансовым данным\n{financial_str}\n
Прогноз по контрактам\n{contracts_str}\n
Для полной аналитики перейдите по ссылке: https://superset.cosahack.ru""",
         "images": images
	}

current_state = {}

@bot.message_handler(commands=['start'])
def process_start(message):
    current_state[message.chat.id] = {
        'current_search': '',
        'current_permission': []
    }
    bot.register_next_step_handler(message, request_login)

@bot.message_handler(
    func=lambda message: emoji.replace_emoji(message.text.lower(), replace='').strip()in ["выйти"]
    )
def request_login(message):
    markup = types.ReplyKeyboardMarkup()
    bot.send_message(message.chat.id, "Пожалуйста, авторизуйтесь для продолжения. Введите логин:", reply_markup=markup)
    bot.register_next_step_handler(message, request_password)

def request_password(message):
    login = message.text.strip()
    bot.send_message(message.chat.id, "Введите пароль:")
    bot.register_next_step_handler(message, authorize, login)

def authorize(message, login):
    password = message.text.strip()
    try:
        access_token = keycloak_openid.token(login, password)
    except:
        bot.send_message(message.chat.id, "Логин или пароль неверные.")
        request_login(message)

    decoded_token = jwt.decode(access_token['access_token'], options={"verify_signature": False})

    roles = decoded_token.get("resource_access", {}).get("auth", []).get('roles', [])
    current_state[message.chat.id]['current_permission'] = roles
    if 'admin' in roles:
        bot.send_message(message.chat.id, """Система администрирования Keycloak - здесь Вы можете управлять пользователями https://auth.cosahack.ru/""")
    send_main_menu(message)

def send_main_menu(message):
    current_state[message.chat.id]['current_search'] = ''
    permissions = current_state[message.chat.id]['current_permission'] 

    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True, one_time_keyboard=True)
    markup.add(types.KeyboardButton('Поиск товара 📦'))
    if 'forecast' in permissions:
        markup.add(types.KeyboardButton('Просмотр остатков и прогноз 📊'))
    if 'json' in permissions:
        markup.add(types.KeyboardButton('Проведение закупки и создание JSON 🛒'))
    
    markup.add(types.KeyboardButton('Выйти'))
    bot.send_message(message.chat.id, "Выберите действие из кнопок ниже:", reply_markup=markup)

# Handlers for each option
@bot.message_handler(func=lambda message: emoji.replace_emoji(message.text.lower(), replace='').strip() in \
    ["поиск товара", "поиск", "товар", "найти", "найти товар"])
def search_product(message):
    markup = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True, one_time_keyboard=True)
    markup.add(types.KeyboardButton('Назад 🔙'))
    bot.send_message(message.chat.id, """Введите название товара 📦:""", reply_markup=markup)
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
            markup = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True, one_time_keyboard=True)
            bot.send_message(message.chat.id, "\n".join([f"📌{i+1}. {r['spgz_name']}" for i, r in enumerate(results)]))
            for i in range(len(results)):
                markup.add(types.KeyboardButton(f"📌 {str(i+1)}"))

            markup.add(types.KeyboardButton('Ни один из этих товаров'))
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
        current_state[message.chat.id]['current_search'] = selected_product
        permissions = current_state[message.chat.id]['current_permission'] 
        markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True, one_time_keyboard=True)
        if 'forecast' in permissions:
            markup.add(types.KeyboardButton('Просмотр остатков и прогноз 📊'))
        if 'json' in permissions:
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
        send_final_json(message)
    elif text in ['назад', 'начало']:
        send_main_menu(message)
    else:
        message = bot.send_message(message.chat.id, "Команда не распознана ❓. Пожалуйста, выберите действие из меню 🔽.")
        send_main_menu(message)

def view_restrictions(message):
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True, one_time_keyboard=True)
    markup.add(types.KeyboardButton('Назад 🔙'))
    restrictions = get_restrictions_api(current_state[message.chat.id]['current_search'])
    if not restrictions:
        restictions_str = 'Ограничения небыли найдены'
    else:
        restictions_str = restrictions[0]
    # for d in restictions:
    #     restictions_str += "\n".join(f"{k}: {v}" for k, v in d.items())
    #     restictions_str += "\n"*2
    bot.send_message(message.chat.id, restictions_str, reply_markup=markup)
    send_main_menu(message)
    

@bot.message_handler(func=lambda message: emoji.replace_emoji(message.text.lower(), replace='').strip() \
    in ["просмотр остатков и прогноз", "остатки", "прогноз"])
def view_stock_and_forecast(message):
    product_name = current_state[message.chat.id]['current_search']
    if product_name:
        process_view_stock_and_forecast(message, product_name)
    else:
        markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True, one_time_keyboard=True)
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
        message = bot.send_message(message.chat.id, "Команда не распознана ❓. Пожалуйста, выберите действие из меню 🔽.")
        send_main_menu(message)

def process_view_stock_and_forecast(message, product_name=None):
    if not product_name:
        product_name = message.text
    current_state[message.chat.id]['current_search'] = product_name
    bot.send_message(message.chat.id, f"Вы выбрали {product_name}")
    markup = types.ReplyKeyboardMarkup(row_width=3, resize_keyboard=True, one_time_keyboard=True)
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
        permissions = current_state[message.chat.id]['current_permission'] 
        bot.send_message(message.chat.id, f"Остатки на складе")
        if 'grafic_dynamics_financial_quantity' in images:
            bot.send_photo(message.chat.id, images['grafic_dynamics_financial_quantity'])
        if 'grafic_dynamics_financial_price' in images:
            bot.send_photo(message.chat.id, images['grafic_dynamics_financial_price'])

        declension = {
            "месяц": "месяца",
            "квартал": "квартала",
            "год": "года"
        }
        bot.send_message(message.chat.id, f"Прогноз на начало {declension[period]}:\n{forecast_data}")
        if 'grafic_dynamics_financial_prognoze' in images:
            bot.send_photo(message.chat.id, images['grafic_dynamics_financial_prognoze'])
        if 'grafic_dynamics_contracts_prognoze' in images:
            bot.send_photo(message.chat.id, images['grafic_dynamics_contracts_prognoze'])
        markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True, one_time_keyboard=True)

        if 'json' in permissions:
            markup.add(types.KeyboardButton('Проведение закупки и создание JSON 🛒'))
        markup.add(types.KeyboardButton('Выбрать другой интервал 📅'))
        markup.add(types.KeyboardButton('Посмотреть ограничения 📊'))
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
        markup = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True, one_time_keyboard=True)
        markup.add(types.KeyboardButton('Назад 🔙'))
        message = bot.send_message(message.chat.id, "Процедура закупки начата 🛍️.", reply_markup=markup)
        send_final_json(message)
    elif text in ['посмотреть ограничения']:
        view_restrictions(message)
    elif text in ['выбрать другой интервал']:
        process_view_stock_and_forecast(message, product_name)
    else:
        message = bot.send_message(message.chat.id, "Команда не распознана ❓. Пожалуйста, выберите действие из меню 🔽.")


def send_final_json(message):
    try:
        spgz_name = current_state[message.chat.id]['current_search']
        last_contract_data = last_contract_api(spgz_name)
        rows = []
        for data in last_contract_data:
            response = requests.get(
            url='http://hack_statistics_server:5000/prognoze_contracts', 
            data=json.dumps({'spgz_name': spgz_name, 'date_grain': 'month'}),
            )
            contracts = json.loads(response.content)[0]
            for k, v in contracts.items():
                if k in ['contract_date']:
                    date_time_obj = datetime.strptime(v, '%Y-%m-%d %H:%M:%S')
                    contracts[k] = date_time_obj.strftime('%Y-%m-%d')
                elif k in ['contract_price']:
                    contracts[k] = f'{round(v, 2)} руб.'
                else:
                    contracts[k] = v
            timedelta_obj =  timedelta(days=contracts['next_contract_delta'])
            contracts['end_date'] = (date_time_obj + timedelta_obj).strftime('%Y-%m-%d')
            contracts['year'] = (date_time_obj).strftime('%Y')

            response = requests.get(
                url='http://hack_statistics_server:5000/search_restrictions', 
                data=json.dumps({'text': spgz_name, "k": 1}),
            )
            restrictions = json.loads(response.content)
            if restrictions:
                entity_id = restrictions[0]['entity_id']
            else:
                entity_id = ''

            rows.append({
                    "DeliverySchedule": {
                        "dates": {
                            "end_date": contracts['end_date'],
                            "start_date": contracts['contract_date']
                        },
                        "deliveryAmount": "",
                        "deliveryConditions":  "",
                        "year": contracts['year']  
                    },
                    "address": {
                        "gar_id": '1',
                        "text": '1'
                    },
                    "entityId": entity_id,
                    "id": "",
                    "nmc": data['contract_price'],
                    "okei_code": "",
                    "purchaseAmount": "",
                    "spgzCharacteristics": [
                    {
                        "characteristicName": data['spgz_name'],
                        "characteristicSpgzEnums": [
                            {  
                                "spgz_code": data['spgz_code'],
                                "kpgz_name": data['kpgz_name'],
                                "kpgz_code": data['kpgz_code']
                            }
                        ],
                        "conditionTypeId": "" ,
                        "kpgzCharacteristicId":""  ,
                        "okei_id": "" ,
                        "selectType": data['supplier_selection_method'] ,
                        "typeId": ""
                    },
                ]
            })

        final_json = {
            "id": '1',
            "lotEntityId": '1',
            "CustomerId": '1',
            "rows": rows
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
    if not product_name and message.chat.id in current_state:
        product_name = current_state[message.chat.id]['current_search']
    if product_name:
        # Simulate purchase process
        message = bot.send_message(message.chat.id, "Формируем Json? Да - для продолжить.")
        bot.register_next_step_handler(message, send_final_json)
        
    else:
        markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True, one_time_keyboard=True)
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
        bot.send_message(message.chat.id, "Команда не распознана ❓. Пожалуйста, выберите действие из меню 🔽.")
        send_main_menu(message)


if __name__ == '__main__':
    
	bot.infinity_polling()
