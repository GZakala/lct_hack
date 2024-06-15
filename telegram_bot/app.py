import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.absolute()))


import json
import requests
# from functools import wraps

import telebot
from telebot import types
from io import BytesIO
import requests
import emoji

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


# Placeholder functions for API calls
def search_product_api(product_name):
    # Return top 3 relevant products
    response = requests.get(
		url='http://hack_statistics_server:5000/search_contracts', 
		data=json.dumps({'text': product_name, 'k': 5}),
	)
    rows = json.loads(response.content)
    response_list = []
    for row in rows:
         response_list.append(row.get('category', ''))
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
    return {
         "forecast":  f"Forecast data for {period}",
         "image": create_image_with_text()
	}

def get_contract_data_api(product_name):
    # Return contract data for the product
    return {
        "last_purchase": "Date of last purchase",
        "amount": "Amount of last purchase",
        "image": create_image_with_text()
    }

data_header = {
    "id": None,
    "lotEntityId": None,
    "CustomerId": None
}

current_search = {}

# Main menu handler
@bot.message_handler(commands=['start'])
def send_welcome(message):
    current_search.pop(message.chat.id, None)  # Clear the search history for the user
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    itembtn1 = types.KeyboardButton('Поиск товара 📦')
    itembtn2 = types.KeyboardButton('Просмотр остатков и прогноз 📊')
    itembtn3 = types.KeyboardButton('Проведение закупки и создание JSON 🛒')
    markup.add(itembtn1, itembtn2, itembtn3)
    bot.send_message(message.chat.id, """
Добро пожаловать! Выберите действие из кнопок ниже, или введите:\n
- Поиск товара 📦\n
- Просмотр остатков и прогноз 📊\n
- Проведение закупки и создание JSON 🛒""", reply_markup=markup)


# Handlers for each option
@bot.message_handler(func=lambda message: emoji.replace_emoji(message.text.lower(), replace='').strip() in \
    ["поиск товара", "поиск", "товар", "найти", "найти товар"])
def search_product(message):
    markup = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
    markup.add(types.KeyboardButton('Назад 🔙'))
    msg = bot.send_message(message.chat.id, "Введите название товара 📦:", reply_markup=markup)
    bot.register_next_step_handler(msg, process_search_product)

def process_search_product(message):
    text = emoji.replace_emoji(message.text.lower(), replace='').strip()
    if text in ['назад', 'начало']:
        send_welcome(message)
    else:  
        product_name = text
        
        results = search_product_api(product_name)
        
        if results:
            current_search[message.chat.id] = results
            
            
            markup = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
            for result in results:
                markup.add(types.KeyboardButton(result))
                bot.send_message(message.chat.id, result)
            
                  
            markup.add(types.KeyboardButton('Ни один из этих товаров'))
            markup.add(types.KeyboardButton('Назад 🔙'))
            bot.send_message(message.chat.id, "Наиболее релевантные товары:", reply_markup=markup)
            bot.register_next_step_handler(message, handle_search_selection)
        else:
            bot.send_message(message.chat.id, "Релевантных товаров не найдено. Пожалуйста, проверьте написание.")
            send_welcome(message)

def handle_search_selection(message):
    text = emoji.replace_emoji(message.text.lower(), replace='').strip()
    if text == 'ни один из этих товаров':
        msg = bot.send_message(message.chat.id, """Введите название товара 📦.\n
                               Если выбранный вариант не очень точен, вы можете потом вручную его скорректировать""")
        bot.register_next_step_handler(msg, process_search_product)
    elif text in ['назад', 'начало'] :
        send_welcome(message)
    else:
        selected_product = message.text
        current_search[message.chat.id] = selected_product
        markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
        markup.add(types.KeyboardButton('Просмотр остатков и прогноз 📊'))
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
    elif text == 'изменить товар':
        msg = bot.send_message(message.chat.id, "Введите новое название товара ✏️:")
        bot.register_next_step_handler(msg, edit_selected_product)
    elif text in ['назад', 'начало']:
        send_welcome(message)
    else:
        send_welcome(message)

