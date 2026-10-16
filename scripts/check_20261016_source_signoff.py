#!/usr/bin/env python3
"""Fail-closed 2026-10-16 Indonesia source-scope SIGNOFF validator.

Read-only: observed source inventory is not a signature and never accepts SHA
baselines or authorizes source rules, deployment or beta OPEN.
"""
from __future__ import annotations

import argparse
import copy
from datetime import datetime
import hashlib
import json
from pathlib import Path
from zoneinfo import ZoneInfo

from check_20261016_source_triage_snapshot import EXPECTED_GROUPS, validate as validate_watch

ROOT = Path(__file__).resolve().parents[1]
ROUTE = "Indonesia > Korea > E-9 > General Manufacturing 2026"


def read(path: str) -> dict:
    return json.loads((ROOT / path).read_text(encoding="utf-8-sig"))


def require(ok: bool, message: str) -> None:
    if not ok:
        raise ValueError("ID_CURRENT_SOURCE_SIGNOFF_BLOCKED " + message)


def validate_signoff(watch: dict, manifest: dict, signed: dict, day: str) -> None:
    validate_watch(watch, manifest)
    require(watch.get("observedAtDate") == day, "official watch must be from actual release day")
    require(signed.get("route") == ROUTE, "signoff route mismatch")
    require(signed.get("status") == "approved_manual_indonesia_scope",
            "named manual source approval is missing")
    require(signed.get("betaAccess") == "hold"
            and signed.get("exactManufacturingJobDocumentsHeld") is True,
            "approval cannot release beta or final unknown job documents")
    require(signed.get("allChangedSourceAlertsRemainVisible") is True
            and signed.get("noOfficialHashAutopromotion") is True
            and signed.get("manualReviewNotImplicit") is True,
            "source hashes and manual review may not be silently promoted")
    for name, count in (("sourceWatchConfigured", 84), ("sourceWatchChecked", 84),
                        ("sourceWatchChanged", 12), ("sourceWatchFetchFailures", 0)):
        require(signed.get(name) == count, "signoff count mismatch: " + name)
    source_pairs = sorted((row["id"], row["url"]) for row in manifest.get("sources", []))
    map_sha = hashlib.sha256(json.dumps(
        source_pairs, separators=(",", ":"), ensure_ascii=False,
    ).encode("utf-8")).hexdigest()
    require(signed.get("monitoredSourceMapSha256") == map_sha,
            "monitored 84-source mapping differs from signoff")
    for field, expected in (
        ("contentReviewedSourceIds", EXPECTED_GROUPS["korea_shared"]),
        ("multiCountryPendingSourceIds", EXPECTED_GROUPS["multi_country_eps_schedule"]),
        ("otherCountryPendingSourceIds", EXPECTED_GROUPS["other_country"]),
    ):
        rows = signed.get(field)
        require(isinstance(rows, list) and len(rows) == len(expected)
                and set(rows) == expected, field + ": incomplete or relabeled alerts")
    reviewer = signed.get("reviewer")
    require(isinstance(reviewer, str) and len(reviewer.strip()) >= 4,
            "real responsible reviewer name required")
    raw = signed.get("approvedAt")
    try:
        timestamp = datetime.fromisoformat(str(raw).replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("ID_CURRENT_SOURCE_SIGNOFF_BLOCKED invalid approval timestamp") from exc
    require(timestamp.tzinfo is not None, "approval timestamp must include time zone")
    require(timestamp.astimezone(ZoneInfo("Asia/Jakarta")).date().isoformat() == day,
            "source signoff must be made on release day in Indonesia")
    require(signed.get("sourceSnapshotDate") == day
            and signed.get("sourceScopeDate") == day,
            "signed watch and scope dates must both match release day")


def self_test() -> None:
    watch = read("research/source_reviews/shared_source_watch_readonly_2026-10-16.json")
    manifest = read("monitor/sources.json")
    pending = read("recruitment/ID_BETA_SOURCE_SIGNOFF_20261016.json")
    require(pending["status"] == "pending_manual_source_signoff"
            and pending["reviewer"] is None
            and pending["approvedAt"] is None, "real signoff must remain pending")
    day = "2026-10-16"
    signed = copy.deepcopy(pending)
    signed.update(status="approved_manual_indonesia_scope",
                  reviewer="Synthetic Operator QA",
                  approvedAt="2026-10-16T13:00:00+07:00",
                  sourceSnapshotDate=day, sourceScopeDate=day)
    validate_signoff(watch, manifest, signed, day)
    bad_cases = [
        lambda w, m, s: s.update(status="pending_manual_source_signoff"),
        lambda w, m, s: s.update(reviewer=None),
        lambda w, m, s: s.update(approvedAt="2026-10-14T13:00:00+07:00"),
        lambda w, m, s: s.update(sourceSnapshotDate="2026-10-14"),
        lambda w, m, s: s["contentReviewedSourceIds"].remove("moel_wage_arrears_2026"),
        lambda w, m, s: s["multiCountryPendingSourceIds"].clear(),
        lambda w, m, s: s["otherCountryPendingSourceIds"].clear(),
        lambda w, m, s: s.update(noOfficialHashAutopromotion=False),
        lambda w, m, s: s.update(betaAccess="open"),
        lambda w, m, s: s.update(sourceWatchChecked=83),
        lambda w, m, s: w["records"][4].update(routeScope="other_country"),
        lambda w, m, s: w["records"][0].update(url="https://example.invalid/changed"),
        lambda w, m, s: m["sources"][0].update(url="https://example.invalid/changed"),
        lambda w, m, s: s.update(approvedAt="2026-10-16T00:30:00+09:00"),
    ]
    for num, mutation in enumerate(bad_cases, 1):
        w, m, s = copy.deepcopy(watch), copy.deepcopy(manifest), copy.deepcopy(signed)
        mutation(w, m, s)
        try:
            validate_signoff(w, m, s, day)
        except (ValueError, TypeError):
            continue
        raise AssertionError("unsafe signed source mutation passed #" + str(num))
    print("ID_CURRENT_SOURCE_SIGNOFF_SELF_TEST_PASS 14/14_fail_closed_mutations")
    print("REAL_SOURCE_SIGNOFF_REMAINS_PENDING")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--approved-date", default="2026-10-16")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return
    validate_signoff(
        read("research/source_reviews/shared_source_watch_readonly_2026-10-16.json"),
        read("monitor/sources.json"),
        read("recruitment/ID_BETA_SOURCE_SIGNOFF_20261016.json"),
        args.approved_date,
    )
    print("ID_CURRENT_SOURCE_SIGNOFF_PASS manual Indonesia-only; beta HOLD")


if __name__ == "__main__":
    main()
