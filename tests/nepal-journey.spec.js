const { test, expect } = require('@playwright/test');

test('Nepal 2026 journey is a guarded preview with explicit closed registration', async ({ page }) => {
  await page.goto('/nepal-journey.html', { waitUntil: 'domcontentloaded' });
  await expect(page.locator('#previewBody')).toBeVisible();
  await expect(page.locator('#statusSummary')).toContainText('beta access उपलब्ध छैन');
  await expect(page.locator('#stageSelect')).toHaveValue('registration');
  await expect(page.locator('#stageDetail .state')).toContainText('२०२६ आवेदन अवधि बन्द');
  await expect(page.locator('input[type="text"]')).toHaveCount(0);
  await expect(page.locator('input[type="file"]')).toHaveCount(0);
  await expect(page.getByText('KEP सरकारी निकाय')).toBeVisible();
});

test('Nepal current cohort holds 2026 test, skill and downstream stages', async ({ page }) => {
  await page.goto('/nepal-journey.html');
  await expect(page.locator('#previewBody')).toBeVisible();

  await page.locator('#stageSelect').selectOption('eps_topik');
  await expect(page.locator('#stageDetail .state')).toContainText('नयाँ आधिकारिक सूचना');
  await expect(page.locator('#stageDetail')).toContainText('undecided');
  await expect(page.locator('#stageDetail a[href*="epstopik.hrdkorea.or.kr"]')).toHaveCount(1);

  await page.locator('#stageSelect').selectOption('skill_competency');
  await expect(page.locator('#stageDetail .state')).toContainText('नयाँ आधिकारिक सूचना');
  await expect(page.locator('#stageDetail a[href*="/postdetails/101"]')).toHaveCount(0);
  await expect(page.locator('#stageDetail a[href="https://epsnepal.gov.np/notices"]')).toHaveCount(2);

  await page.locator('#stageSelect').selectOption('job_application');
  await expect(page.locator('#stageDetail .state')).toContainText('प्रमाणीकरण');
  await expect(page.locator('#stageDetail .document-pack')).toContainText('हालको २०२६ आवेदनका लागि अन्तिम');
  await expect(page.locator('#stageDetail')).not.toContainText('2025 Manufacturing second-round');
});

test('Nepal document baseline cannot be shown as current payment guidance', async ({ page }) => {
  await page.goto('/nepal-journey.html');
  await expect(page.locator('#previewBody')).toBeVisible();
  await page.locator('#stageSelect').selectOption('visa_docs');
  await expect(page.locator('#stageDetail .state')).toContainText('प्रमाणीकरण');
  await expect(page.locator('#stageDetail .warning')).toContainText('विस्तृत सूची');
  await expect(page.locator('#stageDetail .document-pack')).toContainText('पुरानो/सामान्य प्रक्रिया मात्र');
  await expect(page.locator('#stageDetail button')).toHaveCount(0);
});

test('Nepal navigator fails closed when beta safety gate is unexpectedly open', async ({ page }) => {
  await page.route('**/data/np_stage_readiness_2026.json', async route => {
    const original = await route.fetch();
    const current = await original.json();
    current.betaReadiness.status = 'open';
    await route.fulfill({ response: original, json: current });
  });
  await page.goto('/nepal-journey.html', { waitUntil: 'domcontentloaded' });
  await expect(page.locator('#loadError')).toBeVisible();
  await expect(page.locator('#previewBody')).toBeHidden();
  await expect(page.locator('#statusSummary')).toContainText('लोड हुन सकेन');
});


