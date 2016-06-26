-- using 1433771997 as a seed to the RNG


SET statement_timeout = "3600s";
select
	sum(l_extendedprice) / 7.0 as avg_yearly
from
	lineitem,
	part
where
	p_partkey = l_partkey
	and p_brand = 'Brand#52'
	and p_container = 'LG CAN'
	and l_quantity < (
		select
			'0.2'::fixeddecimal * avg(l_quantity)
		from
			lineitem
		where
			l_partkey = p_partkey
	);

