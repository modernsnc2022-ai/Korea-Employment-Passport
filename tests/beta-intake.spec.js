const { test, expect } = require('@playwright/test');

async function betaPage(page, directEndpoint='') {
  await page.route('**/data/beta_program_v1.json', async route => {
    const response = await route.fetch();
    const program = await response.json();
    program.application.directIntake = {
      ...(program.application.directIntake || {}),
      endpoint: directEndpoint
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
      headers: { 'Access-Control-Allow-Origin': 'http://127.0.0.1:4173' },
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
  await page.locator('#betaApplicationSubmitBtn').click();

  await expect(page.locator('#applicationResult')).toContainText('KEP-I-TEST1234');
  expect(submitted).not.toBeNull();
  expect(submitted.kind).toBe('active_applicant');
  expect(submitted.contactEmail).toBe('tester@example.com');
  expect(submitted.sourceCode).toBe('website');
  expect(submitted.activeProcess).toBe(true);
  expect(submitted.feedbackAgreement).toBe(true);
});
