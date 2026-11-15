# Build the smallest coding agent

Build for [Build the smallest coding agent: a tool-calling loop in fifty lines](https://seekanddeploy.io/news/build-the-smallest-agent) by Sora Villanueva.

## What this is

A coding-agent loop in 50 lines of Node: `agent.mjs` (the loop and one tool, `run_command`) and `scripted-model.mjs` (a **scripted stand-in** for a language model; it plays back fixed steps and is not AI). It fixes the one failing test in `project-template/`. No API key, no network, no dependencies.

## Requirements

- Logged on Linux x86_64 (Ubuntu 24.04.5) with Node.js v22.23.4
- Any recent Node.js with ES modules should work. Only built-ins are used.

## Run it

```bash
./reset.sh && node agent.mjs      # copy project-template/ to project/ and run the agent
```

Try the variations from the article:

```bash
./reset.sh && sed -i 's/a - b/a * b/' project/math.mjs && node agent.mjs   # a bug the script doesn't know
./reset.sh && sed -i 's/a - b/a + b/' project/math.mjs && node agent.mjs   # nothing to fix
```

Warning: `run_command` runs whatever command the model asks for, with no permission check. That's fine with the scripted model, which only sends three fixed commands. Don't connect a real model to it without adding permissions or a sandbox.

## What broke

- **Empty tool output.** `sed -i` prints nothing, so a tool result came back blank. Fixed with `|| '(no output)'`.
- **The agent exits 0 when it gives up.** This is left in on purpose so it stays visible. The article and the run log explain the fix.

Full detail in [RUN-LOG.md](RUN-LOG.md).
