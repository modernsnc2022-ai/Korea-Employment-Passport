const { test, expect } = require('@playwright/test');

async function betaPage(page, directEndpoint='', captchaReady=true) {
  // No third-party network or real Turnstile token in browser QA.
  await page.addInitScript((ready)=>{
    let options=null;
    window.turnstile={
      render:(_mount,config)=>{
        options=config;
        if(ready)Promise.resolve().then(()=>config.callback('synthetic-cloudflare-token'));
        return 'mock-widget';
      },
      reset:()=>{
        if(ready&&options)Promise.resolve().then(()=>options.callback('synthetic-cloudflare-token'));
      }
    };
  },captchaReady);
  await page.route('https://intake.example.test/v1/beta/applicant/verify-request',async route=>{
    await route.fulfill({
      status:202,contentType:'application/json',
      headers:{'Access-Control-Allow-Origin':new URL(page.url()).origin},
      body:JSON.stringify({ok:true,verificationRequired:true,expiresMinutes:10})
    });
  });
  await page.route('**/data/beta_program_v1.json', async route => {
    const response = await route.fetch();
    const program = await response.json();
    program.application.directIntake = {
      ...(program.application.directIntake || {}),
      endpoint: directEndpoint,
      turnstileSiteKey: directEndpoint ? 'test-site-key' : ''
    };
    await route.fulfill({ response, json: program });
  });
  await page.goto('/beta.html?src=website', { waitUntil: 'domcontentloaded' });
  await expect(page.locator('#applicationPanel')).toBeVisible({ timeout: 10000 });
}

test('beta applicant intake keeps email fallback while direct endpoint is unconfigured', async ({ page }) => {
  await betaPage(page, '');
  await expect(page.locator('#directIntakeFields')).toBeHidden();
  await expect(page.locator('#betaApplicationSubmitBtn')).toHaveText('Kirim lewat aplikasi email');
});

test('beta applicant intake can submit directly without opening an email client', async ({ page }) => {
  let submitted = null;
  await page.route('https://intake.example.test/v1/beta/applicant', async route => {
    submitted = route.request().postDataJSON();
    await route.fulfill({
      status: 201,
      contentType: 'application/json',
      headers: { 'Access-Control-Allow-Origin': new URL(page.url()).origin },
      body: JSON.stringify({ ok: true, submissionId: 'KEP-I-TEST1234' })
    });
  });

  await betaPage(page, 'https://intake.example.test/v1/beta/applicant');
  await expect(page.locator('#directIntakeFields')).toBeVisible();
  await expect(page.locator('#betaApplicationSubmitBtn')).toHaveText('Kirim pendaftaran');

  await page.locator('#applicantStage').selectOption({ index: 1 });
  await page.locator('#applicantCycle').selectOption({ index: 1 });
  await page.locator('#activeProcess').check();
  await page.locator('#feedbackAgreement').check();
  await page.locator('#applicantContactEmail').fill('tester@example.com');
  await requestAndFillCode(page);

  await expect(page.locator('#applicationResult')).toContainText('KEP-I-TEST1234');
  expect(submitted).not.toBeNull();
  expect(submitted.kind).toBe('active_applicant');
  expect(submitted.contactEmail).toBe('tester@example.com');
  expect(submitted.sourceCode).toBe('website');
  expect(submitted.activeProcess).toBe(true);
  expect(submitted.feedbackAgreement).toBe(true);
});

async function requestAndFillCode(page){
  await page.locator('#betaApplicationSubmitBtn').click();
  await expect(page.locator('#applicantEmailCodeFields')).toBeVisible();
  await expect(page.locator('#applicationResult')).toContainText('Belum ada pendaftaran yang diterima');
  await page.locator('#applicantEmailCode').fill('12345678');
  await page.locator('#betaApplicationSubmitBtn').click();
}

async function fillApplicant(page) {
  await page.locator('#applicantStage').selectOption({ index: 1 });
  await page.locator('#applicantCycle').selectOption({ index: 1 });
  await page.locator('#activeProcess').check();
  await page.locator('#feedbackAgreement').check();
  await page.locator('#applicantContactEmail').fill('tester@example.com');
}

for (const scenario of [
  {
    label: 'HTTP 200 with negative application acknowledgement',
    status: 200, body: {ok:false, submissionId:'KEP-I-TEST1234'}
  },
  {
    label: 'HTTP 200 with no submission reference',
    status: 200, body: {ok:true}
  },
  {
    label: 'HTTP 201 with untrusted submission reference',
    status: 201, body: {ok:true, submissionId:'<script>alert(1)</script>'}
  },
  {
    label: 'HTTP 503 intake server error',
    status: 503, body: {ok:false, error:'Unavailable'}
  }
]) {
  test('beta intake never displays a false receipt: '+scenario.label, async ({page}) => {
    let calls=0;
    await page.route('https://intake.example.test/v1/beta/applicant', async route=>{
      calls++;
      await route.fulfill({
        status:scenario.status,
        contentType:'application/json',
        headers:{'Access-Control-Allow-Origin':new URL(page.url()).origin},
        body:JSON.stringify(scenario.body)
      });
    });
    await betaPage(page,'https://intake.example.test/v1/beta/applicant');
    await fillApplicant(page);
    await requestAndFillCode(page);
    await expect(page.locator('#applicationResult')).toContainText('Data belum dianggap terkirim');
    await expect(page.locator('#applicationResult')).not.toContainText('Pendaftaran diterima langsung');
    await expect(page.locator('#applicantContactEmail')).toHaveValue('tester@example.com');
    await expect(page.locator('#applicantStage')).not.toHaveValue('');
    await expect(page.locator('#betaApplicationSubmitBtn')).toBeEnabled();
    expect(calls).toBe(1);
  });
}

