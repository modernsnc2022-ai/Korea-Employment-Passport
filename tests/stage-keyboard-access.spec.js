const { test, expect } = require('@playwright/test');

test('stage cards open with Enter and Space without changing progress', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto('/app.html');
  await page.locator('#quickStart').waitFor();
  await page.locator('[data-quick-stage="exam_fee"]').click();
  const before = await page.evaluate(() => localStorage.getItem('kep.doneStages'));
  const cards = page.locator('.phase-stage-list .stage[role="button"]');
  await expect(cards).toHaveCount(27);
  await page.locator('#allJourneyDetails').evaluate(node => node.open = true);
  const first = cards.first();
  await first.evaluate(node => node.closest('details').open = true);
  await first.focus();
  await expect(first).toBeFocused();
  await expect(first).toHaveAttribute('aria-label', /Buka detail tahap/);
  await first.press('Enter');
  await expect(page.locator('#stageDialog')).toBeVisible();
  await page.locator('#stageDialog .close').click();
  await first.focus();
  await first.press('Space');
  await expect(page.locator('#stageDialog')).toBeVisible();
  await page.locator('#stageDialog .close').click();
  expect(await page.evaluate(() => localStorage.getItem('kep.doneStages'))).toBe(before);
});
