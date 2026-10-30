const {test,expect}=require('@playwright/test');
test('available installation control remains visible and named on the light header',async({page})=>{
 await page.goto('/app.html');await page.locator('#quickStart').waitFor();
 await page.evaluate(()=>{
  const event=new Event('beforeinstallprompt',{cancelable:true});
  event.prompt=async()=>{window.testInstallPrompted=true};event.userChoice=Promise.resolve({outcome:'dismissed'});
  window.dispatchEvent(event);
 });
 await expect(page.locator('#installBtn')).toBeVisible();
 await expect(page.locator('#installBtn')).toHaveAccessibleName('Pasang');
 await page.addScriptTag({path:require.resolve('axe-core/axe.min.js')});
 const violations=await page.evaluate(async()=>(await axe.run('.topbar')).violations.map(v=>v.id));
 expect(violations).toEqual([]);
 await page.locator('#installBtn').click();
 expect(await page.evaluate(()=>window.testInstallPrompted)).toBe(true);
 await expect(page.locator('#installBtn')).toBeHidden();
});
