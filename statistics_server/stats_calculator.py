import io
import os
import base64

from pathlib import Path
from typing import Dict, Sequence
from dateutil.relativedelta import relativedelta
from datetime import datetime

import numpy as np
import pandas as pd
import seaborn as sns

from matplotlib import pyplot as plt
from matplotlib.ticker import FuncFormatter
from jinja2 import Environment, FileSystemLoader, Template

from psql_client import PSQLClient
from opensearch_client import OpensearchClient


CUR_DIR = Path(__file__).parent
NOW = datetime(year=2023, month=1, day=1)

class StatsCalculator:
	DAY = 'day'
	MONTH = 'month'
	QUARTER = 'quarter'
	YEAR = 'year'

	def __init__(
		self,
		sql_host: str = 'hack_postgres',
		sql_port: int = 5432,
		sql_user: str = 'default',
		sql_password: str = '12345',
		sql_dbname: str = 'hack',
		osearch_host: str = 'hack_opensearch',
		osearch_port: int = 9200,
		osearch_user: str = 'admin',
		osearch_password: str = 'admin',
	):
		self.loader = FileSystemLoader(CUR_DIR / 'templates')
		self.tmpl_env = Environment(loader=self.loader)
		self.templates = self.get_templates()
		self.sql_client = PSQLClient(
			host=sql_host,
			port=sql_port,
			user=sql_user,
			password=sql_password,
			dbname=sql_dbname,
		)
		self.opensearch_client = OpensearchClient(
			host=osearch_host,
			port=osearch_port,
			user=osearch_user,
			password=osearch_password,
			sql_client=self.sql_client,
		)

	def get_templates(self) -> Dict[str, Template]:
		template_files = os.listdir(CUR_DIR / 'templates')
		return {
			filename.split('.')[0]: self.tmpl_env.get_template(filename)
			for filename in template_files
		}

	def select_financial_quarter_data(self, spgz_name: str, date_grain: str):
		sql = self.templates['select_financial_quarter_data'].render(
			spgz_name=spgz_name, date_grain=date_grain
		)
		return self.sql_client.select(sql)

	def prognoze_financial_quarter_data(self, spgz_name: str, date_grain: str):
		if date_grain not in ('month', 'quarter', 'year'):
			return {
				'error': 'date_grain must be one of [month, quarter, year]'
			}

		sql = self.templates['select_financial_quarter_data'].render(
			spgz_name=spgz_name, date_grain='quarter'
		)
		df = self.sql_client.select_df(sql)
		weights = np.array(range(1, df.shape[0]+1)) ** 5
		last_saldo_end_debit_quantity = int(df['last_saldo_end_debit_quantity']
			.head(1).item())
		last_saldo_end_debit_price = float(df['last_saldo_end_debit_price']\
			.head(1).item())
		avg_turnovers_credit_quantity = int(np.average(
			df.sort_values('report_date')['turnovers_credit_quantity'].values, 
			weights=weights))
		avg_turnovers_credit_price = float(np.average(
			df.sort_values('report_date')['turnovers_credit_price'].values, 
			weights=weights))
		avg_saldo_end_credit_quantity = int(np.average(
			df.sort_values('report_date')['saldo_end_debit_quantity'].values, 
			weights=weights))
		avg_saldo_end_credit_price = float(np.average(
			df.sort_values('report_date')['saldo_end_debit_price'].values, 
			weights=weights))

		prognoze_turnovers_debit_quantity = (
			avg_saldo_end_credit_quantity 
			- (last_saldo_end_debit_quantity - avg_turnovers_credit_quantity))
		prognoze_turnovers_debit_price = (
			avg_saldo_end_credit_price 
			- (last_saldo_end_debit_price - avg_turnovers_credit_price))

		regular_type = int(df['is_regular_spgz'].values[0]),
		if regular_type == 1:
			regular_type = 'Регулярные товары'
		else:
			regular_type = 'Нерегулярные товары'

		if date_grain == 'month':
			end_quarter = str(datetime(year=2023, month=2, day=1))
			prognoze_turnovers_debit_quantity /= 3
			prognoze_turnovers_debit_price /= 3
			avg_turnovers_credit_quantity /= 3
			avg_turnovers_credit_price /= 3
			avg_saldo_end_credit_quantity /= 3
			avg_saldo_end_credit_price /= 3
		if date_grain == 'quarter':
			end_quarter = str(datetime(year=2023, month=3, day=31))
		elif date_grain == 'year':
			end_quarter = str(datetime(year=2023, month=9, day=30))
			prognoze_turnovers_debit_quantity *= 4
			prognoze_turnovers_debit_price *= 4
			avg_turnovers_credit_quantity *= 4
			avg_turnovers_credit_price *= 4
			avg_saldo_end_credit_quantity *= 4
			avg_saldo_end_credit_price *= 4

		if prognoze_turnovers_debit_price > 0:
			prognoze_turnovers_debit_quantity = max(prognoze_turnovers_debit_quantity, 1)
		if avg_turnovers_credit_price > 0:
			avg_turnovers_credit_quantity = max(avg_turnovers_credit_quantity, 1)
		if avg_saldo_end_credit_price > 0:
			avg_saldo_end_credit_quantity = max(avg_saldo_end_credit_quantity, 1)

		return {
			'start_quarter': str(datetime(year=2023, month=1, day=1)),
			'end_quarter': str(end_quarter),
			'spgz_name': spgz_name,
			'saldo_start_debit_quantity': abs(last_saldo_end_debit_quantity),
			'saldo_start_debit_price': abs(last_saldo_end_debit_price),
			'turnovers_debit_quantity': abs(prognoze_turnovers_debit_quantity),
			'turnovers_debit_price': abs(prognoze_turnovers_debit_price),
			'turnovers_credit_quantity': abs(avg_turnovers_credit_quantity),
			'turnovers_credit_price': abs(avg_turnovers_credit_price),
			'saldo_end_debit_quantity': abs(avg_saldo_end_credit_quantity),
			'saldo_end_debit_price': abs(avg_saldo_end_credit_price),
			'regularity': regular_type,
		}

	def select_procurement_contracts_date_data(self, spgz_name: str, date_grain: str):
		sql = self.templates['select_procurement_contracts_date_data'].render(
			spgz_name=spgz_name, date_grain=date_grain
		)
		return self.sql_client.select(sql)

	def prognoze_contracts(self, spgz_name: str, date_grain: str = 'month'):
		if date_grain not in ('month', 'quarter', 'year'):
			return [{'error': 'date_grain must be one of [month, quarter, year]'}]

		sql = self.templates['select_procurement_contracts_date_data'].render(
			spgz_name=spgz_name, date_grain='month'
		)
		df = self.sql_client.select_df(sql)
		contracts_df = df[df['contracts_price'] > 0]

		regular_type = self.check_regularity_contracts(contracts_df.sort_values('contract_date')['delta'].values)
		if regular_type == 'Закупка регулярна' or contracts_df.shape[0] == 1:
			avg_price_per_delta = contracts_df['price_per_1_delta'].mean()
			avg_delta = int(contracts_df['delta'].mean())
		else:
			weights = np.array(range(1, contracts_df.shape[0]+1)) ** 5
			avg_price_per_delta = float(np.average(
				contracts_df.sort_values('contract_date')['price_per_1_delta'].astype('float').values[:-1], 
				weights=weights[:-1]))
			avg_delta = int(np.average(
				contracts_df.sort_values('contract_date')['delta'].astype('float').values, 
				weights=weights))

		last_contract_price, last_contract_cur_date_delta = contracts_df \
			[contracts_df['contract_date'] == contracts_df['contract_date'].max()] \
			[['contracts_price', 'delta']].values[0]

		delta_available = (
			float(last_contract_price) 
			- (float(avg_price_per_delta) * float(last_contract_cur_date_delta))
		) // avg_price_per_delta


		if regular_type == 'Закупка больше не регулярна':
			min_contract_date = str(contracts_df['contract_date'].dt.date.min())
			max_contract_date = str(contracts_df.sort_values('contract_date')['contract_date'].dt.date.values[-2])
			regular_type = f'Закупка была регулярна с {min_contract_date} по {max_contract_date}, но потом пересатала проводиться'

		if date_grain == 'month':
			prognoze_limit = 1
		if date_grain == 'quarter':
			prognoze_limit = 3
		if date_grain == 'year':
			prognoze_limit = 12

		first_prognoze_delta = max(1, delta_available)
		next_contract_date = NOW + relativedelta(months=first_prognoze_delta)
		next_prognoze_delta = first_prognoze_delta
		prognoze_contracts = [{
			'contract_date': str(next_contract_date),
			'contract_price': avg_price_per_delta * avg_delta,
			'next_contract_delta': avg_delta,
			'regularity': regular_type,
		}]
		while next_prognoze_delta + avg_delta <= prognoze_limit:
			next_prognoze_delta += avg_delta
			next_delta = np.random.randint(avg_delta-1, avg_delta+2)
			next_price_per_delta = np.random.uniform(0.9, 1.1) * avg_price_per_delta
			next_contract_date = next_contract_date + relativedelta(months=next_delta)
			prognoze_contracts.append({
				'contract_date': str(next_contract_date),
				'contract_price': next_price_per_delta * next_delta,
				'next_contract_delta': next_delta,
				'regularity': regular_type,
			})

		return prognoze_contracts

	def search_kpgz(self, text: str, k: int = 5):
		return self.opensearch_client.search_kpgz(text, k)

	def search_storage_costs(self, text: str, k: int = 5):
		return self.opensearch_client.search_storage_costs(text, k)

	def search_contracts(self, text: str, k: int = 5):
		return self.opensearch_client.search_contracts(text, k)

	def search_restrictions(self, text: str, k: int = 1):
		return self.opensearch_client.search_restrictions(text, k)

	def check_regularity_contracts(self, contracts_deltas: Sequence[int]):
		deltas = contracts_deltas[:-1]
		last_delta = contracts_deltas[-1]
		if len(deltas) <= 2:
			return 'Нерегулярная закупка'

		mean_delta = np.mean(deltas)
		std_delta = np.std(deltas)
		if std_delta / mean_delta > 1:
			return 'Нерегулярная закупка'

		if (np.mean(deltas) * 2) < last_delta:
			return 'Закупка больше не регулярна'

		return 'Закупка регулярна'

	def add_user(
		self, 
		username: str,
		department: str,
		permission_admin: int,
		permission_forecast: int,
		permission_json: int,
		password: str,
	):
		sql = self.templates['add_user'].render(
			username=username,
			department=department,
			permission_admin=permission_admin,
			permission_forecast=permission_forecast,
			permission_json=permission_json,
			password=password,
		)
		return self.sql_client.execute(sql)

	def get_user(self, username: str):
		sql = self.templates['get_user'].render(username=username)
		return self.sql_client.select(sql)

	def del_user(self, username: str):
		sql = self.templates['del_user'].render(username=username)
		return self.sql_client.execute(sql)

	def create_grafic_dynamics_financial_quantity(self, spgz_name: str, date_grain: str):
		sql = self.templates['select_financial_quarter_data'].render(
			spgz_name=spgz_name, date_grain=date_grain
		)

		df = self.sql_client.select_df(sql)

		df_check = not(df.empty)

		df['report_date'] = pd.to_datetime(df['report_date']).dt.quarter.apply(lambda x: f'Q{x}')
		cols_to_convert = [
			'turnovers_debit_quantity',
			'turnovers_debit_price', 'turnovers_credit_quantity',
			'turnovers_credit_price', 'saldo_end_debit_quantity',
			'saldo_end_debit_price', 'last_saldo_end_debit_quantity',
			'last_saldo_end_debit_price'
		]
		df[cols_to_convert] = df[cols_to_convert].astype(float)
		df = df.sort_values(by='report_date')

		dates = df['report_date']
		turnovers_credit = df['turnovers_credit_quantity'].astype(int) * -1
		turnovers_debit = df['turnovers_debit_quantity'].astype(int)
		saldo_end = df['saldo_end_debit_quantity'].astype(int)

		# Создание графика
		plt.figure(figsize=(14, 8))
		sns.set(style="white")

		# Bar chart для turnovers_credit_quantity
		ax = sns.barplot(x=dates, y=turnovers_credit, color='skyblue', label='Отток товара', legend=False)
		ax.bar(dates, turnovers_debit, color='lightgreen', label='Приток товара', alpha=0.6)

		# Добавление числовых меток на столбцы
		for index, value in enumerate(turnovers_credit):
			if value == 0:
				ax.text(index, 0, f'{value}', color='blue', ha="center", va="center")  # Метка по 0
			else:
				ax.text(index, value, f'{value}', color='blue', ha="center", va="top")  # Смещение меток ниже

		for index, value in enumerate(turnovers_debit):
			if value == 0:
				ax.text(index, 0, f'{value}', color='green', ha="center", va="center")  # Метка по 0
			else:
				ax.text(index, value , f'{value}', color='green', ha="center")

		# Вторичная ось для saldo_end_debit_quantity
		ax2 = ax.twinx()
		sns.lineplot(x=dates, y=saldo_end, marker='o', color='coral', label='Общее количество товара', ax=ax2)

		# Добавление числовых меток на линию
		for index, value in enumerate(saldo_end):
			if value == 0:
				ax2.text(index, 0, f'{value}', color='coral', ha="center", va="center")  # Метка по 0
			else:
				ax2.text(index, value, f'{value}', color='coral', ha="center", va="bottom")  # Смещение меток выше

		# Настройка легенды и цветов
		handles, labels = ax.get_legend_handles_labels()
		handles2, labels2 = ax2.get_legend_handles_labels()
		ax2.legend(handles=handles + handles2, labels=labels + labels2, loc='upper center', bbox_to_anchor=(0.5, -0.1), fontsize=12)

		# Названия осей и заголовок
		ax.set_xlabel('Дата', fontsize=14)
		ax.set_ylabel('Количество (Приток и Отток)', fontsize=14)
		ax2.set_ylabel('Количество (Общее)', fontsize=14)
		plt.title('Динамика притока и оттока товара, суммарное количество товара на складе', fontsize=16)

		# Полупрозрачная сетка
		ax.grid(True, which='both', linestyle='--', linewidth=0.5, alpha=0.7)

		# Настройка осей y для симметрии относительно нуля
		y_max = max(turnovers_debit.max(), -turnovers_credit.min())
		ax.set_ylim(-y_max, y_max)

		# Настройка правой оси y для симметрии относительно нуля и в диапазоне ±15% от min и max значений saldo_end
		margin = 0.15 * (saldo_end.max() - saldo_end.min())
		y2_max = max(saldo_end.max(), -saldo_end.min())
		#ax2.set_ylim(-y2_max - margin, y2_max + margin)

		margin_d = 0.15 * (turnovers_credit.max() - turnovers_credit.min())
		margin_t = 0.15 * (turnovers_debit.max() - turnovers_debit.min())
		ax.set_ylim(turnovers_credit.min() - margin_d, turnovers_debit.max() + margin_t)
		ax.set_ylim(-y_max - margin_d, y_max+ margin_t)

		buf = io.BytesIO()
		plt.savefig(buf, format='png')
		buf.seek(0)

		return base64.b64encode(buf.getvalue()).decode(), df_check

	def create_grafic_dynamics_financial_price(self, spgz_name: str, date_grain: str):
		sql = self.templates['select_financial_quarter_data'].render(
			spgz_name=spgz_name, date_grain=date_grain
		)

		df = self.sql_client.select_df(sql)

		df_check = not(df.empty)

		df['report_date'] = pd.to_datetime(df['report_date']).dt.quarter.apply(lambda x: f'Q{x}')
		cols_to_convert = [
			'turnovers_debit_quantity',
			'turnovers_debit_price', 'turnovers_credit_quantity',
			'turnovers_credit_price', 'saldo_end_debit_quantity',
			'saldo_end_debit_price', 'last_saldo_end_debit_quantity',
			'last_saldo_end_debit_price'
		]
		df[cols_to_convert] = df[cols_to_convert].astype(float)
		df = df.sort_values(by='report_date')

		dates = df['report_date']
		turnovers_credit = df['turnovers_credit_price'].astype(int) * -1
		turnovers_debit = df['turnovers_debit_price'].astype(int)
		saldo_end = df['saldo_end_debit_price'].astype(int)

		# Создание графика
		fig, ax = plt.subplots(figsize=(16, 8))
		sns.set(style="white")

		# Bar chart для turnovers_credit_price
		ax.bar(dates, turnovers_credit, color='skyblue', label='Потрачено товара на сумму')
		ax.bar(dates, turnovers_debit, color='lightgreen', label='Приток товара на сумму', alpha=0.6)

		# Добавление числовых меток на столбцы
		for index, value in enumerate(turnovers_credit):
			if value == 0:
				ax.text(index, 0, f'{int(value):,}', color='blue', ha="center", va="center")  # Метка по 0
			else:
				ax.text(index, value - 0.05 * max(turnovers_credit), f'{int(value):,}', color='blue', ha="center", va="top")  # Смещение меток ниже

		for index, value in enumerate(turnovers_debit):
			if value == 0:
				ax.text(index, 0, f'{int(value):,}', color='green', ha="center", va="center")  # Метка по 0
			else:
				ax.text(index, value + 0.05 * max(turnovers_debit), f'{int(value):,}', color='green', ha="center")

		# Линия для saldo_end_debit_price
		ax2 = ax.twinx()
		ax2.plot(dates, saldo_end, marker='o', color='coral', label='Общая сумма товара')

		# Добавление числовых меток на линию
		for index, value in enumerate(saldo_end):
			if value == 0:
				ax2.text(index, 0, f'{int(value):,}', color='coral', ha="center", va="center")  # Метка по 0
			else:
				ax2.text(index, value, f'{int(value):,}', color='coral', ha="center", va="bottom")  # Смещение меток выше

		# Настройка легенды и цветов
		handles1, labels1 = ax.get_legend_handles_labels()
		handles2, labels2 = ax2.get_legend_handles_labels()
		ax2.legend(handles=handles1 + handles2, labels=labels1 + labels2, loc='upper center', bbox_to_anchor=(0.5, -0.1), fontsize=12, ncol=2)

		# Названия осей и заголовок
		ax.set_xlabel('Дата', fontsize=14)
		ax.set_ylabel('Стоимость (Приток и Отток)', fontsize=14)
		ax2.set_ylabel('Общая стоимость', fontsize=14)
		plt.title('Динамика притока и оттока товара, суммарная стоимость товара на складе', fontsize=16)

		# Полупрозрачная сетка
		ax.grid(True, which='both', linestyle='--', linewidth=0.5, alpha=0.7)

		# Функция для форматирования чисел с разделением разрядов
		def millions_formatter(x, pos):
			return f'{int(x):,}'

		# Применение форматирования к оси y на обеих шкалах
		ax.yaxis.set_major_formatter(FuncFormatter(millions_formatter))
		ax2.yaxis.set_major_formatter(FuncFormatter(millions_formatter))

		# Настройка оси y для симметрии относительно нуля
		y_max = max(turnovers_debit.max(), -turnovers_credit.min())
		ax.set_ylim(-y_max, y_max)

		# Настройка правой оси y для симметрии относительно нуля и в диапазоне ±15% от min и max значений saldo_end
		margin = 0.15 * (saldo_end.max() - saldo_end.min())
		y2_max = max(saldo_end.max(), -saldo_end.min())
		#ax2.set_ylim(-y2_max - margin, y2_max + margin)

		# Настройка левой оси y для симметрии относительно нуля и в диапазоне ±15% от min и max значений оборотов
		margin_d = 0.15 * (turnovers_credit.max() - turnovers_credit.min())
		margin_t = 0.15 * (turnovers_debit.max() - turnovers_debit.min())
		ax.set_ylim(turnovers_credit.min() - margin_d, turnovers_debit.max() + margin_t)
		ax.set_ylim(-y_max - margin_d, y_max+ margin_t)

		# Сохранение графика в байтовый буфер
		buf = io.BytesIO()
		plt.savefig(buf, format='png', bbox_inches='tight')
		buf.seek(0)

		return base64.b64encode(buf.getvalue()).decode(), df_check

	def create_grafic_dynamics_financial_prognoze(self, spgz_name: str, date_grain: str):
		sql = self.templates['select_financial_quarter_data'].render(
			spgz_name=spgz_name, date_grain='month'
		)

		df = self.sql_client.select_df(sql)
		df['report_date'] = pd.to_datetime(df['report_date']).dt.quarter.apply(lambda x: f'2022-Q{x}')
		cols_to_convert = [
			'turnovers_debit_quantity',
			'turnovers_debit_price', 'turnovers_credit_quantity',
			'turnovers_credit_price', 'saldo_end_debit_quantity',
			'saldo_end_debit_price', 'last_saldo_end_debit_quantity',
			'last_saldo_end_debit_price'
		]
		df[cols_to_convert] = df[cols_to_convert].astype(float)
		df = df.sort_values(by='report_date')

		predict_month = self.prognoze_financial_quarter_data(spgz_name=spgz_name, date_grain='month')['turnovers_debit_quantity']
		predict_q = predict_month*3
		predict_y = predict_month*12

		turnovers_debit = df['turnovers_debit_quantity'].to_list()

		dates = df['report_date'].to_list()
		
		if date_grain == 'month':
			dates.append('2023-Q1-January')
			turnovers_debit.append(predict_month)
		elif date_grain == 'quarter':
			dates.append('2023-Q1')
			turnovers_debit.append(predict_q)
		else:
			dates.append('2023-(Q1-Q4)')
			turnovers_debit.append(predict_y)


		plt.figure(figsize=(14, 8))
		sns.set(style="whitegrid")

		# Линия для turnovers_debit_m
		ax = sns.lineplot(x=dates, y=turnovers_debit, marker='o', color='coral', label='Исторические значения и прогноз')
		

		# Добавление числовых меток на линию turnovers_debit_m
		for index, value in enumerate(turnovers_debit):
			plt.text(index, value + 0.025 * max(turnovers_debit), f'{value}', color='coral', ha="center", va="bottom")

		#ax.lines[-1].set_color('purple')  # Последняя линия графика (прогноз)

		# Настройка легенды и цветов
		ax.legend(loc='upper left', fontsize=12)

		# Названия осей и заголовок
		ax.set_xlabel('Дата', fontsize=14)
		ax.set_ylabel('Количество', fontsize=14)
		plt.title(f'Динамика закупок по фин. отчетам, прогноз на выбранный период', fontsize=16)

		# Полупрозрачная сетка
		ax.grid(True, which='both', linestyle='--', linewidth=0.5, alpha=0.7)

		buf = io.BytesIO()
		plt.savefig(buf, format='png')
		buf.seek(0)

		return base64.b64encode(buf.getvalue()).decode()

	def create_grafic_dynamics_contracts_prognoze(self, spgz_name: str, date_grain: str):
		sql = self.templates['select_procurement_contracts_date_data'].render(
			spgz_name=spgz_name, date_grain='month'
		)

		df = self.sql_client.select_df(sql)
		contracts_df = df[df['contracts_price'] > 0]
		contracts_df['contract_date'] = pd.to_datetime(df['contract_date'])
		contracts_df['contract_date_formatted'] = contracts_df['contract_date'].dt.to_period('M').astype(str)
		contracts_df[['delta','price_per_1_delta', 'contracts_price']] = contracts_df[['delta','price_per_1_delta', 'contracts_price']].astype(float)

		dic_forecasts = self.prognoze_contracts(spgz_name=spgz_name, date_grain=date_grain)

		# Создание списков дат и значений
		historical_dates = contracts_df['contract_date_formatted'].to_list()
		historical_prices = contracts_df['contracts_price'].to_list()

		forecast_dates = []
		forecast_prices = []
		
		for forecast in dic_forecasts:
			forecast_date = pd.to_datetime(forecast["contract_date"]).strftime('%Y-%m')
			forecast_dates.append(forecast_date)
			forecast_prices.append(int(forecast["contract_price"]))  

		historical_dates.append(forecast_dates[0])
		historical_prices.append(forecast_prices[0])

		# Создание графика
		plt.figure(figsize=(14, 8))
		sns.set(style="whitegrid")

		# Определение основного графика и добавление прогнозных значений
		ax = sns.lineplot(x=historical_dates, y=historical_prices, marker='o', color='coral', label='Исторические данные')
		sns.lineplot(x=forecast_dates, y=forecast_prices, marker='o', color='purple', label='Прогноз')

		# Добавление числовых меток на график
		for index, value in enumerate(historical_prices[:-1]):
			formatted_value = '{:,.0f}'.format(value)  # Форматирование числа с разделением разрядов
			plt.text(index, value, f'{formatted_value}', color='coral', ha="center", va="bottom")

		for index, value in enumerate(forecast_prices[:]):
			formatted_value = '{:,.0f}'.format(value)  # Форматирование числа с разделением разрядов
			plt.text(len(historical_prices[1:]) + index, value, f'{formatted_value}', color='purple', ha="center", va="bottom")
		# Настройка легенды и цветов
		ax.legend(loc='upper left', fontsize=12)

		# Названия осей и заголовок
		ax.set_xlabel('Дата', fontsize=14)
		ax.set_ylabel('Стоимость', fontsize=14)
		plt.title('Динамика закупок по контрактам, прогноз на выбранный период', fontsize=16)

		# Полупрозрачная сетка
		ax.grid(True, which='both', linestyle='--', linewidth=0.5, alpha=0.7)

		# Отключение научного формата оси Y
		ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, loc: "{:,}".format(int(x))))

		buf = io.BytesIO()
		plt.savefig(buf, format='png')
		buf.seek(0)
		return base64.b64encode(buf.getvalue()).decode()
	