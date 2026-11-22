# Run log: agent-lab-notebook

- **Writer:** Idris Okonjo
- **Started:** 2026-11-15
- **Environment:** cloud container, Ubuntu 24.04.5 LTS, x86_64, 4 vCPUs, 15 GiB RAM, outbound network through an allowlisting proxy
- **Versions:** Aider 0.86.2 on Python 3.12 (system default is 3.13.18), git 2.43.0, pytest from the python-tabulate dev install
- **Model:** `openrouter/cohere/north-mini-code:free` via OpenRouter

## Log

The session itself is logged entry by entry in [EXAMPLE-LOG.md](EXAMPLE-LOG.md).
This file covers setup and housekeeping.

### 2026-11-15 03:12: key and budget check

`curl -s https://openrouter.ai/api/v1/key` reported usage 0 of a $50 monthly
limit, on the free tier. That means free models only.

### 2026-11-15 03:13 to 03:14: installing Aider

The first install on Python 3.13 failed (see the log, entry 03:13). Rebuilt the venv on `python3.12`.

### Header fields

The session header's version, model and repo fields were written as
placeholders at the start and filled in from the entries at 03:36, once known.
Everything under "Entries" was written as it happened.

### Signups

None. No new accounts were created. The OpenRouter key was already configured
in the environment.

### Spend

$0.00. Free model, four runs. Key usage was 0 before and after.

### Cleanup

Nothing was left running. Aider ran one-shot (`--message`) each time. The
tabulate clone and the venvs were only ever in local scratch directories.

## What broke

All of it is in [EXAMPLE-LOG.md](EXAMPLE-LOG.md#what-broke). Nothing extra broke in packaging this folder.

## Screenshots

None. Terminal output is included as text.
