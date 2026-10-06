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
require({"id-e9-manufacturing-2026","np-e9-manufacturing-2026","vn-e9-manufacturing-2026","ph-e9-manufacturing-2026","th-e9-manufacturing-2026","bd-e9-manufacturing-2026","lk-e9-manufacturing-2026","la-e9-manufacturing-2026","uz-e9-manufacturing-2026","mn-e9-manufacturing-2026","cn-e9-manufacturing-2026","kh-e9-manufacturing-2026","tl-e9-manufacturing-2026","pk-e9-manufacturing-2026","tj-e9-manufacturing-2026","kg-e9-manufacturing-2026"}.issubset(routes),"registry must include Indonesia, Nepal, Vietnam, Philippines, Thailand, Bangladesh, Sri Lanka, Laos, Uzbekistan, Mongolia, China, Cambodia, Timor-Leste, Pakistan, Tajikistan and Kyrgyzstan")

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


mn_entry=routes["mn-e9-manufacturing-2026"]
mn_pack=load("docs/data/mn_e9_manufacturing_2026.json")
mn_exact=load("docs/data/mn_exact_answer_rules_2026.json")
mn_docs=load("docs/data/mn_document_packs_2026.json")
mn_special=load("docs/data/mn_special_eps_topik_2026.json")
mn_readiness=load("docs/data/mn_stage_readiness_2026.json")
require(mn_entry.get("lifecycle")=="research_hold" and mn_entry.get("publicAvailability")=="preview_only","Mongolia registry route must remain preview-only HOLD")
require(mn_pack.get("lifecycle")=="research_hold" and mn_pack.get("publicAvailability")=="preview_only","Mongolia pack must remain preview-only HOLD")
require(mn_pack.get("safety",{}).get("betaIntakeOpen") is False,"Mongolia beta intake must remain closed")
require(mn_pack.get("safety",{}).get("specialRouteFactsExcludedFromRegular") is True,"Mongolia Special facts must stay outside Regular 11th Manufacturing")
require(mn_pack.get("safety",{}).get("genericResultListingNotAutoLinkedToCurrentManufacturing") is True,"Mongolia generic result listing must not auto-link to current Manufacturing")
require(mn_pack.get("safety",{}).get("officialContactContextsPreserved") is True,"Mongolia official contact contexts must remain source-scoped")
require(mn_pack.get("officialSendingAgency",{}).get("name")=="General Office for Labour and Welfare Service (GOLWS)","Mongolia sending agency must remain GOLWS")
require(mn_pack.get("specialRouteEvidenceFile")=="data/mn_special_eps_topik_2026.json","Mongolia pack must link separate Special evidence")
mn_current=mn_readiness.get("currentCycle",{})
require(mn_current.get("registration",{}).get("status")=="closed_verified","Mongolia 11th registration must remain closed_verified")
require(mn_current.get("epsTopikSchedule",{}).get("status")=="completed_period_verified","Mongolia 11th test period must remain verified")
require(mn_current.get("skillsAndFinalResult",{}).get("status")=="result_index_exists_cycle_linkage_pending","Mongolia final-result linkage must remain gated until exact cycle/sector proof")
require(mn_current.get("fee",{}).get("status")=="cycle_specific_unverified","Mongolia cycle-specific fee must remain unresolved")
require(mn_current.get("documents",{}).get("status")=="cycle_specific_checklist_not_reconstructed","Mongolia registration checklist must remain HOLD")
require(mn_readiness.get("specialRoute",{}).get("mustNotPopulateRegular") is True,"Mongolia Special route must never populate Regular rules")
require(mn_readiness.get("betaReadiness",{}).get("status")=="blocked","Mongolia beta must remain blocked")
require(mn_special.get("excludedFromRegularCountryPack") is True,"Mongolia Special evidence must be explicitly excluded from Regular")
require(mn_special.get("facts",{}).get("registrationPeriod")=="2026-04-20 through 2026-04-22","Mongolia Special registration dates must remain isolated")
require(mn_special.get("facts",{}).get("testDate")=="2026-05-26" and mn_special.get("facts",{}).get("finalResultDate")=="2026-06-16","Mongolia Special test/result dates must remain isolated")
mn_doc_ids={p.get("id") for p in mn_docs.get("packs",[])}
require({"mn_11th_registration_documents_hold","mn_official_contact_context"}.issubset(mn_doc_ids),"Mongolia document packs must preserve HOLD plus official contact context")
mn_hold=next((p for p in mn_docs.get("packs",[]) if p.get("id")=="mn_11th_registration_documents_hold"),{})
require(mn_hold.get("items")==[],"Mongolia current registration HOLD pack must contain no invented checklist items")
mn_exact_ids={row.get("id") for row in mn_exact.get("answers",[])}
for exact_id in [
    "mn_2026_sending_authority","mn_2026_registration_window","mn_2026_test_notice_date",
    "mn_2026_test_period","mn_2026_point_system","mn_2026_result_index_state",
    "mn_2026_special_firewall","mn_2026_skill_structure","mn_no_job_guarantee"
]:
    require(exact_id in mn_exact_ids,f"Mongolia exact-answer catalog missing {exact_id}")


cn_entry=routes["cn-e9-manufacturing-2026"]
cn_pack=load("docs/data/cn_e9_manufacturing_2026.json")
cn_exact=load("docs/data/cn_exact_answer_rules_2026.json")
cn_docs=load("docs/data/cn_document_packs_2026.json")
cn_readiness=load("docs/data/cn_stage_readiness_2026.json")
require(cn_entry.get("lifecycle")=="research_hold" and cn_entry.get("publicAvailability")=="preview_only","China registry route must remain preview-only HOLD")
require(cn_pack.get("lifecycle")=="research_hold" and cn_pack.get("publicAvailability")=="preview_only","China pack must remain preview-only HOLD")
require(cn_pack.get("safety",{}).get("betaIntakeOpen") is False,"China beta intake must remain closed")
require(cn_pack.get("safety",{}).get("genericHrdFeeNotCurrentCycle") is True,"China generic HRD fee must not become cycle-specific")
require(cn_pack.get("safety",{}).get("genericSkillsCandidateEntriesNotAutoLinkedToCurrentManufacturing") is True,"China generic skills-candidate entries must not auto-link to current Manufacturing")
require(cn_pack.get("safety",{}).get("officialContactContextsPreserved") is True,"China official contact contexts must remain source-scoped")
require(cn_pack.get("officialSendingAgency",{}).get("name")=="Investment Promotion Agency of Ministry of Commerce of P.R China (CIPA)","China sending agency must remain CIPA")
cn_current=cn_readiness.get("currentCycle",{})
require(cn_current.get("registration",{}).get("status")=="closed_verified","China 6th registration must remain closed_verified")
require(cn_current.get("epsTopikSchedule",{}).get("status")=="completed_period_verified","China 6th test period must remain verified")
require(cn_current.get("skillsCandidates",{}).get("status")=="generic_entries_exist_cycle_linkage_pending","China skills-candidate linkage must remain gated")
require(cn_current.get("finalResult",{}).get("status")=="awaiting_verified_current_cycle_final_result","China final result must remain gated")
require(cn_current.get("fee",{}).get("status")=="cycle_specific_unverified","China cycle-specific fee must remain unresolved")
require(cn_current.get("documents",{}).get("status")=="cycle_specific_checklist_not_reconstructed","China registration checklist must remain HOLD")
require(cn_readiness.get("betaReadiness",{}).get("status")=="blocked","China beta must remain blocked")
cn_doc_ids={p.get("id") for p in cn_docs.get("packs",[])}
require({"cn_6th_registration_documents_hold","cn_official_contact_context"}.issubset(cn_doc_ids),"China document packs must preserve HOLD plus official contact context")
cn_hold=next((p for p in cn_docs.get("packs",[]) if p.get("id")=="cn_6th_registration_documents_hold"),{})
require(cn_hold.get("items")==[],"China cycle-specific document HOLD pack must contain no invented checklist items")
cn_exact_ids={row.get("id") for row in cn_exact.get("answers",[])}
for exact_id in [
    "cn_2026_sending_authority","cn_2026_registration_window","cn_2026_test_notice_date",
    "cn_2026_test_period","cn_2026_point_system","cn_2026_fee_state",
    "cn_2026_skill_candidate_state","cn_2026_skill_rule","cn_no_job_guarantee"
]:
    require(exact_id in cn_exact_ids,f"China exact-answer catalog missing {exact_id}")


