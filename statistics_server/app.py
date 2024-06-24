import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.absolute()))

import json

from flask import Flask, request, Response
from keycloak import KeycloakOpenID

from stats_calculator import StatsCalculator
from config import Config


app = Flask(__name__)
cfg = Config.load()
stats_calculator = StatsCalculator()
keycloak_openid = KeycloakOpenID(
	server_url=cfg.keycloak_server_url,
	client_id=cfg.keycloak_client_id,
	realm_name=cfg.keycloak_realm_name,
	client_secret_key=cfg.keycloak_client_secret
)


@app.route('/search_kpgz', methods=['GET'])
def search_kpgz():
	data = json.loads(request.get_data())
	text = data.get('text', '')
	k = data.get('k', 5)
	result = stats_calculator.search_kpgz(text, k)
	return Response(
		response=json.dumps(result, ensure_ascii=False), 
		status=200,
		content_type='application/json',
	)

@app.route('/search_storage_costs', methods=['GET'])
def search_storage_costs():
	data = json.loads(request.get_data())
	text = data.get('text', '')
	k = data.get('k', 5)
	result = stats_calculator.search_storage_costs(text, k)
	return Response(
		response=json.dumps(result, ensure_ascii=False), 
		status=200,
		content_type='application/json',
	)

@app.route('/search_contracts', methods=['GET'])
def search_contracts():
	data = json.loads(request.get_data())
	text = data.get('text', '')
	k = data.get('k', 5)
	result = stats_calculator.search_contracts(text, k)
	return Response(
		response=json.dumps(result, ensure_ascii=False), 
		status=200,
		content_type='application/json',
	)

@app.route('/search_restrictions', methods=['GET'])
def search_restrictions():
	data = json.loads(request.get_data())
	text = data.get('text', '')
	k = data.get('k', 5)
	result = stats_calculator.search_restrictions(text, k)
	return Response(
		response=json.dumps(result, ensure_ascii=False), 
		status=200,
		content_type='application/json',
	)

@app.route('/financial_quarter_data', methods=['GET'])
def get_financial_quarter_data():
	data = json.loads(request.get_data())
	if 'spgz_name' not in data:
		return Response(
			response=json.dumps({'error': 'Need field spgz_name'} , ensure_ascii=False),
			status=400,
			content_type='application/json',
		)

	spgz_name = data.get('spgz_name', '')
	date_grain = data.get('date_grain', 'month')
	result = stats_calculator.select_financial_quarter_data(spgz_name, date_grain)
	return Response(
		response=json.dumps(result, ensure_ascii=False), 
		status=200,
		content_type='application/json',
	)

@app.route('/procurement_contracts_date_data', methods=['GET'])
def get_procurement_contracts_date_data():
	data = json.loads(request.get_data())
	if 'spgz_name' not in data:
		return Response(
			response=json.dumps({'error': 'Need field spgz_name'} , ensure_ascii=False), 
			status=400,
			content_type='application/json',
		)

	spgz_name = data.get('spgz_name', '')
	date_grain = data.get('date_grain', 'month')
	result = stats_calculator.select_procurement_contracts_date_data(spgz_name, date_grain)
	return Response(
		response=json.dumps(result, ensure_ascii=False), 
		status=200,
		content_type='application/json',
	)

@app.route('/last_contract', methods=['GET'])
def get_last_contract():
	data = json.loads(request.get_data())
	if 'spgz_name' not in data:
		return Response(
			response=json.dumps({'error': 'Need field spgz_name'} , ensure_ascii=False), 
			status=400,
			content_type='application/json',
		)

	spgz_name = data.get('spgz_name', '')
	result = stats_calculator.select_last_contract(spgz_name)
	return Response(
		response=json.dumps(result, ensure_ascii=False), 
		status=200,
		content_type='application/json',
	)

