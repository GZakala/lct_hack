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
		if date_grain not in ('quarter', 'year'):
			return {
				'error': 'date_grain must be one of [quarter, year]'
			}

		sql = self.templates['select_financial_quarter_data'].render(
			spgz_name=spgz_name, date_grain=date_grain
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

		if date_grain == 'quarter':
			end_quarter = str(datetime(year=2023, month=3, day=31))
		elif date_grain == 'year':
			end_quarter = str(datetime(year=2023, month=9, day=30))

		return {
			'start_quarter': str(datetime(year=2023, month=1, day=1)),
			'end_quarter': str(end_quarter),
			'spgz_name': spgz_name,
			'saldo_start_debit_quantity': last_saldo_end_debit_quantity,
			'saldo_start_debit_price': last_saldo_end_debit_price,
			'turnovers_debit_quantity': prognoze_turnovers_debit_quantity,
			'turnovers_debit_price': prognoze_turnovers_debit_price,
			'turnovers_credit_quantity': avg_turnovers_credit_quantity,
			'turnovers_credit_price': avg_turnovers_credit_price,
			'saldo_end_debit_quantity': avg_saldo_end_credit_quantity,
			'saldo_end_debit_price': avg_saldo_end_credit_price,
			'regularity': regular_type,
		}

	def select_procurement_contracts_date_data(self, spgz_name: str, date_grain: str):
		sql = self.templates['select_procurement_contracts_date_data'].render(
			spgz_name=spgz_name, date_grain=date_grain
		)
		return self.sql_client.select(sql)

	def prognoze_contracts(self, spgz_name: str, date_grain: str = 'month'):
		if date_grain not in ('month',):
			return {
				'error': 'date_grain must be one of [month]'
			}

		sql = self.templates['select_procurement_contracts_date_data'].render(
			spgz_name=spgz_name, date_grain=date_grain
		)
		df = self.sql_client.select_df(sql)
		contracts_df = df[df['contracts_price'] > 0]

		regular_type = self.check_regularity_contracts(contracts_df.sort_values('contract_date')['delta'].values)
		if regular_type == 'Закупка регулярна':
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

		next_contract_date = max(
			NOW + relativedelta(months=1), 
			NOW + relativedelta(months=int(delta_available))
		)

		if regular_type == 'Закупка больше не регулярна':
			min_contract_date = str(contracts_df['contract_date'].dt.date.min())
			max_contract_date = str(contracts_df.sort_values('contract_date')['contract_date'].dt.date.values[-2])
			regular_type = f'Закупка была регулярна с {min_contract_date} по {max_contract_date}, но потом пересатала проводиться'

		return {
			'contract_date': str(next_contract_date),
			'contract_price': avg_price_per_delta * avg_delta,
			'next_contract_delta': avg_delta,
			'regularity': regular_type,
		}

	def search_kpgz(self, text: str, k: int = 5):
		return self.opensearch_client.search_kpgz(text, k)

	def search_storage_costs(self, text: str, k: int = 5):
		return self.opensearch_client.search_storage_costs(text, k)

	def search_contracts(self, text: str, k: int = 5):
		return self.opensearch_client.search_contracts(text, k)

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

	def create_grafic_dynamics_financial(self, spgz_name: str, date_grain: str):
		if date_grain not in ('quarter', 'year'):
			return {
				'error': 'date_grain must be one of [quarter, year]'
			}

		sql = self.templates['select_financial_quarter_data'].render(
			spgz_name=spgz_name, date_grain=date_grain
		)

		df = self.sql_client.select_df(sql)
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
		turnovers_credit = df['turnovers_credit_quantity']*-1
		turnovers_debit = df['turnovers_debit_quantity']
		saldo_end = df['saldo_end_debit_quantity']

		# Создание графика
		plt.figure(figsize=(14, 8))
		sns.set(style="whitegrid")

		# Bar chart для turnovers_credit_quantity
		ax = sns.barplot(x=dates, y=turnovers_credit, color='skyblue', label='Отток товара')
		ax.bar(dates, turnovers_debit, color='lightgreen', label='Приток товара', alpha=0.6)

		# Добавление числовых меток на столбцы
		for index, value in enumerate(turnovers_credit):
			ax.text(index, value + 0.5, f'{value}', color='blue', ha="center")
		for index, value in enumerate(turnovers_debit):
			ax.text(index, value + 0.5, f'{value}', color='green', ha="center")

		# Линия для saldo_end_debit_quantity
		sns.lineplot(x=dates, y=saldo_end, marker='o', color='coral', label='Общее количество товара', ax=ax)

		# Добавление числовых меток на линию
		for index, value in enumerate(saldo_end):
			plt.text(index, value, f'{value}', color='coral', ha="center", va="bottom")

		# Настройка легенды и цветов
		ax.legend(loc='lower left', fontsize=12)

		# Названия осей и заголовок
		ax.set_xlabel('Дата', fontsize=14)
		ax.set_ylabel('Количество', fontsize=14)
		plt.title('Динамика притока и оттока товара и общего количества товара на складе', fontsize=16)

		# Полупрозрачная сетка
		ax.grid(True, which='both', linestyle='--', linewidth=0.5, alpha=0.7)

		buf = io.BytesIO()
		plt.savefig(buf, format='png')
		buf.seek(0)
		return base64.b64encode(buf.getvalue()).decode()
