const { test, expect } = require('@playwright/test');

test('320px document controls remain usable and validate a local file without upload', async ({ page }) => {
  await page.setViewportSize({width:320,height:844});
  await page.goto('/app.html');
  await page.locator('#quickStart').waitFor();
  await page.locator('[data-quick-stage="eligibility"]').click();
  await page.locator('.utility-tab[data-view="documents"]').click();
  const file=page.locator('#docList .doc-file').first();
  await expect(file).toBeVisible();
  const box=await file.boundingBox();
  expect(box.width).toBeGreaterThan(200);
  expect(box.height).toBeGreaterThanOrEqual(44);
  await file.setInputFiles({name:'invalid.jpg',mimeType:'image/jpeg',buffer:Buffer.from('not a JPEG')});
  await expect(page.locator('#docList .file-status').first()).toContainText('isi file bukan JPEG asli');
  const target=page.locator('#docList .doc-check-target').first();
  const targetBox=await target.boundingBox();
  expect(targetBox.width).toBeGreaterThanOrEqual(44);
  expect(targetBox.height).toBeGreaterThanOrEqual(44);
  await target.click();
  await expect(page.locator('#docList .doc-check').first()).toBeChecked();
  await page.reload();
  await page.locator('.utility-tab[data-view="documents"]').click();
  await expect(page.locator('#docList .doc-check').first()).toBeChecked();
  expect(await page.locator('#docList .doc-file').first().inputValue()).toBe('');
});
