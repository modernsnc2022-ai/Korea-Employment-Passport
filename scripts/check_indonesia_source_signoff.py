#!/usr/bin/env python3
"""Explicit Indonesia-only signoff guard for changed official-source watches.

Never mutates the shared 84-source monitor, applicant data, or beta access.
A successful signoff can only satisfy the country-scope source subgate;
a current Manufacturing index, same-HEAD deployment, and manual OPEN remain separate.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
from datetime import datetime
from pathlib import Path

from check_indonesia_release_source_scope import CRITICAL, OTHER_COUNTRY, validate as validate_scope

ROOT = Path(__file__).resolve().parents[1]
ROUTE = "Indonesia > Korea > E-9 > General Manufacturing 2026"


def data(path: str) -> dict:
    return json.loads((ROOT / path).read_text(encoding="utf-8-sig"))


def require(ok: bool, reason: str) -> None:
    if not ok:
        raise ValueError("ID_SOURCE_RELEASE_BLOCKED " + reason)


def validate_scoped_signoff(
    source: dict, manifest: dict, scope: dict, signed: dict, approved_date: str,
) -> None:
    # The immutable triage shows all eight global alerts and rejects unknown
    # or relabeled warnings, even when the Indonesia signoff later succeeds.
    n_shared, n_foreign = validate_scope(source, manifest, scope)
    require((n_shared, n_foreign) == (3, 5),
            "expected three reviewed Korea-shared and five pending other-country sources")
    require(source.get("state") == "review_required",
            "country-scoped signoff cannot invent a clean global monitor")
    require(source.get("autoPublishRules") is False and not source.get("fetchFailureUrls"),
            "source publishing and fetch failures are not permitted")
    source_pairs = sorted((row.get("id"), row.get("url")) for row in manifest.get("sources", []))
    official_map_sha = hashlib.sha256(
        json.dumps(source_pairs, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    ).hexdigest()
    require(signed.get("monitoredSourceMapSha256") == official_map_sha,
            "all 84 monitored official source IDs and URLs must match signed inventory")
    require(signed.get("route") == ROUTE, "the signoff is not for Indonesia 2026 Manufacturing")
    require(signed.get("status") == "approved_manual_indonesia_scope",
            "the Indonesia source signoff has not been manually approved")
    require(isinstance(signed.get("reviewer"), str) and len(signed["reviewer"].strip()) >= 4,
            "named responsible operator is required")
    iso = signed.get("approvedAt")
    try:
        timestamp = datetime.fromisoformat(str(iso).replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("ID_SOURCE_RELEASE_BLOCKED signoff timestamp is invalid") from exc
    require(timestamp.tzinfo is not None, "signoff requires timezone-aware approvedAt")
    require(timestamp.date().isoformat() == approved_date,
            "signoff must be dated the actual Indonesia beta OPEN day")
    require(source.get("detectedAt") == approved_date,
            "the official global source watcher must have run again on OPEN day")
    require(scope.get("checkedAt") == approved_date,
            "Indonesia source-scope review must be refreshed on OPEN day")
    require(signed.get("sourceSnapshotDate") == approved_date
            and signed.get("sourceScopeDate") == approved_date,
            "the signed source review must match the current day's monitor and scope")
    require(set(signed.get("contentReviewedSourceIds") or []) == CRITICAL
            and len(signed.get("contentReviewedSourceIds") or []) == len(CRITICAL),
            "all three Korea-shared sources must be checked by ID")
    require(set(signed.get("otherCountryPendingSourceIds") or []) == OTHER_COUNTRY
            and len(signed.get("otherCountryPendingSourceIds") or []) == len(OTHER_COUNTRY),
            "all five unrelated-country source alerts must remain visible and pending")
    require(signed.get("allChangedSourceAlertsRemainVisible") is True,
            "source signoff cannot hide any pending foreign-country alert")
    require(signed.get("noOfficialHashAutopromotion") is True,
            "source signoff cannot auto-promote changed source hashes")


def self_test() -> None:
    source = data("docs/data/source_review_status.json")
    manifest = data("monitor/sources.json")
    scope = data("recruitment/ID_RELEASE_SOURCE_SCOPE_20261014.json")
    pending = data("recruitment/ID_BETA_SOURCE_SIGNOFF.json")
    assert pending["status"] == "pending_manual_source_signoff"
    day = scope["checkedAt"]
    clean_copy = copy.deepcopy(source)
    clean_copy["detectedAt"] = day
    signed = copy.deepcopy(pending)
    signed.update({
        "status": "approved_manual_indonesia_scope",
        "reviewer": "Authorized release operator",
        "approvedAt": day + "T17:30:00+09:00",
        "sourceSnapshotDate": day,
        "sourceScopeDate": day,
    })
    validate_scoped_signoff(clean_copy, manifest, scope, signed, day)
    for mutant in [
        lambda a,b,c,d: d.update(status="pending_manual_source_signoff"),
        lambda a,b,c,d: d.update(approvedAt="2026-10-13T17:30:00+09:00"),
        lambda a,b,c,d: a.update(detectedAt="2026-10-13"),
        lambda a,b,c,d: d.update(contentReviewedSourceIds=["kdca_qcode_input"]),
        lambda a,b,c,d: d.update(otherCountryPendingSourceIds=[]),
        lambda a,b,c,d: b["sources"][0].update(url="https://evil.invalid"),
        lambda a,b,c,d: a["reviewRequiredSourceIds"].append("new_unknown_alert"),
        lambda a,b,c,d: a.update(autoPublishRules=True),
        lambda a,b,c,d: d.update(reviewer=None),
    ]:
        a,b,c,d = (copy.deepcopy(x) for x in (clean_copy,manifest,scope,signed))
        mutant(a,b,c,d)
        try:
            validate_scoped_signoff(a,b,c,d,day)
        except (ValueError, TypeError):
            pass
        else:
            raise AssertionError("unsafe Indonesia beta source signoff mutation passed")
    print("ID_BETA_SOURCE_SIGNOFF_SELF_TEST_PASS 9 forbidden mutations")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--approved-date", help="actual local Indonesia beta release-day YYYY-MM-DD")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return
    if not args.approved_date:
        parser.error("--approved-date required; read-only, never updates source records")
    validate_scoped_signoff(
        data("docs/data/source_review_status.json"),
        data("monitor/sources.json"),
        data("recruitment/ID_RELEASE_SOURCE_SCOPE_20261014.json"),
        data("recruitment/ID_BETA_SOURCE_SIGNOFF.json"),
        args.approved_date,
    )
    print("ID_BETA_SOURCE_SIGNOFF_PASS scoped Indonesia ONLY; other-country alerts still pending")
    print("MANUFACTURING_NOTICE_AND_DEPLOYED_SHA_AND_MANUAL_OPEN_GATES_STILL_REQUIRED")


if __name__ == "__main__":
    main()
