const { defineConfig } = require('@playwright/test');

// An explicit test port isolates KEP's HTTP server from concurrent local
// projects. Default 4173 remains compatible with the Colab CI script.
const port = Number(process.env.KEP_TEST_PORT || 4173);
if (!Number.isInteger(port) || port < 1024 || port > 65535) {
  throw new Error('KEP_TEST_PORT must be a non-privileged TCP port');
}
const testUrl = 'http://127.0.0.1:' + port;

module.exports = defineConfig({
  testDir: './tests',
  timeout: 30000,
  retries: 0,
  workers: 1,
  use: {
    baseURL: testUrl,
    browserName: 'chromium',
    channel: process.env.PLAYWRIGHT_CHANNEL || (process.platform === 'win32' ? 'msedge' : undefined),
    serviceWorkers: 'block',
    trace: 'retain-on-failure'
  },
  reporter: [['list']],
  webServer: {
    command: 'python -m http.server ' + port + ' --directory docs',
    url: testUrl + '/app.html',
    reuseExistingServer: !process.env.KEP_TEST_PORT,
    timeout: 30000
  }
});
