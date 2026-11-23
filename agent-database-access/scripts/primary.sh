#!/usr/bin/env bash
# primary.sh init|start|stop: the "production" server, with WAL archiving on.
set -euo pipefail; . "$(dirname "$0")/env.sh"
case "$1" in
  init) initdb -D "$PRIMARY" -U postgres --auth=trust --data-checksums >/dev/null
        cat >> "$PRIMARY/postgresql.conf" <<CONF
port = $PRIMARY_PORT
unix_socket_directories = '$PGHOST'
listen_addresses = ''
wal_level = replica
archive_mode = on
archive_command = 'test ! -f $ARCHIVE/%f && cp %p $ARCHIVE/%f'
max_wal_senders = 4
CONF
        ;;
  start) pg_ctl -D "$PRIMARY" -l "$WORK/primary.log" -w start >/dev/null ;;
  stop)  pg_ctl -D "$PRIMARY" -m fast -w stop >/dev/null 2>&1 || true ;;
esac
