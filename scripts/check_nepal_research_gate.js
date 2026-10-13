#!/usr/bin/env node
/**
 * KEP Nepal E-9 Manufacturing 2026 research/beta safety preflight.
 * Node stdlib only; does not contact networks, collect applicant data or launch beta.
 */
'use strict';

const fs = require('node:fs');
const path = require('node:path');
const ROOT = path.resolve(__dirname, '..');
const DATA = path.join(ROOT, 'docs', 'data');
const load = name => JSON.parse(fs.readFileSync(path.join(DATA, name), 'utf8'));
const fail = [];
function assert(condition, label) { if (!condition) fail.push(label); }
const ID = 'np-e9-manufacturing-2026';
const pack = load('np_e9_manufacturing_2026.json');
const ne = load('np_e9_manufacturing_2026_ne.json');
const readiness = load('np_stage_readiness_2026.json');
const docs = load('np_document_packs_2026.json');
const dashboard = load('country_readiness_dashboard_2026.json');
const ledger = load('np_notice_provenance_2026.json');
const supplements = load('np_registration_notices_2026.json');

assert(pack.country === 'NP' && pack.visa === 'E-9' && pack.sector === 'manufacturing', 'Nepal route must be E-9 Manufacturing');
assert(pack.cycle === 2026 && pack.lifecycle === 'research_hold', 'Nepal 2026 pack must stay research_hold');
assert(pack.publicAvailability === 'preview_only' && pack.safety?.betaIntakeOpen === false, 'Nepal applicant beta and service availability must remain blocked');
assert(readiness.routeId === ID && docs.routeId === ID && ledger.routeId === ID && supplements.routeId === ID, 'Nepal data routeId mismatch');
assert(readiness.cycle === 2026 && readiness.betaReadiness?.status === 'blocked', 'Nepal stage readiness must remain blocked');
assert(ledger.policy?.betaAccess === 'blocked' && ledger.policy?.allowDeadlineExtensionInference === false &&
  ledger.policy?.allowDepartureToPromote2026ApplicationStages === false &&
  ledger.policy?.allowCrossSectorPromotion === false, 'Nepal notice provenance safety flags changed');
assert(supplements.policy?.deadlineExtensionVerified === false &&
  supplements.policy?.autoSupersedePrimaryRules === false, 'Unreviewed 2026 registration supplements cannot supersede primary notice');
const dashboardNP = dashboard.rows?.find(x => x.country === 'NP');
assert(dashboardNP?.routeId === ID && dashboardNP.packState === 'research_hold' &&
  dashboardNP.betaState === 'blocked', 'Public Nepal dashboard must stay blocked');

const stages = pack.stages || [];
const ids = new Set();
for (const stage of stages) {
  assert(typeof stage.id === 'string' && !ids.has(stage.id), 'Duplicate/missing Nepal stage ID ' + stage.id);
  ids.add(stage.id);
  assert(ne[stage.id]?.title && ne[stage.id]?.action, 'Missing Nepali translation for ' + stage.id);
  assert(typeof stage.sourceUrl === 'string' && stage.sourceUrl.startsWith('https://'), 'Stage requires official source ' + stage.id);
  if (stage.id === 'psychology_pre_job' || stage.id === 'mcu3_departure') {
    assert(stage.supportState.startsWith('no_separate_step_verified'), 'Do not import Indonesia-only medical/psychological step ' + stage.id);
  }
}
assert(stages.length >= 20, 'Unexpectedly incomplete Nepal route');

const current = readiness.currentCohort || {};
assert(current.recruitmentRegistration?.status === 'closed_verified', 'Current Nepal application is not open');
assert(current.recruitmentRegistration?.crossSourceSchedule?.deadlineExtensionVerified === false, 'HRD vs Nepal deadline extension must remain unresolved');
assert(current.recruitmentRegistration?.crossSourceSchedule?.localPrimaryRegistrationPeriod === '2026-07-27 through 2026-08-02', 'Nepal local-primary dates changed without review');
assert(current.recruitmentRegistration?.crossSourceSchedule?.hrdRegistrationPeriod === '2026-07-27 through 2026-08-05', 'HRD cross-source dates need separate provenance');
for (const key of ['epsTopikResult','skillCompetency','medicalAndJobApplication']) {
  assert(current[key]?.status === 'awaiting_current_cohort_notice', 'An unknown current-cohort stage has been promoted: ' + key);
}
assert(current.postSelectionVisaDeparture?.status === 'research_pending_current_cohort_scope', 'Downstream Nepal scope cannot be assumed current');

const noticeIDs = new Set();
const VALID = new Set(['verified_current_primary','supplementary_unreviewed','prior_2025_cohort','cohort_not_linked','other_2026_program']);
for (const n of ledger.notices || []) {
  assert(!noticeIDs.has(n.id), 'Duplicate Nepal government notice: ' + n.id);
  noticeIDs.add(n.id);
  assert(VALID.has(n.applicability), 'Unsupported notice type ' + n.id);
  assert(/^2026-[0-9]{2}-[0-9]{2}$/.test(n.date) && n.url?.startsWith('https://epsnepal.gov.np/postdetails/'), 'Invalid notice date/url ' + n.id);
  assert(n.title && n.ruleImpact && n.reviewState, 'Missing notice provenance ' + n.id);
  if (n.applicability === 'verified_current_primary') {
    assert(n.id === 'np_2026_first_phase_primary' &&
      n.cohort === '2026_first_phase_manufacturing' &&
      n.reviewState === 'full_primary_document_reviewed', 'Unreviewed notice promoted to 2026 current cohort');
  }
  if (n.applicability === 'prior_2025_cohort') {
    assert(n.cohort === '2025_manufacturing', 'Previous cohort must not become current');
  }
  if (n.applicability === 'cohort_not_linked') {
    assert(n.cohort.startsWith('departure_'), 'Unlinked departure must be isolated');
  }
  if (n.applicability === 'other_2026_program') {
    assert(n.cohort === '2026_root_industry_distinct_program', 'Other 2026 program must not be merged');
  }
}
for (const id of ['np_2026_first_phase_primary','np_2026_urgent_0726','np_2026_passport_0730',
  'np_2025_manu_job_notice','np_oct_2026_regular_departure',
  'np_2026_root_industry_alt_0701']) assert(noticeIDs.has(id), 'Missing essential safety notice ' + id);
for (const id of ['np_2026_urgent_0726','np_2026_passport_0730']) {
  const n = ledger.notices.find(x => x.id === id);
  assert(n?.applicability === 'supplementary_unreviewed', 'Critical unreviewed 2026 supplemental notice falsely promoted ' + id);
}
assert((ledger.notices || []).length >= 10, 'Nepal official notice ledger unexpectedly truncated');

const unsafeDocs = (docs.packs || []).filter(p=>p.status !== 'verified_official_pdf');
for (const doc of unsafeDocs) {
  assert(/baseline|pending|volatile/.test(doc.status), 'Unknown non-current document status '+doc.id);
  assert(doc.warning && doc.sourceUrl?.startsWith('https://epsnepal.gov.np/'), 'Non-current documents must carry warning/source '+doc.id);
}
if (fail.length) {
  for (const label of fail) console.error('NEPAL_GATE_FAIL:', label);
  process.exitCode = 1;
} else {
  console.log('NEPAL_RESEARCH_GATE_PASS');
  console.log('route='+ID+' stages='+stages.length+' notices='+ledger.notices.length+' documents='+docs.packs.length+' beta=blocked');
}