kh_entry=routes["kh-e9-manufacturing-2026"]
kh_pack=load("docs/data/kh_e9_manufacturing_2026.json")
kh_exact=load("docs/data/kh_exact_answer_rules_2026.json")
kh_docs=load("docs/data/kh_document_packs_2026.json")
kh_discovery=load("docs/data/kh_manufacturing_discovery_2026.json")
kh_other=load("docs/data/kh_other_sector_evidence_2026.json")
kh_special=load("docs/data/kh_special_eps_topik_2026.json")
kh_readiness=load("docs/data/kh_stage_readiness_2026.json")
require(kh_entry.get("lifecycle")=="research_hold" and kh_entry.get("publicAvailability")=="preview_only","Cambodia registry route must remain preview-only HOLD")
require(kh_pack.get("lifecycle")=="research_hold" and kh_pack.get("publicAvailability")=="preview_only","Cambodia pack must remain preview-only HOLD")
require(kh_pack.get("safety",{}).get("betaIntakeOpen") is False,"Cambodia beta intake must remain closed")
require(kh_pack.get("safety",{}).get("discoveryScheduleMustNotBecomeExact") is True,"Cambodia discovery schedule must never auto-promote to exact")
require(kh_pack.get("safety",{}).get("agricultureFactsExcludedFromManufacturing") is True,"Cambodia Agriculture facts must stay outside Manufacturing")
require(kh_pack.get("safety",{}).get("specialFactsExcludedFromManufacturing") is True,"Cambodia Special facts must stay outside Manufacturing")
require(kh_pack.get("safety",{}).get("genericOfficialResultArtifactsRequireCycleSectorLinkage") is True,"Cambodia generic official result artifacts require explicit cycle/sector linkage")
require(kh_pack.get("officialSendingAgency",{}).get("name")=="Manpower Training and Overseas Sending Board (MTOSB)","Cambodia sending agency must remain MTOSB")
kh_current=kh_readiness.get("currentManufacturing",{})
require(kh_current.get("officialRegistrationAndTestSchedule",{}).get("status")=="verified_direct_official","Cambodia direct Manufacturing schedule must remain verified")
require(kh_current.get("officialRegistrationAndTestSchedule",{}).get("registrationPeriod")=="2026-05-22 through 2026-05-25","Cambodia Manufacturing registration period must remain exact")
require(kh_current.get("officialRegistrationAndTestSchedule",{}).get("testAnnouncementDate")=="2026-06-12","Cambodia Manufacturing test announcement date must remain exact")
require(kh_current.get("officialRegistrationAndTestSchedule",{}).get("testPeriod")=="2026-06-22 through 2026-07-15","Cambodia Manufacturing test period must remain exact")
require(kh_current.get("discoverySchedule",{}).get("status")=="superseded_by_direct_official_match","Cambodia discovery schedule must remain provenance-only after official confirmation")
require(kh_current.get("skillsCandidateArtifact",{}).get("status")=="official_country_artifact_cycle_sector_linkage_pending","Cambodia skills-candidate artifact linkage must remain gated")
require(kh_current.get("finalPointResultArtifact",{}).get("status")=="official_country_artifact_cycle_sector_linkage_pending","Cambodia final Point System artifact linkage must remain gated")
require(kh_current.get("fee",{}).get("status")=="manufacturing_cycle_specific_unverified","Cambodia Manufacturing fee must remain unresolved")
require(kh_current.get("documents",{}).get("status")=="manufacturing_checklist_not_reconstructed","Cambodia Manufacturing checklist must remain HOLD")
require(kh_readiness.get("otherSector",{}).get("mustNotPopulateManufacturing") is True,"Cambodia Agriculture evidence must never populate Manufacturing")
require(kh_readiness.get("specialRoute",{}).get("mustNotPopulateManufacturing") is True,"Cambodia Special evidence must never populate Manufacturing")
require(kh_readiness.get("betaReadiness",{}).get("status")=="blocked","Cambodia beta must remain blocked")
require(kh_discovery.get("status")=="superseded_by_direct_official_confirmation","Cambodia discovery evidence must record direct-official confirmation")
require(kh_discovery.get("officialConfirmation",{}).get("registrationPeriod")=="2026-05-22 through 2026-05-25","Cambodia discovery confirmation must preserve the official registration period")
require(kh_other.get("excludedFromManufacturing") is True and kh_other.get("sector")=="agriculture_livestock","Cambodia official Agriculture evidence must be explicitly excluded from Manufacturing")
require(kh_special.get("excludedFromManufacturing") is True,"Cambodia Special artifact must be explicitly excluded from Manufacturing")
kh_doc_ids={p.get("id") for p in kh_docs.get("packs",[])}
require({"kh_manufacturing_registration_documents_hold","kh_official_contact_context"}.issubset(kh_doc_ids),"Cambodia document packs must preserve HOLD plus official contact context")
kh_hold=next((p for p in kh_docs.get("packs",[]) if p.get("id")=="kh_manufacturing_registration_documents_hold"),{})
require(kh_hold.get("items")==[],"Cambodia Manufacturing document HOLD pack must contain no invented checklist items")
kh_exact_ids={row.get("id") for row in kh_exact.get("answers",[])}
for exact_id in [
    "kh_2026_sending_authority","kh_2026_reception_office","kh_2026_skills_candidate_artifact",
    "kh_2026_point_result_artifact","kh_2026_manufacturing_schedule_state","kh_2026_registration_window","kh_2026_test_notice_date","kh_2026_test_period",
    "kh_2026_agriculture_firewall","kh_2026_special_firewall","kh_no_job_guarantee"
]:
    require(exact_id in kh_exact_ids,f"Cambodia exact-answer catalog missing {exact_id}")


