#!/usr/bin/env node
'use strict';
// M25: evaluate the *shipped* HTML-stage pre-submit guard in an isolated VM.
const fs=require('node:fs');
const vm=require('node:vm');
const assert=require('node:assert/strict');
const path=require('node:path');
const ROOT=path.resolve(__dirname,'..');
const read=(p)=>JSON.parse(fs.readFileSync(path.join(ROOT,p),'utf8'));
const JS=fs.readFileSync(path.join(ROOT,'docs/app-runtime.js'),'utf8');
const OFFICIAL='https://kp2mi.go.id/gtog-korea/pengumuman';
const route=read('docs/data/id_e9_manufacturing_2026.json');
const packs=read('docs/data/document_packs_2026.json');
const exact=read('docs/data/exact_answer_rules_v1.json');
const m24=read('research/source_reviews/indonesia_m24_manufacturing_title_scope_2026-10-17.json');
const m21=read('research/source_reviews/indonesia_m21_original_html_audit_2026-10-17.json');
const source=read('docs/data/source_review_status.json');
const pick=(name,end)=>{
  const i=JS.indexOf('function '+name+'(');
  const j=JS.indexOf(end,i);
  assert(i>=0&&j>i,'exact runtime function not found: '+name);
  return JS.slice(i,j);
};
const funcs=[
  pick('safeDocumentPack','\nfunction documentPackForStage('),
  pick('documentPackForStage','\nfunction renderDocumentScopePicker('),
  pick('evaluatePreSubmit',"\n$('preSubmitBtn').addEventListener"),
  pick('exactVerificationLabel','\nfunction renderExactAnswers(')
].join('\n');
function vmCheck(packsNow,routeStage,reviewSource=false){
  const ctx={
    documentPacks:{packs:packsNow},
    sourceNeedsReview:()=>reviewSource,
    selectedScope:()=>'',
    bqcStageStats:()=>({items:[]}),
    consistencyRisk:{hasMismatch:false,stageId:''},
    wizardReviewStats:()=>({total:0,missing:0}),
    scopeOptionsForStage:()=>[],
    read:()=>[],
    KEYS:{docs:'kep.docs'}
  };
  vm.createContext(ctx);
  vm.runInContext(funcs,ctx,{timeout:1000});
  ctx.currentStage=routeStage;
  return {result:vm.runInContext('evaluatePreSubmit(currentStage)',ctx,{timeout:1000}),
          label:(status)=>vm.runInContext('exactVerificationLabel({verificationStatus:'+JSON.stringify(status)+'})',ctx,{timeout:1000})};
}
function contract(r,p,idx){
  assert.equal(r.country,'ID');assert.equal(r.visa,'E-9');
  assert.equal(r.sector,'manufacturing');assert.equal(r.cycle,2026);
  const stage=r.stages.find(x=>x.id==='job_application');
  const pack=p.packs.find(x=>x.id==='job_application_manufacturing');
  assert(stage&&pack,'target job stage & document pack');
  assert.equal(stage.brokerReplacement,'held_official_notice');
  assert.equal(stage.sourceUrl,OFFICIAL);
  assert.equal(stage.officialActionUrl,OFFICIAL);
  assert(stage.officialActionLabel.includes('Pengumuman G-to-G Korea'));
  assert(JS.includes("'registration','document_verify','job_application','visa_docs'"),'job stage still uses pre-submit gate');
  assert(JS.includes('const check=evaluatePreSubmit(activeStage);'),'stage submit button still enforces gate');
  assert.equal(pack.status,'awaiting_sector_notice');
  assert.equal(pack.sourceUrl,OFFICIAL);
  assert(Array.isArray(pack.items)&&pack.items.length===0,'no invented document checklist');
  assert(pack.appliesTo.includes('job_application'));
  assert.equal(idx.observedAtJakartaDate,'2026-10-17');
  assert.equal(idx.generalManufacturingTitlesCount,7);
  assert.equal(idx.generalManufacturingFinalOnlineJobApplicationTitleCount,0);
  assert.equal(idx.otherCohortOnlineApplicationNotices.length,3);
  assert.equal(idx.ambiguousGenericApplicationTitles.length,0);
  assert.equal(idx.jobDocs,'hold');assert.equal(idx.betaAccess,'hold');
  assert.equal(idx.humanSemanticReviewApproved,false);
  assert.equal(idx.authorizesRelease,false);
  const originalSet=new Set(m21.manufacturingNoticeHtml.map(x=>x.url));
  assert.equal(originalSet.size,7);
  assert(idx.generalManufacturingTitles.every(x=>originalSet.has(x.url)));
  assert.equal(source.state,'review_required');
  assert.equal(source.latestReadOnlyObservation.humanSemanticReviewApproved,false);
  const answer=exact.answers.find(x=>x.id==='job_application_manufacturing_2026_wait_notice');
  assert(answer&&answer.verificationStatus==='hold_for_official_manufacturing_notice');
  assert.equal(answer.sourceUrl,OFFICIAL);
  return {stage,pack};
}
const {stage,pack}=contract(route,packs,m24);
const baseline=vmCheck(packs.packs,stage);
assert.equal(baseline.result.ready,false);
assert(baseline.result.issues.some(x=>x.includes('Daftar dokumen lamaran online Manufaktur 2026')));
assert(baseline.result.issues.some(x=>x.includes('Checklist dokumen tahap ini')));
const poisoned=JSON.parse(JSON.stringify(packs.packs));
poisoned.find(x=>x.id===pack.id).status='verified';
assert.equal(vmCheck(poisoned,stage).result.ready,false,'route-level hold is independent of checklist status');
assert.equal(vmCheck(poisoned,stage,true).result.ready,false,'source drift cannot clear route-level HOLD');
assert(vmCheck(packs.packs,stage).label('verified_cross_notice_platform_baseline_not_manufacturing_exact').includes('BUKAN'));
assert(vmCheck(packs.packs,stage).label('verified_current_cycle_identity_safety_baseline_not_manufacturing_field_map').includes('BUKAN'));
assert(vmCheck(packs.packs,stage).label('hold_for_official_manufacturing_notice').includes('HOLD'));
const attacks=[
  x=>x.r.stages.find(a=>a.id==='job_application').sourceUrl='https://kp2mi.go.id/gtog-korea/info',
  x=>x.r.stages.find(a=>a.id==='job_application').officialActionUrl='https://kp2mi.go.id/gtog-korea/info',
  x=>x.p.packs.find(a=>a.id==='job_application_manufacturing').sourceUrl='https://kp2mi.go.id/gtog-korea/info',
  x=>x.r.stages.find(a=>a.id==='job_application').brokerReplacement='verified',
  x=>x.p.packs.find(a=>a.id==='job_application_manufacturing').status='verified',
  x=>x.p.packs.find(a=>a.id==='job_application_manufacturing').items.push({id:'invented',required:true}),
  x=>x.idx.generalManufacturingFinalOnlineJobApplicationTitleCount=1,
  x=>x.idx.jobDocs='approved',
  x=>x.idx.humanSemanticReviewApproved=true,
  x=>x.idx.betaAccess='open',
  x=>x.idx.otherCohortOnlineApplicationNotices.pop(),
  x=>x.idx.generalManufacturingTitles[0].url='https://evil.example/imposter'
];
for (const mutate of attacks) {
  const x={r:JSON.parse(JSON.stringify(route)),p:JSON.parse(JSON.stringify(packs)),idx:JSON.parse(JSON.stringify(m24))};
  mutate(x);assert.throws(()=>contract(x.r,x.p,x.idx));
}
assert.equal((JSON.stringify(route).match(/https:\/\/kp2mi\.go\.id\/gtog-korea\/info/g)||[]).length,0);
assert.equal((JSON.stringify(packs).match(/https:\/\/kp2mi\.go\.id\/gtog-korea\/info/g)||[]).length,1,'preserve unrelated visa pack link');
console.log('M25_JOB_APPLICATION_REAL_RUNTIME_FAIL_CLOSED_PASS official_latest_notice_url=3/3 route_HOLD_even_with_poisoned_pack 12_mutations status_labels=3 beta_HOLD');
