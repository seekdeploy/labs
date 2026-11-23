# Error messages now have two readers

Build for [Error messages now have two readers](https://seekanddeploy.io/news/error-messages-two-readers) by Wren Halloran.

## What this is

17 real error messages from 11 command-line tools, each reproduced in a fresh
temp directory, plus a scripted agent with no language model that tries to
recover using only the text of the message. It answers one question: what
does each message hand a machine that cannot ask anyone for help?

## Requirements

- Logged on Ubuntu 24.04.5 LTS, x86_64, Python 3.13 (Python 3.12 for the pip case)
- git 2.43.0, npm 10.9.9, cargo 1.97.0, curl 8.5.0, jq 1.7, GNU tar 1.35,
  GNU grep 3.11, GNU Make 4.3, Docker 29.9.2 CLI with no daemon. Full list in
  [logs/env.txt](logs/env.txt).

## Run it

```bash
python3 run.py          # collect each error, let the scripted agent try; writes results.json
./json-modes.sh         # do cargo's and npm's machine-readable modes cover the errors?
```

Run `run.py` without `python3 -I`: it imports `cases.py` from its own folder.
Results depend on which programs are on your `PATH`, which is part of the point.

## What broke

- **Candidates ran in the wrong directory**, so even git's own correct
  suggestion failed at first. Fixed with a per-case `cwd`.
- **A fresh `HOME` hid the rustup toolchain** and turned the cargo case into a
  different error. Fixed by passing `RUSTUP_HOME` and `CARGO_HOME` through.
- **The pip case did not reproduce** on Python 3.13; the PEP 668 marker is on 3.12.
- **The agent ran `tset` and ImageMagick's `import`**, because text in two
  error messages happened to be the names of real programs. Kept as a finding.

Full detail in [RUN-LOG.md](RUN-LOG.md).
