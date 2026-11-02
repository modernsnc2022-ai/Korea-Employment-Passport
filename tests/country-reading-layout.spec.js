const {test,expect}=require('@playwright/test');
for(const name of ['cn','kh','mn','pk','tl']){
 test(`${name} preview has reading margins, navigation and an explicit hold`,async({page})=>{
  for(const width of [320,390,1280]){
   await page.setViewportSize({width,height:844});await page.goto('/'+name+'.html');
   const main=page.locator('main');const box=await main.locator('h1').boundingBox();
   expect(box.x).toBeGreaterThanOrEqual(16);expect(box.x+box.width).toBeLessThanOrEqual(width-16);
   await expect(page.locator('h1')).toHaveCount(1);await expect(page.locator('main')).toContainText('RESEARCH / HOLD');
   await expect(page.getByRole('navigation',{name:'Country navigation'}).getByRole('link',{name:'Countries',exact:true})).toBeVisible();
   const bounds=await page.locator('main').evaluate(el=>Array.from(el.querySelectorAll('h1,h2,p,a')).map(n=>{const r=n.getBoundingClientRect();return{left:r.left,right:r.right}}));
   expect(bounds.every(r=>r.left>=0&&r.right<=width)).toBe(true);
   await page.addScriptTag({path:require.resolve('axe-core/axe.min.js')});
   expect(await page.evaluate(async()=>(await axe.run(document)).violations.map(v=>v.id))).toEqual([]);
  }
 });
}