@app.route('/create_contract', methods=['GET'])
def create_contract():
	data = json.loads(request.get_data())
	if len({'spgz_name', 'login', 'password'} & set(data)) != 3:
		return Response(
			response=json.dumps({'error': 'Need fields spgz_name, login, password'}), 
			status=400,
			content_type='application/json',
		)

	try:
		keycloak_openid.token(data['login'], data['password'])
	except:
		return Response(
			response=json.dumps({'error': 'Login or password is incorrect'}), 
			status=403,
			content_type='application/json',
		)

	spgz_name = data.get('spgz_name', '')
	spgz_name = stats_calculator.search_contracts(spgz_name, 1)[0]['spgz_name']
	result = stats_calculator.create_contract_json(spgz_name)
	return Response(
		response=json.dumps(result, ensure_ascii=False), 
		status=200,
		content_type='application/json',
	)

@app.route('/prognoze_financial_quarter', methods=['GET'])
def prognoze_financial_quarter():
	data = json.loads(request.get_data())
	if 'spgz_name' not in data:
		return Response(
			response=json.dumps({'error': 'Need field spgz_name'} , ensure_ascii=False), 
			status=400,
			content_type='application/json',
		)

	spgz_name = data.get('spgz_name', '')
	date_grain = data.get('date_grain', 'month')
	result = stats_calculator.prognoze_financial_quarter_data(spgz_name, date_grain)
	return Response(
		response=json.dumps(result, ensure_ascii=False), 
		status=200,
		content_type='application/json',
	)

@app.route('/grafic_dynamics_financial_quantity', methods=['GET'])
def grafic_dynamics_financial_quantity():
	data = json.loads(request.get_data())
	if 'spgz_name' not in data:
		return Response(
			response=json.dumps({'error': 'Need field spgz_name'} , ensure_ascii=False), 
			status=400,
			content_type='application/json',
		)

	spgz_name = data.get('spgz_name', '')
	date_grain = data.get('date_grain', 'quarter')
	img_buf, status = stats_calculator.create_grafic_dynamics_financial_quantity(spgz_name, date_grain)
	if status:
		return Response(
			response=json.dumps({'img': img_buf}, ensure_ascii=False), 
			status=200,
			content_type='application/json',
		)
	else:
		return Response(
			status=400,
			content_type='application/json',
		)

@app.route('/grafic_dynamics_financial_price', methods=['GET'])
def grafic_dynamics_financial_price():
	data = json.loads(request.get_data())
	if 'spgz_name' not in data:
		return Response(
			response=json.dumps({'error': 'Need field spgz_name'} , ensure_ascii=False), 
			status=400,
			content_type='application/json',
		)

	spgz_name = data.get('spgz_name', '')
	date_grain = data.get('date_grain', 'quarter')
	img_buf, status = stats_calculator.create_grafic_dynamics_financial_price(spgz_name, date_grain)
	if status:
		return Response(
			response=json.dumps({'img': img_buf}, ensure_ascii=False), 
			status=200,
			content_type='application/json',
		)
	else:
		return Response(
			status=400,
			content_type='application/json',
		)

@app.route('/grafic_dynamics_financial_prognoze', methods=['GET'])
def grafic_dynamics_financial_prognoze():
	data = json.loads(request.get_data())
	if 'spgz_name' not in data:
		return Response(
			response=json.dumps({'error': 'Need field spgz_name'} , ensure_ascii=False), 
			status=400,
			content_type='application/json',
		)

	spgz_name = data.get('spgz_name', '')
	date_grain = data.get('date_grain', 'quarter')
	img_buf = stats_calculator.create_grafic_dynamics_financial_prognoze(spgz_name, date_grain)
	return Response(
		response=json.dumps({'img': img_buf}, ensure_ascii=False), 
		status=200,
		content_type='application/json',
	)

@app.route('/prognoze_contracts', methods=['GET'])
def prognoze_contracts():
	data = json.loads(request.get_data())
	if 'spgz_name' not in data:
		return Response(
			response=json.dumps({'error': 'Need field spgz_name'} , ensure_ascii=False), 
			status=400,
			content_type='application/json',
		)

	spgz_name = data.get('spgz_name', '')
	date_grain = data.get('date_grain', 'month')
	result = stats_calculator.prognoze_contracts(spgz_name, date_grain)
	return Response(
		response=json.dumps(result, ensure_ascii=False), 
		status=200,
		content_type='application/json',
	)

