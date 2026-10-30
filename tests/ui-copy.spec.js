const {test,expect}=require('@playwright/test');

test('Indonesian fee and authority presentation preserves original source facts and matching behavior',async({page})=>{
 await page.route('**/data/source_review_status.json',async route=>{
  const response=await route.fetch();await route.fulfill({response,json:{state:'clean',reviewRequiredUrls:[],fetchFailureUrls:[]}});
 });
 await page.goto('/app.html');await page.locator('#quickStart').waitFor();
 await page.locator('[data-quick-stage="exam_fee"]').click();
 await page.locator('#nextAction [data-stage="exam_fee"]').click();
 await expect(page.locator('#stageAuthority')).toHaveText('KP2MI / bank yang ditunjuk');
 await page.locator('#stageDialog .close').click();await page.waitForFunction(()=>!history.state?.kepStageDialog);
 await page.locator('.utility-tab[data-view="fees"]').click();
 await expect(page.locator('#knownCostList')).toContainText('Biaya pendaftaran ujian EPS-TOPIK');
 await page.locator('#feeAmount').fill('472161');await page.locator('#feePayee').selectOption('bank');
 await page.locator('#checkFeeBtn').click();
 await expect(page.locator('#feeResult')).toContainText('Bank BNI melalui kode pembayaran resmi');
 const source=await page.evaluate(()=>({authority:route.stages.find(s=>s.id==='exam_fee').authority,purpose:rules.fees.find(f=>f.id==='epsTopik').purpose,amount:rules.fees.find(f=>f.id==='epsTopik').amountIdr}));
 expect(source).toEqual({authority:'KP2MI / designated bank',purpose:'EPS-TOPIK registration exam fee',amount:472161});
});
