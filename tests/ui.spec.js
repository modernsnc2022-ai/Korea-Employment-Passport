const { test, expect } = require('@playwright/test');

async function freshPage(page, options = {}) {
  const errors = [];
  page.on('pageerror', error => errors.push(error.message));

  const sourceState = options.sourceState || 'clean';
  await page.route('**/data/source_review_status.json', async route => {
    const response = await route.fetch();
    const status = await response.json();
    if (sourceState === 'clean') {
      status.state = 'clean';
      status.reviewRequiredUrls = [];
      status.reviewRequiredSourceIds = [];
      status.fetchFailureUrls = [];
      status.fetchFailureSourceIds = [];
      status.message = 'Test fixture: no unreviewed official-source changes.';
    } else if (sourceState === 'review_required') {
      status.state = 'review_required';
      status.reviewRequiredUrls = [
        'https://www.kp2mi.go.id/gtog-detail/korea/pengumuman-ketentuan-pelaksanaan-pemeriksaan-psikologi-bagi-calon-pekerja-migran-indonesia-program-g-to-g-ke-korea-selatan-kelulusan-sebelum-tahun-2026-dan-kelulusan-tahun-2026'
      ];
      status.reviewRequiredSourceIds = ['kp2mi_psychology_2026'];
      status.fetchFailureUrls = [];
      status.fetchFailureSourceIds = [];
      status.message = 'Test fixture: official source review required.';
    }
    await route.fulfill({ response, json: status });
  });

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
  await expect(page.locator('#copyAllBetaFeedbackBtn')).toBeVisible();
  await expect(page.locator('#emailAllBetaFeedbackBtn')).toBeVisible();
  const shareText = await page.evaluate(() => sanitizedBetaFeedbackText(buildBetaFeedbackBundle().rawBody));
  expect(shareText).toContain('Catatan privasi');
  expect(shareText).toContain('nama, alamat');
  expect(shareText).not.toContain('tester@example.com');
  expect(shareText).not.toContain('A1234567');
  expect(shareText).not.toContain('+62 812-3456-7890');
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

  expect(body).toContain('RINGKASAN SESI — PERIKSA & HAPUS IDENTITAS SEBELUM KIRIM');
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
  expect(result.rawBody).toContain('[eligibility |');
  expect(result.rawBody).toContain('[registration |');
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
    write(KEYS.gaps, [
      {id:4, stage:'eligibility', task:'Masih membutuhkan bantuan', helper:'Teman / pekerja senior'}
    ]);
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


test('beta invite URL immediately confirms the assigned anonymous tester and first stage', async ({ page }) => {
  const errors = [];
  page.on('pageerror', error => errors.push(error.message));

  await page.goto('/app.html?beta=KEP-0017&stage=roster', { waitUntil: 'domcontentloaded' });
  await page.waitForFunction(() => /\/\s*27/.test(document.querySelector('#progressText')?.textContent || ''), null, { timeout: 15000 });

  await expect(page.locator('#betaModeBanner')).toBeVisible();
  await expect(page.locator('#betaModeBanner')).toContainText('Mode beta KEP-0017');
  await expect(page.locator('#betaModeBanner')).toContainText('Tahap dari aplikasi beta');
  await expect(page.locator('#betaModeBanner')).toContainText('Roster');
  await expect(page.locator('#betaModeBanner')).toContainText('Nilai hanya tahap yang benar-benar Anda alami');
  await expect(page.locator('#quickStart')).toBeHidden();

  const hydrated = await page.evaluate(() => ({
    testerId: JSON.parse(localStorage.getItem('kep.betaTesterId')||'null'),
    done: JSON.parse(localStorage.getItem('kep.doneStages')||'[]'),
    quickSetup: JSON.parse(localStorage.getItem('kep.quickSetupDone')||'false'),
    current: currentStage()?.id || null
  }));
  expect(hydrated.testerId).toBe('KEP-0017');
  expect(hydrated.done).toHaveLength(12);
  expect(hydrated.done).toContain('job_application');
  expect(hydrated.current).toBe('roster');
  expect(hydrated.quickSetup).toBe(true);

  // A later invite URL must not overwrite progress already created on this device.
  await page.goto('/app.html?beta=KEP-0017&stage=visa_docs', { waitUntil: 'domcontentloaded' });
  await page.waitForFunction(() => /\/\s*27/.test(document.querySelector('#progressText')?.textContent || ''), null, { timeout: 15000 });
  expect(await page.evaluate(() => currentStage()?.id || null)).toBe('roster');

  await page.evaluate(() => localStorage.clear());
  await page.goto('/app.html?beta=KEP-9999&stage=visa_docs', { waitUntil: 'domcontentloaded' });
  await page.waitForFunction(() => /\/\s*27/.test(document.querySelector('#progressText')?.textContent || ''), null, { timeout: 15000 });
  await expect(page.locator('#betaModeBanner')).toBeHidden();
  expect(await page.evaluate(() => localStorage.getItem('kep.betaTesterId'))).toBeNull();
  expect(await page.evaluate(() => JSON.parse(localStorage.getItem('kep.doneStages')||'[]'))).toEqual([]);

  await page.evaluate(() => localStorage.clear());
  await page.goto('/app.html?beta=KEP-0031&stage=visa_docs', { waitUntil: 'domcontentloaded' });
  await page.waitForFunction(() => /\/\s*27/.test(document.querySelector('#progressText')?.textContent || ''), null, { timeout: 15000 });
  expect(await page.evaluate(() => currentStage()?.id || null)).toBe('eligibility');
  expect(await page.evaluate(() => JSON.parse(localStorage.getItem('kep.doneStages')||'[]'))).toEqual([]);

  expect(errors).toEqual([]);
});


test('beta evidence stays isolated when a browser switches tester IDs', async ({ page }) => {
  const errors = [];
  page.on('pageerror', error => errors.push(error.message));

  await page.goto('/app.html?beta=KEP-0001', { waitUntil: 'domcontentloaded' });
  await page.waitForFunction(() => /\/\s*27/.test(document.querySelector('#progressText')?.textContent || ''), null, { timeout: 15000 });
  await page.evaluate(() => {
    const checks={eligibility:{stageId:'eligibility',status:'no_private_help',updatedAt:new Date().toISOString()}};
    write(KEYS.betaChecks,checks);
    write(KEYS.gaps,[{id:1,stage:'eligibility',task:'Gap tester satu',helper:'Teman'}]);
  });
  expect(await page.evaluate(() => betaValidationStats().tested)).toBe(1);
  expect(await page.evaluate(() => buildBetaFeedbackBundle().rawBody)).toContain('Gap tester satu');

  await page.goto('/app.html?beta=KEP-0002', { waitUntil: 'domcontentloaded' });
  await page.waitForFunction(() => /\/\s*27/.test(document.querySelector('#progressText')?.textContent || ''), null, { timeout: 15000 });
  expect(await page.evaluate(() => betaValidationStats().tested)).toBe(0);
  expect(await page.evaluate(() => buildBetaFeedbackBundle().rawBody)).not.toContain('Gap tester satu');

  await page.goto('/app.html?beta=KEP-0001', { waitUntil: 'domcontentloaded' });
  await page.waitForFunction(() => /\/\s*27/.test(document.querySelector('#progressText')?.textContent || ''), null, { timeout: 15000 });
  expect(await page.evaluate(() => betaValidationStats().tested)).toBe(1);
  expect(await page.evaluate(() => buildBetaFeedbackBundle().rawBody)).toContain('Gap tester satu');

  expect(errors).toEqual([]);
});


test('manual beta ID switch removes the previous tester evidence from view', async ({ page }) => {
  const errors = await freshPage(page);
  await setStage(page, 'eligibility');
  await page.evaluate(() => switchView('gaps', false));
  await page.locator('#betaValidationPanel').evaluate((el) => { el.open = true; });

  await page.locator('#betaTesterId').fill('KEP-0001');
  await page.locator('#saveBetaTesterIdBtn').click();
  await page.evaluate(() => {
    write(KEYS.gaps,[{id:11,stage:'eligibility',task:'Gap hanya tester satu',helper:'Teman'}]);
    renderGaps();
  });
  await expect(page.locator('#gapList')).toContainText('Gap hanya tester satu');

  await page.locator('#betaTesterId').fill('KEP-0002');
  await page.locator('#saveBetaTesterIdBtn').click();
  await expect(page.locator('#gapList')).not.toContainText('Gap hanya tester satu');
  expect(await page.evaluate(() => buildBetaFeedbackBundle().rawBody)).not.toContain('Gap hanya tester satu');

  await page.locator('#betaTesterId').fill('KEP-0001');
  await page.locator('#saveBetaTesterIdBtn').click();
  await expect(page.locator('#gapList')).toContainText('Gap hanya tester satu');

  expect(errors).toEqual([]);
});


test('unexperienced beta stage never counts as zero-broker evidence', async ({ page }) => {
  const errors = await freshPage(page);
  await setStage(page, 'eligibility');
  await page.evaluate(() => switchView('gaps', false));
  await page.locator('#betaValidationPanel').evaluate((el) => { el.open = true; });

  await page.locator('#betaCheckStage').selectOption('eligibility');
  await page.locator('#betaCheckOutcome').selectOption('not_experienced');
  await page.locator('#saveBetaCheckBtn').click();

  const result = await page.evaluate(() => {
    const stats=betaValidationStats();
    const bundle=buildBetaFeedbackBundle();
    return {
      recorded:stats.recorded,
      tested:stats.tested,
      passed:stats.passed,
      failed:stats.failed,
      notExperienced:stats.notExperienced,
      routePass:stats.routePass,
      checkpointCount:bundle.checkpointCount,
      body:bundle.rawBody
    };
  });

  expect(result.recorded).toBe(1);
  expect(result.tested).toBe(0);
  expect(result.passed).toBe(0);
  expect(result.failed).toBe(0);
  expect(result.notExperienced).toBe(1);
  expect(result.routePass).toBe(false);
  expect(result.checkpointCount).toBe(1);
  expect(result.body).toContain('BELUM DIJALANI / TIDAK DINILAI');
  await expect(page.locator('#betaValidationSummary')).toContainText('0/27');
  await expect(page.locator('#betaValidationSummary')).toContainText('Belum dijalani/tidak dapat dinilai: 1');
  expect(errors).toEqual([]);
});


test('workplace reality check separates public evidence from worker testimony', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  const errors = await freshPage(page);
  await page.locator('[data-quick-stage="eligibility"]').click();

  await page.evaluate(() => switchView('workplace', false));
  await expect(page.locator('#workplace')).toBeVisible();
  await expect(page.locator('#workplaceEvidencePolicy')).toContainText('Mulai dari bukti publik dan SLC');
  await expect(page.locator('#workplaceOfficialLookups')).toContainText('FactoryOn');
  await expect(page.locator('#workplaceOfficialLookups')).toContainText('EPS');
  await expect(page.locator('#workplaceOfficialLookups a')).toHaveCount(2);
  await expect(page.locator('#realityChecks .evidence-badge')).toHaveCount(8);
  await expect(page.locator('#realityChecks .evidence-badge.public')).toHaveCount(5);
  await expect(page.locator('#realityChecks .evidence-badge.worker')).toHaveCount(3);
  await expect(page.locator('#workplaceCoverageDetail')).toContainText('Bukti publik/kontrak: 0/5');
  await expect(page.locator('#workplaceCoverageDetail')).toContainText('Bukti pengalaman pekerja: 0/3');

  const first = page.locator('#realityChecks article').first();
  await expect(first.locator('.verify-state')).toHaveText('Belum diverifikasi');
  await first.locator('input[type="checkbox"]').check();
  await expect(first.locator('.verify-state')).toHaveText('Sudah diperiksa');
  await expect(page.locator('#workplaceCoverageDetail')).toContainText('Bukti publik/kontrak: 1/5');

  const overflow = await page.evaluate(() => ({
    scrollWidth: document.documentElement.scrollWidth,
    innerWidth: window.innerWidth
  }));
  expect(overflow.scrollWidth).toBeLessThanOrEqual(overflow.innerWidth + 1);
  expect(errors).toEqual([]);
});


