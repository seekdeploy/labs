# Keep a lab notebook for your agent sessions

Build for [Keep a lab notebook for your agent sessions](https://seekanddeploy.io/news/agent-lab-notebook) by Idris Okonjo.

## What this is

A plain-Markdown notebook format for coding-agent sessions: dated, versioned,
one entry per instruction with the outcome and how it was checked. There's a
blank template and one example kept live during a real session, in which Aider
with a free OpenRouter model fixed python-tabulate issue #434 locally, in four
runs.

## Files

- `TEMPLATE.md`: copy this for each session
- `EXAMPLE-LOG.md`: the template filled in during the session
- `prompt-1.txt`, `prompt-2.txt`: the exact instructions given to Aider
- `final.diff`: the reviewed change, against `astanin/python-tabulate@268615a`
- `RUN-LOG.md`: environment and setup for this build

## Requirements

- The notebook: a text editor.
- To repeat the example: Linux, Python 3.10 to 3.12 (aider-chat 0.86.2 doesn't support 3.13), git, an OpenRouter key.

## Run it

```bash
cp TEMPLATE.md "$(date -u +%F)-my-task.md"
```

To repeat the example session:

```bash
git clone https://github.com/astanin/python-tabulate && cd python-tabulate
git checkout 268615a5c27dc40e5c22454c07b44d5c50410da0   # needs enough history; use --depth 50 or more
python3.12 -m venv ../venv && ../venv/bin/pip install aider-chat -e . pytest
OPENROUTER_API_KEY=... ../venv/bin/aider --model openrouter/cohere/north-mini-code:free \
  --edit-format diff --no-auto-commits --message "$(cat ../prompt-1.txt)" \
  tabulate/__init__.py test/test_output.py
../venv/bin/python -m pytest -q
```

Expect different output: the same prompt produced different failures on two runs.

## What broke

Eight entries: a Python version trap on install, two rejected targets, an
edit format that couldn't fit the file, a test Aider got wrong, a repetition
loop, and an unrelated test Aider quietly broke. Details in
[EXAMPLE-LOG.md](EXAMPLE-LOG.md#what-broke).
