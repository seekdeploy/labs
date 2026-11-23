-- Least-privilege roles for a coding agent. Run as the database owner.
-- Nobody gets anything by default.
REVOKE ALL ON DATABASE shop FROM PUBLIC;
REVOKE ALL ON SCHEMA public FROM PUBLIC;

-- agent_ro: reads what it needs, never customers' emails or prefs.
CREATE ROLE agent_ro LOGIN;
GRANT CONNECT ON DATABASE shop TO agent_ro;
GRANT USAGE ON SCHEMA public TO agent_ro;
GRANT SELECT ON orders, pgbench_accounts, pgbench_branches, pgbench_tellers, monthly_revenue TO agent_ro;
GRANT SELECT (id, name, created_at) ON customers TO agent_ro;
ALTER ROLE agent_ro SET default_transaction_read_only = on;
ALTER ROLE agent_ro SET statement_timeout = '5s';

-- agent_rw: may insert and update orders. No DELETE, no TRUNCATE, owns nothing (so no DDL).
CREATE ROLE agent_rw LOGIN;
GRANT CONNECT ON DATABASE shop TO agent_rw;
GRANT USAGE ON SCHEMA public TO agent_rw;
GRANT SELECT, INSERT, UPDATE ON orders TO agent_rw;
GRANT USAGE ON SEQUENCE orders_id_seq TO agent_rw;
GRANT SELECT (id, name, created_at) ON customers TO agent_rw;
ALTER ROLE agent_rw SET statement_timeout = '5s';
ALTER ROLE agent_rw SET lock_timeout = '2s';
ALTER ROLE agent_rw SET idle_in_transaction_session_timeout = '30s';
