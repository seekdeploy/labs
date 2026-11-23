#!/usr/bin/env bash
# Clean LazyVim install, following https://www.lazyvim.org/installation exactly,
# inside an isolated HOME so nothing from the machine leaks in.
# Usage: ./install.sh <path-to-nvim-binary> <work-dir>
set -euo pipefail
NVIM="$1"; WORK="$2"
export HOME="$WORK/home"; mkdir -p "$HOME"
export XDG_CONFIG_HOME="$HOME/.config" XDG_DATA_HOME="$HOME/.local/share" \
       XDG_STATE_HOME="$HOME/.local/state" XDG_CACHE_HOME="$HOME/.cache"
export PATH="$(dirname "$NVIM"):$PATH"
echo "== nvim: $(nvim --version | head -1)"
echo "== step 1: clone the starter"
git clone https://github.com/LazyVim/starter "$XDG_CONFIG_HOME/nvim" 2>&1
echo "== starter commit: $(git -C "$XDG_CONFIG_HOME/nvim" rev-parse --short HEAD)"
echo "== step 2: remove the starter's .git"
rm -rf "$XDG_CONFIG_HOME/nvim/.git"
echo "== step 3: first start, headless sync"
start=$(date +%s)
nvim --headless "+Lazy! sync" +qa 2>&1 | tail -40
echo "== sync took $(( $(date +%s) - start ))s"
