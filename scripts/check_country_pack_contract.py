#!/usr/bin/env python3
from __future__ import annotations
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
EXPECTED=[
    "eligibility","registration","exam_fee","biometric","document_verify","exam_card",
    "eps_topik","skill_competency","final_selection","psychology_pre_job","mcu1",
    "job_application","roster","employer_selection","slc","post_slc_requirements",
    "visa_docs","predeparture_training","mcu3_departure","departure",
    "korea_entry_training","employer_handover","residence_registration",
    "eps_insurance_check","first_payroll_check","labor_support_ready","employment_maintenance",
]

def load(path):
    return json.loads((ROOT/path).read_text(encoding="utf-8-sig"))

failures=[]
def require(condition,message):
    if not condition: failures.append(message)

registry=load("docs/data/country_packs_v1.json")
require(registry.get("commonStageIds")==EXPECTED,"registry commonStageIds must preserve the locked 27-stage core")
routes={row.get("routeId"):row for row in registry.get("routes",[])}
require({"id-e9-manufacturing-2026","np-e9-manufacturing-2026","vn-e9-manufacturing-2026","ph-e9-manufacturing-2026","th-e9-manufacturing-2026","bd-e9-manufacturing-2026","lk-e9-manufacturing-2026","la-e9-manufacturing-2026","uz-e9-manufacturing-2026"}.issubset(routes),"registry must include Indonesia, Nepal, Vietnam, Philippines, Thailand, Bangladesh, Sri Lanka, Laos and Uzbekistan")

for route_id,entry in routes.items():
    pack=load("docs/"+entry["routeFile"])
    locale=load("docs/"+entry["localizationFile"])
    stage_ids=[row.get("id") for row in pack.get("stages",[])]
    require(stage_ids==EXPECTED,f"{route_id}: stage IDs/order must match common core")
    require(pack.get("country")==entry.get("country"),f"{route_id}: country mismatch")
    require(pack.get("visa")==entry.get("visa"),f"{route_id}: visa mismatch")
    require(pack.get("sector")==entry.get("sector"),f"{route_id}: sector mismatch")
    require(set(locale)==set(EXPECTED),f"{route_id}: localization must cover exactly 27 stages")
    for stage in pack.get("stages",[]):
        sid=stage.get("id","<missing>")
        for field in ("title","authority","kind","action","sourceUrl"):
            require(bool(str(stage.get(field,"")).strip()),f"{route_id}/{sid}: missing {field}")
        require(str(stage.get("sourceUrl","")).startswith("https://"),f"{route_id}/{sid}: source must use HTTPS")
        require(bool(str(locale.get(sid,{}).get("title","")).strip()),f"{route_id}/{sid}: localized title missing")
        require(bool(str(locale.get(sid,{}).get("action","")).strip()),f"{route_id}/{sid}: localized action missing")

np_entry=routes["np-e9-manufacturing-2026"]
np_pack=load("docs/data/np_e9_manufacturing_2026.json")
require(np_entry.get("lifecycle")=="research_hold","Nepal must remain research_hold")
require(np_entry.get("publicAvailability")=="preview_only","Nepal registry route must remain preview_only")
require(np_pack.get("lifecycle")=="research_hold","Nepal pack must remain research_hold")
require(np_pack.get("publicAvailability")=="preview_only","Nepal pack must remain preview_only")
require(np_pack.get("safety",{}).get("betaIntakeOpen") is False,"Nepal beta intake must remain closed")
require(np_pack.get("officialSendingAgency",{}).get("url")=="https://epsnepal.gov.np/","Nepal official sending agency URL must remain EPS Nepal")
require(np_pack.get("recruitmentCycleBasis")=="2026-first-phase-eps-topik-application-announced-2026-07-21","Nepal pack must preserve the verified 2026 first-phase recruitment basis")


np_exact=load("docs/data/np_exact_answer_rules_2026.json")
np_docs=load("docs/data/np_document_packs_2026.json")
require(np_pack.get("exactAnswerRulesFile")=="data/np_exact_answer_rules_2026.json","Nepal pack must link exact-answer rules")
require(np_pack.get("documentPacksFile")=="data/np_document_packs_2026.json","Nepal pack must link document packs")
window=np_pack.get("currentApplicationWindow",{})
require(window.get("opensAt")=="2026-07-27" and window.get("closesAt")=="2026-08-02","Nepal application window must match the verified notice")
require(window.get("status")=="closed","Nepal first-phase application window must remain closed after 2026-08-02")
require(window.get("examFeeUsd")==28,"Nepal official exam fee must remain US$28")
require(window.get("estimatedSelection",{}).get("manufacturing")==5000,"Nepal Manufacturing estimate must remain 5,000")
require(window.get("estimatedSelection",{}).get("total")==7200,"Nepal total estimate must remain 7,200")
require(len(np_exact.get("answers",[]))>=22,"Nepal exact-answer catalog must contain the verified 2026 registration/test facts")
exact_ids={row.get("id") for row in np_exact.get("answers",[])}
for exact_id in [
    "np_2026_application_window","np_2026_application_portal","np_2026_exam_fee",
    "np_2026_age_rule","np_2026_color_vision_rule","np_2026_photo_rule",
    "np_2026_test_format","np_2026_result_validity"
]:
    require(exact_id in exact_ids,f"Nepal exact-answer catalog missing {exact_id}")
for row in np_exact.get("answers",[]):
    require(str(row.get("sourceUrl","")).startswith("https://"),f"Nepal exact answer {row.get('id')} must preserve official HTTPS source lineage")
    require(row.get("verifiedAt")=="2026-10-05",f"Nepal exact answer {row.get('id')} verification date missing")
