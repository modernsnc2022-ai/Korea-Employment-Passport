const { defineConfig } = require('@playwright/test');

module.exports = defineConfig({
  testDir: './tests',
  testMatch: '**/nepal-offline.spec.js',
  timeout: 30000,
  retries: 0,
  workers: 1,
  use: {
    browserName: 'chromium',
    launchOptions: process.env.CHROMIUM_PATH ? {
      executablePath: process.env.CHROMIUM_PATH
    } : {},
    serviceWorkers: 'block'
  },
  reporter: [['list']]
  // No webServer, no localhost, no GitHub Actions needed.
});
