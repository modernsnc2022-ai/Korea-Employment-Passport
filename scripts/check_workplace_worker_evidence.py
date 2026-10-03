#!/usr/bin/env python3
import json
import re
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "docs" / "data" / "workplace_worker_evidence_v1.json"

FORBIDDEN_KEYS = {
    "name", "workerName", "worker_name", "testerId", "tester_id", "email", "phone",
    "passport", "passportNumber", "ktp", "nik", "arc", "homeAddress",
    "exactDormAddress", "dormRoom", "rawInterview", "privateContact"
}
PII_PATTERNS = {
    "email": re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.I),
    "phone": re.compile(r"(?<!\w)(?:\+?82|\+?62|0)[\s.-]?(?:\d[\s.-]?){8,13}(?!\w)"),
    "document_id": re.compile(r"\b[A-Z]{1,3}[-\s]?\d{6,12}\b", re.I),
}
ALLOWED_STATUS = {"single_verified_worker", "multi_verified_workers", "worker_plus_public_record"}

def normalize_company_name(value):
    text = unicodedata.normalize("NFKC", str(value or "")).lower()
    text = re.sub(r"[^a-z0-9가-힣\s]", " ", text)
    return re.sub(r"\s+", " ", text).strip()

def fail(message):
    print("WORKPLACE_WORKER_EVIDENCE_FAIL " + message, file=sys.stderr)
    raise SystemExit(1)

def walk(value, path="$"):
    if isinstance(value, dict):
        for key, child in value.items():
            if key in FORBIDDEN_KEYS:
                fail(f"{path}.{key}: forbidden identity/private field")
            walk(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            walk(child, f"{path}[{index}]")
    elif isinstance(value, str):
        for label, pattern in PII_PATTERNS.items():
            if pattern.search(value):
                fail(f"{path}: possible {label}; public worker evidence must remain de-identified")

data=json.loads(PATH.read_text(encoding="utf-8-sig"))
walk(data)
if data.get("status") != "beta_collection":
    fail("registry status must remain beta_collection until real evidence is published")
if data.get("displayPolicy", {}).get("noEvidenceMeaning", "").strip() == "":
    fail("no-evidence interpretation policy is required")
if data.get("displayPolicy", {}).get("mediaRule", "").strip() == "":
    fail("media privacy rule is required")

ids=set()
company_name_owners={}
for row in data.get("records", []):
    evidence_id=str(row.get("evidenceId", "")).strip()
    if not re.fullmatch(r"WPE-\d{4}", evidence_id):
        fail(f"invalid evidenceId: {evidence_id!r}")
    if evidence_id in ids:
        fail(f"duplicate evidenceId: {evidence_id}")
    ids.add(evidence_id)
    if not str(row.get("companyName", "")).strip():
        fail(f"{evidence_id}: companyName is required")
    aliases=row.get("companyAliases", [])
    if not isinstance(aliases, list):
        fail(f"{evidence_id}: companyAliases must be a list")
    canonical=normalize_company_name(row.get("companyName"))
    if not canonical:
        fail(f"{evidence_id}: companyName is empty after normalization")
    for raw_name in [row.get("companyName"), *aliases]:
        normalized=normalize_company_name(raw_name)
        if not normalized:
            fail(f"{evidence_id}: company name/alias is empty after normalization")
        previous=company_name_owners.get(normalized)
        if previous and previous != canonical:
            fail(
                f"{evidence_id}: ambiguous company name/alias {raw_name!r}; "
                f"it already maps to a different canonical company"
            )
        company_name_owners[normalized]=canonical
    if row.get("verificationStatus") not in ALLOWED_STATUS:
        fail(f"{evidence_id}: invalid verificationStatus")
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", str(row.get("verifiedAt", ""))):
        fail(f"{evidence_id}: verifiedAt must use YYYY-MM-DD")
    facts=row.get("facts", [])
    if not facts:
        fail(f"{evidence_id}: at least one summarized fact is required")
    for fact in facts:
        if not str(fact.get("topic", "")).strip() or not str(fact.get("summary", "")).strip():
            fail(f"{evidence_id}: each fact needs topic and summary")
        if fact.get("basis") not in {"worker_experience", "worker_experience_plus_public_record"}:
            fail(f"{evidence_id}: unsupported fact basis")
    for media in row.get("media", []):
        if media.get("type") not in {"photo", "video"}:
            fail(f"{evidence_id}: unsupported media type")
        if media.get("consent") is not True or media.get("privacyReviewed") is not True:
            fail(f"{evidence_id}: media requires consent=true and privacyReviewed=true")
        if media.get("metadataRemoved") is not True:
            fail(f"{evidence_id}: media requires metadataRemoved=true")
        if not str(media.get("url", "")).startswith("https://"):
            fail(f"{evidence_id}: media URL must be HTTPS")

print(f"WORKPLACE_WORKER_EVIDENCE_PASS records={len(data.get('records', []))} privacy_safe=true")
