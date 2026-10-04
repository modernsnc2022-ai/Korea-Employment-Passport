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
SUPPORTED_CURRENT_STAGES = SUPPORTED_STAGES | {"complete"}
BASE_URL = "https://modernsnc2022-ai.github.io/Korea-Employment-Passport/app.html?beta="

FEEDBACK_STATUSES = {"active", "complete", "withdrawn"}
BROKER_GAP_STATUSES = {"pending", "none_reported", "open", "resolved", "official_or_licensed_only"}
RETEST_STATUSES = {"pending", "passed", "failed", "not_applicable"}
YES_NO_UNKNOWN = {"yes", "no", "unknown"}


def fail(message: str) -> None:
    raise ValueError(message)


def validate_public_tester(row: dict[str, str], tester_id: str) -> None:
    match = re.fullmatch(r"KEP-(\d{4})", tester_id)
    number = int(match.group(1)) if match else 0
    if number < 1 or 31 <= number <= 50:
        fail("tester-id must be an active-applicant KEP ID (0001-0030 or 0051+)")
    if row.get("target_group", "").strip() != "active_applicant":
        fail(f"{tester_id}: not a public beta slot")
    if row.get("role", "").strip() != "public_beta_tester":
        fail(f"{tester_id}: public beta slot has not been activated")
    if row.get("eligibility_status", "").strip() != "accepted":
        fail(f"{tester_id}: eligibility_status must be accepted")
    if not row.get("application_received_at", "").strip():
        fail(f"{tester_id}: application receipt is missing")
    if not row.get("activated_at", "").strip() or not row.get("free_until", "").strip():
        fail(f"{tester_id}: beta access has not been activated")


def resume_link(row: dict[str, str]) -> str:
    tester_id = str(row.get("tester_id", "")).strip()
    base = str(row.get("beta_link", "")).strip() or (BASE_URL + tester_id)
    stage = str(row.get("current_stage", "")).strip()
    if stage not in SUPPORTED_STAGES:
        return base
    separator = "&" if "?" in base else "?"
    return f"{base}{separator}stage={stage}"


def normalize_stage_list(values: list[str] | None) -> str | None:
    if values is None:
        return None
    clean: list[str] = []
    for raw in values:
        stage_id = str(raw or "").strip()
        if stage_id not in SUPPORTED_STAGES:
            fail(f"unsupported route stage in evidence list: {stage_id}")
        if stage_id not in clean:
            clean.append(stage_id)
    return ";".join(clean)


def record(
    row: dict[str, str],
    *,
    tester_id: str,
    current_stage: str,
    feedback_status: str,
    broker_gap_status: str | None = None,
    retest_status: str | None = None,
    broker_used: str | None = None,
    workplace_info_needed: str | None = None,
    amount_paid_idr: str | None = None,
    broker_tasks: list[str] | None = None,
    documents_confusing: list[str] | None = None,
    official_process_gap: list[str] | None = None,
    zero_broker_pass_stages: list[str] | None = None,
    zero_broker_fail_stages: list[str] | None = None,
) -> dict[str, str]:
    validate_public_tester(row, tester_id)

    if current_stage not in SUPPORTED_CURRENT_STAGES:
        fail(f"unsupported current-stage: {current_stage}")
    if feedback_status not in FEEDBACK_STATUSES:
        fail("feedback-status must be active, complete, or withdrawn")
    if broker_gap_status is not None and broker_gap_status not in BROKER_GAP_STATUSES:
        fail("unsupported broker-gap-status")
    if retest_status is not None and retest_status not in RETEST_STATUSES:
        fail("unsupported retest-status")
    if broker_used is not None and broker_used not in YES_NO_UNKNOWN:
        fail("broker-used must be yes, no, or unknown")
    if workplace_info_needed is not None and workplace_info_needed not in YES_NO_UNKNOWN:
        fail("workplace-info-needed must be yes, no, or unknown")
    if amount_paid_idr is not None and amount_paid_idr != "" and not amount_paid_idr.isdigit():
        fail("amount-paid-idr must contain digits only")

    row["current_stage"] = current_stage
    row["feedback_status"] = feedback_status

    if broker_gap_status is not None:
        row["broker_gap_status"] = broker_gap_status
    if retest_status is not None:
        row["retest_status"] = retest_status
    if broker_used is not None:
        row["broker_used"] = broker_used
    if workplace_info_needed is not None:
        row["workplace_info_needed"] = workplace_info_needed
    if amount_paid_idr is not None:
        row["amount_paid_idr"] = amount_paid_idr

    for field, values in (
        ("broker_tasks", broker_tasks),
        ("documents_confusing", documents_confusing),
        ("official_process_gap", official_process_gap),
        ("zero_broker_pass_stages", zero_broker_pass_stages),
        ("zero_broker_fail_stages", zero_broker_fail_stages),
    ):
        normalized = normalize_stage_list(values)
        if normalized is not None:
            row[field] = normalized

    zero_pass = {
        part for part in row.get("zero_broker_pass_stages", "").split(";") if part
    }
    zero_fail = {
        part for part in row.get("zero_broker_fail_stages", "").split(";") if part
    }
    overlap = sorted(zero_pass & zero_fail)
    if overlap:
        fail("zero-broker PASS and FAIL cannot contain the same stage: " + ", ".join(overlap))

    row["notes"] = ""
    return row


