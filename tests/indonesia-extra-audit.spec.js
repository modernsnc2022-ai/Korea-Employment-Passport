const { test, expect } = require('@playwright/test');

// Additional launch-readiness audit, separate from the normal Indonesian UI smoke tests.
// No real user data, enrollment, external endpoints or publication actions are used.
test('Indonesian route maps all 27 ordered stages to nonempty Bahasa Indonesia copy', async ({ request }) => {
  const route = await (await request.get('/data/id_e9_manufacturing_2026.json')).json();
  const copy = await (await request.get('/data/id_e9_manufacturing_2026_id.json')).json();
  expect(route.stages).toHaveLength(27);
  expect(Object.keys(copy).sort()).toEqual(route.stages.map(s => s.id).sort());
  const seen = new Set();
  for (const stage of route.stages) {
    expect(seen.has(stage.id)).toBe(false);
    seen.add(stage.id);
    expect(copy[stage.id].title.trim().length).toBeGreaterThan(3);
    expect(copy[stage.id].action.trim().length).toBeGreaterThan(12);
    expect(copy[stage.id].title + copy[stage.id].action).not.toMatch(/\b(undefined|null|TODO|TBD|lorem ipsum)\b/i);
    if (stage.warning) expect(copy[stage.id].warning?.trim().length || 0).toBeGreaterThan(8);
  }
  expect(route.stages.find(s => s.id === 'job_application').brokerReplacement).toBe('held_official_notice');
  expect(copy.job_application.warning).toContain('Jangan submit');
});

for (const width of [320, 360, 390, 1280]) {
  test('Indonesian applicant first-use and 27-stage navigation at ' + width + 'px', async ({ page }) => {
    await page.setViewportSize({ width, height: 760 });
    const jsErrors = [];
    page.on('pageerror', e => jsErrors.push(e.message));
    await page.goto('/app.html', { waitUntil: 'domcontentloaded' });
    await expect(page.locator('#progressText')).toContainText('/ 27');
    await expect(page.locator('#quickStart')).toBeVisible();
    await page.locator('[data-quick-stage="eligibility"]').click();
    await expect(page.locator('#nextAction')).toBeVisible();
    await expect(page.locator('.utility-nav')).toBeVisible();
    await expect(page.locator('.micro-help')).toBeVisible();
    const frame = await page.evaluate(() => {
      const active = [...document.querySelectorAll('button:not([hidden])')]
        .filter(x => x.getClientRects().length && getComputedStyle(x).visibility !== 'hidden');
      const outliers = active.filter(x => {
        // Closed details are not operable, and horizontal carousels are
        // intentionally swipeable on small screens.
        if (x.closest('details:not([open])')) return false;
        let ancestor = x.parentElement;
        while (ancestor && ancestor !== document.body) {
          const style = getComputedStyle(ancestor);
          const r = ancestor.getBoundingClientRect();
          if (/auto|scroll/.test(style.overflowX) &&
              ancestor.scrollWidth > ancestor.clientWidth + 1 &&
              r.left >= -2 && r.right <= innerWidth + 2) return false;
          ancestor = ancestor.parentElement;
        }
        const r = x.getBoundingClientRect();
        return r.left < -2 || r.right > innerWidth + 2;
      }).map(x => {
        const r = x.getBoundingClientRect();
        return { text:x.textContent.trim().slice(0,32), left:r.left, right:r.right };
      });
      return { scrollWidth:document.documentElement.scrollWidth, innerWidth, outliers:outliers.slice(0,12) };
    });
    expect(frame.scrollWidth).toBeLessThanOrEqual(frame.innerWidth + 1);
    expect(frame.outliers).toEqual([]);
    expect(jsErrors).toEqual([]);
  });
}

