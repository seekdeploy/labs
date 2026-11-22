#!/usr/bin/env bash
# verify.sh <logical|physical>: compare a restored fingerprint with the original.
# Physical restores must match exactly. Logical restores re-run materialized-view
# queries (pg_restore's "MATERIALIZED VIEW DATA" step), so a view that was stale
# on the original comes back fresh. For those, check the view against its own
# query instead of against the original's stale contents.
set -euo pipefail; D=$(dirname "$0"); . "$D/env.sh"
name=$1; orig="$WORK/fp/original.txt"; got="$WORK/fp/$name.txt"
skip='^$'; [ "$name" = logical ] && skip='^table monthly_revenue '
if diff -u <(grep -v "$skip" "$orig") <(grep -v "$skip" "$got"); then
  echo "VERIFY $name: identical ($(grep -vc "$skip" "$orig") facts checked)"
else
  echo "VERIFY $name: DIFFERENT"; exit 1
fi
if [ "$name" = logical ]; then
  mv=$(psql -d shop -f "$D/../sql/matview-check.sql" | grep matview_ | awk '{print $2}' | sort -u | wc -l)
  [ "$mv" = 1 ] && echo "VERIFY $name: monthly_revenue matches its query (refreshed by pg_restore)" \
                || { echo "VERIFY $name: monthly_revenue does NOT match its query"; exit 1; }
  grep '^table monthly_revenue' "$orig" "$got" | sed "s#$WORK/fp/##"
fi
