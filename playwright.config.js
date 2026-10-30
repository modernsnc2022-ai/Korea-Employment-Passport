const { defineConfig } = require('@playwright/test');

const engine = process.env.KEP_BROWSER || 'chromium';
if (!['chromium','webkit','firefox'].includes(engine)) throw new Error('Invalid KEP_BROWSER');

const port = Number(process.env.PLAYWRIGHT_PORT || 4173);
if (!Number.isInteger(port) || port < 1024 || port > 65535) throw new Error('Invalid PLAYWRIGHT_PORT');

module.exports = defineConfig({
  testDir: './tests',
  // Worker inspection/injection in this case uses Chromium-only Playwright APIs.
  testIgnore: engine === 'chromium' ? [] : ['**/offline-cache.spec.js'],
  timeout: 30000,
  retries: 0,
  workers: 1,
  use: {
    baseURL: `http://127.0.0.1:${port}`,
    browserName: engine,
    isMobile: engine === 'webkit',
    hasTouch: engine === 'webkit',
    channel: engine === 'chromium' ? (process.env.PLAYWRIGHT_CHANNEL || (process.platform === 'win32' ? 'msedge' : undefined)) : undefined,
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
