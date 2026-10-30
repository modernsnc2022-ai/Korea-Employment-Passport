// Cloud-only visual QA; never contacts an intake service or changes official data.
const { chromium } = require('@playwright/test');
const { spawn } = require('node:child_process');
const fs = require('node:fs');
const path = require('node:path');
const root = path.resolve(__dirname, '..');
const output = path.join(root, 'docs/qa/screenshots');
const port = 4179;
const base = `http://127.0.0.1:${port}`;

(async () => {
  fs.mkdirSync(output, { recursive: true });
  const server = spawn('python', ['-m', 'http.server', String(port), '--bind', '127.0.0.1', '--directory', 'docs'], { cwd: root, stdio: 'ignore' });
  const browser = await chromium.launch();
  const results = [];
  try {
    let ready = false;
    for (let i = 0; i < 30; i++) {
      try { if ((await fetch(`${base}/app.html`)).ok) { ready = true; break; } } catch {}
      await new Promise(resolve => setTimeout(resolve, 100));
    }
    if (!ready) throw new Error('Visual QA server not ready');
    for (const width of [320, 360, 375, 390, 430, 768, 1280]) {
      const context = await browser.newContext({ viewport: { width, height: 844 }, reducedMotion: 'reduce', serviceWorkers: 'block' });
      // No external navigations are required to inspect the application.
      await context.route('https://**', route => route.abort());
      const page = await context.newPage();
      const errors = [];
      page.on('pageerror', error => errors.push(error.message));
      async function capture(name) {
        await page.screenshot({ path: path.join(output, `${name}-${width}.jpg`), type: 'jpeg', quality: 85 });
        const metrics = await page.evaluate(() => ({
          viewport: innerWidth,
          pageWidth: document.documentElement.scrollWidth,
          currentView: document.querySelector('.view.active')?.id,
          dialog: document.querySelector('#stageDialog').open
        }));
        results.push({ name, width, ...metrics });
      }
      await page.goto(`${base}/app.html`);
      await page.locator('#quickStart').waitFor();
      await capture('entry');
      const start = Date.now();
      await page.locator('[data-quick-stage="exam_fee"]').click();
      await page.reload();
      await page.locator('#nextAction').waitFor();
      await capture('home');
      await page.locator('#nextAction [data-stage="exam_fee"]').click();
      await capture('stage-top');
      await page.locator('.stage-dialog-body').evaluate(el => el.scrollTop = el.scrollHeight);
      await capture('stage-bottom');
      await page.locator('#stageDialog .close').click();
      await page.waitForFunction(() => !history.state?.kepStageDialog);
      results.push({ name: 'guided-task', width, elapsedMs: Date.now() - start, actions: 3, errors });
      if ([320,390,1280].includes(width)) {
        await page.evaluate(() => switchView('documents', false));
        await page.locator('#docList .doc-file').first().scrollIntoViewIfNeeded();
        await capture('document-controls');
      }
      if ([390,1280].includes(width)) {
        for (const view of ['eligibility', 'documents', 'fees', 'gaps', 'contract', 'workplace', 'payroll', 'companyHub']) {
          await page.evaluate(view => switchView(view, false), view);
          await page.evaluate(view => document.getElementById(view).scrollIntoView({block:'start',behavior:'instant'}), view);
          await capture(view);
        }
        await page.evaluate(() => { document.documentElement.style.fontSize = '200%'; switchView('documents', false); });
        await page.evaluate(() => document.getElementById('documents').scrollIntoView({block:'start',behavior:'instant'}));
        await capture('documents-text-200');
      }
      await context.close();
    }
    fs.writeFileSync(path.join(root, 'docs/qa/visual-matrix-2026-10-30.json'), JSON.stringify({
      environment: 'Cloud Chromium; viewport emulation, not a physical device',
      sourceData: 'Unmodified checked-in source-review data; no clean-source fixture',
      results
    }, null, 2) + '\n');
    console.log(`VISUAL_CAPTURE_PASS screenshots=${results.filter(row => row.name !== 'guided-task').length} pageErrors=${results.filter(row=>row.errors?.length).length} overflow=${results.filter(row=>row.pageWidth>row.viewport).length}`);
  } finally {
    await browser.close(); server.kill();
  }
})().catch(error => { console.error(error); process.exitCode = 1; });