np_doc_ids={pack.get("id") for pack in np_docs.get("packs",[])}
require({"np_2026_eps_topik_registration","np_2026_eps_topik_exam_day"}.issubset(np_doc_ids),"Nepal document packs must cover registration and test day")


np_registration_notices=load("docs/data/np_registration_notices_2026.json")
require(np_pack.get("registrationNoticesFile")=="data/np_registration_notices_2026.json","Nepal pack must link the registration supplementary-notice registry")
notice_policy=np_registration_notices.get("policy",{})
require(notice_policy.get("deadlineExtensionVerified") is False,"Nepal must not claim a registration deadline extension without reviewed official evidence")
require(notice_policy.get("autoSupersedePrimaryRules") is False,"Supplementary Nepal notices must never auto-supersede exact rules")
np_notice_rows={row.get("id"):row for row in np_registration_notices.get("notices",[])}
for notice_id in [
    "np_2026_first_phase_primary",
    "np_2026_application_urgent_0726",
    "np_2026_application_suspended_0728",
    "np_2026_application_resumed_0728",
    "np_2026_application_passport_0730",
]:
    require(notice_id in np_notice_rows,f"Nepal registration notice registry missing {notice_id}")
for notice_id,row in np_notice_rows.items():
    require(str(row.get("pageUrl","")).startswith("https://epsnepal.gov.np/"),f"{notice_id}: pageUrl must stay on official EPS Nepal")
    require(bool(str(row.get("contentReviewStatus","")).strip()),f"{notice_id}: contentReviewStatus is required")
    require(bool(str(row.get("safeEffect","")).strip()),f"{notice_id}: safeEffect is required")
require(np_notice_rows["np_2026_application_suspended_0728"].get("effectStatus")=="temporary_suspension_verified_by_official_title","Nepal temporary suspension event must remain explicit")
require(np_notice_rows["np_2026_application_resumed_0728"].get("effectStatus")=="service_resumption_verified_by_official_title","Nepal resumption event must remain explicit")
require(np_notice_rows["np_2026_application_urgent_0726"].get("contentReviewStatus")=="pending_large_pdf_review","Unreviewed July 26 large PDF must remain pending")
require(np_notice_rows["np_2026_application_passport_0730"].get("contentReviewStatus")=="title_and_date_verified_content_pending","July 30 passport notice content must remain pending until reviewed")
require(np_exact.get("operationalNoticesFile")=="data/np_registration_notices_2026.json","Nepal exact answers must link operational notices")


np_stage_readiness=load("docs/data/np_stage_readiness_2026.json")
require(np_pack.get("stageReadinessFile")=="data/np_stage_readiness_2026.json","Nepal pack must link current-cohort stage readiness")
require(np_stage_readiness.get("checkedAt")=="2026-10-05","Nepal current-cohort readiness check date must be explicit")
np_current=np_stage_readiness.get("currentCohort",{})
require(np_current.get("recruitmentRegistration",{}).get("status")=="closed_verified","Nepal 2026 registration must remain closed_verified")
for key in ["epsTopikSchedule","epsTopikResult","skillCompetency","medicalAndJobApplication"]:
    require(np_current.get(key,{}).get("status")=="awaiting_current_cohort_notice",f"Nepal {key} must remain awaiting a current-cohort official notice")
for prior in np_current.get("skillCompetency",{}).get("priorCycleEvidence",[]):
    require(prior.get("cycle")==2025 and prior.get("use")=="workflow_shape_only","Nepal prior-cycle skill evidence must never become current exact rules")
for prior in np_current.get("medicalAndJobApplication",{}).get("priorCycleEvidence",[]):
    require(prior.get("cycle")==2025 and prior.get("use")=="workflow_shape_only","Nepal prior-cycle job-application evidence must never become current exact rules")
require(np_stage_readiness.get("betaReadiness",{}).get("status")=="blocked","Nepal beta must remain blocked while current-cohort downstream notices are unresolved")


np_process=load("docs/data/np_eps_process_baseline_2026.json")
require(np_pack.get("processBaselineFile")=="data/np_eps_process_baseline_2026.json","Nepal pack must link the EPS post-selection process baseline")
require(np_exact.get("processBaselineFile")=="data/np_eps_process_baseline_2026.json","Nepal exact answers must link the EPS post-selection process baseline")
require(len(np_exact.get("answers",[]))>=35,"Nepal exact-answer catalog must include verified post-selection process facts")
process_rows={row.get("id"):row for row in np_process.get("steps",[])}
for process_id in [
    "biometric_registration","medical_and_police","employment_application","spas_roster",
    "automated_job_matching","labor_contract_signature","pdot_training","ccvi_package",
    "visa_stamping","labor_approval_and_final_flight","departure_airports","reregistration"
]:
    require(process_id in process_rows,f"Nepal EPS process baseline missing {process_id}")
require(process_rows["medical_and_police"].get("baselineMedicalFeeUsd")==55.64,"Nepal medical process baseline must preserve official US$55.64 lineage")
require(process_rows["employment_application"].get("baselineFeeUsd")==5,"Nepal employment-application baseline must preserve official US$5 lineage")
require(process_rows["pdot_training"].get("durationDays")==6 and process_rows["pdot_training"].get("baselineFeeUsd")==63,"Nepal PDOT baseline must preserve 6 days / US$63 lineage")
require(process_rows["ccvi_package"].get("historicalBaselineFeeNpr")==10700,"Nepal CCVI baseline must preserve historical NPR 10,700 lineage")
require(process_rows["ccvi_package"].get("amountCurrent") is False,"Historical Nepal CCVI amount must never be treated as current")
require(np_process.get("currentnessPolicy",{}).get("visaPayment")=="volatile_2026_multiple_change_notices","Nepal visa/service fee must remain explicitly volatile")
post_exact_ids={row.get("id") for row in np_exact.get("answers",[])}
for exact_id in [
    "np_2026_biometric_day_before","np_2026_exam_arrival_time","np_2026_medical_police_baseline",
    "np_2026_job_application_baseline","np_2026_roster_status","np_2026_job_matching_automation",
    "np_2026_slc_signature","np_2026_pdot_baseline","np_2026_ccvi_package",
    "np_2026_visa_status","np_2026_labor_approval","np_2026_departure_airports",
    "np_2026_reregistration_rule"
]:
    require(exact_id in post_exact_ids,f"Nepal exact-answer catalog missing {exact_id}")
