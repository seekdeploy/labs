# Shared settings. Source this; don't run it.
export PGBIN=/usr/lib/postgresql/16/bin
export PATH="$PGBIN:$PATH"
export WORK=${WORK:-/var/tmp/ada}
export PGHOST=$WORK/sock PGUSER=postgres
export PRIMARY=$WORK/primary PRIMARY_PORT=5544
export REPLICA=$WORK/replica REPLICA_PORT=5545
export PITR=$WORK/pitr PITR_PORT=5546
export ARCHIVE=$WORK/wal-archive BASE=$WORK/base
export SCALE=${SCALE:-5}
export PGPORT=$PRIMARY_PORT
mkdir -p "$WORK/sock" "$ARCHIVE" "$WORK/out"