tl_entry=routes["tl-e9-manufacturing-2026"]
tl_pack=load("docs/data/tl_e9_manufacturing_2026.json")
tl_exact=load("docs/data/tl_exact_answer_rules_2026.json")
tl_docs=load("docs/data/tl_document_packs_2026.json")
tl_discovery=load("docs/data/tl_baucau_discovery_2026.json")
tl_other=load("docs/data/tl_other_sector_evidence_2026.json")
tl_readiness=load("docs/data/tl_stage_readiness_2026.json")
require(tl_entry.get("lifecycle")=="research_hold" and tl_entry.get("publicAvailability")=="preview_only","Timor-Leste registry route must remain preview-only HOLD")
require(tl_pack.get("lifecycle")=="research_hold" and tl_pack.get("publicAvailability")=="preview_only","Timor-Leste pack must remain preview-only HOLD")
require(tl_pack.get("safety",{}).get("betaIntakeOpen") is False,"Timor-Leste beta intake must remain closed")
require(tl_pack.get("safety",{}).get("baucauDiscoveryMustNotBecomeExact") is True,"Timor-Leste Baucau discovery must not auto-promote")
require(tl_pack.get("safety",{}).get("fisheryFactsExcludedFromManufacturing") is True,"Timor-Leste Fishery facts must stay outside Manufacturing")
require(tl_pack.get("safety",{}).get("genericSkillsCandidateEntriesRequireSiteSectorLinkage") is True,"Timor-Leste generic skills entries require site/sector linkage")
require(tl_pack.get("officialSendingAgency",{}).get("name")=="National Directorate of Overseas Employment (NDOE)","Timor-Leste sending agency must remain NDOE")
tl_current=tl_readiness.get("currentManufacturing",{})
require(tl_current.get("diliSchedule",{}).get("status")=="verified_direct_official","Timor-Leste Dili Manufacturing schedule must remain direct-official verified")
require(tl_current.get("baucauSchedule",{}).get("status")=="discovery_only_direct_detail_pending","Timor-Leste Baucau must remain discovery-only until direct detail is captured")
require(tl_current.get("skillsCandidates",{}).get("status")=="official_country_entries_site_sector_linkage_pending","Timor-Leste skills-candidate entries must remain linkage-pending")
require(tl_current.get("finalResult",{}).get("status")=="awaiting_verified_current_cycle_final_result","Timor-Leste final result must remain gated")
require(tl_readiness.get("otherSector",{}).get("mustNotPopulateManufacturing") is True,"Timor-Leste Fishery evidence must never populate Manufacturing")
require(tl_readiness.get("betaReadiness",{}).get("status")=="blocked","Timor-Leste beta must remain blocked")
require(tl_discovery.get("exactPromotionAllowed") is False,"Timor-Leste Baucau discovery cannot promote exact rules")
require(tl_other.get("excludedFromManufacturing") is True,"Timor-Leste Fishery evidence must be explicitly excluded")
tl_doc_ids={p.get("id") for p in tl_docs.get("packs",[])}
require({"tl_9th_registration_documents_hold","tl_official_contact"}.issubset(tl_doc_ids),"Timor-Leste document packs must preserve HOLD plus official contact")
tl_hold=next((p for p in tl_docs.get("packs",[]) if p.get("id")=="tl_9th_registration_documents_hold"),{})
require(tl_hold.get("items")==[],"Timor-Leste registration HOLD pack must contain no invented checklist items")
tl_exact_ids={row.get("id") for row in tl_exact.get("answers",[])}
for exact_id in [
    "tl_2026_sending_authority","tl_2026_dili_registration_window","tl_2026_dili_test_notice",
    "tl_2026_dili_test_period","tl_2026_point_system","tl_2026_baucau_state",
    "tl_2026_skills_candidates_state","tl_no_job_guarantee"
]:
    require(exact_id in tl_exact_ids,f"Timor-Leste exact-answer catalog missing {exact_id}")


