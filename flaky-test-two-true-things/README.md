# A flaky test is telling you two true things

Build for [A flaky test is telling you two true things](https://seekanddeploy.io/news/flaky-test-two-true-things) by Sora Villanueva.

## What this is

A **deliberately** flaky test for a search box, plus a flake meter that runs a test file many times and tallies failures by what the assertion saw. The flakiness has two planted causes, a fixed sleep in the test and a stale-reply bug in the app, and the files let you fix each one separately:

| Test file | App | What it shows |
|---|---|---|
| `search.test.mjs` | `search.mjs` | both bugs (the baseline) |
| `search.waits.test.mjs` | `search.mjs` | test fixed, app bug left |
| `search.fixed-app.sleep.test.mjs` | `search.fixed.mjs` | app fixed, test bug left |
| `search.fixed-app.waits.test.mjs` | `search.fixed.mjs` | both fixed |

## Requirements

- Logged on Linux x86_64 (Ubuntu 24.04.5) with Node.js v22.23.4
- Node's built-in test runner only, no npm packages

## Run it

```bash
node --test search.test.mjs                      # one run: may pass or fail
node flake-meter.mjs search.test.mjs 200         # 200 runs, tallied (about 30 s in the logged runs)
node flake-meter.mjs search.waits.test.mjs 200
node flake-meter.mjs search.fixed-app.sleep.test.mjs 200
node flake-meter.mjs search.fixed-app.waits.test.mjs 200
```

The latency is random, so your counts will differ from the log. The pattern of messages shouldn't.

## What broke

- **A `sed` edit half-applied** while making the first fix. I caught it by printing the file, rewrote the file by hand, and measured again. Both runs are in the log.

Full detail in [RUN-LOG.md](RUN-LOG.md).
