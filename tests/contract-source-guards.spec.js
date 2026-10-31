const {test,expect}=require('@playwright/test');
async function prepare(page,state){
 await page.route('**/data/source_review_status.json',async route=>{
  const response=await route.fetch();
  await route.fulfill({response,json:state==='clean'?{state:'clean',reviewRequiredUrls:[],fetchFailureUrls:[]}:{state:'fetch_warning',fetchFailureUrls:['source_review_status'],reviewRequiredUrls:[]}});
 });
 await page.goto('/app.html');await page.locator('#quickStart').waitFor();
 await page.locator('[data-quick-stage="eligibility"]').click();
}
test('unconfirmed sources block eligibility and wage claims while keeping arithmetic available',async({page})=>{
 await prepare(page,'unknown');
 await page.locator('#nextAction .primary').click();await page.locator('#elig_birthdate').fill('1995-01-01');await page.locator('#eligibilityForm input[type=number]').fill('0');
 const choices=page.locator('#eligibilityForm select');for(let i=0;i<await choices.count();i++)await choices.nth(i).selectOption('yes');
 await page.locator('#checkEligibilityBtn').click();await expect(page.locator('#eligibilityResult')).toContainText('Belum dapat menilai kelayakan');
 await page.evaluate(()=>switchView('contract',false));
 await page.locator('#contract_monthlyWage').fill('1000000');await page.locator('#checkContractBtn').click();
 await expect(page.locator('#contractResult')).toContainText('Perbandingan upah minimum ditahan');
 await expect(page.locator('#contractResult')).not.toContainText('2.156.880');
 await expect(page.locator('#contractNotes')).toContainText('perlu pemeriksaan ulang');
 await page.evaluate(()=>switchView('payroll',false));
 await page.locator('#payrollGross').fill('2000000');await page.locator('#payrollDeposit').fill('1800000');
 await page.locator('#payrollDeductions').fill('200000');await page.locator('#payrollHours').fill('209');await page.locator('#payrollMinimumBase').fill('2000000');
 await page.locator('#checkPayrollBtn').click();
 await expect(page.locator('#payrollResult')).toContainText('konsisten secara aritmetika');
 await expect(page.locator('#payrollResult')).toContainText('Perbandingan upah minimum ditahan');
 await expect(page.locator('#payrollResult')).not.toContainText('10.320');
 await expect(page.locator('#payrollResult')).not.toHaveClass(/safe/);
});
test('a clean source fixture preserves the existing threshold comparison',async({page})=>{
 await prepare(page,'clean');await page.evaluate(()=>switchView('contract',false));
 await page.locator('#contract_monthlyWage').fill('1000000');await page.locator('#checkContractBtn').click();
 await expect(page.locator('#contractResult')).toContainText('di bawah acuan minimum 2026');
 await page.locator('#contract_monthlyWage').fill('3000000');
 await expect(page.locator('#contractResult')).toBeHidden();
});
test('contract reset removes only the active beta participant data',async({page})=>{
 await page.goto('/app.html?beta=KEP-0001&stage=slc');await page.locator('#nextAction').waitFor();
 await page.evaluate(()=>{
  write(KEYS.contract,{enterpriseName:'Dummy one'});
  localStorage.setItem(KEYS.contract+'.KEP-0002',JSON.stringify({enterpriseName:'Dummy two'}));
  localStorage.setItem(KEYS.contract,JSON.stringify({enterpriseName:'Unscoped'}));
  renderContract();switchView('contract',false);
 });
 await page.locator('#resetContractBtn').click();
 const stored=await page.evaluate(()=>({own:read(KEYS.contract,null),other:JSON.parse(localStorage.getItem(KEYS.contract+'.KEP-0002')),unscoped:JSON.parse(localStorage.getItem(KEYS.contract))}));
 expect(stored).toEqual({own:null,other:{enterpriseName:'Dummy two'},unscoped:{enterpriseName:'Unscoped'}});
 await expect(page.locator('#contract_enterpriseName')).toHaveValue('');
});

test('disconnect invalidates an old payment result without clearing entered values',async({page,context})=>{
 await prepare(page,'clean');await page.evaluate(()=>switchView('fees',false));
 await page.locator('#feeAmount').fill('472161');await page.locator('#feePayee').selectOption('bank');
 await page.locator('#checkFeeBtn').click();await expect(page.locator('#feeResult')).toHaveClass(/safe/);
 await page.locator('#feeAmount').fill('472162');await expect(page.locator('#feeResult')).toBeHidden();
 await page.locator('#feeAmount').fill('472161');await page.locator('#checkFeeBtn').click();
 await context.setOffline(true);await expect(page.locator('#feeResult')).toBeHidden();
 await expect(page.locator('#feeAmount')).toHaveValue('472161');
 await page.locator('#checkFeeBtn').click();
 await expect(page.locator('#feeResult')).toContainText('Biaya belum dapat dikonfirmasi');
 await expect(page.locator('#feeResult')).not.toHaveClass(/safe/);
});

test('changing the selected stage hides the old answer without deleting the question',async({page})=>{
 await prepare(page,'clean');
 await page.locator('#toggleHomeHelpBtn').click();await page.locator('#brokerLikeQuestion').fill('Apakah tombol XYZ harus dipilih?');await page.locator('#brokerLikeQuestionBtn').click();
 await expect(page.locator('#brokerLikeQuestionResult')).toBeVisible();
 await page.evaluate(()=>applyCurrentStage('exam_fee',true));
 await expect(page.locator('#brokerLikeQuestionResult')).toBeHidden();
 await expect(page.locator('#brokerLikeQuestion')).toHaveValue('Apakah tombol XYZ harus dipilih?');
});
