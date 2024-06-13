select 	spgz_name,
		date_trunc('{{ date_grain }}', start_report_date_quarter) as report_date,
		sum(turnovers_credit_quantity) as turnovers_credit_quantity,
		sum(turnovers_credit_price) as turnovers_credit_price,
		sum(saldo_end_debit_quantity) as saldo_end_debit_quantity,
		sum(saldo_end_debit_price) as saldo_end_debit_price,
		max(last_saldo_end_debit_quantity) as last_saldo_end_debit_quantity,
		max(last_saldo_end_debit_price) as last_saldo_end_debit_price
	from financial_quarter_data
	where spgz_name = '{{ spgz_name }}'
	group by spgz_name, date_trunc('{{ date_grain }}', start_report_date_quarter)
	order by spgz_name, date_trunc('{{ date_grain }}', start_report_date_quarter);
