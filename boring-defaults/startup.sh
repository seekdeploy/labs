#!/usr/bin/env bash
# Startup time, in a real terminal (tmux), N runs each:
#   bare   = nvim --clean app.py
#   lazyvim = nvim app.py with the LazyVim starter config
# Reads the "--- NVIM STARTED ---" line from --startuptime.
# Usage: ./startup.sh <nvim-bin-dir> <work-dir> [runs]
set -u
NV="$1"; W="$2"; N="${3:-10}"; H="$W/home"
ENVS="HOME=$H XDG_CONFIG_HOME=$H/.config XDG_DATA_HOME=$H/.local/share XDG_STATE_HOME=$H/.local/state XDG_CACHE_HOME=$H/.cache PATH=$NV:$PATH TERM=xterm-256color"
run() { # $1 label, $2 extra args
  for i in $(seq 1 "$N"); do
    rm -f "$W/st.log"
    tmux kill-server 2>/dev/null
    tmux new-session -d -s st -x 120 -y 35 "cd $W/proj && env $ENVS nvim $2 --startuptime $W/st.log app.py +qa"
    for _ in $(seq 1 200); do tmux has-session -t st 2>/dev/null || break; sleep 0.05; done
    ms=$(grep 'NVIM STARTED' "$W/st.log" | tail -1 | awk '{print $1}')
    echo "$1 run $i: ${ms} ms"
  done
}
run bare "--clean"
run lazyvim ""
tmux kill-server 2>/dev/null