post_doc_ids={pack.get("id") for pack in np_docs.get("packs",[])}
require({"np_employment_application_baseline","np_ccvi_visa_baseline"}.issubset(post_doc_ids),"Nepal document packs must cover employment application and CCVI/visa baseline")
ccvi_pack=next((pack for pack in np_docs.get("packs",[]) if pack.get("id")=="np_ccvi_visa_baseline"),{})
require("latest official" in str(ccvi_pack.get("warning","")).lower(),"Nepal CCVI pack must warn against stale visa/service fees")
require(np_stage_readiness.get("processBaseline",{}).get("status")=="verified_workflow_shape_only","Nepal stable process baseline must not be promoted as current-cohort exact readiness")


vn_entry=routes["vn-e9-manufacturing-2026"]
vn_pack=load("docs/data/vn_e9_manufacturing_2026.json")
vn_exact=load("docs/data/vn_exact_answer_rules_2026.json")
vn_stage_readiness=load("docs/data/vn_stage_readiness_2026.json")
vn_docs=load("docs/data/vn_document_packs_2026.json")
require(vn_entry.get("lifecycle")=="research_hold","Vietnam must remain research_hold")
require(vn_entry.get("publicAvailability")=="preview_only","Vietnam registry route must remain preview_only")
require(vn_pack.get("lifecycle")=="research_hold" and vn_pack.get("publicAvailability")=="preview_only","Vietnam pack must remain preview-only HOLD")
require(vn_pack.get("safety",{}).get("betaIntakeOpen") is False,"Vietnam beta intake must remain closed")
require(vn_pack.get("officialSendingAgency",{}).get("url")=="https://colab.moha.gov.vn/","Vietnam official sending authority must remain COLAB")
require(vn_pack.get("exactAnswerRulesFile")=="data/vn_exact_answer_rules_2026.json","Vietnam pack must link exact answers")
require(vn_pack.get("stageReadinessFile")=="data/vn_stage_readiness_2026.json","Vietnam pack must link current-cohort readiness")
require(vn_pack.get("documentPacksFile")=="data/vn_document_packs_2026.json","Vietnam pack must link document packs")
require(vn_pack.get("registrationEvidence",{}).get("receivingDates")=="2026-03-23 through 2026-03-27","Vietnam registration receiving dates must match the verified official notice")
require(vn_pack.get("registrationEvidence",{}).get("status")=="closed","Vietnam 2026 registration receiving window must remain closed")
require(len(vn_exact.get("answers",[]))>=20,"Vietnam exact-answer catalog must preserve current 2026 registration/test facts")
vn_exact_ids={row.get("id") for row in vn_exact.get("answers",[])}
for exact_id in [
    "vn_2026_sending_authority","vn_2026_manufacturing_target","vn_2026_exam_fee","vn_2026_registration_window",
    "vn_2026_age_rule","vn_2026_registration_method","vn_2026_identity_lock",
    "vn_2026_test_format","vn_2026_round1_result","vn_2026_round2_auto",
    "vn_2026_round2_schedule_state","vn_2026_no_job_guarantee"
]:
    require(exact_id in vn_exact_ids,f"Vietnam exact-answer catalog missing {exact_id}")
for row in vn_exact.get("answers",[]):
    require(str(row.get("sourceUrl","")).startswith("https://colab.moha.gov.vn/"),f"Vietnam exact answer {row.get('id')} must preserve official COLAB source lineage")
    require(row.get("verifiedAt")=="2026-10-05",f"Vietnam exact answer {row.get('id')} verification date missing")
vn_doc_ids={p.get("id") for p in vn_docs.get("packs",[])}
require({"vn_2026_eps_topik_registration","vn_2026_candidate_forms_catalog"}.issubset(vn_doc_ids),"Vietnam document packs must cover test registration and the published 2026 candidate forms")
candidate_pack=next((p for p in vn_docs.get("packs",[]) if p.get("id")=="vn_2026_candidate_forms_catalog"),{})
require("exact submission" in str(candidate_pack.get("warning","")).lower(),"Vietnam candidate forms must not be presented as a complete current-cohort submission instruction")

vn_current=vn_stage_readiness.get("currentCohort",{})
require(vn_current.get("recruitmentRegistration",{}).get("status")=="closed_verified","Vietnam 2026 registration must remain closed_verified")
require(vn_current.get("epsTopikResult",{}).get("status")=="round1_result_verified","Vietnam Manufacturing Round 1 result must remain verified")
require(vn_current.get("skillCompetency",{}).get("status")=="awaiting_final_official_schedule","Vietnam Round 2 must not be promoted before final official schedule verification")
require(vn_stage_readiness.get("betaReadiness",{}).get("status")=="blocked","Vietnam beta must remain blocked while downstream exact rules are unresolved")


