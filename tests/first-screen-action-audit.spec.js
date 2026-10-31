const {test,expect}=require('@playwright/test');
for(const width of [320,390,768]) test('first-screen action usability at '+width,async({page})=>{
 await page.setViewportSize({width,height:780});await page.goto('/app.html');
 await page.locator('#quickStart').waitFor();await page.locator('[data-quick-stage="exam_fee"]').click();
 const stats=await page.evaluate(()=>{
  const el=document.querySelector('#nextAction .primary');const r=el.getBoundingClientRect();const nav=document.querySelector('.utility-nav').getBoundingClientRect();
  return {button:{top:r.top,bottom:r.bottom,left:r.left,right:r.right,height:r.height},navTop:nav.top,innerWidth,scrollWidth:document.documentElement.scrollWidth,visible:!!el.getClientRects().length};
 });console.log('FIRST_SCREEN '+width+' '+JSON.stringify(stats));
 expect(stats.visible).toBe(true);expect(stats.button.height).toBeGreaterThanOrEqual(40);expect(stats.button.left).toBeGreaterThanOrEqual(0);expect(stats.button.right).toBeLessThanOrEqual(width);expect(stats.scrollWidth).toBeLessThanOrEqual(width);
});
