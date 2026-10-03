const { test, expect } = require('@playwright/test');

async function freshPage(page) {
  const errors = [];
  page.on('pageerror', error => errors.push(error.message));

  await page.goto('/app.html', { waitUntil: 'domcontentloaded' });
  await page.waitForFunction(() => {
    const progress = document.querySelector('#progressText');
    return progress && /\/\s*27/.test(progress.textContent || '');
  }, null, { timeout: 15000 });

  await page.evaluate(() => {
    localStorage.clear();
    if (typeof refreshProgressViews === 'function') refreshProgressViews();
    if (typeof renderQuickStart === 'function') renderQuickStart();
  });

  await expect(page.locator('#quickStart')).toBeVisible({ timeout: 10000 });
  return errors;
}

async function setStage(page, stageId) {
  await page.evaluate((target) => {
    if (typeof applyCurrentStage !== 'function') throw new Error('applyCurrentStage unavailable');
    applyCurrentStage(target, true);
  }, stageId);
  await expect(page.locator('#nextAction')).toBeVisible({ timeout: 10000 });
}

test('first-time flow stays simple on desktop', async ({ page }) => {
  await page.setViewportSize({ width: 1280, height: 800 });
  const errors = await freshPage(page);

  await expect(page.locator('body')).toHaveClass(/setup-mode/);
  await expect(page.locator('.flow-dashboard')).toBeHidden();
  await expect(page.locator('.how-to-use')).toBeVisible();

  await page.locator('[data-quick-stage="eligibility"]').click();

  await expect(page.locator('#quickStart')).toBeHidden();
  await expect(page.locator('body')).not.toHaveClass(/setup-mode/);
  await expect(page.locator('.flow-dashboard')).toBeVisible();
  await expect(page.locator('#nextAction')).toBeVisible();
  await expect(page.locator('.micro-help')).toBeVisible();
  await expect(page.locator('.utility-nav')).toBeVisible();

  expect(errors).toEqual([]);
});

test('mobile flow has no horizontal overflow and keeps primary controls visible', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  const errors = await freshPage(page);

  await page.locator('[data-quick-stage="eligibility"]').click();
  await expect(page.locator('#nextAction')).toBeVisible();
  await expect(page.locator('.utility-nav')).toBeVisible();

  const overflow = await page.evaluate(() => ({
    scrollWidth: document.documentElement.scrollWidth,
    innerWidth: window.innerWidth
  }));
  expect(overflow.scrollWidth).toBeLessThanOrEqual(overflow.innerWidth + 1);

  await page.locator('.utility-tab[data-view="documents"]').click();
  await expect(page.locator('#documents')).toBeVisible();
  await expect(page.locator('#docStageContext')).toBeVisible();

  expect(errors).toEqual([]);
});

test('optional trust and backup controls stay out of the main flow', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  const errors = await freshPage(page);
  await page.locator('[data-quick-stage="eligibility"]').click();

  const trust = page.locator('.trust-panel');
  await expect(trust).toBeVisible();
  await expect(page.locator('#backupProgressBtn')).toBeHidden();

  await trust.locator('summary').click();
  await expect(page.locator('#backupProgressBtn')).toBeVisible();
  await expect(page.locator('#restoreProgressBtn')).toBeVisible();

  expect(errors).toEqual([]);
});

