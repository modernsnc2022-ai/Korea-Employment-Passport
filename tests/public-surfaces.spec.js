const {test,expect}=require('@playwright/test');

for(const name of ['index','privacy','countries','readiness','beta']){
 test(`${name} is readable, named and contained on narrow and wide screens`,async({page})=>{
  for(const width of [320,390,1280]){
   await page.setViewportSize({width,height:844});
   await page.goto('/'+name+'.html');
   if(name==='beta')await page.locator('#applicationPanel').waitFor();
   await expect(page.locator('h1')).toHaveCount(1);
   expect(await page.evaluate(()=>document.documentElement.scrollWidth)).toBeLessThanOrEqual(width);
   await page.addScriptTag({path:require.resolve('axe-core/axe.min.js')});
   const errors=await page.evaluate(async()=>{
    const r=await axe.run(document,{runOnly:{type:'tag',values:['wcag2a','wcag2aa','wcag21a','wcag21aa','wcag22aa','best-practice']}});
    return r.violations.map(v=>({id:v.id,targets:v.nodes.map(n=>n.target)}));
   });
   expect(errors,`${name} ${width}: ${JSON.stringify(errors)}`).toEqual([]);
  }
 });
}

test('signup keeps the access warning before the form and technical release details after it',async({page})=>{
 await page.goto('/beta.html');await page.locator('#applicationPanel').waitFor();
 const warning=await page.locator('#closedPanel').boundingBox();
 const form=await page.locator('#applicationPanel').boundingBox();
 const details=await page.locator('#releaseGateNote').boundingBox();
 expect(warning.y).toBeLessThan(form.y);expect(form.y).toBeLessThan(details.y);
 await expect(page.locator('#releaseGateNote [data-release-gate]')).toHaveCount(6);
 await page.goto('/index.html');
 await page.waitForURL('**/app.html');
 await expect(page.locator('#routeTitle')).toContainText('Indonesia');
 await expect(page.locator('body > footer')).toContainText('Bukan layanan pemerintah');
});
