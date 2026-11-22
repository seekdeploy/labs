#!/usr/bin/env bash
# cluster.sh init|start|stop  -- manage the throwaway cluster in $DATA
set -euo pipefail; . "$(dirname "$0")/env.sh"
case "$1" in
  init)  initdb -D "$DATA" -U postgres --auth=trust --data-checksums >/dev/null
         cat >> "$DATA/postgresql.conf" <<CONF
port = $PGPORT
unix_socket_directories = '$PGHOST'
listen_addresses = ''
wal_level = replica
max_wal_senders = 4
CONF
         ;;
  start) pg_ctl -D "$DATA" -l "$WORK/server.log" -w start >/dev/null ;;
  stop)  pg_ctl -D "$DATA" -m fast -w stop >/dev/null || true ;;
  *) echo "usage: $0 init|start|stop" >&2; exit 2 ;;
esac
