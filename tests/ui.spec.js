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

  await expect(page.locator('#exactAnswerList')).not.toContainText('07.00 WIB');
  await page.locator('#scopePicker').selectOption('opp_sawangan_wave10_2026');
  await expect(page.locator('#exactAnswerList')).toContainText('07.00 WIB');

  expect(errors).toEqual([]);
});
