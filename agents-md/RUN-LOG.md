# Run log: agents-md

- **Writer:** Sora Villanueva
- **Started:** 2026-11-23
- **Environment:** Linux cloud container, Ubuntu 24.04.5 LTS, x86_64, 4 vCPU, 15 GB RAM, no GPU
- **Versions:** Node.js v22.23.4, node-llama-cpp 3.22.3 (CPU build)
- **Target repo:** [sindresorhus/slugify](https://github.com/sindresorhus/slugify) at commit `99b35c2b0d6ccfad2b96ba9ce6997c6365b9a4b7` (2026-11-09), cloned locally. Nothing was sent upstream: no PR, no issue, no push.
- **Models (free, local, Apache-2.0):**
  - `qwen2.5-coder-1.5b-instruct-q4_k_m.gguf`, 1,117,320,768 bytes, sha256 `cc324af070c2ecbfd324a30884d2f951a7ff756aba85cb811a6ec436933bb046`
  - `qwen2.5-coder-7b-instruct-q4_k_m.gguf`, 4,683,073,536 bytes, sha256 `509287f78cb4d4cf6b3843734733b914b2c158e43e22a7f4bf5e963800894d3c`
- **Accounts, API keys or signups:** none

Two kinds of entries below. Most were captured to files as they ran, and each of those headings was printed by the command with `date -u`. The ones marked *(from the terminal)* weren't logged to a file. Their output is pasted from my terminal session, trimmed to the lines shown, and not rewritten.

## Log

### 2026-11-23 ~15:20 UTC: clone slugify, install, run its tests *(from the terminal)*

```text
$ git clone --depth 1 https://github.com/sindresorhus/slugify
$ git log -1 --format='%H %cs'
99b35c2b0d6ccfad2b96ba9ce6997c6365b9a4b7 2026-11-09
$ npm install --no-audit --no-fund
real	0m21.555s
$ npm test
# tests 84
# pass 84
# fail 0
real	0m5.702s
```

Then I traced an existing option (`preserveTrailingDash`) through `index.js`, `index.d.ts`, `readme.md` and `test.js`, and checked that `index.d.ts` uses `@default` in its JSDoc (9 occurrences). That's the evidence for the "four places" rule in AGENTS.md.

### 2026-11-23 15:22 UTC: check the single-test command from AGENTS.md

```text
$ node --test --test-name-pattern="decamelize acronyms"
# tests 1
# pass 1
# fail 0
# skipped 0
```

The single-test command recommended in AGENTS.md works.

### 2026-11-23 ~15:22 UTC: model and runtime setup *(from the terminal)*

```text
$ npm i node-llama-cpp@3
added 124 packages in 15s
$ node -p "require('./node_modules/node-llama-cpp/package.json').version"
3.22.3
$ curl -s https://huggingface.co/api/models/Qwen/Qwen2.5-Coder-1.5B-Instruct-GGUF   # licence field
apache-2.0
$ curl -sSL -o qwen2.5-coder-1.5b-instruct-q4_k_m.gguf https://huggingface.co/Qwen/Qwen2.5-Coder-1.5B-Instruct-GGUF/resolve/main/qwen2.5-coder-1.5b-instruct-q4_k_m.gguf
real	0m14.870s
```

### 2026-11-23 15:23 UTC: smoke test, 1 run per condition

```text
$ node experiment.mjs <model> <repo> AGENTS.md 1 smoke.json
[node-llama-cpp] The prebuilt binary for platform "linux" "x64" with Vulkan support is not compatible with the current system, falling back to using no GPU
[node-llama-cpp] load: control-looking token: 128247 '</s>' was not control-type; this is probably a bug in the model. its type will be overridden
without seed 1: 2/6
with    seed 1: 5/6

real	0m59.409s
user	3m37.523s
sys	0m2.111s
```

The first smoke test used a 6-check rubric (the first six checks in `experiment.mjs`). Reading the "with" reply showed it scored 5/6 while proposing nonsense, such as editing `.gitignore` to ignore the `.js` files. It had echoed file names from AGENTS.md. **I added a 7th check, `leaves other files alone`, before the main run.** The reply is in `results/smoke-1.5b.json`, which still has the 6-check scores.

### 2026-11-23 15:24 UTC: main run, 10 seeds per condition, 7-check rubric

```text
$ node experiment.mjs <model> <repo> AGENTS.md 10 results.json
without seed 1: 3/7
without seed 2: 1/7
without seed 3: 2/7
without seed 4: 5/7
without seed 5: 1/7
without seed 6: 4/7
without seed 7: 2/7
without seed 8: 1/7
without seed 9: 2/7
without seed 10: 2/7
with    seed 1: 5/7
with    seed 2: 6/7
with    seed 3: 4/7
with    seed 4: 5/7
with    seed 5: 6/7
with    seed 6: 7/7
with    seed 7: 6/7
with    seed 8: 7/7
with    seed 9: 7/7
with    seed 10: 7/7

real	7m5.115s
user	26m44.080s
sys	0m6.922s
```

Main run, 1.5B model.

check                      without with

```text
edits index.js                3/10   10/10
edits index.d.ts              2/10   10/10
edits readme.md               1/10    9/10
edits test.js                 1/10    9/10
runs npm test                 5/10    5/10
no other test runner         10/10    9/10
leaves other files alone      1/10    8/10
mean without 2.3 mean seconds 15.3
mean with 6.0 mean seconds 26.7
```

Per-check counts for the 1.5B model. Reading the replies showed problems the rubric can't see, so I added pattern searches and then read every match. The next entry has those counts.

extra check (counted after reading the replies)  without with

```text
writes code anyway (```js/javascript block)         0/10    4/10
uses CommonJS (require/module.exports)              0/10    2/10
suggests npm test --test-name-pattern               0/10    1/10
suggests node --test --test-name-pattern            0/10    1/10
```

These counts are pattern matches, and I read every hit to confirm it. The four code-writing replies are seeds 3, 5, 7 and 8. The two CommonJS ones are seeds 3 and 8, and seed 8 scored 7/7 on the rubric anyway.

### 2026-11-23 15:31 UTC: what the model's 'npm test --test-name-pattern' actually does

```text
$ npm test --test-name-pattern="decamelize acronyms"
> @sindresorhus/slugify@4.0.1 test
> xo && node --test
# tests 84
# pass 84
# fail 0
```

Seed 6 (1.5B, with AGENTS.md) suggested `npm test --test-name-pattern=...`. I ran it: npm treats the flag as its own setting, runs the whole suite (84 tests), and reports success. There was no error, and it didn't do what was asked.

### 2026-11-23 ~15:32 UTC: choosing a second model *(from the terminal)*

```text
Qwen2.5-Coder-3B-Instruct other qwen-research https://huggingface.co/Qwen/Qwen2.5-Coder-3B-Instruct/blob/main/LICENSE
Qwen2.5-Coder-7B-Instruct-GGUF apache-2.0 None https://huggingface.co/Qwen/Qwen2.5-Coder-7B-Instruct-GGUF/blob/main/LICENSE
$ curl -sSL -o qwen2.5-coder-7b-instruct-q4_k_m.gguf https://huggingface.co/Qwen/Qwen2.5-Coder-7B-Instruct-GGUF/resolve/main/qwen2.5-coder-7b-instruct-q4_k_m.gguf
real	1m2.692s
```

I skipped the 3B model because of its `qwen-research` licence and used the Apache-2.0 7B instead.

### 2026-11-23 15:33 UTC: repeat with the 7B model, 10 seeds per condition, same 7-check rubric

```text
$ node experiment.mjs <7B model> <repo> AGENTS.md 10 results-7b.json
without seed 1: 5/7
without seed 2: 7/7
without seed 3: 6/7
without seed 4: 5/7
without seed 5: 6/7
without seed 6: 6/7
without seed 7: 6/7
without seed 8: 6/7
without seed 9: 5/7
without seed 10: 6/7
with    seed 1: 7/7
with    seed 2: 7/7
with    seed 3: 7/7
with    seed 4: 7/7
with    seed 5: 7/7
with    seed 6: 7/7
with    seed 7: 7/7
with    seed 8: 7/7
with    seed 9: 7/7
with    seed 10: 7/7

