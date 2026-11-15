#!/usr/bin/env bash
# restore-logical.sh: brand-new cluster, roles first, then pg_restore in parallel.
set -euo pipefail; D=$(dirname "$0"); . "$D/env.sh"; . "$D/timed.sh"
"$D/cluster.sh" init; "$D/cluster.sh" start
# pg_dumpall docs: the globals script "is certain to get a 'role already exists'
# error for the bootstrap superuser ... This error is harmless". Allow exactly
# that error and fail on any other, rather than turning error checking off.
restore_globals() {
  psql -q -d postgres -f "$BACKUPS/globals.sql" 2> "$WORK/globals.err" || true
  if grep -v 'role "postgres" already exists' "$WORK/globals.err" | grep -q ERROR; then
    cat "$WORK/globals.err" >&2; return 1
  fi
  echo "globals restored; expected errors: $(grep -c ERROR "$WORK/globals.err")"
}
timed restore_globals restore_globals
createdb shop
timed restore_custom pg_restore -j 4 --exit-on-error -d shop "$BACKUPS/shop.dump"
timed analyze_after vacuumdb -q -z -d shop
psql -d shop -f "$D/../sql/fingerprint.sql" > "$WORK/fp/logical.txt"
