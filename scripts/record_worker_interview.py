#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TRACKER = ROOT / "recruitment" / "BETA_TESTER_TRACKER.csv"
ROUTE = ROOT / "docs" / "data" / "id_e9_manufacturing_2026.json"
SUPPORTED_STAGES = {
    row["id"] for row in json.loads(ROUTE.read_text(encoding="utf-8-sig")).get("stages", [])
}
ALLOWED_YEARS = {str(year) for year in range(2004, 2027)} | {"unknown"}
YES_NO_UNKNOWN = {"yes", "no", "unknown"}
BROKER_GAP_STATUSES = {"pending", "none_reported", "open", "resolved", "official_or_licensed_only"}
RETEST_STATUSES = {"pending", "passed", "failed", "not_applicable"}
WORKPLACE_EVIDENCE_DECISIONS = {"pending", "declined", "not_publishable"}


def fail(message: str) -> None:
    raise ValueError(message)


def normalize_stage_list(values: list[str] | None) -> str:
    clean: list[str] = []
    for raw in values or []:
        stage_id = str(raw or "").strip()
        if stage_id not in SUPPORTED_STAGES:
            fail(f"unsupported route stage in evidence list: {stage_id}")
        if stage_id not in clean:
            clean.append(stage_id)
    return ";".join(clean)


def validate_assigned_worker(row: dict[str, str], tester_id: str) -> None:
    if not re.fullmatch(r"KEP-00(?:3[1-9]|4\d|50)", tester_id):
        fail("tester-id must be KEP-0031 through KEP-0050")
    if row.get("target_group", "").strip() != "e9_worker_korea":
        fail(f"{tester_id}: not an E-9 worker panel slot")
    if row.get("role", "").strip() != "e9_worker_validator":
        fail(f"{tester_id}: worker validator slot is not assigned")
    if not row.get("created_at", "").strip():
        fail(f"{tester_id}: worker validator slot is not assigned")
    if row.get("in_korea", "").strip().lower() != "yes":
        fail(f"{tester_id}: in_korea must be yes")
    if row.get("e9_experience", "").strip().lower() != "confirmed":
        fail(f"{tester_id}: E-9 experience must be confirmed")


def record(
    row: dict[str, str],
    *,
    tester_id: str,
    experience_year: str,
    current_stage: str,
    broker_used: str,
    workplace_info_needed: str,
    broker_gap_status: str,
    retest_status: str,
    workplace_evidence_status: str,
    zero_broker_pass_stages: list[str] | None = None,
    zero_broker_fail_stages: list[str] | None = None,
) -> dict[str, str]:
    validate_assigned_worker(row, tester_id)
    if row.get("interview_status", "").strip().lower() == "completed":
        fail(f"{tester_id}: interview is already completed")
    if experience_year not in ALLOWED_YEARS:
        fail("experience-year must be 2004..2026 or unknown")
    if current_stage not in SUPPORTED_STAGES:
        fail(f"unsupported current-stage: {current_stage}")
    if broker_used not in YES_NO_UNKNOWN:
        fail("broker-used must be yes, no, or unknown")
    if workplace_info_needed not in YES_NO_UNKNOWN:
        fail("workplace-info-needed must be yes, no, or unknown")
    if broker_gap_status not in BROKER_GAP_STATUSES:
        fail("unsupported broker-gap-status")
    if retest_status not in RETEST_STATUSES:
        fail("unsupported retest-status")
    if workplace_evidence_status not in WORKPLACE_EVIDENCE_DECISIONS:
        fail("workplace-evidence-status must be pending, declined, or not_publishable")

    row["experience_year"] = experience_year
    row["current_stage"] = current_stage
    row["broker_used"] = broker_used
    row["workplace_info_needed"] = workplace_info_needed
    row["broker_gap_status"] = broker_gap_status
    row["retest_status"] = retest_status
    row["interview_status"] = "completed"
    row["workplace_evidence_status"] = workplace_evidence_status
    row["zero_broker_pass_stages"] = normalize_stage_list(zero_broker_pass_stages)
    row["zero_broker_fail_stages"] = normalize_stage_list(zero_broker_fail_stages)
    zero_pass = {part for part in row["zero_broker_pass_stages"].split(";") if part}
    zero_fail = {part for part in row["zero_broker_fail_stages"].split(";") if part}
    overlap = sorted(zero_pass & zero_fail)
    if overlap:
        fail("zero-broker PASS and FAIL cannot contain the same stage: " + ", ".join(overlap))
    return row


