const {test,expect}=require('@playwright/test');
test('install identity retains its URL and supplies correctly sized platform icons',async({page,request})=>{
 await page.goto('/app.html');await page.locator('#quickStart').waitFor();
 const manifest=await(await request.get('/manifest.webmanifest')).json();
 expect(manifest.start_url).toBe('./app.html');expect(manifest.scope).toBe('./');
 expect(manifest.theme_color).toBe(await page.locator('meta[name="theme-color"]').getAttribute('content'));
 for(const [src,n,purpose]of [['icons/icon-192.png',192,'any'],['icons/icon-512.png',512,'any'],['icons/maskable-512.png',512,'maskable']]){
  expect(manifest.icons).toContainEqual({src,sizes:`${n}x${n}`,type:'image/png',purpose});
  const r=await request.get('/'+src);expect(r.ok()).toBe(true);expect(r.headers()['content-type']).toContain('image/png');const b=await r.body();expect(b.subarray(0,8).toString('hex')).toBe('89504e470d0a1a0a');expect(b.readUInt32BE(16)).toBe(n);expect(b.readUInt32BE(20)).toBe(n);
 }
 const apple=page.locator('link[rel="apple-touch-icon"]');expect(await apple.getAttribute('sizes')).toBe('180x180');
 const b=await(await request.get('/'+await apple.getAttribute('href'))).body();expect(b.readUInt32BE(16)).toBe(180);expect(b.readUInt32BE(20)).toBe(180);
});
