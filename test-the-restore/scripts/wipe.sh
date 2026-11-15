#!/usr/bin/env bash
# wipe.sh: simulate losing the server. Stop it and delete the data directory.
set -euo pipefail; D=$(dirname "$0"); . "$D/env.sh"
"$D/cluster.sh" stop
rm -rf "$DATA"
echo "wiped: $(ls "$DATA" 2>&1 | head -1)"
