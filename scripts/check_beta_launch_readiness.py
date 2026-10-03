#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

parser = argparse.ArgumentParser()
parser.add_argument(
    "--allow-source-review-pending",
    action="store_true",
    help="Validate product/static integrity without requiring official-source launch readiness.",
)
args = parser.parse_args()

EXPECTED_STAGES = [
    "eligibility","registration","exam_fee","biometric","document_verify","exam_card",
    "eps_topik","skill_competency","final_selection","psychology_pre_job","mcu1",
    "job_application","roster","employer_selection","slc","post_slc_requirements",
    "visa_docs","predeparture_training","mcu3_departure","departure",
    "korea_entry_training","employer_handover","residence_registration",
    "eps_insurance_check","first_payroll_check","labor_support_ready","employment_maintenance",
]
EXPECTED_JOB_HOLDS = {"job_docs","job_scan","job_name","job_edit","job_submit"}

failures: list[str] = []

def require(condition: bool, message: str) -> None:
    if not condition:
        failures.append(message)

def load_json(path: str):
    return json.loads((ROOT / path).read_text(encoding="utf-8-sig"))

route = load_json("docs/data/id_e9_manufacturing_2026.json")
i18n = load_json("docs/data/id_e9_manufacturing_2026_id.json")
bqc = load_json("docs/data/broker_question_catalog_v1.json")
source = load_json("docs/data/source_review_status.json")
forms = load_json("docs/data/form_wizards_2026.json")
workplace = load_json("docs/data/workplace_reality_v1.json")
beta_program = load_json("docs/data/beta_program_v1.json")
departure_calls = load_json("docs/data/departure_calls_2026.json")
runtime = (ROOT / "docs/app-runtime.js").read_text(encoding="utf-8")
app_page = (ROOT / "docs/app.html").read_text(encoding="utf-8")
beta_page = (ROOT / "docs/beta.html").read_text(encoding="utf-8")
beta_js = (ROOT / "docs/beta.js").read_text(encoding="utf-8")
beta_target = (ROOT / "recruitment/BETA_TARGET.md").read_text(encoding="utf-8")
outreach = (ROOT / "recruitment/OUTREACH_ID.md").read_text(encoding="utf-8")
beta_tracker = (ROOT / "recruitment/BETA_TESTER_TRACKER.csv").read_text(encoding="utf-8-sig")
worker_recorder = (ROOT / "scripts/record_worker_interview.py").read_text(encoding="utf-8")

stage_ids = [row.get("id") for row in route.get("stages", [])]
require(stage_ids == EXPECTED_STAGES, "supported route must contain the locked 27 stages in exact order")

allowed_broker_states = {"complete", "guided_official", "prep_complete", "held_official_notice"}
for stage in route.get("stages", []):
    stage_id = stage.get("id", "<missing>")
    for field in ("title", "authority", "kind", "action", "brokerReplacement", "sourceUrl"):
        require(bool(str(stage.get(field, "")).strip()), f"{stage_id}: missing required route field {field}")
    require(
        str(stage.get("sourceUrl", "")).startswith("https://"),
        f"{stage_id}: sourceUrl must use HTTPS",
    )
    require(
        stage.get("brokerReplacement") in allowed_broker_states,
        f"{stage_id}: unsupported brokerReplacement state {stage.get('brokerReplacement')!r}",
    )
    if stage.get("officialActionUrl"):
        require(
            str(stage.get("officialActionUrl")).startswith("https://"),
            f"{stage_id}: officialActionUrl must use HTTPS",
        )
        require(bool(str(stage.get("officialActionLabel", "")).strip()),
                f"{stage_id}: officialActionUrl requires officialActionLabel")
    localized = i18n.get(stage_id, {})
    require(bool(str(localized.get("title", "")).strip()), f"{stage_id}: missing Indonesian title")
    require(bool(str(localized.get("action", "")).strip()), f"{stage_id}: missing Indonesian action")
    if stage.get("warning"):
        require(bool(str(localized.get("warning", "")).strip()), f"{stage_id}: route warning is not localized")
require(set(i18n.keys()) == set(EXPECTED_STAGES), "Indonesian route localization must match exactly the 27 supported stages")

