const {test,expect}=require('@playwright/test');
const fs=require('fs');const path=require('path');
for(const width of [320,390,768]) test('visual audit '+width,async({page})=>{
 await page.setViewportSize({width,height:844});await page.goto('/app.html');
 await page.locator('#quickStart').waitFor();await page.locator('[data-quick-stage="exam_fee"]').click();
 const output=path.join('test-results','k eps'.replace(' ',''));fs.mkdirSync(output,{recursive:true});
 await page.screenshot({path:path.join(output,'home-'+width+'.png'),fullPage:true});
 const nav=page.locator('.utility-nav');const cta=page.locator('#nextAction .primary');
 const info=await page.evaluate(()=>({viewport:innerWidth,scrollWidth:document.documentElement.scrollWidth,visiblePanels:[...document.querySelectorAll('.flow-dashboard > *,#journey,.how-to-use,.trust-panel')].filter(e=>e.getClientRects().length).map(e=>({id:e.id||e.className,top:Math.round(e.getBoundingClientRect().top)}))}));
 console.log('VISUAL_AUDIT '+JSON.stringify(info));expect(info.scrollWidth).toBeLessThanOrEqual(width);
 await expect(cta).toBeVisible();await expect(nav).toBeVisible();
 await page.locator('.utility-tab[data-view="gaps"]').click();await page.screenshot({path:path.join(output,'help-'+width+'.png'),fullPage:true});
});
