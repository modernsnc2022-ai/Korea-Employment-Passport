#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import re
import unicodedata
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TRACKER = ROOT / "recruitment" / "BETA_TESTER_TRACKER.csv"
REGISTRY = ROOT / "docs" / "data" / "workplace_worker_evidence_v1.json"

ALLOWED_ROOT_KEYS = {
    "testerId", "experienceYear", "companyName", "companyAliases", "verificationStatus",
    "verifiedAt", "facts", "media", "reviewConfirmed"
}
ALLOWED_FACT_KEYS = {"topic", "summary", "basis"}
ALLOWED_MEDIA_KEYS = {"type", "url", "consent", "privacyReviewed", "metadataRemoved"}
PUBLISHABLE_STATUS = {"single_verified_worker"}
ALLOWED_BASIS = {"worker_experience", "worker_experience_plus_public_record"}
WORKPLACE_EVIDENCE_PUBLISHED = "published_single_verified_worker"

def valid_experience_year(value: str) -> bool:
    value = str(value or "").strip()
    return value == "unknown" or bool(re.fullmatch(r"20(?:0[4-9]|1\d|2[0-6])", value))
FORBIDDEN_KEYS = {
    "name", "workerName", "worker_name", "email", "phone", "passport",
    "passportNumber", "ktp", "nik", "arc", "homeAddress", "exactDormAddress",
    "dormRoom", "rawInterview", "privateContact"
}
PII_PATTERNS = {
    "email": re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.I),
    "phone": re.compile(r"(?<!\w)(?:\+?82|\+?62|0)[\s.-]?(?:\d[\s.-]?){8,13}(?!\w)"),
    "document_id": re.compile(r"\b[A-Z]{1,3}[-\s]?\d{6,12}\b", re.I),
}


def fail(message: str) -> None:
    raise ValueError(message)


