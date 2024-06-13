create table procurement_contracts_date_data
as
select 	spgz_name,
				contract_date,
				sum(contract_price) as contracts_price,
				coalesce(
					lead(contract_date) over(partition by spgz_name order by contract_date) - contract_date,
					'2023-01-01' - max(contract_date) over(partition by spgz_name)
				) as next_contracts_delta
	from procurement_contracts
	group by spgz_name, contract_date
	order by spgz_name, contract_date;
