with dates as (
select distinct date_trunc('{{ date_grain }}', generate_series('2018-01-09'::date, '2023-01-01', interval '1 day')) as date
),
contracts_raw_delta as (
select 	
	spgz_name,
	date_trunc('{{ date_grain }}', contract_date) as contract_date,
	sum(contracts_price) as contracts_price,
	coalesce(
		age(lead(date_trunc('{{ date_grain }}', contract_date)) over(order by date_trunc('{{ date_grain }}', contract_date)), date_trunc('{{ date_grain }}', contract_date)),
		age('2023-01-01'::date, date_trunc('{{ date_grain }}', contract_date))
	) as delta
from procurement_contracts_date_data
where spgz_name = '{{ spgz_name }}'
group by spgz_name, date_trunc('{{ date_grain }}', contract_date)
),
contracts as (
select 
	spgz_name,
	contract_date,
	contracts_price,
	extract(year from delta)*12 + extract(month from delta) as delta
from contracts_raw_delta
)
select 	
	'{spgz_name}' as spgz_name,
	t.date as contract_date,
	coalesce(contracts_price, 0) as contracts_price,
	coalesce(tt.delta, 0) as delta,
	case 
		when coalesce(tt.delta, 0) = 0 then 0 
		else round(coalesce(contracts_price, 0) / coalesce(tt.delta, 0), 2) 
	end as price_per_1_delta
from dates t
left join contracts tt on t.date = tt.contract_date
order by t.date
;