test('beta enrollment stays closed until launch status opens', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  const errors = [];
  page.on('pageerror', error => errors.push(error.message));

  await page.goto('/beta.html', { waitUntil: 'domcontentloaded' });
  await expect(page.locator('#betaStatusPill')).toHaveText('BELUM DIBUKA', { timeout: 10000 });
  await expect(page.locator('#closedPanel')).toBeVisible();
  await expect(page.locator('#applicationPanel')).toBeHidden();
  await expect(page.locator('body')).toContainText('Beta terbatas untuk 30 peserta pertama');
  await expect(page.locator('body')).toContainText('6 bulan gratis');
  await expect(page.locator('body')).toContainText('Jangan kirim gambar paspor/KTP/ARC');

  const overflow = await page.evaluate(() => ({
    scrollWidth: document.documentElement.scrollWidth,
    innerWidth: window.innerWidth
  }));
  expect(overflow.scrollWidth).toBeLessThanOrEqual(overflow.innerWidth + 1);
  expect(errors).toEqual([]);
});


test('manufacturing job application cannot complete before sector notice', async ({ page }) => {
  const errors = await freshPage(page);
  await setStage(page, 'job_application');

  await page.evaluate(() => {
    const stage=route.stages.find(row=>row.id==='job_application');
    if(!stage)throw new Error('job_application stage missing');
    openStage(stage);
  });

  await expect(page.locator('#stageDialog')).toBeVisible();
  await expect(page.locator('#stageDoneBtn')).toBeEnabled();
  await page.locator('#stageDoneBtn').click();

  await expect(page.locator('#preSubmitResult')).toBeVisible();
  await expect(page.locator('#preSubmitResult')).toContainText('JANGAN LANJUT DULU');
  await expect(page.locator('#preSubmitResult')).toContainText('Checklist dokumen tahap ini belum cukup spesifik');

  const state=await page.evaluate(() => ({
    done: JSON.parse(localStorage.getItem('kep.doneStages')||'[]'),
    current: currentStage()?.id
  }));
  expect(state.done).not.toContain('job_application');
  expect(state.current).toBe('job_application');
  expect(errors).toEqual([]);
});


