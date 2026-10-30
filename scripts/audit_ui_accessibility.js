const {chromium}=require('@playwright/test');
const {spawn}=require('node:child_process');
const fs=require('node:fs');
const path=require('node:path');
const root=path.resolve(__dirname,'..');
const output=process.env.KEP_A11Y_REPORT||path.join(root,'docs/qa/accessibility-audit-2026-10-30.json');
const server=spawn('python',['-m','http.server','4181','--bind','127.0.0.1','--directory','docs'],{cwd:root,stdio:'ignore'});
(async()=>{
 const browser=await chromium.launch();
 const results=[];
 try{
  let ready=false;
  for(let i=0;i<30;i++){try{if((await fetch('http://127.0.0.1:4181/app.html')).ok){ready=true;break}}catch{}await new Promise(r=>setTimeout(r,100));}
  if(!ready)throw Error('Audit server unavailable');
  for(const width of [390,1280]){
   const context=await browser.newContext({viewport:{width,height:844},reducedMotion:'reduce',serviceWorkers:'block'});
   await context.route('https://**',r=>r.abort());
   const page=await context.newPage();
   async function audit(name){
    await page.addScriptTag({path:require.resolve('axe-core/axe.min.js')});
    const result=await page.evaluate(async()=>await axe.run(document,{runOnly:{type:'tag',values:['wcag2a','wcag2aa','wcag21a','wcag21aa','wcag22aa','best-practice']}}));
    results.push({name,width,violations:result.violations.map(v=>({id:v.id,impact:v.impact,help:v.help,nodes:v.nodes.map(n=>({target:n.target,html:n.html,failureSummary:n.failureSummary}))})),incomplete:result.incomplete.map(v=>({id:v.id,nodes:v.nodes.map(n=>n.target)})),passes:result.passes.length});
   }
   await page.goto('http://127.0.0.1:4181/app.html');await page.locator('#quickStart').waitFor();await audit('entry');
   await page.locator('[data-quick-stage="exam_fee"]').click();await audit('home');
   for(const view of ['eligibility','documents','fees','gaps','contract','workplace','payroll','companyHub']){
    await page.evaluate(view=>switchView(view,false),view);await audit(view);
    if(view==='eligibility'){await page.locator('#checkEligibilityBtn').click();await audit('eligibility-errors');}
    if(view==='contract'){await page.locator('#checkContractBtn').click();await audit('contract-result-unconfirmed-source');}
   }
   await page.evaluate(()=>{switchView('journey',false);openStage(route.stages.find(s=>s.id==='predeparture_training'));});await audit('stage-dialog');
   await page.locator('#stageDialog .close').click();await page.waitForFunction(()=>!history.state?.kepStageDialog);
   await page.evaluate(()=>{
    switchView('documents',false);
    document.querySelector('.consistency-check').open=true;
   });await audit('documents-expanded');
   await page.evaluate(()=>{
    sourceReviewStatus={state:'clean',reviewRequiredUrls:[],fetchFailureUrls:[]};
    applyCurrentStage('visa_docs',true);switchView('documents',false);
   });
   await page.locator('#docScopeSelect').selectOption('visa_sep08_2026');
   await page.locator('#formWizardSection').waitFor();
   await page.locator('#formFieldCheck').evaluate(el=>el.open=true);
   await audit('wizard-clean-source-fixture');
   for(const name of ['index','privacy','countries','readiness']){
    await page.goto('http://127.0.0.1:4181/'+name+'.html');
    await audit(name);
   }
   await page.goto('http://127.0.0.1:4181/beta.html');await page.locator('#applicationPanel').waitFor();await audit('beta');
   await context.close();
  }
  fs.writeFileSync(output,JSON.stringify({axeVersion:require('axe-core/package.json').version,automatedOnly:true,results},null,2)+'\n');
  for(const r of results)console.log(r.name,r.width,r.violations.map(v=>v.id+':'+v.nodes.length).join(',')||'PASS');
 }finally{await browser.close();server.kill();}
})().catch(e=>{console.error(e);server.kill();process.exitCode=1;});
