-- A small shop on top of pgbench's tables: the things a real app has that a
-- row-count check would miss (roles, grants, sequences, a view, a function,
-- a trigger, jsonb, an extension, a materialized view).
CREATE EXTENSION IF NOT EXISTS pg_trgm;
DO $$ BEGIN
  IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'app_rw') THEN CREATE ROLE app_rw LOGIN; END IF;
  IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'app_ro') THEN CREATE ROLE app_ro LOGIN; END IF;
END $$;
CREATE TABLE customers (
  id bigserial PRIMARY KEY,
  email text NOT NULL UNIQUE,
  name text NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  prefs jsonb NOT NULL DEFAULT '{}'
);
CREATE TABLE orders (
  id bigserial PRIMARY KEY,
  customer_id bigint NOT NULL REFERENCES customers(id),
  placed_at timestamptz NOT NULL,
  total_cents integer NOT NULL CHECK (total_cents >= 0),
  status text NOT NULL,
  updated_at timestamptz
);
CREATE INDEX orders_customer_idx ON orders (customer_id);
CREATE INDEX customers_name_trgm ON customers USING gin (name gin_trgm_ops);
CREATE FUNCTION touch_updated_at() RETURNS trigger LANGUAGE plpgsql AS
$$ BEGIN NEW.updated_at := now(); RETURN NEW; END $$;
CREATE TRIGGER orders_touch BEFORE UPDATE ON orders
  FOR EACH ROW EXECUTE FUNCTION touch_updated_at();
CREATE VIEW customer_totals AS
  SELECT c.id, c.email, count(o.id) AS orders, coalesce(sum(o.total_cents),0) AS cents
  FROM customers c LEFT JOIN orders o ON o.customer_id = c.id GROUP BY c.id, c.email;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO app_rw;
GRANT USAGE ON ALL SEQUENCES IN SCHEMA public TO app_rw;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO app_ro;

-- Deterministic fake data (setseed) so every run produces the same rows.
SELECT setseed(0.42);
INSERT INTO customers (email, name, created_at, prefs)
SELECT 'user' || g || '@example.test',
       'Customer ' || md5(g::text),
       timestamptz '2024-01-01' + (g || ' minutes')::interval,
       jsonb_build_object('newsletter', g % 3 = 0, 'locale', (ARRAY['sv','en','de'])[1 + g % 3])
FROM generate_series(1, 200000) g;
INSERT INTO orders (customer_id, placed_at, total_cents, status)
SELECT 1 + (random() * 199999)::int,
       timestamptz '2024-01-01' + (random() * 600 || ' days')::interval,
       (random() * 50000)::int,
       (ARRAY['paid','shipped','refunded','pending'])[1 + (random()*3)::int]
FROM generate_series(1, 1000000);
CREATE MATERIALIZED VIEW monthly_revenue AS
  SELECT date_trunc('month', placed_at) AS month, sum(total_cents) AS cents
  FROM orders WHERE status <> 'refunded' GROUP BY 1;
UPDATE orders SET status = 'shipped' WHERE id % 1000 = 0;  -- fires the trigger
ANALYZE;
