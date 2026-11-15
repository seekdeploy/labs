# Keep a lab notebook for your agent sessions

Build for [Keep a lab notebook for your agent sessions](https://seekanddeploy.io/news/agent-lab-notebook) by Idris Okonjo (a SeekDeploy house byline; see the note below).

## What this is

A plain-Markdown notebook format for coding-agent sessions: dated, versioned,
one entry per prompt with the outcome and how it was checked. There's a blank
template and one filled-in example.

The example log records a session run by an AI agent (Claude, in Claude Code)
working under the Idris Okonjo byline. The log says so at the top.

## Files

- `TEMPLATE.md`: copy this for each session
- `EXAMPLE-LOG.md`: the template filled in for one real session
- `RUN-LOG.md`: how this folder was made

## Requirements

A text editor. Nothing to install.

## Run it

```bash
cp TEMPLATE.md "$(date -u +%F)-my-task.md"
```

## What broke

Seven entries in the example log, from a misleading-looking fetch summary to
a clock mismatch that was never resolved. See the table in
[EXAMPLE-LOG.md](EXAMPLE-LOG.md#what-broke).
