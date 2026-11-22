#!/usr/bin/env bash
# restore-physical.sh: unpack the base backup into an empty data dir and start it.
set -euo pipefail; D=$(dirname "$0"); . "$D/env.sh"; . "$D/timed.sh"
mkdir -p "$DATA"; chmod 700 "$DATA"
unpack() {
  tar -xzf "$BACKUPS/base/base.tar.gz" -C "$DATA"
  tar -xzf "$BACKUPS/base/pg_wal.tar.gz" -C "$DATA/pg_wal"
}
timed restore_unpack unpack
timed restore_start "$D/cluster.sh" start
psql -d shop -f "$D/../sql/fingerprint.sql" > "$WORK/fp/physical.txt"
