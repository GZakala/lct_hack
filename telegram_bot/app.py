import json
import requests

import telebot


API_TOKEN = '7292865506:AAHk1-6hUxhaDCEYg9lbXWG3RwBcf2RwxWs'
bot = telebot.TeleBot(API_TOKEN)

@bot.message_handler(commands=['start', 'info'])
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
СТЕ: {row.get('ste_name', '')}
Характеристика СТЕ: {row.get('ste_name', '')}
		"""
		if row['kpgz_code'] != '':
			response_text += f"КПГЗ: {row['kpgz_code']} - {row['kpgz_name']}\n"
		if row['spgz_code'] != '':
			response_text += f"СПГЗ: {row['spgz_code']} - {row['spgz_name']}\n"

	bot.reply_to(message, response_text)

@bot.message_handler(commands=['search_kpgz'])
def search_kpgz(message: telebot.types.Message):
	response = requests.get(
		url='http://hack_statistics_server:5000/search_kpgz', 
		data=json.dumps({'text': message.text, 'k': 5}),
	)
	
	response_text = 'Я нешел следующие КПГЗ по вашему запросу\n'
	rows = json.loads(response.content)
	if not rows:
		return bot.reply_to(message, 'Я не нашел КПГЗ по вашему запросу')
	for row in rows:
		response_text += "\n"
		if row['kpgz_code'] != '':
			response_text += f"КПГЗ: {row['kpgz_code']} - {row['kpgz_name']}\n"
		if row['spgz_code'] != '':
			response_text += f"СПГЗ: {row['spgz_code']} - {row['spgz_name']}\n"

	bot.reply_to(message, response_text)


if __name__ == '__main__':
	bot.infinity_polling()