test('scout request excludes dorm residence details', async ({ page }) => {
  const errors = await freshPage(page);
  const body = await page.evaluate(() => buildScoutRequestBody(
    {
      company:'PT Test Company',
      address:'Seoul workplace address',
      dorm:'PRIVATE DORM ADDRESS 123'
    },
    '• Akomodasi diverifikasi'
  ));

  expect(body).toContain('PT Test Company');
  expect(body).toContain('Seoul workplace address');
  expect(body).toContain('Akomodasi diverifikasi');
  expect(body).not.toContain('PRIVATE DORM ADDRESS 123');
  expect(body).toContain('informasi/alamat asrama tidak disertakan');
  expect(errors).toEqual([]);
});


test('mcu1 uses its verified stage-specific document pack', async ({ page }) => {
  const errors = await freshPage(page);
  await setStage(page, 'mcu1');

  const selected = await page.evaluate(() => {
    const pack=documentPackForStage('mcu1');
    return pack ? {id:pack.id,status:pack.status,title:pack.title,items:(pack.items||[]).length} : null;
  });

  expect(selected).toEqual({
    id:'mcu1_2026',
    status:'verified_2026',
    title:'Persiapan MCU I 2026',
    items:4
  });
  await expect(page.locator('#docStageContext')).toContainText('Persiapan MCU I 2026');
  await expect(page.locator('#docStageContext')).not.toContainText('tunggu pengumuman resmi');
  expect(errors).toEqual([]);
});