pk_entry=routes["pk-e9-manufacturing-2026"]
pk_pack=load("docs/data/pk_e9_manufacturing_2026.json")
pk_exact=load("docs/data/pk_exact_answer_rules_2026.json")
pk_docs=load("docs/data/pk_document_packs_2026.json")
pk_discovery=load("docs/data/pk_manufacturing_discovery_2026.json")
pk_special=load("docs/data/pk_special_eps_topik_2026.json")
pk_readiness=load("docs/data/pk_stage_readiness_2026.json")
pk_oec=load("docs/data/pk_oec_portal_2026.json")
require(pk_entry.get("lifecycle")=="research_hold" and pk_entry.get("publicAvailability")=="preview_only","Pakistan registry route must remain preview-only HOLD")
require(pk_pack.get("lifecycle")=="research_hold" and pk_pack.get("publicAvailability")=="preview_only","Pakistan pack must remain preview-only HOLD")
require(pk_pack.get("safety",{}).get("betaIntakeOpen") is False,"Pakistan beta intake must remain closed")
require(pk_pack.get("safety",{}).get("cityRoundFactsRequireManufacturingSectorLinkage") is True,"Pakistan city-round facts must require Manufacturing linkage")
require(pk_pack.get("safety",{}).get("discoveryManufacturingTitleMustNotBecomeExact") is True,"Pakistan Manufacturing discovery title must not auto-promote")
require(pk_pack.get("safety",{}).get("specialFactsExcludedFromManufacturing") is True,"Pakistan Special facts must stay outside Manufacturing")
require(pk_pack.get("officialSendingAgency",{}).get("name")=="Overseas Employment Corporation (OEC)","Pakistan sending agency must remain OEC")
require(pk_pack.get("oecPortalEvidenceFile")=="data/pk_oec_portal_2026.json","Pakistan pack must link current OEC portal evidence")
pk_current=pk_readiness.get("currentManufacturing",{})
require(pk_current.get("cityRoundSchedule",{}).get("status")=="official_country_round_sector_linkage_pending","Pakistan city-round schedule must remain sector-linkage pending")
require(pk_current.get("oecPortal2026",{}).get("status")=="verified_country_round_operation_manufacturing_linkage_pending","Pakistan OEC portal operation must remain verified without Manufacturing promotion")
require(pk_current.get("manufacturingDiscovery",{}).get("status")=="discovery_only_not_promoted","Pakistan Manufacturing discovery must remain non-promoted")
require(pk_current.get("fee",{}).get("status")=="manufacturing_cycle_specific_unverified","Pakistan Manufacturing fee must remain unresolved")
require(pk_current.get("fee",{}).get("oecPreRegistrationChallan",{}).get("amountPkr")==1000 and pk_current.get("fee",{}).get("oecPreRegistrationChallan",{}).get("epsTopikExamFee") is False,"Pakistan OEC PKR 1,000 challan must never become EPS-TOPIK exam fee")
require(pk_current.get("documents",{}).get("status")=="manufacturing_checklist_not_reconstructed","Pakistan Manufacturing checklist must remain HOLD")
require(pk_readiness.get("specialRoute",{}).get("mustNotPopulateManufacturing") is True,"Pakistan Special route must never populate Manufacturing")
require(pk_readiness.get("betaReadiness",{}).get("status")=="blocked","Pakistan beta must remain blocked")
require(pk_discovery.get("exactPromotionAllowed") is False,"Pakistan discovery evidence cannot promote exact rules")
require(pk_special.get("excludedFromManufacturing") is True,"Pakistan Special evidence must be explicitly excluded")
require(pk_oec.get("scope")=="pakistan_eps_2026_oec_portal_country_round_not_manufacturing_sector_linkage","Pakistan OEC evidence must remain country-round scoped")
pk_oec_sources={row.get("id"):row for row in pk_oec.get("sources",[])}
require(pk_oec_sources.get("pk_oec_2026_test_schedule_lookup",{}).get("facts",{}).get("individualScheduleLookupLive") is True,"Pakistan OEC individual test-schedule lookup must remain verified")
require(pk_oec_sources.get("pk_oec_2026_test_schedule_lookup",{}).get("facts",{}).get("manufacturingSectorLinkageEstablished") is False,"Pakistan OEC schedule lookup must not auto-establish Manufacturing linkage")
require(pk_oec_sources.get("pk_oec_2026_pre_registration",{}).get("facts",{}).get("feeChallanPkr")==1000 and pk_oec_sources.get("pk_oec_2026_pre_registration",{}).get("facts",{}).get("isEpsTopikExamFee") is False,"Pakistan OEC PKR 1,000 pre-registration challan scope must remain explicit")
require("treating PKR 1,000 as the EPS-TOPIK exam fee" in pk_oec.get("promotionRules",{}).get("mustRemainHold",[]),"Pakistan OEC evidence must explicitly forbid exam-fee conflation")
pk_doc_ids={p.get("id") for p in pk_docs.get("packs",[])}
require({"pk_manufacturing_registration_documents_hold","pk_official_contact","pk_oec_2026_prereg_portal_snapshot"}.issubset(pk_doc_ids),"Pakistan document packs must preserve Manufacturing HOLD, official contact and OEC portal snapshot")
pk_hold=next((p for p in pk_docs.get("packs",[]) if p.get("id")=="pk_manufacturing_registration_documents_hold"),{})
require(pk_hold.get("items")==[],"Pakistan Manufacturing registration HOLD pack must contain no invented checklist items")
pk_oec_pack=next((p for p in pk_docs.get("packs",[]) if p.get("id")=="pk_oec_2026_prereg_portal_snapshot"),{})
require(pk_oec_pack.get("paidChallan",{}).get("amountPkr")==1000 and pk_oec_pack.get("paidChallan",{}).get("epsTopikExamFee") is False,"Pakistan OEC portal document pack must scope PKR 1,000 as non-exam-fee")
pk_exact_ids={row.get("id") for row in pk_exact.get("answers",[])}
for exact_id in [
    "pk_2026_sending_authority","pk_2026_city_registration_window","pk_2026_schedule_state",
    "pk_2026_manufacturing_linkage","pk_2026_special_firewall","pk_no_job_guarantee",
    "pk_2026_oec_schedule_lookup","pk_2026_oec_prereg_dob","pk_2026_oec_prereg_fields",
    "pk_2026_oec_prereg_challan","pk_2026_oec_challan_upload","pk_2026_oec_registration_lookup"
]:
    require(exact_id in pk_exact_ids,f"Pakistan exact-answer catalog missing {exact_id}")


tj_entry=routes["tj-e9-manufacturing-2026"]
tj_pack=load("docs/data/tj_e9_manufacturing_2026.json")
tj_exact=load("docs/data/tj_exact_answer_rules_2026.json")
tj_docs=load("docs/data/tj_document_packs_2026.json")
tj_notice=load("docs/data/tj_registration_notice_2026.json")
tj_readiness=load("docs/data/tj_stage_readiness_2026.json")
require(tj_entry.get("lifecycle")=="research_hold" and tj_entry.get("publicAvailability")=="preview_only","Tajikistan registry route must remain preview-only HOLD")
require(tj_pack.get("lifecycle")=="research_hold" and tj_pack.get("publicAvailability")=="preview_only","Tajikistan pack must remain preview-only HOLD")
require(tj_pack.get("safety",{}).get("betaIntakeOpen") is False,"Tajikistan beta intake must remain closed")
require(tj_pack.get("safety",{}).get("manufacturingSectorCrossSourceVerified") is True,"Tajikistan Manufacturing sector linkage must remain cross-source verified")
require(tj_pack.get("safety",{}).get("postSelectionFactsRequireCurrentArtifact") is True,"Tajikistan post-selection facts must remain artifact-gated")
require(tj_pack.get("officialSendingAgency",{}).get("name")=="Agency of Overseas Employment","Tajikistan sending agency must remain Agency of Overseas Employment")
require(tj_pack.get("registrationNoticeFile")=="data/tj_registration_notice_2026.json","Tajikistan pack must link official registration notice evidence")
require(tj_pack.get("documentPacksFile")=="data/tj_document_packs_2026.json","Tajikistan pack must link verified registration document pack")
tj_current=tj_readiness.get("currentCycle",{})
require(tj_current.get("manufacturingLinkage",{}).get("status")=="verified_cross_source","Tajikistan Manufacturing linkage must remain verified_cross_source")
require(tj_current.get("registration",{}).get("status")=="closed_verified","Tajikistan 2026 Manufacturing registration must remain closed_verified")
require(tj_current.get("eligibilityAndDocuments",{}).get("status")=="verified_current_local","Tajikistan eligibility/documents must remain verified from current local notice")
require(tj_current.get("epsTopikSchedule",{}).get("status")=="completed_period_verified","Tajikistan EPS-TOPIK schedule must remain verified")
require(tj_current.get("skillsAndFinalResult",{}).get("status")=="awaiting_verified_current_cycle_result","Tajikistan skills/final result must remain gated")
require(tj_readiness.get("betaReadiness",{}).get("status")=="blocked","Tajikistan beta must remain blocked")
require(tj_notice.get("facts",{}).get("registrationPeriod")=="2026-03-02 through 2026-03-05","Tajikistan registration window must match official Manufacturing notice")
require(tj_notice.get("facts",{}).get("examFeeSomoni")==330,"Tajikistan official exam fee must remain 330 somoni")
require(tj_notice.get("facts",{}).get("dobRange")=="1986-03-03 through 2008-03-02","Tajikistan cycle-specific DOB range must remain exact")
require(tj_notice.get("crossSourceLink",{}).get("matchingRegistrationPeriod") is True and tj_notice.get("crossSourceLink",{}).get("manufacturingSectorFromLocalOfficialNotice") is True,"Tajikistan Manufacturing cross-source linkage must stay explicit")
tj_doc_ids={p.get("id") for p in tj_docs.get("packs",[])}
require("tj_2026_manufacturing_registration" in tj_doc_ids,"Tajikistan verified Manufacturing registration document pack is required")
tj_regpack=next((p for p in tj_docs.get("packs",[]) if p.get("id")=="tj_2026_manufacturing_registration"),{})
require(len(tj_regpack.get("items",[]))==4,"Tajikistan registration pack must preserve four verified registration items")
tj_exact_ids={row.get("id") for row in tj_exact.get("answers",[])}
for exact_id in [
    "tj_2026_manufacturing_linkage","tj_2026_registration_window","tj_2026_exam_fee",
    "tj_2026_age_rule","tj_2026_registration_docs","tj_2026_test_notice",
    "tj_2026_test_period","tj_2026_point_system","tj_2026_final_state","tj_no_job_guarantee"
]:
    require(exact_id in tj_exact_ids,f"Tajikistan exact-answer catalog missing {exact_id}")