ph_entry=routes["ph-e9-manufacturing-2026"]
ph_pack=load("docs/data/ph_e9_manufacturing_2026.json")
ph_exact=load("docs/data/ph_exact_answer_rules_2026.json")
ph_docs=load("docs/data/ph_document_packs_2026.json")
ph_special=load("docs/data/ph_special_eps_topik_2026.json")
ph_readiness=load("docs/data/ph_stage_readiness_2026.json")
require(ph_entry.get("lifecycle")=="research_hold" and ph_entry.get("publicAvailability")=="preview_only","Philippines registry route must remain preview-only HOLD")
require(ph_pack.get("lifecycle")=="research_hold" and ph_pack.get("publicAvailability")=="preview_only","Philippines pack must remain preview-only HOLD")
require(ph_pack.get("safety",{}).get("betaIntakeOpen") is False,"Philippines beta intake must remain closed")
require(ph_pack.get("safety",{}).get("specialRouteFactsExcludedFromRegular") is True,"Philippines Special facts must be excluded from Regular route")
require(ph_pack.get("officialSendingAgency",{}).get("name")=="Department of Migrant Workers (DMW)","Philippines official sending agency must remain DMW")
require(ph_pack.get("exactAnswerRulesFile")=="data/ph_exact_answer_rules_2026.json","Philippines pack must link exact answers")
require(ph_pack.get("documentPacksFile")=="data/ph_document_packs_2026.json","Philippines pack must link document packs")
require(ph_pack.get("stageReadinessFile")=="data/ph_stage_readiness_2026.json","Philippines pack must link readiness")
require(ph_pack.get("specialRouteEvidenceFile")=="data/ph_special_eps_topik_2026.json","Philippines pack must link separate Special evidence")
ph_current=ph_readiness.get("currentRegular",{})
require(ph_current.get("registration",{}).get("status")=="no_open_registration","Philippines DMW portal must remain no-open-registration until official change")
require(ph_current.get("regularManufacturingSchedule",{}).get("status")=="listed_dates_undecided","Philippines Regular Manufacturing dates must remain undecided until official schedule")
require(ph_readiness.get("specialRoute",{}).get("mustNotPopulateRegular") is True,"Philippines Special route must never populate Regular rules")
require(ph_readiness.get("betaReadiness",{}).get("status")=="blocked","Philippines beta must remain blocked")
require(ph_special.get("excludedFromRegularCountryPack") is True,"Philippines Special evidence must be explicitly excluded from Regular pack")
require(ph_special.get("facts",{}).get("testFeeUsd")==24 and ph_special.get("facts",{}).get("expectedSuccessfulCandidates")==100,"Philippines Special facts must preserve their own fee/quota only inside special evidence")
require(ph_special.get("crossSourceScheduleNote",{}).get("status")=="special_route_schedule_sources_differ","Philippines Special DMW/HRD schedule discrepancy must remain isolated from Regular")
require("Regular Manufacturing" in ph_special.get("crossSourceScheduleNote",{}).get("rule",""),"Philippines Special discrepancy rule must explicitly block promotion into Regular Manufacturing")
regular_exact_ids={row.get("id") for row in ph_exact.get("answers",[])}
for exact_id in ["ph_2026_sending_authority","ph_2026_regular_schedule_status","ph_2026_portal_registration_status","ph_2026_special_route_separation","ph_regular_no_job_guarantee"]:
    require(exact_id in regular_exact_ids,f"Philippines exact-answer catalog missing {exact_id}")
special_sep=next((row for row in ph_exact.get("answers",[]) if row.get("id")=="ph_2026_special_route_separation"),{})
require("must not" in str(special_sep.get("writeExactly","")).lower() or "do not" in str(special_sep.get("writeExactly","")).lower(),"Philippines Special/Regular firewall must be explicit")
ph_doc_ids={p.get("id") for p in ph_docs.get("packs",[])}
require("ph_current_portal_registration_preparation" in ph_doc_ids,"Philippines current portal preparation pack is required")


th_entry=routes["th-e9-manufacturing-2026"]
th_pack=load("docs/data/th_e9_manufacturing_2026.json")
th_exact=load("docs/data/th_exact_answer_rules_2026.json")
th_readiness=load("docs/data/th_stage_readiness_2026.json")
th_special=load("docs/data/th_special_eps_topik_2026.json")
require(th_entry.get("lifecycle")=="research_hold" and th_entry.get("publicAvailability")=="preview_only","Thailand registry route must remain preview-only HOLD")
require(th_pack.get("lifecycle")=="research_hold" and th_pack.get("publicAvailability")=="preview_only","Thailand pack must remain preview-only HOLD")
require(th_pack.get("safety",{}).get("betaIntakeOpen") is False,"Thailand beta intake must remain closed")
require(th_pack.get("safety",{}).get("specialRouteFactsExcludedFromRegular") is True,"Thailand Special facts must be excluded from Round 18 Regular route")
require(th_pack.get("officialSendingAgency",{}).get("name")=="Department of Employment, Ministry of Labour","Thailand official sending agency must remain DOE")
require(th_pack.get("exactAnswerRulesFile")=="data/th_exact_answer_rules_2026.json","Thailand pack must link exact answers")
require(th_pack.get("stageReadinessFile")=="data/th_stage_readiness_2026.json","Thailand pack must link readiness")
require(th_pack.get("specialRouteEvidenceFile")=="data/th_special_eps_topik_2026.json","Thailand pack must link separate Special evidence")
th_exact_ids={row.get("id") for row in th_exact.get("answers",[])}
for exact_id in [
    "th_2026_round18_manufacturing_quota","th_2026_registration_window","th_2026_exam_fee",
    "th_2026_age_rule","th_2026_e9_e10_limit","th_2026_skill_candidate_list_date",
    "th_2026_no_job_guarantee","th_2026_roster_year2"
]:
    require(exact_id in th_exact_ids,f"Thailand exact-answer catalog missing {exact_id}")
