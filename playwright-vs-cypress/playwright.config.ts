import { defineConfig } from '@playwright/test';

// Optional: set PW_CHROMIUM_PATH to use a Chromium you already have
// instead of the one `npx playwright install chromium` downloads.
const executablePath = process.env.PW_CHROMIUM_PATH;

export default defineConfig({
  testDir: 'tests',
  use: {
    baseURL: 'http://localhost:4173',
    ...(executablePath ? { launchOptions: { executablePath } } : {}),
  },
  webServer: { command: 'npx http-server site -p 4173 -s', url: 'http://localhost:4173' },
});
