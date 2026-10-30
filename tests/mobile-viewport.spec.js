const {test,expect}=require('@playwright/test');
for(const width of [320,390]){
 test(`focused payment input and its action remain usable in a reduced ${width}px viewport`,async({page})=>{
  await page.setViewportSize({width,height:844});await page.goto('/app.html');await page.locator('#quickStart').waitFor();await page.locator('[data-quick-stage="exam_fee"]').click();
  await page.locator('.utility-tab[data-view="fees"]').click();
  await page.locator('#feeAmount').fill('472161');await page.locator('#feeAmount').focus();
  // Layout-viewport reduction is not an OS virtual-keyboard simulation.
  await page.setViewportSize({width,height:360});await page.locator('#feeAmount').scrollIntoViewIfNeeded();
  await expect(page.locator('#feeAmount')).toBeFocused();await expect(page.locator('#feeAmount')).toHaveValue('472161');
  const input=await page.locator('#feeAmount').boundingBox(),nav=await page.locator('.utility-nav').boundingBox();
  expect(input.y).toBeGreaterThanOrEqual(0);expect(input.y+input.height).toBeLessThanOrEqual(nav.y);
  await page.locator('#checkFeeBtn').click();await expect(page.locator('#feeResult')).toBeVisible();
  await page.locator('#fees .tool-return').click();await expect(page.locator('#nextAction')).toContainText('Pembayaran biaya EPS-TOPIK');
 });
 test(`open stage guide adapts to a reduced ${width}px viewport`,async({page})=>{
  await page.setViewportSize({width,height:844});await page.goto('/app.html');await page.locator('#quickStart').waitFor();await page.locator('[data-quick-stage="exam_fee"]').click();await page.locator('#nextAction [data-stage="exam_fee"]').click();
  await page.setViewportSize({width,height:360});
  for(const selector of ['#stageDialog .close','#stageDoneBtn']){
   const box=await page.locator(selector).boundingBox();expect(box.y).toBeGreaterThanOrEqual(0);expect(box.y+box.height).toBeLessThanOrEqual(360);
  }
  await page.locator('#stageDialog .close').click();await expect(page.locator('#stageDialog')).toBeHidden();await expect(page.locator('#nextAction [data-stage="exam_fee"]')).toBeFocused();
 });
}
test('Forward reopens the same guide after Back without marking a stage complete',async({page})=>{
 await page.goto('/app.html');await page.locator('#quickStart').waitFor();await page.locator('[data-quick-stage="exam_fee"]').click();
 const done=await page.evaluate(()=>localStorage.getItem('kep.doneStages'));
 await page.locator('#nextAction [data-stage="exam_fee"]').click();await expect(page.locator('#stageDialog')).toBeVisible();
 await page.goBack();await expect(page.locator('#stageDialog')).toBeHidden();await page.goForward();await expect(page.locator('#stageDialog')).toBeVisible();
 await expect(page.locator('#stageDialog')).toContainText('Pembayaran biaya EPS-TOPIK');expect(await page.evaluate(()=>localStorage.getItem('kep.doneStages'))).toBe(done);
});