require(th_readiness.get("currentRegular",{}).get("recruitment",{}).get("status")=="closed_verified","Thailand Round 18 registration must remain closed_verified")
require(th_readiness.get("currentRegular",{}).get("skillCompetency",{}).get("status")=="awaiting_2026_10_19_candidate_list","Thailand skills stage must remain awaiting the 2026-10-19 official candidate list")
require(th_readiness.get("betaReadiness",{}).get("status")=="blocked","Thailand beta must remain blocked")
require(th_special.get("excludedFromRegularCountryPack") is True,"Thailand Special evidence must be explicitly excluded from Round 18")
require(th_special.get("facts",{}).get("testFeeThb")==970,"Thailand Special 970 THB fee must stay isolated in Special evidence")


bd_entry=routes["bd-e9-manufacturing-2026"]
bd_pack=load("docs/data/bd_e9_manufacturing_2026.json")
bd_exact=load("docs/data/bd_exact_answer_rules_2026.json")
bd_docs=load("docs/data/bd_document_packs_2026.json")
bd_special=load("docs/data/bd_special_eps_topik_2026.json")
bd_readiness=load("docs/data/bd_stage_readiness_2026.json")
require(bd_entry.get("lifecycle")=="research_hold" and bd_entry.get("publicAvailability")=="preview_only","Bangladesh registry route must remain preview-only HOLD")
require(bd_pack.get("lifecycle")=="research_hold" and bd_pack.get("publicAvailability")=="preview_only","Bangladesh pack must remain preview-only HOLD")
require(bd_pack.get("safety",{}).get("betaIntakeOpen") is False,"Bangladesh beta intake must remain closed")
require(bd_pack.get("safety",{}).get("specialRouteFactsExcludedFromRegular") is True,"Bangladesh Special facts must stay outside Regular Manufacturing")
require(bd_pack.get("safety",{}).get("genericHrdBaselineNotCurrentCycle") is True,"Generic HRD baseline must not become a current Bangladesh Regular rule")
require(bd_pack.get("officialSendingAgency",{}).get("name")=="Bangladesh Overseas Employment and Services Limited (BOESL)","Bangladesh sending agency must remain BOESL")
require(bd_pack.get("exactAnswerRulesFile")=="data/bd_exact_answer_rules_2026.json","Bangladesh pack must link exact answers")
require(bd_pack.get("documentPacksFile")=="data/bd_document_packs_2026.json","Bangladesh pack must link document packs")
require(bd_pack.get("stageReadinessFile")=="data/bd_stage_readiness_2026.json","Bangladesh pack must link readiness")
require(bd_pack.get("specialRouteEvidenceFile")=="data/bd_special_eps_topik_2026.json","Bangladesh pack must link separate Special evidence")
bd_current=bd_readiness.get("currentRegular",{})
require(bd_current.get("registrationAndTestSchedule",{}).get("status")=="not_yet_verified_current_regular","Bangladesh Regular registration/test schedule must remain unverified until a current official Regular notice is reviewed")
require(bd_current.get("genericRegistrationBaseline",{}).get("status")=="process_baseline_only","Bangladesh generic HRD visiting-registration guidance must remain baseline-only")
require(bd_readiness.get("specialRoute",{}).get("mustNotPopulateRegular") is True,"Bangladesh Special route must never populate Regular rules")
require(bd_readiness.get("betaReadiness",{}).get("status")=="blocked","Bangladesh beta must remain blocked")
require(bd_special.get("excludedFromRegularCountryPack") is True,"Bangladesh Special evidence must be explicitly excluded from Regular")
require(bd_special.get("facts",{}).get("registrationPeriod")=="2026-03-10 through 2026-03-11","Bangladesh Special registration dates must remain isolated")
require(bd_special.get("facts",{}).get("testDate")=="2026-05-08" and bd_special.get("facts",{}).get("resultDate")=="2026-06-08","Bangladesh Special test/result dates must remain isolated")
bd_doc_ids={p.get("id") for p in bd_docs.get("packs",[])}
require("bd_hrd_visit_registration_baseline" in bd_doc_ids,"Bangladesh generic HRD registration baseline pack is required")
bd_baseline=next((p for p in bd_docs.get("packs",[]) if p.get("id")=="bd_hrd_visit_registration_baseline"),{})
require(bd_baseline.get("feeBaselineUsd")==28 and bd_baseline.get("feeCurrentForBangladeshRegular") is False,"Bangladesh US$28 generic baseline must never be marked as current Regular fee")
bd_exact_ids={row.get("id") for row in bd_exact.get("answers",[])}
for exact_id in [
    "bd_2026_sending_authority","bd_2026_reception_office","bd_2026_regular_status",
    "bd_hrd_generic_visit_fee","bd_hrd_generic_visit_docs",
    "bd_2026_special_route_separation","bd_regular_no_job_guarantee"
]:
    require(exact_id in bd_exact_ids,f"Bangladesh exact-answer catalog missing {exact_id}")