@app.route('/grafic_dynamics_contracts_prognoze', methods=['GET'])
def grafic_dynamics_contracts_prognoze():
	data = json.loads(request.get_data())
	if 'spgz_name' not in data:
		return Response(
			response=json.dumps({'error': 'Need field spgz_name'} , ensure_ascii=False), 
			status=400,
			content_type='application/json',
		)

	spgz_name = data.get('spgz_name', '')
	date_grain = data.get('date_grain', 'month')
	img_buf = stats_calculator.create_grafic_dynamics_contracts_prognoze(spgz_name, date_grain)
	return Response(
		response=json.dumps({'img': img_buf}, ensure_ascii=False), 
		status=200,
		content_type='application/json',
	)

# @app.route('/user', methods=['PUT'])
# def add_user():
# 	data = json.loads(request.get_data())
# 	must_fields = 'username department permission_admin permission_forecast permission_json password'.split()
# 	if any(must_field not in data for must_field in must_fields):
# 		return Response(
# 			response=json.dumps({'error': f'Need fields {must_fields}'} , ensure_ascii=False), 
# 			status=400,
# 			content_type='application/json',
# 		)

# 	username = data['username']
# 	department = data['department']
# 	permission_admin = data['permission_admin']
# 	permission_forecast = data['permission_forecast']
# 	permission_json = data['permission_json']
# 	password = data['password']
# 	result = stats_calculator.add_user(
# 		username=username,
# 		department=department,
# 		permission_admin=permission_admin,
# 		permission_forecast=permission_forecast,
# 		permission_json=permission_json,
# 		password=password,
# 	)

# 	if not result:
# 		return Response(
# 			response=json.dumps({'error': f'Internal error'} , ensure_ascii=False), 
# 			status=500,
# 			content_type='application/json',
# 		)

# 	return Response(
# 		status=200,
# 		content_type='application/json',
# 	)

# @app.route('/user', methods=['GET'])
# def get_user():
# 	data = json.loads(request.get_data())
# 	if 'username' not in data:
# 		return Response(
# 			response=json.dumps({'error': f'Need field "username"'} , ensure_ascii=False), 
# 			status=400,
# 			content_type='application/json',
# 		)

# 	username = data['username']
# 	users = stats_calculator.get_user(username=username)
# 	if not users:
# 		return Response(
# 			response=json.dumps({'result': 'User not found'}, ensure_ascii=False),
# 			status=200,
# 			content_type='application/json',
# 		)

# 	user = users[0]
# 	return Response(
# 		response=json.dumps({
# 			'username': user.get('username', ''),
# 			'department': user.get('department', ''),
# 			'permission_admin': user.get('permission_admin', ''),
# 			'permission_forecast': user.get('permission_forecast', ''),
# 			'permission_json': user.get('permission_json', ''),
# 			'password': user.get('password', ''),
# 		}, ensure_ascii=False),
# 		status=200,
# 		content_type='application/json',
# 	)

# @app.route('/user', methods=['DELETE'])
# def del_user():
# 	data = json.loads(request.get_data())
# 	if 'username' not in data or 'password' not in data:
# 		return Response(
# 			response=json.dumps({'error': f'Need field "username"'} , ensure_ascii=False), 
# 			status=400,
# 			content_type='application/json',
# 		)

# 	username = data['username']
# 	password = data['password']

# 	users = stats_calculator.get_user(username=username)
# 	if not users or users[0].get('password') != password:
# 		return Response(
# 			response=json.dumps({'error': f'Incorrect password'} , ensure_ascii=False), 
# 			status=200,
# 			content_type='application/json',
# 		)

# 	result = stats_calculator.del_user(username=username)
# 	if not result:
# 		return Response(
# 			response=json.dumps({'error': f'Internal error'} , ensure_ascii=False), 
# 			status=500,
# 			content_type='application/json',
# 		)

# 	return Response(
# 		status=200,
# 		content_type='application/json',
# 	)


if __name__ == '__main__':
	app.run(host='0.0.0.0', port=5000, debug=True)
