#!/usr/bin/env bash
# pitr.sh: the mistake every permission allows, and the way back.
# 1. Base backup of the primary (WAL is already being archived).
# 2. Fingerprint orders, note the time, let agent_rw run a 900-row UPDATE that
#    passes its grants and the 1,000-row guard.
# 3. Restore the base backup into a new data dir, replay archived WAL up to the
#    noted time, and compare orders with the pre-mistake fingerprint.
set -euo pipefail; D=$(dirname "$0"); . "$D/env.sh"; . "$D/timed.sh"
fp() { psql -X -At -p "$1" -d shop -c "SELECT count(*) || ' rows, md5 ' || md5(string_agg(o::text, ',' ORDER BY id)) FROM orders o"; }
rm -rf "$BASE"; pg_ctl -D "$PITR" -m fast -w stop >/dev/null 2>&1 || true; rm -rf "$PITR"
timed pitr_basebackup pg_basebackup -p "$PRIMARY_PORT" -D "$BASE" -X stream --checkpoint=fast
# Some ordinary traffic after the backup, so recovery has WAL to replay.
psql -X -q -d shop -c "INSERT INTO orders (customer_id, placed_at, total_cents, status)
  SELECT 1 + g % 200000, now(), 250, 'pending' FROM generate_series(1, 20000) g"
before=$(fp "$PRIMARY_PORT"); echo "orders before mistake: $before"
target=$(psql -X -At -d shop -c "SELECT clock_timestamp()")
echo "recovery target: $target"
sleep 1
psql -X -q -U agent_rw -d shop -c "UPDATE orders SET status = 'refunded' WHERE id <= 900"
echo "agent_rw UPDATE of 900 rows: committed"
psql -X -q -U agent_rw -d shop -c "INSERT INTO orders (customer_id, placed_at, total_cents, status)
  SELECT 1 + g, now(), 999, 'paid' FROM generate_series(1, 100) g"
echo "agent_rw then INSERTed 100 good orders"
echo "orders after mistake:  $(fp "$PRIMARY_PORT")"
psql -X -At -d shop -c "SELECT 'refunded among id<=900: ' || count(*) FROM orders WHERE id <= 900 AND status = 'refunded'"
psql -X -q -d shop -c "SELECT pg_switch_wal()" >/dev/null   # push the mistake's WAL segment to the archive
sleep 2
ls "$ARCHIVE" | wc -l | sed 's/^/WAL segments archived: /'
restore() {
  : > "$WORK/pitr.log"
  cp -a "$BASE" "$PITR"
  sed -i "s/^port = .*/port = $PITR_PORT/; s/^archive_mode = on/archive_mode = off/" "$PITR/postgresql.conf"
  cat >> "$PITR/postgresql.conf" <<CONF
restore_command = 'cp $ARCHIVE/%f %p'
recovery_target_time = '$target'
recovery_target_action = 'promote'
CONF
  touch "$PITR/recovery.signal"
  pg_ctl -D "$PITR" -l "$WORK/pitr.log" -w -t 300 start >/dev/null
  until [ "$(psql -X -At -p "$PITR_PORT" -d postgres -c 'SELECT NOT pg_is_in_recovery()')" = t ]; do sleep 0.2; done
}
timed pitr_restore restore
after=$(fp "$PITR_PORT"); echo "orders after PITR:     $after"
[ "$before" = "$after" ] && echo "VERIFY pitr: orders identical to pre-mistake state" || { echo "VERIFY pitr: DIFFERENT"; exit 1; }
# Surgical repair: copy only the damaged rows back from the restored copy, so
# the 100 good orders written after the mistake survive. session_replication_role
# = replica skips triggers, so orders_touch doesn't restamp updated_at and the
# guard doesn't count the repair.
repair() {
  psql -X -q -p "$PITR_PORT" -d shop -c "\\copy (SELECT id, status, updated_at FROM orders WHERE id <= 900) TO '$WORK/repair.csv' CSV"
  psql -X -q -v ON_ERROR_STOP=1 -d shop \
    -c "BEGIN" -c "SET LOCAL session_replication_role = replica" \
    -c "CREATE TEMP TABLE repair (id bigint, status text, updated_at timestamptz) ON COMMIT DROP" \
    -c "\\copy repair FROM '$WORK/repair.csv' CSV" \
    -c "UPDATE orders o SET status = r.status, updated_at = r.updated_at FROM repair r WHERE o.id = r.id" \
    -c "COMMIT"
}
timed surgical_repair repair
fixed=$(psql -X -At -d shop -c "SELECT count(*) || ' rows, md5 ' || md5(string_agg(o::text, ',' ORDER BY id)) FROM orders o WHERE id <= ${before%% rows*}")
echo "primary, original rows after repair: $fixed"
[ "$before" = "$fixed" ] && echo "VERIFY repair: original rows identical to pre-mistake state" || { echo "VERIFY repair: DIFFERENT"; exit 1; }
psql -X -At -d shop -c "SELECT 'good orders written after the mistake still present: ' || count(*) FROM orders WHERE id > ${before%% rows*}"
grep -E "recovery stopping|starting point-in-time|archive recovery complete|redo done" "$WORK/pitr.log" | sed 's/^.*LOG: */log: /'
pg_ctl -D "$PITR" -m fast -w stop >/dev/null
