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
require({"id-e9-manufacturing-2026","np-e9-manufacturing-2026"}.issubset(routes),"registry must include Indonesia and Nepal")

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

countries=(ROOT/"docs/countries.html").read_text(encoding="utf-8")
nepal=(ROOT/"docs/np.html").read_text(encoding="utf-8")
require("RESEARCH / HOLD" in countries and "preview_only" not in countries,"countries page must visibly label Nepal HOLD")
require("Research HOLD" in nepal and "Beta registration/access अहिले खुला छैन" in nepal and "2026-07-21" in nepal,"Nepal page must visibly keep beta closed while acknowledging the verified 2026 notice")
require("2026 EXACT FACTS" in nepal and "US$28" in nepal and "5,000" in nepal,"Nepal preview must expose verified first-phase facts without opening beta")
require("APPLICATION SYSTEM HISTORY" in nepal and "deadline extension" in nepal.lower(),"Nepal preview must disclose the registration interruption/resumption without claiming an extension")
require('href="beta.html"' not in nepal,"Nepal preview must not link to Indonesia beta enrollment")
require('id="betaForm"' not in nepal,"Nepal preview must not contain a beta enrollment form")

if failures:
    print("COUNTRY_PACK_CONTRACT_FAIL")
    for failure in failures: print("- "+failure)
    raise SystemExit(1)

print("COUNTRY_PACK_CONTRACT_PASS routes=%d stages=%d nepal=research_hold" % (len(routes),len(EXPECTED)))
