#!/usr/bin/env bash
# replica.sh: build a streaming read replica of the primary, point the agent at it,
# measure how far behind it is after a burst of writes, then stop it.
set -euo pipefail; D=$(dirname "$0"); . "$D/env.sh"; . "$D/timed.sh"
pg_ctl -D "$REPLICA" -m fast -w stop >/dev/null 2>&1 || true; rm -rf "$REPLICA"
timed replica_basebackup pg_basebackup -p "$PRIMARY_PORT" -D "$REPLICA" -R -X stream --checkpoint=fast
sed -i "s/^port = .*/port = $REPLICA_PORT/; s/^archive_mode = on/archive_mode = off/" "$REPLICA/postgresql.conf"
timed replica_start pg_ctl -D "$REPLICA" -l "$WORK/replica.log" -w start
psql -X -At -p "$REPLICA_PORT" -d shop -c "SELECT 'replica in recovery: ' || pg_is_in_recovery()"
echo "--- agent_ro and agent_rw against the replica:"
"$D/probe.sh" agent_ro "$REPLICA_PORT" | grep -E "read orders|update one|drop table"
"$D/probe.sh" agent_rw "$REPLICA_PORT" | grep -E "update one|update 900"
echo "--- lag after inserting 50,000 rows on the primary:"
psql -X -q -p "$PRIMARY_PORT" -d shop -c "INSERT INTO orders (customer_id, placed_at, total_cents, status)
  SELECT 1 + g % 200000, now(), 100, 'pending' FROM generate_series(1, 50000) g"
lsn=$(psql -X -At -p "$PRIMARY_PORT" -d shop -c "SELECT pg_current_wal_lsn()")
t0=$(date +%s.%N)
until [ "$(psql -X -At -p "$REPLICA_PORT" -d shop -c "SELECT pg_last_wal_replay_lsn() >= '$lsn'")" = t ]; do sleep 0.01; done
printf '%s,replica_catchup,%.3f\n' "${RUN:-1}" "$(echo "$(date +%s.%N) - $t0" | bc)" | tee -a "$WORK/timings.csv"
psql -X -At -p "$PRIMARY_PORT" -d shop -c "SELECT 'pg_stat_replication replay_lag: ' || coalesce(replay_lag::text, 'null') FROM pg_stat_replication"
pg_ctl -D "$REPLICA" -m fast -w stop >/dev/null
