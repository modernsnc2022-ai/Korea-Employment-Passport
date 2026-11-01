const { test, expect } = require('@playwright/test');
test('account deployment gate preserves free use and 4 navigation tabs', async ({page}) => {
  await page.goto('/app.html');
  await expect(page.locator('#accountOpenBtn')).toBeHidden();
  await expect(page.locator('.utility-tab')).toHaveCount(4);
  await page.locator('[data-quick-stage="eligibility"]').click();
  await page.locator('.utility-tab[data-view="gaps"]').click();
  await expect(page.locator('#routeTitle')).toHaveText('Bantuan');
});
test('account UI email signup, login, sync and logout with mocked Google Cloud SDK', async ({page}) => {
  await page.route('**/account-config.js', r=>r.fulfill({contentType:'application/javascript',body:`window.KEP_ACCOUNT_CONFIG={provider:'firebase',projectId:'kep-staging',authDomain:'kep-staging.firebaseapp.com',apiKey:'AIza${'x'.repeat(35)}',appId:'1:123:web:abcdef'};`}));
  await page.route('https://www.gstatic.com/firebasejs/12.4.0/**', async r=>{
    const file=r.request().url().split('/').pop();
    const fake={
      'firebase-app.js':`export function initializeApp(){return {}}`,
      'firebase-auth.js':`export function getAuth(){return {}};
         export function onAuthStateChanged(a,callback){callback(null)};
         export async function createUserWithEmailAndPassword(a,e,p){return {user:{uid:'demo',email:e,emailVerified:false}}};
         export async function sendEmailVerification(){};
         export async function signOut(){};
         export async function signInWithEmailAndPassword(a,e,p){return {user:{uid:'demo',email:e,emailVerified:true}}};
         export async function reload(){};
         export async function sendPasswordResetEmail(){};`,
      'firebase-firestore.js':`export function getFirestore(){return {}};
         export function doc(db,c,id){return {id}};
         export function serverTimestamp(){return '2026-11-01T00:00:00.000Z'};
         export async function setDoc(){};
         export async function getDoc(){return {exists:()=>true,data:()=>({payload:{}})}};
         export async function deleteDoc(){};`
    };
    await r.fulfill({contentType:'application/javascript',headers:{'access-control-allow-origin':'*'},body:fake[file]||''});
  });
  await page.goto('/app.html');
  await expect(page.locator('#accountOpenBtn')).toBeVisible({timeout:12000});
  await page.locator('[data-quick-stage="eligibility"]').click();
  await page.locator('#accountOpenBtn').click();
  await page.locator('[data-account-mode="signup"]').click();
  await page.locator('#accountEmail').fill('demo@example.org');
  await page.locator('#accountPassword').fill('demo-long-passphrase!');
  await page.locator('#accountPrivacyConsent').check();
  await page.locator('#accountSubmit').click();
  await expect(page.locator('#accountStatus')).toContainText('verifikasi');
  await page.locator('#accountPassword').fill('demo-long-passphrase!');
  await page.locator('#accountSubmit').click();
  await expect(page.locator('#accountSignedIn')).toBeVisible();
  await page.locator('#accountSaveBtn').click();
  await expect(page.locator('#accountStatus')).toContainText('tersimpan');
  await page.locator('#accountLogoutBtn').click();
  await expect(page.locator('#accountForm')).toBeVisible();
});
