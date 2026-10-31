const {test,expect}=require('@playwright/test');
const fs=require('fs');const path=require('path');
test('pre-device gate retains beta HOLD and source review lock',async({page})=>{
 const app=JSON.parse(fs.readFileSync(path.resolve(__dirname,'../docs/data/beta_program_v1.json'),'utf8'));
 const sources=JSON.parse(fs.readFileSync(path.resolve(__dirname,'../docs/data/source_review_status.json'),'utf8'));
 expect(app.status).toBe('hold');expect(sources.state).toBe('review_required');expect(sources.autoPublishRules).toBe(false);
 await page.goto('/app.html');await page.locator('#quickStart').waitFor();
 await expect(page.locator('.service-identity')).toContainText('bukan pemerintah');
 await expect(page.locator('#cycleStatus')).toContainText('ditutup');
});
for(const width of [320,390]) test('pre-device keyboard access and help disclosure at '+width,async({page})=>{
 await page.setViewportSize({width,height:780});await page.goto('/app.html');await page.locator('#quickStart').waitFor();
 await page.locator('[data-quick-stage="exam_fee"]').click();
 const toggle=page.locator('#toggleHomeHelpBtn');await expect(toggle).toHaveAttribute('aria-expanded','false');
 await toggle.focus();await page.keyboard.press('Enter');await expect(toggle).toHaveAttribute('aria-expanded','true');
 await expect(page.locator('#brokerLikeQuestion')).toBeFocused();
 await toggle.focus();await page.keyboard.press('Space');await expect(toggle).toHaveAttribute('aria-expanded','false');
 await expect(page.locator('#homeHelpContent')).toBeHidden();
 expect(await page.evaluate(()=>document.documentElement.scrollWidth)).toBeLessThanOrEqual(width);
});