real	12m13.928s
user	47m12.490s
sys	0m9.475s
```

Main run, 7B model. Same prompt, seeds and 7-check rubric.

check                      without with

```text
edits index.js               10/10   10/10
edits index.d.ts              9/10   10/10
edits readme.md               2/10   10/10
edits test.js                 9/10   10/10
runs npm test                10/10   10/10
no other test runner          9/10   10/10
leaves other files alone      9/10   10/10
+ writes code anyway (js/ts fence)    0/10    0/10
+ uses CommonJS               0/10    0/10
+ npm test --test-name-pattern    0/10    0/10
+ node --test --test-name-pattern    0/10    1/10
+ runs xo or npx xo           0/10    0/10
mean without 5.8 mean seconds 34.7
mean with 7.0 mean seconds 37.9
```

The 7B model got most checks right without AGENTS.md. The one it missed was `readme.md`, which went from 2/10 to 10/10. Without the file, seed 9 planned `npm install --save-dev @types/jest` and seed 4 planned to edit `package.json`. Neither happened with the file.

## What broke

**The first rubric measured repetition, not following (fixed).**
- **Expected:** keyword checks would show whether the plan follows AGENTS.md.
- **Actual:** in the smoke run, a 1.5B reply scored 5/6 by repeating file names from AGENTS.md inside a plan that edited the wrong files.
- **Cause found by:** reading the reply instead of only the score.
- **Fix:** added `leaves other files alone` before the main runs, plus pattern searches with every hit read (05). The rubric still can't judge whether a plan is *sensible*, and the article says so.

**3B model dropped over its licence (worked around).** `qwen-research` isn't Apache-2.0, and SeekDeploy is commercial, so I used the 7B instead.

**A model-suggested command failed silently.** See the 06 entry. This is a finding, not a fault in the setup.

**Vulkan warning (harmless).** `node-llama-cpp` tried its Vulkan build, found no GPU, and fell back to CPU. That affects timing only.

## Screenshots

None. The terminal output above is the record.

| File | Shows | State produced by |
|---|---|---|