test('Nepal provenance separates 2025 job notices from 2026 application and October departure', async ({ page }) => {
  await page.goto('/nepal-journey.html', { waitUntil: 'domcontentloaded' });
  await expect(page.locator('#previewBody')).toBeVisible();
  const audit = page.locator('#noticeReview');
  await expect(audit.locator('.notice-item')).toHaveCount(10);
  await expect(audit).toContainText('२०२५ समूहको सूचना');
  await expect(audit).toContainText('प्रस्थान सूचना');
  await expect(audit).toContainText('२०२६ को अर्को कार्यक्रम');
  const root = audit.locator('.notice-item', { has: page.locator('a[href*="/postdetails/131"]') });
  await expect(root).toContainText('Manufacturing पहिलो चरणमा लागू हुँदैन');
  await expect(audit).toContainText('2026-10-02');
  await expect(audit).toContainText('2026-07-30');
  const prior = audit.locator('.notice-item', { has: page.locator('a[href*="/postdetails/127"]') });
  await expect(prior).toContainText('२०२६ मा लागू हुँदैन');
  const departure = audit.locator('.notice-item', { has: page.locator('a[href*="/postdetails/157"]') });
  await expect(departure).toContainText('हालको आवेदन समूहसँग सम्बन्ध अपुष्ट');
  await expect(audit.locator('a[href*="/postdetails/137"]')).toHaveCount(1);
});

test('Nepal notice provenance cannot silently promote an October departure to current 2026 first phase', async ({ page }) => {
  await page.route('**/data/np_notice_provenance_2026.json', async route => {
    const original = await route.fetch();
    const ledger = await original.json();
    const departure = ledger.notices.find(n => n.id === 'np_oct_2026_regular_departure');
    departure.applicability = 'verified_current_primary';
    await route.fulfill({ response: original, json: ledger });
  });
  await page.goto('/nepal-journey.html', { waitUntil: 'domcontentloaded' });
  await expect(page.locator('#loadError')).toBeVisible();
  await expect(page.locator('#previewBody')).toBeHidden();
});

test('Nepal notice provenance fails closed when approval flags are loosened', async ({ page }) => {
  await page.route('**/data/np_notice_provenance_2026.json', async route => {
    const original = await route.fetch();
    const ledger = await original.json();
    ledger.policy.allowDepartureToPromote2026ApplicationStages = true;
    await route.fulfill({ response: original, json: ledger });
  });
  await page.goto('/nepal-journey.html', { waitUntil: 'domcontentloaded' });
  await expect(page.locator('#loadError')).toBeVisible();
  await expect(page.locator('#previewBody')).toBeHidden();
});

test('Nepal Root Industry notice cannot become current Manufacturing primary notice', async ({ page }) => {
  await page.route('**/data/np_notice_provenance_2026.json', async route => {
    const original = await route.fetch();
    const ledger = await original.json();
    const root = ledger.notices.find(n => n.id === 'np_2026_root_industry_alt_0701');
    root.applicability = 'verified_current_primary';
    await route.fulfill({ response: original, json: ledger });
  });
  await page.goto('/nepal-journey.html', { waitUntil: 'domcontentloaded' });
  await expect(page.locator('#loadError')).toBeVisible();
  await expect(page.locator('#previewBody')).toBeHidden();
});

test('Nepal refuses policy that allows same-year Root Industry to leak into Manufacturing', async ({ page }) => {
  await page.route('**/data/np_notice_provenance_2026.json', async route => {
    const original = await route.fetch();
    const ledger = await original.json();
    ledger.policy.allowCrossSectorPromotion = true;
    await route.fulfill({ response: original, json: ledger });
  });
  await page.goto('/nepal-journey.html', { waitUntil: 'domcontentloaded' });
  await expect(page.locator('#loadError')).toBeVisible();
  await expect(page.locator('#previewBody')).toBeHidden();
});


test('Future Nepal applicants cannot see closed 2026 first-phase instructions as actionable steps', async ({ page }) => {
  await page.goto('/nepal-journey.html', { waitUntil: 'domcontentloaded' });
  await expect(page.locator('#previewBody')).toBeVisible();
  await page.locator('#cohortSelect').selectOption('future');
  await expect(page.locator('#stagePicker')).toBeHidden();
  await expect(page.locator('#stageDetail')).toBeHidden();
  await expect(page.locator('#cohortGuidance')).toBeVisible();
  await expect(page.locator('#cohortGuidance')).toContainText('अर्को Manufacturing आवेदनको आधिकारिक सूचना');
  await expect(page.locator('#cohortGuidance a[href="https://epsnepal.gov.np/notices"]')).toHaveCount(1);
  await page.locator('#cohortSelect').selectOption('current');
  await expect(page.locator('#stagePicker')).toBeVisible();
  await expect(page.locator('#stageDetail')).toBeVisible();
  await expect(page.locator('#stageDetail .state')).toContainText('२०२६ आवेदन अवधि बन्द');
});