questions = bqc.get("questions", [])
unresolved_high = [
    q.get("id") for q in questions
    if q.get("severity") == "high"
    and q.get("blocksZeroBrokerReady")
    and q.get("status") not in {"answered", "answered_hold"}
]
require(not unresolved_high, f"unresolved HIGH zero-broker blockers: {unresolved_high}")

holds = {
    q.get("id") for q in questions
    if q.get("stageId") == "job_application" and q.get("status") == "answered_hold"
}
require(holds == EXPECTED_JOB_HOLDS, f"Manufacturing job-application HOLD set changed: {sorted(holds)}")
job_stage = next((row for row in route.get("stages", []) if row.get("id") == "job_application"), {})
require(
    job_stage.get("brokerReplacement") == "held_official_notice",
    "job_application must remain explicitly held until the Manufacturing 2026 notice is verified",
)
for q in questions:
    if q.get("id") in EXPECTED_JOB_HOLDS:
        require(
            q.get("answerId") == "job_application_manufacturing_2026_wait_notice",
            f"{q.get('id')} must stay on the verified-wait answer until an official Manufacturing 2026 notice exists",
        )

require(source.get("autoPublishRules") is False, "official-source rules must never auto-publish")
require(int(source.get("configured", 0)) > 0, "official-source monitor must configure at least one source")
if args.allow_source_review_pending:
    require(
        source.get("state") in {"clean", "review_required", "fetch_warning"},
        f"unsupported official-source monitor state: {source.get('state')!r}",
    )
else:
    require(source.get("state") == "clean", f"official-source monitor state is {source.get('state')!r}, expected 'clean'")
    require(source.get("configured") == source.get("checked"),
            "official-source monitor must have checked every configured source")
    require(not source.get("reviewRequiredUrls"), "official-source reviewRequiredUrls is not empty")
    require(not source.get("fetchFailureUrls"), "official-source fetchFailureUrls is not empty")

document_packs = load_json("docs/data/document_packs_2026.json")
mcu1_candidates = [
    pack for pack in document_packs.get("packs", [])
    if "mcu1" in pack.get("appliesTo", []) and not pack.get("scopeKey")
]
require(bool(mcu1_candidates), "MCU I must have at least one document pack")
mcu1_candidates.sort(key=lambda pack: len(pack.get("appliesTo", [])) or 999)
require(
    mcu1_candidates[0].get("id") == "mcu1_2026" and mcu1_candidates[0].get("status") == "verified_2026",
    "MCU I most-specific document pack must remain the verified mcu1_2026 pack",
)
post_slc_pack = next((pack for pack in document_packs.get("packs", []) if pack.get("id") == "post_slc_mcu2_2026"), {})
require(
    post_slc_pack.get("status") == "verified_across_multiple_2026_notices"
    and post_slc_pack.get("appliesTo") == ["post_slc_requirements"]
    and len(post_slc_pack.get("items", [])) >= 9,
    "post_slc_requirements must expose a verified psychology/MCU II preparation pack",
)

psych_pack = next((pack for pack in document_packs.get("packs", []) if pack.get("id") == "psychology_pre_job_2026"), {})
require(
    psych_pack.get("status") == "verified_2026"
    and psych_pack.get("appliesTo") == ["psychology_pre_job"]
    and len(psych_pack.get("items", [])) >= 4,
    "psychology_pre_job must use its verified 2026 stage-specific pack",
)
job_pack = next((pack for pack in document_packs.get("packs", []) if pack.get("id") == "job_application_manufacturing"), {})
require(
    job_pack.get("appliesTo") == ["job_application"]
    and job_pack.get("status") == "awaiting_sector_notice",
    "Manufacturing job-application HOLD pack must apply only to job_application",
)

residence_pack = next((pack for pack in document_packs.get("packs", []) if pack.get("id") == "korea_residence"), {})
require(
    residence_pack.get("status") == "verified_current_immigration"
    and residence_pack.get("appliesTo") == ["residence_registration"]
    and len(residence_pack.get("items", [])) >= 5,
    "Residence Card document pack must stay scoped only to residence_registration",
)
require(
    "korea_entry_training:[]" in runtime.replace(" ", ""),
    "korea_entry_training must not expose the generic document tool unless a stage-specific pack exists",
)

