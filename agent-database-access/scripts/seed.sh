#!/usr/bin/env bash
# seed.sh: fresh primary with the shop database, the agent roles, nothing else.
set -euo pipefail; D=$(dirname "$0"); . "$D/env.sh"; . "$D/timed.sh"
"$D/primary.sh" stop; rm -rf "$PRIMARY" "$ARCHIVE"/*
"$D/primary.sh" init; "$D/primary.sh" start
createdb shop
timed seed_pgbench pgbench -i -q -s "$SCALE" shop
timed seed_shop psql -X -q -v ON_ERROR_STOP=1 -d shop -f "$D/../sql/schema.sql"
psql -X -q -v ON_ERROR_STOP=1 -d shop -f "$D/../sql/roles.sql"
psql -X -At -d shop -c "SELECT pg_size_pretty(pg_database_size('shop'))"
