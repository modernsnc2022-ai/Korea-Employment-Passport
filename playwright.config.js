const { defineConfig } = require('@playwright/test');

const port = Number(process.env.PLAYWRIGHT_PORT || 4173);
if (!Number.isInteger(port) || port < 1024 || port > 65535) throw new Error('Invalid PLAYWRIGHT_PORT');

module.exports = defineConfig({
  testDir: './tests',
  timeout: 30000,
  retries: 0,
  workers: 1,
  use: {
    baseURL: `http://127.0.0.1:${port}`,
    browserName: 'chromium',
    channel: process.env.PLAYWRIGHT_CHANNEL || (process.platform === 'win32' ? 'msedge' : undefined),
    serviceWorkers: 'block',
    trace: 'retain-on-failure'
  },
  reporter: [['list']],
  webServer: {
    command: `python -m http.server ${port} --bind 127.0.0.1 --directory docs`,
    url: `http://127.0.0.1:${port}/app.html`,
    reuseExistingServer: false,
    timeout: 30000
  }
});
