# Run log: playwright-vs-cypress

- **Writer:** Sora Villanueva
- **Started:** 2026-11-14 (first run); this log records a clean re-run on 2026-11-15
- **Environment:** Linux cloud container, Ubuntu 24.04.5 LTS, kernel 6.18.44, x86_64. A Chromium build (Chrome for Testing 153) was already installed at `/opt/pw-browsers/chromium` for Playwright 1.63, and `PLAYWRIGHT_BROWSERS_PATH=/opt/pw-browsers` was set.
- **Versions:** Node.js v22.23.4, npm 10.9.9, @playwright/test 1.65.1, cypress 16.3.0, http-server 14.1.1
- **Accounts or signups:** none

## Log

Entries in the order they happened. The output is pasted unedited.

The article's tests were first written and run on 2026-11-14 in a scratch project. That run hit the same Playwright browser-path failure shown below, and I fixed it the same way. I didn't keep its full output, so everything below comes from a clean re-run in a fresh folder on 2026-11-15. The only change from the article's files: the Chromium path in `playwright.config.ts` is an opt-in `PW_CHROMIUM_PATH` variable instead of being hard-coded.

### 2026-11-15 ~01:46 UTC (one scripted run): install the pinned versions

```text
$ npm install
npm warn deprecated whatwg-encoding@2.0.0: Use @exodus/bytes instead for a more spec-conformant and faster implementation

added 193 packages in 7s
```

Installed cleanly. The deprecation warning comes from a transitive dependency.

### 2026-11-15 ~01:46 UTC (one scripted run): run Playwright with its default browser

```text
$ npx playwright test --trace off --reporter=line
[WebServer] (node:257) [DEP0066] DeprecationWarning: OutgoingMessage.prototype._headers is deprecated
[WebServer] (Use `node --trace-deprecation ...` to show where the warning was created)


Running 1 test using 1 worker

[1/1] tests/login.spec.ts:3:1 › signs in with the right password
  1) tests/login.spec.ts:3:1 › signs in with the right password ────────────────────────────────────

    Error: browserType.launch: Executable doesn't exist at /opt/pw-browsers/chromium_headless_shell-1255/chrome-headless-shell-linux64/chrome-headless-shell
    ╔════════════════════════════════════════════════════════════╗
    ║ Looks like Playwright was just installed or updated.       ║
    ║ Please run the following command to download new browsers: ║
    ║                                                            ║
    ║     npx playwright install                                 ║
    ║                                                            ║
    ║ <3 Playwright Team                                         ║
    ╚════════════════════════════════════════════════════════════╝

    Error Context: test-results/login-signs-in-with-the-right-password/error-context.md


  1 failed
    tests/login.spec.ts:3:1 › signs in with the right password ─────────────────────────────────────
exit=1
```

I expected a pass. Instead it failed: Playwright 1.65.1 looks for its own Chromium headless-shell build (1255) under `PLAYWRIGHT_BROWSERS_PATH`, and only the 1.63 build (1243) is on this machine. Next, I pointed it at the existing Chromium.

### 2026-11-15 ~01:46 UTC (one scripted run): run Playwright against the existing Chromium

```text
$ PW_CHROMIUM_PATH=/opt/pw-browsers/chromium npx playwright test --trace off --reporter=line
[WebServer] (node:322) [DEP0066] DeprecationWarning: OutgoingMessage.prototype._headers is deprecated
[WebServer] (Use `node --trace-deprecation ...` to show where the warning was created)


Running 1 test using 1 worker

[1/1] tests/login.spec.ts:3:1 › signs in with the right password
  1 passed (2.5s)
exit=0
```

It passed. The fix is the `PW_CHROMIUM_PATH` variable read in `playwright.config.ts`.

### 2026-11-15 ~01:46 UTC (one scripted run): start the site for Cypress

```text
$ npx http-server site -p 4173 -s   (in the background; stopped after step 6)
```

Cypress does not start your server, unlike Playwright's `webServer`.

### 2026-11-15 ~01:46 UTC (one scripted run): run Cypress in its bundled Electron

