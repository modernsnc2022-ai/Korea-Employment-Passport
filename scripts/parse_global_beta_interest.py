#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
READINESS = ROOT / "docs" / "data" / "country_readiness_dashboard_2026.json"
SOURCES = ROOT / "docs" / "data" / "beta_recruitment_sources_v1.json"

READINESS_DATA = json.loads(READINESS.read_text(encoding="utf-8-sig"))
SUPPORTED_COUNTRIES = {
    row["country"]: row
    for row in READINESS_DATA.get("rows", [])
    if row.get("country") != "ID"
    and row.get("routeId")
    and row.get("packState") == "research_hold"
}
ALLOWED_SOURCES = set(json.loads(SOURCES.read_text(encoding="utf-8-sig")).get("codes", []))
ALLOWED_STAGES = {
    "preparation",
    "eps_topik",
    "skills",
    "final_selection",
    "job_application",
    "roster",
    "employer_selection",
    "slc",
    "visa_predeparture",
    "departure_ready",
    "in_korea",
}
ALLOWED_CYCLES = {"2026", "2025", "2024", "unknown"}

PATTERNS = {
    "country_code": re.compile(r"^Country code:\s*(\S+)\s*$", re.M),
    "route_id": re.compile(r"^Country Pack route ID:\s*(\S+)\s*$", re.M),
    "stage_category": re.compile(r"^Current stage category:\s*(\S+)\s*$", re.M),
    "route_cycle": re.compile(r"^EPS process cycle:\s*(\S+)\s*$", re.M),
    "source_channel": re.compile(r"^Recruitment source code:\s*(\S+)\s*$", re.M),
    "official_process": re.compile(r"^Official G-to-G / EPS E-9 process:\s*(YES|NO)\s*$", re.M),
    "feedback_agreement": re.compile(r"^Feedback participation agreement:\s*(YES|NO)\s*$", re.M),
}

def parse_interest(text: str) -> dict[str, str]:
    if "KOREA EMPLOYMENT PASSPORT — GLOBAL TESTER INTEREST" not in text:
        raise ValueError("not a current KEP global tester-interest body")

    result = {}
    for field, pattern in PATTERNS.items():
        match = pattern.search(text)
        if not match:
            raise ValueError(f"missing required field: {field}")
        result[field] = match.group(1).strip()

    country = result["country_code"]
    if country not in SUPPORTED_COUNTRIES:
        raise ValueError(f"unsupported country_code: {country}")
    expected_route = SUPPORTED_COUNTRIES[country]["routeId"]
    if result["route_id"] != expected_route:
        raise ValueError(f"country/route mismatch: {country} != {result['route_id']}")
    if result["stage_category"] not in ALLOWED_STAGES:
        raise ValueError(f"unsupported stage_category: {result['stage_category']}")
    if result["route_cycle"] not in ALLOWED_CYCLES:
        raise ValueError(f"unsupported route_cycle: {result['route_cycle']}")
    if result["source_channel"] not in ALLOWED_SOURCES:
        raise ValueError(f"unsupported source_channel: {result['source_channel']}")
    if result["official_process"] != "YES":
        raise ValueError("official process participation was not confirmed")
    if result["feedback_agreement"] != "YES":
        raise ValueError("feedback participation was not confirmed")

    return {
        "country_code": country,
        "route_id": expected_route,
        "stage_category": result["stage_category"],
        "route_cycle": result["route_cycle"],
        "source_channel": result["source_channel"],
    }

def self_test() -> None:
    sample = """KOREA EMPLOYMENT PASSPORT — GLOBAL TESTER INTEREST

Country code: KH
Country name: Cambodia
Country Pack route ID: kh-e9-manufacturing-2026
Current stage category: roster
Current stage description: Job seeker roster / waiting for employer selection
EPS process cycle: 2026
Recruitment source code: global_beta_website
Official G-to-G / EPS E-9 process: YES
Feedback participation agreement: YES
"""
    parsed = parse_interest(sample)
    assert parsed["country_code"] == "KH"
    assert parsed["route_id"] == "kh-e9-manufacturing-2026"
    assert parsed["stage_category"] == "roster"
    print("GLOBAL_BETA_INTEREST_PARSE_SELF_TEST_PASS")

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()

    if args.self_test:
        self_test()
        return 0
    if not args.input:
        ap.error("--input is required")

    path = Path(args.input).expanduser()
    if not path.exists() or not path.is_file():
        raise SystemExit("GLOBAL_BETA_INTEREST_PARSE_BLOCKED input file does not exist")
    try:
        result = parse_interest(path.read_text(encoding="utf-8-sig"))
    except ValueError as exc:
        raise SystemExit("GLOBAL_BETA_INTEREST_PARSE_BLOCKED " + str(exc)) from exc

    print("GLOBAL_BETA_INTEREST_PARSE_PASS")
    for key in ("country_code", "route_id", "stage_category", "route_cycle", "source_channel"):
        print(key + "=" + result[key])
    print("RAW_BODY_NOT_STORED=true")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