test('predeparture OPP scope resolves to verified common pack', async ({ page }) => {
  const errors = await freshPage(page);
  await setStage(page, 'predeparture_training');

  const scopeKey = await page.evaluate(() => {
    const options=scopeOptionsForStage('predeparture_training');
    const preferred=options.find(row=>row.key==='opp_sawangan_wave9_2026')||options[0];
    if(!preferred)throw new Error('no OPP scope available');
    saveScopeSelection('predeparture_training',preferred.key);
    renderDocuments();
    return preferred.key;
  });
  expect(scopeKey).toMatch(/^opp_/);

  const pack = await page.evaluate(() => {
    const value=documentPackForStage('predeparture_training');
    return value ? {id:value.id,status:value.status,items:(value.items||[]).length} : null;
  });
  expect(pack).toEqual({
    id:'opp_common_2026_pack',
    status:'verified_across_multiple_2026_calls',
    items:7
  });
  await expect(page.locator('#docStageContext')).toContainText('OPP 2026');
  await expect(page.locator('#docStageContext')).toContainText('Terverifikasi silang');
  expect(errors).toEqual([]);
});


test('psychology stage uses its verified 2026 pack', async ({ page }) => {
  const errors = await freshPage(page);
  await setStage(page, 'psychology_pre_job');

  const selected = await page.evaluate(() => {
    const pack=documentPackForStage('psychology_pre_job');
    return pack ? {id:pack.id,status:pack.status,title:pack.title,items:(pack.items||[]).length} : null;
  });

  expect(selected?.id).toBe('psychology_pre_job_2026');
  expect(selected?.status).toBe('verified_2026');
  expect(selected?.items).toBe(4);
  expect(selected?.title).toContain('Psikologi 2026');
  await expect(page.locator('#docStageContext')).toContainText('Psikologi 2026');
  await expect(page.locator('#docStageContext')).not.toContainText('Lamaran online Manufaktur 2026 — tunggu pengumuman resmi');
  expect(errors).toEqual([]);
});


test('post SLC stage exposes verified psychology and MCU II checklist', async ({ page }) => {
  const errors = await freshPage(page);
  await setStage(page, 'post_slc_requirements');

  const selected = await page.evaluate(() => {
    const pack=documentPackForStage('post_slc_requirements');
    return pack ? {id:pack.id,status:pack.status,items:(pack.items||[]).length} : null;
  });

  expect(selected).toEqual({
    id:'post_slc_mcu2_2026',
    status:'verified_across_multiple_2026_notices',
    items:9
  });
  await expect(page.locator('#docStageContext')).toContainText('Setelah SLC');
  await expect(page.locator('#docStageContext')).toContainText('Terverifikasi silang');
  await expect(page.locator('#docList')).toContainText('Rp906.000');
  await expect(page.locator('#docList')).toContainText('KTP asli');
  expect(errors).toEqual([]);
});


test('departure scope picker includes partial verified 2026 registry', async ({ page }) => {
  const errors = await freshPage(page);

  const result = await page.evaluate(() => {
    const departure=scopeOptionsForStage('departure');
    const mcu3=scopeOptionsForStage('mcu3_departure');
    return {
      departureKeys:departure.map(row=>row.key),
      mcu3Keys:mcu3.map(row=>row.key),
      jan5:departure.find(row=>row.key==='departure_2026_01_05')||null,
      aug24:mcu3.find(row=>row.key==='departure_2026_08_24')||null
    };
  });

  expect(result.departureKeys.length).toBeGreaterThanOrEqual(15);
  expect(result.departureKeys).toContain('departure_2026_01_05');
  expect(result.departureKeys).toContain('departure_2026_04_27');
  expect(result.departureKeys).toContain('departure_2026_09_15');
  expect(result.mcu3Keys).toContain('departure_2026_08_10');
  expect(result.mcu3Keys).toContain('departure_2026_08_24');
  expect(result.mcu3Keys).toContain('departure_2026_08_25');
  expect(result.mcu3Keys).toContain('departure_2026_08_31');
  expect(result.mcu3Keys).toContain('departure_2026_09_15');
  expect(result.jan5?.sourceUrl).toContain('kp2mi.go.id');
  expect(result.aug24?.sourceUrl).toContain('kp2mi.go.id');
  expect(errors).toEqual([]);
});