opp_common = next((pack for pack in document_packs.get("packs", []) if pack.get("id") == "opp_common_2026_pack"), {})
require(
    opp_common.get("status") == "verified_across_multiple_2026_calls",
    "predeparture_training must have a cross-verified 2026 OPP preparation pack",
)
require(
    opp_common.get("appliesTo") == ["predeparture_training"] and len(opp_common.get("items", [])) >= 7,
    "OPP common pack must be stage-specific and contain the verified preparation checklist",
)

form_rows = forms.get("forms", [])
field_count = sum(len(form.get("fields", [])) for form in form_rows)
require(len(form_rows) == 8, f"expected 8 form wizards, found {len(form_rows)}")
require(field_count == 113, f"expected 113 form fields, found {field_count}")

checks = workplace.get("checks", [])
public_checks = [row for row in checks if row.get("coverageGroup") == "public"]
worker_checks = [row for row in checks if row.get("coverageGroup") == "worker"]
require(len(checks) == 8, f"expected 8 workplace checks, found {len(checks)}")
require(len(public_checks) == 5, f"expected 5 public/contract workplace checks, found {len(public_checks)}")
require(len(worker_checks) == 3, f"expected 3 worker-evidence workplace checks, found {len(worker_checks)}")
require(len(workplace.get("workerEvidencePolicy", {}).get("points", [])) >= 4,
        "worker evidence privacy/verification policy is incomplete")

worker_registry = load_json("docs/data/workplace_worker_evidence_v1.json")
require(worker_registry.get("status") == "beta_collection",
        "worker evidence registry must remain in beta_collection mode")
publisher = (ROOT / "scripts/publish_worker_evidence.py").read_text(encoding="utf-8")
require("PUBLISHABLE_STATUS = {\"single_verified_worker\"}" in publisher,
        "worker evidence publisher must not let one interview claim multi-worker verification")
require("metadataRemoved" in publisher and "reviewConfirmed" in publisher,
        "worker evidence publisher must require privacy review and metadata removal")
require("experienceYear" in publisher and "workplace_evidence_status" in publisher,
        "worker evidence publishing must preserve experience cycle and separate publish status")
require("experience_year" in beta_tracker and "workplace_evidence_status" in beta_tracker,
        "beta tracker must keep worker experience year and workplace evidence status separate")
require("testerId" in publisher and "tester_id" in publisher,
        "worker evidence publisher must validate a worker-panel KEP slot before publishing")
require("interview_status" in publisher and "!= \"completed\"" in publisher,
        "worker evidence publisher must require interview completion before publication")
require('worker["interview_status"] = "completed"' not in publisher,
        "worker evidence publisher must not complete interviews as a side effect")
require("WORKER_INTERVIEW_RECORD_SELF_TEST_PASS" in worker_recorder,
        "privacy-safe worker interview recorder must exist and expose a self-test")
require('"interview_status"] = "completed"' in worker_recorder,
        "worker interview recorder must own interview completion state")
require('"workplace_evidence_status"] = workplace_evidence_status' in worker_recorder,
        "worker interview recorder must explicitly record workplace publication consent state")
official_lookups = workplace.get("officialLookups", [])
require(len(official_lookups) >= 2, "workplace reality check must expose official verification routes")
lookup_urls = {row.get("url", "") for row in official_lookups}
require("https://www.factoryon.go.kr/" in lookup_urls, "FactoryOn official lookup is missing")
require("https://eps.go.kr/eo/kr/frnr/index.eo" in lookup_urls, "EPS worker-record lookup is missing")
require("Belum diverifikasi" in runtime, "workplace UI must visibly label unverified evidence")
require("function buildScoutRequestBody" in runtime, "workplace scout request must use privacy-safe body builder")
require("'Info asrama: '+(data.dorm" not in runtime, "workplace scout request must not transmit dorm address")

require("first **30** eligible people" in beta_target, "beta target must preserve first-30 public cohort")
require("activation timing must never reorder" in beta_target.lower(),
        "beta queue order must remain independent of activation timing")
require("free for 6 months from beta account activation" in beta_target,
        "beta benefit must be 6 months from activation")
require("gratis selama 6 bulan sejak akun beta diaktifkan" in outreach,
        "Indonesian outreach must state 6 months free from activation")
