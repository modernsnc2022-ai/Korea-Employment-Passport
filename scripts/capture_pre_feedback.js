const {chromium}=require('@playwright/test');
const {spawn}=require('node:child_process');
const fs=require('node:fs');
const path=require('node:path');
const output=path.resolve('docs/qa/pre-feedback-screenshots');
(async()=>{
 fs.mkdirSync(output,{recursive:true});
 const server=spawn('python',['-m','http.server','4184','--bind','127.0.0.1','--directory','docs'],{stdio:'ignore'});
 const browser=await chromium.launch();const results=[];
 try{
  let ready=false;
  for(let i=0;i<30;i++){try{if((await fetch('http://127.0.0.1:4184/app.html')).ok){ready=true;break}}catch{}await new Promise(r=>setTimeout(r,100));}
  if(!ready)throw Error('Capture server unavailable');
  for(const width of [320,360,375,390,430,768,1280]){
   const context=await browser.newContext({viewport:{width,height:844},reducedMotion:'reduce',serviceWorkers:'block'});
   await context.route('https://**',r=>r.abort());
   const page=await context.newPage();const errors=[];page.on('pageerror',e=>errors.push(e.message));
   async function shot(name){
    await page.screenshot({path:path.join(output,`${name}-${width}.jpg`),type:'jpeg',quality:85});
    results.push({name,width,...await page.evaluate(()=>({viewport:innerWidth,documentWidth:document.documentElement.scrollWidth})),pageErrors:[...errors]});
   }
   await page.goto('http://127.0.0.1:4184/app.html');await page.locator('#quickStart').waitFor();
   await page.locator('[data-quick-stage="exam_fee"]').click();await shot('home');
   await page.locator('.utility-tab[data-view="documents"]').click();await shot('documents');
   await page.evaluate(()=>{applyCurrentStage('predeparture_training',true);switchView('journey',false);openStage(route.stages.find(s=>s.id==='predeparture_training'));});
   await shot('notice');await page.locator('#stageDialog .close').click();await page.waitForFunction(()=>!history.state?.kepStageDialog);
   if(width===320){
    await page.evaluate(()=>{applyCurrentStage('eligibility',true);switchView('eligibility');});
    await page.locator('#checkEligibilityBtn').click();await shot('eligibility-errors');
    await page.evaluate(()=>{document.documentElement.style.fontSize='200%';switchView('documents',false);});
    await page.locator('#docList .doc-file').first().scrollIntoViewIfNeeded();await shot('documents-text200');
   }
   if(width===390){
    await page.evaluate(()=>switchView('contract',false));await page.locator('#contract_monthlyWage').fill('1000000');await page.locator('#checkContractBtn').click();
    await page.locator('#contractResult').scrollIntoViewIfNeeded();await shot('contract-source-state');
   }
   if([390,1280].includes(width)){
    for(const name of ['index','beta','privacy']){
     await page.goto('http://127.0.0.1:4184/'+name+'.html');
     if(name==='beta')await page.locator('#applicationPanel').waitFor();
     await shot(name);
    }
   }
   await context.close();
  }
  fs.writeFileSync('docs/qa/pre-feedback-visual-matrix.json',JSON.stringify({environment:'Cloud Chromium viewport emulation, not physical-device testing',sourceState:'Unmodified checked-in source-review data',results},null,2)+'\n');
  console.log(JSON.stringify({screenshots:results.length,overflow:results.filter(r=>r.documentWidth>r.viewport).length,pageErrors:results.filter(r=>r.pageErrors.length).length}));
 }finally{await browser.close();server.kill();}
})().catch(e=>{console.error(e);process.exitCode=1});
