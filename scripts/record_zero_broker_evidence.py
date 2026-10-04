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


def fail(message: str) -> None:
    raise ValueError(message)


def normalize_stage_list(values: list[str] | None) -> str:
    clean: list[str] = []
    for raw in values or []:
        stage_id = str(raw or "").strip()
        if stage_id not in SUPPORTED_STAGES:
            fail(f"unsupported route stage: {stage_id}")
        if stage_id not in clean:
            clean.append(stage_id)
    return ";".join(clean)


def validate_assigned_tester(row: dict[str, str], tester_id: str) -> None:
    if not re.fullmatch(r"KEP-00(?:0[1-9]|[1-4]\d|50)", tester_id):
        fail("tester-id must be KEP-0001 through KEP-0050")

    group = row.get("target_group", "").strip()
    if group == "active_applicant":
        if row.get("role", "").strip() != "public_beta_tester":
            fail(f"{tester_id}: public beta slot is not activated")
        if row.get("eligibility_status", "").strip() != "accepted":
            fail(f"{tester_id}: public beta eligibility is not accepted")
        if not row.get("activated_at", "").strip():
            fail(f"{tester_id}: public beta access is not activated")
        return

    if group == "e9_worker_korea":
        if row.get("role", "").strip() != "e9_worker_validator":
            fail(f"{tester_id}: worker validator slot is not assigned")
        if row.get("interview_status", "").strip() != "completed":
            fail(f"{tester_id}: worker interview must be completed before follow-up stage evidence is recorded")
        if not row.get("experience_year", "").strip():
            fail(f"{tester_id}: worker experience_year is missing")
        return

    fail(f"{tester_id}: unsupported beta target group")


def record(
    row: dict[str, str],
    *,
    tester_id: str,
    pass_stages: list[str] | None,
    fail_stages: list[str] | None,
) -> dict[str, str]:
    validate_assigned_tester(row, tester_id)
    if pass_stages is None and fail_stages is None:
        fail("provide at least one --pass-stage or --fail-stage snapshot")

    pass_value = normalize_stage_list(pass_stages)
    fail_value = normalize_stage_list(fail_stages)
    pass_set = {part for part in pass_value.split(";") if part}
    fail_set = {part for part in fail_value.split(";") if part}
    overlap = sorted(pass_set & fail_set)
    if overlap:
        fail("zero-broker PASS and FAIL cannot contain the same stage: " + ", ".join(overlap))

    # This command treats the supplied PASS/FAIL lists as the latest complete
    # stage-evidence snapshot from the verified participant channel.
    row["zero_broker_pass_stages"] = pass_value
    row["zero_broker_fail_stages"] = fail_value
    row["notes"] = ""
    return row


def self_test() -> None:
    public = {
        "tester_id": "KEP-0001",
        "target_group": "active_applicant",
        "role": "public_beta_tester",
        "eligibility_status": "accepted",
        "activated_at": "2026-10-04",
        "zero_broker_pass_stages": "",
        "zero_broker_fail_stages": "",
        "notes": "",
    }
    updated = record(
        dict(public),
        tester_id="KEP-0001",
        pass_stages=["eligibility", "registration"],
        fail_stages=["exam_fee"],
    )
    assert updated["zero_broker_pass_stages"] == "eligibility;registration"
    assert updated["zero_broker_fail_stages"] == "exam_fee"

    worker = {
        "tester_id": "KEP-0031",
        "target_group": "e9_worker_korea",
        "role": "e9_worker_validator",
        "interview_status": "completed",
        "experience_year": "2024",
        "zero_broker_pass_stages": "",
        "zero_broker_fail_stages": "",
        "notes": "",
    }
    worker_updated = record(
        dict(worker),
        tester_id="KEP-0031",
        pass_stages=["korea_entry_training"],
        fail_stages=[],
    )
    assert worker_updated["zero_broker_pass_stages"] == "korea_entry_training"

    incomplete = dict(worker)
    incomplete["interview_status"] = "new"
    try:
        record(
            incomplete,
            tester_id="KEP-0031",
            pass_stages=["korea_entry_training"],
            fail_stages=[],
        )
    except ValueError as exc:
        assert "interview must be completed" in str(exc)
    else:
        raise AssertionError("worker follow-up evidence was accepted before interview completion")

    try:
        record(
            dict(public),
            tester_id="KEP-0001",
            pass_stages=["roster"],
            fail_stages=["roster"],
        )
    except ValueError as exc:
        assert "PASS and FAIL" in str(exc)
    else:
        raise AssertionError("contradictory stage evidence was accepted")

    print("ZERO_BROKER_EVIDENCE_RECORD_SELF_TEST_PASS")


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Replace a beta tester's stage-level zero-broker PASS/FAIL snapshot. "
            "Use only after verifying the private enrollment/contact channel."
        )
    )
    parser.add_argument("--tester-id")
    parser.add_argument("--pass-stage", action="append")
    parser.add_argument("--fail-stage", action="append")
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    if args.self_test:
        self_test()
        return 0
    if not args.tester_id:
        parser.error("--tester-id is required")

    with TRACKER.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        fields = list(reader.fieldnames or [])
        rows = list(reader)

    tester_id = str(args.tester_id).strip().upper()
    target = next((row for row in rows if row.get("tester_id", "").strip() == tester_id), None)
    if target is None:
        raise SystemExit(f"ZERO_BROKER_EVIDENCE_BLOCKED unknown tester slot: {tester_id}")

    try:
        record(
            target,
            tester_id=tester_id,
            pass_stages=args.pass_stage,
            fail_stages=args.fail_stage,
        )
    except ValueError as exc:
        raise SystemExit("ZERO_BROKER_EVIDENCE_BLOCKED " + str(exc)) from exc

    mode = "WRITE" if args.write else "DRY_RUN"
    print(
        f"ZERO_BROKER_EVIDENCE_{mode} tester_id={tester_id} "
        f"pass={target.get('zero_broker_pass_stages','')} "
        f"fail={target.get('zero_broker_fail_stages','')}"
    )
    if not args.write:
        print("DRY_RUN_ONLY tracker was not changed")
        return 0

    with TRACKER.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    print("ZERO_BROKER_EVIDENCE_WRITTEN stage_ids_only=true notes_empty=true")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
