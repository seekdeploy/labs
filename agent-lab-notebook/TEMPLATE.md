# Agent lab notebook

One file per session. Copy this file, name it `YYYY-MM-DD-<short-task>.md`,
and fill it in as you go, not afterwards.

## Session header

- **Date (UTC):** YYYY-MM-DD, start HH:MM, end HH:MM
- **Who is driving:** the person (or agent) giving instructions, and who reviews the output
- **Agent:** product and exact version (e.g. `claude --version`)
- **Model:** exact identifier if you can record it; if not, say why
- **Where it ran:** OS, machine or container, network limits
- **Repo and starting commit:** `owner/repo@sha`
- **Task, in one sentence:**
- **Cost or usage, if visible:** and where the number came from

## Entries

One entry per prompt or decision. Keep them short. Paste real output; trim,
don't rewrite.

### HH:MM — <what I asked for or decided>

- **Prompt / instruction:** exact text, or a link to it
- **What the agent did:** tools called, files touched, commands run
- **Outcome:** worked / partly / failed, and how I know (test, diff read, output)
- **Observed vs suspected:** keep these apart in so many words

## What broke

For each failure: what I expected, what happened (real output), how I found
the cause, the fix. If it was never fixed, say so.

## Verified, and how

Every claim that left the session (in a commit, an article, a message), and
what checked it: a test, a primary source, a second tool, a person.

## Sample size

How many sessions this notebook covers, on what kind of code. One session is
an anecdote.
