# AGENTS.md

Instructions for coding agents working in this repository. Humans should start with `readme.md`.

## What this is

`@sindresorhus/slugify`: one ES module (`index.js`) that turns a string into a URL-safe slug. Node.js 22 or later.

## Commands

- Install: `npm install`
- Test: `npm test`. This runs the `xo` linter first, then `node --test`. Both must pass. A lint error fails the run before any test runs.
- One test: `node --test --test-name-pattern="<test name>"`

There is no build step. Don't add Jest, Mocha or any other test runner: the tests use `node:test` and `node:assert/strict`.

## Adding or changing an option

An option lives in four places. Change all four in the same change:

1. `index.js`: the default value in the `options` object, and the behaviour.
2. `index.d.ts`: the property on `Options`, with a JSDoc comment that has a description, `@default`, and an `@example`.
3. `readme.md`: a `##### optionName` section under `## API` → `#### options`, with type, default and an example.
4. `test.js`: a `test(...)` block using `assert.equal`.

## Style

- Tabs for indentation, LF line endings, final newline (`.editorconfig`). `xo` enforces the rest; don't disable its rules inline.
- ES modules only (`import`/`export`), no CommonJS.

## Don't

- Don't commit a lockfile. `.npmrc` sets `package-lock=false`.
- Don't change `version` in `package.json`, `license`, or the CI workflow.
- Don't add a dependency unless the task needs one. Say why in the change description.
