const { test, expect } = require('@playwright/test');
test('account deployment gate preserves free use and 4 navigation tabs', async ({page}) => {
  await page.goto('/app.html');
  await expect(page.locator('#accountOpenBtn')).toBeHidden();
  await expect(page.locator('.utility-tab')).toHaveCount(4);
  await page.locator('[data-quick-stage="eligibility"]').click();
  await page.locator('.utility-tab[data-view="gaps"]').click();
  await expect(page.locator('#routeTitle')).toHaveText('Bantuan');
});
test('account UI login and progress save with mock backend', async ({page}) => {
  await page.route('**/account-config.js', r=>r.fulfill({contentType:'text/javascript',body:`window.KEP_ACCOUNT_CONFIG={url:'https://demo.supabase.co',publishableKey:'sb_publishable_test'};`}));
  await page.route('https://esm.sh/**', r=>r.fulfill({contentType:'text/javascript',headers:{'access-control-allow-origin':'*'},body:`
export function createClient(){let user=null;return {auth:{getSession:async()=>({data:{session:null}}),getUser:async()=>({data:{user}}),signInWithPassword:async()=>{user={id:'demo-user',email:'demo@example.org'};return {error:null}},onAuthStateChange:()=>({}),signOut:async()=>({error:null})},from:()=>({upsert:async()=>({error:null})})}}
`}));
  await page.goto('/app.html');
  await expect(page.locator('#accountOpenBtn')).toBeVisible({timeout:12000});
  await page.locator('[data-quick-stage="eligibility"]').click();
  await page.locator('#accountOpenBtn').click();
  await page.locator('#accountEmail').fill('demo@example.org');
  await page.locator('#accountPassword').fill('demo-long-passphrase');
  await page.locator('#accountSubmit').click();
  await expect(page.locator('#accountSignedIn')).toBeVisible();
  await page.locator('#accountSaveBtn').click();
  await expect(page.locator('#accountStatus')).toContainText('berhasil disimpan');
});
