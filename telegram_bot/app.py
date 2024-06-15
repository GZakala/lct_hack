import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.absolute()))


import json
import requests
# from functools import wraps
from PIL import Image
import telebot
from telebot import types
from io import BytesIO
import requests
import emoji
import base64
import io

# from flask import Flask, request
# from keycloak import KeycloakOpenID

from config import Config

cfg = Config.load()
# app = Flask(__name__)
bot = telebot.TeleBot(cfg.api_token)
# keycloak_openid = KeycloakOpenID(
# 	server_url=cfg.keycloak_server_url,
#     client_id=cfg.keycloak_client_id,
#     realm_name=cfg.keycloak_realm_name,
#     client_secret_key=cfg.keycloak_client_secret,
# )

# @app.route('/callback')
# def callback():
# 	global access_token
# 	authorization_code = request.args.get('code')
# 	if not authorization_code:
# 		return "Authorization code not provided", 400

# 	token_response = keycloak_openid.token(authorization_code, cfg.keycloak_redirect_url)
# 	access_token = token_response['access_token']
# 	refresh_token = token_response['refresh_token']
	
# 	return f"Access Token: {access_token}<br>Refresh Token: {refresh_token}"

# def requires_auth(func):
#     @wraps(func)
#     def wrapper(message, *args, **kwargs):
#         global access_token
#         if not access_token:
#             bot.reply_to(message, "Вы должны сначала авторизоваться!/start")
#             return
#         return func(message, *args, **kwargs)
#     return wrapper

# @bot.message_handler(commands=['start'])
# def start(message):
#     auth_url = keycloak_openid.auth_url(redirect_uri=cfg.keycloak_redirect_uri)
#     bot.reply_to(message, f"Перейдите для авторизации: {auth_url}")

periodru2e = {
    'месяц': "month",
    'квартал': "quarter",
    'год': "year"
}


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
        if not row['ste_name'] in seen and len(response_list) <= 5 and row['ste_name']:
            response_list.append({
                'ste_name': row['ste_name'] if row['ste_name'] else row['spgz_name'],
                'spgz_name': row['spgz_name']
                })
            seen.add(row['ste_name'])
    return response_list

def create_image_with_text():
    with open("./src/h.png", 'rb') as image_file:
        img_byte_arr = BytesIO(image_file.read())
        img_byte_arr.seek(0)
        return img_byte_arr

def get_stock_and_forecast_api(product_name):
    # Return stock and forecast data as a dictionary
    return {
        "stock": "Stock data for product",
        "forecast": "Forecast data for product",
        "image": create_image_with_text()
    }

def get_forecast_period_api(product_name, period):
    # Return forecast data for a given period
    # response = requests.get(
	# 	url='http://hack_statistics_server:5000/prognoze_financial_quarter', 
	# 	data=json.dumps({'spgz_name': product_name, 'date_grain': periodru2e[period]}),
	# )
    # rows = json.loads(response.content)

    response = requests.get(
		url='http://hack_statistics_server:5000/grafic_dynamics_financial', 
		data=json.dumps({'spgz_name': ste2kpgs[product_name], 'date_grain': periodru2e[period]}),
	)
    val = json.loads(response.content)['img']
    image = Image.open(io.BytesIO(base64.b64decode(val.encode())))
    return {
         "forecast":  f"Forecast data for {period}",
         "image": image
	}

def get_contract_data_api(product_name):
    # Return contract data for the product
    return {
        "last_purchase": "Date of last purchase",
        "amount": "Amount of last purchase",
        "image": create_image_with_text()
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
           
        }
    ]
}


current_search = {}
user_sessions = {}
ste2kpgs = {}


# Main menu handler
@bot.message_handler(commands=['start'])
def send_welcome(message):
    current_search.pop(message.chat.id, None)  # Clear the search history for the user
    user_sessions.pop(message.chat.id, None)  # Clear the session for the user
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
    if user_data['password'] == password:
        user_sessions[message.chat.id]['permission_admin'] = user_data['permission_admin']
        send_main_menu(message)
    else:
        bot.send_message(message.chat.id, "Неправильный пароль. Попробуйте снова.")
        send_welcome(message)

