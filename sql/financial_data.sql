CREATE TABLE public.financial_data_101 (
	account_number int4 NULL,
	report_date date NULL,
	responsible_person varchar(255) NULL,
	responsible_person_id int4 NULL,
	subcategory_by_account_number numeric(10, 2) NULL,
	item_name varchar(255) NULL,
	ref_code varchar(50) NULL,
	metric varchar(50) NULL,
	saldo_start_debit numeric(15, 2) NULL,
	saldo_start_credit numeric(15, 2) NULL,
	turnovers_debit numeric(15, 2) NULL,
	turnovers_credit numeric(15, 2) NULL,
	saldo_end_debit numeric(15, 2) NULL,
	saldo_end_credit numeric(15, 2) NULL
);
--insert data

CREATE TABLE public.financial_data_105 (
	account_number int4 NULL,
	report_date date NULL,
	responsible_person varchar(255) NULL,
	responsible_person_id int4 NULL,
	subcategory_by_account_number numeric(10, 2) NULL,
	item_name varchar(255) NULL,
	ref_code varchar(50) NULL,
	metric varchar(50) NULL,
	saldo_start_debit numeric(15, 2) NULL,
	saldo_start_credit numeric(15, 2) NULL,
	turnovers_debit numeric(15, 2) NULL,
	turnovers_credit numeric(15, 2) NULL,
	saldo_end_debit numeric(15, 2) NULL,
	saldo_end_credit numeric(15, 2) NULL
);
--insert data

CREATE TABLE public.financial_data_21 (
	account_number int4 NULL,
	report_date date NULL,
	responsible_person varchar(255) NULL,
	responsible_person_id int4 NULL,
	subcategory_by_account_number numeric(10, 2) NULL,
	item_name varchar(255) NULL,
	ref_code varchar(50) NULL,
	metric varchar(50) NULL,
	saldo_start_debit numeric(15, 2) NULL,
	saldo_start_credit numeric(15, 2) NULL,
	turnovers_debit numeric(15, 2) NULL,
	turnovers_credit numeric(15, 2) NULL,
	saldo_end_debit numeric(15, 2) NULL,
	saldo_end_credit numeric(15, 2) NULL
);
--insert data



create table financial_data
as
select *
	from financial_data_101
union
select *
	from financial_data_105
union
select *
	from financial_data_21;

select *
	from financial_data;

create table financial_data_new
as
select 
 	row_number() over() as id,
	account_number, 
	subcategory_by_account_number,
	report_date,
	responsible_person_id,
	responsible_person,
	ref_code,
	item_name,
	max(case when metric = 'Кол.' then saldo_start_debit else null end) as saldo_start_debit_quantity,
	max(case when metric = 'Кол.' then saldo_start_credit else null end) as saldo_start_credit_quantity,
	max(case when metric = 'Кол.' then turnovers_debit else null end) as turnovers_debit_quantity,
	max(case when metric = 'Кол.' then turnovers_credit else null end) as turnovers_credit_quantity,
	max(case when metric = 'Кол.' then saldo_end_debit else null end) as saldo_end_debit_quantity,
	max(case when metric = 'Кол.' then saldo_end_credit else null end) as saldo_end_credit_quantity,
	max(case when metric = 'Сумма' then saldo_start_debit else null end) as saldo_start_debit_prcice,
	max(case when metric = 'Сумма' then saldo_start_credit else null end) as saldo_start_credit_prcice,
	max(case when metric = 'Сумма' then turnovers_debit else null end) as turnovers_debit_prcice,
	max(case when metric = 'Сумма' then turnovers_credit else null end) as turnovers_credit_prcice,
	max(case when metric = 'Сумма' then saldo_end_debit else null end) as saldo_end_debit_prcice,
	max(case when metric = 'Сумма' then saldo_end_credit else null end) as saldo_end_credit_prcice
from financial_data
group by 	account_number, 
					subcategory_by_account_number,
					report_date,
					responsible_person_id,
					responsible_person,
					ref_code,
					item_name;

drop table financial_data;
alter table financial_data_new rename to financial_data;

select *
	from financial_data;

select 
	count(*), 
	count(distinct t.*), 
	count(distinct coalesce(account_number)||coalesce(item_name)||coalesce(subcategory_by_account_number)||coalesce(report_date::text)||coalesce(ref_code))
from financial_data t;
--3580	3580	3580



-- drop table financial_data_101;
-- drop table financial_data_105;
-- drop table financial_data_21;

-- CREATE TABLE public.financial_data (
-- 	contract_id_match_1 text NULL,
-- 	lot_number_match_1 text NULL,
-- 	contract_id_match_2 text NULL,
-- 	lot_number_match_2 text NULL,
-- 	id int8 NULL,
-- 	account_number int4 NULL,
-- 	subcategory_by_account_number numeric(10, 2) NULL,
-- 	report_date date NULL,
-- 	responsible_person_id int4 NULL,
-- 	responsible_person varchar(255) NULL,
-- 	ref_code varchar(50) NULL,
-- 	item_name varchar(255) NULL,
-- 	saldo_start_debit_quantity numeric NULL,
-- 	saldo_start_credit_quantity numeric NULL,
-- 	turnovers_debit_quantity numeric NULL,
-- 	turnovers_credit_quantity numeric NULL,
-- 	saldo_end_debit_quantity numeric NULL,
-- 	saldo_end_credit_quantity numeric NULL,
-- 	saldo_start_debit_prcice numeric NULL,
-- 	saldo_start_credit_prcice numeric NULL,
-- 	turnovers_debit_prcice numeric NULL,
-- 	turnovers_credit_prcice numeric NULL,
-- 	saldo_end_debit_prcice numeric NULL,
-- 	saldo_end_credit_prcice numeric NULL
-- );

create table financial_data_new
as
select 
	contract_id_match_1,
	lot_number_match_1,
	contract_id_match_2,
	lot_number_match_2,
	id,
	account_number,
	subcategory_by_account_number,
	report_date,
	responsible_person_id,
	responsible_person,
	case 
		when ref_code = '' or ref_code is null then 'Неизвестно'
		else ref_code 
	end as ref_code,
	item_name,
	coalesce(saldo_start_debit_quantity, 0) as saldo_start_debit_quantity,
	coalesce(saldo_start_credit_quantity, 0) as saldo_start_credit_quantity,
	coalesce(turnovers_debit_quantity, 0) as turnovers_debit_quantity,
	coalesce(turnovers_credit_quantity, 0) as turnovers_credit_quantity,
	coalesce(saldo_end_debit_quantity, 0) as saldo_end_debit_quantity,
	coalesce(saldo_end_credit_quantity, 0) as saldo_end_credit_quantity,
	coalesce(saldo_start_debit_prcice, 0) as saldo_start_debit_prcice,
	coalesce(saldo_start_credit_prcice, 0) as saldo_start_credit_prcice,
	coalesce(turnovers_debit_prcice, 0) as turnovers_debit_prcice,
	coalesce(turnovers_credit_prcice, 0) as turnovers_credit_prcice,
	coalesce(saldo_end_debit_prcice, 0) as saldo_end_debit_prcice,
	coalesce(saldo_end_credit_prcice, 0) as saldo_end_credit_prcice
from financial_data;

drop table financial_data;
alter table financial_data_new rename to financial_data;
