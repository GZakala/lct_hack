import ndjson

from opensearchpy import OpenSearch

from psql_client import PSQLClient
from utils import batched


class OpensearchClient:
	def __init__(
		self, 
		host: str,
		port: int,
		user: str,
		password: str,
		sql_client: PSQLClient,
	):
		self.sql_client = sql_client
		self.client = OpenSearch(
			hosts=[{'host': host, 'port': port}],
			http_compress=True,
			http_auth=(user, password),
			use_ssl=False,
			verify_certs=False,
			ssl_assert_hostname=False,
			ssl_show_warn=False,
		)

	def create_kpgz_index(self, drop: bool = False):
		if self.client.indices.exists(index='kpgz'):
			if not drop:
				return
			self.client.indices.delete(index='kpgz')

		self.client.indices.create(index='kpgz', body={
			"settings": {
				"number_of_shards": 1,
				"number_of_replicas": 1
			},
			"mappings": {
				"dynamic": False,
				"properties": {
				"kpgz_code": { "type": "keyword" },
				"kpgz_name": { "type": "text" },
				"spgz_code": { "type": "keyword" },
				"spgz_name": { "type": "text" }
				}
			}
		})

		sql = """
		select 	
			kpgz_code as kpgz_code,
			kpgz_name as kpgz_name,
			spgz_code as spgz_code,
			spgz_name as spgz_name
		from kpgz_spgz
		"""

		rows = self.sql_client.select(sql)
		batch_size = 10000
		action = {'create': {'_index': 'kpgz'}}
		for batch in batched(rows, batch_size):
			bulk_body = []
			for row in batch:
				bulk_body.append(action)
				bulk_body.append({
					'kpgz_code': row.get('kpgz_code', ''),
					'kpgz_name': row.get('kpgz_name', ''),
					'spgz_code': row.get('spgz_code', ''),
					'spgz_name': row.get('spgz_name', ''),
				})

			self.client.bulk(
				index='kpgz', 
				body=ndjson.dumps(bulk_body, ensure_ascii=False)
			)

	def search_kpgz(self, text: str, k: int = 5):
		response = self.client.search(
			index='kpgz',
			body={
				'size': k,
				'query': {
					'multi_match': {
						'query': text,
						'fields': ['kpgz_name', 'spgz_name^2']
					}
				}
			}
		)
		return [hit['_source'] for hit in response['hits']['hits']]

	def create_storage_costs_index(self, drop: bool = False):
		if self.client.indices.exists(index='storage_costs'):
			if not drop:
				return
			self.client.indices.delete(index='storage_costs')

		self.client.indices.create(index='storage_costs', body={
			"settings": {
				"number_of_shards": 1,
				"number_of_replicas": 1
			},
			"mappings": {
				"dynamic": False,
				"properties": {
					"category": { "type": "text" },
					"avg_turnovers_credit_quantity": { "type": "float" },
					"avg_turnovers_credit_price": { "type": "float" },
					"last_saldo_end_debit_quantity": { "type": "float" },
					"last_saldo_end_debit_price": { "type": "float" },
				}
			}
		})

		sql = """
		select 	spgz_name as category,
				round(avg(turnovers_credit_quantity), 2) as avg_turnovers_credit_quantity,
				round(avg(turnovers_credit_price), 2) as avg_turnovers_credit_price,
				round(max(last_saldo_end_debit_quantity), 2) as last_saldo_end_debit_quantity,
				round(max(last_saldo_end_debit_price), 2) as last_saldo_end_debit_price
			from financial_quarter_data
			group by spgz_name
		"""

		rows = self.sql_client.select(sql)
		batch_size = 10000
		action = {'create': {'_index': 'storage_costs'}}
		for batch in batched(rows, batch_size):
			bulk_body = []
			for row in batch:
				bulk_body.append(action)
				bulk_body.append({
					"category": row.get('category', ''),
					"avg_turnovers_credit_quantity": row.get('avg_turnovers_credit_quantity', 0),
					"avg_turnovers_credit_price": row.get('avg_turnovers_credit_price', 0),
					"last_saldo_end_debit_quantity": row.get('last_saldo_end_debit_quantity', 0),
					"last_saldo_end_debit_price": row.get('last_saldo_end_debit_price', 0),
				})

			self.client.bulk(
				index='storage_costs', 
				body=ndjson.dumps(bulk_body, ensure_ascii=False)
			)

	def search_storage_costs(self, text: str, k: int = 5):
		response = self.client.search(
			index='storage_costs',
			body={
				'size': k,
				'query': {
					'match': {
						'category': {
							'query': text,
						}
					}
				}
			},
		)
		return [hit['_source'] for hit in response['hits']['hits']]

	def create_contracts_index(self, drop: bool = False):
		if self.client.indices.exists(index='contracts'):
			if not drop:
				return
			self.client.indices.delete(index='contracts')

		self.client.indices.create(index='contracts', body={
			"settings": {
				"number_of_shards": 1,
				"number_of_replicas": 1
			},
			"mappings": {
				"dynamic": False,
				"properties": {
					"category": { "type": "text" },
					"avg_contracts_price": { "type": "float" },
					"avg_contracts_delta": { "type": "float" },
					"avg_price_per_day": { "type": "float" },
					"first_contract_date": { "type": "date" },
					"last_contract_date": { "type": "date" }
				}
			}
		})

		sql = """
		select 	spgz_name as category,
				round(avg(contracts_price), 2) as avg_contracts_price,
				ceil(avg(next_contracts_delta)) as avg_contracts_delta,
				round(avg(contracts_price) / avg(next_contracts_delta), 2) as avg_price_per_day,
				min(contract_date) as first_contract_date,
				max(contract_date) as last_contract_date
			from procurement_contracts_date_data
			group by spgz_name;
		"""

		rows = self.sql_client.select(sql)
		batch_size = 10000
		action = {'create': {'_index': 'contracts'}}
		for batch in batched(rows, batch_size):
			bulk_body = []
			for row in batch:
				bulk_body.append(action)
				bulk_body.append({
					"category": row.get('category', ''),
					"avg_contracts_price": row.get('avg_contracts_price', 0),
					"avg_contracts_delta": row.get('avg_contracts_delta', 0),
					"avg_price_per_day": row.get('avg_price_per_day', 0),
					"first_contract_date": row.get('first_contract_date', ''),
					"last_contract_date": row.get('last_contract_date', ''),
				})

			self.client.bulk(
				index='contracts', 
				body=ndjson.dumps(bulk_body, ensure_ascii=False)
			)

	def search_contracts(self, text: str, k: int = 5):
		response = self.client.search(
			index='contracts',
			body={
				'size': k,
				'query': {
					'match': {
						'category': {
							'query': text,
						}
					}
				}
			},
		)
		return [hit['_source'] for hit in response['hits']['hits']]