def send_main_menu(message):
    current_search.pop(message.chat.id, None)
    username = user_sessions[message.chat.id]['login']
    response = requests.get(
		url='http://hack_statistics_server:5000/user', 
		data=json.dumps({'username': username}),
	)
    user_data = json.loads(response.content)
    permission_admin = user_data['permission_admin']

    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    itembtn1 = types.KeyboardButton('Поиск товара 📦')
    markup.add(itembtn1)
    if user_data['permission_forecast']:
        markup.add(types.KeyboardButton('Просмотр остатков и прогноз 📊'))
    if user_data['permission_json']:
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

def process_search_product(message):
    text = emoji.replace_emoji(message.text.lower(), replace='').strip()
    if text in ['назад', 'начало']:
        send_main_menu(message)
    else:  
        product_name = text
        
        results = search_product_api(product_name)
        
        if results:
            ste2kpgs.update({r['ste_name']: r['spgz_name'] for r in results})
            markup = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
            for result in results:
                markup.add(types.KeyboardButton(result['ste_name']))
                bot.send_message(message.chat.id, result['ste_name'])
                  
            markup.add(types.KeyboardButton('Ни один из этих товаров'))
            markup.add(types.KeyboardButton('Задать товар вручную ✏️'))
            markup.add(types.KeyboardButton('Назад 🔙'))
            bot.send_message(message.chat.id, "Наиболее релевантные товары:", reply_markup=markup)
            bot.register_next_step_handler(message, handle_search_selection)
        else:
            bot.send_message(message.chat.id, "Релевантных товаров не найдено. Пожалуйста, проверьте написание.")
            send_main_menu(message)

def handle_search_selection(message):
    text = emoji.replace_emoji(message.text.lower(), replace='').strip()
    if text == 'ни один из этих товаров':
        message = bot.send_message(message.chat.id, """Введите название товара 📦.\n
Если выбранный вариант не очень точен, вы можете потом вручную его скорректировать""")
        bot.register_next_step_handler(message, process_search_product)
    elif text in ['назад', 'начало'] :
        send_main_menu(message)
    elif text in ['изменить товар', 'задать товар вручную']:
        message = bot.send_message(message.chat.id, "Введите новое название товара ✏️:")
        bot.register_next_step_handler(message, edit_selected_product)
    else:
        selected_product = message.text
        current_search[message.chat.id] = selected_product
        username = user_sessions[message.chat.id]['login']
        response = requests.get(
            url='http://hack_statistics_server:5000/user', 
            data=json.dumps({'username': username}),
        )
        user_data = json.loads(response.content)
        markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
        if user_data['permission_forecast']:
            markup.add(types.KeyboardButton('Просмотр остатков и прогноз 📊'))
        if user_data['permission_json']:
            markup.add(types.KeyboardButton('Проведение закупки и создание JSON 🛒'))
        markup.add(types.KeyboardButton('Изменить товар ✏️'))
        markup.add(types.KeyboardButton('Назад 🔙'))
        bot.send_message(message.chat.id, f"Вы выбрали {selected_product}. Что дальше?", reply_markup=markup)
        bot.register_next_step_handler(message, handle_post_search_actions)

