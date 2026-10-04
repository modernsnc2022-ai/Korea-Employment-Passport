#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROGRAM = ROOT / "docs" / "data" / "beta_program_v1.json"
SOURCE = ROOT / "docs" / "data" / "source_review_status.json"


def fail(message: str) -> None:
    raise ValueError(message)


def parse_aware(value: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("approved-at must use timezone-aware ISO-8601 datetime") from exc
    if parsed.tzinfo is None:
        fail("approved-at must include timezone")
    return parsed


def prepare_open(program: dict, source: dict, approved_at: str) -> dict:
    panel = program.get("retrospectivePanel", {})
    if panel.get("status") != "hold":
        fail("worker panel can be opened only from HOLD")

    release = program.get("releaseDecision", {})
    if release.get("retrospectivePanel") != "pending_manual_approval":
        fail("worker-panel release decision is not pending manual approval")

    parse_aware(approved_at)

    if source.get("state") != "clean":
        fail(f"official source state must be clean, got {source.get('state')!r}")
    if source.get("configured") != source.get("checked"):
        fail("all configured official sources must be checked before worker-panel OPEN")
    if source.get("reviewRequiredUrls"):
        fail("official source reviewRequiredUrls must be empty before worker-panel OPEN")
    if source.get("fetchFailureUrls"):
        fail("official source fetchFailureUrls must be empty before worker-panel OPEN")

    updated = json.loads(json.dumps(program))
    updated.setdefault("retrospectivePanel", {})["status"] = "open"
    updated.setdefault("releaseDecision", {})["retrospectivePanel"] = "approved_manual"
    updated["releaseDecision"]["retrospectiveApprovedAt"] = approved_at
    return updated


def self_test() -> None:
    program = {
        "retrospectivePanel": {"status": "hold"},
        "releaseDecision": {
            "retrospectivePanel": "pending_manual_approval",
            "retrospectiveApprovedAt": None,
        },
    }
    source = {
        "state": "clean",
        "configured": 72,
        "checked": 72,
        "reviewRequiredUrls": [],
        "fetchFailureUrls": [],
    }
    approved = "2026-10-04T18:45:00+09:00"
    opened = prepare_open(program, source, approved)
    assert opened["retrospectivePanel"]["status"] == "open"
    assert opened["releaseDecision"]["retrospectivePanel"] == "approved_manual"
    assert opened["releaseDecision"]["retrospectiveApprovedAt"] == approved

    try:
        prepare_open(program, source, "2026-10-04T18:45:00")
    except ValueError as exc:
        assert "include timezone" in str(exc)
    else:
        raise AssertionError("worker panel opened without approval timezone")

    bad = dict(source)
    bad["state"] = "review_required"
    try:
        prepare_open(program, bad, approved)
    except ValueError as exc:
        assert "must be clean" in str(exc)
    else:
        raise AssertionError("worker panel opened with dirty source state")

    print("WORKER_PANEL_RELEASE_SELF_TEST_PASS")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Prepare the explicit E-9 worker-panel HOLD -> OPEN release-state change."
    )
    parser.add_argument("--approved-at")
    parser.add_argument("--confirm-open", action="store_true")
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    if args.self_test:
        self_test()
        return 0
    if not args.confirm_open:
        raise SystemExit("WORKER_PANEL_RELEASE_BLOCKED --confirm-open is required")
    if not args.approved_at:
        parser.error("--approved-at is required")

    program = json.loads(PROGRAM.read_text(encoding="utf-8-sig"))
    source = json.loads(SOURCE.read_text(encoding="utf-8-sig"))
    try:
        updated = prepare_open(program, source, str(args.approved_at))
    except ValueError as exc:
        raise SystemExit("WORKER_PANEL_RELEASE_BLOCKED " + str(exc)) from exc

    print(
        "WORKER_PANEL_RELEASE_DRY_RUN "
        f"status={updated['retrospectivePanel']['status']} "
        f"decision={updated['releaseDecision']['retrospectivePanel']} "
        f"approved_at={updated['releaseDecision']['retrospectiveApprovedAt']}"
    )

    if not args.write:
        print("DRY_RUN_ONLY no worker-panel release files were changed")
        return 0

    PROGRAM.write_text(
        json.dumps(updated, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print("WORKER_PANEL_RELEASE_WRITTEN retrospective_panel_status=open")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
