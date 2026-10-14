const { test, expect } = require('@playwright/test');
const fs = require('node:fs');
const path = require('node:path');

// Additional launch-readiness audit, separate from the normal Indonesian UI smoke tests.
// No real user data, enrollment, external endpoints or publication actions are used.
test('Indonesian route maps all 27 ordered stages to nonempty Bahasa Indonesia copy', async ({ request }) => {
  const route = await (await request.get('/data/id_e9_manufacturing_2026.json')).json();
  const copy = await (await request.get('/data/id_e9_manufacturing_2026_id.json')).json();
  expect(route.stages).toHaveLength(27);
  expect(Object.keys(copy).sort()).toEqual(route.stages.map(s => s.id).sort());
  const seen = new Set();
  for (const stage of route.stages) {
    expect(seen.has(stage.id)).toBe(false);
    seen.add(stage.id);
    expect(copy[stage.id].title.trim().length).toBeGreaterThan(3);
    expect(copy[stage.id].action.trim().length).toBeGreaterThan(12);
    expect(copy[stage.id].title + copy[stage.id].action).not.toMatch(/\b(undefined|null|TODO|TBD|lorem ipsum)\b/i);
    if (stage.warning) expect(copy[stage.id].warning?.trim().length || 0).toBeGreaterThan(8);
  }
  expect(route.stages.find(s => s.id === 'job_application').brokerReplacement).toBe('held_official_notice');
  expect(copy.job_application.warning).toContain('Jangan submit');
});

for (const width of [320, 360, 390, 1280]) {
  test('Indonesian applicant first-use and 27-stage navigation at ' + width + 'px', async ({ page }) => {
    await page.setViewportSize({ width, height: 760 });
    const jsErrors = [];
    page.on('pageerror', e => jsErrors.push(e.message));
    await page.goto('/app.html', { waitUntil: 'domcontentloaded' });
    await expect(page.locator('#progressText')).toContainText('/ 27');
    await expect(page.locator('#quickStart')).toBeVisible();
    await page.locator('[data-quick-stage="eligibility"]').click();
    await expect(page.locator('#nextAction')).toBeVisible();
    await expect(page.locator('.utility-nav')).toBeVisible();
    await expect(page.locator('.micro-help')).toBeVisible();
    const frame = await page.evaluate(() => {
      const active = [...document.querySelectorAll('button:not([hidden])')]
        .filter(x => x.getClientRects().length && getComputedStyle(x).visibility !== 'hidden');
      const outliers = active.filter(x => {
        // Closed details are not operable, and horizontal carousels are
        // intentionally swipeable on small screens.
        if (x.closest('details:not([open])')) return false;
        let ancestor = x.parentElement;
        while (ancestor && ancestor !== document.body) {
          const style = getComputedStyle(ancestor);
          const r = ancestor.getBoundingClientRect();
          if (/auto|scroll/.test(style.overflowX) &&
              ancestor.scrollWidth > ancestor.clientWidth + 1 &&
              r.left >= -2 && r.right <= innerWidth + 2) return false;
          ancestor = ancestor.parentElement;
        }
        const r = x.getBoundingClientRect();
        return r.left < -2 || r.right > innerWidth + 2;
      }).map(x => {
        const r = x.getBoundingClientRect();
        return { text:x.textContent.trim().slice(0,32), left:r.left, right:r.right };
      });
      return { scrollWidth:document.documentElement.scrollWidth, innerWidth, outliers:outliers.slice(0,12) };
    });
    expect(frame.scrollWidth).toBeLessThanOrEqual(frame.innerWidth + 1);
    expect(frame.outliers).toEqual([]);
    expect(jsErrors).toEqual([]);
  });
}

for (const width of [320, 390]) {
  test('Beta intake at ' + width + 'px distinguishes applications from access and advertises six months', async ({ page }) => {
    await page.setViewportSize({ width, height: 760 });
    await page.goto('/beta.html?src=website', { waitUntil: 'domcontentloaded' });
    await expect(page.locator('#betaStatusPill')).toContainText('PENDAFTARAN OPEN');
    await expect(page.locator('#betaStatusPill')).toContainText('AKSES MENUNGGU');
    await expect(page.locator('#applicationPanel')).toBeVisible();
    await expect(page.locator('#closedPanel')).toBeVisible();
    await expect(page.locator('#directIntakeFields')).toBeHidden();
    await expect(page.locator('#betaApplicationSubmitBtn')).toHaveText('Kirim lewat aplikasi email');
    await expect(page.locator('body')).toContainText('6 bulan gratis');
    await expect(page.locator('body')).toContainText('tidak dimasukkan ke repositori publik');
    const horizontal = await page.evaluate(() => ({scrollWidth:document.documentElement.scrollWidth, width:innerWidth}));
    expect(horizontal.scrollWidth).toBeLessThanOrEqual(horizontal.width + 1);
  });
}

