#!/usr/bin/env python3
from __future__ import annotations

import argparse
import calendar
import csv
import json
from datetime import date, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TRACKER = ROOT / "recruitment" / "BETA_TESTER_TRACKER.csv"
PROGRAM = ROOT / "docs" / "data" / "beta_program_v1.json"

def add_months(value: date, months: int) -> date:
    idx = value.month - 1 + months
    year = value.year + idx // 12
    month = idx % 12 + 1
    day = min(value.day, calendar.monthrange(year, month)[1])
    return date(year, month, day)

def parse_ts(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("received timestamp must include timezone")
    return parsed

def load_tracker():
    with TRACKER.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        return list(reader.fieldnames or []), list(reader)

def assign(rows, received_at, activation_date, current_stage, source_channel):
    received = parse_ts(received_at)
    activation = date.fromisoformat(activation_date)
    public = [r for r in rows if r.get("target_group", "").strip() == "active_applicant"]
    assigned = [r for r in public if r.get("application_received_at", "").strip()]
    if assigned and received < parse_ts(assigned[-1]["application_received_at"].strip()):
        raise ValueError("received timestamp is earlier than the last assigned eligible application")
    target = next((r for r in public if not r.get("application_received_at", "").strip()), None)
    if target is None:
        raise ValueError("all 30 public beta slots are already assigned")
    target["application_received_at"] = received_at
    target["eligibility_status"] = "accepted"
    target["activated_at"] = activation.isoformat()
    target["free_until"] = add_months(activation, 6).isoformat()
    target["feedback_status"] = "not_started"
    target["current_stage"] = current_stage
    target["source_channel"] = source_channel
    target["role"] = "public_beta_tester"
    target["created_at"] = activation.isoformat()
    return target

def self_test():
    rows = [{
        "tester_id": f"KEP-{i:04d}",
        "target_group": "active_applicant" if i <= 30 else "e9_worker_korea",
        "application_received_at": "", "eligibility_status": "", "activated_at": "",
        "free_until": "", "feedback_status": "", "current_stage": "",
        "source_channel": "", "role": "", "created_at": "", "beta_link": ""
    } for i in range(1, 51)]
    first = assign(rows, "2026-10-05T09:00:00+07:00", "2026-10-06", "roster", "community")
    second = assign(rows, "2026-10-05T09:01:00+07:00", "2026-10-05", "slc", "community")
    assert first["tester_id"] == "KEP-0001"
    assert first["free_until"] == "2027-04-06"
    assert second["tester_id"] == "KEP-0002"
    assert second["activated_at"] < first["activated_at"]
    try:
        assign(rows, "2026-10-05T08:59:00+07:00", "2026-10-07", "visa_docs", "community")
    except ValueError:
        pass
    else:
        raise AssertionError("out-of-order receipt was not rejected")
    print("BETA_SLOT_ASSIGNMENT_SELF_TEST_PASS")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--received-at")
    parser.add_argument("--activation-date")
    parser.add_argument("--current-stage")
    parser.add_argument("--source-channel")
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return 0
    if json.loads(PROGRAM.read_text(encoding="utf-8-sig")).get("status") != "open":
        raise SystemExit("BETA_SLOT_ASSIGNMENT_BLOCKED recruitment status is not OPEN")
    required = [args.received_at, args.activation_date, args.current_stage, args.source_channel]
    if not all(required):
        parser.error("--received-at, --activation-date, --current-stage and --source-channel are required")
    fields, rows = load_tracker()
    target = assign(rows, *required)
    if args.write:
        with TRACKER.open("w", encoding="utf-8-sig", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
            writer.writeheader()
            writer.writerows(rows)
    print(
        "BETA_SLOT_" + ("WRITTEN" if args.write else "DRY_RUN") +
        " tester_id=" + target["tester_id"] +
        " free_until=" + target["free_until"] +
        " beta_link=" + target.get("beta_link", "")
    )
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
