#!/usr/bin/env bash
# Every commit needs a Signed-off-by from someone other than the agent account.
# Commits authored by the agent account must also carry Assisted-by:.
set -euo pipefail
BASE=$1 HEAD=$2 AGENT_EMAIL=${AGENT_EMAIL:-agent-bot@example.invalid}
fail=0
for c in $(git rev-list "$BASE..$HEAD"); do
  author=$(git log -1 --format=%ae "$c")
  sob=$(git log -1 --format='%(trailers:key=Signed-off-by,valueonly)' "$c" | grep -v "$AGENT_EMAIL" | grep -c . || true)
  ab=$(git log -1 --format='%(trailers:key=Assisted-by,valueonly)' "$c" | grep -c . || true)
  short=$(git log -1 --format='%h %s' "$c")
  if (( sob == 0 )); then echo "::error::$short has no human Signed-off-by"; fail=1; fi
  if [[ $author == "$AGENT_EMAIL" ]] && (( ab == 0 )); then echo "::error::$short is by the agent but has no Assisted-by"; fail=1; fi
done
(( fail == 0 )) && echo "provenance trailers OK"
exit $fail