test('Official-target links open with noopener on Indonesian pages', async ({ page }) => {
  for (const url of ['/app.html','/beta.html','/privacy.html']) {
    await page.goto(url, { waitUntil:'domcontentloaded' });
    if(url.includes('app.html')) await expect(page.locator('#progressText')).toContainText('/ 27');
    const problems = await page.evaluate(() =>
      [...document.querySelectorAll('a[target="_blank"]')]
       .filter(x => !x.rel.split(/\s+/).includes('noopener'))
       .map(x => ({text:x.textContent.trim().slice(0,55), href:x.getAttribute('href')}))
    );
    expect(problems, url + ' has unsafe new-window links').toEqual([]);
  }
});

test('Indonesian document comparison never persists typed identity strings', async ({ page }) => {
  await page.goto('/app.html', {waitUntil:'domcontentloaded'});
  await expect(page.locator('#quickStart')).toBeVisible();
  await page.locator('[data-quick-stage="eligibility"]').click();
  await page.locator('.utility-tab[data-view="documents"]').click();
  await expect(page.locator('#documents')).toBeVisible();
  await page.getByText('Cek apakah data sama di semua dokumen (opsional)', { exact: true }).click();
  await page.locator('#consNamePassport').fill('PRIVATE_TEST_PASSPORT_NAME_7171');
  await page.locator('#consNameSlc').fill('PRIVATE_TEST_SLC_NAME_8282');
  await page.locator('#checkConsistencyBtn').click();
  await expect(page.locator('#consistencyResult')).toBeVisible();
  const stored = await page.evaluate(() => JSON.stringify(localStorage));
  expect(stored).not.toContain('PRIVATE_TEST_PASSPORT_NAME_7171');
  expect(stored).not.toContain('PRIVATE_TEST_SLC_NAME_8282');
});


test('Indonesia app, landing and privacy disclose in Indonesian without stale English placeholders', async ({ page }) => {
  await page.goto('/app.html', { waitUntil: 'domcontentloaded' });
  await expect(page.locator('.summary .eyebrow')).toHaveText('JALUR TANPA CALO');
  await expect(page.locator('#routeMeta')).not.toContainText('Loading verified route');
  await page.locator('[data-quick-stage="eligibility"]').click();
  await page.locator('.utility-tab[data-view="documents"]').click();
  await expect(page.locator('#documents h2').first()).toHaveText('Asisten Dokumen');
  await expect(page.locator('.field-copilot .eyebrow')).toHaveText('BANTUAN ISI KOLOM');
  await page.goto('/index.html');
  await expect(page.locator('body')).toContainText('Asisten Dokumen');
  await expect(page.locator('footer a[href="privacy.html"]')).toHaveText('Privasi');
  await expect(page.locator('footer a[href="countries.html"]')).toHaveText('Negara');
  await page.goto('/privacy.html');
  await expect(page.locator('h2').first()).toHaveText('Pemberitahuan privasi beta');
  await expect(page).toHaveTitle(/Privasi/);
});

test('PWA icon file is a valid SVG and Indonesian pages explicitly link it', async ({ request, page }) => {
  const response = await request.get('/icon.svg');
  expect(response.status()).toBe(200);
  const icon = await response.text();
  expect(icon.trimStart()).toMatch(/^<svg\s/);
  expect(icon).toContain('viewBox="0 0 64 64"');
  expect(icon).toContain('</svg>');
  for (const path of ['/app.html','/index.html','/beta.html','/privacy.html']) {
    await page.goto(path, { waitUntil:'domcontentloaded' });
    await expect(page.locator('link[rel="icon"]')).toHaveAttribute('href','icon.svg');
  }
});