def self_test() -> None:
    base = {
        "tester_id": "KEP-0031",
        "target_group": "e9_worker_korea",
        "created_at": "2026-10-04",
        "role": "e9_worker_validator",
        "current_stage": "employment_maintenance",
        "in_korea": "yes",
        "e9_experience": "confirmed",
        "experience_year": "",
        "broker_used": "",
        "workplace_info_needed": "",
        "interview_status": "new",
        "broker_gap_status": "pending",
        "retest_status": "pending",
        "workplace_evidence_status": "pending",
        "zero_broker_pass_stages": "",
        "zero_broker_fail_stages": "",
    }
    row = record(
        dict(base),
        tester_id="KEP-0031",
        experience_year="2024",
        current_stage="first_payroll_check",
        broker_used="no",
        workplace_info_needed="yes",
        broker_gap_status="open",
        retest_status="pending",
        workplace_evidence_status="pending",
        zero_broker_pass_stages=["korea_entry_training", "employer_handover"],
        zero_broker_fail_stages=["residence_registration"],
    )
    assert row["interview_status"] == "completed"
    assert row["experience_year"] == "2024"
    assert row["workplace_evidence_status"] == "pending"
    assert row["zero_broker_pass_stages"] == "korea_entry_training;employer_handover"
    assert row["zero_broker_fail_stages"] == "residence_registration"

    duplicate = dict(row)
    try:
        record(
            duplicate,
            tester_id="KEP-0031",
            experience_year="2024",
            current_stage="first_payroll_check",
            broker_used="no",
            workplace_info_needed="yes",
            broker_gap_status="open",
            retest_status="pending",
            workplace_evidence_status="pending",
        )
    except ValueError as exc:
        assert "already completed" in str(exc)
    else:
        raise AssertionError("completed interview was allowed to overwrite")

    try:
        record(
            dict(base),
            tester_id="KEP-0031",
            experience_year="2027",
            current_stage="first_payroll_check",
            broker_used="no",
            workplace_info_needed="yes",
            broker_gap_status="open",
            retest_status="pending",
            workplace_evidence_status="pending",
        )
    except ValueError as exc:
        assert "2004..2026" in str(exc)
    else:
        raise AssertionError("invalid experience year was accepted")

    print("WORKER_INTERVIEW_RECORD_SELF_TEST_PASS")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Record privacy-safe retrospective worker interview status. No free-text interview content is accepted."
    )
    parser.add_argument("--tester-id")
    parser.add_argument("--experience-year")
    parser.add_argument("--current-stage", default="employment_maintenance")
    parser.add_argument("--broker-used", choices=sorted(YES_NO_UNKNOWN))
    parser.add_argument("--workplace-info-needed", choices=sorted(YES_NO_UNKNOWN))
    parser.add_argument("--broker-gap-status", choices=sorted(BROKER_GAP_STATUSES), default="pending")
    parser.add_argument("--retest-status", choices=sorted(RETEST_STATUSES), default="pending")
    parser.add_argument(
        "--workplace-evidence-status",
        choices=sorted(WORKPLACE_EVIDENCE_DECISIONS),
        default="pending",
        help="pending if privacy-reviewed workplace evidence may later be published; otherwise declined/not_publishable.",
    )
    parser.add_argument("--zero-broker-pass-stage", action="append")
    parser.add_argument("--zero-broker-fail-stage", action="append")
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    if args.self_test:
        self_test()
        return 0

    required = {
        "--tester-id": args.tester_id,
        "--experience-year": args.experience_year,
        "--broker-used": args.broker_used,
        "--workplace-info-needed": args.workplace_info_needed,
    }
    missing = [flag for flag, value in required.items() if value in {None, ""}]
    if missing:
        parser.error("required: " + ", ".join(missing))

    with TRACKER.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        fields = list(reader.fieldnames or [])
        rows = list(reader)

    tester_id = str(args.tester_id).strip().upper()
    target = next((row for row in rows if row.get("tester_id", "").strip() == tester_id), None)
    if target is None:
        raise SystemExit(f"WORKER_INTERVIEW_BLOCKED unknown tester slot: {tester_id}")

    try:
        record(
            target,
            tester_id=tester_id,
            experience_year=str(args.experience_year),
            current_stage=str(args.current_stage),
            broker_used=str(args.broker_used),
            workplace_info_needed=str(args.workplace_info_needed),
            broker_gap_status=str(args.broker_gap_status),
            retest_status=str(args.retest_status),
            workplace_evidence_status=str(args.workplace_evidence_status),
            zero_broker_pass_stages=args.zero_broker_pass_stage,
            zero_broker_fail_stages=args.zero_broker_fail_stage,
        )
    except ValueError as exc:
        raise SystemExit("WORKER_INTERVIEW_BLOCKED " + str(exc)) from exc

    mode = "WRITE" if args.write else "DRY_RUN"
    print(
        f"WORKER_INTERVIEW_{mode} tester_id={tester_id} "
        f"experience_year={target['experience_year']} current_stage={target['current_stage']} "
        f"broker_used={target['broker_used']} workplace_info_needed={target['workplace_info_needed']} "
        f"interview_status={target['interview_status']} workplace_evidence_status={target['workplace_evidence_status']} "
        f"zero_broker_pass={target.get('zero_broker_pass_stages','')} "
        f"zero_broker_fail={target.get('zero_broker_fail_stages','')}"
    )

    if args.write:
        with TRACKER.open("w", encoding="utf-8-sig", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
            writer.writeheader()
            writer.writerows(rows)
        print("WORKER_INTERVIEW_WRITTEN privacy_safe_categorical_only=true")
    else:
        print("DRY_RUN_ONLY tracker was not changed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
