create table financial_quarter_data
as
with 
spgz_report_all as (
select *
		from 	(select distinct spgz_name from procurement_contracts), 
					(select distinct report_date from financial_data)
), 
financial as (
select tt.spgz_name, t.*
	from financial_data t
	left join procurement_contracts tt 
		on t.contract_id_match_1 = tt.contract_id 
		and t.lot_number_match_1 = tt.lot_number::text
), financial_all_data as (
select 	t.spgz_name, t.report_date,
				coalesce(tt.turnovers_debit_quantity, 0) as turnovers_debit_quantity,
				coalesce(tt.turnovers_debit_price, 0) as turnovers_debit_price,
				coalesce(tt.turnovers_credit_quantity, 0) as turnovers_credit_quantity,
				coalesce(tt.turnovers_credit_price, 0) as turnovers_credit_price,
				coalesce(tt.saldo_end_debit_quantity, 0) as saldo_end_debit_quantity,
				coalesce(tt.saldo_end_debit_price, 0) as saldo_end_debit_price
	from spgz_report_all t
	left join financial tt on t.spgz_name = tt.spgz_name and t.report_date = tt.report_date
)
select 	spgz_name,
				date_trunc('quarter', report_date) as start_report_date_quarter,
				sum(turnovers_debit_quantity) as turnovers_debit_quantity,
				sum(turnovers_debit_price) as turnovers_debit_price,
				sum(turnovers_credit_quantity) as turnovers_credit_quantity,
				sum(turnovers_credit_price) as turnovers_credit_price,
				sum(saldo_end_debit_quantity) as saldo_end_debit_quantity,
				sum(saldo_end_debit_price) as saldo_end_debit_price,
 				first_value(sum(saldo_end_debit_quantity)) over(partition by spgz_name order by report_date desc) as last_saldo_end_debit_quantity,
				first_value(sum(saldo_end_debit_price)) over(partition by spgz_name order by report_date desc) as last_saldo_end_debit_price
	from financial_all_data
	group by spgz_name, report_date
	order by spgz_name, start_report_date_quarter;
