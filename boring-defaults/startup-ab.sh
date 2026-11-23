#!/usr/bin/env bash
# Interleaved A/B: LazyVim startup with parsers missing vs present, alternating
# run by run so machine drift hits both equally. Same file, same tmux setup as
# startup.sh. Parsers are hidden by renaming site/parser.
# Usage: ./startup-ab.sh <nvim-bin-dir> <work-dir> [pairs]
set -u
NV="$1"; W="$2"; N="${3:-10}"; H="$W/home"; SITE="$H/.local/share/nvim/site"
ENVS="HOME=$H XDG_CONFIG_HOME=$H/.config XDG_DATA_HOME=$H/.local/share XDG_STATE_HOME=$H/.local/state XDG_CACHE_HOME=$H/.cache PATH=$NV:$PATH TERM=xterm-256color"
hide()    { mv "$SITE/parser" "$SITE/parser.off"; }
restore() { [ -d "$SITE/parser" ] && rmdir "$SITE/parser" 2>/dev/null; mv "$SITE/parser.off" "$SITE/parser"; }
one() {
  rm -f "$W/st.log"; tmux kill-server 2>/dev/null
  tmux new-session -d -s st -x 120 -y 35 "cd $W/proj && env $ENVS nvim --startuptime $W/st.log app.py +qa"
  for _ in $(seq 1 200); do tmux has-session -t st 2>/dev/null || break; sleep 0.05; done
  grep 'NVIM STARTED' "$W/st.log" | tail -1 | awk '{print $1}'
}
for i in $(seq 1 "$N"); do
  hide;    m=$(one); restore
  p=$(one)
  echo "pair $i: missing ${m} ms  present ${p} ms  (parsers on disk: $(ls "$SITE/parser"/*.so | wc -l))"
done
tmux kill-server 2>/dev/null
