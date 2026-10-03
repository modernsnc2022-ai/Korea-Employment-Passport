#!/usr/bin/env python3
import csv
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TRACKER = ROOT / "recruitment" / "BETA_TESTER_TRACKER.csv"
BASE_URL = "https://modernsnc2022-ai.github.io/Korea-Employment-Passport/app.html?beta="

FORBIDDEN_COLUMNS = {
    "name",
    "full_name",
    "nickname",
    "handle",
    "contact",
    "phone",
    "phone_number",
    "email",
    "passport",
    "passport_number",
    "ktp",
    "nik",
    "arc",
    "address",
    "home_address",
    "broker_name",
    "broker_name_or_type",
}
REQUIRED_COLUMNS = {
    "tester_id",
    "target_group",
    "created_at",
    "source_channel",
    "role",
    "current_stage",
    "in_korea",
    "e9_experience",
    "broker_used",
    "broker_tasks",
    "amount_paid_idr",
    "documents_confusing",
    "official_process_gap",
    "workplace_info_needed",
    "interview_status",
    "broker_gap_status",
    "retest_status",
    "notes",
    "beta_link",
}

PII_PATTERNS = {
    "email": re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.I),
    "phone": re.compile(r"(?<!\w)(?:\+?62|0)[\s.-]?(?:\d[\s.-]?){8,13}(?!\w)"),
    "document_id": re.compile(r"\b[A-Z]{1,3}[-\s]?\d{6,12}\b", re.I),
}
SCAN_FIELDS = {
    "source_channel",
    "role",
    "current_stage",
    "e9_experience",
    "broker_tasks",
    "documents_confusing",
    "official_process_gap",
    "workplace_info_needed",
    "notes",
}


def fail(message: str) -> None:
    print("BETA_TRACKER_FAIL " + message, file=sys.stderr)
    raise SystemExit(1)


if not TRACKER.exists():
    fail(f"missing {TRACKER}")

with TRACKER.open("r", encoding="utf-8-sig", newline="") as handle:
    reader = csv.DictReader(handle)
    headers = set(reader.fieldnames or [])
    rows = list(reader)

forbidden = sorted(headers & FORBIDDEN_COLUMNS)
if forbidden:
    fail("forbidden public-repo columns: " + ", ".join(forbidden))

missing = sorted(REQUIRED_COLUMNS - headers)
if missing:
    fail("missing required columns: " + ", ".join(missing))

expected_ids = [f"KEP-{index:04d}" for index in range(1, 51)]
actual_ids = [row.get("tester_id", "").strip() for row in rows]
if actual_ids != expected_ids:
    fail("tester IDs must be exactly KEP-0001..KEP-0050 in order")

active = 0
workers = 0
for index, row in enumerate(rows, start=1):
    tester_id = row["tester_id"].strip()
    expected_group = "active_applicant" if index <= 30 else "e9_worker_korea"
    if row.get("target_group", "").strip() != expected_group:
        fail(f"{tester_id} target_group must be {expected_group}")
    if expected_group == "active_applicant":
        active += 1
    else:
        workers += 1

    expected_link = BASE_URL + tester_id
    if row.get("beta_link", "").strip() != expected_link:
        fail(f"{tester_id} beta_link mismatch")

    for field in SCAN_FIELDS:
        value = row.get(field, "") or ""
        for label, pattern in PII_PATTERNS.items():
            if pattern.search(value):
                fail(f"{tester_id} {field} contains possible {label}; keep public tracker pseudonymous")

if len(rows) != 50 or active != 30 or workers != 20:
    fail(f"unexpected cohort counts rows={len(rows)} active={active} workers={workers}")

print(f"BETA_TRACKER_PASS rows={len(rows)} active_applicants={active} e9_workers={workers}")