kg_entry=routes["kg-e9-manufacturing-2026"]
kg_pack=load("docs/data/kg_e9_manufacturing_2026.json")
kg_exact=load("docs/data/kg_exact_answer_rules_2026.json")
kg_docs=load("docs/data/kg_document_packs_2026.json")
kg_special=load("docs/data/kg_special_eps_topik_2026.json")
kg_additional=load("docs/data/kg_additional_general_round_2026.json")
kg_readiness=load("docs/data/kg_stage_readiness_2026.json")
kg_post_contract=load("docs/data/kg_post_contract_process_2026.json")
require(kg_entry.get("lifecycle")=="research_hold" and kg_entry.get("publicAvailability")=="preview_only","Kyrgyzstan registry route must remain preview-only HOLD")
require(kg_pack.get("lifecycle")=="research_hold" and kg_pack.get("publicAvailability")=="preview_only","Kyrgyzstan pack must remain preview-only HOLD")
require(kg_pack.get("safety",{}).get("betaIntakeOpen") is False,"Kyrgyzstan beta intake must remain closed")
require(kg_pack.get("safety",{}).get("manufacturingSectorCrossSourceVerified") is True,"Kyrgyzstan Manufacturing sector linkage must remain cross-source verified")
require(kg_pack.get("safety",{}).get("laterGeneralRoundMustNotOverwrite13thManufacturing") is True,"Kyrgyzstan later general round must not overwrite the 13th Manufacturing route")
require(kg_pack.get("safety",{}).get("specialRouteFactsExcludedFromManufacturing") is True,"Kyrgyzstan Special facts must remain outside Regular Manufacturing")
require(kg_pack.get("exactAnswerRulesFile")=="data/kg_exact_answer_rules_2026.json","Kyrgyzstan pack must link exact answers")
require(kg_pack.get("documentPacksFile")=="data/kg_document_packs_2026.json","Kyrgyzstan pack must link document packs")
require(kg_pack.get("stageReadinessFile")=="data/kg_stage_readiness_2026.json","Kyrgyzstan pack must link readiness")
kg_current=kg_readiness.get("currentCycle",{})
require(kg_current.get("manufacturingSectorLinkage",{}).get("status")=="verified_cross_source","Kyrgyzstan Manufacturing sector linkage must remain verified_cross_source")
require(kg_current.get("registration",{}).get("status")=="closed_verified","Kyrgyzstan 13th registration must remain closed_verified")
require(kg_current.get("registrationDocuments",{}).get("status")=="verified_current_cycle","Kyrgyzstan registration documents must remain current-cycle verified")
require(kg_current.get("epsTopik",{}).get("status")=="completed_verified","Kyrgyzstan Round 1 must remain completed_verified")
require(kg_current.get("skillsTest",{}).get("status")=="completed_verified","Kyrgyzstan Skills Test must remain completed_verified")
require(kg_current.get("postSelectionRoster",{}).get("status")=="verified_current_cycle_historical_window","Kyrgyzstan June post-selection/roster window must remain verified but historical")
require(kg_current.get("slcVisaDeparture",{}).get("status")=="partial_process_verified_exact_slc_visa_pending","Kyrgyzstan post-contract process may be verified while exact SLC/visa rules remain gated")
require(kg_current.get("slcContractProcess",{}).get("status")=="verified_country_process_exact_slc_pending","Kyrgyzstan contract-before-training process must remain verified without inventing exact SLC instructions")
require(kg_current.get("predepartureTraining",{}).get("status")=="verified_country_process_2026_five_day","Kyrgyzstan pre-departure training must remain verified as a 5-day country process")
require(kg_current.get("departureProcess",{}).get("status")=="verified_country_process_2026_individual_assignment_pending","Kyrgyzstan departure process must remain verified while individual assignments stay gated")
require(kg_readiness.get("betaReadiness",{}).get("status")=="blocked","Kyrgyzstan beta must remain blocked")
require(kg_special.get("excludedFromRegular13thManufacturing") is True,"Kyrgyzstan Special route must be excluded from Regular 13th Manufacturing")
require(kg_additional.get("excludedFromRegular13thManufacturing") is True,"Kyrgyzstan later additional/general round must be excluded from Regular 13th Manufacturing")
require(kg_post_contract.get("scope")=="country_process_2026_not_individual_departure_assignment","Kyrgyzstan post-contract evidence must remain country-process scoped")
require(all(src.get("facts",{}).get("predepartureTrainingDays")==5 for src in kg_post_contract.get("sources",[]) if src.get("id","").startswith("kg_eps_departure_")),"Kyrgyzstan post-contract evidence must preserve 5-day training")
require("individual departure date or flight assignment" in kg_post_contract.get("promotionRules",{}).get("mustRemainHold",[]),"Kyrgyzstan individual departure assignment must remain HOLD")
kg_doc_ids={p.get("id") for p in kg_docs.get("packs",[])}
require({"kg_13th_online_registration","kg_13th_postselection_roster"}.issubset(kg_doc_ids),"Kyrgyzstan document packs must cover registration and post-selection roster")
kg_regpack=next((p for p in kg_docs.get("packs",[]) if p.get("id")=="kg_13th_online_registration"),{})
require(kg_regpack.get("fee",{}).get("amountUsd")==28 and kg_regpack.get("fee",{}).get("currentForThisCycle") is True,"Kyrgyzstan 13th-cycle fee must remain US$28")
require(len(kg_regpack.get("items",[]))==4,"Kyrgyzstan online registration pack must preserve four verified items")
kg_postpack=next((p for p in kg_docs.get("packs",[]) if p.get("id")=="kg_13th_postselection_roster"),{})
require(kg_postpack.get("medicalWindow")=="2026-06-09 through 2026-06-11","Kyrgyzstan current-cycle medical window must remain exact")
require(kg_postpack.get("fullPackageSubmissionDate")=="2026-06-15","Kyrgyzstan current-cycle full-package submission date must remain exact")
kg_exact_ids={row.get("id") for row in kg_exact.get("answers",[])}
for exact_id in [
    "kg_2026_manufacturing_linkage","kg_2026_registration_window","kg_2026_exam_fee",
    "kg_2026_registration_files","kg_2026_test_announcement","kg_2026_bishkek_test_period",
    "kg_2026_osh_test_period","kg_2026_skills_dates","kg_2026_postselection_documents",
    "kg_2026_roster_rule","kg_2026_anti_broker_rule","kg_2026_later_round_firewall","kg_2026_special_firewall",
    "kg_2026_contract_before_training_process","kg_2026_predeparture_training_five_day","kg_2026_departure_process"
]:
    require(exact_id in kg_exact_ids,f"Kyrgyzstan exact-answer catalog missing {exact_id}")