lk_entry=routes["lk-e9-manufacturing-2026"]
lk_pack=load("docs/data/lk_e9_manufacturing_2026.json")
lk_exact=load("docs/data/lk_exact_answer_rules_2026.json")
lk_docs=load("docs/data/lk_document_packs_2026.json")
lk_readiness=load("docs/data/lk_stage_readiness_2026.json")
lk_special=load("docs/data/lk_special_eps_topik_2026.json")
require(lk_entry.get("lifecycle")=="research_hold" and lk_entry.get("publicAvailability")=="preview_only","Sri Lanka registry route must remain preview-only HOLD")
require(lk_pack.get("lifecycle")=="research_hold" and lk_pack.get("publicAvailability")=="preview_only","Sri Lanka pack must remain preview-only HOLD")
require(lk_pack.get("safety",{}).get("betaIntakeOpen") is False,"Sri Lanka beta intake must remain closed")
require(lk_pack.get("safety",{}).get("specialRouteFactsExcludedFromCurrentPointSystem") is True,"Sri Lanka Special facts must remain outside the current Point System")
require(lk_pack.get("safety",{}).get("prior10thCycleFactsExcludedFromCurrent") is True,"Sri Lanka completed 10th-cycle facts must remain outside the current September 2026 route")
require(lk_pack.get("officialSendingAgency",{}).get("name")=="Sri Lanka Bureau of Foreign Employment (SLBFE)","Sri Lanka sending agency must remain SLBFE")
require(lk_pack.get("exactAnswerRulesFile")=="data/lk_exact_answer_rules_2026.json","Sri Lanka pack must link exact answers")
require(lk_pack.get("documentPacksFile")=="data/lk_document_packs_2026.json","Sri Lanka pack must link document pack")
require(lk_pack.get("stageReadinessFile")=="data/lk_stage_readiness_2026.json","Sri Lanka pack must link readiness")
require(lk_pack.get("specialRouteEvidenceFile")=="data/lk_special_eps_topik_2026.json","Sri Lanka pack must link separate Special evidence")
lk_ids={row.get("id") for row in lk_exact.get("answers",[])}
for exact_id in [
    "lk_2026_manufacturing_quota","lk_2026_application_window","lk_2026_application_instructions_date",
    "lk_2026_exam_fee","lk_2026_age_rule","lk_2026_one_industry","lk_2026_passport_spec",
    "lk_2026_photo_spec","lk_2026_test_notice_date","lk_2026_test_start","lk_2026_test_format",
    "lk_2026_skill_floor","lk_2026_no_job_guarantee"
]:
    require(exact_id in lk_ids,f"Sri Lanka exact-answer catalog missing {exact_id}")
require(lk_readiness.get("currentCohort",{}).get("recruitment",{}).get("status")=="upcoming_verified","Sri Lanka current recruitment must remain upcoming_verified before application opens")
require(lk_readiness.get("currentCohort",{}).get("recruitment",{}).get("publicActionState")=="hold_until_2026_10_12_instructions_reviewed","Sri Lanka field-level application guidance must stay held until Oct 12 instructions are reviewed")
require(lk_readiness.get("nextReviewTrigger",{}).get("date")=="2026-10-12","Sri Lanka next review trigger must remain 2026-10-12")
require(len(lk_readiness.get("nextReviewTrigger",{}).get("promoteOnlyWhen",[]))>=3,"Sri Lanka Oct 12 promotion guard must remain explicit")
require(lk_readiness.get("betaReadiness",{}).get("status")=="blocked","Sri Lanka beta must remain blocked")
require(lk_readiness.get("specialRoute",{}).get("mustNotPopulateCurrentPointSystem") is True,"Sri Lanka Special route must never populate the current Point System")
require(lk_readiness.get("priorCycle10th",{}).get("mustNotPopulateCurrentSeptember2026Rules") is True,"Sri Lanka completed 10th Point System must remain historical only")
require(lk_special.get("excludedFromCurrentPointSystemCountryPack") is True,"Sri Lanka Special evidence must be explicitly excluded from current Point System")
require(lk_special.get("facts",{}).get("testFeeUsd")==28 and lk_special.get("facts",{}).get("testFeeLkr")==8716.40,"Sri Lanka Special fee must remain isolated from current LKR 9,250 fee")
lk_doc_ids={p.get("id") for p in lk_docs.get("packs",[])}
require("lk_2026_point_system_application" in lk_doc_ids,"Sri Lanka application document pack is required")


la_entry=routes["la-e9-manufacturing-2026"]
la_pack=load("docs/data/la_e9_manufacturing_2026.json")
la_exact=load("docs/data/la_exact_answer_rules_2026.json")
la_docs=load("docs/data/la_document_packs_2026.json")
la_readiness=load("docs/data/la_stage_readiness_2026.json")
la_prior=load("docs/data/la_prior_round_evidence_2026.json")
require(la_entry.get("lifecycle")=="research_hold" and la_entry.get("publicAvailability")=="preview_only","Laos registry route must remain preview-only HOLD")
require(la_pack.get("lifecycle")=="research_hold" and la_pack.get("publicAvailability")=="preview_only","Laos pack must remain preview-only HOLD")
require(la_pack.get("safety",{}).get("betaIntakeOpen") is False,"Laos beta intake must remain closed")
require(la_pack.get("safety",{}).get("priorRoundFactsExcludedFromCurrent") is True,"Laos prior-round facts must stay outside the current 34th round")
require(la_pack.get("safety",{}).get("unverifiedFeeQuotaDocumentsMustStayBlank") is True,"Laos unverified fee/quota/document details must remain blank")
require(la_pack.get("officialSendingAgency",{}).get("name")=="Department of Employment of Lao PDR (DOE)","Laos official sending agency must remain DOE")
require(la_pack.get("officialSendingAgency",{}).get("receptionOffice",{}).get("name")=="Ministry of Labour and Social Welfare Employment Service Center (ESC)","Laos current reception office must remain ESC")
require(la_pack.get("documentPacksFile")=="data/la_document_packs_2026.json","Laos pack must link current document HOLD pack")
require(la_pack.get("priorRoundEvidenceFile")=="data/la_prior_round_evidence_2026.json","Laos pack must link 33rd-round firewall evidence")
la_current=la_readiness.get("currentRound",{})
require(la_current.get("registration",{}).get("status")=="closed_verified","Laos 34th registration must remain closed_verified")
require(la_current.get("examAndResult",{}).get("status")=="dates_undecided","Laos 34th test/result dates must remain undecided")
for key in ["fee","quota","documents"]:
    require(la_current.get(key,{}).get("status")=="unverified_current_round",f"Laos {key} must remain unverified_current_round")