```text
$ npx cypress run --browser electron

================================================================================

  (Run Starting)

  ┌────────────────────────────────────────────────────────────────────────────────────────────────┐
  │ Cypress:        16.3.0                                                                         │
  │ Browser:        Electron 150 (headless) (deprecated)                                           │
  │ Node Version:   v22.23.4 (/opt/node22/bin/node)                                                │
  │ Specs:          1 found (login.cy.js)                                                          │
  │ Searched:       cypress/e2e/**/*.cy.{js,jsx,ts,tsx}                                            │
  └────────────────────────────────────────────────────────────────────────────────────────────────┘

Warning: The Electron browser is deprecated as a test browser and will be removed in a future version of Cypress.

Switch to Chrome or another installed browser to avoid a breaking change when you upgrade.

Read more about supported browsers: https://on.cypress.io/launching-browsers


────────────────────────────────────────────────────────────────────────────────────────────────────
                                                                                                    
  Running:  login.cy.js                                                                     (1 of 1)


  login
    ✓ signs in with the right password (847ms)


  1 passing (886ms)


  (Results)

  ┌────────────────────────────────────────────────────────────────────────────────────────────────┐
  │ Tests:        1                                                                                │
  │ Passing:      1                                                                                │
  │ Failing:      0                                                                                │
  │ Pending:      0                                                                                │
  │ Skipped:      0                                                                                │
  │ Screenshots:  0                                                                                │
  │ Video:        false                                                                            │
  │ Duration:     0 seconds                                                                        │
  │ Spec Ran:     login.cy.js                                                                      │
  └────────────────────────────────────────────────────────────────────────────────────────────────┘


================================================================================

  (Run Finished)


       Spec                                              Tests  Passing  Failing  Pending  Skipped  
  ┌────────────────────────────────────────────────────────────────────────────────────────────────┐
  │ ✔  login.cy.js                              884ms        1        1        -        -        - │
  └────────────────────────────────────────────────────────────────────────────────────────────────┘
    ✔  All specs passed!                        884ms        1        1        -        -        -  

exit=0
```

It passed, but the summary labels the browser `Electron 150 (headless) (deprecated)`.

### 2026-11-15 ~01:46 UTC (one scripted run): run Cypress in the existing Chromium

```text
$ npx cypress run --browser /opt/pw-browsers/chromium

================================================================================

  (Run Starting)

  ┌────────────────────────────────────────────────────────────────────────────────────────────────┐
  │ Cypress:        16.3.0                                                                         │
  │ Browser:        Custom Chrome for Testing 153 (headless)                                       │
  │ Node Version:   v22.23.4 (/opt/node22/bin/node)                                                │
  │ Specs:          1 found (login.cy.js)                                                          │
  │ Searched:       cypress/e2e/**/*.cy.{js,jsx,ts,tsx}                                            │
  └────────────────────────────────────────────────────────────────────────────────────────────────┘


────────────────────────────────────────────────────────────────────────────────────────────────────
                                                                                                    
  Running:  login.cy.js                                                                     (1 of 1)


  login
    ✓ signs in with the right password (814ms)


  1 passing (848ms)


  (Results)

  ┌────────────────────────────────────────────────────────────────────────────────────────────────┐
  │ Tests:        1                                                                                │
  │ Passing:      1                                                                                │
  │ Failing:      0                                                                                │
  │ Pending:      0                                                                                │
  │ Skipped:      0                                                                                │
  │ Screenshots:  0                                                                                │
  │ Video:        false                                                                            │
  │ Duration:     0 seconds                                                                        │
  │ Spec Ran:     login.cy.js                                                                      │
  └────────────────────────────────────────────────────────────────────────────────────────────────┘


================================================================================

  (Run Finished)


       Spec                                              Tests  Passing  Failing  Pending  Skipped  
  ┌────────────────────────────────────────────────────────────────────────────────────────────────┐
  │ ✔  login.cy.js                              850ms        1        1        -        -        - │
  └────────────────────────────────────────────────────────────────────────────────────────────────┘
    ✔  All specs passed!                        850ms        1        1        -        -        -  

exit=0
```

It passed.

### 2026-11-15 ~01:46 UTC (one scripted run): clean up

```text
$ rm -rf test-results playwright-report cypress/screenshots cypress/videos node_modules
```

I stopped the background `http-server` with `kill`.

## What broke

**Playwright: browser executable missing.**
- **Expected:** the test runs in Chromium.
- **Actual:** `Error: browserType.launch: Executable doesn't exist at /opt/pw-browsers/chromium_headless_shell-1255/chrome-headless-shell-linux64/chrome-headless-shell` (full output in the Log above).
- **Cause:** the machine's preinstalled browsers were for Playwright 1.63 (build 1243). Playwright 1.65.1 expects build 1255. Listing `/opt/pw-browsers` showed only the 1243 builds.
- **Fix:** I set `PW_CHROMIUM_PATH=/opt/pw-browsers/chromium`, which `playwright.config.ts` passes to `launchOptions.executablePath`. On a normal machine, `npx playwright install chromium` is the standard fix. That command was not run here.

**Cypress: Electron is deprecated.** This didn't fail anything. The test passed, but the run summary flags Electron as deprecated, which matches the Cypress docs. The same test also passed in Chrome for Testing 153.

Nothing else broke.

## Screenshots

None. The terminal output above is the record.

| File | Shows | State produced by |
|---|---|---|