test('partial departure registry never suggests another call when date is missing', async ({ page }) => {
  const errors = await freshPage(page);
  await setStage(page, 'departure');

  await page.evaluate(() => {
    const stage=route.stages.find(row=>row.id==='departure');
    openStage(stage);
  });

  await expect(page.locator('#scopePickerSection')).toBeVisible();
  await expect(page.locator('#scopePicker')).toHaveValue('');
  await expect(page.locator('#scopePickerSource')).toBeVisible();
  await expect(page.locator('#scopePickerSource')).toContainText('indeks resmi KP2MI');
  await expect(page.locator('#scopePickerSection small')).toContainText('belum lengkap');
  await expect(page.locator('#scopePickerSection small')).toContainText('jangan memakai aturan tanggal lain');
  const href=await page.locator('#scopePickerSource').getAttribute('href');
  expect(href).toContain('kp2mi.go.id/gtog-korea/info');
  expect(errors).toEqual([]);
});


test('beta OPEN path remains functional and identity-minimal', async ({ page }) => {
  const errors = [];
  page.on('pageerror', error => errors.push(error.message));

  await page.route('**/data/beta_program_v1.json', async route => {
    const response = await route.fetch();
    const program = await response.json();
    program.status = 'open';
    await route.fulfill({
      response,
      json: program
    });
  });

  await page.goto('/beta.html', { waitUntil: 'domcontentloaded' });
  await expect(page.locator('#betaStatusPill')).toHaveText('OPEN · 30 PESERTA', { timeout: 10000 });
  await expect(page.locator('#closedPanel')).toBeHidden();
  await expect(page.locator('#applicationPanel')).toBeVisible();

  const identityInputs = await page.locator(
    '#betaApplicationForm input[type="text"], ' +
    '#betaApplicationForm input[type="email"], ' +
    '#betaApplicationForm input[type="tel"], ' +
    '#betaApplicationForm input[type="file"], ' +
    '#betaApplicationForm textarea'
  ).count();
  expect(identityInputs).toBe(0);

  await expect(page.locator('#applicantStage option')).toHaveCount(28);
  await page.locator('#applicantStage').selectOption('roster');
  await page.locator('#activeProcess').check();
  await page.locator('#feedbackAgreement').check();

  const application = await page.evaluate(() => applicationText());
  expect(application).toContain('Current route stage ID: roster');
  expect(application).toContain('Current stage title:');
  expect(application).toContain('Official G-to-G / EPS E-9 process: YES');
  expect(application).toContain('Feedback participation agreement: YES');
  expect(application).toContain('Queue order should use the received timestamp');
  expect(application.toLowerCase()).not.toContain('passport number:');
  expect(application.toLowerCase()).not.toContain('ktp number:');
  expect(application.toLowerCase()).not.toContain('phone number:');
  expect(application.toLowerCase()).not.toContain('home address:');

  const stageIds = await page.locator('#applicantStage option').evaluateAll(options =>
    options.map(option => option.value).filter(Boolean)
  );
  expect(stageIds).toHaveLength(27);
  expect(new Set(stageIds).size).toBe(27);
  expect(stageIds).toContain('eligibility');
  expect(stageIds).toContain('employment_maintenance');

  expect(errors).toEqual([]);
});


test('progress backup preserves reviewed form fields without beta evidence', async ({ page }) => {
  const errors = await freshPage(page);

  const result = await page.evaluate(() => {
    const form=(formWizards?.forms||[]).find(item=>
      item.stages?.includes('visa_docs') &&
      Array.isArray(item.scopeKeys) &&
      item.scopeKeys.includes('visa_sep08_2026') &&
      (item.fields||[]).some(field=>field.validator)
    );
    if(!form)throw new Error('verified visa form missing');
    const field=(form.fields||[]).find(item=>item.validator);
    if(!field)throw new Error('validated field missing');

    saveScopeSelection('visa_docs','visa_sep08_2026');
    markWizardFieldReviewed(form,field,'visa_docs');
    write(KEYS.gaps,[{id:99,stage:'visa_docs',task:'PRIVATE BETA GAP'}]);
    write(KEYS.betaChecks,{visa_docs:{stageId:'visa_docs',status:'no_private_help'}});

    const key=wizardReviewKey(form,field,'visa_docs');
    const backup=makeProgressBackup();

    write(KEYS.wizardReviewed,[]);
    safeRestoreProgress(backup);

    return {
      key,
      reviewed:read(KEYS.wizardReviewed,[]),
      progressKeys:Object.keys(backup.progress).sort(),
      serialized:JSON.stringify(backup)
    };
  });

  expect(result.reviewed).toContain(result.key);
  expect(result.progressKeys).toContain('wizardReviewed');
  expect(result.serialized).not.toContain('PRIVATE BETA GAP');
  expect(result.progressKeys).not.toContain('gaps');
  expect(result.progressKeys).not.toContain('betaChecks');
  expect(errors).toEqual([]);
});


