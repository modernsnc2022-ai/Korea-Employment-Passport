const {test,expect}=require('@playwright/test');

async function openStageDialog(page,stageId='eligibility') {
 await page.goto('/app.html',{waitUntil:'domcontentloaded'});
 await page.waitForFunction(()=>document.querySelector('#progressText')?.textContent?.includes('/ 27'));
 await page.evaluate(id=>{
   const stage=route.stages.find(item=>item.id===id);
   if(!stage)throw new Error('Missing stage '+id);
   openStage(stage);
 },stageId);
 await expect(page.locator('#stageDialog')).toBeVisible();
}

async function geometry(page){
 return page.evaluate(()=>{
  const box=document.querySelector('#stageDialog');
  const header=box.querySelector('.stage-dialog-header');
  const body=box.querySelector('.stage-dialog-body');
  const foot=box.querySelector('.stage-dialog-footer');
  const close=box.querySelector('.close');
  const btn=document.querySelector('#stageDoneBtn');
  const rect=x=>({top:x.getBoundingClientRect().top,bottom:x.getBoundingClientRect().bottom});
  return {box:rect(box),header:rect(header),body:rect(body),foot:rect(foot),
    close:rect(close),button:rect(btn),scrollTop:body.scrollTop,
    clientHeight:body.clientHeight,scrollHeight:body.scrollHeight,
    docWidth:document.documentElement.scrollWidth,viewport:window.innerWidth,
    footerVisible:btn.getBoundingClientRect().bottom <= window.innerHeight+2};
 });
}

test('M46 long FAQ stage keeps header X and footer CTA visible while only content scrolls',async({page})=>{
 await page.setViewportSize({width:990,height:760});
 await openStageDialog(page);
 const first=await geometry(page);
 expect(first.scrollHeight).toBeGreaterThan(first.clientHeight+100);
 await page.locator('#stageDialog .stage-dialog-body').evaluate(el=>{el.scrollTop=el.scrollHeight});
 const after=await geometry(page);
 expect(after.scrollTop).toBeGreaterThan(100);
 expect(Math.abs(first.close.top-after.close.top)).toBeLessThan(2);
 expect(Math.abs(first.button.top-after.button.top)).toBeLessThan(2);
 expect(after.close.top).toBeGreaterThanOrEqual(after.box.top-1);
 expect(after.close.bottom).toBeLessThan(after.header.bottom+1);
 expect(after.button.bottom).toBeLessThanOrEqual(after.box.bottom+1);
 expect(after.footerVisible).toBe(true);
 await page.locator('#stageDialog .stage-dialog-header .close').click();
 await expect(page.locator('#stageDialog')).toBeHidden();
});

test('M46 mobile 390 and narrow 320 and small-height dialogs always expose X and CTA',async({page})=>{
 for(const [width,height] of [[390,700],[320,568],[390,380]]){
  await page.setViewportSize({width,height});
  await openStageDialog(page,'eligibility');
  await page.locator('#stageDialog .stage-dialog-body').evaluate(el=>el.scrollTop=el.scrollHeight);
  const m=await geometry(page);
  expect(m.scrollTop).toBeGreaterThan(20);
  expect(m.close.top).toBeGreaterThanOrEqual(0);
  expect(m.close.bottom).toBeLessThanOrEqual(height+1);
  expect(m.button.top).toBeGreaterThanOrEqual(0);
  expect(m.button.bottom).toBeLessThanOrEqual(height+1);
  expect(m.docWidth).toBeLessThanOrEqual(m.viewport+1);
  await page.locator('#stageDialog .stage-dialog-header .close').click();
  await expect(page.locator('#stageDialog')).toBeHidden();
 }
});

test('M46 modal escape preserves native close behavior and exposes one close control',async({page})=>{
 await openStageDialog(page);
 await expect(page.locator('#stageDialog .close')).toHaveCount(1);
 await expect(page.locator('#stageDialog .close')).toHaveAttribute('aria-label','Tutup panduan tahap');
 await expect(page.locator('#stageDialog .stage-dialog-footer #stageDoneBtn')).toHaveCount(1);
 await page.locator('#stageDialog .stage-dialog-body').evaluate(el=>el.scrollTop=el.scrollHeight);
 await page.keyboard.press('Escape');
 await expect(page.locator('#stageDialog')).toBeHidden();
});

test('M46 submit warning still scrolls inside modal while X and action button stay visible',async({page})=>{
 await openStageDialog(page,'job_application');
 await page.evaluate(()=>{
   document.querySelector('#stageDialog').close();
   applyCurrentStage('job_application',true);
   openStage(route.stages.find(x=>x.id==='job_application'));
 });
 await expect(page.locator('#stageDoneBtn')).toBeEnabled();
 await page.locator('#stageDoneBtn').click();
 await expect(page.locator('#preSubmitResult')).toBeVisible();
 await expect(page.locator('#preSubmitResult')).toContainText('JANGAN LANJUT DULU');
 const m=await geometry(page);
 expect(m.close.top).toBeGreaterThanOrEqual(0);
 expect(m.button.bottom).toBeLessThanOrEqual(m.box.bottom+1);
 await page.locator('#stageDialog .close').click();
 await expect(page.locator('#stageDialog')).toBeHidden();
});
