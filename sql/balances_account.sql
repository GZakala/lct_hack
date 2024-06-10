CREATE TABLE public.balances_account_101 (
	account_number int4 NULL,
	report_date date NULL,
	responsible_person varchar(255) NULL,
	responsible_person_id int4 NULL,
	subcategory_by_account_number varchar(50) NULL,
	inventory_number varchar(50) NULL,
	okof varchar(50) NULL,
	depreciation_group varchar(50) NULL,
	depreciation_method varchar(50) NULL,
	accounting_date date NULL,
	condition_ varchar(50) NULL,
	useful_life_years int4 NULL,
	monthly_depreciation_rate numeric(10, 2) NULL,
	depreciation_rate numeric(10, 2) NULL,
	item_name varchar(255) NULL,
	price numeric(10, 2) NULL,
	quantity int4 NULL,
	depreciation_amount numeric(10, 2) NULL,
	residual_value numeric(10, 2) NULL
);
--insert data

CREATE TABLE public.balances_account_105 (
	account_number int4 NULL,
	report_date date NULL,
	responsible_person varchar(255) NULL,
	responsible_person_id int4 NULL,
	subcategory_by_account_number varchar(255) NULL,
	item_name varchar(255) NULL,
	price numeric(10, 2) NULL,
	quantity int4 NULL,
	total_amount numeric(10, 2) NULL
);
--insert data

CREATE TABLE public.balances_account_21 (
	account_number int4 NULL,
	report_date date NULL,
	responsible_person varchar(255) NULL,
	responsible_person_id int4 NULL,
	subcategory_by_account_number varchar(50) NULL,
	inventory_number varchar(50) NULL,
	okof varchar(50) NULL,
	depreciation_group varchar(50) NULL,
	depreciation_method varchar(50) NULL,
	accounting_date date NULL,
	condition_ varchar(50) NULL,
	useful_life_years int4 NULL,
	monthly_depreciation_rate varchar(50) NULL,
	depreciation_rate varchar(50) NULL,
	item_name varchar(255) NULL,
	price numeric(10, 2) NULL,
	quantity int4 NULL,
	depreciation_amount numeric(10, 2) NULL,
	residual_value numeric(10, 2) NULL
);
--insert data



create table balances_account
as
select 
	account_number,
	subcategory_by_account_number,
	report_date,
	responsible_person_id,
	responsible_person,
	inventory_number,
	depreciation_group,
	depreciation_method,
	depreciation_rate,
	accounting_date,
	item_name,
	okof,
	condition_ as condition,
	quantity,
	price,
	null as total_price,
	depreciation_amount,
	residual_value,
	useful_life_years as useful_months,
	monthly_depreciation_rate
from balances_account_101
union
select 
	account_number,
	subcategory_by_account_number,
	report_date,
	responsible_person_id,
	responsible_person,
	null as inventory_number,
	null as depreciation_group,
	null as depreciation_method,
	null as depreciation_rate,
	null as accounting_date,
	item_name,
	null as okof,
	null as condition,
	quantity,
	price,
	total_amount as total_price,
	null as depreciation_amount,
	null as residual_value,
	null as useful_months,
	null as monthly_depreciation_rate
from balances_account_105
union
select 
	account_number,
	subcategory_by_account_number,
	report_date,
	responsible_person_id,
	responsible_person,
	inventory_number,
	depreciation_group,
	depreciation_method,
	(case when depreciation_rate = '' then 0 else depreciation_rate::int end)::int as depreciation_rate,
	accounting_date,
	item_name,
	okof,
	condition_ as condition,
	quantity,
	price,
	null as total_price,
	depreciation_amount,
	residual_value,
	useful_life_years as useful_months,
	(case when monthly_depreciation_rate = '' then 0 else monthly_depreciation_rate::int end)::int as monthly_depreciation_rate
from balances_account_21;

select *
	from balances_account;

create table balances_account_new 
as
select row_number() as id, *
	from balances_account;

drop table balances_account;
alter table balances_account_new rename to balances_account;

select 
	count(*), 
	count(distinct t.*), 
	count(distinct coalesce(account_number, 0)||coalesce(inventory_number, '')||coalesce(accounting_date::text, '')||coalesce(report_date::text, '')||coalesce(item_name, ''))
from balances_account t;
--36248	36248	36248

-- CREATE TABLE public.match_contr_bal (
-- 	balances_id text NULL,
-- 	balances_item_name text NULL,
-- 	contracts_contract_id text NULL,
-- 	contract_lot_number text NULL,
-- 	contracts_spgz_name text NULL,
-- 	contracts_contract_subject text NULL,
-- 	contracts_contract_id_2_match text NULL,
-- 	contracts_lot_number_2_match text NULL,
-- 	"matched" bool NULL
-- );


create table balances_account_new
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
		when inventory_number = '' or inventory_number is null then 'Неизвестно'
		else inventory_number 
	end as inventory_number,
	case 
		when depreciation_group = '' or depreciation_group is null then 'Неизвестно'
		else depreciation_group 
	end as depreciation_group,
	case 
		when depreciation_method = '' or depreciation_method is null then 'Неизвестно'
		else depreciation_method 
	end as depreciation_method,
	depreciation_rate,
	accounting_date,
	item_name,
	case 
		when okof = '' or okof is null then 'Неизвестно'
		else okof 
	end as okof,
	case 
		when condition = '' or condition is null then 'Неизвестно'
		else condition 
	end as condition,
	quantity,
	price,
	price * quantity as total_price,
	case 
		when depreciation_amount is null then 0
		else depreciation_amount 
	end as depreciation_amount,
	case 
		when residual_value is null then 0
		else residual_value 
	end as residual_value,
	case 
		when useful_months is null then 0
		else useful_months 
	end as useful_months,
	case 
		when monthly_depreciation_rate is null then 0
		else monthly_depreciation_rate 
	end as monthly_depreciation_rate
from balances_account;

drop table balances_account;
alter table balances_account_new rename to balances_account;

update balances_account
set account_number = (string_to_array(subcategory_by_account_number, '.')::int[])[1]
where account_number is null;
