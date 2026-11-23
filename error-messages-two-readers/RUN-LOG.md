# Run log: error-messages-two-readers

- **Writer:** Wren Halloran
- **Started:** 2026-11-23
- **Environment:** SeekDeploy cloud container, Ubuntu 24.04.5 LTS, Linux 6.18 x86_64. Outbound HTTPS goes through a proxy (this matters for the curl case).
- **Versions:** git 2.43.0, npm 10.9.9 (node v22.23.4), Python 3.13.18 (and 3.12 for the pip case), pip 24.0, cargo 1.97.0, curl 8.5.0, jq 1.7, GNU tar 1.35, GNU grep 3.11, Docker 29.9.2 (no daemon running), GNU Make 4.3. Full list in `logs/env.txt`.
- **Model:** none. No language model was used. The "agent" is a script (`run.py`) that acts only on the text of each error message.
- **Times:** log headings use the file modification time (UTC) of each output in `logs/`.

## Method

`cases.py` holds 17 failing commands from 11 CLIs. Each case runs in a fresh
temp directory with `HOME` pointing at that directory and `GIT_CONFIG_NOSYSTEM=1`,
so no identity or config leaks in from the machine.

`run.py` collects the exit code and the full stdout and stderr, then lets a
scripted agent try to recover. Its three rules were written before the first
run and are the same for every case:

- **R1:** text in backticks or quotes whose first word is an executable on `PATH`.
- **R2:** a line whose first word is an executable on `PATH`, after stripping
  common log prefixes (`error:`, `fatal:`, `hint:`, `npm error`, ...) and `# comments`.
- **R3:** a "did you mean", "most similar command" or "perhaps you meant"
  suggestion, substituted for the closest-matching word of the original command.

It tries at most three candidates, in that order. For R1 and R2 it runs the
candidate and then reruns the original command. For R3 it runs the corrected
command. A case is resolved when that run exits 0. A candidate containing a
placeholder (`path/to`, `<...>`, `example.com`, `Your Name`, `...`) is flagged.

The agent cannot read docs, cannot reason, and cannot chain steps. That is
deliberate: it measures what the message itself hands a machine, not how
clever a model is.

## Log

### 2026-11-23 15:07 UTC: first run

```text
$ python3 run.py        # full output: logs/run-1.txt
git-no-upstream          exit=128 tried  R1:'git help config'->128; R2:'git push --set-upstream origin feat'->128
npm-missing-script       exit=1   tried  R1:'tset'->1; R2:'npm set'->1; R2:'npm run'->1
python-missing-module    exit=1   tried  R2:'import sklearn'->1
pip-externally-managed   exit=0   no-candidate
cargo-no-manifest        exit=1   tried  R1:'rustup default stable'->101; ...
```

Several results were wrong because of my harness, not the CLIs. See What
broke #1 to #3. Two results were real and surprising. See What broke #4.

### 2026-11-23 15:08 UTC: fixes, second run

Added a per-case working directory, passed `RUSTUP_HOME` and `CARGO_HOME`
through, moved the pip case to Python 3.12, and recorded each candidate's own
output as well as the rerun. Output in `logs/run-2.txt`.

### 2026-11-23 15:08 UTC: machine-readable modes

```text
$ ./json-modes.sh       # full output: logs/json-modes.txt
--- cargo build --message-format=json (no Cargo.toml)
error: could not find `Cargo.toml` in `/tmp/tmp.KwvJTtl7KI` or any parent directory
exit 101
--- npm run tset --json (stdout only)
{
  "error": {
    "summary": "Missing script: \"tset\"\n\nDid you mean this?\n  npm set # Set a value in the npm configuration\n\nTo see a list of scripts, run:\n  npm run",
    "detail": ""
  }
}
exit 1
```

Cargo's JSON mode does not cover this error: it still prints plain text.
npm's `--json` wraps the same human text in one string.

### 2026-11-23 15:21 UTC: final run, from this folder

