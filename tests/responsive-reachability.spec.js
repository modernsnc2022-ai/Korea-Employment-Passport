const {test,expect}=require('@playwright/test');
for(const [width,height,scale] of [[320,568,1],[390,568,1],[320,568,2]]){
 test(`tool actions remain reachable at ${width}x${height} with text scale ${scale}`,async({page})=>{
  await page.setViewportSize({width,height});
  await page.goto('/app.html');await page.locator('#quickStart').waitFor();
  await page.locator('[data-quick-stage="exam_fee"]').click();
  if(scale===2)await page.evaluate(()=>document.documentElement.style.fontSize='200%');
  for(const view of ['eligibility','documents','fees','gaps','contract','workplace','payroll','companyHub']){
   await page.evaluate(view=>switchView(view,false),view);
   const section=page.locator('#'+view);
   await section.locator('details').evaluateAll(nodes=>nodes.forEach(el=>el.open=true));
   expect(await section.evaluate(el=>el.scrollWidth<=el.clientWidth),view+' width').toBe(true);
   const action=section.locator('button:visible').last();
   await action.scrollIntoViewIfNeeded();
   const box=await action.boundingBox();const nav=await page.locator('.utility-nav').boundingBox();
   expect(box.y,view+' top').toBeGreaterThanOrEqual(0);
   expect(box.y+box.height,view+' covered action').toBeLessThanOrEqual(nav.y+1);
  }
 });
}