test('visa document helper shows one field at a time on mobile', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  const errors = await freshPage(page);
  await setStage(page, 'visa_docs');

  await page.locator('.utility-tab[data-view="documents"]').click();
  await expect(page.locator('#documents')).toBeVisible();
  await expect(page.locator('#docScopeWrap')).toBeVisible();
  await page.locator('#docScopeSelect').selectOption('visa_sep08_2026');

  await expect(page.locator('#formWizardSection')).toBeVisible({ timeout: 10000 });
  await expect(page.locator('#formWizardCard')).toBeVisible();
  await expect(page.locator('#formWizardLabel')).not.toHaveText('');
  await expect(page.locator('#formWizardInstruction')).not.toHaveText('');

  const before = await page.locator('#formWizardProgress').textContent();
  await page.locator('#formWizardNext').click();
  const after = await page.locator('#formWizardProgress').textContent();
  expect(after).not.toBe(before);

  const reviewState = await page.evaluate(() => ({
    reviewed: JSON.parse(localStorage.getItem('kep.formWizardReviewed') || '[]'),
    leakedValue: localStorage.getItem('formFieldValue')
  }));
  expect(reviewState.reviewed.length).toBeGreaterThan(0);
  expect(reviewState.leakedValue).toBeNull();

  const overflow = await page.evaluate(() => ({
    scrollWidth: document.documentElement.scrollWidth,
    innerWidth: window.innerWidth
  }));
  expect(overflow.scrollWidth).toBeLessThanOrEqual(overflow.innerWidth + 1);
  expect(errors).toEqual([]);
});

test('notice-specific answers stay hidden until the user selects the matching notice', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  const errors = await freshPage(page);
  await setStage(page, 'predeparture_training');

  const openStageButton = page.locator('#nextAction [data-stage="predeparture_training"]');
  await expect(openStageButton).toBeVisible();
  await openStageButton.click();

  await expect(page.locator('#stageDialog')).toBeVisible();
  await expect(page.locator('#scopePickerSection')).toBeVisible();

  const wave10Location='BBPPMPV Bisnis dan Pariwisata, Sawangan';
  await expect(page.locator('#exactAnswerList')).not.toContainText(wave10Location);
  await page.locator('#scopePicker').selectOption('opp_sawangan_wave10_2026');
  await expect(page.locator('#exactAnswerList')).toContainText(wave10Location);

  expect(errors).toEqual([]);
});

test('simple UX lock: first-time user can identify now, ask, and continue without opening extra panels', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  const errors = await freshPage(page);

  await expect(page.locator('.how-to-use')).toContainText('Ikuti “Langkah sekarang”');
  await expect(page.locator('.how-to-use')).toContainText('Kalau ragu sekecil apa pun, tanya');
  await expect(page.locator('.how-to-use')).toContainText('Selesai');

  await page.locator('[data-quick-stage="eligibility"]').click();

  await expect(page.locator('#nextAction')).toBeVisible();
  await expect(page.locator('#nextAction')).toContainText('LANGKAH BERIKUTNYA');
  await expect(page.locator('#brokerLikeQuestion')).toBeVisible();
  await expect(page.locator('#brokerLikeQuestionBtn')).toBeVisible();

  const primaryActions = await page.locator('#nextAction .primary:visible').count();
  expect(primaryActions).toBe(1);

  await expect(page.locator('.context-tools')).not.toHaveAttribute('open', '');
  await expect(page.locator('.trust-panel')).not.toHaveAttribute('open', '');

  expect(errors).toEqual([]);
});

test('form wizard exposes only one actionable field instruction at a time', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  const errors = await freshPage(page);
  await setStage(page, 'visa_docs');

  await page.locator('.utility-tab[data-view="documents"]').click();
  await page.locator('#docScopeSelect').selectOption('visa_sep08_2026');

  await expect(page.locator('#formWizardSection')).toBeVisible();
  await expect(page.locator('#formWizardCard')).toBeVisible();

  const visibleLabels = await page.locator('#formWizardCard #formWizardLabel:visible').count();
  const visibleInstructions = await page.locator('#formWizardCard #formWizardInstruction:visible').count();
  const visibleExamples = await page.locator('#formWizardCard #formWizardExample:visible').count();
  expect(visibleLabels).toBe(1);
  expect(visibleInstructions).toBe(1);
  expect(visibleExamples).toBe(1);

  const initialLabel = await page.locator('#formWizardLabel').textContent();
  await page.locator('#formWizardNext').click();
  const nextLabel = await page.locator('#formWizardLabel').textContent();
  expect(nextLabel).not.toBe(initialLabel);

  expect(errors).toEqual([]);
});


