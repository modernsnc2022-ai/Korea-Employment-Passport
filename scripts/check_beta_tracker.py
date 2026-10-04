#!/usr/bin/env python3
import calendar
import csv
import json
import re
import sys
from datetime import date, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TRACKER = ROOT / "recruitment" / "BETA_TESTER_TRACKER.csv"
ROUTE = ROOT / "docs" / "data" / "id_e9_manufacturing_2026.json"
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
    "experience_year",
    "broker_used",
    "broker_tasks",
    "amount_paid_idr",
    "documents_confusing",
    "official_process_gap",
    "workplace_info_needed",
    "workplace_evidence_status",
    "interview_status",
    "broker_gap_status",
    "retest_status",
    "application_received_at",
    "eligibility_status",
    "activated_at",
    "free_until",
    "feedback_status",
    "notes",
    "beta_link",
    "zero_broker_pass_stages",
    "zero_broker_fail_stages",
}

PII_PATTERNS = {
    "email": re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.I),
    "phone": re.compile(r"(?<!\w)(?:\+?82|\+?62|0)[\s.-]?(?:\d[\s.-]?){8,13}(?!\w)"),
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

ELIGIBILITY_STATUSES = {"", "pending", "eligible", "ineligible", "waitlist", "accepted"}
FEEDBACK_STATUSES = {"", "not_started", "active", "complete", "withdrawn"}
INTERVIEW_STATUSES = {"", "new", "scheduled", "completed", "withdrawn"}
BROKER_GAP_STATUSES = {"", "open", "resolved", "official_or_licensed_only"}
RETEST_STATUSES = {"", "pending", "passed", "failed", "not_applicable"}
WORKPLACE_EVIDENCE_STATUSES = {"", "pending", "published_single_verified_worker", "declined", "not_publishable"}
YES_NO_UNKNOWN = {"", "yes", "no", "unknown"}
CONTROLLED_STAGE_LIST_FIELDS = {
    "broker_tasks", "documents_confusing", "official_process_gap",
    "zero_broker_pass_stages", "zero_broker_fail_stages"
}
SUPPORTED_STAGES = {
    row["id"] for row in json.loads(ROUTE.read_text(encoding="utf-8-sig")).get("stages", [])
}
SUPPORTED_CURRENT_STAGES = SUPPORTED_STAGES | {"complete"}


def add_calendar_months(value: date, months: int) -> date:
    month_index = value.month - 1 + months
    year = value.year + month_index // 12
    month = month_index % 12 + 1
    day = min(value.day, calendar.monthrange(year, month)[1])
    return date(year, month, day)


