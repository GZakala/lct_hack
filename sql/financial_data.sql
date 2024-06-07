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
