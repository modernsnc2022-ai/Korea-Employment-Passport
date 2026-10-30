const {test,expect}=require('@playwright/test');
test('enlarged mobile navigation keeps complete words and clears the final action',async({page})=>{
 await page.setViewportSize({width:320,height:568});await page.goto('/app.html');await page.locator('#quickStart').waitFor();await page.locator('[data-quick-stage="exam_fee"]').click();
 await page.evaluate(()=>document.documentElement.style.fontSize='200%');
 const tabs=page.locator('.utility-tab');
 await expect.poll(async()=>{const a=await tabs.nth(0).boundingBox(),b=await tabs.nth(2).boundingBox();return b.y>a.y;}).toBe(true);
 for(const tab of await tabs.all())expect(await tab.evaluate(el=>el.scrollWidth<=el.clientWidth)).toBe(true);
 await page.locator('.utility-tab[data-view="documents"]').click();
 const action=page.locator('#documents button:visible').last();await action.scrollIntoViewIfNeeded();
 expect((await action.boundingBox()).y+(await action.boundingBox()).height).toBeLessThan((await page.locator('.utility-nav').boundingBox()).y);
});
test('incomplete contract fields are grouped while source warnings stay visible',async({page})=>{
 await page.setViewportSize({width:390,height:844});await page.goto('/app.html');await page.locator('#quickStart').waitFor();await page.locator('[data-quick-stage="exam_fee"]').click();await page.evaluate(()=>switchView('contract',false));
 await page.locator('#checkContractBtn').click();
 const out=page.locator('#contractResult');await expect(out).toContainText('kolom wajib belum diisi');await expect(out).toContainText('Perbandingan upah minimum ditahan');
 await expect(out.locator('details')).not.toHaveAttribute('open','');await expect(out.locator('.contract-flag')).not.toContainText(['Belum diisi']);
 await out.locator('summary').click();await expect(out.locator('details li').first()).toContainText('Nama perusahaan');
 await page.locator('#completeContractFields').click();await expect(page.locator('#contract_enterpriseName')).toBeFocused();
});
