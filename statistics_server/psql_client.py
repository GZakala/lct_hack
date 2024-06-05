from typing import Any, Sequence, List

import psycopg2
import pandas as pd


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

	def select_df(self, sql: str, columns: Sequence[str] = None) -> pd.DataFrame:
		cursor = self.client.cursor()
		try:
			cursor.execute(sql)
		except Exception as e:
			print(f'Error while executing method select_df: {sql}')
			print(str(e))
			return

		rows = [row for row in cursor]
		cursor.close()
		if columns:
			return pd.DataFrame(rows, columns=columns)
		return pd.DataFrame(rows)

	def select(self, sql) -> List[Any]:
		cursor = self.client.cursor()
		try:
			cursor.execute(sql)
		except Exception as e:
			print(f'Error while executing method select_df: {sql}')
			print(str(e))
			return

		rows = [[str(field) for field in row] for row in cursor]
		cursor.close()
		return rows

