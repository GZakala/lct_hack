import os

from pathlib import Path
from typing import Dict

from jinja2 import Environment, FileSystemLoader, Template

from psql_client import PSQLClient
from opensearch_client import OpensearchClient


CUR_DIR = Path(__file__).parent

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

	def select_procurement_contracts_date_data(self, spgz_name: str, date_grain: str):
		sql = self.templates['select_procurement_contracts_date_data'].render(
			spgz_name=spgz_name, date_grain=date_grain
		)
		return self.sql_client.select(sql)

	def select_financial_quarter_data(self, spgz_name: str, date_grain: str):
		sql = self.templates['select_financial_quarter_data'].render(
			spgz_name=spgz_name, date_grain=date_grain
		)
		return self.sql_client.select(sql)

	def search_kpgz(self, text: str, k: int = 5):
		return self.opensearch_client.search_kpgz(text, k)

	def search_storage_costs(self, text: str, k: int = 5):
		return self.opensearch_client.search_storage_costs(text, k)

	def search_contracts(self, text: str, k: int = 5):
		return self.opensearch_client.search_contracts(text, k)