test('workplace worker evidence empty state is neutral and privacy safe', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  const errors = await freshPage(page);
  await page.locator('[data-quick-stage="eligibility"]').click();
  await page.evaluate(() => switchView('workplace', false));
  await expect(page.locator('#workplace')).toBeVisible();

  await page.locator('#wpCompany').fill('Contoh Manufacturing Co');
  await expect(page.locator('#workplaceWorkerEvidence')).toContainText('BELUM ADA KECOCOKAN');
  await expect(page.locator('#workplaceWorkerEvidence')).toContainText('bukan temuan negatif');
  await expect(page.locator('#workplaceWorkerEvidence')).not.toContainText('palsu');

  const overflow = await page.evaluate(() => ({
    scrollWidth: document.documentElement.scrollWidth,
    innerWidth: window.innerWidth
  }));
  expect(overflow.scrollWidth).toBeLessThanOrEqual(overflow.innerWidth + 1);
  expect(errors).toEqual([]);
});

test('workplace worker evidence renders only summarized verified facts', async ({ page }) => {
  const errors = await freshPage(page);
  await page.locator('[data-quick-stage="eligibility"]').click();
  await page.evaluate(() => switchView('workplace', false));
  await expect(page.locator('#workplace')).toBeVisible();
  await page.locator('#wpCompany').fill('Demo Factory');

  await page.evaluate(() => {
    workplaceWorkerEvidence = {
      status:'beta_collection',
      displayPolicy:{noEvidenceMeaning:'No evidence is not a negative finding.'},
      records:[{
        evidenceId:'WPE-0001',
        experienceYear:'2024',
        companyName:'Demo Factory',
        companyAliases:['DEMO FACTORY'],
        verificationStatus:'single_verified_worker',
        verifiedAt:'2026-10-04',
        facts:[
          {topic:'Pembayaran gaji',summary:'Dalam pengalaman yang diverifikasi, gaji masuk sesuai tanggal yang dilaporkan.',basis:'worker_experience'}
        ],
        media:[]
      }]
    };
    renderWorkplaceWorkerEvidence();
  });

  await expect(page.locator('#workplaceWorkerEvidence')).toContainText('1 CATATAN');
  await expect(page.locator('#workplaceWorkerEvidence')).toContainText('Pembayaran gaji');
  await expect(page.locator('#workplaceWorkerEvidence')).toContainText('1 pekerja terverifikasi');
  await expect(page.locator('#workplaceWorkerEvidence')).toContainText('Pengalaman EPS 2024 · retrospektif');
  await expect(page.locator('#workplaceWorkerEvidence')).toContainText('bukan jaminan kondisi semua pekerja');
  expect(errors).toEqual([]);
});


test('E-9 worker validator panel can open independently without identity fields', async ({ page }) => {
  const errors = [];
  page.on('pageerror', error => errors.push(error.message));

  await page.route('**/data/beta_program_v1.json', async route => {
    const response = await route.fetch();
    const program = await response.json();
    program.status = 'hold';
    program.retrospectivePanel.status = 'open';
    await route.fulfill({ response, json: program });
  });

  await page.goto('/beta.html', { waitUntil: 'domcontentloaded' });
  await expect(page.locator('#closedPanel')).toBeVisible();
  await expect(page.locator('#applicationPanel')).toBeHidden();
  await expect(page.locator('#workerPanelClosed')).toBeHidden();
  await expect(page.locator('#workerValidatorForm')).toBeVisible();

  const identityInputs = await page.locator(
    '#workerValidatorForm input[type="text"], ' +
    '#workerValidatorForm input[type="email"], ' +
    '#workerValidatorForm input[type="tel"], ' +
    '#workerValidatorForm input[type="file"], ' +
    '#workerValidatorForm textarea'
  ).count();
  expect(identityInputs).toBe(0);

  await page.locator('#workerInKorea').check();
  await page.locator('#workerUsedG2G').check();
  await page.locator('#workerFeedbackAgreement').check();
  const body=await page.evaluate(() => workerValidatorText());
  expect(body).toContain('20-person retrospective validation panel');
  expect(body).toContain('Currently working in Korea with E-9: YES');
  expect(body.toLowerCase()).not.toContain('passport number:');
  expect(body.toLowerCase()).not.toContain('phone number:');
  expect(errors).toEqual([]);
});


test('review-required official source suppresses affected exact document guidance', async ({ page }) => {
  const errors = await freshPage(page, { sourceState: 'review_required' });
  await setStage(page, 'psychology_pre_job');

  const selected = await page.evaluate(() => {
    const pack = documentPackForStage('psychology_pre_job');
    return pack ? { id: pack.id, status: pack.status, items: (pack.items || []).length } : null;
  });

  expect(selected).toEqual({
    id: 'psychology_pre_job_2026',
    status: 'review_required',
    items: 0
  });
  await expect(page.locator('#freshnessStatus')).toContainText('PERUBAHAN SUMBER RESMI TERDETEKSI');
  await expect(page.locator('#docStageContext')).toContainText('Panduan tahap ini sedang ditinjau');
  await expect(page.locator('#docStageContext')).toContainText('Jangan gunakan rincian lama');
  await expect(page.locator('#docStageContext')).not.toContainText('Rp350.000');
  await expect(page.locator('#docList')).toContainText('Jangan submit berdasarkan checklist lama');
  expect(errors).toEqual([]);
});


