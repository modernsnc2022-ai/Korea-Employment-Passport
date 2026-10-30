const {test,expect}=require('@playwright/test');
test('keyboard skip link enters the visible first-use setup',async({page})=>{
 await page.goto('/app.html');await page.locator('#quickStart').waitFor();
 await page.locator('.skip-link').focus();await page.keyboard.press('Enter');await expect(page.locator('#quickStart')).toBeFocused();
});
test('keyboard skip link enters the current task and the selected tool',async({page})=>{
 await page.goto('/app.html');await page.locator('#quickStart').waitFor();await page.locator('[data-quick-stage="exam_fee"]').click();
 await page.locator('.skip-link').focus();await page.keyboard.press('Enter');await expect(page.locator('#nextAction')).toBeFocused();
 for(const view of ['documents','fees','gaps']){
  await page.locator(`.utility-tab[data-view="${view}"]`).click();await expect(page.locator('.skip-link')).toHaveAttribute('href','#'+view);
  await page.locator('.skip-link').focus();await page.keyboard.press('Enter');await expect(page.locator('#'+view)).toBeFocused();
 }
});
test('failed initial route load exposes a working skip link to recovery',async({page})=>{
 await page.route('**/data/id_e9_manufacturing_2026.json',r=>r.abort());await page.goto('/app.html');await page.locator('#routeLoadRecovery').waitFor();
 await page.locator('.skip-link').focus();await page.keyboard.press('Enter');await expect(page.locator('#routeLoadRecovery')).toBeFocused();
});
