#!/usr/bin/env node
'use strict';
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const vm=require('node:vm');
const ROOT=path.resolve(__dirname,'..');
const data=(p)=>JSON.parse(fs.readFileSync(path.join(ROOT,p),'utf8'));
const js=fs.readFileSync(path.join(ROOT,'docs/app-runtime.js'),'utf8');
const source=data('docs/data/source_review_status.json');
const watch=data('research/source_reviews/indonesia_daily_readonly_2026-10-17.json');
const html=data('research/source_reviews/indonesia_m21_original_html_audit_2026-10-17.json');
const answers=data('docs/data/exact_answer_rules_v1.json').answers;
const channels=data('docs/data/official_help_channels_v1.json').channels;
const claims=[
 ['minimum_wage','minimum_wage_2026'],
 ['labor_standards_wage_statement','payslip_required_items'],
 ['moel_wage_arrears_2026','labor_unpaid_wage_first_action_current'],
 ['kdca_qcode_input','departure_qcode_current_official'],
 ['moel_1350_contact','labor_1350_scope_current']
];
const start=js.indexOf('function latestReadOnlyObservation(){');
const end=js.indexOf('\nfunction sourceHasFetchWarning(',start);
assert(start>=0&&end>start);
const code=js.slice(start,end);
function createGuard(input){
 const ctx={sourceReviewStatus:input};
 vm.createContext(ctx);
 vm.runInContext(code,ctx,{timeout:1000});
 return (url)=>vm.runInContext('sourceNeedsReview('+JSON.stringify(url)+')',ctx,{timeout:1000});
}
const guard=createGuard(source);
assert.equal(source.latestReadOnlyObservation.checked,84);
assert.equal(watch.unacceptedBaselineDriftCount,12);
assert.equal(html.koreaOfficialText.length,5);
for(const pair of claims){
 const id=pair[0],claimId=pair[1];
 const alert=watch.pendingReviews.find(x=>x.id===id);
 const observed=html.koreaOfficialText.find(x=>x.id===id);
 const item=answers.find(x=>x.id===claimId);
 assert(alert&&observed&&item,'missing claim binding '+id);
 assert.equal(observed.normalizedTextSha256,alert.observedSha256);
 assert.equal(observed.matches20261017SourceMonitorSha,true);
 assert.equal(alert.semanticReview,'pending');
 assert.equal(guard(alert.url),true,'pending source escaped watch '+id);
 assert.equal(guard(item.sourceUrl),true,'app claim escaped watch '+claimId);
}
assert.equal(guard('https://travelhealth.kdca.go.kr/travel/cd/qcoInfo.do'),true);
assert.equal(guard('https://qcode.kdca.go.kr/qco/cd/codeInput2.do'),true);
assert.equal(guard('https://www.minimumwage.go.kr/index.jsp'),true);
assert.equal(guard('https://example.net/unrelated'),false);
const help=channels.find(x=>x.id==='moel_1350');
assert(help&&help.hours.includes('berbayar')&&help.hours.includes('09:00')&&help.hours.includes('18:00'));
assert.equal(help.phones[0].href,'tel:1350');
const wage=answers.find(x=>x.id==='minimum_wage_2026');
assert(wage.answer.includes('10.320')&&wage.answer.includes('2.156.880'));
assert(wage.writeExactly.includes('209 jam'));
const qcode=answers.find(x=>x.id==='departure_qcode_current_official');
assert(qcode.answer.includes('tidak boleh dinyatakan wajib bagi setiap'));
assert.equal(qcode.sourceUrl,'https://travelhealth.kdca.go.kr/travel/cd/qcoInfo.do');
const mutations=[
 x=>x.latestReadOnlyObservation.checked=83,
 x=>x.latestReadOnlyObservation.hashBaselineAutoAccepted=true,
 x=>x.latestReadOnlyObservation.betaAccess='open',
 x=>x.latestReadOnlyObservation.unacceptedBaselineDriftCount=11,
 x=>x.state='clean'
];
mutations.forEach((mutate,index)=>{
 const altered=JSON.parse(JSON.stringify(source));mutate(altered);
 assert.equal(createGuard(altered)('https://example.net/unrelated'),true,'invalid watch escaped fail-closed case '+index);
});
const expected=new Set(claims.map(x=>x[0]));
assert.deepEqual(new Set(watch.pendingReviews.filter(x=>x.scope==='korea_shared').map(x=>x.id)),expected);
assert.notEqual(wage.sourceUrl,'https://moel.go.kr/news/enews/report/enewsView.do?bbs_id=12&news_seq=18144&pageIndex=1&pageUnit=10&searchField=3');
console.log('M27_KOREA_OFFICIAL_CLAIM_GUARD_PASS 5_of_5_app_sources_blocked 2_qcode_aliases 5_bad_watch_cases 1350_paid_phone 2026_wage_209h');