test('2026 October departure notice fee does not overwrite August or any other cohort', async ({ request }) => {
  const response = await request.get('/data/id_e9_manufacturing_2026_rules.json');
  expect(response.status()).toBe(200);
  const data = await response.json();
  const august = data.fees.find(f => f.id === 'departureFacility2026');
  const october = data.fees.find(f => f.id === 'departureFacilityOct2026');
  expect(august.amountIdr).toBe(8500000);
  expect(august.conditional).toBe(true);
  expect(august.scope).toContain('10 Agustus 2026');
  expect(august.scope).toContain('tidak otomatis');
  expect(october.amountIdr).toBe(8450000);
  expect(october.kind).toBe('fee');
  expect(october.payeeCategory).toBe('official');
  expect(october.conditional).toBe(true);
  expect(october.periodStart).toBe('2026-10-01');
  expect(october.periodEnd).toBe('2026-10-31');
  expect(october.scope).toContain('Hanya periode keberangkatan Oktober 2026');
  expect(october.scope).toContain('bukan biaya pendaftaran EPS');
  expect(october.noticeNumber).toBe('PENG.2649/04.04/PP.02.06/X/2026');
  expect(october.sourceUrl).toBe(
    'https://kp2mi.go.id/gtog-detail/korea/pemberitahuan-penyesuaian-harga-tiket-pada-layanan-pemberangkatan-pekerja-migran-indonesia-program-g-to-g-korea-selatan-pada-periode-bulan-oktober-2026'
  );
});

test('KDCA Q-CODE follows official travelhealth redirect and is not mandatory for everyone', async ({ request }) => {
  const r = await request.get('/data/exact_answer_rules_v1.json');
  expect(r.status()).toBe(200);
  const d = await r.json();
  const record = d.answers.find(x => x.id === 'departure_qcode_current_official');
  expect(record.sourceUrl).toBe('https://travelhealth.kdca.go.kr/travel/cd/qcoInfo.do');
  expect(record.verifiedAt).toBe('2026-10-13');
  expect(record.answer).toContain('tidak boleh dinyatakan wajib bagi setiap pendatang');
  expect(record.answer).toContain('7 hari');
  expect(record.doNotDo.join(' ')).toContain('Jangan menyatakan Q-CODE wajib untuk semua orang');
});


test('Official source warnings remain visible until review signoff and do not auto-authorize applicant', async ({ page, request }) => {
  const res = await request.get('/data/source_review_status.json');
  expect(res.status()).toBe(200);
  const data = await res.json();
  const changed = [
    'labor_standards_wage_statement', 'kdca_qcode_input', 'moel_1350_contact',
    'np_eps_notice_index', 'vn_colab_eps_notices', 'lk_slbfe_home',
    'kg_migrant_home', 'mm_mol_dol_index'
  ];
  expect(data.state).toBe('review_required');
  expect(data.checked).toBe(83);
  expect(data.configured).toBe(84);
  expect(data.autoPublishRules).toBe(false);
  expect(data.reviewRequiredSourceIds).toEqual(changed);
  expect(data.reviewRequiredUrls).toHaveLength(changed.length);
  expect(data.fetchFailureSourceIds).toEqual(['np_eps_notice_index']);
  expect(data.fetchFailureUrls).toEqual(['https://epsnepal.gov.np/notices']);
  expect(data.currentScan.changedSourceIds).toHaveLength(7);
  await page.goto('/app.html', { waitUntil:'domcontentloaded' });
  await expect(page.locator('#freshnessStatus')).toBeVisible();
  await expect(page.locator('#freshnessStatus')).toContainText('8 sumber perlu ditinjau');
  await expect(page.locator('#freshnessStatus')).toContainText('3 sumber terkait Indonesia/Korea, 5 sumber negara lain');
  await expect(page.locator('#freshnessStatus')).toContainText('1 sumber negara lain gagal diakses');
  await expect(page.locator('#freshnessStatus')).toContainText('tidak diubah otomatis');
  await expect(page.locator('#freshnessStatus')).not.toContainText('Tidak ada perubahan resmi yang belum direview');
});

