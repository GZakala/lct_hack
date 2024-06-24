from flask_appbuilder.security.manager import AUTH_OAUTH

FEATURE_FLAGS = {
        'ENABLE_TEMPLATE_PROCESSING': True,
}

# Enable OAuth authentication
AUTH_TYPE = AUTH_OAUTH
LOGOUT_REDIRECT_URL='https://auth.cosahack.ru/realms/master/protocol/openid-connect/logout'
LOGIN_REDIRECT_URL='https://auth.cosahack.ru/realms/master/protocol/openid-connect/auth'
AUTH_USER_REGISTRATION = True
AUTH_USER_REGISTRATION_ROLE = 'Admin'
# OAuth provider configuration for Keycloak
OAUTH_PROVIDERS = [
    {
        'name': 'keycloak',
        'token_key': 'access_token',  # Keycloak uses 'access_token' for the access token
        'remote_app': {
            'client_id': 'superset',
            'client_secret': 'muKqP52DtY6tK39I8pXHP6zcVVuiT3FE',
			'api_base_url': 'https://auth.cosahack.ru/realms/master/protocol/openid-connect',
            'client_kwargs': {
                'scope': 'openid profile email',
            },
            'access_token_url': 'https://auth.cosahack.ru/realms/master/protocol/openid-connect/token',
            'userinfo_uri': 'https://auth.cosahack.ru/realms/master/protocol/openid-connect/userinfo',
            'authorize_url': 'https://auth.cosahack.ru/realms/master/protocol/openid-connect/auth',
			"request_token_url": None,
			'jwks_uri': 'https://auth.cosahack.ru/realms/master/protocol/openid-connect/certs',
        },
    }
]
