\pset format unaligned
\pset tuples_only on
SELECT 'matview_stored   ' || md5(string_agg(m::text, ',' ORDER BY month)) FROM monthly_revenue m;
SELECT 'matview_query_now ' || md5(string_agg(m::text, ',' ORDER BY month)) FROM (
  SELECT date_trunc('month', placed_at) AS month, sum(total_cents) AS cents
  FROM orders WHERE status <> 'refunded' GROUP BY 1) m;