require("Recruitment status: **HOLD" in outreach,
        "public recruitment must remain HOLD before the launch gate passes")
require(beta_program.get("status") == "hold", "beta enrollment program must remain hold before launch")
require(beta_program.get("publicBeta", {}).get("slots") == 30, "public beta enrollment must preserve 30 slots")
worker_panel = beta_program.get("retrospectivePanel", {})
require(worker_panel.get("slots") == 20, "E-9 retrospective validation panel must preserve 20 slots")
require(worker_panel.get("separateFromPublicBeta") is True,
        "E-9 worker panel must remain separate from the 30-person public beta")
require(worker_panel.get("status") in {"hold", "open"}, "E-9 worker panel must use explicit hold/open status")
require(beta_program.get("publicBeta", {}).get("freeMonths") == 6, "public beta benefit must remain 6 months")
require(beta_program.get("publicBeta", {}).get("benefitStarts") == "beta_activation_date",
        "six-month benefit must start from beta activation")
require("Beta terbatas untuk 30 peserta pertama" in beta_page, "beta enrollment page must state the 30-person limit")
require("program.status==='open'" in beta_js, "beta application UI must be gated by OPEN status")

require("number>=1&&number<=50" in runtime, "beta ID range must remain KEP-0001..KEP-0050")
for key in ["KEYS.gaps","KEYS.fieldQuestions","KEYS.rejections","KEYS.betaChecks","KEYS.betaWorkerExperienceYear"]:
    require(key in runtime.split("const BETA_SCOPED_KEYS", 1)[1].split(";", 1)[0],
            f"{key} must stay beta-tester scoped")
require("sanitizedBetaFeedbackText" in runtime, "sanitized beta feedback sharing must remain enabled")
require("betaWorkerExperienceWrap" in app_page,
        "worker validator UI must capture experience-year context")
require("Tahun pengalaman/proses EPS:" in runtime,
        "worker validator feedback must preserve experience-year context")

require(departure_calls.get("coverageStatus") == "partial_verified",
        "departure call registry must remain explicitly partial until the full 2026 cycle is verified")
require(departure_calls.get("complete") is False,
        "departure call registry must not claim complete 2026 coverage yet")
call_rows = departure_calls.get("calls", [])
require(len(call_rows) >= 15, f"expected at least 15 verified departure calls, found {len(call_rows)}")
call_keys = [row.get("key") for row in call_rows]
require(len(call_keys) == len(set(call_keys)), "departure call registry keys must be unique")
for row in call_rows:
    require(str(row.get("key", "")).startswith("departure_2026_"), "departure call key must be 2026-scoped")
    require(str(row.get("sourceUrl", "")).startswith("https://kp2mi.go.id/"),
            f"{row.get('key')}: departure source must be official KP2MI HTTPS")
    require("departure" in row.get("stages", []), f"{row.get('key')}: departure stage mapping missing")
mcu_verified = [row for row in call_rows if row.get("mcuRuleVerified")]
require(len(mcu_verified) >= 5, "expected at least five departure calls with verified final-MCU rules")

if failures:
    print("BETA_PRELAUNCH_STATIC_FAIL")
    for failure in failures:
        print(f"- {failure}")
    raise SystemExit(1)

print(
    "BETA_PRELAUNCH_STATIC_PASS "
    f"stages={len(stage_ids)} "
    f"bqc={len(questions)} "
    f"job_holds={len(holds)} "
    f"sources={source.get('checked')}/{source.get('configured')} "
    f"forms={len(form_rows)} "
    f"fields={field_count} "
    f"workplace_public={len(public_checks)} "
    f"workplace_worker={len(worker_checks)} "
    "public_beta=30 free_months=6"
)
if args.allow_source_review_pending and source.get("state") != "clean":
    print(f"PRODUCT_CI_SOURCE_HOLD state={source.get('state')} launch gate remains blocked")
print("BETA_OPEN_MANUAL_GATES_REMAIN: final Manufacturing notice re-check at OPEN decision, explicit release decision")
print("ROUTE_PASS_EVIDENCE_REMAINS: 30 active applicants, 20 E-9 worker validators, late-stage coverage, every Broker Gap resolved or official/licensed-only")