def handle_post_search_actions(message):
    text = emoji.replace_emoji(message.text.lower(), replace='').strip()
    if text == 'просмотр остатков и прогноз':
        view_stock_and_forecast(message)
    elif text == 'проведение закупки и создание json':
        initiate_purchase_and_create_json(message)
    elif text in ['изменить товар', 'задать товар вручную']:
        message = bot.send_message(message.chat.id, "Введите новое название товара ✏️:")
        bot.register_next_step_handler(message, edit_selected_product)
    elif text in ['назад', 'начало']:
        send_main_menu(message)
    else:
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
    if user_data['permission_forecast']:
            markup.add(types.KeyboardButton('Просмотр остатков и прогноз 📊'))
    if user_data['permission_json']:
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
    if text == 'ввести название товара':
        markup = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
        markup.add(types.KeyboardButton('Назад 🔙'))
        message = bot.send_message(message.chat.id, """Введите название товара 📦:
Если выбранный вариант не очень точен, вы можете потом вручную его скорректировать""", reply_markup=markup)
        
        bot.register_next_step_handler(message, process_view_stock_and_forecast)
    elif text in ['поиск товара', 'поиск', 'товар', 'найти', 'найти товар']:
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
    data = get_stock_and_forecast_api(product_name)
    if data:
        bot.send_photo(message.chat.id, data['image'])
        bot.send_message(message.chat.id, f"Остатки: {data['stock']}\nПрогноз: {data['forecast']}")
        markup = types.ReplyKeyboardMarkup(row_width=3, resize_keyboard=True)
        markup.add(types.KeyboardButton('Месяц 📅'), types.KeyboardButton('Квартал 📅📅'), types.KeyboardButton('Год 📅📅📅'))
        markup.add(types.KeyboardButton('Назад 🔙'))
        bot.send_message(message.chat.id, "На какой период 📅 вас интересует прогноз?", reply_markup=markup)
        bot.register_next_step_handler(message, handle_forecast_period, product_name)
    else:
        contract_data = get_contract_data_api(product_name)
        if contract_data:
            bot.send_photo(message.chat.id, contract_data['image'])
            bot.send_message(message.chat.id, f"Последняя закупка: {contract_data['last_purchase']}\nСумма: {contract_data['amount']}")
            markup = types.ReplyKeyboardMarkup(row_width=3, resize_keyboard=True)
            markup.add(types.KeyboardButton('Месяц 📅'), types.KeyboardButton('Квартал 📅📅'), types.KeyboardButton('Год 📅📅📅'))
            markup.add(types.KeyboardButton('Назад 🔙'))
            bot.send_message(message.chat.id, "На какой период 📅 вас интересует прогноз ?", reply_markup=markup)
            bot.register_next_step_handler(message, handle_forecast_period, product_name)
        else:
            bot.send_message(message.chat.id, "Товар не найден 🔍🚫. Попробуйте снова.")
            send_main_menu(message)

def handle_forecast_period(message, product_name):
    text = emoji.replace_emoji(message.text.lower(), replace='').strip()
    if text in ['назад', 'начало']:
        send_main_menu(message)
    elif text in ['месяц', 'квартал', 'год']:
        period = text
        data = get_forecast_period_api(product_name, period)
        forecast_data = data['forecast']
        image = data['image']
        login = user_sessions[message.chat.id]['login']
        bot.send_photo(message.chat.id, image)
        bot.send_message(message.chat.id, f"Прогноз на {period}: {forecast_data}")
        markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)

        response = requests.get(
            url='http://hack_statistics_server:5000/user', 
            data=json.dumps({'username': login}),
        )
        user_data = json.loads(response.content)

        if user_data['permission_json']:
            markup.add(types.KeyboardButton('Проведение закупки и создание JSON 🛒'))
        markup.add(types.KeyboardButton('Назад 🔙'))
        bot.send_message(message.chat.id, "Хотите провести закупку 🛍️?", reply_markup=markup)
        bot.register_next_step_handler(message, handle_post_forecast_actions, product_name)
    else:
        bot.send_message(message.chat.id, "Пожалуйста, выберите правильный период: 'Месяц', 'Квартал' или 'Год'.")
        bot.register_next_step_handler(message, handle_forecast_period, product_name)

def handle_post_forecast_actions(message, product_name):
    if emoji.replace_emoji(message.text.lower(), replace='').strip() in ['назад', 'начало']:
        send_main_menu(message)
    else:
        bot.send_message(message.chat.id, "Процедура закупки начата 🛍️.")
        initiate_purchase_and_create_json(message, product_name)


def handle_initial_data(message):
    text = emoji.replace_emoji(message.text.lower(), replace='').strip()
    if text in ['назад', 'начало']:
        send_main_menu(message)
    else:
        try:
            data_list = message.text.split(',')
            if len(data_list) != 3:
                raise ValueError("Неверное количество данных")
            data["id"], data["lotEntityId"], data["CustomerId"] = data_list
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            markup.add(types.KeyboardButton('Назад 🔙'))
            bot.send_message(message.chat.id, "Введите следующие данные через запятую: start_date, end_date, deliveryAmount, deliveryConditions, year", reply_markup=markup)
            bot.register_next_step_handler(message, handle_delivery_schedule)
        except ValueError as e:
            bot.send_message(message.chat.id, f"Ошибка: {e}. Попробуйте еще раз.")
            bot.register_next_step_handler(message, handle_initial_data)

