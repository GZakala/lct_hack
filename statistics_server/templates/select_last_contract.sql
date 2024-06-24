select *
	from procurement_contracts
	where contract_id = (
		select unnest(contract_ids) as contract_id
			from procurement_contracts_date_data
			where spgz_name = '{{ spgz_name }}'
			order by contract_date desc
			limit 1
	)
