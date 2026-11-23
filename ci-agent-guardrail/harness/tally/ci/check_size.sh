#!/usr/bin/env bash
# Fail if the PR changes more than MAX_LINES lines or MAX_FILES files.
set -euo pipefail
BASE=$1 HEAD=$2 MAX_LINES=${MAX_LINES:-300} MAX_FILES=${MAX_FILES:-10}
read -r files lines < <(git diff --numstat "$BASE" "$HEAD" | awk '{f++; l+=$1+$2} END {print f+0, l+0}')
echo "changed files: $files (max $MAX_FILES), changed lines: $lines (max $MAX_LINES)"
if (( files > MAX_FILES || lines > MAX_LINES )); then
  echo "::error::PR too large for review: split it"; exit 1
fi