def normalize_company_name(value: str) -> str:
    text = unicodedata.normalize("NFKC", str(value or "")).lower()
    text = re.sub(r"[^a-z0-9가-힣\s]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def assert_no_company_alias_collision(registry: dict, candidate: dict) -> None:
    candidate_canonical = normalize_company_name(candidate.get("companyName"))
    candidate_names = {
        normalize_company_name(value)
        for value in [candidate.get("companyName"), *candidate.get("companyAliases", [])]
        if normalize_company_name(value)
    }
    for existing in registry.get("records", []):
        existing_canonical = normalize_company_name(existing.get("companyName"))
        existing_names = {
            normalize_company_name(value)
            for value in [existing.get("companyName"), *existing.get("companyAliases", [])]
            if normalize_company_name(value)
        }
        if candidate_names.intersection(existing_names) and candidate_canonical != existing_canonical:
            fail(
                "company name/alias collides with a different canonical company in the public registry; "
                "use a public branch/location disambiguator and remove ambiguous aliases"
            )


def assert_keys(value: dict, allowed: set[str], path: str) -> None:
    unknown = sorted(set(value) - allowed)
    if unknown:
        fail(f"{path}: unsupported fields: {', '.join(unknown)}")


def scan_public_text(value, path: str = "$") -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            if key in FORBIDDEN_KEYS:
                fail(f"{path}.{key}: forbidden identity/private field")
            scan_public_text(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            scan_public_text(child, f"{path}[{index}]")
    elif isinstance(value, str):
        for label, pattern in PII_PATTERNS.items():
            if pattern.search(value):
                fail(f"{path}: possible {label}; public worker evidence must remain de-identified")


def validate_worker_row(row: dict[str, str], tester_id: str) -> None:
    if not re.fullmatch(r"KEP-00(?:3[1-9]|4\d|50)", tester_id):
        fail("testerId must be KEP-0031 through KEP-0050")
    if row.get("target_group", "").strip() != "e9_worker_korea":
        fail(f"{tester_id}: not an E-9 worker panel slot")
    if row.get("role", "").strip() != "e9_worker_validator":
        fail(f"{tester_id}: worker validator slot has not been assigned")
    if not row.get("created_at", "").strip():
        fail(f"{tester_id}: worker validator slot has not been assigned")
    if row.get("in_korea", "").strip().lower() != "yes":
        fail(f"{tester_id}: in_korea must be yes")
    if row.get("e9_experience", "").strip().lower() != "confirmed":
        fail(f"{tester_id}: E-9 experience must be confirmed")
    if row.get("interview_status", "").strip().lower() != "completed":
        fail(f"{tester_id}: worker interview must be completed before workplace evidence is published")
    experience_year = row.get("experience_year", "").strip()
    if not valid_experience_year(experience_year):
        fail(f"{tester_id}: experience_year must be 2004..2026 or unknown")
    evidence_status = row.get("workplace_evidence_status", "").strip().lower()
    if evidence_status == WORKPLACE_EVIDENCE_PUBLISHED:
        fail(f"{tester_id}: workplace evidence is already published")
    if evidence_status not in {"pending", "declined", "not_publishable"}:
        fail(
            f"{tester_id}: workplace_evidence_status must be pending, declined, or not_publishable "
            "before publication"
        )


def validate_intake(intake: dict) -> None:
    if not isinstance(intake, dict):
        fail("intake must be a JSON object")
    assert_keys(intake, ALLOWED_ROOT_KEYS, "$")

    tester_id = str(intake.get("testerId", "")).strip()
    if not re.fullmatch(r"KEP-00(?:3[1-9]|4\d|50)", tester_id):
        fail("testerId must be KEP-0031 through KEP-0050")

    experience_year = str(intake.get("experienceYear", "")).strip()
    if not valid_experience_year(experience_year):
        fail("experienceYear must be 2004..2026 or unknown")

    company = str(intake.get("companyName", "")).strip()
    if not company:
        fail("companyName is required")

    aliases = intake.get("companyAliases", [])
    if not isinstance(aliases, list) or any(not isinstance(x, str) for x in aliases):
        fail("companyAliases must be a list of strings")

    status = intake.get("verificationStatus")
    if status not in PUBLISHABLE_STATUS:
        fail("single-interview publisher only allows verificationStatus=single_verified_worker")

    verified_at = str(intake.get("verifiedAt", ""))
    date.fromisoformat(verified_at)

    if intake.get("reviewConfirmed") is not True:
        fail("reviewConfirmed must be true before evidence can be prepared")

    facts = intake.get("facts")
    if not isinstance(facts, list) or not facts:
        fail("at least one summarized fact is required")
    for index, fact in enumerate(facts):
        if not isinstance(fact, dict):
            fail(f"$.facts[{index}]: must be an object")
        assert_keys(fact, ALLOWED_FACT_KEYS, f"$.facts[{index}]")
        if not str(fact.get("topic", "")).strip() or not str(fact.get("summary", "")).strip():
            fail(f"$.facts[{index}]: topic and summary are required")
        if fact.get("basis") not in ALLOWED_BASIS:
            fail(f"$.facts[{index}]: unsupported basis")

    media = intake.get("media", [])
    if not isinstance(media, list):
        fail("media must be a list")
    for index, item in enumerate(media):
        if not isinstance(item, dict):
            fail(f"$.media[{index}]: must be an object")
        assert_keys(item, ALLOWED_MEDIA_KEYS, f"$.media[{index}]")
        if item.get("type") not in {"photo", "video"}:
            fail(f"$.media[{index}]: unsupported media type")
        if item.get("consent") is not True:
            fail(f"$.media[{index}]: consent=true is required")
        if item.get("privacyReviewed") is not True:
            fail(f"$.media[{index}]: privacyReviewed=true is required")
        if item.get("metadataRemoved") is not True:
            fail(f"$.media[{index}]: metadataRemoved=true is required")
        if not str(item.get("url", "")).startswith("https://"):
            fail(f"$.media[{index}]: HTTPS URL is required")

    public_projection = {
        "experienceYear": experience_year,
        "companyName": company,
        "companyAliases": aliases,
        "verificationStatus": status,
        "verifiedAt": verified_at,
        "facts": facts,
        "media": media,
    }
    scan_public_text(public_projection)


def next_evidence_id(registry: dict) -> str:
    numbers = []
    for row in registry.get("records", []):
        match = re.fullmatch(r"WPE-(\d{4})", str(row.get("evidenceId", "")))
        if not match:
            fail(f"registry contains invalid evidenceId: {row.get('evidenceId')!r}")
        numbers.append(int(match.group(1)))
    numbers.sort()
    expected = list(range(1, len(numbers) + 1))
    if numbers != expected:
        fail("registry evidence IDs must remain contiguous before adding a new record")
    return f"WPE-{len(numbers) + 1:04d}"


def build_public_record(intake: dict, registry: dict) -> dict:
    validate_intake(intake)
    record = {
        "evidenceId": next_evidence_id(registry),
        "experienceYear": str(intake["experienceYear"]).strip(),
        "companyName": str(intake["companyName"]).strip(),
        "companyAliases": [x.strip() for x in intake.get("companyAliases", []) if x.strip()],
        "verificationStatus": intake["verificationStatus"],
        "verifiedAt": intake["verifiedAt"],
        "facts": intake["facts"],
    }
    if intake.get("media"):
        record["media"] = intake["media"]
    scan_public_text(record)
    assert_no_company_alias_collision(registry, record)
    return record


def read_tracker() -> tuple[list[str], list[dict[str, str]]]:
    with TRACKER.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        return list(reader.fieldnames or []), list(reader)


def write_tracker(fields: list[str], rows: list[dict[str, str]]) -> None:
    with TRACKER.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def self_test() -> None:
    rows = [{
        "tester_id": "KEP-0031",
        "target_group": "e9_worker_korea",
        "created_at": "2026-10-04",
        "role": "e9_worker_validator",
        "in_korea": "yes",
        "e9_experience": "confirmed",
        "experience_year": "2024",
        "interview_status": "completed",
        "workplace_evidence_status": "pending",
    }]
    registry = {"records": [{"evidenceId": "WPE-0001"}]}
    intake = {
        "testerId": "KEP-0031",
        "experienceYear": "2024",
        "companyName": "Sample Manufacturing Co.",
        "companyAliases": ["Sample Mfg"],
        "verificationStatus": "single_verified_worker",
        "verifiedAt": "2026-10-04",
        "reviewConfirmed": True,
        "facts": [{
            "topic": "accommodation",
            "summary": "Worker reported employer-provided shared accommodation; cost varies by contract.",
            "basis": "worker_experience",
        }],
        "media": [],
    }
    validate_worker_row(rows[0], intake["testerId"])
    published_row = dict(rows[0])
    published_row["workplace_evidence_status"] = WORKPLACE_EVIDENCE_PUBLISHED
    try:
        validate_worker_row(published_row, intake["testerId"])
    except ValueError as exc:
        assert "already published" in str(exc)
    else:
        raise AssertionError("published worker evidence was allowed to publish twice")

    incomplete_row = dict(rows[0])
    incomplete_row["interview_status"] = "new"
    try:
        validate_worker_row(incomplete_row, intake["testerId"])
    except ValueError as exc:
        assert "interview must be completed" in str(exc)
    else:
        raise AssertionError("workplace evidence was allowed before interview completion")

    record = build_public_record(intake, registry)
    assert record["evidenceId"] == "WPE-0002"
    assert "testerId" not in record and "tester_id" not in record

    bad = json.loads(json.dumps(intake))
    bad["facts"][0]["summary"] = "Contact worker@example.com"
    try:
        build_public_record(bad, registry)
    except ValueError as exc:
        assert "possible email" in str(exc)
    else:
        raise AssertionError("PII-like email was not rejected")

    exaggerated = json.loads(json.dumps(intake))
    exaggerated["verificationStatus"] = "multi_verified_workers"
    try:
        build_public_record(exaggerated, registry)
    except ValueError as exc:
        assert "single-interview publisher" in str(exc)
    else:
        raise AssertionError("single interview was allowed to claim multi-worker verification")

    collision_registry = {
        "records": [{
            "evidenceId": "WPE-0001",
            "companyName": "Other Manufacturing",
            "companyAliases": ["Sample Manufacturing Co."],
        }]
    }
    try:
        build_public_record(intake, collision_registry)
    except ValueError as exc:
        assert "collides with a different canonical company" in str(exc)
    else:
        raise AssertionError("ambiguous company alias collision was not rejected")

    bad_media = json.loads(json.dumps(intake))
    bad_media["media"] = [{
        "type": "photo",
        "url": "https://example.invalid/photo.jpg",
        "consent": True,
        "privacyReviewed": True,
        "metadataRemoved": False,
    }]
    try:
        build_public_record(bad_media, registry)
    except ValueError as exc:
        assert "metadataRemoved=true" in str(exc)
    else:
        raise AssertionError("media without metadata removal was not rejected")

    print("WORKER_EVIDENCE_PUBLISH_SELF_TEST_PASS")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Prepare or publish a privacy-safe E-9 worker evidence record. Dry-run is the default."
    )
    parser.add_argument("--intake", help="Path to a private/local JSON intake file; do not commit completed intake files.")
    parser.add_argument("--write", action="store_true", help="Write sanitized record to public registry after the interview has already been completed.")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    if args.self_test:
        self_test()
        return 0
    if not args.intake:
        parser.error("--intake is required unless --self-test is used")

    intake_path = Path(args.intake).expanduser().resolve()
    intake = json.loads(intake_path.read_text(encoding="utf-8-sig"))
    validate_intake(intake)

    fields, rows = read_tracker()
    tester_id = str(intake["testerId"]).strip()
    worker = next((row for row in rows if row.get("tester_id", "").strip() == tester_id), None)
    if worker is None:
        raise SystemExit(f"WORKER_EVIDENCE_BLOCKED unknown tester slot: {tester_id}")
    try:
        validate_worker_row(worker, tester_id)
    except ValueError as exc:
        raise SystemExit("WORKER_EVIDENCE_BLOCKED " + str(exc)) from exc
    intake_year = str(intake.get("experienceYear", "")).strip()
    tracker_year = str(worker.get("experience_year", "") or "").strip()
    if not tracker_year:
        raise SystemExit("WORKER_EVIDENCE_BLOCKED tracker experience_year is missing; record the interview first")
    if tracker_year != intake_year:
        raise SystemExit(
            f"WORKER_EVIDENCE_BLOCKED experience year mismatch tracker={tracker_year} intake={intake_year}"
        )

    registry = json.loads(REGISTRY.read_text(encoding="utf-8-sig"))
    try:
        record = build_public_record(intake, registry)
    except ValueError as exc:
        raise SystemExit("WORKER_EVIDENCE_BLOCKED " + str(exc)) from exc

    mode = "WRITE" if args.write else "DRY_RUN"
    print(f"WORKER_EVIDENCE_{mode} tester_id={tester_id} -> {record['evidenceId']}")
    print(json.dumps(record, ensure_ascii=False, indent=2))

    if not args.write:
        print("DRY_RUN_ONLY completed intake file was not copied and public files were not changed")
        return 0

    registry.setdefault("records", []).append(record)
    worker["workplace_evidence_status"] = WORKPLACE_EVIDENCE_PUBLISHED
    REGISTRY.write_text(json.dumps(registry, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_tracker(fields, rows)
    print(
        f"WORKER_EVIDENCE_WRITTEN evidence_id={record['evidenceId']} "
        f"experience_year={intake_year} workplace_evidence_status={WORKPLACE_EVIDENCE_PUBLISHED} "
        "interview_status=already_completed"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