def handle_delivery_schedule(message):
    text = emoji.replace_emoji(message.text.lower(), replace='').strip()
    if text in ['назад', 'начало']:
        send_main_menu(message)
    else:
        try:
            data_list = message.text.split(',')
            if len(data_list) != 5:
                raise ValueError("Неверное количество данных")
            row = data["rows"][0]
            row["DeliverySchedule"]["dates"]["start_date"], row["DeliverySchedule"]["dates"]["end_date"], row["DeliverySchedule"]["deliveryAmount"], row["DeliverySchedule"]["deliveryConditions"], row["DeliverySchedule"]["year"] = data_list
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            markup.add(types.KeyboardButton('Назад 🔙'))
            bot.send_message(message.chat.id, "Введите следующие данные через запятую: gar_id, текстовый адрес", reply_markup=markup)
            bot.register_next_step_handler(message, handle_address)
        except ValueError as e:
            bot.send_message(message.chat.id, f"Ошибка: {e}. Попробуйте еще раз.")
            bot.register_next_step_handler(message, handle_delivery_schedule)

def handle_address(message):
    text = emoji.replace_emoji(message.text.lower(), replace='').strip()
    if text in ['назад', 'начало']:
        send_main_menu(message)
    else:
        try:
            data_list = message.text.split(',')
            if len(data_list) != 2:
                raise ValueError("Неверное количество данных")
            row = data["rows"][0]
            row["address"]["gar_id"], row["address"]["text"] = data_list
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            markup.add(types.KeyboardButton('Назад 🔙'))
            bot.send_message(message.chat.id, "Введите следующие данные через запятую: entityId, id, nmc, okei_code, purchaseAmount", reply_markup=markup)
            bot.register_next_step_handler(message, handle_row_data)
        except ValueError as e:
            bot.send_message(message.chat.id, f"Ошибка: {e}. Попробуйте еще раз.")
            bot.register_next_step_handler(message, handle_address)

def handle_row_data(message):
    text = emoji.replace_emoji(message.text.lower(), replace='').strip()
    if text in ['назад', 'начало']:
        send_main_menu(message)
    else:
        try:
            data_list = message.text.split(',')
            if len(data_list) != 5:
                raise ValueError("Неверное количество данных")
            row = data["rows"][0]
            row["entityId"], row["id"], row["nmc"], row["okei_code"], row["purchaseAmount"] = data_list
            # Send JSON file
            json_file = BytesIO(json.dumps(data, ensure_ascii=False, indent=4).encode('utf-8'))
            product_name = current_search[message.chat.id]
            json_file.name = f"{"_".join(product_name.split())}_contract.json"
            bot.send_document(message.chat.id, json_file)
            send_main_menu(message)

        except ValueError as e:
            bot.send_message(message.chat.id, f"Ошибка: {e}. Попробуйте еще раз.")
            bot.register_next_step_handler(message, handle_row_data)

# Handlers for purchase initiation and JSON creation
@bot.message_handler(func=lambda message: emoji.replace_emoji(message.text.lower(), replace='').strip() in \
    ["проведение закупки и создание json", "закупка"])
def initiate_purchase_and_create_json(message, product_name=None):
    if not product_name and message.chat.id in current_search:
        product_name = current_search[message.chat.id]
    if product_name:
        # Simulate purchase process
        bot.send_message(message.chat.id, f"Процедура закупки для {product_name} начата 🛒.")
        bot.send_message(message.chat.id, "Введите следующие данные через запятую: id, lotEntityId, CustomerId")
        bot.register_next_step_handler(message, handle_initial_data)
        
    else:
        markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
        markup.add(types.KeyboardButton('Ввести название товара 📦'))
        markup.add(types.KeyboardButton('Поиск товара 📦'))
        markup.add(types.KeyboardButton('Назад 🔙'))
        bot.send_message(message.chat.id, "Выберите действие 🔽:", reply_markup=markup)
        bot.register_next_step_handler(message, handle_purchase_selection)

