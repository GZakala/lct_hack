import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.absolute()))

import json

from flask import Flask, request, Response

from stats_calculator import StatsCalculator


app = Flask(__name__)
stats_calculator = StatsCalculator()


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


if __name__ == '__main__':
	app.run(host='0.0.0.0', port=5000, debug=True)
