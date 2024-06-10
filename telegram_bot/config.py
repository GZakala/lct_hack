import os

class Config:
	def __init__(
		self,
		keycloak_server_url: str,
		keycloak_realm_name: str,
		keycloak_client_id: str,
		keycloak_client_secret: str,
		keycloak_redirect_uri: str,
		api_token: str,
	):
		self.keycloak_server_url = keycloak_server_url
		self.keycloak_realm_name = keycloak_realm_name
		self.keycloak_client_id = keycloak_client_id
		self.keycloak_client_secret = keycloak_client_secret
		self.keycloak_redirect_uri = keycloak_redirect_uri
		self.api_token = api_token

	@classmethod
	def load(cls):
		return cls(
			keycloak_server_url=os.getenv("KEYCLOAK_SERVER_URL"),
			keycloak_realm_name=os.getenv("KEYCLOAK_REALM_NAME"),
			keycloak_client_id=os.getenv("KEYCLOAK_CLIENT_ID"),
			keycloak_client_secret=os.getenv("KEYCLOAK_CLIENT_SECRET"),
			keycloak_redirect_uri=os.getenv("KEYCLOAK_REDIRECT_URI"),
			api_token=os.getenv("API_TOKEN"),
		)
