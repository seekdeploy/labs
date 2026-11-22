-- One line per fact. Two databases are "the same" if this output is identical.
\pset format unaligned
\pset tuples_only on
SELECT 'table ' || t || ' rows=' || n || ' md5=' || h FROM (
  SELECT 'pgbench_accounts' t, count(*) n, md5(string_agg(aid||':'||bid||':'||abalance, ',' ORDER BY aid)) h FROM pgbench_accounts
  UNION ALL SELECT 'pgbench_branches', count(*), md5(string_agg(bid||':'||bbalance, ',' ORDER BY bid)) FROM pgbench_branches
  UNION ALL SELECT 'pgbench_tellers', count(*), md5(string_agg(tid||':'||tbalance, ',' ORDER BY tid)) FROM pgbench_tellers
  UNION ALL SELECT 'customers', count(*), md5(string_agg(c::text, ',' ORDER BY id)) FROM customers c
  UNION ALL SELECT 'orders', count(*), md5(string_agg(o::text, ',' ORDER BY id)) FROM orders o
  UNION ALL SELECT 'monthly_revenue', count(*), md5(string_agg(m::text, ',' ORDER BY month)) FROM monthly_revenue m
) x ORDER BY t;
SELECT 'seq ' || sequencename || ' last=' || coalesce(last_value::text,'null') FROM pg_sequences ORDER BY 1;
SELECT 'objects relations=' || (SELECT count(*) FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace WHERE n.nspname='public')
  || ' functions=' || (SELECT count(*) FROM pg_proc p JOIN pg_namespace n ON n.oid=p.pronamespace WHERE n.nspname='public')
  || ' triggers=' || (SELECT count(*) FROM pg_trigger WHERE NOT tgisinternal)
  || ' extensions=' || (SELECT string_agg(extname, ',' ORDER BY extname) FROM pg_extension);
SELECT 'grant ' || grantee || ' ' || table_name || ' ' || string_agg(privilege_type, ',' ORDER BY privilege_type)
  FROM information_schema.role_table_grants WHERE table_schema='public' AND grantee IN ('app_rw','app_ro')
  GROUP BY grantee, table_name ORDER BY 1;
SELECT 'roles ' || string_agg(rolname, ',' ORDER BY rolname) FROM pg_roles WHERE rolname LIKE 'app_%';
SELECT 'matview_populated ' || ispopulated FROM pg_matviews WHERE matviewname='monthly_revenue';
