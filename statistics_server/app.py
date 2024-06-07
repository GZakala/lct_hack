import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.absolute()))

import json

from flask import Flask, request, Response

from stats_calculator import StatsCalculator


app = Flask(__name__)
stats_calculator = StatsCalculator()


@app.route('/select_balances_accaunt_101', methods=['GET'])
def select_balances_accaunt_101():
	data = json.loads(request.get_data())
	limit = data.get('limit', 10)
	result = stats_calculator.select_balances_accaunt_101(limit=limit)
	return Response(
		response=json.dumps(result, ensure_ascii=False), 
		status=200,
		content_type='application/json',
	)

@app.route('/search_ste', methods=['GET'])
def search_ste():
	data = json.loads(request.get_data())
	text = data.get('text', '')
	k = data.get('k', 5)
	result = stats_calculator.search_ste(text, k)
	return Response(
		response=json.dumps(result, ensure_ascii=False), 
		status=200,
		content_type='application/json',
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

if __name__ == '__main__':
	app.run(host='0.0.0.0', port=5000, debug=True)