def handle_purchase_selection(message):
    text = emoji.replace_emoji(message.text.lower(), replace='').strip()
    if text == 'ввести название товара':
        markup = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
        markup.add(types.KeyboardButton('Назад 🔙'))
        message = bot.send_message(message.chat.id, """Введите название товара 📦:
Если выбранный вариант не очень точен, вы можете потом вручную его скорректировать""", reply_markup=markup)
        bot.send_message(message.chat.id, "Введите следующие данные через запятую: id, lotEntityId, CustomerId")
        bot.register_next_step_handler(message, handle_initial_data)
    elif text in ['поиск товара', 'поиск', 'товар', 'найти', 'найти товар']:
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
    permission_admin = user_data['permission_admin']
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
        message = bot.send_message(message.chat.id, "Введите имя нового пользователя:")
        bot.register_next_step_handler(message, add_user_name)
    elif text == 'удалить пользователя':
        message = bot.send_message(message.chat.id, "Введите имя пользователя для удаления:")
        bot.register_next_step_handler(message, delete_user_name)
    elif text in ['назад', 'начало']:
        send_main_menu(message)
    else:
        bot.send_message(message.chat.id, "Неправильный выбор.")
        manage_users(message)

def add_user_name(message):
    new_username = message.text.strip()
    response = requests.get(
            url='http://hack_statistics_server:5000/user', 
            data=json.dumps({'username': new_username}),
        )
    user_data = json.loads(response.content)
    if user_data != {"result": "User not found"}:
        bot.send_message(message.chat.id, "Пользователь уже существует. Попробуйте другое имя.")
        manage_users(message)
    else:
        user_data = {'username': new_username}
        message = bot.send_message(message.chat.id, "Введите пароль для нового пользователя:")
        bot.register_next_step_handler(message, add_user_password, user_data)

def add_user_password(message, user_data):
    new_password = message.text.strip()
    user_data['password'] = new_password
    bot.send_message(message.chat.id, f"В каком подразделении находится пользователь?")
    bot.register_next_step_handler(message, add_user_department, user_data)

def add_user_department(message, user_data):
    department = message.text.strip()
    user_data['department'] = department
    bot.send_message(message.chat.id, f"Дать пользователю админ-права? да/нет")
    bot.register_next_step_handler(message, add_user_permission_admin, user_data)

def add_user_permission_admin(message, user_data):
    perm = message.text.strip()
    if perm in ['да', 'нет']:
        if perm == 'да':
            user_data['add_user_permission_admin'] = 1
        elif perm == 'нет':
            user_data['add_user_permission_admin'] = 0
        bot.send_message(message.chat.id, f"Разрешить просматривать остатки и делать прогнозы для нового пользователя? да/нет")
        bot.register_next_step_handler(message, add_user_permission_view_forecasts, user_data)
    else:
        bot.send_message(message.chat.id, f"Вы должны ввести да/нет")
        bot.register_next_step_handler(message, add_user_permission_admin, user_data)
   

def add_user_permission_view_forecasts(message, user_data):
    perm = message.text.strip()
    if perm in ['да', 'нет']:
        if perm == 'да':
            user_data['permission_forecast'] = 1
        elif perm == 'нет':
            user_data['permission_forecast'] = 0
        bot.send_message(message.chat.id, f"Разрешить создавать закупку и json для нового пользователя? да/нет")
        bot.register_next_step_handler(message, add_user_permission_create_json, user_data)
    else:
        bot.send_message(message.chat.id, f"Вы должны ввести да/нет")
        bot.register_next_step_handler(message, add_user_permission_view_forecasts, user_data)

def add_user_permission_create_json(message, user_data):
    perm = message.text.strip()
    if perm in ['да', 'нет']:
        if perm == 'да':
            user_data['permission_json'] = 1
        elif perm == 'нет':
            user_data['permission_json'] = 0
        response = requests.put(
            url='http://hack_statistics_server:5000/user', 
            data=json.dumps(user_data),
        )
        
        if response.status_code == 200:
            bot.send_message(message.chat.id, f"Пользователь {user_data['username']} не добавлен, возникли ошибки")
        else:
            bot.send_message(message.chat.id, f"Пользователь {user_data['username']} успешно добавлен.")

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