def edit_selected_product(message):
    new_product_name = message.text
    current_search[message.chat.id] = new_product_name
    bot.send_message(message.chat.id, f"Товар изменён на {new_product_name}.")
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    markup.add(types.KeyboardButton('Просмотр остатков и прогноз 📊'))
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
        markup.add(types.KeyboardButton('Ввести название товара ✏️'))
        markup.add(types.KeyboardButton('Поиск товара 📦'))
        markup.add(types.KeyboardButton('Назад 🔙'))
        bot.send_message(message.chat.id, "Выберите действие 🔽:", reply_markup=markup)
        bot.register_next_step_handler(message, handle_stock_or_forecast_selection)

def handle_stock_or_forecast_selection(message):
    text = emoji.replace_emoji(message.text.lower(), replace='').strip()
    if text == 'ввести название товара':
        markup = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
        markup.add(types.KeyboardButton('Назад 🔙'))
        msg = bot.send_message(message.chat.id, "Введите название товара 📦:", reply_markup=markup)
        
        bot.register_next_step_handler(msg, process_view_stock_and_forecast)
    elif text in ['поиск товара', 'поиск', 'товар', 'найти', 'найти товар']:
        search_product(message)
    elif text in ['назад', 'начало']:
        send_welcome(message)
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
            send_welcome(message)

def handle_forecast_period(message, product_name):
    text = emoji.replace_emoji(message.text.lower(), replace='').strip()
    if text in ['назад', 'начало']:
        send_welcome(message)
    elif text in ['месяц', 'квартал', 'год']:
        period = text
        data = get_forecast_period_api(product_name, period)
        forecast_data = data['forecast']
        image = data['image']
        bot.send_photo(message.chat.id, image)
        bot.send_message(message.chat.id, f"Прогноз на {period}: {forecast_data}")
        markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
        markup.add(types.KeyboardButton('Проведение закупки и создание JSON 🛒'))
        markup.add(types.KeyboardButton('Назад 🔙'))
        bot.send_message(message.chat.id, "Хотите провести закупку 🛍️?", reply_markup=markup)
        bot.register_next_step_handler(message, handle_post_forecast_actions, product_name)
    else:
        bot.send_message(message.chat.id, "Пожалуйста, выберите правильный период: 'Месяц', 'Квартал' или 'Год'.")
        bot.register_next_step_handler(message, handle_forecast_period, product_name)

def handle_post_forecast_actions(message, product_name):
    if emoji.replace_emoji(message.text.lower(), replace='').strip() in ['назад', 'начало']:
        send_welcome(message)
    else:
        bot.send_message(message.chat.id, "Процедура закупки начата 🛍️.")
        initiate_purchase_and_create_json(message, product_name)


# Handlers for purchase initiation and JSON creation
@bot.message_handler(func=lambda message: emoji.replace_emoji(message.text.lower(), replace='').strip() in \
    ["проведение закупки и создание json", "закупка"])
def initiate_purchase_and_create_json(message, product_name=None):
    if not product_name and message.chat.id in current_search:
        product_name = current_search[message.chat.id]
    if product_name:
        # Simulate purchase process
        bot.send_message(message.chat.id, f"Процедура закупки для {product_name} начата 🛒.")
        
        
        
        # Send JSON file
        json_file = BytesIO(json.dumps(json_data, ensure_ascii=False, indent=4).encode('utf-8'))
        json_file.name = f"{product_name}_contract.json"
        bot.send_document(message.chat.id, json_file)

        send_welcome(message)
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
        msg = bot.send_message(message.chat.id, "Введите название товара 📦:", reply_markup=markup)
        bot.register_next_step_handler(msg, process_initiate_purchase)
    elif text in ['поиск товара', 'поиск', 'товар', 'найти', 'найти товар']:
        search_product(message)
    elif text in ['назад', 'начало']:
        send_welcome(message)
    else:
        handle_unrecognized(message)

def process_initiate_purchase(message):
    product_name = message.text
    current_search[message.chat.id] = product_name
    bot.send_message(message.chat.id, f"Вы выбрали {product_name}")
    initiate_purchase_and_create_json(message, product_name)

# Handler for unrecognized commands
@bot.message_handler(func=lambda message: True)
def handle_unrecognized(message):
    bot.send_message(message.chat.id, "Команда не распознана ❓. Пожалуйста, выберите действие из меню 🔽.")

if __name__ == '__main__':
	# from threading import Thread
	# Thread(target=app.run, kwargs={'host':'0.0.0.0', 'port': 8000}).start()
	bot.infinity_polling()
