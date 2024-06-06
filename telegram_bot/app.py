import json
import requests

import telebot


API_TOKEN = '7292865506:AAHk1-6hUxhaDCEYg9lbXWG3RwBcf2RwxWs'
bot = telebot.TeleBot(API_TOKEN)

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
	bot.reply_to(message, 'How are you doing?')

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
		response_text += f"""
		{row.get('kpgz_code', '')}:
			Название КПГЗ: {row.get('ste_name', '')}
			СТЕ: {row.get('ste_name', '')}
			Характеристика СТЕ: {row.get('ste_name', '')}
			Название СПГЗ: {row.get('spgz_name', '')}
			Код СПГЗ: {row.get('spgz_code', '')}
		"""

	bot.reply_to(message, response_text)


if __name__ == '__main__':
	bot.infinity_polling()
