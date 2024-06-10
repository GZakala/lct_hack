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

	def create_ste_index(self, drop: bool = False):
		if self.client.indices.exists(index='ste'):
			if not drop:
				return
			self.client.indices.delete(index='ste')

		self.client.indices.create(index='ste', body={
			"settings": {
				"number_of_shards": 1,
				"number_of_replicas": 1
			},
			"mappings": {
				"dynamic": False,
				"properties": {
				"ste_name": { "type": "text" },
				"characteristics": { "type": "text" },
				"kpgz_code": { "type": "keyword" },
				"kpgz_name": { "type": "text" },
				"spgz_code": { "type": "keyword" },
				"spgz_name": { "type": "text" }
				}
			}
		})

		sql = """
		select 	
			coalesce(ste_name, '') as ste_name,
			coalesce(characteristic_name, '') as characteristics,
			coalesce(kpgz_code, '') as kpgz_code,
			coalesce(kpgz, '') as kpgz_name,
			coalesce(spgz_code::text, '') as spgz_code,
			coalesce(spgz, '') as spgz_name
		from ste_data
		"""

		rows = self.sql_client.select(sql)
		batch_size = 10000
		action = {'create': {'_index': 'ste'}}
		for batch in batched(rows, batch_size):
			bulk_body = []
			for row in batch:
				bulk_body.append(action)
				bulk_body.append({
					'ste_name': row.get('ste_name', ''),
					'characteristics': row.get('characteristics', ''),
					'kpgz_code': row.get('kpgz_code', ''),
					'kpgz_name': row.get('kpgz_name', ''),
					'spgz_code': row.get('spgz_code', ''),
					'spgz_name': row.get('spgz_name', ''),
				})

			self.client.bulk(
				index='ste', 
				body=ndjson.dumps(bulk_body, ensure_ascii=False)
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
				"contract_id": { "type": "keyword" },
				"contract_date": { "type": "date" },
				"lot_number": { "type": "keyword" },
				"spgz_code": { "type": "keyword" },
				"spgz_name": { "type": "text" },
				"kpgz_code": { "type": "keyword" },
				"kpgz_name": { "type": "text" },
				"contract_subject": { "type": "text" },
				}
			}
		})

		sql = """
		select 
			coalesce(contract_id, '') as contract_id, 
			contract_date as contract_date, 
			lot_number, 
			coalesce(spgz_code, '') as spgz_code, 
			coalesce(spgz_name, '') as spgz_name, 
			coalesce(kpgz_code, '') as kpgz_code, 
			coalesce(kpgz_name, '') as kpgz_name, 
			coalesce(contract_subject, '') as contract_subject
		from procurement_contracts;
		"""

		rows = self.sql_client.select(sql)
		batch_size = 10000
		action = {'create': {'_index': 'contracts'}}
		for batch in batched(rows, batch_size):
			bulk_body = []
			for row in batch:
				bulk_body.append(action)
				bulk_body.append({
					"contract_id": row.get('contract_id', ''),
					"contract_date": str(row.get('contract_date', '')),
					"lot_number": row.get('lot_number', ''),
					"spgz_code": row.get('spgz_code', ''),
					"spgz_name": row.get('spgz_name', ''),
					"kpgz_code": row.get('kpgz_code', ''),
					"kpgz_name": row.get('kpgz_name', ''),
					"contract_subject": row.get('contract_subject', ''),
				})

			self.client.bulk(
				index='contracts', 
				body=ndjson.dumps(bulk_body, ensure_ascii=False)
			)

	def search_ste(self, text: str, k: int = 5):
		response = self.client.search(
			index='ste',
			body={
				'size': k,
				'query': {
					'multi_match': {
						'query': text,
						'fields': [
							'ste_name^2', 
							'characteristics', 
							'kpgz_name', 
							'spgz_name',
						]
					}
				}
			}
		)
		return [hit['_source'] for hit in response['hits']['hits']]

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

	def search_contracts(self, text: str, k: int = 5):
		response = self.client.search(
			index='contracts',
			body={
				'size': k,
				'query': {
					'multi_match': {
						'query': text,
						'fields': ['spgz_name^4', 'contract_subject']
					}
				}
				# 'filter': { 
				# 	'bool': {
				# 		'filter': [
				# 			{ 
				# 				'range': { 
				# 					'contact_date': {
				# 						'gte': '2018-01-01', 
				# 						'lt': '2020-01-01',
				# 					}
				# 				}
				# 			}
				# 		],
				# 		'must': [
				# 			{ 'match': { 'spgz_name': text} },
				# 		],
				# 	},
				# },
			},
		)
		return [hit['_source'] for hit in response['hits']['hits']]