test('beta email-only fallback identifies mailto composer as NOT a sent application',async({page})=>{
  await betaPage(page,'');
  await page.locator('#applicantStage').selectOption({index:1});
  await page.locator('#applicantCycle').selectOption({index:1});
  await page.locator('#activeProcess').check();
  await page.locator('#feedbackAgreement').check();
  await page.locator('#betaApplicationSubmitBtn').click({noWaitAfter:true});
  await expect(page.locator('#applicationResult')).toContainText('BELUM terkirim');
  await expect(page.locator('#applicationResult')).toContainText('folder Terkirim');
});

test('beta Gmail compose is NOT reported as successful application submission',async({page})=>{
  await betaPage(page,'');
  await page.locator('#applicantStage').selectOption({index:1});
  await page.locator('#applicantCycle').selectOption({index:1});
  await page.locator('#activeProcess').check();
  await page.locator('#feedbackAgreement').check();
  await page.evaluate(()=>{window.open=()=>({closed:false});});
  await page.locator('#gmailApplicationBtn').click();
  await expect(page.locator('#applicationResult')).toContainText('BELUM terkirim');
  await expect(page.locator('#applicationResult')).toContainText('Tekan Kirim');
});

test('direct intake is gated by a real Turnstile challenge before POST', async({page})=>{
  let calls=0;
  await page.route('https://intake.example.test/v1/beta/applicant', async route=>{
    calls++;await route.fulfill({status:201,contentType:'application/json',
      headers:{'Access-Control-Allow-Origin':new URL(page.url()).origin},
      body:JSON.stringify({ok:true,submissionId:'KEP-I-TEST-DIRECT'})});
  });
  await betaPage(page,'https://intake.example.test/v1/beta/applicant',false);
  await expect(page.locator('#directIntakeChallenge')).toBeVisible();
  await fillApplicant(page);
  await page.locator('#betaApplicationSubmitBtn').click();
  await expect(page.locator('#applicationResult')).toContainText('Selesaikan verifikasi keamanan');
  expect(calls).toBe(0);
});

test('unconfigured HTTPS endpoint remains email-only fallback and never loads Turnstile',async({page})=>{
  await page.addInitScript(()=>{window.__turnstileRequests=0;});
  await betaPage(page,'');
  await expect(page.locator('#directIntakeChallenge')).toBeHidden();
  await expect(page.locator('#directIntakeFields')).toBeHidden();
  await expect(page.locator('#betaApplicationSubmitBtn')).toContainText('aplikasi email');
  expect(await page.evaluate(()=>document.querySelectorAll('script[src*="turnstile"]').length)).toBe(0);
});

test('direct applicant cannot receive a receipt with no email ownership code',async({page})=>{
  let finalCalls=0;
  await page.route('https://intake.example.test/v1/beta/applicant',async route=>{
    finalCalls++;
    await route.fulfill({status:403,contentType:'application/json',
      body:JSON.stringify({ok:false,error:'email_verification_required'})});
  });
  await betaPage(page,'https://intake.example.test/v1/beta/applicant');
  await fillApplicant(page);
  await page.locator('#betaApplicationSubmitBtn').click();
  await expect(page.locator('#applicantEmailCodeFields')).toBeVisible();
  expect(finalCalls).toBe(0);
  await page.locator('#applicantEmailCode').fill('00000000');
  await page.locator('#betaApplicationSubmitBtn').click();
  await expect(page.locator('#applicationResult')).toContainText('Data belum dianggap terkirim');
  await expect(page.locator('#applicationResult')).not.toContainText('Pendaftaran diterima langsung');
  expect(finalCalls).toBe(1);
});

test('changing the applicant email address invalidates pending verification code',async({page})=>{
  await betaPage(page,'https://intake.example.test/v1/beta/applicant');
  await fillApplicant(page);
  await page.locator('#betaApplicationSubmitBtn').click();
  await expect(page.locator('#applicantEmailCodeFields')).toBeVisible();
  await page.locator('#applicantEmailCode').fill('12345678');
  await page.locator('#applicantContactEmail').fill('second@example.com');
  await expect(page.locator('#applicantEmailCodeFields')).toBeHidden();
  await expect(page.locator('#applicantEmailCode')).toHaveValue('');
  await expect(page.locator('#betaApplicationSubmitBtn')).toHaveText('Kirim pendaftaran');
});