def self_test() -> None:
    base = {
        "tester_id": "KEP-0001",
        "target_group": "active_applicant",
        "role": "public_beta_tester",
        "eligibility_status": "accepted",
        "application_received_at": "2026-10-05T09:00:00+07:00",
        "activated_at": "2026-10-06",
        "free_until": "2027-04-06",
        "current_stage": "roster",
        "feedback_status": "not_started",
        "broker_gap_status": "pending",
        "retest_status": "pending",
        "broker_used": "",
        "workplace_info_needed": "",
        "amount_paid_idr": "",
        "broker_tasks": "",
        "documents_confusing": "",
        "official_process_gap": "",
        "zero_broker_pass_stages": "",
        "zero_broker_fail_stages": "",
        "notes": "",
    }
    row = record(
        dict(base),
        tester_id="KEP-0001",
        current_stage="slc",
        feedback_status="active",
        broker_gap_status="open",
        retest_status="pending",
        broker_used="yes",
        workplace_info_needed="yes",
        amount_paid_idr="500000",
        broker_tasks=["roster", "employer_selection", "roster"],
        documents_confusing=["slc"],
        official_process_gap=["employer_selection"],
        zero_broker_pass_stages=["eligibility", "registration", "roster"],
        zero_broker_fail_stages=["employer_selection"],
    )
    assert row["feedback_status"] == "active"
    assert row["current_stage"] == "slc"
    assert row["broker_tasks"] == "roster;employer_selection"
    assert row["zero_broker_pass_stages"] == "eligibility;registration;roster"
    assert row["zero_broker_fail_stages"] == "employer_selection"
    assert row["notes"] == ""
    row["beta_link"] = BASE_URL + "KEP-0001"
    assert resume_link(row).endswith("?beta=KEP-0001&stage=slc")

    contradictory = dict(base)
    try:
        record(
            contradictory,
            tester_id="KEP-0001",
            current_stage="slc",
            feedback_status="active",
            zero_broker_pass_stages=["roster"],
            zero_broker_fail_stages=["roster"],
        )
    except ValueError as exc:
        assert "PASS and FAIL" in str(exc)
    else:
        raise AssertionError("contradictory zero-broker stage evidence was accepted")

    finished = record(
        dict(base),
        tester_id="KEP-0001",
        current_stage="complete",
        feedback_status="complete",
        broker_gap_status="resolved",
        retest_status="passed",
    )
    assert finished["current_stage"] == "complete"
    assert finished["feedback_status"] == "complete"

    try:
        record(
            dict(base),
            tester_id="KEP-0001",
            current_stage="not_a_stage",
            feedback_status="active",
        )
    except ValueError as exc:
        assert "unsupported current-stage" in str(exc)
    else:
        raise AssertionError("invalid stage was accepted")

    overflow = dict(base)
    overflow["tester_id"] = "KEP-0051"
    overflow_row = record(
        overflow,
        tester_id="KEP-0051",
        current_stage="roster",
        feedback_status="active",
    )
    assert overflow_row["current_stage"] == "roster"

    worker = dict(base)
    worker["tester_id"] = "KEP-0031"
    worker["target_group"] = "e9_worker_korea"
    try:
        record(
            worker,
            tester_id="KEP-0031",
            current_stage="employment_maintenance",
            feedback_status="active",
        )
    except ValueError as exc:
        assert "active-applicant KEP ID" in str(exc)
    else:
        raise AssertionError("worker validator was accepted by public-beta feedback recorder")

    print("BETA_FEEDBACK_RECORD_SELF_TEST_PASS")


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Record privacy-safe public-beta feedback state in the public tracker. "
            "Only categorical values and route-stage IDs are accepted; narrative feedback stays private."
        )
    )
    parser.add_argument("--tester-id")
    parser.add_argument("--current-stage")
    parser.add_argument("--feedback-status", choices=sorted(FEEDBACK_STATUSES))
    parser.add_argument("--broker-gap-status", choices=sorted(BROKER_GAP_STATUSES))
    parser.add_argument("--retest-status", choices=sorted(RETEST_STATUSES))
    parser.add_argument("--broker-used", choices=sorted(YES_NO_UNKNOWN))
    parser.add_argument("--workplace-info-needed", choices=sorted(YES_NO_UNKNOWN))
    parser.add_argument("--amount-paid-idr")
    parser.add_argument("--broker-task-stage", action="append")
    parser.add_argument("--document-confusing-stage", action="append")
    parser.add_argument("--official-process-gap-stage", action="append")
    parser.add_argument("--zero-broker-pass-stage", action="append")
    parser.add_argument("--zero-broker-fail-stage", action="append")
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    if args.self_test:
        self_test()
        return 0

    if not args.tester_id or not args.current_stage or not args.feedback_status:
        parser.error("--tester-id, --current-stage and --feedback-status are required")

    with TRACKER.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        fields = list(reader.fieldnames or [])
        rows = list(reader)

    tester_id = str(args.tester_id).strip().upper()
    target = next((row for row in rows if row.get("tester_id", "").strip() == tester_id), None)
    if target is None:
        raise SystemExit(f"BETA_FEEDBACK_BLOCKED unknown tester slot: {tester_id}")

    try:
        record(
            target,
            tester_id=tester_id,
            current_stage=str(args.current_stage),
            feedback_status=str(args.feedback_status),
            broker_gap_status=args.broker_gap_status,
            retest_status=args.retest_status,
            broker_used=args.broker_used,
            workplace_info_needed=args.workplace_info_needed,
            amount_paid_idr=args.amount_paid_idr,
            broker_tasks=args.broker_task_stage,
            documents_confusing=args.document_confusing_stage,
            official_process_gap=args.official_process_gap_stage,
            zero_broker_pass_stages=args.zero_broker_pass_stage,
            zero_broker_fail_stages=args.zero_broker_fail_stage,
        )
    except ValueError as exc:
        raise SystemExit("BETA_FEEDBACK_BLOCKED " + str(exc)) from exc

    mode = "WRITE" if args.write else "DRY_RUN"
    print(
        f"BETA_FEEDBACK_{mode} tester_id={tester_id} "
        f"current_stage={target['current_stage']} feedback_status={target['feedback_status']} "
        f"broker_gap_status={target.get('broker_gap_status','')} retest_status={target.get('retest_status','')}"
    )
    print(
        "BETA_FEEDBACK_STAGE_LISTS "
        f"broker_tasks={target.get('broker_tasks','')} "
        f"documents_confusing={target.get('documents_confusing','')} "
        f"official_process_gap={target.get('official_process_gap','')} "
        f"zero_broker_pass={target.get('zero_broker_pass_stages','')} "
        f"zero_broker_fail={target.get('zero_broker_fail_stages','')}"
    )
    print("BETA_RESUME_LINK " + resume_link(target))

    if not args.write:
        print("DRY_RUN_ONLY public tracker was not changed")
        return 0

    with TRACKER.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    print("BETA_FEEDBACK_WRITTEN categorical_only=true notes_empty=true")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