test('unknown broker-like question routes to official human help instead of guessing', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  const errors = await freshPage(page);
  await setStage(page, 'eligibility');

  await page.locator('#brokerLikeQuestion').fill('Apakah saya harus memilih tombol rahasia XYZ?');
  await page.locator('#brokerLikeQuestionBtn').click();

  const result = page.locator('#brokerLikeQuestionResult');
  await expect(result).toContainText('Belum ada jawaban resmi yang cukup spesifik');
  await expect(result.locator('.official-help-fallback')).toBeVisible();
  await expect(result.locator('.official-help-fallback')).toContainText('KP2MI');
  await expect(result.locator('.official-help-fallback')).toContainText('bukan calo');
  await expect(result.locator('.official-help-source').first()).toHaveAttribute('href', 'https://kp2mi.go.id/index.php/profil-kontak');

  expect(errors).toEqual([]);
});


test('beta feedback removes sensitive-looking identifiers before email draft', async ({ page }) => {
  const errors = await freshPage(page);
  const result = await page.evaluate(() => {
    const raw='Paspor A1234567; NIK 3174123456789012; email tester@example.com; HP +62 812-3456-7890';
    const sanitized=sanitizeBetaFeedback(raw);
    const mailBody=decodeURIComponent(encodeSanitizedBetaBody(raw));
    return {sanitized,mailBody};
  });

  expect(result.sanitized.redacted).toBe(true);
  expect(result.sanitized.text).not.toContain('A1234567');
  expect(result.sanitized.text).not.toContain('3174123456789012');
  expect(result.sanitized.text).not.toContain('tester@example.com');
  expect(result.sanitized.text).not.toContain('+62 812-3456-7890');
  expect(result.mailBody).toContain('Catatan privasi');
  expect(result.mailBody).toContain('[DIHAPUS:');
  expect(errors).toEqual([]);
});


test('beta feedback bundle combines all gap types and redacts them in one draft', async ({ page }) => {
  const errors = await freshPage(page);
  await setStage(page, 'eligibility');

  const result = await page.evaluate(() => {
    localStorage.setItem('kep.unresolvedFieldQuestions', JSON.stringify([
      {stageId:'registration', stageTitle:'Pendaftaran', question:'Konfirmasi ke tester@example.com'}
    ]));
    localStorage.setItem('kep.rejectionCases', JSON.stringify([
      {id:1, stageId:'visa_docs', stageTitle:'Visa', field:'Paspor A1234567', reason:'Hubungi +62 812-3456-7890', fix:'NIK 3174123456789012'}
    ]));
    localStorage.setItem('kep.brokerGaps', JSON.stringify([
      {id:2, stage:'eligibility', task:'Diminta bayar ke 081234567890', helper:'Calo / agen swasta'}
    ]));
    const bundle=buildBetaFeedbackBundle();
    const href=betaFeedbackBundleMailto(bundle);
    const body=decodeURIComponent(href.split('&body=')[1]);
    switchView('gaps', false);
    return {count:bundle.count, rawBody:bundle.rawBody, body};
  });

  expect(result.count).toBe(3);
  expect(result.rawBody).toContain('PERTANYAAN YANG BELUM TERVERIFIKASI');
  expect(result.rawBody).toContain('KASUS PENOLAKAN');
  expect(result.rawBody).toContain('CELAH CALO / PERANTARA');
  expect(result.body).toContain('Catatan privasi');
  expect(result.body).not.toContain('tester@example.com');
  expect(result.body).not.toContain('A1234567');
  expect(result.body).not.toContain('+62 812-3456-7890');
  expect(result.body).not.toContain('3174123456789012');
  expect(result.body).not.toContain('081234567890');
  await expect(page.locator('#emailAllBetaFeedbackBtn')).toBeVisible();
  expect(errors).toEqual([]);
});


