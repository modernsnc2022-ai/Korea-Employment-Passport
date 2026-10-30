const {test,expect}=require('@playwright/test');
const views=['eligibility','documents','fees','gaps','contract','workplace','payroll','companyHub'];
for(const width of [390,1280]){
 for(const state of ['entry','home',...views,'stage-dialog','documents-expanded','wizard-clean-source-fixture']){
  test(`automated accessibility: ${state} at ${width}px`,async({page})=>{
   await page.setViewportSize({width,height:844});
   await page.goto('/app.html');await page.locator('#quickStart').waitFor();
   if(state!=='entry')await page.locator('[data-quick-stage="exam_fee"]').click();
   if(views.includes(state))await page.evaluate(view=>switchView(view,false),state);
   if(state==='stage-dialog')await page.evaluate(()=>openStage(route.stages.find(s=>s.id==='predeparture_training')));
   if(state==='documents-expanded')await page.evaluate(()=>{switchView('documents',false);document.querySelector('.consistency-check').open=true;});
   if(state==='wizard-clean-source-fixture'){
    await page.evaluate(()=>{sourceReviewStatus={state:'clean',reviewRequiredUrls:[],fetchFailureUrls:[]};applyCurrentStage('visa_docs',true);switchView('documents',false);});
    await page.locator('#docScopeSelect').selectOption('visa_sep08_2026');
    await expect(page.locator('#formWizardSection')).toBeVisible();
    await page.locator('#formFieldCheck').evaluate(el=>el.open=true);
   }
   await page.addScriptTag({path:require.resolve('axe-core/axe.min.js')});
   const violations=await page.evaluate(async()=>{
    const r=await axe.run(document,{runOnly:{type:'tag',values:['wcag2a','wcag2aa','wcag21a','wcag21aa','wcag22aa','best-practice']}});
    return r.violations.map(v=>({id:v.id,targets:v.nodes.map(n=>n.target)}));
   });
   expect(violations,`${state}: ${JSON.stringify(violations)}`).toEqual([]);
  });
 }
}

test('missing eligibility answers focus the first named field and clear stale feedback on edit',async({page})=>{
 await page.goto('/app.html');await page.locator('#quickStart').waitFor();
 await page.locator('[data-quick-stage="eligibility"]').click();
 await page.locator('#nextAction .primary').click();
 await page.locator('#checkEligibilityBtn').click();
 const firstId=await page.locator('#eligibilityForm [aria-invalid="true"]').first().getAttribute('id');
 const first=page.locator('#'+firstId);
 await expect(first).toBeFocused();
 await expect(first).toHaveAccessibleName(/.+/);
 await expect(page.locator('#eligibilityResult')).toContainText('Pemeriksaan belum lengkap');
 await first.fill('1995-01-01');
 await expect(first).not.toHaveAttribute('aria-invalid','true');
 await expect(page.locator('#eligibilityResult')).toBeHidden();
 expect(await page.evaluate(()=>Object.keys(localStorage).some(key=>key.startsWith('elig_')))).toBe(false);
});