```text
$ python3 run.py        # logs/run-3-final.txt, results.json
git-no-upstream          exit=128 RESOLVED  R1:'git help config'->128; R2:'git push --set-upstream origin feat'->0
git-no-identity          exit=128 RESOLVED (placeholder)  R2:'git config --global user.email "you@example.com"'->0
git-typo                 exit=1   RESOLVED  R1:'git --help'->1; R3:'git status'->0
git-bad-pathspec         exit=1   no-candidate
git-dirty-merge          exit=1   no-candidate
git-push-behind          exit=1   tried  R1:'git pull'->1; R1:'git push --help'->1
npm-missing-script       exit=1   tried  R1:'tset'->1; R2:'npm set'->1; R2:'npm run'->1
python-nameerror         exit=1   RESOLVED  R3:"python3 -c 'print(1)'"->0
python-missing-module    exit=1   tried  R2:'import sklearn'->1
pip-externally-managed   exit=1   no-candidate
cargo-no-manifest        exit=101 no-candidate
curl-bad-host            exit=56  no-candidate
jq-index-number          exit=5   no-candidate
grep-bad-regex           exit=2   no-candidate
tar-missing-file         exit=2   no-candidate
docker-no-daemon         exit=1   no-candidate
make-no-makefile         exit=2   no-candidate
```

The outcome column is identical to run 2. The cases are deterministic, so
one final run is the record. Four of 17 resolved, one of those by writing a
placeholder identity into git's config.

## Findings beyond resolved / not resolved

- **git-push-behind:** git's own suggestion, `git pull`, failed with exit 128
  and a new hint listing three `git config pull.*` choices. Recovering takes
  three steps (choose a strategy, pull, push), and the second message asks the
  reader to make a decision.
- **npm-missing-script:** for `npm run tset` with a `test` script present,
  npm's "Did you mean this?" suggests `npm set # Set a value in the npm
  configuration`. It matched against npm's own commands, not the project's scripts.
- **pip-externally-managed:** every fix is written as prose with placeholders
  (`apt install python3-xyz`, `python3 -m venv path/to/venv`, `pipx install
  xyz`). The only literal flag is `--break-system-packages`, which the message
  says risks breaking the Python installation.
- **curl-bad-host:** exit 56 (`CONNECT tunnel failed, response 502`) is what
  this container's proxy produces. I did not observe curl's direct DNS failure
  here, so I make no claim about its exit code from this run.
- **Exit codes:** 9 of 17 cases exit 1. git uses 128 for `fatal:` and 1 for
  others; jq 5, grep 2, tar 2, make 2, cargo 101, curl 56 here.

## What broke

1. **Candidates ran in the wrong directory.** Expected `git push
   --set-upstream origin feat` to succeed. Actual: exit 128 with the same
   error. Cause: the case command started with `cd work &&` but candidates ran
   in the temp root, so git was not even in the repo. Found by reading the
   rerun output. Fix: a `cwd` field per case. git's own suggestion then worked.
2. **My isolation broke cargo.** Expected cargo's "no Cargo.toml" error.
   Actual: `rustup could not choose a version of cargo to run ... no default
   is configured`, because a fresh `HOME` hid the real rustup toolchain.
   The agent ran rustup's suggested `rustup default stable`, which exited 0 and
   only exposed the next error. Fix: pass the real `RUSTUP_HOME` and `CARGO_HOME`.
3. **The pip case did not reproduce at first.** Expected PEP 668's
   externally-managed error. Actual: `Requirement already satisfied`, exit 0.
   Cause: the `EXTERNALLY-MANAGED` marker is in `/usr/lib/python3.12/`, but
   `python3` here is 3.13 in `/usr/local`. Fix: run the case with `python3.12 -m pip`.
4. **The agent ran programs nobody asked for.** Not a harness bug, so not
   fixed: this is a finding. In the npm case R1 picked `'tset'` out of
   `Missing script: "tset"`. `/usr/bin/tset` exists (ncurses, "initialize or
   reset terminal state") and ran, exiting 10 with `terminal attributes: No
   such device or address`. In the Python case R2 took the traceback line
   `import sklearn` as a command. `/usr/bin/import` is ImageMagick
   6.9.12-98, whose help text reads `Usage: import [options ...] [ file ]`. It
   exited 1 with `unable to open X server`. Both were harmless only because
   this container has no terminal attached and no display.
5. **Smaller:** I first ran `python3 -I run.py`, which drops the script's own
   folder from the import path (`ModuleNotFoundError: No module named 'tasks'`).
   `git help config` and `git push --help` print Ubuntu's "This system has been
   minimized" notice here instead of a man page.

## Clean up

Every case runs in its own temp directory, which `run.py` deletes afterwards.
No daemons were started.
