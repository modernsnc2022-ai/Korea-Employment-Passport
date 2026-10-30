const { test, expect } = require('@playwright/test');

test('stage chooser starts with three clear options and discloses remaining four', async ({ page }) => {
  await page.goto('/app.html', { waitUntil: 'domcontentloaded' });
  await expect(page.locator('#quickStart')).toBeVisible({ timeout: 15000 });
  const firstChoices = page.locator('#quickStart > .quick-choice-grid .quick-choice');
  await expect(firstChoices).toHaveCount(3);
  const advanced = page.locator('#quickStart .advanced-stage-choices');
  await expect(advanced).toBeVisible();
  await expect(advanced.locator('.quick-choice')).toHaveCount(4);
  await expect(advanced.locator('.quick-choice').first()).toBeHidden();
  await advanced.locator('summary').click();
  await expect(advanced.locator('.quick-choice').first()).toBeVisible();
});

test('mobile guided entry does not overflow width', async ({ page }) => {
  await page.setViewportSize({ width: 375, height: 812 });
  await page.goto('/app.html', { waitUntil: 'domcontentloaded' });
  await expect(page.locator('#quickStart')).toBeVisible({ timeout: 15000 });
  const width = await page.evaluate(() => ({ page: document.documentElement.scrollWidth, viewport: innerWidth }));
  expect(width.page).toBeLessThanOrEqual(width.viewport + 1);
});