mm_verify=load("docs/data/mm_manufacturing_verification_2026.json")
require(mm_verify.get("status")=="pending_manufacturing_verification","Myanmar verification dossier must remain pending Manufacturing verification")
require(mm_verify.get("routeId") is None,"Myanmar verification dossier must not expose a promoted routeId")
require(mm_verify.get("officialSendingAgency",{}).get("name")=="Public Overseas Employment Agency (POEA)","Myanmar sending agency must remain POEA")
mm_rows=mm_verify.get("current2026Evidence",{}).get("hrdScheduleIndex",{}).get("observedSectorRows",[])
require({row.get("sector") for row in mm_rows}=={"Agriculture·Livestock","Construction","Forestry"},"Myanmar 2026 negative-evidence dossier must preserve the three captured non-Manufacturing sectors")
require(mm_verify.get("current2026Evidence",{}).get("hrdScheduleIndex",{}).get("manufacturingRowCaptured") is False,"Myanmar dossier must not claim a captured 2026 Manufacturing row")
require(mm_verify.get("historicalManufacturingEvidence",{}).get("status")=="historical_only_not_2026_recruitment","Myanmar historical Manufacturing evidence must never become a 2026 route")
require(mm_verify.get("historicalManufacturingEvidence",{}).get("facts",{}).get("examCycle")=="16th EPS-TOPIK Manufacturing second batch","Myanmar historical Manufacturing cycle lineage must remain explicit")
require(mm_verify.get("historicalManufacturingEvidence",{}).get("facts",{}).get("successfulCandidates")==4249,"Myanmar historical Manufacturing pass-count lineage must remain 4,249")
require(mm_verify.get("historicalManufacturingEvidence",{}).get("facts",{}).get("jobApplicationPeriod")=="2025-07-21 through 2025-08-01","Myanmar historical Manufacturing job-application window must remain exact")
require(len(mm_verify.get("promotionRule",{}).get("requiredEvidence",[]))>=3,"Myanmar promotion rule must state direct current Manufacturing evidence requirements")
require(len(mm_verify.get("promotionRule",{}).get("prohibitedInference",[]))>=3,"Myanmar promotion rule must prohibit other-sector/historical inference")

coverage=load("docs/data/country_coverage_matrix_2026.json")
coverage_rows={row.get("country"):row for row in coverage.get("countries",[])}
expected_sending={"PH","TH","ID","VN","LK","MN","UZ","PK","KH","CN","BD","KG","NP","MM","TL","LA","TJ"}
require(set(coverage_rows)==expected_sending,"coverage matrix must account for exactly all 17 HRD Korea EPS sending countries")
require(coverage.get("summary",{}).get("listedSendingCountries")==17,"coverage matrix listedSendingCountries must remain 17")
require(coverage.get("summary",{}).get("registeredManufacturingCountryPacks")==16,"coverage matrix must report 16 registered Manufacturing Country Packs")
require(coverage.get("summary",{}).get("pendingManufacturingVerification")==1,"coverage matrix must report 1 pending Manufacturing country")
registered={code for code,row in coverage_rows.items() if row.get("status")=="country_pack_registered"}
pending={code for code,row in coverage_rows.items() if row.get("status")=="pending_manufacturing_verification"}
require(pending=={"MM"},"only Myanmar may remain pending Manufacturing verification")
require(len(registered)==16,"coverage matrix must contain exactly 16 registered Manufacturing Country Packs")
registry_countries={entry.get("country") for entry in routes.values()}
require(registered==registry_countries,"coverage registered-country set must exactly match country_packs_v1 registry")
for code in registered:
    row=coverage_rows[code]
    require(row.get("routeId") in routes,f"{code}: coverage routeId must exist in country registry")
    require(routes[row.get("routeId")].get("country")==code,f"{code}: coverage routeId country mismatch")
for code in pending:
    row=coverage_rows[code]
    require(code not in registry_countries,f"{code}: pending country must not have a promoted Manufacturing Country Pack")
    require(len(row.get("blockers",[]))>=1,f"{code}: pending coverage row must state blockers")
    require(bool(row.get("officialSendingAgency")),f"{code}: pending coverage row must retain official sending agency")
require(coverage_rows["KG"].get("routeId")=="kg-e9-manufacturing-2026","Kyrgyzstan coverage row must point to promoted Manufacturing Country Pack")
require(coverage_rows["KG"].get("promotionEvidence",{}).get("rule","").find("2026-02-23 through 2026-02-27")>=0,"Kyrgyzstan coverage must preserve cross-source Manufacturing promotion evidence")
require(coverage_rows["MM"].get("evidence",{}).get("note","").find("Manufacturing")>=0,"Myanmar pending reason must explicitly discuss missing Manufacturing verification")
require(coverage_rows["MM"].get("verificationDossierFile")=="data/mm_manufacturing_verification_2026.json","Myanmar coverage row must link the verification dossier")
require(coverage_rows["MM"].get("previewFile")=="mm.html","Myanmar pending coverage row must link the public verification preview")
require(set(coverage_rows["MM"].get("evidence",{}).get("current2026OtherSectors",[]))=={"Agriculture·Livestock","Construction","Forestry"},"Myanmar coverage must preserve captured 2026 non-Manufacturing sectors")
require(coverage_rows["MM"].get("evidence",{}).get("historicalManufacturingSource","").startswith("https://www.mol.gov.mm/"),"Myanmar coverage must preserve official historical Manufacturing lineage")
require(coverage_rows["TJ"].get("routeId")=="tj-e9-manufacturing-2026","Tajikistan coverage row must point to promoted Manufacturing Country Pack")
require(coverage_rows["TJ"].get("promotionEvidence",{}).get("rule","").find("same 2026-03-02 through 2026-03-05 registration window")>=0,"Tajikistan coverage must preserve cross-source Manufacturing promotion evidence")


