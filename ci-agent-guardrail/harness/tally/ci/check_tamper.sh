#!/usr/bin/env bash
# Fail if the PR edits CI files, or removes test assertions.
set -euo pipefail
BASE=$1 HEAD=$2
fail=0
if git diff --name-only "$BASE" "$HEAD" | grep -E '^(\.gitea/workflows/|ci/)'; then
  echo "::error::PR modifies CI configuration; needs a maintainer"; fail=1
fi
count() { git grep -h -E 'assert[A-Z]|assertRaises' "$1" -- tests/ | wc -l; }
before=$(count "$BASE") after=$(count "$HEAD")
echo "test assertions: $before -> $after"
if (( after < before )); then echo "::error::PR removes test assertions"; fail=1; fi
exit $fail
