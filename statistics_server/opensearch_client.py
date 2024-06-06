from opensearchpy import OpenSearch

from psql_client import PSQLClient


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
		if drop:
			self.client.indices.delete(index='kpgz')

		if self.client.indices.exists(index='kpgz'):
			return

		self.client.indices.create(index='kpgz', body={
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
			(row_number() over())::text as row_id,
			coalesce(ste_name, '') as ste_name,
			coalesce(characteristic_name, '') as characteristics,
			coalesce(kpgz_code, '') as kpgz_code,
			coalesce(kpgz, '') as kpgz_name,
			coalesce(spgz_code::text, '') as spgz_code,
			coalesce(spgz, '') as spgz_name
		from kpgz
		"""

		rows = self.sql_client.select(sql)
		for i, row in enumerate(rows, start=1):
			refresh = True if i == len(rows) else False
			self.client.index(
				index='kpgz',
				refresh=refresh,
				id=row['row_id'],
				body={
					'ste_name': row['ste_name'],
					'characteristics': row['characteristics'],
					'kpgz_code': row['kpgz_code'],
					'kpgz_name': row['kpgz_name'],
					'spgz_code': row['spgz_code'],
					'spgz_name': row['spgz_name'],
				}
			)

	def search_kpgz(self, text: str, k: int = 5):
		response = self.client.search(
			index='kpgz',
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