test('2026 Manufacturing Skill Test mandatory with optional Job Capacity Assessment on 320px screen', async ({page, request}) => {
  const official = 'https://kp2mi.go.id/gtog-detail/korea/pengumuman-hasil-ujian-kemampuan-bahasa-korea-eps-topik-ubt-umum-sektor-manufaktur-tahun-2026';
  const route = await (await request.get('/data/id_e9_manufacturing_2026.json')).json();
  const copy = await (await request.get('/data/id_e9_manufacturing_2026_id.json')).json();
  const rules = await (await request.get('/data/exact_answer_rules_v1.json')).json();
  const stage = route.stages.find(s => s.id === 'skill_competency');
  expect(stage).toBeDefined();
  expect(stage.sourceUrl).toBe(official);
  expect(stage.action).toMatch(/mandatory Skill Test/);
  expect(stage.action).toMatch(/optional/);
  expect(copy.skill_competency.action).toMatch(/WAJIB mengikuti Skill Test/);
  expect(copy.skill_competency.action).toMatch(/OPSIONAL/);
  expect(copy.skill_competency.warning).toMatch(/Tidak mengikuti Skill Test menyebabkan gugur/);
  for (const id of ['skill_target_eps_pass_only_2026','skill_stage2_eligibility_2026']) {
    const rule = rules.answers.find(a => a.id === id);
    expect(rule).toBeDefined();
    expect(rule.sourceUrl).toBe(official);
    expect(rule.answer).toContain('OPSIONAL');
    expect(rule.answer).toMatch(/WAJIB/);
  }
  await page.setViewportSize({width:320,height:700});
  await page.goto('/app.html');
  await expect(page.locator('#quickStart')).toBeVisible();
  await page.locator('[data-quick-stage="skill_competency"]').click();
  await expect(page.locator('#nextAction')).toContainText('WAJIB mengikuti Skill Test');
  await expect(page.locator('#nextAction')).toContainText('OPSIONAL');
  await expect(page.locator('#progressText')).toContainText('/ 27');
});

test('offline service-worker cache refreshes 2026 Skill Test guidance and official-source alerts', async ({request}) => {
  const response = await request.get('/sw.js');
  expect(response.status()).toBe(200);
  const script = await response.text();
  expect(script).toContain("const CACHE='kep-v133'");
  for (const name of ['id_e9_manufacturing_2026.json','id_e9_manufacturing_2026_id.json','exact_answer_rules_v1.json','source_review_status.json']) {
    expect(script).toContain("./data/" + name);
  }
  expect(script).toContain('caches.delete');
});

test('Unrecognized new official source is never wrongly excluded from Indonesian warnings', async ({page}) => {
  await page.route('**/data/source_review_status.json', async route => {
    const data=JSON.parse(fs.readFileSync(
      path.join(__dirname,'..','docs','data','source_review_status.json'),'utf8'
    ));
    data.reviewRequiredSourceIds.push('unexpected_new_source_no_scope_approval');
    data.reviewRequiredUrls.push('https://official.example/new-notice');
    await route.fulfill({status:200,contentType:'application/json',json:data});
  });
  await page.goto('/app.html', {waitUntil:'domcontentloaded'});
  await expect(page.locator('#freshnessStatus')).toBeVisible();
  await expect(page.locator('#freshnessStatus')).toContainText('9 sumber perlu ditinjau');
  await expect(page.locator('#freshnessStatus')).toContainText('4 sumber terkait Indonesia/Korea, 5 sumber negara lain');
  await expect(page.locator('#freshnessStatus')).toContainText('Aturan tidak diubah otomatis');
  await expect(page.locator('#freshnessStatus')).not.toContainText('Tidak ada perubahan resmi yang belum direview');
});


