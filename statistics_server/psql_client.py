from pathlib import Path
from typing import Any, List

import psycopg2
import pandas as pd

from logger import get_logger

LOGGER = get_logger(str(Path(__file__).absolute()))


class PSQLClient:
	def __init__(
		self, 
		host: str,
		port: int,
		user: str,
		password: str,
		dbname: str,
	):
		self.client = psycopg2.connect(
			host=host,
			port=port,
			user=user,
			password=password,
			dbname=dbname,
		)

	def select_df(self, sql: str) -> pd.DataFrame:
		cursor = self.client.cursor()
		try:
			cursor.execute(sql)
		except Exception as e:
			LOGGER.error(f'Error while executing method select_df: {sql}')
			LOGGER.error(str(e))
			cursor.close()
			return {
				'error': f'Error while executing method select_df: {sql}',
				'python_error': str(e),
		   	}

		rows = [row for row in cursor]
		columns = [col.name for col in cursor.description]

		self.client.commit()
		cursor.close()
		return pd.DataFrame(rows, columns=columns)

	def select(self, sql: str) -> List[Any]:
		cursor = self.client.cursor()
		try:
			cursor.execute(sql)
		except Exception as e:
			LOGGER.error(f'Error while executing method select: {sql}')
			LOGGER.error(str(e))
			return {
				'error': f'Error while executing method select: {sql}',
				'python_error': str(e),
		   	}

		columns = [col.name for col in cursor.description]
		rows = [
			{col: str(val) for col, val in zip(columns, row)}
			for row in cursor
		]

		self.client.commit()
		cursor.close()
		return rows

	def execute(self, sql: str):
		cursor = self.client.cursor()
		try:
			cursor.execute(sql)
		except Exception as e:
			LOGGER.error(f'Error while executing method select: {sql}')
			LOGGER.error(str(e))
			return False

		self.client.commit()
		cursor.close()
		return True
