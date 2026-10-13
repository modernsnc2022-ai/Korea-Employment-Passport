'use strict';
const { test, expect } = require('@playwright/test');
const fs = require('node:fs');
const path = require('node:path');

const root = path.resolve(__dirname, '..');
const docs = path.join(root, 'docs');
const dataNames = [
  'np_e9_manufacturing_2026.json',
  'np_e9_manufacturing_2026_ne.json',
  'np_stage_readiness_2026.json',
  'np_document_packs_2026.json',
  'np_notice_provenance_2026.json'
];

function sourceAssets() {
  const html = fs.readFileSync(path.join(docs, 'nepal-journey.html'), 'utf8');
  // Remote CSS/JS requests are forbidden in this smoke test: all code is
  // loaded from the checked-in branch directly into Chromium.
  if (!html.includes('<script src="nepal-journey.js" defer></script>')) {
    throw new Error('Expected Nepal navigator script tag is missing');
  }
  const body = html
    .replace(/<script src="nepal-journey\.js" defer><\/script>/, '')
    .replace(/<link rel="stylesheet" href="styles\.css">/, '');
  const javascript = fs.readFileSync(path.join(docs, 'nepal-journey.js'), 'utf8');
  const data = Object.fromEntries(dataNames.map(name => [
    'data/' + name,
    JSON.parse(fs.readFileSync(path.join(docs, 'data', name), 'utf8'))
  ]));
  return { body, javascript, data };
}

async function openOffline(page, change = () => {}) {
  const { body, javascript, data } = sourceAssets();
  change(data);
  // page.setContent does not request localhost, a file:// path or a web URL.
  // This works on restricted browser hosts where page.goto is not allowed.
  await page.setContent(body, { waitUntil: 'domcontentloaded' });
  await page.evaluate(entries => {
    window.fetch = async input => {
      const name = String(input);
      if (!Object.hasOwn(entries, name)) {
        return new Response('not found', { status: 404 });
      }
      return new Response(JSON.stringify(entries[name]), {
        status: 200, headers: { 'Content-Type': 'application/json' }
      });
    };
  }, data);
  await page.addScriptTag({ content: javascript });
}

test('Nepal Chromium offline: 2026 closed registration and cohort selection', async ({ page }) => {
  await openOffline(page);
  await expect(page.locator('#previewBody')).toBeVisible();
  await expect(page.locator('#stageDetail .state')).toContainText('२०२६ आवेदन अवधि बन्द');
  await expect(page.locator('#noticeReview .notice-item')).toHaveCount(10);
  await page.locator('#cohortSelect').selectOption('future');
  await expect(page.locator('#stageDetail')).toBeHidden();
  await expect(page.locator('#cohortGuidance')).toContainText('अर्को Manufacturing');
  await page.locator('#cohortSelect').selectOption('other');
  await expect(page.locator('#stageDetail')).toBeHidden();
  await expect(page.locator('#cohortGuidance')).toContainText('Root Industry');
  await page.locator('#cohortSelect').selectOption('current');
  await expect(page.locator('#stageDetail')).toBeVisible();
});

test('Nepal Chromium offline: unverified 2026 fees and old document lists are never shown', async ({ page }) => {
  await openOffline(page);
  await expect(page.locator('#previewBody')).toBeVisible();
  await page.locator('#stageSelect').selectOption('job_application');
  await expect(page.locator('#stageDetail .state')).toContainText('प्रमाणीकरण');
  await expect(page.locator('#stageDetail')).not.toContainText('US$5');
  await expect(page.locator('#stageDetail .document-pack li')).toHaveCount(0);
  await page.locator('#stageSelect').selectOption('visa_docs');
  await expect(page.locator('#stageDetail .document-pack li')).toHaveCount(0);
  await expect(page.locator('#stageDetail')).not.toContainText('NPR 10,700');
  await expect(page.locator('#stageDetail .warning')).toContainText('विस्तृत सूची');
});

test('Nepal Chromium offline: policy changes cause fail-closed view', async ({ page }) => {
  await openOffline(page, data => {
    data['data/np_notice_provenance_2026.json'].policy.allowCrossSectorPromotion = true;
  });
  await expect(page.locator('#loadError')).toBeVisible();
  await expect(page.locator('#previewBody')).toBeHidden();
  await expect(page.locator('#statusSummary')).toContainText('लोड हुन सकेन');
});

test('Nepal Chromium offline: missing official-data file causes fail-closed view', async ({ page }) => {
  await openOffline(page, data => { delete data['data/np_stage_readiness_2026.json']; });
  await expect(page.locator('#loadError')).toBeVisible();
  await expect(page.locator('#previewBody')).toBeHidden();
});


test('Nepal Chromium offline: stale payment warning cannot be rendered for held visa stage', async ({ page }) => {
  await openOffline(page, data => {
    data['data/np_e9_manufacturing_2026.json'].stages.find(s => s.id === 'visa_docs').warning = 'Pay NPR 10,700 now';
  });
  await expect(page.locator('#previewBody')).toBeVisible();
  await page.locator('#stageSelect').selectOption('visa_docs');
  await expect(page.locator('#stageDetail')).not.toContainText('NPR 10,700');
  await expect(page.locator('#stageDetail .document-pack li')).toHaveCount(0);
});

test('Nepal Chromium offline: authenticated August 5 extension and passport exception', async ({ page }) => {
  await openOffline(page);
  await expect(page.locator('#previewBody')).toBeVisible();
  await expect(page.locator('#statusSummary')).toContainText('५ अगस्टसम्म');
  await page.locator('#stageSelect').selectOption('registration');
  await expect(page.locator('#stageDetail .action-text')).toContainText('५ अगस्ट २०२६');
  await expect(page.locator('#stageDetail a[href="https://epsnepal.gov.np/postdetails/143"]')).toHaveCount(1);
  await page.locator('#stageSelect').selectOption('document_verify');
  await expect(page.locator('#stageDetail .action-text')).toContainText('मान्य राहदानी');
});

test('Nepal Chromium offline: forged verified extension is rejected', async ({ page }) => {
  await openOffline(page, data => {
    data['data/np_stage_readiness_2026.json'].currentCohort.recruitmentRegistration.crossSourceSchedule.extensionNoticeUrl =
      'https://epsnepal.gov.np/postdetails/136';
  });
  await expect(page.locator('#loadError')).toBeVisible();
  await expect(page.locator('#previewBody')).toBeHidden();
});