dashboard=load("docs/data/country_readiness_dashboard_2026.json")
dashboard_rows={row.get("country"):row for row in dashboard.get("rows",[])}
require(set(dashboard_rows)==set(coverage_rows),"readiness dashboard must account for the same 17 sending countries as coverage matrix")
require(dashboard.get("summary",{}).get("sendingCountries")==17,"readiness dashboard must report 17 sending countries")
require(dashboard.get("summary",{}).get("registeredCountryPacks")==16,"readiness dashboard must report 16 registered Country Packs")
require(dashboard.get("summary",{}).get("betaHold")==1,"readiness dashboard must report exactly one beta HOLD route")
require(dashboard.get("summary",{}).get("researchHold")==15,"readiness dashboard must report 15 research HOLD routes")
require(dashboard.get("summary",{}).get("pendingManufacturingVerification")==1,"readiness dashboard must report 1 pending Manufacturing country")
require(dashboard.get("summary",{}).get("datedReviewTriggers")==2,"readiness dashboard must report exactly two dated review triggers")
require(dashboard.get("summary",{}).get("betaReady")==0,"readiness dashboard must not claim any beta-ready route")
require(dashboard_rows["ID"].get("packState")=="beta_hold","Indonesia readiness state must remain beta_hold")
require(dashboard_rows["ID"].get("betaState")=="pending_manual_approval","Indonesia beta must remain pending manual approval")
require(len(dashboard_rows["ID"].get("releaseGates",[]))==3,"Indonesia readiness must separate three beta release gates")
require(len(dashboard_rows["ID"].get("validationGaps",[]))>=2,"Indonesia readiness must separate validation gaps from beta release gates")
require(dashboard_rows["ID"].get("blockers")==dashboard_rows["ID"].get("releaseGates"),"Indonesia generic blockers must contain only actual beta release gates")
require(any("100% PASS" in str(x) and "not" in str(x).lower() for x in dashboard_rows["ID"].get("validationGaps",[])),"Indonesia validation-gap copy must say safe HOLDs are not automatic beta blockers")
for code in registered-{"ID"}:
    require(dashboard_rows[code].get("packState")=="research_hold",f"{code}: registered non-Indonesia route must remain research_hold")
    require(dashboard_rows[code].get("betaState")=="blocked",f"{code}: registered research route beta must remain blocked")
for code in pending:
    require(dashboard_rows[code].get("packState")=="pending_manufacturing_verification",f"{code}: readiness state must remain pending Manufacturing verification")
    require(dashboard_rows[code].get("routeId") is None,f"{code}: pending readiness row must not expose a promoted routeId")
require(dashboard_rows["LK"].get("nextReview",{}).get("date")=="2026-10-12","Sri Lanka readiness review date must remain 2026-10-12")
require(dashboard_rows["TH"].get("nextReview",{}).get("date")=="2026-10-19","Thailand readiness review date must remain 2026-10-19")
require(dashboard_rows["MM"].get("verificationDossierFile")=="data/mm_manufacturing_verification_2026.json","Myanmar readiness row must link the verification dossier")
require(dashboard_rows["MM"].get("detailsPage")=="mm.html","Myanmar readiness row must link the public verification preview")
require(dashboard_rows["MM"].get("routeId") is None and dashboard_rows["MM"].get("packState")=="pending_manufacturing_verification","Myanmar must remain pending without a promoted route")
require(any("mol.gov.mm" in s for s in dashboard_rows["MM"].get("nextReview",{}).get("officialSources",[])),"Myanmar next-review sources must include the Ministry of Labour EPS page")
dated={code for code,row in dashboard_rows.items() if row.get("nextReview",{}).get("type")=="dated_official_review"}
require(dated=={"LK","TH"},"only Sri Lanka and Thailand should have dated official review triggers in the 2026-10-06 snapshot")
for code,row in dashboard_rows.items():
    require(len(row.get("blockers",[]))>=1,f"{code}: readiness row must include at least one blocker")
    sources=row.get("nextReview",{}).get("officialSources",[])
    require(len(sources)>=1,f"{code}: readiness row must include an official review source")
    for source in sources:
        require(str(source).startswith("https://"),f"{code}: readiness source must use HTTPS")
    if row.get("routeId"):
        require(row.get("routeId") in routes,f"{code}: readiness routeId must exist in country registry")

