const {chromium,webkit,firefox}=require('@playwright/test');
const {spawn}=require('node:child_process');
const fs=require('node:fs');
const path=require('node:path');
const output=path.resolve('docs/qa/browser-parity-screenshots');
(async()=>{
 fs.mkdirSync(output,{recursive:true});
 const server=spawn('python',['-m','http.server','4186','--bind','127.0.0.1','--directory','docs'],{stdio:'ignore'});
 const records=[];const engines={chromium,webkit,firefox};
 const selected=(process.env.KEP_CAPTURE_ENGINES||'chromium,webkit,firefox').split(',');
 if(selected.some(name=>!engines[name]))throw Error('Invalid KEP_CAPTURE_ENGINES');
 try{
  let ready=false;for(let i=0;i<30;i++){try{if((await fetch('http://127.0.0.1:4186/app.html')).ok){ready=true;break}}catch{}await new Promise(r=>setTimeout(r,100));}
  if(!ready)throw Error('Capture server unavailable');
  for(const engine of selected){
   const type=engines[engine];
   const browser=await type.launch();
   try{
    for(const width of [390,320]){
     const context=await browser.newContext({viewport:{width,height:844},isMobile:engine==='webkit',hasTouch:engine==='webkit',reducedMotion:'reduce',serviceWorkers:'block'});
     context.setDefaultTimeout(15000);context.setDefaultNavigationTimeout(15000);
     await context.route('https://**',r=>r.abort());const page=await context.newPage();const errors=[];page.on('pageerror',e=>errors.push(e.message));
     async function shot(state){
      await page.screenshot({path:path.join(output,`${engine}-${state}-${width}.jpg`),type:'jpeg',quality:85});
      records.push({engine,state,width,mobileTouchEmulation:engine==='webkit',...await page.evaluate(()=>({viewport:innerWidth,documentWidth:document.documentElement.scrollWidth})),pageErrors:[...errors]});
     }
     await page.goto('http://127.0.0.1:4186/app.html');await page.locator('#quickStart').waitFor();await page.locator('[data-quick-stage="exam_fee"]').click();
     if(width===390){
      await shot('home');await page.locator('.utility-tab[data-view="documents"]').click();await shot('documents');
      await page.evaluate(()=>{applyCurrentStage('predeparture_training',true);switchView('journey',false);openStage(route.stages.find(s=>s.id==='predeparture_training'));});await shot('notice');
     }else{
      await page.locator('.utility-tab[data-view="documents"]').click();await page.evaluate(()=>document.documentElement.style.fontSize='200%');await page.locator('#docList .doc-file').first().scrollIntoViewIfNeeded();await shot('documents-text200');
      for(const [view,id,state] of [['gaps','gapHelper','support-select-text200'],['companyHub','companyInvestigationTier','company-select-text200']]){
       await page.evaluate(view=>{switchView(view,false);document.querySelector('#'+view).querySelectorAll('details').forEach(d=>d.open=true)},view);
       await page.locator('#'+id).selectOption(id==='gapHelper'?'Teman / pekerja senior':'phone');
       await page.locator('#'+id).scrollIntoViewIfNeeded();await shot(state);
      }
     }
     await context.close();
    }
   }finally{await browser.close();}
  }
  fs.writeFileSync('docs/qa/browser-parity-visual-matrix.json',JSON.stringify({physicalDeviceTesting:false,records},null,2)+'\n');
  console.log(JSON.stringify({screenshots:records.length,overflow:records.filter(r=>r.documentWidth>r.viewport).length,pageErrors:records.filter(r=>r.pageErrors.length).length}));
 }finally{server.kill();}
})().catch(e=>{console.error(e);process.exitCode=1});
