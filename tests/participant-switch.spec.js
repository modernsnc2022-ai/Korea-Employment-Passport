const {test,expect}=require('@playwright/test');
const data=require('../docs/data/id_e9_manufacturing_2026.json');
async function setup(page){
 await page.addInitScript(({done})=>{
  if(!sessionStorage.getItem('testSeeded')){
   for(const [id,company,gross]of [['KEP-0001','Company A','3000000'],['KEP-0002','Company B','4000000'],['','Unscoped company','5000000']]){
    const suffix=id?'.'+id:'';
    localStorage.setItem('kep.doneStages'+suffix,JSON.stringify(id==='KEP-0001'?done:[]));
    localStorage.setItem('kep.quickSetupDone'+suffix,'true');
    localStorage.setItem('kep.contract'+suffix,JSON.stringify({enterpriseName:company,monthlyWage:gross}));
    localStorage.setItem('kep.payroll'+suffix,JSON.stringify({payrollGross:gross}));
    localStorage.setItem('kep.workplace'+suffix,JSON.stringify({company,checks:[]}));
   }
   sessionStorage.setItem('testSeeded','true');
  }
 },{done:data.stages.slice(0,data.stages.findIndex(s=>s.id==='slc')).map(s=>s.id)});
 await page.goto('/app.html?beta=KEP-0001&stage=slc&src=regression');await page.locator('#nextAction').waitFor();
}
async function changeId(page,id){
 await page.locator('.utility-tab[data-view="gaps"]').click();await page.locator('#betaValidationPanel').evaluate(el=>el.open=true);await expect(page.locator('#betaTesterIdHint')).toBeVisible();await page.locator('#betaTesterId').fill(id);await page.locator('#saveBetaTesterIdBtn').click();
}
test('participant switch refreshes private fields, current stage and clears temporary content',async({page})=>{
 await setup(page);await page.evaluate(()=>switchView('contract',false));await page.locator('#checkContractBtn').click();await expect(page.locator('#contractResult')).toBeVisible();
 await page.evaluate(()=>{document.querySelector('#slcText').value='Private draft A';document.querySelector('#consNamePassport').value='Private name A';});
 await changeId(page,'KEP-0002');
 await expect(page.locator('#contract_enterpriseName')).toHaveValue('Company B');await expect(page.locator('#payrollGross')).toHaveValue('4000000');await expect(page.locator('#wpCompany')).toHaveValue('Company B');
 await expect(page.locator('#contractResult')).toBeHidden();await expect(page.locator('#slcText')).toHaveValue('');await expect(page.locator('#consNamePassport')).toHaveValue('');
 await page.locator('.utility-tab[data-view="journey"]').click();await expect(page.locator('#nextAction')).toContainText(/Cek kelayakan/i);
 expect(new URL(page.url()).searchParams.get('beta')).toBe('KEP-0002');expect(new URL(page.url()).searchParams.has('stage')).toBe(false);
 await page.reload();await expect(page.locator('#contract_enterpriseName')).toHaveValue('Company B');expect(new URL(page.url()).searchParams.get('src')).toBe('regression');
 const a=await page.evaluate(()=>JSON.parse(localStorage.getItem('kep.contract.KEP-0001')));expect(a.enterpriseName).toBe('Company A');
});
test('clearing a participant loads unscoped data and cannot be undone by the old URL',async({page})=>{
 await setup(page);await changeId(page,'');await expect(page.locator('#contract_enterpriseName')).toHaveValue('Unscoped company');
 expect(new URL(page.url()).searchParams.has('beta')).toBe(false);expect(new URL(page.url()).searchParams.has('stage')).toBe(false);
 await page.reload();await expect(page.locator('#contract_enterpriseName')).toHaveValue('Unscoped company');expect(await page.evaluate(()=>localStorage.getItem('kep.betaTesterId'))).toBe(null);
});
test('saving the same participant keeps their temporary question',async({page})=>{
 await setup(page);await page.locator('#brokerLikeQuestion').fill('Draft for the same participant');await changeId(page,'KEP-0001');
 await expect(page.locator('#brokerLikeQuestion')).toHaveValue('Draft for the same participant');
});
test('a fresh participant can keep editing their ID before declaring their own stage',async({page})=>{
 await setup(page);await page.evaluate(()=>localStorage.removeItem('kep.quickSetupDone.KEP-0002'));
 await changeId(page,'KEP-0002');await expect(page.locator('#betaTesterId')).toBeVisible();await expect(page.locator('#quickStart')).toBeHidden();expect(await page.evaluate(()=>localStorage.getItem('kep.quickSetupDone.KEP-0002'))).toBe(null);
 await page.locator('.utility-tab[data-view="journey"]').click();await expect(page.locator('#quickStart')).toBeVisible();await expect(page.locator('#nextAction')).toBeHidden();
 await expect(page.locator('[data-quick-stage="eligibility"]')).toBeFocused();
});