test('Manufacturing September 2026 competency upload stays optional and closed, not job_docs', async ({page,request}) => {
  const route = await (await request.get('/data/id_e9_manufacturing_2026.json')).json();
  const copy = await (await request.get('/data/id_e9_manufacturing_2026_id.json')).json();
  const rules = await (await request.get('/data/exact_answer_rules_v1.json')).json();
  const stage=route.stages.find(s=>s.id==='skill_competency');
  const optional=stage.competencyUploadNotice;
  const notice='https://kp2mi.go.id/gtog-detail/korea/pengumuman-persyaratan-unggah-dokumen-kompetensi-peserta-skill-test-ubt-umum-sektor-manufaktur-eps-topik-tahun-2026';
  expect(optional.url).toBe(notice);
  expect(optional.optional).toBe(true);
  expect(optional.notJobApplicationDocuments).toBe(true);
  expect(optional.status).toBe('closed');
  expect(optional.periodStart).toBe('2026-09-21T09:00:00');
  expect(optional.periodEnd).toBe('2026-09-23T13:00:00');
  expect(optional.timeZone).toBe('Asia/Jakarta');
  expect(copy.skill_competency.action).toContain('OPSIONAL');
  expect(copy.skill_competency.action).toContain('SUDAH BERAKHIR');
  const exact=rules.answers.find(a=>a.id==='skill_docs_wait_official_2026');
  expect(exact.sourceUrl).toBe(notice);
  expect(exact.answer).toContain('BERAKHIR');
  expect(exact.answer).toContain('BUKAN daftar dokumen wajib');
  const application=route.stages.find(s=>s.id==='job_application');
  expect(application.brokerReplacement).toBe('held_official_notice');
  await page.setViewportSize({width:320,height:760});
  await page.goto('/app.html');
  await expect(page.locator('#stageCompetencyNotice')).toBeHidden();
  await page.locator('[data-quick-stage="skill_competency"]').click();
  // The full 27-stage journey is intentionally collapsed until requested.
  await page.locator('#allJourneyDetails > summary').click();
  await page.locator('#stageList .stage.current').click();
  await expect(page.locator('#stageCompetencyNotice')).toBeVisible();
  await expect(page.locator('#stageCompetencyNotice')).toHaveAttribute('href',notice);
  await expect(page.locator('#stageAction')).toContainText('SUDAH BERAKHIR');
  await expect(page.locator('#stageWarning')).toContainText('bukan persyaratan wajib');
});


test('2026 Manufacturing voluntary competency upload required annexes are conditional and the window remains CLOSED', async ({page,request}) => {
  const route = await (await request.get('/data/id_e9_manufacturing_2026.json')).json();
  const copy = await (await request.get('/data/id_e9_manufacturing_2026_id.json')).json();
  const rules = await (await request.get('/data/exact_answer_rules_v1.json')).json();
  const stage = route.stages.find(s => s.id === 'skill_competency');
  const opt = stage.competencyUploadNotice;
  const details = opt.conditionalSubmission;
  expect(opt.optional).toBe(true);
  expect(opt.status).toBe('closed');
  expect(details.appliesOnlyIfApplicantChoosesOptionalCompetencyEvidence).toBe(true);
  expect(details.competencyFormRequiredWithAnyUploadedEvidence).toBe(true);
  expect(details.requiredCompetencyFormUrl).toBe('https://kp2mi.go.id/uploads/gtgkorea/images/data_17-09-2026_FORMULIR_UJI_KOMPETENSI.pdf');
  expect(details.officialUploadInstructionsUrl).toContain('JUKNIS_PEMENUHAN_DOKUMEN_UJI_KOMPETENSI_UBT_UMUM_MANUFAKTUR_2026.pdf');
  expect(details.workExperienceFallbackOnlyIfEmployerCannotIssueCertificate).toBe(true);
  expect(details.workExperienceFallbackFormUrl).toContain('FORMULIR_SURAT_KONFIRMASI_DASAR_FAKTUAL_PENGALAMAN_KERJA.pdf');
  expect(details.workExperienceFallbackRequiresTwoNonRelativeSureties).toBe(true);
  expect(details.workExperienceFallbackRequiresEachSuretyIdCopyAndContact).toBe(true);
  expect(details.workExperienceFallbackRequiresWorkContractOrVisaImmigrationEvidence).toBe(true);
  expect(details.closedPeriodMustNotBeReopenedByApp).toBe(true);
  expect(details.notGeneralSkillTestRequirement).toBe(true);
  expect(details.notFinalManufacturingJobApplicationChecklist).toBe(true);
  expect(copy.skill_competency.action).toContain('Formulir Uji Kompetensi');
  expect(copy.skill_competency.action).toContain('dua penjamin');
  expect(copy.skill_competency.action).toContain('SUDAH BERAKHIR');
  const exact=rules.answers.find(x=>x.id==='skill_docs_wait_official_2026');
  expect(exact.answer).toContain('DUA penjamin');
  expect(exact.answer).toContain('BERSYARAT');
  expect(exact.answer).toContain('BERAKHIR');
  expect(route.stages.find(x=>x.id==='job_application').brokerReplacement).toBe('held_official_notice');
  await page.setViewportSize({width:320,height:760});
  await page.goto('/app.html');
  await page.locator('[data-quick-stage="skill_competency"]').click();
  await expect(page.locator('#nextAction')).toContainText('Formulir Uji Kompetensi');
  await expect(page.locator('#nextAction')).toContainText('dua penjamin');
  await expect(page.locator('#nextAction')).toContainText('SUDAH BERAKHIR');
});