for (const width of [320, 390]) {
  test('Beta intake at ' + width + 'px distinguishes applications from access and advertises six months', async ({ page }) => {
    await page.setViewportSize({ width, height: 760 });
    await page.goto('/beta.html?src=website', { waitUntil: 'domcontentloaded' });
    await expect(page.locator('#betaStatusPill')).toContainText('PENDAFTARAN OPEN');
    await expect(page.locator('#betaStatusPill')).toContainText('AKSES MENUNGGU');
    await expect(page.locator('#applicationPanel')).toBeVisible();
    await expect(page.locator('#closedPanel')).toBeVisible();
    await expect(page.locator('#directIntakeFields')).toBeHidden();
    await expect(page.locator('#betaApplicationSubmitBtn')).toHaveText('Kirim lewat aplikasi email');
    await expect(page.locator('body')).toContainText('6 bulan gratis');
    await expect(page.locator('body')).toContainText('tidak dimasukkan ke repositori publik');
    const horizontal = await page.evaluate(() => ({scrollWidth:document.documentElement.scrollWidth, width:innerWidth}));
    expect(horizontal.scrollWidth).toBeLessThanOrEqual(horizontal.width + 1);
  });
}

test('Official-target links open with noopener on Indonesian pages', async ({ page }) => {
  for (const url of ['/app.html','/beta.html','/privacy.html']) {
    await page.goto(url, { waitUntil:'domcontentloaded' });
    if(url.includes('app.html')) await expect(page.locator('#progressText')).toContainText('/ 27');
    const problems = await page.evaluate(() =>
      [...document.querySelectorAll('a[target="_blank"]')]
       .filter(x => !x.rel.split(/\s+/).includes('noopener'))
       .map(x => ({text:x.textContent.trim().slice(0,55), href:x.getAttribute('href')}))
    );
    expect(problems, url + ' has unsafe new-window links').toEqual([]);
  }
});

test('Indonesian document comparison never persists typed identity strings', async ({ page }) => {
  await page.goto('/app.html', {waitUntil:'domcontentloaded'});
  await expect(page.locator('#quickStart')).toBeVisible();
  await page.locator('[data-quick-stage="eligibility"]').click();
  await page.locator('.utility-tab[data-view="documents"]').click();
  await expect(page.locator('#documents')).toBeVisible();
  await page.getByText('Cek apakah data sama di semua dokumen (opsional)', { exact: true }).click();
  await page.locator('#consNamePassport').fill('PRIVATE_TEST_PASSPORT_NAME_7171');
  await page.locator('#consNameSlc').fill('PRIVATE_TEST_SLC_NAME_8282');
  await page.locator('#checkConsistencyBtn').click();
  await expect(page.locator('#consistencyResult')).toBeVisible();
  const stored = await page.evaluate(() => JSON.stringify(localStorage));
  expect(stored).not.toContain('PRIVATE_TEST_PASSPORT_NAME_7171');
  expect(stored).not.toContain('PRIVATE_TEST_SLC_NAME_8282');
});


test('Indonesia app, landing and privacy disclose in Indonesian without stale English placeholders', async ({ page }) => {
  await page.goto('/app.html', { waitUntil: 'domcontentloaded' });
  await expect(page.locator('.summary .eyebrow')).toHaveText('JALUR TANPA CALO');
  await expect(page.locator('#routeMeta')).not.toContainText('Loading verified route');
  await page.locator('[data-quick-stage="eligibility"]').click();
  await page.locator('.utility-tab[data-view="documents"]').click();
  await expect(page.locator('#documents h2').first()).toHaveText('Asisten Dokumen');
  await expect(page.locator('.field-copilot .eyebrow')).toHaveText('BANTUAN ISI KOLOM');
  await page.goto('/index.html');
  await expect(page.locator('body')).toContainText('Asisten Dokumen');
  await expect(page.locator('footer a[href="privacy.html"]')).toHaveText('Privasi');
  await page.goto('/privacy.html');
  await expect(page.locator('h2').first()).toHaveText('Pemberitahuan privasi beta');
  await expect(page).toHaveTitle(/Privasi/);
});