require(la_readiness.get("priorRound",{}).get("mustNotPopulateCurrent") is True,"Laos 33rd round must never populate 34th-round rules")
require(la_readiness.get("betaReadiness",{}).get("status")=="blocked","Laos beta must remain blocked")
require(la_prior.get("excludedFromCurrent34thCountryPack") is True,"Laos 33rd-round evidence must be explicitly excluded from current 34th pack")
require(la_prior.get("facts",{}).get("registrationPeriod")=="2026-03-10 through 2026-03-13","Laos prior registration dates must remain isolated")
require(la_prior.get("facts",{}).get("testPeriod")=="2026-04-20 through 2026-04-27","Laos prior test dates must remain isolated")
la_doc_ids={p.get("id") for p in la_docs.get("packs",[])}
require({"la_34th_registration_documents_hold","la_current_reception_contact"}.issubset(la_doc_ids),"Laos document packs must preserve HOLD plus verified reception contact")
la_hold=next((p for p in la_docs.get("packs",[]) if p.get("id")=="la_34th_registration_documents_hold"),{})
require(la_hold.get("status")=="current_round_exact_checklist_not_verified" and la_hold.get("items")==[],"Laos current document HOLD pack must contain no invented checklist items")
la_exact_ids={row.get("id") for row in la_exact.get("answers",[])}
for exact_id in [
    "la_2026_sending_authority","la_2026_reception_office","la_2026_34th_registration_window",
    "la_2026_34th_schedule_state","la_2026_current_fee_state","la_2026_current_quota_state",
    "la_2026_prior_round_firewall"
]:
    require(exact_id in la_exact_ids,f"Laos exact-answer catalog missing {exact_id}")


uz_entry=routes["uz-e9-manufacturing-2026"]
uz_pack=load("docs/data/uz_e9_manufacturing_2026.json")
uz_exact=load("docs/data/uz_exact_answer_rules_2026.json")
uz_docs=load("docs/data/uz_document_packs_2026.json")
uz_readiness=load("docs/data/uz_stage_readiness_2026.json")
require(uz_entry.get("lifecycle")=="research_hold" and uz_entry.get("publicAvailability")=="preview_only","Uzbekistan registry route must remain preview-only HOLD")
require(uz_pack.get("lifecycle")=="research_hold" and uz_pack.get("publicAvailability")=="preview_only","Uzbekistan pack must remain preview-only HOLD")
require(uz_pack.get("safety",{}).get("betaIntakeOpen") is False,"Uzbekistan beta intake must remain closed")
require(uz_pack.get("safety",{}).get("genericHrdFeeNotCurrentCycle") is True,"Uzbekistan generic HRD fee must not become a cycle-specific exact fee")
require(uz_pack.get("safety",{}).get("contactSourcesPreservedWithoutSilentReconciliation") is True,"Uzbekistan official contact contexts must not be silently reconciled")
require(uz_pack.get("officialSendingAgency",{}).get("name")=="MIGRATION AGENCY UNDER THE CABINET OF MINSTERS OF THE REPUBLIC OF UZBEKISTAN (AELM)","Uzbekistan sending agency must remain Migration Agency/AELM")
require(uz_pack.get("documentPacksFile")=="data/uz_document_packs_2026.json","Uzbekistan pack must link document/contact HOLD packs")
uz_current=uz_readiness.get("currentCycle",{})
require(uz_current.get("recruitmentRegistration",{}).get("status")=="closed_verified","Uzbekistan 9th registration must remain closed_verified")
require(uz_current.get("epsTopikSchedule",{}).get("status")=="completed_period_verified","Uzbekistan 9th Round 1 test period must remain verified")
require(uz_current.get("skillsAndFinalResult",{}).get("status")=="awaiting_verified_current_cycle_result_state","Uzbekistan skills/final-result state must remain unpromoted until verified")
require(uz_current.get("fee",{}).get("status")=="cycle_specific_unverified","Uzbekistan cycle-specific fee must remain unresolved")
require(uz_current.get("documents",{}).get("status")=="cycle_specific_checklist_not_reconstructed","Uzbekistan cycle-specific registration checklist must remain HOLD")
require(uz_readiness.get("betaReadiness",{}).get("status")=="blocked","Uzbekistan beta must remain blocked")
uz_doc_ids={p.get("id") for p in uz_docs.get("packs",[])}
require({"uz_9th_registration_documents_hold","uz_official_contact_context"}.issubset(uz_doc_ids),"Uzbekistan document packs must preserve HOLD plus official contact context")
uz_hold=next((p for p in uz_docs.get("packs",[]) if p.get("id")=="uz_9th_registration_documents_hold"),{})
require(uz_hold.get("items")==[],"Uzbekistan cycle-specific document HOLD pack must contain no invented checklist items")
uz_exact_ids={row.get("id") for row in uz_exact.get("answers",[])}
for exact_id in [
    "uz_2026_sending_authority","uz_2026_registration_window","uz_2026_test_notice_date",
    "uz_2026_test_period","uz_2026_point_system","uz_2026_contact_context",
    "uz_2026_fee_state","uz_2026_skill_structure","uz_2026_final_state","uz_no_job_guarantee"
]:
    require(exact_id in uz_exact_ids,f"Uzbekistan exact-answer catalog missing {exact_id}")