test('Prior-year and Root Industry applicants are isolated from general Manufacturing instructions', async ({ page }) => {
  await page.goto('/nepal-journey.html', { waitUntil: 'domcontentloaded' });
  await expect(page.locator('#previewBody')).toBeVisible();
  await page.locator('#cohortSelect').selectOption('other');
  await expect(page.locator('#stagePicker')).toBeHidden();
  await expect(page.locator('#stageDetail')).toBeHidden();
  await expect(page.locator('#cohortGuidance')).toBeVisible();
  await expect(page.locator('#cohortGuidance')).toContainText('२०२५');
  await expect(page.locator('#cohortGuidance')).toContainText('Root Industry');
  await expect(page.locator('#noticeReview')).toContainText('२०२६ को अर्को कार्यक्रम');
});


test('Nepal held 2026 employment stage never renders obsolete fee or exact prior-cohort checklist', async ({ page }) => {
  await page.goto('/nepal-journey.html', { waitUntil: 'domcontentloaded' });
  await expect(page.locator('#previewBody')).toBeVisible();
  await page.locator('#stageSelect').selectOption('job_application');
  await expect(page.locator('#stageDetail .state')).toContainText('प्रमाणीकरण');
  await expect(page.locator('#stageDetail')).not.toContainText('US$5');
  await expect(page.locator('#stageDetail .document-pack li')).toHaveCount(0);
  await expect(page.locator('#stageDetail .document-pack')).toContainText('विस्तृत सूची');
  await expect(page.locator('#stageDetail a[href="https://epsnepal.gov.np/notices"]')).toHaveCount(2);
});

test('Nepal held visa stage suppresses obsolete cost while verified closed registration keeps sources', async ({ page }) => {
  await page.goto('/nepal-journey.html', { waitUntil: 'domcontentloaded' });
  await expect(page.locator('#previewBody')).toBeVisible();
  await page.locator('#stageSelect').selectOption('visa_docs');
  await expect(page.locator('#stageDetail .state')).toContainText('प्रमाणीकरण');
  await expect(page.locator('#stageDetail .document-pack li')).toHaveCount(0);
  await expect(page.locator('#stageDetail')).not.toContainText('NPR 10,700');
  await expect(page.locator('#stageDetail .warning')).toContainText('विस्तृत सूची');
  await page.locator('#stageSelect').selectOption('registration');
  await expect(page.locator('#stageDetail .state')).toContainText('२०२६ आवेदन अवधि बन्द');
  await expect(page.locator('#stageDetail .document-pack li').first()).toBeVisible();
  await expect(page.locator('#stageDetail a[href*="/postdetails/136"]').first()).toBeVisible();
});


test('Nepal held visa stage ignores an injected obsolete payment warning', async ({ page }) => {
  await page.route('**/data/np_e9_manufacturing_2026.json', async route => {
    const original = await route.fetch();
    const pack = await original.json();
    pack.stages.find(stage => stage.id === 'visa_docs').warning = 'Pay NPR 10,700 now';
    await route.fulfill({ response: original, json: pack });
  });
  await page.goto('/nepal-journey.html', { waitUntil: 'domcontentloaded' });
  await expect(page.locator('#previewBody')).toBeVisible();
  await page.locator('#stageSelect').selectOption('visa_docs');
  await expect(page.locator('#stageDetail .state')).toContainText('प्रमाणीकरण');
  await expect(page.locator('#stageDetail')).not.toContainText('NPR 10,700');
  await expect(page.locator('#stageDetail .document-pack li')).toHaveCount(0);
});
