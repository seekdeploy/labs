#!/usr/bin/env bash
# Second measurement only, outside LazyVim's defaults: fetch each treesitter
# parser with git (not nvim-treesitter's tarball download) at the exact revision
# nvim-treesitter pins, so nvim-treesitter can compile them from a local path.
# Usage: ./clone-parsers.sh <parsers.json> <dest-dir>
set -euo pipefail
JSON="$1"; DEST="$2"; mkdir -p "$DEST"
python3 -c '
import json, sys
seen = set()
for p in json.load(open(sys.argv[1])):
    key = (p["url"], p["revision"])
    if key in seen: continue
    seen.add(key)
    print(p["url"], p["revision"])
' "$JSON" | while read -r url rev; do
  dir="$DEST/$(basename "$url")-$rev"
  [ -d "$dir/.git" ] && { echo "have $dir"; continue; }
  git init -q "$dir"
  git -C "$dir" fetch -q --depth 1 "$url" "$rev" && git -C "$dir" checkout -q FETCH_HEAD \
    && echo "ok   $(basename "$url") $rev" || echo "FAIL $(basename "$url") $rev"
done
