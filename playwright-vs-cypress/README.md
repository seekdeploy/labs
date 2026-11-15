# Playwright vs Cypress: the same login test, two different ideas

Build for [Playwright vs Cypress: the same login test, two different ideas](https://seekanddeploy.io/news/playwright-vs-cypress) by Sora Villanueva.

## What this is

A one-page login form (`site/index.html`) and the same login test written in
both tools: `tests/login.spec.ts` with `playwright.config.ts`, and
`cypress/e2e/login.cy.js` with `cypress.config.js`. The page waits 300 ms
before showing the result, so you can see that both tools wait for it without
any `sleep` in the test.

## Requirements

- Logged on Linux x86_64 (Ubuntu 24.04.5), Node.js v22.23.4, npm 10.9.9
- @playwright/test 1.65.1, cypress 16.3.0, http-server 14.1.1 (pinned in `package.json`)
- About 1 GB of disk for browser downloads (the Cypress 16.3.0 binary alone took 811 MB on Linux)

## Run it

```bash
npm install
npx playwright install --with-deps chromium   # standard setup; not run in the log
npm run test:pw                               # Playwright starts the site itself

npm run serve                                 # terminal 1: Cypress needs the site running
npm run test:cy                               # terminal 2
```

To use a Chromium you already have, which is what the logged run did:

```bash
PW_CHROMIUM_PATH=/path/to/chromium npm run test:pw
```

## What broke

- **Playwright couldn't find its browser.** The machine's preinstalled Chromium belonged to Playwright 1.63, and 1.65.1 looks for its own build, so the first run failed with `Executable doesn't exist`. Fixed by pointing it at the existing browser with `PW_CHROMIUM_PATH`.
- **Cypress's default browser is deprecated.** The test passed in the bundled Electron, but the run summary labels it `(deprecated)`. It also passed in Chromium.

Full detail in [RUN-LOG.md](RUN-LOG.md).
