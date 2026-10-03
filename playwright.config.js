const { defineConfig } = require('@playwright/test');

module.exports = defineConfig({
  testDir: './tests',
  timeout: 30000,
  retries: 0,
  workers: 1,
  use: {
    baseURL: 'http://127.0.0.1:4173',
    browserName: 'chromium',
    channel: process.env.PLAYWRIGHT_CHANNEL || (process.platform === 'win32' ? 'msedge' : undefined),
    serviceWorkers: 'block',
    trace: 'retain-on-failure'
  },
  reporter: [['list']],
  webServer: {
    command: 'python -m http.server 4173 --directory docs',
    url: 'http://127.0.0.1:4173/app.html',
    reuseExistingServer: true,
    timeout: 15000
  }
});
