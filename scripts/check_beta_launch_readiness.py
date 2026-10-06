#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from datetime import datetime
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
EXPECTED_JOB_HOLDS = {"job_docs"}
EXPECTED_JOB_SAFE_BASELINES = {"job_scan","job_name","job_edit","job_submit"}
EXPECTED_SAFE_ANSWER_IDS = {
    "job_scan": "job_application_scan_safe_platform_baseline_2026",
    "job_name": "job_application_identity_safe_platform_baseline_2026",
    "job_edit": "job_application_edit_safe_platform_baseline_2026",
    "job_submit": "job_application_submit_safe_platform_baseline_2026",
}
EXPECTED_SAFE_VERIFICATION_STATUS = {
    "job_scan": "verified_cross_notice_platform_baseline_not_manufacturing_exact",
    "job_name": "verified_current_cycle_identity_safety_baseline_not_manufacturing_field_map",
    "job_edit": "verified_cross_notice_platform_baseline_not_manufacturing_exact",
    "job_submit": "verified_cross_notice_platform_baseline_not_manufacturing_exact",
}

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
recruitment_sources = load_json("docs/data/beta_recruitment_sources_v1.json")
departure_calls = load_json("docs/data/departure_calls_2026.json")
manufacturing_launch_check = load_json("recruitment/MANUFACTURING_LAUNCH_CHECK.json")
runtime = (ROOT / "docs/app-runtime.js").read_text(encoding="utf-8")
landing_page = (ROOT / "docs/index.html").read_text(encoding="utf-8")
landing_js = (ROOT / "docs/landing.js").read_text(encoding="utf-8")
app_page = (ROOT / "docs/app.html").read_text(encoding="utf-8")
beta_page = (ROOT / "docs/beta.html").read_text(encoding="utf-8")
beta_js = (ROOT / "docs/beta.js").read_text(encoding="utf-8")
sw_js = (ROOT / "docs/sw.js").read_text(encoding="utf-8")
beta_target = (ROOT / "recruitment/BETA_TARGET.md").read_text(encoding="utf-8")
mvp_validation = (ROOT / "docs/MVP_VALIDATION.md").read_text(encoding="utf-8")
outreach = (ROOT / "recruitment/OUTREACH_ID.md").read_text(encoding="utf-8")
beta_tracker = (ROOT / "recruitment/BETA_TESTER_TRACKER.csv").read_text(encoding="utf-8-sig")
worker_recorder = (ROOT / "scripts/record_worker_interview.py").read_text(encoding="utf-8")
worker_interest_parser = (ROOT / "scripts/parse_worker_interest.py").read_text(encoding="utf-8")
beta_interest_parser = (ROOT / "scripts/parse_beta_interest.py").read_text(encoding="utf-8")
beta_feedback_recorder = (ROOT / "scripts/record_beta_feedback.py").read_text(encoding="utf-8")
beta_progress_reporter = (ROOT / "scripts/report_beta_progress.py").read_text(encoding="utf-8")
zero_broker_recorder = (ROOT / "scripts/record_zero_broker_evidence.py").read_text(encoding="utf-8")
manufacturing_check_recorder = (ROOT / "scripts/record_manufacturing_launch_check.py").read_text(encoding="utf-8")
outreach_send_guard = (ROOT / "scripts/check_outreach_send_guard.py").read_text(encoding="utf-8")

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
require(
    set(manufacturing_launch_check.get("heldQuestions", [])) == EXPECTED_JOB_HOLDS,
    "Manufacturing launch-check record must preserve exactly the one exact HOLD question",
)
require(
    {row.get("questionId") for row in manufacturing_launch_check.get("safePlatformBaselines", [])}
    == EXPECTED_JOB_SAFE_BASELINES,
    "Manufacturing launch-check record must preserve exactly the four safe platform baselines",
)
require(
    manufacturing_launch_check.get("result") == "no_current_manufacturing_job_application_notice",
    "Manufacturing launch-check record indicates a notice was found or still needs review",
)
require(
    manufacturing_launch_check.get("primaryIndex") == "https://kp2mi.go.id/gtog-korea/info",
    "Manufacturing launch check must use the official KP2MI G-to-G Korea index",
)
baseline = route.get("jobApplicationBaselineEvidence", {})
require(
    baseline.get("status") == "verified_current_cycle_plus_four_safe_platform_baselines_one_exact_detail_held",
    "Indonesia job-application baseline must distinguish current-cycle process evidence, safe platform baselines and exact HOLDs",
)
require(
    baseline.get("verifiedAt") == "2026-10-06",
    "Indonesia job-application current-cycle baseline must preserve the 2026-10-06 verification date",
)
require(
    set(baseline.get("heldExactQuestions", [])) == EXPECTED_JOB_HOLDS,
    "Indonesia job-application baseline must preserve exactly the one held exact question",
)
require(
    {row.get("questionId") for row in baseline.get("safePlatformBaselines", [])}
    == EXPECTED_JOB_SAFE_BASELINES,
    "Indonesia job-application baseline must preserve job_scan/job_name/job_edit/job_submit as the four safe platform baselines",
)
require(
    all(
        row.get("verificationStatus") == EXPECTED_SAFE_VERIFICATION_STATUS.get(row.get("questionId"))
        for row in baseline.get("safePlatformBaselines", [])
    ),
    "Indonesia safe job-application baselines must remain explicitly non-exact for Manufacturing 2026",
)
require(
    len(baseline.get("facts", [])) >= 4
    and any("Sisko P2MI" in str(x) for x in baseline.get("facts", []))
    and any("HIMPSI" in str(x) for x in baseline.get("facts", [])),
    "Indonesia job-application baseline must preserve MCU/HIMPSI/Sisko process evidence",
)
require(
    manufacturing_launch_check.get("checkedAt") == "2026-10-06",
    "Manufacturing launch evidence must be refreshed on 2026-10-06",
)
same_day = manufacturing_launch_check.get("sameDayOfficialRecheck", {})
require(
    same_day.get("status") == "completed_no_detailed_manufacturing_notice_found"
    and same_day.get("repeatOnActualReleaseDay") is True,
    "Manufacturing launch check must record the completed 2026-10-06 recheck and require another check on release day",
)
verified_baseline = manufacturing_launch_check.get("verifiedBaseline", {})
require(
    verified_baseline.get("status") == "process_and_four_safe_platform_baselines_verified_one_exact_submission_rule_held"
    and set(verified_baseline.get("stillHeld", [])) == EXPECTED_JOB_HOLDS
    and set(verified_baseline.get("safePlatformBaselines", [])) == EXPECTED_JOB_SAFE_BASELINES,
    "Manufacturing launch check must distinguish verified process/safe baselines from the one exact held rule",
)

