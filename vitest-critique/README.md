# Vitest, critiqued: what fast costs you

Build for [Vitest, critiqued: what fast costs you](https://seekanddeploy.io/news/vitest-critique) by Sora Villanueva.

## What this is

A port of [vercel/ms](https://github.com/vercel/ms)'s Jest suite (167 tests) to Vitest 5.1.1, timed against Jest 30. It also has small probe tests I wrote for what vercel/ms doesn't exercise: module isolation, mocking differences, the Edge runtime, and watch mode.

- `port.patch`: the whole port, against commit `4ff48ce`. It covers `package.json`, the four import swaps, and the new `vitest.config.ts`. The `pnpm-lock.yaml` diff is left out because it's 785 lines of resolver output. Run `pnpm install` to regenerate it.
- `probes-jest/`: the Jest-style originals. They pass under Jest 30.
- `probes-vitest/`: the Vitest versions. The mock probes are the *fixed* versions. The literal port is the same files with `jest.` changed to `vi.`, and its failures are in the run log.

## Requirements

- Logged on Linux x86_64 (Ubuntu 24.04.5), Node.js v22.23.4, pnpm 10.33.0
- Versions pinned by the patch: vitest 5.1.1, @vitest/coverage-v8 5.1.1, @edge-runtime/vm 5.0.0

## Run it

```bash
git clone https://github.com/vercel/ms && cd ms && git checkout 4ff48ce
git apply ../vitest-critique/port.patch && pnpm install
npx vitest run                                   # 167 tests, 100% coverage
npx vitest run --environment edge-runtime --coverage.enabled=false
cp -r ../vitest-critique/probes-vitest probe     # the probe config expects probe/
npx vitest run --config probe/vitest.config.ts --reporter=verbose
```

To see the Jest side, run the `probes-jest` files from a clean checkout with
`npx jest --rootDir <dir> --testMatch '**/*.test.ts' --preset ts-jest --no-coverage`.

## What broke

All of these were my own setup mistakes, and all are logged with their fixes:

- **I timed Jest on already-ported files.** Every run failed. I re-timed it on a clean worktree.
- **Probes outside `src/` found no tests** in either tool, because of the project's test pattern.
- **My cleanup after the watch test** reverted one file's import swap. I re-applied it.
- **One logged exit code came from `bc`, not Vitest.** Corrected in the log.

Full detail in [RUN-LOG.md](RUN-LOG.md).
