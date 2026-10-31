const {test,expect}=require('@playwright/test');
test('home optional help toggles without affecting stage action',async({page})=>{
 await page.setViewportSize({width:390,height:844});await page.goto('/app.html');await page.locator('#quickStart').waitFor();
 await page.locator('[data-quick-stage="exam_fee"]').click();
 const trigger=page.locator('#toggleHomeHelpBtn');const body=page.locator('#homeHelpContent');
 await expect(trigger).toHaveAttribute('aria-expanded','false');await expect(body).toBeHidden();
 await trigger.click();await expect(body).toBeVisible();await expect(trigger).toHaveAttribute('aria-expanded','true');await expect(page.locator('#brokerLikeQuestion')).toBeFocused();
 await trigger.click();await expect(body).toBeHidden();await expect(trigger).toHaveAttribute('aria-expanded','false');
 await expect(page.locator('#nextAction .primary')).toBeVisible();
});
