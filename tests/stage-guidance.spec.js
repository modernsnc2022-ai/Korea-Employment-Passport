const { test, expect } = require('@playwright/test');

test('all 27 stages share preparation guidance without changing recorded progress', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto('/app.html');
  await page.locator('#quickStart').waitFor();
  await page.locator('[data-quick-stage="exam_fee"]').click();
  const before = await page.evaluate(() => localStorage.getItem('kep.doneStages'));
  const stages = await page.evaluate(() => route.stages.map(stage => stage.id));
  expect(stages).toHaveLength(27);
  for (const id of stages) {
    await page.evaluate(id => openStage(route.stages.find(stage => stage.id === id)), id);
    await expect(page.locator('#stageAction')).not.toBeEmpty();
    await expect(page.locator('#stagePreparation')).toContainText('Dokumen yang perlu disiapkan');
    await expect(page.locator('#stagePreparation')).toContainText('Informasi yang belum tersedia tidak berarti gratis');
    await expect(page.locator('#stageSource')).toHaveAttribute('href', /^https:\/\//);
    await page.locator('#stageDialog .close').click();
  }
  expect(await page.evaluate(() => localStorage.getItem('kep.doneStages'))).toBe(before);
});

test('stage preparation cannot leak another cohort checklist', async ({ page }) => {
  await page.goto('/app.html');
  await page.locator('#quickStart').waitFor();
  await page.evaluate(() => openStage(route.stages.find(stage => stage.id === 'visa_docs')));
  await expect(page.locator('#stagePreparation')).toContainText('Jangan memakai dokumen dari panggilan lain');
  await expect(page.locator('#stagePreparation li')).toHaveCount(0);
});

test('documents put matching notice and checklist context before optional field tools', async ({ page }) => {
  await page.goto('/app.html');
  await page.locator('#quickStart').waitFor();
  await page.locator('[data-quick-stage="eligibility"]').click();
  await page.locator('.utility-tab[data-view="documents"]').click();
  const context = await page.locator('#docStageContext').boundingBox();
  const tool = await page.locator('.field-copilot').boundingBox();
  expect(context.y).toBeLessThan(tool.y);
});