test('worker validator beta IDs show retrospective instructions and role', async ({ page }) => {
  const errors = [];
  page.on('pageerror', error => errors.push(error.message));

  await page.goto('/app.html?beta=KEP-0031&stage=first_payroll_check', { waitUntil: 'domcontentloaded' });
  await page.waitForFunction(() => /\/\s*27/.test(document.querySelector('#progressText')?.textContent || ''), null, { timeout: 15000 });

  await expect(page.locator('#betaModeBanner')).toBeVisible();
  await expect(page.locator('#quickStart')).toBeHidden();
  expect(await page.evaluate(() => document.body.classList.contains('setup-mode'))).toBe(false);
  await expect(page.locator('#betaModeBanner')).toContainText('Panel validator E-9 KEP-0031');
  await expect(page.locator('#betaModeBanner')).toContainText('Fokus awal');
  await expect(page.locator('#betaModeBanner')).toContainText('gaji');
  await page.evaluate(() => switchView('gaps', false));
  await expect(page.locator('#betaCheckStage')).toHaveValue('first_payroll_check');
  expect(await page.evaluate(() => read(KEYS.done,[]).length)).toBe(0);
  await expect(page.locator('#betaModeBanner')).toContainText('pengalaman nyata');
  await expect(page.locator('#betaModeBanner')).toContainText('alamat asrama pribadi');

  const result = await page.evaluate(() => ({
    role: betaTesterRole(),
    body: buildBetaFeedbackBundle().rawBody
  }));
  expect(result.role).toBe('e9_worker_validator');
  expect(result.body).toContain('Peran beta: validator E-9 retrospektif');
  expect(result.body).not.toContain('nama pekerja');
  expect(errors).toEqual([]);
});


test('post-entry document pack stays scoped to residence registration', async ({ page }) => {
  const errors = [];
  page.on('pageerror', error => errors.push(error.message));

  await page.goto('/app.html', { waitUntil: 'domcontentloaded' });
  await page.waitForFunction(() => /\/\s*27/.test(document.querySelector('#progressText')?.textContent || ''), null, { timeout: 15000 });

  const state = await page.evaluate(() => ({
    entryTools: STAGE_TOOLS.korea_entry_training,
    entryPack: documentPackForStage('korea_entry_training')?.id || null,
    handoverPack: documentPackForStage('employer_handover')?.id || null,
    residencePack: documentPackForStage('residence_registration')?.id || null,
    insurancePack: documentPackForStage('eps_insurance_check')?.id || null,
    insuranceTools: STAGE_TOOLS.eps_insurance_check
  }));

  expect(state.entryTools).not.toContain('documents');
  expect(state.entryPack).toBeNull();
  expect(state.handoverPack).toBeNull();
  expect(state.residencePack).toBe('korea_residence');
  expect(state.insurancePack).toBeNull();
  expect(state.insuranceTools).not.toContain('fees');
  expect(errors).toEqual([]);
});


test('quick milestones do not infer post-entry compliance from first payroll receipt', async ({ page }) => {
  const errors = [];
  page.on('pageerror', error => errors.push(error.message));

  await page.goto('/app.html', { waitUntil: 'domcontentloaded' });
  await page.waitForFunction(() => /\/\s*27/.test(document.querySelector('#progressText')?.textContent || ''), null, { timeout: 15000 });

  const milestones = await page.evaluate(() => QUICK_MILESTONES.map(item => ({ ...item })));
  expect(milestones.some(item => item.label.includes('gaji pertama'))).toBe(false);
  expect(milestones.some(item => item.nextStage === 'labor_support_ready')).toBe(false);
  expect(errors).toEqual([]);
});


test('post-entry official help uses Korea foreign worker counseling', async ({ page }) => {
  const errors = [];
  page.on('pageerror', error => errors.push(error.message));

  await page.goto('/app.html', { waitUntil: 'domcontentloaded' });
  await page.waitForFunction(() => typeof officialHelp !== 'undefined' && officialHelp?.channels?.length > 0, null, { timeout: 15000 });

  const state = await page.evaluate(() => {
    const channel = officialHelp.channels.find(item => item.id === 'foreign_worker_counseling');
    return {
      channel,
      entry: officialHelp.stageMap.korea_entry_training,
      insurance: officialHelp.stageMap.eps_insurance_check,
      payroll: officialHelp.stageMap.first_payroll_check
    };
  });

  expect(state.channel?.phones?.some(item => item.display === '1577-0071')).toBe(true);
  expect(state.channel?.languages || '').toContain('Bahasa Indonesia');
  expect(state.entry).toContain('foreign_worker_counseling');
  expect(state.insurance).toContain('foreign_worker_counseling');
  expect(state.payroll).toContain('foreign_worker_counseling');
  expect(errors).toEqual([]);
});


