# CI is the agent's guardrail

Build for [CI is the agent's guardrail](https://seekanddeploy.io/news/ci-agent-guardrail) by Tobias Brandt.

## What this is

A four-job pipeline (tests, size, provenance trailers, tamper check) on a small
Python project in a local Gitea, and thirteen scripted agent-style pull
requests that try to get past it, first without branch protection and then
with it. It answers which of these gates catch which kinds of agent-style
change, and which changes get through. The pull requests are written by hand
to imitate agent output; no model was used.

## Requirements

- Linux x86_64. Run on Ubuntu 24.04.5 LTS in a cloud container, 4 vCPU, 16 GB RAM.
- Gitea 28.4.0 and Gitea Runner 6.0.0 (host mode). Checksums are in the run
  log; the binaries are not committed.
- git 2.43 and Python 3.13 on the runner host.

## Run it

```bash
# 1. Start Gitea with harness/app.ini as a non-root user; create a "maintainer"
#    admin and an "agent-bot" user, each with an API token; register a runner
#    with label lab:host.
# 2. Create maintainer/tally, push harness/tally/ to main, and add agent-bot as
#    a collaborator with write access.
# 3. Open the pull requests as agent-bot:
AGENT_TOKEN=... bash harness/make_prs.sh        http://127.0.0.1:3002 maintainer/tally /tmp/work
AGENT_TOKEN=... bash harness/make_prs_round2.sh http://127.0.0.1:3002 maintainer/tally /tmp/work
# 4. Read the check results:
GITEA_TOKEN=... python3 harness/collect.py http://127.0.0.1:3002 maintainer/tally
# 5. Apply branch protection and try to merge each PR as agent-bot:
MAINTAINER_TOKEN=... AGENT_TOKEN=... WORKDIR=<clone of tally> \
  python3 harness/try_merges.py http://127.0.0.1:3002 maintainer/tally <original main sha> harness/protection-stage1b.json
```

The exact sequence, including the cases added along the way (G2b, G4, G5),
is in [RUN-LOG.md](RUN-LOG.md).

## What broke

- **No tests ran:** `tests/` needed an `__init__.py`.
- **"Please try again later":** Gitea refuses merges while it re-checks
  mergeability after a protection change. Retry.
- **Protected-file patterns matched nothing:** Gitea treats `.` as a glob
  separator, so `ci/*` does not match `ci/check_size.sh`. Use `ci/**`. Until I
  fixed this, two pull requests that edited the guardrail were merged.
- **One case was caught by accident:** its code change broke a test, masking
  the result. Re-run as G2.
