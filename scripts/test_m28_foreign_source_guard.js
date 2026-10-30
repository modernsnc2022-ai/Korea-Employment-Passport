#!/usr/bin/env node
'use strict';
// M28 regression: actual runtime still blocks all seven non-Indonesia drifts.
// This checks source/review routing, NEVER automatically approves foreign policy.
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
const path=require('node:path');
const ROOT=path.resolve(__dirname,'..');
const data=(name)=>JSON.parse(fs.readFileSync(path.join(ROOT,name),'utf8'));
const watch=data('research/source_reviews/indonesia_daily_readonly_2026-10-17.json');
const work=data('research/source_reviews/indonesia_m26_unsigned_review_handoff_2026-10-17.json');
const runtime=fs.readFileSync(path.join(ROOT,'docs/app-runtime.js'),'utf8');
const status=data('docs/data/source_review_status.json');
const main=data('docs/data/id_e9_manufacturing_2026.json');
const begin=runtime.indexOf('function latestReadOnlyObservation(){');
const end=runtime.indexOf('\nfunction sourceHasFetchWarning(',begin);
assert(begin>=0&&end>begin);
function blocked(condition,url){
 const ctx={sourceReviewStatus:condition};
 vm.createContext(ctx);vm.runInContext(runtime.slice(begin,end),ctx,{timeout:1000});
 return vm.runInContext('sourceNeedsReview('+JSON.stringify(url)+')',ctx,{timeout:1000});
}
const seven=watch.pendingReviews.filter(x=>x.scope!=='korea_shared');
assert.equal(seven.length,7);
assert.equal(seven.filter(x=>x.scope==='multi_country_eps_schedule').length,2);
assert.equal(seven.filter(x=>x.scope==='other_country').length,5);
assert.equal(watch.groupCounts.korea_shared,5);
assert.equal(status.latestReadOnlyObservation.unacceptedBaselineDriftCount,12);
for(const row of seven){
 assert.equal(row.semanticReview,'pending');
 assert.notEqual(row.acceptedBaselineSha256,row.observedSha256);
 assert.equal(blocked(status,row.url),true,'foreign/HRD source bypassed changed-source warning '+row.id);
 const queue=work.tasks.find(x=>x.id==='SRC:'+row.id);
 assert(queue&&queue.decision==='pending'&&queue.humanReviewer===null);
 assert.equal(queue.scope,row.scope);
 assert.equal(queue.authorizesRelease,false);
}
for(const url of [
 'https://epstopik.hrdkorea.or.kr/epstopik/abot/exam/selectSechduleDescList.do?lang=en',
 'https://epstopik.hrdkorea.or.kr/epstopik/pass/candidate/functionalLevelCandidateList.do?lang=en'
])assert.equal(blocked(status,url),true,'HRD multi-country schedule must stay visible');
const job=main.stages.find(x=>x.id==='job_application');
assert.equal(job.brokerReplacement,'held_official_notice');
assert.equal(job.officialActionUrl,'https://kp2mi.go.id/gtog-korea/pengumuman');
const mutated=[
 x=>x.latestReadOnlyObservation.checked=83,
 x=>x.latestReadOnlyObservation.unacceptedBaselineDriftCount=11,
 x=>x.latestReadOnlyObservation.hashBaselineAutoAccepted=true,
 x=>x.latestReadOnlyObservation.betaAccess='open',
 x=>x.latestReadOnlyObservation.groupCounts.other_country=0
];
for(const mutate of mutated){
 const altered=JSON.parse(JSON.stringify(status));mutate(altered);
 assert.equal(blocked(altered,'https://example.com/not-monitored'),true,'malformed monitor did not fail closed');
}
console.log('M28_RUNTIME_FOREIGN_HRD_REVIEW_PASS 2_multi_country_HRD 5_foreign_pending 7_warnings_active 5_corrupt_monitors_rejected beta_hold');
