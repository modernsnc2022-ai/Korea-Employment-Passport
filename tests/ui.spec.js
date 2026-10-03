const { test, expect } = require('@playwright/test');

async function freshPage(page) {
  await page.addInitScript(() => localStorage.clear());
  const errors = [];
  page.on('pageerror', error => errors.push(error.message));
  await page.goto('/app.html', { waitUntil: 'networkidle' });
  return errors;
}

test('first-time flow stays simple on desktop', async ({ page }) => {
  await page.setViewportSize({ width: 1280, height: 800 });
  const errors = await freshPage(page);

  await expect(page.locator('#quickStart')).toBeVisible();
  await expect(page.locator('body')).toHaveClass(/setup-mode/);
  await expect(page.locator('.flow-dashboard')).toBeHidden();

  await page.locator('[data-quick-stage="eligibility"]').click();

  await expect(page.locator('#quickStart')).toBeHidden();
  await expect(page.locator('body')).not.toHaveClass(/setup-mode/);
  await expect(page.locator('.flow-dashboard')).toBeVisible();
  await expect(page.locator('#nextAction')).toBeVisible();
  await expect(page.locator('.micro-help')).toBeVisible();
  await expect(page.locator('.utility-nav')).toBeVisible();

  expect(errors).toEqual([]);
});

test('mobile flow has no horizontal overflow and keeps primary controls visible', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  const errors = await freshPage(page);

  await expect(page.locator('#quickStart')).toBeVisible();
  await page.locator('[data-quick-stage="eligibility"]').click();
  await expect(page.locator('#nextAction')).toBeVisible();
  await expect(page.locator('.utility-nav')).toBeVisible();

  const overflow = await page.evaluate(() => ({
    scrollWidth: document.documentElement.scrollWidth,
    innerWidth: window.innerWidth
  }));
  expect(overflow.scrollWidth).toBeLessThanOrEqual(overflow.innerWidth + 1);

  await page.locator('.utility-tab[data-view="documents"]').click();
  await expect(page.locator('#documents')).toBeVisible();
  await expect(page.locator('#docStageContext')).toBeVisible();

  expect(errors).toEqual([]);
});

test('optional trust and backup controls stay out of the main flow', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  const errors = await freshPage(page);
  await page.locator('[data-quick-stage="eligibility"]').click();

  const trust = page.locator('.trust-panel');
  await expect(trust).toBeVisible();
  await expect(page.locator('#backupProgressBtn')).toBeHidden();

  await trust.locator('summary').click();
  await expect(page.locator('#backupProgressBtn')).toBeVisible();
  await expect(page.locator('#restoreProgressBtn')).toBeVisible();

  expect(errors).toEqual([]);
});
