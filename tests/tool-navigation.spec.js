const {test,expect}=require('@playwright/test');

test('tools expose their own heading and a keyboard route back to the selected task',async({page})=>{
 await page.goto('/app.html');await page.locator('#quickStart').waitFor();
 await page.locator('[data-quick-stage="exam_fee"]').click();
 for(const view of ['documents','fees','gaps']){
  await page.locator(`.utility-tab[data-view="${view}"]`).click();
  await expect(page.locator(`#${view} h2`).first()).toBeFocused();
  await expect(page.locator('.flow-dashboard')).toBeHidden();
  await expect(page.locator('.trust-panel')).toBeHidden();
  await expect(page.locator(`.utility-tab[data-view="${view}"]`)).toHaveAttribute('aria-current','page');
  await page.locator(`#${view} .tool-return`).click();
  await expect(page.locator('#nextAction')).toBeVisible();
  await expect(page.locator('#nextAction')).toContainText('Pembayaran biaya EPS-TOPIK');
  await expect(page.locator('#nextAction .primary')).toBeFocused();
 }
});

for(const width of [320,390,430]){
 test(`notice selection is above source details and reachable on the first dialog screen at ${width}px`,async({page})=>{
  await page.setViewportSize({width,height:844});
  await page.goto('/app.html');await page.locator('#quickStart').waitFor();
  await page.evaluate(()=>applyCurrentStage('predeparture_training',true));
  await page.locator('#nextAction [data-stage="predeparture_training"]').click();
  const picker=page.locator('#scopePicker');
  const pickerBox=await picker.boundingBox();const footer=await page.locator('.stage-dialog-footer').boundingBox();
  expect(pickerBox.y+pickerBox.height).toBeLessThan(footer.y);
  expect(pickerBox.y).toBeGreaterThan(0);
  const evidence=await page.locator('#stageEvidence').boundingBox();
  expect(pickerBox.y).toBeLessThan(evidence.y);
  await picker.selectOption('opp_sawangan_wave10_2026');
  await expect(picker).toHaveValue('opp_sawangan_wave10_2026');
 });
}