test('Indonesia campaign shares the directly verified HTTPS custom origin without an HTTP downgrade', async ({page}) => {
  await page.goto('/');
  await expect(page.locator('meta[property="og:url"]')).toHaveAttribute(
    'content', 'https://www.gdglobal.kr/Korea-Employment-Passport/'
  );
  await expect(page.locator('a[href="beta.html"]').first()).toBeVisible();
});

test('Jan 2026 initial EPS registration annex safeguards are exact while final Manufacturing job_docs remains HELD', async ({page, request}) => {
  const officialGuide='https://kp2mi.go.id/uploads/gtgkorea/images/data_27-01-2026_JUKNIS_PENDAFTARAN_CPMI_G2G_KOREA_UBT_UMUM_MANUFAKTUR_DAN_PERIKANAN_TAHUN_2026.pdf';
  const officialScans='https://kp2mi.go.id/uploads/gtgkorea/images/data_27-01-2026_Contoh_Scan_Persyaratan_Dokumen_Pendaftaran_yang_Benar.pdf';
  const [rules, documentPacks, copy, route] = await Promise.all([
    request.get('/data/exact_answer_rules_v1.json').then(r=>r.json()),
    request.get('/data/document_packs_2026.json').then(r=>r.json()),
    request.get('/data/id_e9_manufacturing_2026_id.json').then(r=>r.json()),
    request.get('/data/id_e9_manufacturing_2026.json').then(r=>r.json()),
  ]);
  const expected={
    registration_one_sector_no_transfer_juknis_2026:officialGuide,
    registration_bankbook_missing_mobile_screenshot_2026:officialScans,
    registration_manufacturing_skl_not_diploma_2026:officialScans,
    registration_fingerprint_location_job_field_final_save_2026:officialGuide,
  };
  for (const [id, url] of Object.entries(expected)) {
    const answer=rules.answers.find(a=>a.id===id);
    expect(answer).toBeDefined();
    expect(answer.sourceUrl).toBe(url);
    expect(answer.scopeType).toBe('route_2026');
    expect(answer.verificationStatus).toBe('verified_2026_official_pdf');
    expect(answer.stages).not.toContain('job_application');
  }
  const scanned=rules.answers.find(a=>a.id==='registration_bankbook_missing_mobile_screenshot_2026');
  expect(scanned.answer).toMatch(/mobile\/internet banking/);
  expect(scanned.answer).toMatch(/atas nama peserta sendiri/);
  const diploma=rules.answers.find(a=>a.id==='registration_manufacturing_skl_not_diploma_2026');
  expect(diploma.answer).toMatch(/SKL tidak diperbolehkan/);
  const sector=rules.answers.find(a=>a.id==='registration_one_sector_no_transfer_juknis_2026');
  expect(sector.answer).toMatch(/tidak dapat diubah/);
  const pack=documentPacks.packs.find(x=>x.id==='registration');
  expect(pack.message).toMatch(/bukan daftar dokumen final/);
  expect(pack.items.find(x=>x.id==='reg_diploma').note).toMatch(/SKL tidak diterima/);
  expect(pack.items.find(x=>x.id==='reg_bankbook').note).toMatch(/screenshot mobile\/internet banking/);
  expect(copy.registration.action).toContain('SUDAH BERAKHIR');
  expect(copy.registration.action).toContain('tidak dapat pindah sektor');
  expect(route.stages.find(x=>x.id==='job_application').brokerReplacement).toBe('held_official_notice');
  expect(route.stages.find(x=>x.id==='skill_competency').competencyUploadNotice.status).toBe('closed');
  await page.setViewportSize({width:320,height:720});
  await page.goto('/app.html');
  await page.locator('[data-quick-stage="registration"]').click();
  await expect(page.locator('#nextAction')).toContainText('SUDAH BERAKHIR');
  await expect(page.locator('#nextAction')).toContainText('tidak dapat pindah sektor');
  await page.locator('[data-quick-stage="document_verify"]').click();
  await expect(page.locator('#nextAction')).toContainText('SKL tidak menggantikan ijazah');
});
