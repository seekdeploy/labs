#!/usr/bin/env bash
# seed.sh: fresh cluster with a "shop" database, then record its fingerprint.
set -euo pipefail; D=$(dirname "$0"); . "$D/env.sh"; . "$D/timed.sh"
"$D/cluster.sh" stop; rm -rf "$DATA"
"$D/cluster.sh" init; "$D/cluster.sh" start
createdb shop
timed seed_pgbench pgbench -i -q -s "$SCALE" shop
timed seed_shop psql -q -v ON_ERROR_STOP=1 -d shop -f "$D/../sql/schema.sql"
psql -d shop -f "$D/../sql/fingerprint.sql" > "$WORK/fp/original.txt"
psql -Atc "SELECT pg_size_pretty(pg_database_size('shop'))" -d shop
