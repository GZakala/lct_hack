select 	'{{ spgz_name }}' as spgz_name,
		t.date as contract_date,
		coalesce(contracts_price, 0) as contracts_price
	from 
	(
	select distinct date_trunc('{{ date_grain }}', generate_series('2018-01-09'::date, '2023-01-01', interval '1 day')) as date
	) t
	left join
	(
	select 	spgz_name,
			date_trunc('{{ date_grain }}', contract_date) as contract_date,
			sum(contracts_price) as contracts_price
		from procurement_contracts_date_data
		where spgz_name = '{{ spgz_name }}'
		group by spgz_name, date_trunc('{{ date_grain }}', contract_date)
	) tt
	on t.date = tt.contract_date
	order by t.date;