countries=(ROOT/"docs/countries.html").read_text(encoding="utf-8")
readiness_page=(ROOT/"docs/readiness.html").read_text(encoding="utf-8")
readiness_js=(ROOT/"docs/readiness.js").read_text(encoding="utf-8")
myanmar=(ROOT/"docs/mm.html").read_text(encoding="utf-8")
nepal=(ROOT/"docs/np.html").read_text(encoding="utf-8")
vietnam=(ROOT/"docs/vn.html").read_text(encoding="utf-8")
philippines=(ROOT/"docs/ph.html").read_text(encoding="utf-8")
thailand=(ROOT/"docs/th.html").read_text(encoding="utf-8")
bangladesh=(ROOT/"docs/bd.html").read_text(encoding="utf-8")
srilanka=(ROOT/"docs/lk.html").read_text(encoding="utf-8")
laos=(ROOT/"docs/la.html").read_text(encoding="utf-8")
uzbekistan=(ROOT/"docs/uz.html").read_text(encoding="utf-8")
mongolia=(ROOT/"docs/mn.html").read_text(encoding="utf-8")
china=(ROOT/"docs/cn.html").read_text(encoding="utf-8")
cambodia=(ROOT/"docs/kh.html").read_text(encoding="utf-8")
timorleste=(ROOT/"docs/tl.html").read_text(encoding="utf-8")
pakistan=(ROOT/"docs/pk.html").read_text(encoding="utf-8")
tajikistan=(ROOT/"docs/tj.html").read_text(encoding="utf-8")
kyrgyzstan=(ROOT/"docs/kg.html").read_text(encoding="utf-8")
require("RESEARCH / HOLD" in countries and "preview_only" not in countries,"countries page must visibly label Nepal HOLD")
require("PENDING MANUFACTURING VERIFICATION" in countries and "Myanmar" in countries,"countries page must expose the remaining pending Manufacturing country")
require("Agriculture/Livestock, Construction and Forestry" in countries and "16th EPS-TOPIK Manufacturing second-batch" in countries,"Myanmar pending UI must distinguish current non-Manufacturing and historical Manufacturing evidence")
require('href="tj.html"' in countries and 'href="kg.html"' in countries,"countries page must expose promoted Tajikistan and Kyrgyzstan Country Packs")
require('href="readiness.html"' in countries,"countries page must link readiness dashboard")
require("2026 COUNTRY READINESS" in readiness_page and 'id="summary"' in readiness_page and 'id="readiness"' in readiness_page,"readiness page must expose summary and readiness containers")
require("A validation gap is not automatically a beta blocker" in readiness_page,"readiness page must explain that validation gaps are not automatic beta blockers")
require("country_readiness_dashboard_2026.json" in readiness_js,"readiness renderer must load the readiness dashboard data")
require("Beta release gates" in readiness_js and "Validation gaps — not automatic beta blockers" in readiness_js,"readiness renderer must render release gates separately from validation gaps")
require("No promoted Manufacturing routeId" in readiness_js,"readiness renderer must visibly distinguish pending countries")
require('href="kg.html"' in countries and 'href="mm.html"' in countries,"Kyrgyzstan must stay promoted while Myanmar exposes only a pending verification preview")
require("PENDING MANUFACTURING VERIFICATION" in countries,"pending-country UI must clearly preserve the remaining unverified route state")
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
require("RESEARCH / HOLD" in mongolia and "2026-03-25" in mongolia and "2026-06-26" in mongolia,"Mongolia preview must visibly remain HOLD with verified registration/test timeline")
require("Special EPS-TOPIK remains a separate route" in mongolia and "Final-result linkage" in mongolia,"Mongolia preview shell must visibly preserve Special and result-linkage gates")
require('href="beta.html"' not in mongolia and 'id="betaForm"' not in mongolia,"Mongolia preview must not expose beta enrollment")
require("RESEARCH / HOLD" in china and "2026-03-18" in china and "2026-09-11" in china,"China preview must visibly remain HOLD with verified registration/test timeline")
require("2026-09-30" in china and "US$28" in china and "not promoted" in china,"China preview must preserve generic skill-candidate and fee gates")
require('href="beta.html"' not in china and 'id="betaForm"' not in china,"China preview must not expose beta enrollment")
require("RESEARCH / HOLD" in cambodia and "2026-08-06" in cambodia and "2026-08-21" in cambodia,"Cambodia preview must visibly remain HOLD with official August artifacts")
require("Agriculture/Livestock and Special EPS-TOPIK are separate routes" in cambodia,"Cambodia preview must visibly preserve sector/special firewalls")
require("Verified Manufacturing schedule" in cambodia and "2026-05-22" in cambodia and "2026-07-15" in cambodia,"Cambodia preview must show verified 12th Manufacturing schedule")
require('href="beta.html"' not in cambodia and 'id="betaForm"' not in cambodia,"Cambodia preview must not expose beta enrollment")
require("RESEARCH / HOLD" in timorleste and "2026-03-09" in timorleste and "2026-07-30" in timorleste,"Timor-Leste preview must visibly remain HOLD with direct-official Dili timeline")
require("DISCOVERY ONLY" in timorleste and "2026-09-22" in timorleste and "Fishery is a separate sector" in timorleste,"Timor-Leste preview must show Baucau discovery, generic skills linkage gate and Fishery firewall")
require('href="beta.html"' not in timorleste and 'id="betaForm"' not in timorleste,"Timor-Leste preview must not expose beta enrollment")
require("RESEARCH / HOLD" in pakistan and "2026-03-31" in pakistan and "2026-04-08" in pakistan,"Pakistan preview must visibly remain HOLD with verified city-round registration window")
require("Manufacturing-specific exact rules yet" in pakistan and "DISCOVERY ONLY" in pakistan and "2026-08-21" in pakistan,"Pakistan preview must show Manufacturing linkage gate, discovery-only state and Special result separation")
require("OEC 2026 PORTAL VERIFIED" in pakistan and "1986-03-31" in pakistan and "PKR 1,000" in pakistan,"Pakistan preview must expose OEC 2026 portal operation and scoped pre-registration facts")
require("EPS-TOPIK exam fee" in pakistan,"Pakistan preview must explicitly prevent PKR 1,000 exam-fee conflation")
require('href="beta.html"' not in pakistan and 'id="betaForm"' not in pakistan,"Pakistan preview must not expose beta enrollment")
require("RESEARCH / HOLD" in tajikistan and "330 somoni" in tajikistan and "2026-03-02" in tajikistan and "2026-03-29" in tajikistan,"Tajikistan preview must show verified Manufacturing facts")
require("3.5×4.5" in tajikistan and "Foreign passport" in tajikistan,"Tajikistan preview must expose verified registration-document basics")
require('href="beta.html"' not in tajikistan and 'id="betaForm"' not in tajikistan,"Tajikistan preview must not expose beta enrollment")
require("RESEARCH / HOLD" in kyrgyzstan and "2026-02-23" in kyrgyzstan and "US$28" in kyrgyzstan,"Kyrgyzstan preview must show verified Manufacturing registration and fee")
require("2026-05-30" in kyrgyzstan and "2026-06-09" in kyrgyzstan and "2 жылдык" in kyrgyzstan,"Kyrgyzstan preview must expose Skills Test, post-selection medical and two-year roster facts")
require("ANTI-BROKER RULE" in kyrgyzstan and "ROUTE FIREWALLS" in kyrgyzstan,"Kyrgyzstan preview must expose anti-broker and later-route firewalls")
require('href="beta.html"' not in kyrgyzstan and 'id="betaForm"' not in kyrgyzstan,"Kyrgyzstan preview must not expose beta enrollment")
require("PENDING MANUFACTURING VERIFICATION" in myanmar and "No promoted Manufacturing routeId" in myanmar,"Myanmar preview must remain pending without a promoted Manufacturing route")
require("Agriculture/Livestock" in myanmar and "Construction" in myanmar and "Forestry" in myanmar,"Myanmar preview must show the three captured 2026 non-Manufacturing sectors")
require("16th EPS-TOPIK Manufacturing second batch" in myanmar and "4,249" in myanmar and "2025-07-21" in myanmar,"Myanmar preview must preserve historical Manufacturing lineage without promoting it")
require('href="beta.html"' not in myanmar and 'id="betaForm"' not in myanmar,"Myanmar verification preview must not expose beta enrollment")

if failures:
    print("COUNTRY_PACK_CONTRACT_FAIL")
    for failure in failures: print("- "+failure)
    raise SystemExit(1)

print("COUNTRY_PACK_CONTRACT_PASS routes=%d stages=%d nepal=research_hold vietnam=research_hold philippines=research_hold thailand=research_hold bangladesh=research_hold srilanka=research_hold laos=research_hold uzbekistan=research_hold mongolia=research_hold china=research_hold cambodia=research_hold timorleste=research_hold pakistan=research_hold tajikistan=research_hold kyrgyzstan=research_hold" % (len(routes),len(EXPECTED)))
