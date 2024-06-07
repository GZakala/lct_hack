

CREATE TABLE public.procurement_contracts (
	spgz_id int4 NULL,
	spgz_name text NULL,
	reg_num int4 NULL,
	lot_number int4 NULL,
	ikz text NULL,
	customer text NULL,
	contract_subject text NULL,
	supplier_selection_method text NULL,
	contract_basis text NULL,
	contract_status text NULL,
	version_number int4 NULL,
	contract_price numeric(15, 2) NULL,
	initial_contract_price numeric(15, 2) NULL,
	paid_amount numeric(15, 2) NULL,
	paid_percentage numeric(5, 2) NULL,
	final_kpgz_code text NULL,
	final_kpgz_name text NULL,
	contract_date date NULL,
	registration_date date NULL,
	last_modified_date date NULL,
	execution_start_date date NULL,
	execution_end_date date NULL,
	contract_expiry_date date NULL,
	msp_inclusion text NULL,
	supplier_region text NULL,
	legal_basis text NULL,
	electronic_execution text NULL,
	fulfilled_by_supplier text NULL
);
--insert data

create table procurement_contracts_new
as
select 
	reg_num::text as contract_id,
	lot_number,
	contract_status,
	version_number,
	contract_price,
	initial_contract_price,
	paid_amount,
	paid_percentage,
	(case when fulfilled_by_supplier = '' then '0' else fulfilled_by_supplier end)::float as fulfilled_by_supplier_price,
	contract_basis,
	contract_subject,
	ikz,
	supplier_selection_method,
	customer,
	contract_date,
	registration_date,
	last_modified_date,
	execution_start_date,
	execution_end_date,
	contract_expiry_date,
	spgz_id::text as spgz_code,
	spgz_name as spgz_name,
	final_kpgz_code as kpgz_code,
	final_kpgz_name as kpgz_name,
	msp_inclusion as msp,
	supplier_region,
	legal_basis as fz,
	electronic_execution
from procurement_contracts;

drop table procurement_contracts;
alter table procurement_contracts_new rename to procurement_contracts;

select *
	from procurement_contracts;

select count(*), count(distinct t.*)
	from procurement_contracts t;
--3699	2995

create table procurement_contracts_new
as
select distinct *
	from procurement_contracts;

drop table procurement_contracts;
alter table procurement_contracts_new rename to procurement_contracts;

select 
	count(*), 
	count(distinct t.*), 
	count(distinct coalesce(contract_id, '')||coalesce(lot_number, 0)||coalesce(spgz_code, '')||coalesce(kpgz_code, ''))
from procurement_contracts t;
--2995	2995	2995