countries=(ROOT/"docs/countries.html").read_text(encoding="utf-8")
nepal=(ROOT/"docs/np.html").read_text(encoding="utf-8")
vietnam=(ROOT/"docs/vn.html").read_text(encoding="utf-8")
philippines=(ROOT/"docs/ph.html").read_text(encoding="utf-8")
thailand=(ROOT/"docs/th.html").read_text(encoding="utf-8")
bangladesh=(ROOT/"docs/bd.html").read_text(encoding="utf-8")
srilanka=(ROOT/"docs/lk.html").read_text(encoding="utf-8")
laos=(ROOT/"docs/la.html").read_text(encoding="utf-8")
uzbekistan=(ROOT/"docs/uz.html").read_text(encoding="utf-8")
require("RESEARCH / HOLD" in countries and "preview_only" not in countries,"countries page must visibly label Nepal HOLD")
require("Research HOLD" in nepal and "Beta registration/access अहिले खुला छैन" in nepal and "2026-07-21" in nepal,"Nepal page must visibly keep beta closed while acknowledging the verified 2026 notice")
require("2026 EXACT FACTS" in nepal and "US$28" in nepal and "5,000" in nepal,"Nepal preview must expose verified first-phase facts without opening beta")
require("APPLICATION SYSTEM HISTORY" in nepal and "deadline extension" in nepal.lower(),"Nepal preview must disclose the registration interruption/resumption without claiming an extension")
require("CURRENT 2026 COHORT STATUS" in nepal and "Skill & Competency" in nepal,"Nepal preview must show current-cohort downstream HOLD status")
require("POST-SELECTION VERIFIED" in nepal and "6-day" in nepal and "FEIMS" in nepal and "visa/service" in nepal.lower(),"Nepal preview must expose verified process shape without hiding fee volatility")
require('href="beta.html"' not in nepal,"Nepal preview must not link to Indonesia beta enrollment")
require('id="betaForm"' not in nepal,"Nepal preview must not contain a beta enrollment form")
require("RESEARCH / HOLD" in vietnam and "150" in vietnam and "COLAB" in vietnam,"Vietnam preview must show HOLD, verified Round 1 cutoff and official sending authority")
require("CURRENT 2026 COHORT STATUS" in vietnam and "Vòng 2" in vietnam,"Vietnam preview must show downstream current-cohort HOLD")
require('href="beta.html"' not in vietnam and 'id="betaForm"' not in vietnam,"Vietnam preview must not expose beta enrollment")
require("RESEARCH / HOLD" in philippines and "No registration is currently open" in philippines,"Philippines preview must visibly remain HOLD with no open registration")
require("SPECIAL ROUTE FIREWALL" in philippines and "US$24" in philippines and "100-person" in philippines,"Philippines preview must visibly separate Special from Regular")
require('href="beta.html"' not in philippines and 'id="betaForm"' not in philippines,"Philippines preview must not expose beta enrollment")
require("RESEARCH / HOLD" in thailand and "2,000" in thailand and "960" in thailand,"Thailand preview must show HOLD, Manufacturing target and official Round 18 fee")
require("19 ต.ค. 2569" in thailand and "SPECIAL ROUTE FIREWALL" in thailand,"Thailand preview must show current skills-stage gate and Special firewall")
require('href="beta.html"' not in thailand and 'id="betaForm"' not in thailand,"Thailand preview must not expose beta enrollment")
require("RESEARCH / HOLD" in bangladesh and "BOESL" in bangladesh,"Bangladesh preview must visibly remain HOLD and identify BOESL")
require("SPECIAL ROUTE FIREWALL" in bangladesh and "10–11 March" in bangladesh and "8 May" in bangladesh,"Bangladesh preview must visibly isolate the verified Special route")
require("US$28" in bangladesh and "current Bangladesh Regular fee" in bangladesh,"Bangladesh preview must label generic HRD US$28 as non-current Regular fee")
require('href="beta.html"' not in bangladesh and 'id="betaForm"' not in bangladesh,"Bangladesh preview must not expose beta enrollment")
require("RESEARCH / HOLD" in srilanka and "1,000" in srilanka and "LKR 9,250" in srilanka,"Sri Lanka preview must show HOLD, current Manufacturing quota and official fee")
require("2026-10-12" in srilanka and "2026-10-26" in srilanka and "2026-10-30" in srilanka,"Sri Lanka preview must show current application timeline using locale-neutral ISO dates")
require('href="beta.html"' not in srilanka and 'id="betaForm"' not in srilanka,"Sri Lanka preview must not expose beta enrollment")
require("RESEARCH / HOLD" in laos and "2026-09-07" in laos and "2026-09-11" in laos,"Laos preview must visibly remain HOLD with verified 34th registration window")
require("INTENTIONALLY UNRESOLVED" in laos and "PRIOR-ROUND FIREWALL" in laos,"Laos preview must show unresolved current rules and prior-round firewall")
require("2026-03-10" in laos and "2026-04-20" in laos,"Laos preview must visibly isolate 33rd-round dates")
require('href="beta.html"' not in laos and 'id="betaForm"' not in laos,"Laos preview must not expose beta enrollment")
require("RESEARCH / HOLD" in uzbekistan and "2026-03-09" in uzbekistan and "2026-04-22" in uzbekistan,"Uzbekistan preview must visibly remain HOLD with verified registration/test timeline")
require("OFFICIAL CONTACT CONTEXT" in uzbekistan and "INTENTIONALLY UNRESOLVED" in uzbekistan,"Uzbekistan preview must preserve official contact contexts and unresolved current rules")
require("US$28" in uzbekistan and "current Uzbekistan exact fee" in uzbekistan,"Uzbekistan preview must label generic US$28 baseline as non-current exact fee")
require('href="beta.html"' not in uzbekistan and 'id="betaForm"' not in uzbekistan,"Uzbekistan preview must not expose beta enrollment")

if failures:
    print("COUNTRY_PACK_CONTRACT_FAIL")
    for failure in failures: print("- "+failure)
    raise SystemExit(1)

print("COUNTRY_PACK_CONTRACT_PASS routes=%d stages=%d nepal=research_hold vietnam=research_hold philippines=research_hold thailand=research_hold bangladesh=research_hold srilanka=research_hold laos=research_hold uzbekistan=research_hold" % (len(routes),len(EXPECTED)))
