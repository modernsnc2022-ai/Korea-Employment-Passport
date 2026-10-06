#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RECRUITMENT_SOURCES = ROOT / "docs" / "data" / "beta_recruitment_sources_v1.json"
ALLOWED_SOURCE_CHANNELS = set(
    json.loads(RECRUITMENT_SOURCES.read_text(encoding="utf-8-sig")).get("codes", [])
)

FIELD_PATTERNS = {
    "source_channel": re.compile(r"^Recruitment source code:\s*(\S+)\s*$", re.M),
    "in_korea": re.compile(r"^Currently working in Korea with E-9:\s*(YES|NO)\s*$", re.M),
    "g2g_experience": re.compile(r"^Completed Indonesia G-to-G Korea / EPS process:\s*(YES|NO)\s*$", re.M),
    "feedback_agreement": re.compile(r"^Experience-validation participation agreement:\s*(YES|NO)\s*$", re.M),
}


def fail(message: str) -> None:
    raise ValueError(message)


def parse_worker_interest(text: str) -> dict[str, str]:
    if "KOREA EMPLOYMENT PASSPORT — E-9 WORKER VALIDATOR INTEREST" not in text:
        fail("not a current Korea Employment Passport worker-validator interest body")

    result: dict[str, str] = {}
    for field, pattern in FIELD_PATTERNS.items():
        match = pattern.search(text)
        if not match:
            fail(f"missing required field: {field}")
        result[field] = match.group(1).strip()

    if result["source_channel"] not in ALLOWED_SOURCE_CHANNELS:
        fail(f"unsupported source_channel: {result['source_channel']}")
    if result["in_korea"] != "YES":
        fail("current E-9 work in Korea was not confirmed")
    if result["g2g_experience"] != "YES":
        fail("Indonesia G-to-G Korea / EPS experience was not confirmed")
    if result["feedback_agreement"] != "YES":
        fail("experience-validation participation was not confirmed")

    return {
        "source_channel": result["source_channel"],
        "in_korea": "yes",
        "e9_experience": "confirmed",
        "interest_status": "eligible_for_manual_review",
    }


def self_test() -> None:
    body = """KOREA EMPLOYMENT PASSPORT — E-9 WORKER VALIDATOR INTEREST

Recruitment source code: ut_korea_pmi
Currently working in Korea with E-9: YES
Completed Indonesia G-to-G Korea / EPS process: YES
Experience-validation participation agreement: YES

I am registering my interest in the separate 20-person retrospective validation panel.
I understand that sending this interest does not activate worker-panel access yet.
"""
    parsed = parse_worker_interest(body)
    assert parsed == {
        "source_channel": "ut_korea_pmi",
        "in_korea": "yes",
        "e9_experience": "confirmed",
        "interest_status": "eligible_for_manual_review",
    }

    tampered = body.replace(
        "Recruitment source code: ut_korea_pmi",
        "Recruitment source code: worker@example.com",
    )
    try:
        parse_worker_interest(tampered)
    except ValueError as exc:
        assert "unsupported source_channel" in str(exc)
    else:
        raise AssertionError("arbitrary/private source channel was accepted")

    not_in_korea = body.replace(
        "Currently working in Korea with E-9: YES",
        "Currently working in Korea with E-9: NO",
    )
    try:
        parse_worker_interest(not_in_korea)
    except ValueError as exc:
        assert "current E-9 work in Korea was not confirmed" in str(exc)
    else:
        raise AssertionError("non-current E-9 worker was accepted")

    print("WORKER_INTEREST_PARSE_SELF_TEST_PASS")


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Parse a private KEP E-9 worker-validator interest body into "
            "non-identifying manual-review fields. The raw body is never written."
        )
    )
    parser.add_argument("--input", help="Private text file containing only the worker-interest email body")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    if args.self_test:
        self_test()
        return 0
    if not args.input:
        parser.error("--input is required")

    path = Path(args.input).expanduser()
    if not path.exists() or not path.is_file():
        raise SystemExit("WORKER_INTEREST_PARSE_BLOCKED input file does not exist")

    try:
        result = parse_worker_interest(path.read_text(encoding="utf-8-sig"))
    except ValueError as exc:
        raise SystemExit("WORKER_INTEREST_PARSE_BLOCKED " + str(exc)) from exc

    print("WORKER_INTEREST_PARSE_PASS")
    print("source_channel=" + result["source_channel"])
    print("in_korea=" + result["in_korea"])
    print("e9_experience=" + result["e9_experience"])
    print("interest_status=" + result["interest_status"])
    print("RAW_BODY_NOT_STORED=true")
    print("WORKER_SLOT_NOT_ASSIGNED=true")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
