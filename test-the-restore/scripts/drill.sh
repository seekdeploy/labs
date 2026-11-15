#!/usr/bin/env bash
# drill.sh [runs]: the whole drill, N times. Seed, back up, wipe, restore both ways, verify.
set -euo pipefail; D=$(dirname "$0"); . "$D/env.sh"
runs=${1:-3}; : > "$WORK/timings.csv"
for RUN in $(seq 1 "$runs"); do
  export RUN; echo "=== run $RUN of $runs ==="
  "$D/seed.sh"
  "$D/backup.sh"
  "$D/wipe.sh";  "$D/restore-logical.sh";  "$D/verify.sh" logical
  "$D/wipe.sh";  "$D/restore-physical.sh"; "$D/verify.sh" physical
done
"$D/cluster.sh" stop
echo "timings in $WORK/timings.csv"
