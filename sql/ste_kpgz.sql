create table ste_kpgz_new
as
select 
	reg_num as contract_id,
	ste_name,
	characteristic_name as characteristics,
	final_category as category,
	spgz_code,
	spgz as spgz_name,
	kpgz_code,
	kpgz as kpgz_name,
	reference_price as price
from ste_kpgz;

drop table ste_kpgz;
alter table ste_kpgz_new rename to ste_kpgz;

create table ste_kpgz_new
as
select distinct *
	from ste_kpgz;

drop table ste_kpgz;
alter table ste_kpgz_new rename to ste_kpgz;

select *
	from ste_kpgz;

select count(*), count(distinct t.*), count(distinct coalesce(contract_id, '')||coalesce(ste_name, '')||coalesce(characteristics, ''))
	from ste_kpgz t;
--1874	1874	1873

select count(*) filter(where contract_id in (select contract_id from procurement_contracts)), count(*)
	from ste_kpgz;
--1536	1874

create table ste_kpgz_new
as
select
	contract_id,
	ste_name,
	"characteristics",
	case 
		when category = '' or category is null then 'Неизвестно'
		else category 
	end as category,
	coalesce(spgz_code::text, 'Неизвестно') as spgz_code,
	case 
		when spgz_name = '' or spgz_name is null then 'Неизвестно'
		else spgz_name 
	end as spgz_name,
	case 
		when kpgz_code = '' or kpgz_code is null then 'Неизвестно'
		else kpgz_code 
	end as kpgz_code,
	case 
		when kpgz_name = '' or kpgz_name is null then 'Неизвестно'
		else kpgz_name 
	end as kpgz_name,
	coalesce(price, 0) as price
from ste_kpgz;

drop table ste_kpgz;
alter table ste_kpgz_new rename to ste_kpgz;

alter table ste_kpgz add column kpgz_code_name text;
update ste_kpgz 
set kpgz_code_name = kpgz_code||' '||kpgz_name;

alter table ste_kpgz add column spgz_code_name text;
update ste_kpgz 
set spgz_code_name = spgz_code||' '||spgz_name;
