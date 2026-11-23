# Run log: vitest-critique

- **Writer:** Sora Villanueva
- **Started:** 2026-11-23
- **Environment:** Linux cloud container, Ubuntu 24.04.5 LTS, x86_64, 4 vCPU, 15 GB RAM
- **Versions:** Node.js v22.23.4, pnpm 10.33.0, Jest 30.0.5 + ts-jest 29.4.0 (as shipped), Vitest 5.1.1, @vitest/coverage-v8 5.1.1, @edge-runtime/vm 5.0.0
- **Project:** [vercel/ms](https://github.com/vercel/ms) at `4ff48cec099f0514c3e9bbca18706c9c21122bfb` (2026-05-20), cloned locally. The port stayed on a local branch. Nothing went upstream.
- **Accounts or signups:** none

**Probe tests are mine.** vercel/ms has no mocks or module state, so the isolation, mocking and runtime probes in `probes-*` were written for this build, Jest-style first. The vercel/ms tests themselves were changed only by the import swap.

Each heading line was printed by the command with `date -u`. Output is trimmed with `grep`/`tail` as shown in each command, and not otherwise edited.

## Log

### 2026-11-23 17:32 UTC: install as shipped

```text
$ pnpm install --frozen-lockfile
+ tsdown 0.13.0
+ typescript 5.8.3

. prepare$ husky
. prepare: Done
Done in 10.4s using pnpm v10.33.0

real	0m10.821s
user	0m4.996s
sys	0m1.137s
```

### 2026-11-23 17:33 UTC: Jest baseline, run 1

```text
$ pnpm test
All files |     100 |      100 |     100 |     100 |                   
Test Suites: 4 passed, 4 total
Tests:       167 passed, 167 total
Time:        1.657 s
Test Suites: 4 passed, 4 total
Tests:       167 passed, 167 total
Time:        0.87 s, estimated 1 s

real	0m4.941s
user	0m8.228s
sys	0m0.942s
```

Jest prints its summary twice because `pnpm test` runs the Node and Edge environments one after the other.

### 2026-11-23 17:33 UTC: Jest baseline, run 2

```text
$ pnpm test
All files |     100 |      100 |     100 |     100 |                   
Test Suites: 4 passed, 4 total
Tests:       167 passed, 167 total
Time:        0.589 s, estimated 1 s
Test Suites: 4 passed, 4 total
Tests:       167 passed, 167 total
Time:        0.686 s, estimated 1 s

real	0m3.609s
user	0m3.584s
sys	0m0.552s
```

### 2026-11-23 17:33 UTC: Jest baseline, run 3

```text
$ pnpm test
All files |     100 |      100 |     100 |     100 |                   
Test Suites: 4 passed, 4 total
Tests:       167 passed, 167 total
Time:        0.749 s, estimated 1 s
Test Suites: 4 passed, 4 total
Tests:       167 passed, 167 total
Time:        0.772 s, estimated 1 s

real	0m4.094s
user	0m3.992s
sys	0m0.643s
```

### 2026-11-23 17:33 UTC: add Vitest

```text
$ pnpm add -D vitest@5.1.1 @vitest/coverage-v8@5.1.1 @edge-runtime/vm@5.0.0
devDependencies:
+ @edge-runtime/vm 5.0.0
+ @vitest/coverage-v8 5.1.1
+ vitest 5.1.1

Done in 4.1s using pnpm v10.33.0
```

Then: `sed -i "s#from '@jest/globals'#from 'vitest'#" src/*.test.ts`, plus a 6-line `vitest.config.ts` with only `include`.

### 2026-11-23 17:33 UTC: first Vitest run: imports swapped, minimal config, no coverage

```text
$ npx vitest run

 RUN  v5.1.1 /home/user/vercel/ms


 Test Files  4 passed (4)
      Tests  167 passed (167)
   Start at  17:33:44
   Duration  498ms (transform 59%, import 20%, tests 16%, worker 4%)


real	0m1.355s
user	0m1.621s
sys	0m0.225s
```

It passed the first time.

### 2026-11-23 17:33 UTC: Edge runtime environment

```text
$ npx vitest run --environment edge-runtime
 RUN  v5.1.1 /home/user/vercel/ms


 Test Files  4 passed (4)
      Tests  167 passed (167)
   Start at  17:33:52
   Duration  511ms (environment 66%, import 13%, tests 11%, transform 6%, worker 4%)
```

### 2026-11-23 17:33 UTC: coverage with the same 100% thresholds Jest enforces

```text
$ npx vitest run

 RUN  v5.1.1 /home/user/vercel/ms
      Coverage enabled with v8


 Test Files  4 passed (4)
      Tests  167 passed (167)
   Start at  17:33:53
   Duration  511ms (transform 54%, worker 20%, import 16%, tests 11%)

[34m % [39m[2mCoverage report from [22m[33mv8[39m
No files with missing coverage.
1 file fully covered.

=============================== Coverage summary ===============================
Statements   : 100% ( 58/58 )
Branches     : 100% ( 48/48 )
Functions    : 100% ( 7/7 )
Lines        : 100% ( 58/58 )
================================================================================
exit=0
```

The config now has the same 100% thresholds as Jest (full config in `port.patch`). It passed with the v8 provider.

### 2026-11-23 17:34 UTC: probe: which runtime does each environment give? (probe test written by me)

```text
$ npx vitest run probe/env.test.ts --environment node --coverage.enabled=false
$ npx vitest run probe/env.test.ts --environment edge-runtime --coverage.enabled=false
```

Nothing printed, which wasn't what I expected. See the next entry.

### 2026-11-23 17:34 UTC: why the probe printed nothing (full output)

```text
$ npx vitest run probe/env.test.ts --environment node --coverage.enabled=false
 RUN  v5.1.1 /home/user/vercel/ms

No test files found, exiting with code 1

filter: probe/env.test.ts
include: src/**/*.test.ts
exclude:  **/node_modules/**, **/.git/**

exit=1
```

My mistake: the project config's `include` filters out probe files.

### 2026-11-23 17:34 UTC: probe with its own config

```text
$ npx vitest run --config probe/vitest.config.ts env --environment node
      Tests  1 passed (1)
$ npx vitest run --config probe/vitest.config.ts env --environment edge-runtime
      Tests  1 passed (1)
```

Both runs passed, but the `console.log` didn't appear in the output, so I put the result in the test name instead.

### 2026-11-23 17:34 UTC: probe, runtime reported in the test name (console.log from a passing test did not appear in the default reporter)

```text
$ npx vitest run --config probe/vitest.config.ts env --environment node --reporter=verbose
 ✓ probe/env.test.ts > runtime: EdgeRuntime is undefined, process.versions.node is string 2ms
$ npx vitest run --config probe/vitest.config.ts env --environment edge-runtime --reporter=verbose
 ✓ probe/env.test.ts > runtime: EdgeRuntime is string, process.versions.node is string 2ms
```

Vitest's `edge-runtime` sets `EdgeRuntime`, and `process.versions.node` is still present.

### 2026-11-23 17:34 UTC: same probe under Jest's environments (probe written by me)

```text
$ npx jest --env node --rootDir probe-jest --testMatch '**/*.test.ts' --no-coverage --verbose
  ✓ runtime: EdgeRuntime is undefined, process.versions.node is string (2 ms)
Tests:       1 passed, 1 total
$ npx jest --env @edge-runtime/jest-environment --rootDir probe-jest --testMatch '**/*.test.ts' --no-coverage --verbose
  ✓ runtime: EdgeRuntime is string, process.versions.node is string (3 ms)
Tests:       1 passed, 1 total
```

Jest's Edge environment behaves the same way, so this isn't a Vitest-specific difference.

### 2026-11-23 17:34 UTC: wall-clock timing, Node environment, coverage on, 4 vCPU container

```text
Jest: $ npx jest --env node   (after npx jest --clearCache for the cold run)
  cold: 1.86 s (exit 1)
  warm 1: 1.81 s (exit 1)
  warm 2: 1.63 s (exit 1)
  warm 3: 1.68 s (exit 1)
  warm 4: 1.65 s (exit 1)
  warm 5: 1.63 s (exit 1)
Vitest: $ npx vitest run   (after rm -rf node_modules/.vite for the cold run)
  cold: 1.16 s (exit 0)
  warm 1: 1.10 s (exit 0)
  warm 2: 1.18 s (exit 0)
  warm 3: 1.16 s (exit 0)
  warm 4: 1.15 s (exit 0)
  warm 5: 1.19 s (exit 0)
```

**These Jest numbers are invalid.** Every run exited 1. See the next entry.

### 2026-11-23 17:35 UTC: why Jest exited 1 during timing

```text
$ npx jest --env node
      3 |
      4 | // numbers
      at Object.<anonymous> (node_modules/.pnpm/vitest@5.1.1_@edge-runtime+vm@5.0.0_@types+node@24.1.0_@vitest+coverage-v8@5.1.1_vite@8_4405999f3cdd6e8cb623cbfdc0fef168/node_modules/vitest/index.cjs:1:7)
      at Object.<anonymous> (src/format.test.ts:1:1)
FAIL src/parse.test.ts
  ● Test suite failed to run
    Vitest cannot be imported in a CommonJS module using require(). Please use "import" instead.
    If you are using "import" in your source code, then it's possible it was bundled into require() automatically by your bundler. In that case, do not bundle CommonJS output since it will never work with Vitest, or use dynamic import() which is available in all CommonJS modules.
    > 1 | import { describe, expect, it } from 'vitest';
        | ^
      2 | import { parse } from './index';
      3 |
      4 | describe('parse(string)', () => {
      at Object.<anonymous> (node_modules/.pnpm/vitest@5.1.1_@edge-runtime+vm@5.0.0_@types+node@24.1.0_@vitest+coverage-v8@5.1.1_vite@8_4405999f3cdd6e8cb623cbfdc0fef168/node_modules/vitest/index.cjs:1:7)
      at Object.<anonymous> (src/parse.test.ts:1:1)
----------|---------|----------|---------|---------|-------------------
File      | % Stmts | % Branch | % Funcs | % Lines | Uncovered Line #s 
----------|---------|----------|---------|---------|-------------------
All files |       0 |        0 |       0 |       0 |                   
----------|---------|----------|---------|---------|-------------------
Test Suites: 4 failed, 4 total
Tests:       0 total
Snapshots:   0 total
Time:        0.871 s
Ran all test suites.
```

Cause: I timed Jest in the folder where I'd already swapped the imports to `vitest`. The Vitest numbers in 08 are valid (exit 0).

### 2026-11-23 17:35 UTC: Jest timing again, on an untouched worktree of the original commit

```text
Jest: $ npx jest --env node   (after npx jest --clearCache for the cold run)
  cold: 2.27 s (exit 0)
  warm 1: 1.40 s (exit 0)
  warm 2: 1.50 s (exit 0)
  warm 3: 1.44 s (exit 0)
  warm 4: 1.47 s (exit 0)
  warm 5: 1.53 s (exit 0)
Jest, Edge environment: $ npx jest --env @edge-runtime/jest-environment --no-coverage
  warm 1: 1.66 s (exit 0)
  warm 2: 1.17 s (exit 0)
  warm 3: 1.30 s (exit 0)
Vitest, Edge environment: $ npx vitest run --environment edge-runtime --coverage.enabled=false
  warm 1: 1.14 s (exit 0)
  warm 2: 1.12 s (exit 0)
  warm 3: 1.15 s (exit 0)
```

Jest re-timed on `git worktree add ../ms-jest main` (the original commit), after `pnpm install --frozen-lockfile`. These are the numbers in the article.

### 2026-11-23 17:35 UTC: isolation probe: two files share a module-level counter (probe written by me)

```text
$ npx vitest run --config probe/vitest.config.ts isolation --isolate=true --pool=threads --maxWorkers=1
      Tests  2 passed (2)
$ npx vitest run --config probe/vitest.config.ts isolation --isolate=false --pool=threads --maxWorkers=1
   × starts from a fresh module 5ms
⎯⎯⎯⎯⎯⎯⎯ Failed Tests 1 ⎯⎯⎯⎯⎯⎯⎯
 FAIL  probe/isolation/b.test.ts > starts from a fresh module
AssertionError: expected 2 to be 1 // Object.is equality
      Tests  1 failed | 1 passed (2)
```

Probe files are in `probes-vitest/isolation/`.

### 2026-11-23 17:36 UTC: mocking probes under Jest 30, with --testMatch (the first attempt found no tests: the project's testMatch only covers src/)

```text
$ npx jest --rootDir probe-mock --testMatch '**/*.test.ts' --preset ts-jest --no-coverage --verbose
  ✓ first test calls once (4 ms)
  ✓ second test sees both calls (2 ms)
  ✓ uses the mocked default export (4 ms)
  ✓ mockReset forgets the implementation (4 ms)
Tests:       4 passed, 4 total
```

The probes are in `probes-jest/mock/`. A first attempt without `--testMatch` printed "No tests found", because the project's testMatch only covers `src/`. The heading records this; that attempt's output wasn't kept.

### 2026-11-23 17:36 UTC: the same probes, ported literally (jest. -> vi., @jest/globals -> vitest), Vitest 5.1.1

```text
$ npx vitest run --config probe/vitest.config.ts mock --reporter=verbose
 × probe/mock/reset.test.ts > mockReset forgets the implementation 5ms
   → expected 'original' to be undefined
 ✓ probe/mock/counts.test.ts > first test calls once 2ms
 × probe/mock/counts.test.ts > second test sees both calls 3ms
   → expected "vi.fn()" to be called 2 times, but got 1 times
TypeError: [vitest] vi.mock("./format-name", factory?: () => unknown) is not returning an object. Did you mean to return an object with a "default" key?
⎯⎯⎯⎯⎯⎯⎯ Failed Tests 2 ⎯⎯⎯⎯⎯⎯⎯
AssertionError: expected "vi.fn()" to be called 2 times, but got 1 times
AssertionError: expected 'original' to be undefined
      Tests  2 failed | 1 passed (3)
```

The literal port: `sed -e "s#from '@jest/globals'#from 'vitest'#" -e "s#\bjest\b#vi#g"` on copies of the Jest probes. All three differences from Vitest's Jest migration guide reproduce. The factory error fails the whole file.

### 2026-11-23 17:36 UTC: probes after the three fixes ({ default } in the factory; assert Vitest's mockReset; count per test)

```text
$ npx vitest run --config probe/vitest.config.ts mock --reporter=verbose
 ✓ probe/mock/counts.test.ts > first test calls once 2ms
 ✓ probe/mock/counts.test.ts > second test counts its own call 0ms
 ✓ probe/mock/reset.test.ts > mockReset restores the original implementation 3ms
 ✓ probe/mock/factory.test.ts > uses the mocked default export 4ms
      Tests  4 passed (4)
```

The fixed versions are in `probes-vitest/mock/`.

### 2026-11-23 17:36 UTC: watch mode: start, append a newline to src/format.test.ts, then to src/index.ts (both reverted afterwards)

```text
$ npx vitest watch --coverage.enabled=false   (CI unset)
 Test Files  4 passed (4)
      Tests  167 passed (167)
 PASS  Waiting for file changes...
c RERUN  src/format.test.ts x1 
 Test Files  1 passed (1)
      Tests  28 passed (28)
 PASS  Waiting for file changes...
c RERUN  src/index.ts 
 Test Files  4 passed (4)
      Tests  167 passed (167)
 PASS  Waiting for file changes...
```

Edits were a trailing newline, appended with `printf`. Afterwards I ran `git checkout -- src/format.test.ts src/index.ts` to clean up, which caused the next problem.

### 2026-11-23 17:37 UTC: my watch-mode cleanup (git checkout -- src/format.test.ts) also undid that file's import swap; re-applied and re-ran

```text
$ npx vitest run
 Test Files  4 passed (4)
      Tests  167 passed (167)
Statements   : 100% ( 58/58 )
Branches     : 100% ( 48/48 )
$ npx vitest run --isolate=false   (speed vs isolation, 3 runs)
  1.01 s (exit 0)
  0.98 s (exit 0)
  1.04 s (exit 0)
```

**The exit values in this entry are wrong.** `$?` was read after a `$(... | bc)` substitution, so it reports `bc`, not Vitest. See 14a.

### 2026-11-23 17:37 UTC: correction: the 'exit' values in the previous entry came from bc, not Vitest. Checking --isolate=false directly

```text
$ npx vitest run --isolate=false
 Test Files  4 passed (4)
      Tests  167 passed (167)
exit=0
```

## What broke

**Timing a broken suite (fixed).**
- **Expected:** Jest timings for the original suite.
- **Actual:** `exit 1` on every Jest run (08), with "Vitest cannot be imported in a CommonJS module using require()" (08a).
- **Cause:** I timed Jest in the folder where the imports were already swapped.
- **Fix:** re-timed on an untouched worktree of the original commit (08b).

**Probes found no tests, in both tools (fixed).** Each tool applied the project's own pattern (`src/**`). Fixed with `probes-vitest/vitest.config.ts` for Vitest, and `--testMatch '**/*.test.ts'` for Jest.

**`console.log` from a passing test didn't appear (worked around).** I put the result in the test name and used `--reporter=verbose`. I didn't investigate the reporter setting further.

**Cleanup reverted part of the port (fixed).** `git checkout -- src/format.test.ts` removed the watch-test newline *and* that file's import swap. `git diff --stat` showed one file missing. I re-applied the swap and the suite passed again (14).

**A wrong exit code in my own log (corrected).** See 14 and 14a.

**Side effect, not a failure:** `pnpm add` rewrote the tab-indented `packageManager` line in `package.json` with spaces. It's visible in `port.patch`.

## Screenshots

None. The terminal output above is the record.

| File | Shows | State produced by |
|---|---|---|
