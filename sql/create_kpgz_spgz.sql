CREATE TABLE public.kpgz (
	kpgzcode text NULL,
	kpgzname text NULL,
	global_id text NULL
);
--insert data from kpgz.csv

select count(*), count(distinct t.*), count(distinct kpgzcode)
	from kpgz t;
--17531	17531	17531



CREATE TABLE public.spgz (
	spgzname text NULL,
	kpgzparent text NULL,
	global_id text NULL
);
--insert data from spgz.csv

select count(*), count(distinct t.*), count(distinct global_id)
	from spgz t;
--172254	172254	172254



create table kpgz_spgz
(
	kpgz_code text,
	kpgz_name text,
	spgz_code text,
	spgz_name text,
	kpgz_global_id text
);

insert into kpgz_spgz
select 	tt.kpgzcode as kpgz_code,
				tt.kpgzname as kpgz_name,
				t.global_id as spgz_code,
				t.spgzname as spgz_name,
				tt.global_id as kpgz_global_id
	from spgz t
	full join kpgz tt on (regexp_match(t.kpgzparent, 'global_id=([0-9]+)'))[1] = tt.global_id;

select count(*), count(distinct t.*), count(distinct spgz_code), count(distinct kpgz_code)
	from kpgz_spgz t;
--175764	175764	172254	17531



drop table kpgz;
drop table spgz;
