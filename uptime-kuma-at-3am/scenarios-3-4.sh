#!/usr/bin/env bash
# Scenario 3: Kuma restarts during an outage. Scenario 4: an outage happens while Kuma is down.
set -u
HERE=$(cd "$(dirname "$0")" && pwd)
KUMA_SRC=${KUMA_SRC:?set KUMA_SRC to the uptime-kuma checkout}
L(){ echo "$(date -u +%FT%TZ) $*" >> "$HERE/logs/scenarios.log"; }
T(){ echo "$1" > "$HERE/state/target"; echo "$(date -u +%FT%TZ) target -> $1" >> "$HERE/logs/target-changes.log"; }
stop_kuma(){ local p; p=$(pgrep -x uptime-kuma); L "stopping Kuma (SIGTERM pid $p)"; kill "$p"; while pgrep -x uptime-kuma >/dev/null; do sleep 1; done; L "Kuma stopped"; }
start_kuma(){ (cd "$KUMA_SRC" && DATA_DIR=../data/ UPTIME_KUMA_HOST=127.0.0.1 nohup node server/server.js >> "$1" 2>&1 &) ; until curl -s -o /dev/null http://127.0.0.1:3001/; do sleep 1; done; L "Kuma started (pid $(pgrep -x uptime-kuma)), log $1"; }

L "SCENARIO 3 START: Kuma restart during an outage"
T down; sleep 90
stop_kuma; sleep 30
start_kuma "$KUMA_SRC/../kuma-2.log"; sleep 90
T up; sleep 60
L "SCENARIO 3 END"

L "SCENARIO 4 START: outage while Kuma is down"
stop_kuma; sleep 10
T down; sleep 90
T up; sleep 20
start_kuma "$KUMA_SRC/../kuma-3.log"; sleep 90
L "SCENARIO 4 END"
