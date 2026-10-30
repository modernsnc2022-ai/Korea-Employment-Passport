const {test,expect}=require('@playwright/test');

for(const width of [390,1280]){
 test(`all visible app views and dialog have no automated accessibility violations at ${width}px`,async({page})=>{
  await page.setViewportSize({width,height:844});
  await page.goto('/app.html');await page.locator('#quickStart').waitFor();
  async function audit(name){
   await page.addScriptTag({path:require.resolve('axe-core/axe.min.js')});
   const violations=await page.evaluate(async()=>{
    const r=await axe.run(document,{runOnly:{type:'tag',values:['wcag2a','wcag2aa','wcag21a','wcag21aa','wcag22aa','best-practice']}});
    return r.violations.map(v=>({id:v.id,targets:v.nodes.map(n=>n.target)}));
   });
   expect(violations,`${name}: ${JSON.stringify(violations)}`).toEqual([]);
  }
  await audit('entry');await page.locator('[data-quick-stage="exam_fee"]').click();await audit('home');
  for(const view of ['eligibility','documents','fees','gaps','contract','workplace','payroll','companyHub']){
   await page.evaluate(view=>switchView(view,false),view);await audit(view);
  }
  await page.evaluate(()=>{switchView('journey',false);openStage(route.stages.find(s=>s.id==='predeparture_training'));});
  await audit('stage-dialog');
  await page.locator('#stageDialog .close').click();await page.waitForFunction(()=>!history.state?.kepStageDialog);
  await page.evaluate(()=>{switchView('documents',false);document.querySelector('.consistency-check').open=true;});
  await audit('documents-expanded');
  await page.evaluate(()=>{sourceReviewStatus={state:'clean',reviewRequiredUrls:[],fetchFailureUrls:[]};applyCurrentStage('visa_docs',true);switchView('documents',false);});
  await page.locator('#docScopeSelect').selectOption('visa_sep08_2026');
  await expect(page.locator('#formWizardSection')).toBeVisible();
  await page.locator('#formFieldCheck').evaluate(el=>el.open=true);
  await audit('wizard-clean-source-fixture');
 });
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
