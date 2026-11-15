# Run log: flaky-test-two-true-things

- **Writer:** Sora Villanueva
- **Started:** 2026-11-15
- **Environment:** Linux cloud container, Ubuntu 24.04.5 LTS, kernel 6.18.44, x86_64
- **Versions:** Node.js v22.23.4 with its built-in test runner (`node:test`). No npm packages.
- **Accounts or signups:** none

**The flakiness is deliberate.** `search.mjs` has a planted stale-reply bug and `search.test.mjs` a planted fixed 40 ms sleep. That's what the article is about. Everything under What broke was not planned.

**One edit to the output:** Node's reporter prints absolute file paths, and my working folder's path has been replaced with `<build-dir>`. Nothing else was changed. Each heading line was printed by the command itself with `date -u`.

## Log

### 2026-11-15 03:11 UTC: one run with node --test

```text
$ node --test search.test.mjs
TAP version 13
# Subtest: shows results for the latest query
not ok 1 - shows results for the latest query
  ---
  duration_ms: 43.135498
  type: 'test'
  location: '<build-dir>/search.test.mjs:8:1'
  failureType: 'testCodeFailure'
  error: |-
    Expected values to be strictly equal:
    + actual - expected
    
    + 'results for "pen"'
    - 'results for "pens"'
                       ^
    
  code: 'ERR_ASSERTION'
  name: 'AssertionError'
  expected: 'results for "pens"'
  actual: 'results for "pen"'
  operator: 'strictEqual'
  stack: |-
    TestContext.<anonymous> (file://<build-dir>/search.test.mjs:13:10)
    async Test.run (node:internal/test_runner/test:1054:7)
    async startSubtestAfterBootstrap (node:internal/test_runner/harness:296:3)
  ...
1..1
# tests 1
# suites 0
# pass 0
```

One run fails with the stale result. On its own, that tells you almost nothing.

### 2026-11-15 03:11 UTC: baseline, 200 runs

```text
$ node flake-meter.mjs search.test.mjs 200
search.test.mjs: 200 runs
    98  (passed)
    83  'results for "pen"'
    19  ''

real	0m28.404s
user	0m17.262s
sys	0m4.728s
```

102 failures in 200, with two messages: stale `"pen"` (83) and empty (19).

### 2026-11-15 03:12 UTC: fix 1 only (test waits for replies), 200 runs

```text
$ node flake-meter.mjs search.waits.test.mjs 200
search.waits.test.mjs: 200 runs
    95  'results for "pen"'
   105  (passed)
```

This was meant to be fix 1 (wait for the replies). The `sed` command only half-applied: the wait was fixed, but the old comment and the unused `sleep` helper stayed in the file. I noticed when I printed the file. See What broke. I discarded this run's file and rewrote it.

### 2026-11-15 03:12 UTC: fix 1 only, file rewritten cleanly, 200 runs

```text
$ node flake-meter.mjs search.waits.test.mjs 200
search.waits.test.mjs: 200 runs
   104  (passed)
    96  'results for "pen"'
```

Fix 1, clean: 96 failures, all stale `"pen"`, and no empty results. This fits the race: with two independent uniform delays, the old reply lands last about half the time.

### 2026-11-15 03:13 UTC: fix 2 only (app drops stale replies, test still sleeps 40 ms), 200 runs

```text
$ node flake-meter.mjs search.fixed-app.sleep.test.mjs 200
search.fixed-app.sleep.test.mjs: 200 runs
   132  (passed)
    68  ''
```

Fix 2 only (the app drops stale replies, the test still sleeps 40 ms): 68 failures, all empty. This fits the sleep: a 40 ms wait misses a reply drawn from 0 to 60 ms about a third of the time.

### 2026-11-15 03:13 UTC: both fixes, 200 runs

```text
$ node flake-meter.mjs search.fixed-app.waits.test.mjs 200
search.fixed-app.waits.test.mjs: 200 runs
   200  (passed)
```

Both fixes: 0 failures in 200. That's strong evidence both causes are gone, not proof the test can never fail.

## What broke

**A `sed` edit half-applied (fixed).**
- **Expected:** one command that swaps `await sleep(40)` for `await Promise.all(box.pending)`, updates the comment above the test, and deletes the unused `sleep` helper.
- **Actual:** only the first substitution took effect. The printed file in the 03a entry still shows `const sleep = ...` and the "DELIBERATELY FLAKY" comment.
- **Cause found by:** printing the file after measuring. I didn't dig into why the other two expressions didn't match. I stopped using `sed` for that edit instead.
- **Fix:** wrote `search.waits.test.mjs` by hand and measured again (03b). The published file is the hand-written one.

**Absolute paths in the output.** This isn't a failure. The reporter's paths exposed the name of my working folder, so I replaced it with `<build-dir>` as noted above.

Nothing else broke.

## Screenshots

None. The terminal output above is the record.

| File | Shows | State produced by |
|---|---|---|
