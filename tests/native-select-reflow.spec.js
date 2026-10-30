const {test,expect}=require('@playwright/test');
test('long selections remain changeable without expanding enlarged support and company forms',async({page})=>{
 await page.setViewportSize({width:320,height:568});await page.goto('/app.html');await page.locator('#quickStart').waitFor();await page.locator('[data-quick-stage="exam_fee"]').click();await page.evaluate(()=>document.documentElement.style.fontSize='200%');
 for(const [view,id,value,text] of [['gaps','gapHelper','Teman / pekerja senior','Teman / pekerja senior'],['companyHub','companyInvestigationTier','phone','2 · Riset + verifikasi telepon bila memungkinkan']]){
  await page.evaluate(view=>{switchView(view,false);document.querySelector('#'+view).querySelectorAll('details').forEach(d=>d.open=true)},view);
  const select=page.locator('#'+id);await select.selectOption(value);await expect(select).toHaveValue(value);await expect(select.locator('option:checked')).toHaveText(text);
  expect(await page.locator('#'+view).evaluate(el=>el.scrollWidth<=el.clientWidth)).toBe(true);
  await select.focus();await expect(select).toBeFocused();
 }
});
