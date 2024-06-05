import os

from pathlib import Path
from typing import Dict

from jinja2 import Environment, FileSystemLoader, Template

from psql_client import PSQLClient


class StatsCalculator:
	def __init__(self):
		self.loader = FileSystemLoader('./templates')
		self.tmpl_env = Environment(loader=self.loader)
		self.templates = self.get_templates()
		self.sql_client = PSQLClient(
			host='0.0.0.0',
			port=5432,
			user='default',
			password='12345',
			dbname='hack',
		)

	def get_templates(self) -> Dict[str, Template]:
		template_files = os.listdir(Path(__file__).parent / 'templates')
		return {
			filename: self.tmpl_env.get_template(filename)
			for filename in template_files
		}

	def select_balances_accaunt_101(self, limit: int = 10):
		sql = self.templates['select_balances_accaunt_101'].render(
			limit=limit,
		)
		return self.sql_client.select(sql)
