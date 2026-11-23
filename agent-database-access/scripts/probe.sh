#!/usr/bin/env bash
# probe.sh <role> [port] [db]: run every statement in sql/probes.txt as <role>,
# each in its own transaction that is ROLLED BACK, and print OK or the error.
set -uo pipefail; D=$(dirname "$0"); . "$D/env.sh"
role=$1; port=${2:-$PRIMARY_PORT}; db=${3:-shop}
while IFS='|' read -r label sql; do
  [ -z "$label" ] && continue
  out=$(psql -X -q -At -p "$port" -U "$role" -d "$db" -v ON_ERROR_STOP=1 \
        -c "BEGIN" -c "$sql" -c "ROLLBACK" 2>&1 >/dev/null) && res="OK" \
        || res="BLOCKED: $(echo "$out" | grep -m1 -oE 'ERROR: .*' | sed 's/ERROR:  *//')"
  printf '%-20s | %-22s | %s\n' "$role" "$label" "$res"
done < "$D/../sql/probes.txt"
