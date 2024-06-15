import os

from pathlib import Path
from typing import Dict
from dateutil.relativedelta import relativedelta
from datetime import datetime

import numpy as np

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

		return {
			'saldo_start_debit_quantity': last_saldo_end_debit_quantity,
			'saldo_start_debit_price': last_saldo_end_debit_price,
			'turnovers_debit_quantity': prognoze_turnovers_debit_quantity,
			'turnovers_debit_price': prognoze_turnovers_debit_price,
			'turnovers_credit_quantity': avg_turnovers_credit_quantity,
			'turnovers_credit_price': avg_turnovers_credit_price,
			'saldo_end_debit_quantity': avg_saldo_end_credit_quantity,
			'saldo_end_debit_price': avg_saldo_end_credit_price,
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
		avg_price_per_delta = contracts_df['price_per_1_delta'].mean().item()
		avg_contracts_price = float(np.average(
			contracts_df.sort_values('contract_date')['contracts_price'].values, 
			weights=np.array(range(1, contracts_df.shape[0]+1)) ** 5))
		last_contract_price, last_contract_cur_date_delta = contracts_df \
			[contracts_df['contract_date'] == contracts_df['contract_date'].max()] \
			[['contracts_price', 'delta']].values[0]

		delta_available = (
			float(last_contract_price) 
			- (float(avg_price_per_delta) * float(last_contract_cur_date_delta))
		) // avg_price_per_delta

		if date_grain == 'month':
			next_contract_date = max(NOW, NOW + relativedelta(months=int(delta_available)))
		if date_grain == 'quarter':
			next_contract_date = NOW + relativedelta(months=int(delta_available*3))
		if date_grain == 'year':
			next_contract_date = NOW + relativedelta(years=int(delta_available))

		return {
			'contract_date': str(next_contract_date),
			'contract_price': float(avg_contracts_price),
		}

	def search_kpgz(self, text: str, k: int = 5):
		return self.opensearch_client.search_kpgz(text, k)

	def search_storage_costs(self, text: str, k: int = 5):
		return self.opensearch_client.search_storage_costs(text, k)

	def search_contracts(self, text: str, k: int = 5):
		return self.opensearch_client.search_contracts(text, k)
