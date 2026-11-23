#!/usr/bin/env bash
# branch.sh: a throwaway copy of the database that the agent may wreck.
# CREATE DATABASE ... TEMPLATE copies the files; the source must have no other connections.
set -euo pipefail; D=$(dirname "$0"); . "$D/env.sh"; . "$D/timed.sh"
dropdb --if-exists shop_branch
timed branch_create createdb -T shop shop_branch
psql -X -q -d shop_branch -c "GRANT ALL ON DATABASE shop_branch TO agent_rw" \
  -c "ALTER TABLE orders OWNER TO agent_rw" -c "GRANT CREATE ON SCHEMA public TO agent_rw"
echo "--- agent_rw on the branch (owns orders there):"
"$D/probe.sh" agent_rw "$PRIMARY_PORT" shop_branch | grep -E "truncate|alter table|create table|delete one"
echo "--- actually drop orders on the branch, then count on both:"
psql -X -q -U agent_rw -d shop_branch -c "DROP TABLE orders CASCADE" 2>&1 | grep -v NOTICE || true
psql -X -At -d shop_branch -c "SELECT 'branch orders table exists: ' || (to_regclass('orders') IS NOT NULL)"
psql -X -At -d shop -c "SELECT 'main orders rows: ' || count(*) FROM orders"
timed branch_drop dropdb shop_branch
