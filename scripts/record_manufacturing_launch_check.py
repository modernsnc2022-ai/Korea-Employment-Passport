#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from datetime import date
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "recruitment" / "MANUFACTURING_LAUNCH_CHECK.json"
PRIMARY_INDEX = "https://kp2mi.go.id/gtog-korea/pengumuman"
HISTORICAL_WRONG_INDEX = "https://kp2mi.go.id/gtog-korea/info"
NO_NOTICE = "no_current_manufacturing_job_application_notice"
NOTICE_FOUND = "notice_found_review_required"
ALLOWED_RESULTS = {NO_NOTICE, NOTICE_FOUND}
LOCKED_HOLDS = ["job_docs"]


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
    full_inventory_url: str | None = None,
    confirm_full_inventory: bool = False,
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

    if confirm_full_inventory != bool(full_inventory_url):
        fail("a completed index review requires both --full-inventory-url and --confirm-full-inventory")
    if full_inventory_url:
        validate_official_url(full_inventory_url)
        target = urlparse(full_inventory_url)
        path = target.path.lower()
        if path.rstrip("/") != "/gtog-korea/pengumuman" or target.query or target.fragment:
            fail("full inventory URL must be the verified official KP2MI Pengumuman listing, not Preliminary Training or an invented index")

    record = json.loads(json.dumps(current))
    record["checkedAt"] = checked_at
    record["result"] = result
    record["primaryIndex"] = PRIMARY_INDEX
    record["heldQuestions"] = list(LOCKED_HOLDS)
    # A new daily manual check must never inherit an old index-coverage signoff.
    record["noticeIndexCoverage"] = {
        "status": (
            "verified_complete_general_manufacturing_index_review"
            if confirm_full_inventory else "correct_pengumuman_index_review_not_operator_confirmed"
        ),
        "checkedAt": checked_at,
        "previouslyAssumedIndex": HISTORICAL_WRONG_INDEX,
        "currentCategory": "Pengumuman",
        "currentListingUrl": PRIMARY_INDEX,
        "serverSideAjaxUrl": "https://kp2mi.go.id/gtog-data/korea/Pengumuman",
        "actualCategory": "Preliminary Training dan Info",
        "completeGeneralManufacturingInventory": bool(confirm_full_inventory),
        "officialManufacturingInventoryUrl": full_inventory_url,
        "operatorConfirmedCompleteReview": bool(confirm_full_inventory),
        "notes": (
            "Operator explicitly reviewed official General Manufacturing announcement listing and confirmed the complete cohort inventory."
            if confirm_full_inventory else
            "The right Pengumuman category is identified, but a release-day full 2026 Manufacturing notice review and manual signoff are still required."
        ),
    }
    # Keep the nested official-evidence timestamp in sync. A new release-day
    # audit must never look current merely because the top-level date changed.
    record["sameDayOfficialRecheck"] = {
        "checkedAt": checked_at,
        "status": (
            "completed_no_detailed_manufacturing_notice_found"
            if result == NO_NOTICE else "notice_found_review_required"
        ),
        "queryScope": "KP2MI G-to-G Korea official 2026 Manufacturing notice index",
        "repeatOnActualReleaseDay": True,
    }

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
    assert clean["noticeIndexCoverage"]["completeGeneralManufacturingInventory"] is False
    assert clean["noticeIndexCoverage"]["officialManufacturingInventoryUrl"] is None
    assert clean["sameDayOfficialRecheck"]["checkedAt"] == "2026-10-04"
    assert clean["sameDayOfficialRecheck"]["status"] == (
        "completed_no_detailed_manufacturing_notice_found"
    )

    found = updated_record(
        base,
        checked_at="2026-10-04",
        result=NOTICE_FOUND,
        notice_url="https://kp2mi.go.id/gtog-detail/korea/example-manufacturing-notice",
    )
    assert found["result"] == NOTICE_FOUND
    assert found["sameDayOfficialRecheck"]["status"] == "notice_found_review_required"
    assert found["sameDayOfficialRecheck"]["checkedAt"] == "2026-10-04"
    assert found["officialEvidence"][-1]["url"].startswith("https://kp2mi.go.id/")
    # Structural self-test never fetches or attests current content.
    example = PRIMARY_INDEX
    signed = updated_record(base, checked_at="2026-10-04", result=NO_NOTICE,
                            full_inventory_url=example, confirm_full_inventory=True)
    assert signed["noticeIndexCoverage"]["completeGeneralManufacturingInventory"] is True
    assert signed["noticeIndexCoverage"]["officialManufacturingInventoryUrl"] == example
    for bad_url in [HISTORICAL_WRONG_INDEX, "https://kp2mi.go.id/gtog-data/korea/Preliminary%20Training%20dan%20Info",
                    "https://kp2mi.go.id/gtog-detail/korea/single-notice",
                    "https://kp2mi.go.id/gtog-korea/verified-index-example"]:
        try:
            updated_record(base, checked_at="2026-10-04", result=NO_NOTICE,
                           full_inventory_url=bad_url, confirm_full_inventory=True)
        except ValueError:
            pass
        else:
            raise AssertionError("Incomplete/non-manufacturing listing was accepted")
    try:
        updated_record(base, checked_at="2026-10-04", result=NO_NOTICE,
                       full_inventory_url=example)
    except ValueError as exc:
        assert "both" in str(exc)
    else:
        raise AssertionError("Complete-index review was accepted without explicit confirmation")

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
    parser.add_argument("--full-inventory-url",
                        help="Exact authoritative KP2MI G-to-G Korea announcements-list URL, NOT /gtog-korea/info")
    parser.add_argument("--confirm-full-inventory", action="store_true",
                        help="Explicit human attestation after checking current General Manufacturing notices in full")
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
            full_inventory_url=args.full_inventory_url,
            confirm_full_inventory=args.confirm_full_inventory,
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