test('beta feedback bundle includes anonymous progress context', async ({ page }) => {
  const errors = await freshPage(page);
  await setStage(page, 'registration');

  const body = await page.evaluate(() => {
    localStorage.setItem('kep.doneStages', JSON.stringify(['eligibility']));
    localStorage.setItem('kep.brokerGaps', JSON.stringify([
      {id:3, stage:'registration', task:'Masih bingung langkah berikutnya', helper:'Teman / pekerja senior'}
    ]));
    if (typeof refreshProgressViews === 'function') refreshProgressViews();
    return buildBetaFeedbackBundle().rawBody;
  });

  expect(body).toContain('RINGKASAN SESI TANPA IDENTITAS');
  expect(body).toContain('Tahap sekarang:');
  expect(body).toContain('Tahap selesai: 1/27');
  expect(body).toContain('1 Celah Calo');
  expect(errors).toEqual([]);
});


test('beta zero-broker checkpoint tracks stage pass and fail without identity data', async ({ page }) => {
  const errors = await freshPage(page);
  await setStage(page, 'eligibility');
  await page.evaluate(() => switchView('gaps', false));
  await page.locator('#betaValidationPanel summary').click();

  await page.locator('#betaCheckStage').selectOption('eligibility');
  await page.locator('#betaCheckOutcome').selectOption('no_private_help');
  await page.locator('#saveBetaCheckBtn').click();
  await page.locator('#betaCheckStage').selectOption('registration');
  await page.locator('#betaCheckOutcome').selectOption('private_help_needed');
  await page.locator('#saveBetaCheckBtn').click();

  const result = await page.evaluate(() => {
    const stats=betaValidationStats();
    const bundle=buildBetaFeedbackBundle();
    return {
      tested:stats.tested,
      passed:stats.passed,
      failed:stats.failed,
      routePass:stats.routePass,
      checkpointCount:bundle.checkpointCount,
      count:bundle.count,
      rawBody:bundle.rawBody,
      saved:JSON.parse(localStorage.getItem('kep.betaZeroBrokerChecks')||'{}')
    };
  });

  expect(result.tested).toBe(2);
  expect(result.passed).toBe(1);
  expect(result.failed).toBe(1);
  expect(result.routePass).toBe(false);
  expect(result.checkpointCount).toBe(2);
  expect(result.count).toBe(2);
  expect(Object.keys(result.saved)).toEqual(['eligibility','registration']);
  expect(result.rawBody).toContain('CHECKPOINT ZERO-BROKER');
  expect(result.rawBody).toContain('1 PASS');
  expect(result.rawBody).toContain('1 FAIL');
  await expect(page.locator('#betaValidationSummary')).toContainText('2/27');
  await expect(page.locator('#gapStage')).toHaveValue('registration');
  expect(errors).toEqual([]);
});


test('anonymous beta ID links feedback to tracker without identity data', async ({ page }) => {
  const errors = await freshPage(page);
  await setStage(page, 'eligibility');
  await page.evaluate(() => switchView('gaps', false));
  await page.locator('#betaValidationPanel').evaluate((el) => { el.open = true; });

  await page.locator('#betaTesterId').fill('kep-0042');
  await page.locator('#saveBetaTesterIdBtn').click();
  await expect(page.locator('#betaTesterId')).toHaveValue('KEP-0042');
  await expect(page.locator('#betaTesterIdStatus')).toContainText('KEP-0042');

  const result = await page.evaluate(() => {
    localStorage.setItem('kep.brokerGaps', JSON.stringify([
      {id:4, stage:'eligibility', task:'Masih membutuhkan bantuan', helper:'Teman / pekerja senior'}
    ]));
    const bundle=buildBetaFeedbackBundle();
    const href=betaFeedbackBundleMailto(bundle);
    return {
      testerId:bundle.testerId,
      body:bundle.rawBody,
      subject:decodeURIComponent(href.split('?subject=')[1].split('&body=')[0]),
      stored:JSON.parse(localStorage.getItem('kep.betaTesterId')||'null')
    };
  });

  expect(result.testerId).toBe('KEP-0042');
  expect(result.stored).toBe('KEP-0042');
  expect(result.body).toContain('ID beta anonim: KEP-0042');
  expect(result.subject).toContain('[KEP-0042]');
  expect(result.body).not.toContain('email');
  expect(errors).toEqual([]);
});
