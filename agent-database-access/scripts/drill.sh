#!/usr/bin/env bash
# drill.sh [runs]: the whole build, N times from scratch:
# seed -> probe roles -> guard -> probe again -> replica -> branch -> PITR + surgical repair.
set -euo pipefail; D=$(dirname "$0"); . "$D/env.sh"
runs=${1:-3}
# Never start on top of a server left over from an earlier run (see RUN-LOG, "What broke" #2).
if pgrep -u "$(id -u)" -f "postgres -D $WORK/" >/dev/null; then
  echo "a server under $WORK is still running; stop it first:"; pgrep -af "postgres -D $WORK/"; exit 1
fi
stop_all() { for d in "$PRIMARY" "$REPLICA" "$PITR"; do pg_ctl -D "$d" -m fast -w stop >/dev/null 2>&1 || true; done; }
trap stop_all EXIT
: > "$WORK/timings.csv"
for RUN in $(seq 1 "$runs"); do
  export RUN; echo "=== run $RUN of $runs ==="
  "$D/seed.sh"
  for r in agent_ro agent_rw; do "$D/probe.sh" $r; done
  psql -X -q -v ON_ERROR_STOP=1 -d shop -f "$D/../sql/guard.sql"; echo "guard installed"
  "$D/probe.sh" agent_rw | grep -E "update"
  "$D/replica.sh"
  "$D/branch.sh"
  "$D/pitr.sh"
done
echo "timings in $WORK/timings.csv"
