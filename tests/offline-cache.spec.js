const {test,expect}=require('@playwright/test');

test('real service worker preserves other apps, caches current styling and discloses offline guidance',async({browser})=>{
 const context=await browser.newContext({serviceWorkers:'allow'});
 const page=await context.newPage();
 try{
  await page.goto('/privacy.html');
  await page.evaluate(async()=>{
   const other=await caches.open('other-app-cache');await other.put('/unrelated',new Response('keep'));
   await caches.open('kep-v144');
  });
  await page.goto('/app.html');await page.locator('#quickStart').waitFor();
  await page.evaluate(()=>navigator.serviceWorker.ready);
  await page.reload();await page.waitForFunction(()=>Boolean(navigator.serviceWorker.controller));
  const keys=await page.evaluate(()=>caches.keys());
  expect(keys).toContain('other-app-cache');expect(keys).toContain('kep-v152-account-delete-safe-20261101');expect(keys).not.toContain('kep-v144');
  expect(await page.evaluate(async()=>Boolean(await caches.match(new URL('styles.css',location.href).href)))).toBe(true);
  await page.locator('[data-quick-stage="exam_fee"]').click();
  const saved=await page.evaluate(()=>localStorage.getItem('kep.doneStages'));
  await context.setOffline(true);await page.reload();
  for(const name of ['icon-192.png','icon-512.png','maskable-512.png','apple-touch-180.png'])expect(await page.evaluate(async name=>(await fetch('./icons/'+name)).ok,name)).toBe(true);
  await expect(page.locator('#nextAction')).toBeVisible();
  await expect(page.locator('#offlineStatus')).toBeVisible();
  await expect(page.locator('#offlineStatus')).toContainText('sebelum mengirim dokumen atau membayar');
  expect(await page.evaluate(()=>localStorage.getItem('kep.doneStages'))).toBe(saved);
  expect(await page.evaluate(async()=>{try{await fetch('/not-a-core-asset.json');return 'unexpected-response';}catch{return 'network-error';}})).toBe('network-error');
  // Inject the worker-side network failure as well: browser offline emulation
  // alone does not prove that the worker cannot obtain a network response.
  const worker=context.serviceWorkers().find(w=>w.url().endsWith('/sw.js'));
  await worker.evaluate(()=>{self.kepOriginalFetch=self.fetch;self.fetch=()=>Promise.reject(new TypeError('test network loss'));});
  const deleted=await page.evaluate(async()=>{const c=await caches.open('kep-v152-account-delete-safe-20261101');return await c.delete(new URL('data/id_e9_manufacturing_2026.json',location.href).href);});
  expect(deleted).toBe(true);
  await page.reload();await expect(page.locator('#routeLoadRecovery')).toBeVisible();
  await expect(page.locator('#nextAction')).toBeHidden();
  await worker.evaluate(()=>{self.fetch=self.kepOriginalFetch;delete self.kepOriginalFetch;});
  await context.setOffline(false);await expect(page.locator('#offlineStatus')).toBeHidden();
  await page.locator('#retryRouteLoadBtn').click();await expect(page.locator('#nextAction')).toBeVisible();
  expect(await page.evaluate(()=>localStorage.getItem('kep.doneStages'))).toBe(saved);
 }finally{await context.close();}
});