job_stage = next((row for row in route.get("stages", []) if row.get("id") == "job_application"), {})
require(
    job_stage.get("brokerReplacement") == "held_official_notice",
    "job_application must remain explicitly held until the Manufacturing 2026 notice is verified",
)
for q in questions:
    if q.get("id") in EXPECTED_JOB_HOLDS:
        require(
            q.get("answerId") == "job_application_manufacturing_2026_wait_notice"
            and q.get("status") == "answered_hold"
            and q.get("blocksZeroBrokerReady") is True,
            f"{q.get('id')} must stay an exact blocking HOLD until an official Manufacturing 2026 notice exists",
        )
    if q.get("id") in EXPECTED_JOB_SAFE_BASELINES:
        require(
            q.get("answerId") == EXPECTED_SAFE_ANSWER_IDS[q.get("id")]
            and q.get("status") == "answered"
            and q.get("blocksZeroBrokerReady") is False,
            f"{q.get('id')} must remain a resolved non-blocking safe platform baseline",
        )

answer_by_id = {row.get("id"): row for row in load_json("docs/data/exact_answer_rules_v1.json").get("answers", [])}
for qid, answer_id in EXPECTED_SAFE_ANSWER_IDS.items():
    safe_answer = answer_by_id.get(answer_id, {})
    require(
        safe_answer.get("verificationStatus") == EXPECTED_SAFE_VERIFICATION_STATUS[qid]
        and safe_answer.get("blocksSubmission") is False,
        f"{qid} safe baseline must remain explicitly non-exact and non-authorizing for Manufacturing submission",
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
document_items = [
    item
    for pack in document_packs.get("packs", [])
    for item in pack.get("items", [])
]
require(bool(document_items), "document guidance must contain checklist items")
require(
    all(isinstance(item.get("required"), bool) for item in document_items),
    "every document item must explicitly distinguish required vs conditional",
)
require(
    "Wajib / perlu disiapkan" in runtime and "Jika tersedia / bersyarat" in runtime,
    "document UI must visibly distinguish required and conditional items",
)
require(
    "JANGAN SUBMIT DULU." in runtime
    and "Checklist dokumen tahap ini belum cukup spesifik" in runtime,
    "pre-submit UI must block unresolved/unconfirmed requirements",
)

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
require("contributorConsent" in publisher,
        "worker evidence publisher must require explicit contributor consent for public summaries")
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
require("WORKER_INTEREST_PARSE_SELF_TEST_PASS" in worker_interest_parser,
        "privacy-safe worker-interest parser must exist and expose a self-test")
require("RAW_BODY_NOT_STORED=true" in worker_interest_parser
        and "WORKER_SLOT_NOT_ASSIGNED=true" in worker_interest_parser,
        "worker-interest parser must keep raw mail private and must not assign a validator slot before approval")
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

require("target at least **30** active Indonesian applicants" in beta_target,
        "beta target must preserve an initial validation target of at least 30 active applicants")
require("30 is a validation target, not an automatic rejection cap" in beta_target,
        "beta target must not use 30 as an automatic rejection cap")
require("KEP-0051 and upward" in beta_target,
        "beta target must reserve overflow active-applicant IDs above KEP-0050")
require("free for 6 months from beta account activation" in beta_target,
        "beta benefit must be 6 months from activation")
require("gratis selama 6 bulan sejak akun beta diaktifkan" in outreach,
        "Indonesian outreach must state 6 months free from activation")
program_status = beta_program.get("status")
release_decision = beta_program.get("releaseDecision", {})
hold_policy = release_decision.get("publicBetaHoldPolicy", {})
require(
    hold_policy.get("safeOfficialEvidenceHoldsMayRemain") is True,
    "public beta policy must allow safely-held official-evidence gaps without auto-blocking beta activation",
)
require(
    set(hold_policy.get("currentHeldQuestions", [])) == EXPECTED_JOB_HOLDS,
    "public beta HOLD policy must name exactly the one exact Manufacturing job-application question",
)
require(
    {row.get("questionId") for row in hold_policy.get("safePlatformBaselines", [])}
    == EXPECTED_JOB_SAFE_BASELINES,
    "public beta policy must preserve job_scan/job_name/job_edit/job_submit as four safe platform baselines",
)
require(
    "final Broker Replacement Rate 100% PASS" in str(hold_policy.get("rule", "")),
    "public beta HOLD policy must distinguish beta activation from final Broker Replacement Rate 100% PASS",
)
actual_open_gates = release_decision.get("actualOpenGates", [])
require(
    len(actual_open_gates) == 3
    and any("same-HEAD" in str(x) for x in actual_open_gates)
    and any("same-day" in str(x) for x in actual_open_gates)
    and any("manual beta OPEN" in str(x) for x in actual_open_gates),
    "public beta must preserve exactly the three release gates: same-HEAD checks, same-day source recheck, manual OPEN",
)
require(program_status in {"hold", "open"}, f"unsupported public beta status: {program_status!r}")
if program_status == "hold":
    require(release_decision.get("publicBeta") == "pending_manual_approval",
            "HOLD state must remain pending manual OPEN approval")
    require(release_decision.get("approvedAt") in {None, ""},
            "HOLD state must not carry an OPEN approval timestamp")
    require("Application intake status: **OPEN**" in outreach,
            "tester-interest intake must remain OPEN while beta access is HOLD")
    require("Beta access status: **HOLD" in outreach,
            "HOLD program must keep beta access status HOLD")
else:
    require(release_decision.get("publicBeta") == "approved_manual",
            "OPEN state requires explicit releaseDecision.publicBeta=approved_manual")
    approved_at = str(release_decision.get("approvedAt") or "").strip()
    require(bool(approved_at), "OPEN state requires releaseDecision.approvedAt")
    approved_dt = None
    if approved_at:
        try:
            approved_dt = datetime.fromisoformat(approved_at.replace("Z", "+00:00"))
        except ValueError:
            failures.append("OPEN approval timestamp must be valid ISO-8601")
        else:
            require(approved_dt.tzinfo is not None,
                    "OPEN approval timestamp must include timezone")
    require(
        approved_dt is not None
        and manufacturing_launch_check.get("checkedAt") == approved_dt.date().isoformat(),
        "OPEN state requires a same-day Manufacturing launch-check record",
    )
    require("Application intake status: **OPEN**" in outreach,
            "application intake must remain OPEN after beta access opens")
    require("Beta access status: **OPEN" in outreach,
            "OPEN program must keep beta access status OPEN")
require(beta_program.get("publicBeta", {}).get("targetParticipants") == 30,
        "public beta must preserve 30 as the initial validation target")
require(beta_program.get("publicBeta", {}).get("capacityPolicy") == "soft_target_no_automatic_rejection",
        "public beta must keep 30 as a soft target, not a hard cap")
require(beta_program.get("application", {}).get("intakeStatus") == "open",
        "tester-interest application intake must be OPEN")
require('id="releaseGateNote"' in beta_page,
        "beta page must explain the actual release gates")
require("satu detail exact lamaran online Manufaktur yang masih HOLD" in beta_page
        and "Empat pertanyaan lain" in beta_page
        and "tidak otomatis melarang dimulainya beta" in beta_page,
        "beta page must distinguish one exact HOLD, four safe baselines and beta release blockers")
worker_panel = beta_program.get("retrospectivePanel", {})
require(worker_panel.get("slots") == 20, "E-9 retrospective validation panel must preserve 20 slots")
require(worker_panel.get("separateFromPublicBeta") is True,
        "E-9 worker panel must remain separate from the active-applicant validation cohort")
require(worker_panel.get("status") in {"hold", "open"}, "E-9 worker panel must use explicit hold/open status")
require(worker_panel.get("intakeStatus") == "open",
        "E-9 worker-panel interest intake must remain OPEN independently of panel access")
require(worker_panel.get("interestIntakeIndependentFromPanelAccess") is True,
        "E-9 worker interest intake must remain independent from panel access state")
require(worker_panel.get("application", {}).get("opensOnlyWhenStatus") is None,
        "E-9 worker interest intake must not be gated by panel OPEN state")
require("function workerInterestOpen()" in beta_js
        and "program.retrospectivePanel?.intakeStatus==='open'" in beta_js
        and "$('workerValidatorForm').hidden=!workerIntakeOpen" in beta_js,
        "worker interest form must be gated by interest intake, not worker-panel access")
require("Recruitment source code: '+recruitmentSourceCode()" in beta_js,
        "worker-panel interest email must preserve controlled recruitment source attribution")
require("mengirim minat tidak mengaktifkan akses panel" in beta_page,
        "worker-panel page must disclose that interest registration does not activate access")
worker_release_state = release_decision.get("retrospectivePanel")
worker_release_at = str(release_decision.get("retrospectiveApprovedAt") or "").strip()
if worker_panel.get("status") == "hold":
    require(worker_release_state == "pending_manual_approval",
            "worker-panel HOLD state must remain pending manual approval")
    require(not worker_release_at,
            "worker-panel HOLD state must not carry an approval timestamp")
else:
    require(worker_release_state == "approved_manual",
            "worker-panel OPEN requires explicit approved release decision")
    require(bool(worker_release_at),
            "worker-panel OPEN requires retrospectiveApprovedAt")
    if worker_release_at:
        try:
            worker_approved_dt = datetime.fromisoformat(worker_release_at.replace("Z", "+00:00"))
        except ValueError:
            failures.append("worker-panel approval timestamp must be valid ISO-8601")
        else:
            require(worker_approved_dt.tzinfo is not None,
                    "worker-panel approval timestamp must include timezone")
require(beta_program.get("publicBeta", {}).get("freeMonths") == 6, "public beta benefit must remain 6 months")
require(beta_program.get("publicBeta", {}).get("benefitStarts") == "beta_activation_date",
        "six-month benefit must start from beta activation")
require(len(beta_program.get("publicBeta", {}).get("feedback", [])) >= 3,
        "public beta must keep explicit feedback participation requirements")
no_guarantee = set(beta_program.get("publicBeta", {}).get("noGuarantee", []))
require(
    {"No job guarantee", "No SLC guarantee", "No visa guarantee", "No departure guarantee"}.issubset(no_guarantee),
    "public beta must clearly preserve job/SLC/visa/departure no-guarantee copy",
)
require(
    all(token in beta_page for token in ["nomor paspor", "nomor KTP", "nomor ARC", "nomor telepon"]),
    "beta enrollment page must state that sensitive identity/contact fields are not required",
)
require(
    "alamat email pengirim akan terlihat oleh tim" in beta_page
    and "tidak dimasukkan ke repositori publik" in beta_page,
    "beta enrollment page must disclose sender-email handling without public-repo storage",
)
privacy_page = (ROOT / "docs/privacy.html").read_text(encoding="utf-8")
require(
    "alamat email pengirim akan terlihat oleh tim" in privacy_page
    and "tidak disimpan di repositori publik" in privacy_page,
    "privacy notice must disclose sender-email handling and public-repo exclusion",
)
require('href="beta.html"' in landing_page,
        "public landing must route tester enrollment to beta.html")
require('src="landing.js"' in landing_page,
        "public landing must load the recruitment-source attribution helper")
require(
    "new URLSearchParams(location.search).get('src')" in landing_js
    and "a[href=\"beta.html\"]" in landing_js
    and "beta.html?src=" in landing_js,
    "landing source attribution must propagate src into every beta enrollment link",
)
require(
    "/^[a-z0-9_]{1,64}$/" in landing_js,
    "landing source attribution must accept only a bounded non-identifying source token",
)
require(
    "workerSourceCodes=new Set(['ut_korea_pmi','wongrow_pmi_korea','kbri_seoul_pmi','sbmi_korea_worker_referral','pcim_korea_referral','kp2mi_departure_worker_referral','korea_indonesia_center_referral','appik_purna_korea_referral','pui_kmi_worker_referral','hwaseong_foreign_welfare','yangsan_foreign_worker_center','seosan_foreign_worker_center'])" in landing_js
    and "beta.html?src=" in landing_js
    and "#worker-panel" in landing_js,
    "worker-only recruitment sources must route directly to the worker-interest section",
)
require(
    "genericLandingSourceCodes=new Set(['website','email','community','community_admin','social','referral','direct_outreach','partner','other'])" in landing_js
    and "location.replace('beta.html?src='+encodeURIComponent(raw)+'#apply')" in landing_js,
    "non-generic attributed campaigns must route directly to the beta intake anchor",
)
require('id="apply"' in beta_page,
        "beta page must expose a stable applicant-intake anchor")
require("Sekitar 30 detik" in beta_page
        and "Tidak perlu nama atau nomor telepon" in beta_page,
        "beta application panel must make the low-friction intake steps explicit")
require('id="worker-panel"' in beta_page,
        "beta page must expose a stable worker-interest anchor")
require('id="betaForm"' not in landing_page and 'id="name"' not in landing_page and 'id="contact"' not in landing_page,
        "public landing must not collect identity/contact data in a legacy beta form")
require("Pendaftaran minat beta sudah dibuka" in beta_page, "beta enrollment page must state that tester-interest intake is open")
require("30 bukan batas otomatis" in beta_page, "beta enrollment page must state that 30 is not an automatic rejection cap")
require("6 bulan gratis" in beta_page, "beta enrollment page must preserve the six-month benefit copy")
require("program.application?.intakeStatus==='open'" in beta_js,
        "tester-interest application UI must be gated by intakeStatus, independently of beta access")
require(
    'id="gmailApplicationBtn"' in beta_page
    and 'id="gmailWorkerValidatorBtn"' in beta_page
    and "function gmailComposeUrl(" in beta_js
    and "https://mail.google.com/mail/?" in beta_js,
    "beta intake must preserve a direct Gmail compose fallback in addition to default mailto/copy flows",
)
require(
    "URLSearchParams" in beta_js
    and "applicationText()" in beta_js
    and "workerValidatorText()" in beta_js,
    "Gmail fallback must reuse the same privacy-minimized application bodies instead of collecting new identity fields",
)
require("Recruitment source code:" in beta_js and "RECRUITMENT_SOURCES_URL" in beta_js,
        "tester-interest email must carry a controlled non-identifying recruitment source code from shared data")
require(
    'id="communitySharePanel"' in beta_page
    and 'id="shareCommunityApplicantInviteBtn"' in beta_page
    and 'id="copyCommunityApplicantInviteBtn"' in beta_page
    and 'id="shareCommunityWorkerInviteBtn"' in beta_page
    and 'id="copyCommunityWorkerInviteBtn"' in beta_page,
    "beta page must expose native-share and copy actions for the source-attributed community kit",
)
require(
    "async function shareText(text)" in beta_js
    and "navigator.share" in beta_js
    and "await navigator.share({text})" in beta_js
    and "const ok=await copyText(text)" in beta_js,
    "community sharing must prefer the native share sheet and fail back to copy without new data collection",
)
require(
    "function sourceAttributedBetaUrl(worker=false)" in beta_js
    and "url.searchParams.set('src',recruitmentSourceCode())" in beta_js
    and "url.hash=worker?'worker-panel':''" in beta_js,
    "community share URLs must preserve only the controlled recruitment source and worker anchor",
)
require(
    "function communityApplicantInviteText()" in beta_js
    and "function communityWorkerInviteText()" in beta_js
    and "KEP adalah proyek independen" in beta_js,
    "community share copy must preserve independent-service disclosure",
)
require(
    "$('communitySharePanel').hidden=shareSource==='website'" in beta_js
    and "$('communityShareSource').textContent=shareSource" in beta_js,
    "community share kit must stay hidden for unattributed website traffic and visibly preserve its source code",
)
require(
    "Mengirim minat belum mengaktifkan akses panel" in beta_js
    and "Tidak ada jaminan kelulusan, pekerjaan, employer selection, SLC, visa, atau keberangkatan." in beta_js,
    "community share copy must preserve worker-access and no-guarantee boundaries",
)
require("OUTREACH_SEND_GUARD_SELF_TEST_PASS" in outreach_send_guard,
        "fail-closed outreach send guard must exist and expose a self-test")
require("already_sent_or_closed" in outreach_send_guard
        and "followup_not_explicitly_ready" in outreach_send_guard,
        "outreach guard must block duplicate initial sends and unapproved follow-ups")
require("BETA_INTEREST_PARSE_SELF_TEST_PASS" in beta_interest_parser,
        "privacy-safe tester-interest parser must exist and expose a self-test")
require("RAW_BODY_NOT_STORED=true" in beta_interest_parser,
        "tester-interest parser must explicitly avoid raw-body storage")
require("return betaRecruitmentSourceCodes.has(raw)?raw:betaRecruitmentDefaultCode" in beta_js,
        "unknown recruitment source values must fall back to the shared default code")
require(recruitment_sources.get("defaultCode") == "website",
        "shared recruitment-source default must remain website")
require(
    "./data/beta_recruitment_sources_v1.json" in sw_js,
    "service worker must cache the shared beta recruitment-source catalog",
)
require(
    set(recruitment_sources.get("codes", [])) >= {
        "website","epstopik_indonesia","topikly","apsan_hakwon","owie_epstopik",
        "lpk_samwon","jendela_asa","lpk_ggum","lpk_hana_korea","lpk_hanaman",
        "mendunia_korea","korean_first","lpk_maheswara","lpk_caranta",
        "ubt_eps_topik_app","topiknow_app","kamus_korea_app","jeongsang_eps_app",
        "kosakata_eps_topik_app","ubt_eps_topik_id_app","ubt_eps_topik_eddie_app",
        "kbri_seoul_pmi","indonesia_eps_center_hrdk","sbmi_korea_worker_referral","pcim_korea_referral",
        "kp2mi_departure_worker_referral","kp2mi_sending_applicant","lpk_master_korea",
        "lpk_hanaro","lpk_go_korea","korea_indonesia_center_referral","appik_purna_korea_referral",
        "pui_kmi_worker_referral","bp3mi_dki_applicant","bp3mi_jateng_applicant","bp3mi_jatim_applicant",
        "bp3mi_jabar_applicant","bp3mi_banten_applicant","bp3mi_sumut_applicant",
        "jettyland_eps_app","zenski_eps_app","lpk_seoul_lombok","hwaseong_foreign_welfare","yangsan_foreign_worker_center","seosan_foreign_worker_center"
    },
    "shared recruitment-source catalog is missing a required controlled code",
)
require("release.publicBeta==='approved_manual'" in beta_js and "release.approvedAt" in beta_js,
        "beta access state must require explicit approved release state, not status alone")
require("release.retrospectivePanel==='approved_manual'" in beta_js and "release.retrospectiveApprovedAt" in beta_js,
        "worker-panel UI must require explicit approved release state, not status alone")

require("number>=1&&number<=9999" in runtime,
        "beta ID parser must support contiguous overflow active-applicant IDs")
require("if(number>=31&&number<=50)return 'e9_worker_validator'" in runtime,
        "KEP-0031..KEP-0050 must stay reserved for worker validators")
require("number>=51" in runtime and "return 'active_applicant'" in runtime,
        "KEP-0051+ must map to overflow active applicants")
for key in [
    "KEYS.done","KEYS.docs","KEYS.gaps","KEYS.contract","KEYS.workplace","KEYS.ledger",
    "KEYS.payroll","KEYS.fieldQuestions","KEYS.rejections","KEYS.betaChecks",
    "KEYS.betaWorkerExperienceYear","KEYS.scopeSelections","KEYS.formWizard",
    "KEYS.wizardReviewed","KEYS.quickSetup"
]:
    require(key in runtime.split("const BETA_SCOPED_KEYS", 1)[1].split(";", 1)[0],
            f"{key} must stay beta-tester scoped")
require("sanitizedBetaFeedbackText" in runtime, "sanitized beta feedback sharing must remain enabled")
require("schemaVersion:2" in runtime and "betaTesterId:betaTesterIdState()||null" in runtime,
        "progress backup must carry anonymous beta-ID context")
require("Backup ini berasal dari ID beta yang berbeda." in runtime,
        "beta progress restore must reject cross-ID backups")
require("Backup lama tanpa konteks ID beta" in runtime,
        "legacy progress backups must not enter active beta namespaces")
require("betaWorkerExperienceWrap" in app_page,
        "worker validator UI must capture experience-year context")
require("Tahun pengalaman/proses EPS:" in runtime,
        "worker validator feedback must preserve experience-year context")
require("Current route stage ID:" in beta_js,
        "beta application must send an exact supported route stage ID")
require('id="applicantCycle"' in beta_page and "EPS process cycle:" in beta_js,
        "beta interest intake must capture non-identifying EPS route-cycle context")
require("--route-cycle" in beta_feedback_recorder,
        "public beta feedback recorder must support verified route-cycle correction")
require("BETA_FEEDBACK_RECORD_SELF_TEST_PASS" in beta_feedback_recorder,
        "privacy-safe public beta feedback recorder must exist and expose a self-test")
require('row["notes"] = ""' in beta_feedback_recorder,
        "public beta feedback recorder must keep narrative notes out of the public tracker")
require("route_cycle" in beta_tracker,
        "beta tracker must preserve active-applicant EPS route-cycle context")
require("zero_broker_pass_stages" in beta_tracker and "zero_broker_fail_stages" in beta_tracker,
        "beta tracker must preserve stage-level zero-broker PASS/FAIL evidence")
require("--zero-broker-pass-stage" in beta_feedback_recorder and "--zero-broker-fail-stage" in beta_feedback_recorder,
        "public beta feedback recorder must accept stage-level zero-broker evidence")
require("--zero-broker-pass-stage" in worker_recorder and "--zero-broker-fail-stage" in worker_recorder,
        "worker interview recorder must accept stage-level zero-broker evidence")
require("zero_broker_stage_ready" in beta_progress_reporter and "ROUTE_CYCLE" in beta_progress_reporter,
        "beta progress report must gate route evidence on all current-cycle zero-broker stages")
require("active_is_current_cycle" in beta_progress_reporter
        and "current_cycle_active_rows" in beta_progress_reporter
        and "current_cycle_evidence_rows = current_cycle_active_rows + current_cycle_worker_rows" in beta_progress_reporter,
        "route PASS evidence must exclude prior-cycle/unknown active-applicant evidence")
require("STRUCTURED_ROUTE_HOLDS" in beta_progress_reporter,
        "beta progress report must block final route PASS on structured official-evidence HOLDs")
require("SOURCE_REVIEW_READY" in beta_progress_reporter,
        "beta progress report must require a clean official-source state for final route PASS")
require("No structured `blocksZeroBrokerReady=true` question remains on `answered_hold`." in mvp_validation,
        "MVP validation must keep structured HOLDs out of final Broker Replacement Rate PASS")
require("They do **not** require the beta itself to stay closed" in mvp_validation,
        "MVP validation must distinguish beta OPEN from final route PASS")
require("ZERO_BROKER_EVIDENCE_RECORD_SELF_TEST_PASS" in zero_broker_recorder,
        "follow-up stage evidence recorder must exist and expose a self-test")
require('row["notes"] = ""' in zero_broker_recorder,
        "follow-up stage evidence recorder must keep public tracker narrative-free")
require("MANUFACTURING_LAUNCH_CHECK_RECORD_SELF_TEST_PASS" in manufacturing_check_recorder,
        "same-day Manufacturing launch-check recorder must exist and expose a self-test")
require("Kode KEP saja bukan bukti identitas" in app_page,
        "beta UI must state that a KEP ID alone is not authentication")
require("same private enrollment email/thread" in (ROOT / "recruitment/BETA_OPERATIONS.md").read_text(encoding="utf-8"),
        "beta operations must verify private-channel provenance before counting evidence")

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
    "public_beta_target=30 overflow_allowed=true free_months=6"
)
if args.allow_source_review_pending and source.get("state") != "clean":
    print(f"PRODUCT_CI_SOURCE_HOLD state={source.get('state')} launch gate remains blocked")
print("BETA_ACCESS_OPEN_MANUAL_GATES_REMAIN: intake is open; final Manufacturing notice re-check and explicit access release decision remain")
print("ROUTE_PASS_EVIDENCE_REMAINS: at least 30 active applicants, 20 E-9 worker validators, late-stage coverage, every Broker Gap resolved or official/licensed-only")
