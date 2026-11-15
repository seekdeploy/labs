# Shared settings. Source this; don't run it.
export PGBIN=/usr/lib/postgresql/16/bin
export PATH="$PGBIN:$PATH"
export WORK=${WORK:-/var/tmp/ttr}          # all data, backups and logs live here
export PGHOST=$WORK/sock PGPORT=5544 PGUSER=postgres
export DATA=$WORK/data                      # the "production" cluster
export BACKUPS=$WORK/backups
export SCALE=${SCALE:-20}                   # pgbench scale: 20 = 2M accounts rows
mkdir -p "$WORK/sock" "$BACKUPS" "$WORK/fp"
