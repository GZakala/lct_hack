import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.absolute()))


import json
import requests
from functools import wraps

import telebot
from flask import Flask, request
from keycloak import KeycloakOpenID

from config import Config

cfg = Config.load()
app = Flask(__name__)
bot = telebot.TeleBot(cfg.api_token)
keycloak_openid = KeycloakOpenID(
	server_url=cfg.keycloak_server_url,
    client_id=cfg.keycloak_client_id,
    realm_name=cfg.keycloak_realm_name,
    client_secret_key=cfg.keycloak_client_secret,
)


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

@bot.message_handler(commands=['info'])
# @requires_auth
def send_welcome(message: telebot.types.Message):
	bot.reply_to(
		message, 
		f"""
Привет, я бот для помощи в закупках.
Я умею анализировать историю закупок и делать прогнозы.
Вот полный список моих умений:
/search_ste [text] - найти СТЕ по тексту
/search_kpgz [text] - найти КПГЗ и СПГЗ по тексту
		""",
	)

@bot.message_handler(commands=['search_ste'])
# @requires_auth
def search_ste(message: telebot.types.Message):
	response = requests.get(
		url='http://hack_statistics_server:5000/search_ste', 
		data=json.dumps({'text': message.text, 'k': 5}),
	)
	
	response_text = 'Я нешел следующие КПГЗ по вашему запросу\n'
	rows = json.loads(response.content)
	if not rows:
		return bot.reply_to(message, 'Я не нашел КПГЗ по вашему запросу')
	for row in rows:
		response_text += f"""
СТЕ?: {row.get('ste_name', '')}
Характеристика СТЕ: {row.get('ste_name', '')}
		"""
		if row['kpgz_code'] != '':
			response_text += f"КПГЗ: {row['kpgz_code']} - {row['kpgz_name']}\n"
		if row['spgz_code'] != '':
			response_text += f"СПГЗ: {row['spgz_code']} - {row['spgz_name']}\n"

	bot.reply_to(message, response_text)

@bot.message_handler(commands=['search_kpgz'])
# @requires_auth
def search_kpgz(message: telebot.types.Message):
	response = requests.get(
		url='http://hack_statistics_server:5000/search_kpgz', 
		data=json.dumps({'text': message.text, 'k': 5}),
	)
	
	response_text = 'Я нешел следующие КПГЗ по вашему запросу\n'
	rows = json.loads(response.content)
	if not rows:
		return bot.reply_to(message, '')
	for row in rows:
		response_text += "\n"
		if row['kpgz_code'] != 'Я не нашел КПГЗ по вашему запросу':
			response_text += f"КПГЗ: {row['kpgz_code']} - {row['kpgz_name']}\n"
		if row['spgz_code'] != '':
			response_text += f"СПГЗ: {row['spgz_code']} - {row['spgz_name']}\n"

	bot.reply_to(message, response_text)


if __name__ == '__main__':
	from threading import Thread
	Thread(target=app.run, kwargs={'host':'0.0.0.0', 'port': 8000}).start()
	bot.infinity_polling()
