#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

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
bqc = load_json("docs/data/broker_question_catalog_v1.json")
source = load_json("docs/data/source_review_status.json")
forms = load_json("docs/data/form_wizards_2026.json")
workplace = load_json("docs/data/workplace_reality_v1.json")
beta_program = load_json("docs/data/beta_program_v1.json")
runtime = (ROOT / "docs/app-runtime.js").read_text(encoding="utf-8")
beta_page = (ROOT / "docs/beta.html").read_text(encoding="utf-8")
beta_js = (ROOT / "docs/beta.js").read_text(encoding="utf-8")
beta_target = (ROOT / "recruitment/BETA_TARGET.md").read_text(encoding="utf-8")
outreach = (ROOT / "recruitment/OUTREACH_ID.md").read_text(encoding="utf-8")

stage_ids = [row.get("id") for row in route.get("stages", [])]
require(stage_ids == EXPECTED_STAGES, "supported route must contain the locked 27 stages in exact order")

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

require(source.get("state") == "clean", f"official-source monitor state is {source.get('state')!r}, expected 'clean'")
require(source.get("configured") == source.get("checked") and int(source.get("configured", 0)) > 0,
        "official-source monitor must have checked every configured source")
require(not source.get("reviewRequiredUrls"), "official-source reviewRequiredUrls is not empty")
require(not source.get("fetchFailureUrls"), "official-source fetchFailureUrls is not empty")

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
require("Belum diverifikasi" in runtime, "workplace UI must visibly label unverified evidence")

require("first **30** eligible people" in beta_target, "beta target must preserve first-30 public cohort")
require("free for 6 months from beta account activation" in beta_target,
        "beta benefit must be 6 months from activation")
require("gratis selama 6 bulan sejak akun beta diaktifkan" in outreach,
        "Indonesian outreach must state 6 months free from activation")
require("Recruitment status: **HOLD" in outreach,
        "public recruitment must remain HOLD before the launch gate passes")
require(beta_program.get("status") == "hold", "beta enrollment program must remain hold before launch")
require(beta_program.get("publicBeta", {}).get("slots") == 30, "public beta enrollment must preserve 30 slots")
require(beta_program.get("publicBeta", {}).get("freeMonths") == 6, "public beta benefit must remain 6 months")
require(beta_program.get("publicBeta", {}).get("benefitStarts") == "beta_activation_date",
        "six-month benefit must start from beta activation")
require("Beta terbatas untuk 30 peserta pertama" in beta_page, "beta enrollment page must state the 30-person limit")
require("program.status==='open'" in beta_js, "beta application UI must be gated by OPEN status")

require("number>=1&&number<=50" in runtime, "beta ID range must remain KEP-0001..KEP-0050")
for key in ["KEYS.gaps","KEYS.fieldQuestions","KEYS.rejections","KEYS.betaChecks"]:
    require(key in runtime.split("const BETA_SCOPED_KEYS", 1)[1].split(";", 1)[0],
            f"{key} must stay beta-tester scoped")
require("sanitizedBetaFeedbackText" in runtime, "sanitized beta feedback sharing must remain enabled")

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
print("MANUAL_LAUNCH_GATES_REMAIN: fresh Manufacturing notice re-check, mobile release review, open-defect review, real-user evidence")
