const {chromium,webkit}=require('@playwright/test');const {spawn}=require('node:child_process');const fs=require('node:fs');const path=require('node:path');
(async()=>{
 const output=path.resolve('docs/qa/storage-recovery-screenshots');fs.mkdirSync(output,{recursive:true});const records=[];
 const server=spawn('python',['-m','http.server','4189','--bind','127.0.0.1','--directory','docs'],{stdio:'ignore'});
 try{
  let ready=false;for(let i=0;i<30;i++){try{if((await fetch('http://127.0.0.1:4189/app.html')).ok){ready=true;break}}catch{}await new Promise(r=>setTimeout(r,100));}if(!ready)throw Error('Capture server unavailable');
  for(const [engine,type]of Object.entries({chromium,webkit})){
   const browser=await type.launch();
   try{
    for(const [state,width]of [['quota',320],['quota',390],['quota-text200',320],['blocked-read',390],['deletion-blocked',390],['participant-editor',320]]){
     const context=await browser.newContext({viewport:{width,height:844},isMobile:engine==='webkit',hasTouch:engine==='webkit',serviceWorkers:'block',reducedMotion:'reduce'});context.setDefaultTimeout(15000);context.setDefaultNavigationTimeout(15000);
     await context.route('https://**',r=>r.abort());
     if(state.startsWith('quota')||state==='blocked-read')await context.addInitScript(state=>{
      const set=Storage.prototype.setItem;Storage.prototype.setItem=function(k,v){if(String(k).startsWith('kep.'))throw new DOMException('test storage fault',state==='blocked-read'?'SecurityError':'QuotaExceededError');return set.call(this,k,v)};
      if(state==='blocked-read')Storage.prototype.getItem=function(){throw new DOMException('test read fault','SecurityError')};
     },state);
     const page=await context.newPage();const errors=[];page.on('pageerror',e=>errors.push(e.message));await page.goto('http://127.0.0.1:4189/app.html');await page.locator('#quickStart').waitFor();await page.locator('[data-quick-stage="exam_fee"]').click();
     if(state==='quota-text200')await page.evaluate(()=>document.documentElement.style.fontSize='200%');
     if(state==='deletion-blocked'){
      await page.evaluate(()=>{write(KEYS.contract,{enterpriseName:'Contoh perusahaan'});renderContract();switchView('contract',false);Storage.prototype.removeItem=function(){throw new DOMException('test deletion fault','SecurityError')}});await page.locator('#resetContractBtn').click();
     }
     if(state==='participant-editor'){
      await page.evaluate(()=>{localStorage.setItem('kep.contract.KEP-0001',JSON.stringify({enterpriseName:'Contoh perusahaan A'}));localStorage.setItem('kep.contract.KEP-0002',JSON.stringify({enterpriseName:'Contoh perusahaan B'}));switchView('gaps',false)});
      await page.locator('#betaValidationPanel').evaluate(el=>el.open=true);
      for(const id of ['KEP-0001','KEP-0002']){await page.locator('#betaTesterId').fill(id);await page.locator('#saveBetaTesterIdBtn').click();}
      await page.locator('#betaTesterId').scrollIntoViewIfNeeded();
     }else if(state==='quota-text200')await page.locator('#backupSessionProgressBtn').scrollIntoViewIfNeeded();
     else await page.locator('#storageStatus').scrollIntoViewIfNeeded();
     await page.screenshot({path:path.join(output,`${engine}-${state}-${width}.jpg`),type:'jpeg',quality:85});
     records.push({engine,state,width,...await page.evaluate(()=>({viewport:innerWidth,documentWidth:document.documentElement.scrollWidth})),backupActionReachable:state==='quota-text200'?await page.locator('#backupSessionProgressBtn').evaluate(el=>{const r=el.getBoundingClientRect();return r.top>=0&&r.bottom<=document.querySelector('.utility-nav').getBoundingClientRect().top}):null,pageErrors:errors});await context.close();
    }
   }finally{await browser.close();}
  }
  fs.writeFileSync('docs/qa/storage-recovery-visual-matrix.json',JSON.stringify({physicalDeviceTesting:false,records},null,2)+'\n');if(records.some(r=>r.backupActionReachable===false))throw Error('Enlarged backup action is covered');console.log(JSON.stringify({screenshots:records.length,overflow:records.filter(r=>r.documentWidth>r.viewport).length,pageErrors:records.filter(r=>r.pageErrors.length).length}));
 }finally{server.kill();}
})().catch(e=>{console.error(e);process.exitCode=1});
