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

if __name__ == '__main__':
	app.run(host='0.0.0.0', port=50550, debug=True)
