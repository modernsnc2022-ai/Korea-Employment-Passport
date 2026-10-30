const { test, expect } = require('@playwright/test');

for (const width of [320, 360, 375, 390, 430, 768, 1280]) {
  test(`action-first home at ${width}px preserves the primary journey`, async ({ page }) => {
    await page.setViewportSize({ width, height: 844 });
    await page.goto('/app.html');
    await page.locator('#quickStart').waitFor();
    await expect(page.locator('.service-identity')).toContainText('bukan pemerintah');
    await page.locator('[data-quick-stage="exam_fee"]').click();
    await expect(page.locator('#nextAction')).toContainText('bukan status resmi');
    const task = await page.locator('#nextAction').boundingBox();
    const optional = await page.locator('.trust-panel').boundingBox();
    expect(task.y).toBeLessThan(optional.y);
    const cta = page.locator('#nextAction .primary');
    await expect(cta).toBeVisible();
    if (width <= 430) {
      const box = await cta.boundingBox();
      const nav = await page.locator('.utility-nav').boundingBox();
      expect(box.y + box.height).toBeLessThanOrEqual(nav.y);
    }
    expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(width);
    await page.locator('.utility-tab[data-view="documents"]').click();
    await expect(page.locator('#documents')).toBeVisible();
    await page.reload();
    await expect(page.locator('#quickStart')).toBeHidden();
    await expect(page.locator('#nextAction')).toContainText('Pembayaran biaya EPS-TOPIK');
  });
}
