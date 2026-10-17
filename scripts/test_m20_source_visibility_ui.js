#!/usr/bin/env node
/* M20. DOM-free verification of the exact Indonesia app official-source panel.
   This executes the shipped render/URL-trust helpers in a restricted VM context.
   No network access, browser automation, or production deploy. */
'use strict';
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const root = path.resolve(__dirname, '..');
const status = JSON.parse(fs.readFileSync(path.join(root,'docs/data/source_review_status.json'),'utf8'));
const runtime = fs.readFileSync(path.join(root,'docs/app-runtime.js'),'utf8');
const begin = runtime.indexOf('function latestReadOnlyObservation(){');
const end = runtime.indexOf('function selectedScope(stageId){',begin);
assert.ok(begin>0 && end>begin, 'source-review UI helpers must be present in production JS');
const extracted = runtime.slice(begin,end);

function render(model){
  const box={hidden:true,className:'',innerHTML:'',textContent:'',
    classList:{names:[],add(name){this.names.push(name);}}};
  const panel={open:false};
  const sandbox={
    sourceReviewStatus:JSON.parse(JSON.stringify(model)),
    route:{lastVerified:'2026-10-06'},
    freshnessPolicy:{monitorCadence:'every 6 hours'},
    document:{querySelector:()=>panel},
    $:()=>box,
    escapeHtml:(x)=>String(x).replace(/[&<>"']/g,c=>(
      {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#039;'}[c]))
  };
  vm.createContext(sandbox);
  vm.runInContext(extracted,sandbox,{filename:'app-runtime.js:official-source-status'});
  vm.runInContext('renderFreshnessStatus()',sandbox);
  return {
    html:box.innerHTML,hidden:box.hidden,classes:box.classList.names,
    opened:panel.open,
    needsReview:(url)=>vm.runInContext('sourceNeedsReview('+JSON.stringify(url)+')',sandbox),
    hasFetchWarning:(url)=>vm.runInContext('sourceHasFetchWarning('+JSON.stringify(url)+')',sandbox)
  };
}

const current=render(status);
assert.equal(status.state,'review_required');
assert.equal(status.checked,83); // Historical record is not rewritten as current.
assert.equal(status.detectedAt,'2026-10-14');
assert.equal(status.latestReadOnlyObservation.checked,84);
assert.equal(status.latestReadOnlyObservation.observedAtDate,'2026-10-17');
assert.equal(status.latestReadOnlyObservation.humanSemanticReviewApproved,false);
assert.equal(status.latestReadOnlyObservation.betaAccess,'hold');
assert.ok(current.html.includes('2026-10-17: 84/84'));
assert.ok(current.html.includes('12 sumber berbeda'));
assert.ok(current.html.includes('5 sumber Korea'));
assert.ok(current.html.includes('2 sumber jadwal HRD Korea'));
assert.ok(current.html.includes('5 sumber negara lain'));
assert.ok(current.html.includes('2026-10-14'));
assert.ok(current.html.includes('83/84'));
assert.ok(current.html.includes('Persetujuan manual: belum selesai'));
assert.ok(current.classes.includes('review-required')&&current.opened);
assert.equal(current.hidden,false);

// New alerts not present in the historic eight must now block exact answers.
assert.equal(current.needsReview('https://www.minimumwage.go.kr/index.jsp'),true);
assert.equal(current.needsReview('https://epstopik.hrdkorea.or.kr/epstopik/abot/exam/selectSechduleDescList.do?lang=en'),true);
assert.equal(current.needsReview('https://epsnepal.gov.np/notices'),true);
assert.equal(current.needsReview('https://unrelated.gov.example/other'),false);
// An October 14 Nepal HTTP failure does not count as an October 17 failed fetch.
assert.equal(current.hasFetchWarning('https://epsnepal.gov.np/notices'),false);

const past=JSON.parse(JSON.stringify(status));
delete past.latestReadOnlyObservation;
const historical=render(past);
assert.ok(historical.html.includes('8 sumber perlu ditinjau'));
assert.ok(historical.html.includes('1 sumber negara lain gagal'));
assert.equal(historical.hasFetchWarning('https://epsnepal.gov.np/notices'),true);
assert.equal(historical.needsReview('https://www.minimumwage.go.kr/index.jsp'),false);

for(const tamper of [
  m=>m.latestReadOnlyObservation.checked=83,
  m=>m.latestReadOnlyObservation.observedAtDate='2026-10-17<script>',
  m=>m.latestReadOnlyObservation.humanSemanticReviewApproved=true,
  m=>m.latestReadOnlyObservation.hashBaselineAutoAccepted=true,
  m=>m.latestReadOnlyObservation.betaAccess='open',
  m=>m.latestReadOnlyObservation.authorizesRelease=true,
  m=>m.latestReadOnlyObservation.reviewRequiredUrls.pop(),
  m=>m.latestReadOnlyObservation.groupCounts.korea_shared=0,
  m=>m.state='clean'
]){
  const malicious=JSON.parse(JSON.stringify(status));
  tamper(malicious);
  const blocked=render(malicious);
  assert.ok(blocked.html.includes('BUKTI PEMANTAUAN TIDAK VALID'),
    'corrupt state must fail closed in public UI');
  assert.equal(blocked.needsReview('https://unrelated.gov.example/other'),true,
    'corrupt latest evidence must not unblock any source-dependent exact answer');
  assert.equal(blocked.hasFetchWarning('https://epsnepal.gov.np/notices'),true);
}
console.log('M20_SOURCE_VISIBILITY_UI_PASS latest_84of84_vs_historical_83of84; 12_pending; 9_fail_closed_UI_mutations; no_public_release');
