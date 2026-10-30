const {test,expect}=require('@playwright/test');
const fs=require('fs');
const path=require('path');

test('M45 clean Indonesian public entry keeps operator diagnostics private and honest numbers',async({page})=>{
  await page.goto('/app.html');
  await expect(page.locator('#progressText')).toContainText('/ 27');
  await expect(page.locator('#freshnessStatus')).toBeHidden();
  await expect(page.locator('.trust-panel')).not.toHaveAttribute('open','');
  await expect(page.locator('#cycleStatus')).toContainText('Pendaftaran baru Manufaktur 2026 telah ditutup.');
  expect((await page.locator('#cycleStatus').innerText()).match(/telah ditutup/g)).toHaveLength(1);
  await expect(page.locator('#routeMeta')).not.toContainText('paket ');
  await expect(page.locator('#routeMeta')).toContainText('pengumuman resmi');
  expect(await page.locator('body').innerText()).not.toMatch(/SUMBER RESMI MASIH MENUNGGU TINJAUAN MANUSIA|Pemantauan teknis|baseline yang terakhir disetujui|sumber Nepal/);
  // On first visit, choose a stage before opening the optional detail panel.
  await page.locator('[data-quick-stage="eligibility"]').click();
  await page.locator('.trust-panel > summary').click();
  const stats=await page.evaluate(()=>{
    const stageIds=route.stages.map(s=>s.id);
    const all=stageIds.flatMap(id=>bqcQuestionsForStage(id));
    return {all:all.length,answered:all.filter(x=>x.resolved).length,unresolved:all.filter(x=>!x.resolved).length,blockers:all.filter(x=>!x.resolved&&x.blocksZeroBrokerReady).length};
  });
  await expect(page.locator('#bqcStatus')).toContainText(stats.answered+'/'+stats.all);
  await expect(page.locator('#bqcStatus')).toContainText(stats.unresolved+' masih perlu konfirmasi');
  await expect(page.locator('#bqcStatus')).toContainText(stats.blockers+' penting');
  expect(await page.locator('#freshnessStatus').innerText()).toBe('');
});

test('M45 review pending remains held despite operator panel being hidden',async({page,request})=>{
  const reply=await request.get('/data/document_packs_2026.json');
  const docs=await reply.json();
  const pack=docs.packs.find(x=>x.id==='job_application_manufacturing');
  expect(pack).toMatchObject({status:'awaiting_sector_notice',items:[]});
  await page.goto('/app.html');
  await expect(page.locator('#progressText')).toContainText('/ 27');
  await expect(page.locator('#freshnessStatus')).toBeHidden();
  const blocked=await page.evaluate(()=>({
    exactStatus:documentPackForStage('job_application')?.status,
    officialSourceHeld:sourceNeedsReview('https://kp2mi.go.id/gtog-korea/pengumuman')
  }));
  expect(blocked.exactStatus).toBe('awaiting_sector_notice');
  // Even where no specific source drift is observed, the exact checklist is held.
});

test('M45 optional monitoring endpoint failure stays safely fail-closed without technical scare banner',async({page})=>{
  let tries=0;
  await page.route('**/data/source_review_status.json',route=>{tries++;return route.abort('failed')});
  await page.goto('/app.html');
  await expect(page.locator('#progressText')).toContainText('/ 27',{timeout:14000});
  await expect(page.locator('#freshnessStatus')).toBeHidden();
  expect(await page.evaluate(()=>sourceNeedsReview('https://kp2mi.go.id/gtog-korea/pengumuman'))).toBe(true);
  expect(tries).toBe(3);
});

test('M45 mobile public first impression avoids internal logs and horizontal overflow',async({page})=>{
  await page.setViewportSize({width:320,height:720});
  await page.goto('/app.html');
  await expect(page.locator('#progressText')).toContainText('/ 27');
  await expect(page.locator('#freshnessStatus')).toBeHidden();
  expect(await page.evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth+1)).toBe(true);
  await expect(page.locator('#cycleStatus a')).toHaveAttribute('href',/^https:\/\//);
  await expect(page.locator('.trust-panel')).not.toHaveAttribute('open','');
});
