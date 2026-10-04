#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ROUTE = ROOT / "docs" / "data" / "id_e9_manufacturing_2026.json"
RECRUITMENT_SOURCES = ROOT / "docs" / "data" / "beta_recruitment_sources_v1.json"
ROUTE_DATA = json.loads(ROUTE.read_text(encoding="utf-8-sig"))
ROUTE_CYCLE = int(ROUTE_DATA.get("cycle", 0))
SUPPORTED_STAGES = {row["id"] for row in ROUTE_DATA.get("stages", [])}
SUPPORTED_ROUTE_CYCLES = {
    str(year) for year in range(max(2004, ROUTE_CYCLE - 2), ROUTE_CYCLE + 1)
} | {"unknown"}
ALLOWED_SOURCE_CHANNELS = set(
    json.loads(RECRUITMENT_SOURCES.read_text(encoding="utf-8-sig")).get("codes", [])
)

FIELD_PATTERNS = {
    "current_stage": re.compile(r"^Current route stage ID:\s*(\S+)\s*$", re.M),
    "route_cycle": re.compile(r"^EPS process cycle:\s*(\S+)\s*$", re.M),
    "source_channel": re.compile(r"^Recruitment source code:\s*(\S+)\s*$", re.M),
    "official_process": re.compile(r"^Official G-to-G / EPS E-9 process:\s*(YES|NO)\s*$", re.M),
    "feedback_agreement": re.compile(r"^Feedback participation agreement:\s*(YES|NO)\s*$", re.M),
}


def fail(message: str) -> None:
    raise ValueError(message)


def parse_interest(text: str) -> dict[str, str]:
    if "KOREA EMPLOYMENT PASSPORT — TESTER INTEREST" not in text:
        fail("not a current Korea Employment Passport tester-interest body")

    result: dict[str, str] = {}
    for field, pattern in FIELD_PATTERNS.items():
        match = pattern.search(text)
        if not match:
            fail(f"missing required field: {field}")
        result[field] = match.group(1).strip()

    if result["current_stage"] not in SUPPORTED_STAGES:
        fail(f"unsupported current_stage: {result['current_stage']}")
    if result["route_cycle"] not in SUPPORTED_ROUTE_CYCLES:
        fail(f"unsupported route_cycle: {result['route_cycle']}")
    if result["source_channel"] not in ALLOWED_SOURCE_CHANNELS:
        fail(f"unsupported source_channel: {result['source_channel']}")
    if result["official_process"] != "YES":
        fail("official G-to-G / EPS E-9 participation was not confirmed")
    if result["feedback_agreement"] != "YES":
        fail("feedback participation was not confirmed")

    return {
        "current_stage": result["current_stage"],
        "route_cycle": result["route_cycle"],
        "source_channel": result["source_channel"],
    }


def self_test() -> None:
    body = """KOREA EMPLOYMENT PASSPORT — TESTER INTEREST

Current route stage ID: roster
Current stage title: Daftar pencari kerja
EPS process cycle: 2026
Recruitment source code: epstopik_indonesia
Official G-to-G / EPS E-9 process: YES
Feedback participation agreement: YES

I am registering my interest as a beta tester.
"""
    parsed = parse_interest(body)
    assert parsed == {
        "current_stage": "roster",
        "route_cycle": "2026",
        "source_channel": "epstopik_indonesia",
    }

    tampered = body.replace(
        "Recruitment source code: epstopik_indonesia",
        "Recruitment source code: person@example.com",
    )
    try:
        parse_interest(tampered)
    except ValueError as exc:
        assert "unsupported source_channel" in str(exc)
    else:
        raise AssertionError("arbitrary/private source channel was accepted")

    incomplete = body.replace("Feedback participation agreement: YES", "Feedback participation agreement: NO")
    try:
        parse_interest(incomplete)
    except ValueError as exc:
        assert "feedback participation was not confirmed" in str(exc)
    else:
        raise AssertionError("interest without feedback agreement was accepted")

    print("BETA_INTEREST_PARSE_SELF_TEST_PASS")


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Parse a private Korea Employment Passport tester-interest body into "
            "non-identifying approval fields. The raw body is never written by this script."
        )
    )
    parser.add_argument("--input", help="Private text file containing only the tester-interest email body")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    if args.self_test:
        self_test()
        return 0
    if not args.input:
        parser.error("--input is required")

    path = Path(args.input).expanduser()
    if not path.exists() or not path.is_file():
        raise SystemExit("BETA_INTEREST_PARSE_BLOCKED input file does not exist")

    try:
        result = parse_interest(path.read_text(encoding="utf-8-sig"))
    except ValueError as exc:
        raise SystemExit("BETA_INTEREST_PARSE_BLOCKED " + str(exc)) from exc

    print("BETA_INTEREST_PARSE_PASS")
    print("current_stage=" + result["current_stage"])
    print("route_cycle=" + result["route_cycle"])
    print("source_channel=" + result["source_channel"])
    print("RAW_BODY_NOT_STORED=true")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
