const {test, expect} = require('@playwright/test');

// M42: public applicant copy must obey the hard release gate even while
// expression-of-interest remains open. Never substitute other cohorts' docs.
test('M42 Indonesian beta copy keeps exact 2026 manufacturing job-doc gate mandatory', async ({page}) => {
  await page.goto('/beta.html?src=website', {waitUntil:'domcontentloaded'});
  const closed = page.locator('#closedPanel');
  const gates = page.locator('#releaseGateNote');
  await expect(closed).toBeVisible();
  await expect(closed).toContainText('akses layanan beta masih HOLD');
  await expect(closed).toContainText('Manufaktur Umum E-9 tahun 2026 setelah Skill Test');
  await expect(closed).toContainText('Perikanan, Root Industry, tahun lain');
  await expect(gates).toContainText('Masih menjadi syarat wajib sebelum akses beta dibuka');
  await expect(gates).toContainText('persetujuan manusia');
  await expect(gates).toContainText('versi commit');
  await expect(gates).toContainText('keputusan OPEN');
  await expect(gates).not.toContainText('Bukan syarat untuk membuka beta');
  await expect(closed).not.toContainText('tidak otomatis melarang');
  await expect(page.locator('#betaStatusPill')).toContainText('AKSES MENUNGGU');
});

test('M42 interest stays OPEN but direct intake and public beta remain unapproved', async ({page, request}) => {
  const program = await (await request.get('/data/beta_program_v1.json')).json();
  expect(program.status).not.toBe('open');
  await page.goto('/beta.html?src=website', {waitUntil:'domcontentloaded'});
  await expect(page.locator('#applicationPanel')).toBeVisible();
  await expect(page.locator('#betaStatusPill')).toContainText('PENDAFTARAN OPEN');
  await expect(page.locator('#directIntakeFields')).toBeHidden();
  await expect(page.locator('#betaApplicationSubmitBtn')).toHaveText('Kirim lewat aplikasi email');
  await expect(page.locator('#releaseGateNote')).toContainText('pengiriman minat bukan aktivasi akses beta');
});
