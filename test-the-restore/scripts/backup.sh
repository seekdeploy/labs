#!/usr/bin/env bash
# backup.sh: two backups of the running cluster.
#  A) logical: pg_dumpall --globals-only (roles) + pg_dump -Fc (one database)
#  B) physical: pg_basebackup, tar format, WAL streamed in, then unpack + pg_verifybackup
set -euo pipefail; D=$(dirname "$0"); . "$D/env.sh"; . "$D/timed.sh"
rm -rf "$BACKUPS"/*
timed dump_globals pg_dumpall --globals-only -f "$BACKUPS/globals.sql"
timed dump_custom  pg_dump -Fc -d shop -f "$BACKUPS/shop.dump"
timed basebackup   pg_basebackup -D "$BACKUPS/base" -Ft -z -X stream --checkpoint=fast
# PG 16's pg_verifybackup only reads plain-format backups ("a tar format backup
# can be checked after extracting it"), so unpack to a scratch dir and verify that.
verify_base() {
  local v="$WORK/verify"; rm -rf "$v"; mkdir -p "$v/pg_wal"; chmod 700 "$v"
  tar -xzf "$BACKUPS/base/base.tar.gz" -C "$v"
  tar -xzf "$BACKUPS/base/pg_wal.tar.gz" -C "$v/pg_wal"
  pg_verifybackup -m "$BACKUPS/base/backup_manifest" "$v"
  rm -rf "$v"
}
timed verify_base verify_base
du -sh "$BACKUPS"/* | sed "s#$BACKUPS/##"
