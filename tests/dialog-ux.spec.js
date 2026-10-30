const { test, expect } = require('@playwright/test');

async function openPayment(page) {
  await page.goto('/app.html');
  await page.locator('#quickStart').waitFor();
  await page.locator('[data-quick-stage="exam_fee"]').click();
  await page.locator('#nextAction [data-stage="exam_fee"]').click();
  await expect(page.locator('#stageDialog')).toBeVisible();
}

for (const width of [320, 360, 375, 390, 430, 768, 1280]) {
  test(`modal header and action stay visible while reading at ${width}px`, async ({ page }) => {
    await page.setViewportSize({width, height:844});
    await openPayment(page);
    const close=page.locator('#stageDialog .close');
    const before=await close.boundingBox();
    await page.locator('.stage-dialog-body').evaluate(el => el.scrollTop=el.scrollHeight);
    const after=await close.boundingBox();
    expect(after.y).toBe(before.y);
    expect(after.x).toBeGreaterThanOrEqual(0);
    expect(after.x+after.width).toBeLessThanOrEqual(width);
    const done=await page.locator('#stageDoneBtn').boundingBox();
    expect(done.y+done.height).toBeLessThanOrEqual(844);
    expect(done.y).toBeGreaterThan(after.y+after.height);
    await close.click();
    await expect(page.locator('#stageDialog')).toBeHidden();
    await expect(page.locator('#nextAction [data-stage="exam_fee"]')).toBeFocused();
    await expect.poll(() => page.evaluate(() => Boolean(history.state?.kepStageDialog))).toBe(false);
  });
}

test('browser Back closes the guide and leaves the current stage intact', async ({ page }) => {
  await openPayment(page);
  const before=await page.evaluate(() => localStorage.getItem('kep.doneStages'));
  await page.goBack();
  await expect(page.locator('#stageDialog')).toBeHidden();
  await expect(page.locator('#nextAction')).toContainText('Pembayaran biaya EPS-TOPIK');
  expect(await page.evaluate(() => localStorage.getItem('kep.doneStages'))).toBe(before);
});

test('Escape and keyboard focus stay within native dialog behavior', async ({ page }) => {
  await openPayment(page);
  for(let i=0;i<15;i++){
    await page.keyboard.press('Tab');
    // Chromium may move to browser chrome at the cycle boundary (activeElement=body).
    // A further Tab must return to the modal, never a background app control.
    if(await page.evaluate(() => document.activeElement===document.body)) await page.keyboard.press('Tab');
    expect(await page.evaluate(() => document.querySelector('#stageDialog').contains(document.activeElement))).toBe(true);
  }
  await page.keyboard.press('Escape');
  await expect(page.locator('#stageDialog')).toBeHidden();
  await expect(page.locator('#nextAction [data-stage="exam_fee"]')).toBeFocused();
});

test('short viewport and 200% text keep a working close button and contained content', async ({ page }) => {
  await page.setViewportSize({width:320,height:420});
  await openPayment(page);
  await page.evaluate(() => document.documentElement.style.fontSize='200%');
  const close=await page.locator('#stageDialog .close').boundingBox();
  expect(close.y).toBeGreaterThanOrEqual(0);
  expect(close.y+close.height).toBeLessThanOrEqual(420);
  expect(await page.locator('#stageDialog').evaluate(el => el.scrollWidth<=el.clientWidth)).toBe(true);
  await page.locator('#stageDialog .close').click();
  await expect(page.locator('#stageDialog')).toBeHidden();
});
