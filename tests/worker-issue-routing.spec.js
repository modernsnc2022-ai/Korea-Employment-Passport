const {test,expect}=require('@playwright/test');
test('worker issue choices open existing tools without claiming official decisions',async({page})=>{
 await page.setViewportSize({width:390,height:844});await page.goto('/app.html');
 await page.locator('#quickStart').waitFor();await page.locator('[data-quick-stage="exam_fee"]').click();
 await page.locator('.utility-tab[data-view="gaps"]').click();
 await expect(page.locator('.worker-help-chooser')).toBeVisible();
 for(const target of ['payroll','contract','workplace']){
  await page.locator('[data-worker-tool="'+target+'"]').click();
  await expect(page.locator('#'+target)).toBeVisible();
  await page.locator('.utility-tab[data-view="gaps"]').click();
 }
 expect(await page.evaluate(()=>document.documentElement.scrollWidth)).toBeLessThanOrEqual(390);
});
