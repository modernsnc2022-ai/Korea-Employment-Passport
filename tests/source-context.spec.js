const { test, expect } = require('@playwright/test');

async function choosePayment(page) {
  await page.goto('/app.html');
  await page.locator('#quickStart').waitFor();
  await page.locator('[data-quick-stage="exam_fee"]').click();
}

test('source context gives the original link and dated scope without claiming live verification', async ({ page, context }) => {
  await choosePayment(page);
  await expect(page.locator('#nextAction .next-evidence')).toBeVisible();
  const source = page.locator('#nextAction .task-source-shortcut');
  const url = await source.getAttribute('href');
  expect(url).toMatch(/^https:\/\/(www\.)?kp2mi\.go\.id\//);
  await page.locator('#nextAction .next-evidence>details>summary').click();
  await expect(page.locator('#nextAction .source-facts')).toContainText('bukan pemeriksaan langsung hari ini');
  await expect(page.locator('#nextAction .source-facts')).toContainText('Manufaktur');
  // Test the real outbound click safely without contacting an official service.
  await context.route(url, route => route.fulfill({ contentType: 'text/html', body: '<h1>Official-link navigation fixture</h1>' }));
  const popupPromise = page.waitForEvent('popup');
  await source.click();
  const popup = await popupPromise;
  await expect(popup).toHaveURL(url);
  await popup.close();
});

test('a malformed source observation cannot certify documents or payment', async ({ page }) => {
  await page.route('**/data/source_review_status.json', async route => {
    const response = await route.fetch();
    const status = await response.json();
    status.latestReadOnlyObservation = { schemaVersion: 999 };
    await route.fulfill({ response, json: status });
  });
  await choosePayment(page);
  await expect(page.locator('#nextAction .next-evidence>.source-state')).toHaveText('Informasi belum cukup');
  await page.locator('#nextAction .primary').click();
  await page.locator('#feeAmount').fill('472161');
  await page.locator('#feePayee').selectOption('bank');
  await page.locator('#checkFeeBtn').click();
  await expect(page.locator('#feeResult')).toContainText('Biaya belum dapat dikonfirmasi');
  await expect(page.locator('#feeResult')).not.toHaveClass(/safe/);
  await expect(page.locator('#knownCostList')).not.toContainText('Rp472.161');
});

test('a consistent source fixture is called recorded, never a current official confirmation', async ({ page }) => {
  await page.route('**/data/source_review_status.json', async route => {
    const response = await route.fetch();
    await route.fulfill({ response, json: {state:'clean',reviewRequiredUrls:[],fetchFailureUrls:[]} });
  });
  await choosePayment(page);
  await expect(page.locator('#nextAction .next-evidence>.source-state')).toHaveText('Rujukan tercatat');
  await page.locator('#nextAction .next-evidence>details>summary').click();
  await expect(page.locator('#nextAction .next-evidence')).toContainText('bukan konfirmasi bahwa ketentuan masih berlaku hari ini');
});

test('missing source-review feed remains explicit and fail-closed', async ({ page }) => {
  await page.route('**/data/source_review_status.json', route => route.fulfill({status:503,body:'Unavailable'}));
  await choosePayment(page);
  await expect(page.locator('#nextAction .next-evidence>.source-state')).toHaveText('Informasi belum cukup');
  await page.locator('#nextAction .next-evidence>details>summary').click();
  await expect(page.locator('#nextAction .official-help-fallback')).toContainText('bukan calo');
});
