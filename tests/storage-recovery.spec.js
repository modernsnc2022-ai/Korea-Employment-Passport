const {test,expect}=require('@playwright/test');const fs=require('node:fs');
async function failStorage(page,mode){
 await page.addInitScript(mode=>{
  const get=Storage.prototype.getItem,set=Storage.prototype.setItem;
  set.call(localStorage,'kep.contract',JSON.stringify({enterpriseName:'private persistent marker'}));
  window.testRawGet=key=>get.call(localStorage,key);
  Storage.prototype.setItem=function(key,value){if(String(key).startsWith('kep.'))throw new DOMException('test storage failure',mode==='denied'?'SecurityError':'QuotaExceededError');return set.call(this,key,value)};
  if(mode==='denied')Storage.prototype.getItem=function(){throw new DOMException('test blocked read','SecurityError')};
 },mode);
}
async function backup(page,button){
 const pending=page.waitForEvent('download');await page.locator(button).click();const file=await pending;return JSON.parse(fs.readFileSync(await file.path(),'utf8'));
}
test('quota failure retains current-tab progress and a privacy-safe downloadable backup',async({page})=>{
 await failStorage(page,'quota');const errors=[];page.on('pageerror',e=>errors.push(e.message));await page.goto('/app.html');await page.locator('#quickStart').waitFor();await page.locator('[data-quick-stage="exam_fee"]').click();
 await expect(page.locator('#quickStart')).toBeHidden();await expect(page.locator('#nextAction')).toContainText('Pembayaran biaya EPS-TOPIK');await expect(page.locator('#storageStatus')).toContainText('tab ini');
 const payload=await backup(page,'#backupSessionProgressBtn');expect(payload.progress.done.length).toBe(2);expect(JSON.stringify(payload)).not.toContain('private persistent marker');
 expect(await page.evaluate(()=>window.testRawGet('kep.doneStages'))).toBe(null);expect(await page.evaluate(()=>window.testRawGet('kep.contract'))).toContain('private persistent marker');expect(errors).toEqual([]);
});
test('blocked storage still loads the guide and isolates current-tab participants',async({page})=>{
 await failStorage(page,'denied');await page.goto('/app.html?beta=KEP-0001&stage=slc');await expect(page.locator('#nextAction')).toBeVisible();await expect(page.locator('#routeLoadRecovery')).toBeHidden();
 await page.evaluate(()=>switchView('contract',false));await page.locator('#contract_enterpriseName').fill('Session company A');await page.locator('#checkContractBtn').click();
 for(const id of ['KEP-0002','KEP-0001']){
  await page.locator('.utility-tab[data-view="gaps"]').click();await page.locator('#betaValidationPanel').evaluate(el=>el.open=true);await page.locator('#betaTesterId').fill(id);await page.locator('#saveBetaTesterIdBtn').click();
  await expect(page.locator('#betaTesterIdStatus')).not.toContainText('tersimpan');await expect(page.locator('#contract_enterpriseName')).toHaveValue(id==='KEP-0001'?'Session company A':'');
  if(id==='KEP-0002')await page.locator('[data-quick-stage="exam_fee"]').click();
 }
});
test('a failed contract deletion never claims that the saved record was erased',async({page})=>{
 await page.goto('/app.html');await page.locator('#quickStart').waitFor();await page.locator('[data-quick-stage="exam_fee"]').click();
 await page.evaluate(()=>{write(KEYS.contract,{enterpriseName:'Retain me'});renderContract();switchView('contract',false);const remove=Storage.prototype.removeItem;window.testRestoreRemove=()=>Storage.prototype.removeItem=remove;Storage.prototype.removeItem=function(){throw new DOMException('test blocked removal','SecurityError')}});
 await page.locator('#resetContractBtn').click();await expect(page.locator('#contract_enterpriseName')).toHaveValue('Retain me');await expect(page.locator('#storageStatus')).toContainText('belum dihapus');expect(await page.evaluate(()=>read(KEYS.contract,{}))).toEqual({enterpriseName:'Retain me'});
 await page.evaluate(()=>window.testRestoreRemove());await page.locator('#resetContractBtn').click();await expect(page.locator('#contract_enterpriseName')).toHaveValue('');await expect(page.locator('#storageStatus')).not.toContainText('belum dihapus');
});
test('restoring a backup in current-tab mode does not reload away the restored progress',async({page})=>{
 await failStorage(page,'quota');await page.goto('/app.html');await page.locator('#quickStart').waitFor();await page.locator('[data-quick-stage="exam_fee"]').click();
 const payload=await backup(page,'#backupSessionProgressBtn');payload.progress.done=[];payload.progress.quickSetup=true;
 let reloads=0;page.on('framenavigated',f=>{if(f===page.mainFrame())reloads++});
 await page.locator('#restoreProgressFile').setInputFiles({name:'progress.json',mimeType:'application/json',buffer:Buffer.from(JSON.stringify(payload))});await expect(page.locator('#backupProgressResult')).toContainText('tab ini');await expect(page.locator('#nextAction')).toContainText(/Cek kelayakan/i);
 await new Promise(resolve=>setTimeout(resolve,750));expect(reloads).toBe(0);
});
test('a mid-restore quota error rolls back previous device progress before using current-tab state',async({page})=>{
 await page.goto('/app.html');await page.locator('#quickStart').waitFor();await page.locator('[data-quick-stage="exam_fee"]').click();
 const payload=await page.evaluate(()=>makeProgressBackup());const original=await page.evaluate(()=>localStorage.getItem('kep.doneStages'));payload.progress.done=[];
 await page.evaluate(()=>{const set=Storage.prototype.setItem;Storage.prototype.setItem=function(k,v){if(k==='kep.scopeSelections')throw new DOMException('test mid-batch quota','QuotaExceededError');return set.call(this,k,v)}});
 await page.locator('.trust-panel').evaluate(el=>el.open=true);await page.locator('#restoreProgressFile').setInputFiles({name:'progress.json',mimeType:'application/json',buffer:Buffer.from(JSON.stringify(payload))});
 await expect(page.locator('#backupProgressResult')).toContainText('tab ini');expect(await page.evaluate(()=>localStorage.getItem('kep.doneStages'))).toBe(original);await expect(page.locator('#nextAction')).toContainText(/Cek kelayakan/i);
});
test('the storage warning and backup action remain accessible on a narrow mobile screen',async({page})=>{
 await page.setViewportSize({width:320,height:568});await failStorage(page,'quota');await page.goto('/app.html');await page.locator('#quickStart').waitFor();await page.locator('[data-quick-stage="exam_fee"]').click();
 const status=page.locator('#storageStatus');await expect(status).toHaveAttribute('role','alert');expect(await status.evaluate(el=>el.scrollWidth<=el.clientWidth)).toBe(true);
 await page.locator('#backupSessionProgressBtn').scrollIntoViewIfNeeded();const button=await page.locator('#backupSessionProgressBtn').boundingBox(),nav=await page.locator('.utility-nav').boundingBox();expect(button.y+button.height).toBeLessThanOrEqual(nav.y);
 await page.addScriptTag({path:require.resolve('axe-core/axe.min.js')});expect(await page.evaluate(async()=>(await axe.run(document)).violations.map(v=>v.id))).toEqual([]);
});
test('when device rollback is blocked the original progress remains recoverable in a backup',async({page})=>{
 await page.goto('/app.html');await page.locator('#quickStart').waitFor();await page.locator('[data-quick-stage="exam_fee"]').click();
 const original=await page.evaluate(()=>localStorage.getItem('kep.doneStages'));const payload=await page.evaluate(()=>makeProgressBackup());payload.progress.done=[];
 await page.evaluate(original=>{const set=Storage.prototype.setItem;Storage.prototype.setItem=function(k,v){if(k==='kep.scopeSelections'||k==='kep.doneStages'&&v===original)throw new DOMException('test rollback unavailable','SecurityError');return set.call(this,k,v)}},original);
 await page.locator('#restoreProgressFile').setInputFiles({name:'progress.json',mimeType:'application/json',buffer:Buffer.from(JSON.stringify(payload))});
 await expect(page.locator('#backupProgressResult')).toContainText('Progres sebelumnya');await expect(page.locator('#storageStatus')).toContainText('sebagian');
 const recovered=await backup(page,'#backupSessionProgressBtn');expect(recovered.progress.done).toEqual(JSON.parse(original));await expect(page.locator('#nextAction')).toContainText('Pembayaran biaya EPS-TOPIK');
});
