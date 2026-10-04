#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROGRAM = ROOT / "docs" / "data" / "beta_program_v1.json"
SOURCE = ROOT / "docs" / "data" / "source_review_status.json"
MANUFACTURING_CHECK = ROOT / "recruitment" / "MANUFACTURING_LAUNCH_CHECK.json"
OUTREACH = ROOT / "recruitment" / "OUTREACH_ID.md"


def fail(message: str) -> None:
    raise ValueError(message)


def prepare_open(program: dict, source: dict, manufacturing_check: dict, approved_at: str) -> dict:
    if program.get("status") != "hold":
        fail("public beta can be opened only from HOLD")
    release = program.get("releaseDecision", {})
    if release.get("publicBeta") != "pending_manual_approval":
        fail("release decision is not pending manual approval")
    try:
        date.fromisoformat(approved_at)
    except ValueError as exc:
        raise ValueError("approved-at must use YYYY-MM-DD") from exc

    if source.get("state") != "clean":
        fail(f"official source state must be clean, got {source.get('state')!r}")
    if source.get("configured") != source.get("checked"):
        fail("all configured official sources must be checked before OPEN")
    if source.get("reviewRequiredUrls"):
        fail("official source reviewRequiredUrls must be empty before OPEN")
    if source.get("fetchFailureUrls"):
        fail("official source fetchFailureUrls must be empty before OPEN")

    if manufacturing_check.get("checkedAt") != approved_at:
        fail("Manufacturing launch check must be recorded on the same date as OPEN approval")
    if manufacturing_check.get("result") != "no_current_manufacturing_job_application_notice":
        fail(
            "Manufacturing launch check found/requires review of a notice; "
            "do not OPEN until route rules and launch checks are updated"
        )
    if manufacturing_check.get("heldQuestions") != [
        "job_docs", "job_scan", "job_name", "job_edit", "job_submit"
    ]:
        fail("Manufacturing launch check must preserve the locked five HOLD questions")

    updated = json.loads(json.dumps(program))
    updated["status"] = "open"
    updated.setdefault("releaseDecision", {})["publicBeta"] = "approved_manual"
    updated["releaseDecision"]["approvedAt"] = approved_at
    return updated


def outreach_open_text(text: str) -> str:
    if "Recruitment status: **HOLD" not in text:
        fail("OUTREACH_ID.md does not contain the expected HOLD status marker")
    return text.replace(
        "Recruitment status: **HOLD",
        "Recruitment status: **OPEN",
        1,
    )


def self_test() -> None:
    program = {
        "status": "hold",
        "releaseDecision": {
            "publicBeta": "pending_manual_approval",
            "approvedAt": None,
        },
    }
    source = {
        "state": "clean",
        "configured": 72,
        "checked": 72,
        "reviewRequiredUrls": [],
        "fetchFailureUrls": [],
    }
    manufacturing_check = {
        "checkedAt": "2026-10-04",
        "result": "no_current_manufacturing_job_application_notice",
        "heldQuestions": ["job_docs", "job_scan", "job_name", "job_edit", "job_submit"],
    }
    opened = prepare_open(program, source, manufacturing_check, "2026-10-04")
    assert opened["status"] == "open"
    assert opened["releaseDecision"]["publicBeta"] == "approved_manual"
    assert opened["releaseDecision"]["approvedAt"] == "2026-10-04"

    bad_source = dict(source)
    bad_source["state"] = "review_required"
    try:
        prepare_open(program, bad_source, manufacturing_check, "2026-10-04")
    except ValueError as exc:
        assert "must be clean" in str(exc)
    else:
        raise AssertionError("OPEN was allowed with non-clean official-source state")

    stale_check = dict(manufacturing_check)
    stale_check["checkedAt"] = "2026-10-03"
    try:
        prepare_open(program, source, stale_check, "2026-10-04")
    except ValueError as exc:
        assert "same date" in str(exc)
    else:
        raise AssertionError("OPEN was allowed with a stale Manufacturing launch check")

    found_check = dict(manufacturing_check)
    found_check["result"] = "notice_found_review_required"
    try:
        prepare_open(program, source, found_check, "2026-10-04")
    except ValueError as exc:
        assert "requires review" in str(exc)
    else:
        raise AssertionError("OPEN was allowed after a Manufacturing notice was found")

    changed = outreach_open_text("Recruitment status: **HOLD — do not publish**")
    assert "Recruitment status: **OPEN" in changed
    print("BETA_RELEASE_STATE_SELF_TEST_PASS")


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Prepare the explicit public-beta HOLD -> OPEN release-state change. "
            "This does not bypass same-HEAD CI or the required manual decision."
        )
    )
    parser.add_argument("--approved-at")
    parser.add_argument(
        "--confirm-open",
        action="store_true",
        help="Required explicit operator confirmation for the OPEN transition.",
    )
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    if args.self_test:
        self_test()
        return 0

    if not args.confirm_open:
        raise SystemExit("BETA_RELEASE_BLOCKED --confirm-open is required")
    if not args.approved_at:
        parser.error("--approved-at is required")

    program = json.loads(PROGRAM.read_text(encoding="utf-8-sig"))
    source = json.loads(SOURCE.read_text(encoding="utf-8-sig"))
    manufacturing_check = json.loads(MANUFACTURING_CHECK.read_text(encoding="utf-8-sig"))
    outreach = OUTREACH.read_text(encoding="utf-8")

    try:
        updated_program = prepare_open(
            program, source, manufacturing_check, str(args.approved_at)
        )
        updated_outreach = outreach_open_text(outreach)
    except ValueError as exc:
        raise SystemExit("BETA_RELEASE_BLOCKED " + str(exc)) from exc

    print(
        "BETA_RELEASE_DRY_RUN "
        f"status={updated_program['status']} "
        f"decision={updated_program['releaseDecision']['publicBeta']} "
        f"approved_at={updated_program['releaseDecision']['approvedAt']}"
    )
    print("MANUAL_GATE_REMAINS same-day Manufacturing 2026 notice re-check and same-HEAD CI review")

    if not args.write:
        print("DRY_RUN_ONLY no release files were changed")
        return 0

    PROGRAM.write_text(
        json.dumps(updated_program, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    OUTREACH.write_text(updated_outreach, encoding="utf-8")
    print("BETA_RELEASE_WRITTEN public_beta_status=open outreach_status=OPEN")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
