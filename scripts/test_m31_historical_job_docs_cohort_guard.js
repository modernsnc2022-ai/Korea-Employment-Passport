#!/usr/bin/env node
'use strict';
// M31: old-cycle online job application files MUST never be an approved
// document pack for the 2026 General Manufacturing cohort.
const fs=require('node:fs');
const path=require('node:path');
const assert=require('node:assert/strict');
const ROOT=path.resolve(__dirname,'..');
const read=(f)=>JSON.parse(fs.readFileSync(path.join(ROOT,f),'utf-8'));
const route=read('docs/data/id_e9_manufacturing_2026.json');
const packs=read('docs/data/document_packs_2026.json');
const m30=read('research/source_reviews/indonesia_m30_post_skill_notice_candidates_corrected_r1_2026-10-17.json');
const m29=read('research/source_reviews/indonesia_m29_slbfe_and_kp2mi_context_2026-10-17.json');
const sign=read('recruitment/ID_BETA_SOURCE_SIGNOFF_20261017.json');
const wanted='https://kp2mi.go.id/gtog-korea/pengumuman';
const historical=[
 'https://kp2mi.go.id/gtog-detail/korea/pengumuman-hasil-akhir-kelulusan-eps-topik-ubt-umum-sektor-manufaktur-program-g-to-g-ke-korea-selatan-tahun-2025',
 'https://kp2mi.go.id/gtog-detail/korea/pengumuman-pembagian-sertifikat-kelulusan-digital-e-sertifikat-ujian-eps-topik-ubt-umum-sektor-manufaktur-dan-pengajuan-lamaran-online-calon-pekerja-migran-indonesia-program-g-to-g-korea-tahun-2025'
];
function safe(r,p,m,prior,s){
 assert.equal(r.country,'ID');assert.equal(r.visa,'E-9');
 assert.equal(r.sector,'manufacturing');assert.equal(r.cycle,2026);
 const job=r.stages.find(x=>x.id==='job_application');
 const packet=p.packs.find(x=>x.id==='job_application_manufacturing');
 assert(job&&packet);
 assert.equal(job.brokerReplacement,'held_official_notice');
 assert.equal(job.sourceUrl,wanted);
 assert.equal(job.officialActionUrl,wanted);
 assert.equal(packet.status,'awaiting_sector_notice');
 assert.equal(packet.sourceUrl,wanted);
 assert.deepEqual(packet.items,[]);
 assert(!historical.some(u=>JSON.stringify(job).includes(u)||JSON.stringify(packet).includes(u)),'old 2025 job doc source wrongly used');
 assert.equal(m.manufacturingExplicitFinalOnlineApplicationTitles,0);
 assert.equal(m.jobDocs,'hold');assert.equal(m.publicBetaAccess,'hold');
 assert.equal(m.correctedCandidateCount,9);
 assert.equal(prior.kp2miOfficialNoticePagesRead,7);
 assert.equal(prior.finalOnlineManufacturingJobDocsOfficialEvidenceEstablished,false);
 assert.equal(s.status,'pending_manual_source_signoff');
 assert.equal(s.reviewer,null);assert.equal(s.betaAccess,'hold');
 return true;
}
safe(route,packs,m30,m29,sign);
const attacks=[
 x=>x.r.cycle=2025,
 x=>x.r.stages.find(a=>a.id==='job_application').brokerReplacement='verified',
 x=>x.r.stages.find(a=>a.id==='job_application').sourceUrl=historical[1],
 x=>x.r.stages.find(a=>a.id==='job_application').officialActionUrl=historical[1],
 x=>x.p.packs.find(a=>a.id==='job_application_manufacturing').sourceUrl=historical[1],
 x=>x.p.packs.find(a=>a.id==='job_application_manufacturing').status='verified',
 x=>x.p.packs.find(a=>a.id==='job_application_manufacturing').items.push({id:'2025_mcu',required:true}),
 x=>x.m.manufacturingExplicitFinalOnlineApplicationTitles=1,
 x=>x.m.jobDocs='verified',
 x=>x.m.publicBetaAccess='open',
 x=>x.prior.finalOnlineManufacturingJobDocsOfficialEvidenceEstablished=true,
 x=>x.s.reviewer='fabricated reviewer'
];
for(const mutate of attacks){
 const obj={r:structuredClone(route),p:structuredClone(packs),m:structuredClone(m30),prior:structuredClone(m29),s:structuredClone(sign)};
 mutate(obj);assert.throws(()=>safe(obj.r,obj.p,obj.m,obj.prior,obj.s));
}
console.log('M31_2025_2026_JOB_DOCS_COHORT_GUARD_PASS 12_negative_mutations 2026_exact_documents_empty 2025_sources_not_imported beta_hold');