def parse_utc_timestamp(value: str, tester_id: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        fail(f"{tester_id} application_received_at must be ISO-8601")
    if parsed.tzinfo is None:
        fail(f"{tester_id} application_received_at must include timezone")
    return parsed


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

    application_received = row.get("application_received_at", "").strip()
    eligibility_status = row.get("eligibility_status", "").strip()
    activated_at = row.get("activated_at", "").strip()
    free_until = row.get("free_until", "").strip()
    feedback_status = row.get("feedback_status", "").strip()
    interview_status = row.get("interview_status", "").strip()
    experience_year = row.get("experience_year", "").strip()
    workplace_evidence_status = row.get("workplace_evidence_status", "").strip()
    broker_gap_status = row.get("broker_gap_status", "").strip()
    retest_status = row.get("retest_status", "").strip()
    current_stage = row.get("current_stage", "").strip()

    if interview_status not in INTERVIEW_STATUSES:
        fail(f"{tester_id} invalid interview_status {interview_status!r}")
    if workplace_evidence_status not in WORKPLACE_EVIDENCE_STATUSES:
        fail(f"{tester_id} invalid workplace_evidence_status {workplace_evidence_status!r}")
    if experience_year and experience_year != "unknown" and not re.fullmatch(r"20(?:0[4-9]|1\d|2[0-6])", experience_year):
        fail(f"{tester_id} experience_year must be 2004..2026 or unknown")
    if expected_group == "active_applicant" and (experience_year or workplace_evidence_status):
        fail(f"{tester_id} active applicant must not use retrospective worker evidence fields")
    if workplace_evidence_status == "published_single_verified_worker":
        if expected_group != "e9_worker_korea":
            fail(f"{tester_id} published worker evidence requires E-9 worker panel")
        if interview_status != "completed":
            fail(f"{tester_id} published worker evidence requires interview_status=completed")
        if not experience_year:
            fail(f"{tester_id} published worker evidence requires experience_year")
    if broker_gap_status not in BROKER_GAP_STATUSES:
        fail(f"{tester_id} invalid broker_gap_status {broker_gap_status!r}")
    if retest_status not in RETEST_STATUSES:
        fail(f"{tester_id} invalid retest_status {retest_status!r}")
    if current_stage and current_stage not in SUPPORTED_CURRENT_STAGES:
        fail(f"{tester_id} current_stage is not a supported route stage or complete: {current_stage}")
    if eligibility_status not in ELIGIBILITY_STATUSES:
        fail(f"{tester_id} invalid eligibility_status {eligibility_status!r}")
    if feedback_status not in FEEDBACK_STATUSES:
        fail(f"{tester_id} invalid feedback_status {feedback_status!r}")

    broker_used = row.get("broker_used", "").strip()
    workplace_info_needed = row.get("workplace_info_needed", "").strip()
    amount_paid_idr = row.get("amount_paid_idr", "").strip()
    if broker_used not in YES_NO_UNKNOWN:
        fail(f"{tester_id} broker_used must be yes/no/unknown or blank")
    if workplace_info_needed not in YES_NO_UNKNOWN:
        fail(f"{tester_id} workplace_info_needed must be yes/no/unknown or blank")
    if amount_paid_idr and not amount_paid_idr.isdigit():
        fail(f"{tester_id} amount_paid_idr must contain digits only")
    if row.get("notes", "").strip():
        fail(f"{tester_id} public tracker notes must remain empty; keep narrative interview notes private")
    for field in CONTROLLED_STAGE_LIST_FIELDS:
        value = row.get(field, "").strip()
        if not value:
            continue
        values = [part.strip() for part in value.split(";") if part.strip()]
        if not values or any(stage_id not in SUPPORTED_STAGES for stage_id in values):
            fail(f"{tester_id} {field} must contain only semicolon-separated route stage IDs")
        if len(values) != len(set(values)):
            fail(f"{tester_id} {field} must not contain duplicate stage IDs")
    zero_pass = {
        part.strip() for part in row.get("zero_broker_pass_stages", "").split(";") if part.strip()
    }
    zero_fail = {
        part.strip() for part in row.get("zero_broker_fail_stages", "").split(";") if part.strip()
    }
    overlap = sorted(zero_pass & zero_fail)
    if overlap:
        fail(f"{tester_id} zero-broker PASS/FAIL overlap: {', '.join(overlap)}")
    if expected_group == "e9_worker_korea" and interview_status == "completed" and not experience_year:
        fail(f"{tester_id} completed worker interview requires experience_year")

    if application_received:
        if expected_group != "active_applicant":
            fail(f"{tester_id} retrospective worker panel must not use public-beta application queue fields")
        if eligibility_status != "accepted":
            fail(f"{tester_id} assigned public-beta slot requires eligibility_status=accepted")
        parse_utc_timestamp(application_received, tester_id)
    elif eligibility_status == "accepted":
        fail(f"{tester_id} eligibility_status=accepted requires application_received_at")

    if bool(activated_at) != bool(free_until):
        fail(f"{tester_id} activated_at and free_until must be set together")

    if activated_at:
        if expected_group != "active_applicant":
            fail(f"{tester_id} E-9 worker validator must not receive public-beta entitlement fields")
        if eligibility_status != "accepted":
            fail(f"{tester_id} activated beta access requires eligibility_status=accepted")
        if not application_received:
            fail(f"{tester_id} activated beta access requires application_received_at")
        try:
            activation_date = date.fromisoformat(activated_at)
            expiry_date = date.fromisoformat(free_until)
        except ValueError:
            fail(f"{tester_id} activated_at/free_until must use YYYY-MM-DD")
        expected_expiry = add_calendar_months(activation_date, 6)
        if expiry_date != expected_expiry:
            fail(
                f"{tester_id} free_until must be exactly six calendar months after activation "
                f"({expected_expiry.isoformat()})"
            )

    for field in SCAN_FIELDS:
        value = row.get(field, "") or ""
        for label, pattern in PII_PATTERNS.items():
            if pattern.search(value):
                fail(f"{tester_id} {field} contains possible {label}; keep public tracker pseudonymous")

if len(rows) != 50 or active != 30 or workers != 20:
    fail(f"unexpected cohort counts rows={len(rows)} active={active} workers={workers}")

public_rows = rows[:30]
seen_empty_slot = False
previous_received = None
previous_id = None
assigned_public = 0
for row in public_rows:
    tester_id = row["tester_id"].strip()
    value = row.get("application_received_at", "").strip()
    if not value:
        seen_empty_slot = True
        continue
    if seen_empty_slot:
        fail(f"{tester_id} is assigned after an empty earlier public-beta slot; assign KEP IDs contiguously from KEP-0001")
    received = parse_utc_timestamp(value, tester_id)
    if previous_received is not None and received < previous_received:
        fail(
            f"{tester_id} application_received_at is earlier than {previous_id}; "
            "KEP-0001..KEP-0030 must follow eligible application receipt order"
        )
    previous_received = received
    previous_id = tester_id
    assigned_public += 1

worker_rows = rows[30:]
seen_empty_worker = False
assigned_workers = 0
for row in worker_rows:
    tester_id = row["tester_id"].strip()
    joined = row.get("created_at", "").strip()
    if not joined:
        if row.get("experience_year", "").strip() or row.get("workplace_evidence_status", "").strip():
            fail(f"{tester_id} unassigned worker slot must not contain interview/evidence state")
        seen_empty_worker = True
        continue
    if seen_empty_worker:
        fail(f"{tester_id} is assigned after an empty earlier worker-validator slot; assign KEP-0031..KEP-0050 contiguously")
    try:
        date.fromisoformat(joined)
    except ValueError:
        fail(f"{tester_id} created_at must use YYYY-MM-DD for worker validators")
    if row.get("role", "").strip() != "e9_worker_validator":
        fail(f"{tester_id} assigned worker validator requires role=e9_worker_validator")
    if row.get("in_korea", "").strip() != "yes":
        fail(f"{tester_id} assigned worker validator requires in_korea=yes")
    if row.get("e9_experience", "").strip() != "confirmed":
        fail(f"{tester_id} assigned worker validator requires e9_experience=confirmed")
    evidence_status = row.get("workplace_evidence_status", "").strip()
    if evidence_status not in {"pending", "published_single_verified_worker", "declined", "not_publishable"}:
        fail(f"{tester_id} assigned worker validator requires explicit workplace_evidence_status")
    assigned_workers += 1

activated = sum(1 for row in rows if row.get("activated_at", "").strip())
print(
    f"BETA_TRACKER_PASS rows={len(rows)} active_applicants={active} "
    f"e9_workers={workers} assigned_public_beta={assigned_public} "
    f"assigned_worker_validators={assigned_workers} "
    f"activated_public_beta={activated} free_months=6"
)