test('mid-process selector explains that prior stages are marked complete', async ({ page }) => {
  await page.goto('/app.html', { waitUntil: 'domcontentloaded' });
  await page.waitForFunction(() => /\/\s*27/.test(document.querySelector('#progressText')?.textContent || ''), null, { timeout: 15000 });
  await page.locator('#allJourneyDetails').evaluate(el => el.open = true);
  await expect(page.locator('.jump-stage')).toContainText('Tahap paling awal yang belum selesai');
  await expect(page.locator('.jump-stage')).toContainText('Residence Card');
  await expect(page.locator('#currentStageSelect option').first()).toHaveText('Pilih tahap paling awal yang belum selesai');
});


test('retrospective worker evidence records experience year before stage validation', async ({ page }) => {
  const errors = [];
  page.on('pageerror', error => errors.push(error.message));

  await page.goto('/app.html?beta=KEP-0031', { waitUntil: 'domcontentloaded' });
  await page.waitForFunction(() => /\/\s*27/.test(document.querySelector('#progressText')?.textContent || ''), null, { timeout: 15000 });
  await page.evaluate(() => switchView('gaps', false));
  await page.locator('#betaValidationPanel').evaluate(el => { el.open = true; });

  await expect(page.locator('#betaWorkerExperienceWrap')).toBeVisible();
  await page.locator('#betaCheckStage').selectOption('korea_entry_training');
  await page.locator('#betaCheckOutcome').selectOption('no_private_help');
  await page.locator('#saveBetaCheckBtn').click();
  expect(await page.evaluate(() => betaValidationStats().tested)).toBe(0);
  await expect(page.locator('#betaWorkerExperienceStatus')).toContainText('Pilih tahun pengalaman');

  await page.locator('#betaWorkerExperienceYear').selectOption('2024');
  await page.locator('#saveBetaCheckBtn').click();
  expect(await page.evaluate(() => betaValidationStats().tested)).toBe(1);
  const bundle = await page.evaluate(() => buildBetaFeedbackBundle().rawBody);
  expect(bundle).toContain('Tahun pengalaman/proses EPS: 2024');

  await page.goto('/app.html?beta=KEP-0032', { waitUntil: 'domcontentloaded' });
  await page.waitForFunction(() => /\/\s*27/.test(document.querySelector('#progressText')?.textContent || ''), null, { timeout: 15000 });
  await page.evaluate(() => switchView('gaps', false));
  await page.locator('#betaValidationPanel').evaluate(el => { el.open = true; });
  await expect(page.locator('#betaWorkerExperienceYear')).toHaveValue('');

  expect(errors).toEqual([]);
});


test('retrospective worker year keeps prior-cycle evidence out of 2026 route PASS', async ({ page }) => {
  const errors = [];
  page.on('pageerror', error => errors.push(error.message));

  await page.goto('/app.html', { waitUntil: 'domcontentloaded' });
  await page.waitForFunction(() => /\/\s*27/.test(document.querySelector('#progressText')?.textContent || ''), null, { timeout: 15000 });

  const state = await page.evaluate(() => {
    write(KEYS.betaTesterId, 'KEP-0031');
    write(KEYS.betaWorkerExperienceYear, '2024');
    const allPass = Object.fromEntries(
      route.stages.map(stage => [stage.id, {
        stageId: stage.id,
        status: 'no_private_help',
        updatedAt: '2026-10-04T00:00:00.000Z'
      }])
    );
    write(KEYS.betaChecks, allPass);
    const prior = betaValidationStats();

    write(KEYS.betaWorkerExperienceYear, '2026');
    const current = betaValidationStats();

    return {
      prior: {
        checkpointComplete: prior.checkpointComplete,
        currentRouteEligible: prior.currentRouteEligible,
        retrospectiveOnly: prior.retrospectiveOnly,
        routePass: prior.routePass
      },
      current: {
        checkpointComplete: current.checkpointComplete,
        currentRouteEligible: current.currentRouteEligible,
        retrospectiveOnly: current.retrospectiveOnly,
        routePass: current.routePass
      }
    };
  });

  expect(state.prior).toEqual({
    checkpointComplete: true,
    currentRouteEligible: false,
    retrospectiveOnly: true,
    routePass: false
  });
  expect(state.current).toEqual({
    checkpointComplete: true,
    currentRouteEligible: true,
    retrospectiveOnly: false,
    routePass: true
  });
  expect(errors).toEqual([]);
});


test('beta feedback sanitizer redacts Korean phone numbers and always warns about residual privacy risk', async ({ page }) => {
  const errors = await freshPage(page);
  const result = await page.evaluate(() => {
    const raw='Hubungi +82 10-1234-5678. Nama/alamat mungkin tetap ada.';
    return {
      sanitized:sanitizeBetaFeedback(raw),
      shared:sanitizedBetaFeedbackText(raw),
      cleanShared:sanitizedBetaFeedbackText('Tidak ada nomor di sini.')
    };
  });
  expect(result.sanitized.redacted).toBe(true);
  expect(result.sanitized.text).not.toContain('+82 10-1234-5678');
  expect(result.shared).toContain('tidak dapat menjamin nama, alamat');
  expect(result.cleanShared).toContain('tidak ada pola nomor/email yang terdeteksi otomatis');
  expect(errors).toEqual([]);
});
