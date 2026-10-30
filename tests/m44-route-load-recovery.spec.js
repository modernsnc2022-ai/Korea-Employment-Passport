const {test,expect} = require('@playwright/test');

// M44: mandatory country-pack data failures must never show incomplete
// applicant actions or infer official requirements.
test('M44 offline required route data fails closed with actionable Indonesian retry',async({page})=>{
  let attempts=0;
  await page.route('**/data/id_e9_manufacturing_2026.json',route=>{
    attempts+=1;
    return route.abort('failed');
  });
  await page.goto('/app.html',{waitUntil:'domcontentloaded'});
  await expect(page.locator('#routeLoadRecovery')).toBeVisible({timeout:15000});
  await expect(page.locator('body')).toHaveClass(/route-unavailable/);
  await expect(page.locator('#routeLoadRecovery')).toContainText('Periksa sambungan internet');
  await expect(page.locator('#routeLoadRecovery')).toContainText('Jangan menebak dokumen');
  await expect(page.locator('#retryRouteLoadBtn')).toBeEnabled();
  await expect(page.locator('#quickStart')).toBeHidden();
  await expect(page.locator('.utility-nav')).toBeHidden();
  await expect(page.locator('#nextAction')).toBeHidden();
  await expect(page.locator('#progressText')).toHaveText('0 / 0');
  expect(attempts).toBe(3);
});

test('M44 retry restores full 27-stage journey without changing local progress',async({page})=>{
  let fails=true,requests=0;
  await page.addInitScript(()=>{
    localStorage.setItem('kep.m44-preserve-progress-sentinel','untouched');
  });
  await page.route('**/data/id_e9_manufacturing_2026.json',route=>{
    requests+=1;
    return fails?route.abort('failed'):route.continue();
  });
  await page.goto('/app.html',{waitUntil:'domcontentloaded'});
  await expect(page.locator('#routeLoadRecovery')).toBeVisible({timeout:15000});
  fails=false;
  await page.locator('#retryRouteLoadBtn').click();
  await expect(page.locator('#progressText')).toContainText('/ 27',{timeout:15000});
  await expect(page.locator('#routeLoadRecovery')).toBeHidden();
  await expect(page.locator('body')).not.toHaveClass(/route-unavailable/);
  await expect(page.locator('#quickStart')).toBeVisible();
  await expect(page.locator('#freshnessStatus')).toBeHidden();
  await page.locator('[data-quick-stage="eligibility"]').click();
  await expect(page.locator('#nextAction')).toBeVisible();
  expect(await page.evaluate(()=>localStorage.getItem('kep.m44-preserve-progress-sentinel'))).toBe('untouched');
  expect(requests).toBe(4);
});

test('M44 repeated failed retry stays blocked and never claims loaded guidance',async({page})=>{
  let requests=0;
  await page.route('**/data/id_e9_manufacturing_2026.json',route=>{
    requests+=1;
    return route.abort('failed');
  });
  await page.goto('/app.html');
  await expect(page.locator('#routeLoadRecovery')).toBeVisible({timeout:15000});
  await page.locator('#retryRouteLoadBtn').click();
  await expect(page.locator('#routeLoadRecovery')).toBeVisible({timeout:15000});
  await expect(page.locator('#retryRouteLoadBtn')).toBeEnabled();
  await expect(page.locator('body')).toHaveClass(/route-unavailable/);
  await expect(page.locator('#quickStart')).toBeHidden();
  await expect(page.locator('#progressText')).toHaveText('0 / 0');
  expect(requests).toBe(6);
});
