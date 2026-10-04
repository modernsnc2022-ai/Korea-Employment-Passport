#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from datetime import date
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "recruitment" / "MANUFACTURING_LAUNCH_CHECK.json"
PRIMARY_INDEX = "https://kp2mi.go.id/gtog-korea/info"
NO_NOTICE = "no_current_manufacturing_job_application_notice"
NOTICE_FOUND = "notice_found_review_required"
ALLOWED_RESULTS = {NO_NOTICE, NOTICE_FOUND}
LOCKED_HOLDS = ["job_docs", "job_scan", "job_name", "job_edit", "job_submit"]


def fail(message: str) -> None:
    raise ValueError(message)


def validate_official_url(value: str) -> str:
    parsed = urlparse(value)
    host = (parsed.hostname or "").lower()
    if parsed.scheme != "https" or host not in {"kp2mi.go.id", "www.kp2mi.go.id"}:
        fail("notice-url must be an official HTTPS kp2mi.go.id URL")
    return value


def updated_record(
    current: dict,
    *,
    checked_at: str,
    result: str,
    notice_url: str | None = None,
) -> dict:
    try:
        date.fromisoformat(checked_at)
    except ValueError as exc:
        raise ValueError("checked-at must use YYYY-MM-DD") from exc
    if result not in ALLOWED_RESULTS:
        fail("unsupported result")

    if result == NOTICE_FOUND:
        if not notice_url:
            fail("notice-url is required when a new Manufacturing notice is found")
        validate_official_url(notice_url)
    elif notice_url:
        fail("notice-url is only valid with notice_found_review_required")

    record = json.loads(json.dumps(current))
    record["checkedAt"] = checked_at
    record["result"] = result
    record["primaryIndex"] = PRIMARY_INDEX
    record["heldQuestions"] = list(LOCKED_HOLDS)

    if result == NOTICE_FOUND:
        evidence = list(record.get("officialEvidence", []))
        if not any(item.get("url") == notice_url for item in evidence if isinstance(item, dict)):
            evidence.append({
                "url": notice_url,
                "interpretation": (
                    "New 2026 Manufacturing online job-application candidate notice found; "
                    "structured rule review is required before beta OPEN."
                ),
            })
        record["officialEvidence"] = evidence

    return record


def self_test() -> None:
    base = {
        "checkedAt": "2026-10-03",
        "result": NO_NOTICE,
        "primaryIndex": PRIMARY_INDEX,
        "heldQuestions": list(LOCKED_HOLDS),
        "officialEvidence": [],
    }
    clean = updated_record(
        base,
        checked_at="2026-10-04",
        result=NO_NOTICE,
    )
    assert clean["checkedAt"] == "2026-10-04"
    assert clean["result"] == NO_NOTICE
    assert clean["heldQuestions"] == LOCKED_HOLDS

    found = updated_record(
        base,
        checked_at="2026-10-04",
        result=NOTICE_FOUND,
        notice_url="https://kp2mi.go.id/gtog-detail/korea/example-manufacturing-notice",
    )
    assert found["result"] == NOTICE_FOUND
    assert found["officialEvidence"][-1]["url"].startswith("https://kp2mi.go.id/")

    try:
        updated_record(
            base,
            checked_at="2026-10-04",
            result=NOTICE_FOUND,
            notice_url="https://example.com/not-official",
        )
    except ValueError as exc:
        assert "official HTTPS" in str(exc)
    else:
        raise AssertionError("non-official notice URL was accepted")

    print("MANUFACTURING_LAUNCH_CHECK_RECORD_SELF_TEST_PASS")


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Record the manual same-day official KP2MI check for a 2026 Manufacturing "
            "online job-application notice. This tool records the review; it does not "
            "perform the web search itself."
        )
    )
    parser.add_argument("--checked-at")
    parser.add_argument("--result", choices=sorted(ALLOWED_RESULTS))
    parser.add_argument("--notice-url")
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    if args.self_test:
        self_test()
        return 0
    if not args.checked_at or not args.result:
        parser.error("--checked-at and --result are required")

    current = json.loads(PATH.read_text(encoding="utf-8-sig"))
    try:
        record = updated_record(
            current,
            checked_at=str(args.checked_at),
            result=str(args.result),
            notice_url=args.notice_url,
        )
    except ValueError as exc:
        raise SystemExit("MANUFACTURING_LAUNCH_CHECK_BLOCKED " + str(exc)) from exc

    mode = "WRITE" if args.write else "DRY_RUN"
    print(
        f"MANUFACTURING_LAUNCH_CHECK_{mode} "
        f"checked_at={record['checkedAt']} result={record['result']} "
        f"held_questions={len(record['heldQuestions'])}"
    )
    if record["result"] == NOTICE_FOUND:
        print("BETA_OPEN_BLOCKED new Manufacturing notice requires structured rule review")

    if not args.write:
        print("DRY_RUN_ONLY launch-check audit file was not changed")
        return 0

    PATH.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("MANUFACTURING_LAUNCH_CHECK_WRITTEN")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
