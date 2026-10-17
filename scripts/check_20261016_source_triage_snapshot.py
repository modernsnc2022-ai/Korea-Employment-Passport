#!/usr/bin/env python3
"""Validate the 2026-10-16 read-only 84-source drift snapshot, NOT a release gate.

This checks source identity, URL, SHA, scope and HOLD integrity offline. A
valid snapshot never constitutes official semantic signoff or fingerprint acceptance.
"""
from __future__ import annotations

import argparse
import copy
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXPECTED_GROUPS = {
    "korea_shared": {
        "minimum_wage", "labor_standards_wage_statement", "moel_wage_arrears_2026",
        "kdca_qcode_input", "moel_1350_contact",
    },
    "multi_country_eps_schedule": {"mm_hrdk_schedule_index", "mm_hrdk_skills_candidates"},
    "other_country": {
        "np_eps_notice_index", "vn_colab_eps_notices", "lk_slbfe_home",
        "kg_migrant_home", "mm_mol_dol_index",
    },
}
GROUP_FIELDS = {
    "korea_shared": "candidateKoreaSharedIds",
    "multi_country_eps_schedule": "candidateMultiCountryScheduleIds",
    "other_country": "candidateOtherCountryIds",
}
SHA = re.compile(r"[0-9a-f]{64}\Z")


def require(condition: bool, reason: str) -> None:
    if not condition:
        raise ValueError("KEP_SOURCE_TRIAGE_SNAPSHOT_FAIL " + reason)


def validate(snapshot: dict, source_manifest: dict) -> None:
    sources = source_manifest.get("sources", [])
    source_urls = {source["id"]: source["url"] for source in sources}
    expected = set().union(*EXPECTED_GROUPS.values())
    require(len(sources) == len(source_urls) == 84,
            "source manifest is not exactly 84 unique IDs")
    require(snapshot.get("observedAtDate") == "2026-10-16",
            "snapshot is not the reviewed monitoring date")
    require(snapshot.get("configured") == snapshot.get("checked") == 84
            and snapshot.get("fetchFailures") == 0 and snapshot.get("changed") == 12,
            "read-only 84/84 zero-failure twelve-drift evidence changed")
    for field in ("sourceHashesAutomaticallyAccepted",
                  "manualIndonesiaSourceSignoff",
                  "manualManufacturingNoticeSignoff"):
        require(snapshot.get(field) is False, field + " must remain false")
    require(snapshot.get("doesNotAuthorizeLaunch") is True,
            "snapshot must not authorize beta release")
    for field in ("betaAccess", "directHttpsIntake",
                  "exactManufacturingJobDocuments"):
        require(snapshot.get(field) == "hold", field + " must stay on HOLD")
    records = snapshot.get("records")
    require(isinstance(records, list) and len(records) == 12,
            "twelve distinct drift records required")
    seen = set()
    for group, ids in EXPECTED_GROUPS.items():
        field = GROUP_FIELDS[group]
        declared = snapshot.get(field)
        require(isinstance(declared, list) and len(declared) == len(ids)
                and set(declared) == ids, field + " incorrectly classified")
    for row in records:
        require(isinstance(row, dict), "drift record malformed")
        name = row.get("id")
        require(isinstance(name, str) and name in expected and name not in seen,
                "drift ID unexpected, absent or duplicate")
        seen.add(name)
        require(row.get("url") == source_urls.get(name), name + " URL mismatch")
        group = next(group for group, ids in EXPECTED_GROUPS.items() if name in ids)
        require(row.get("routeScope") == group, name + " cross-country scope mismatch")
        require(row.get("reviewStatus") == "pending_semantic_review",
                name + " cannot be pre-approved by a snapshot")
        require(row.get("reason") == "content_changed",
                name + " is not the observed change reason")
        before, after = row.get("baselineSha256"), row.get("observedSha256")
        require(isinstance(before, str) and isinstance(after, str)
                and SHA.fullmatch(before) and SHA.fullmatch(after)
                and before != after, name + " invalid fingerprint evidence")
    require(seen == expected, "not all twelve original drift records preserved")


def self_test(snapshot: dict, manifest: dict) -> None:
    validate(snapshot, manifest)
    mutations = [
        lambda s: s["candidateOtherCountryIds"].append("mm_hrdk_schedule_index"),
        lambda s: s["candidateMultiCountryScheduleIds"].clear(),
        lambda s: s["records"][4].update(routeScope="other_country"),
        lambda s: s["records"][4].update(reviewStatus="approved"),
        lambda s: s["records"][0].update(observedSha256="malformed"),
        lambda s: s["records"][0].update(url="https://example.invalid/tampered"),
        lambda s: s.update(sourceHashesAutomaticallyAccepted=True),
        lambda s: s.update(betaAccess="open"),
        lambda s: s.update(checked=83),
        lambda s: s["records"].pop(),
    ]
    for i, mutation in enumerate(mutations, start=1):
        wrong = copy.deepcopy(snapshot)
        mutation(wrong)
        try:
            validate(wrong, manifest)
        except ValueError:
            pass
        else:
            raise AssertionError("unsafe snapshot mutation " + str(i) + " passed")
    print("KEP_20261016_SOURCE_SCOPE_SELF_TEST_PASS 10/10_negative_cases")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    snapshot = json.loads((ROOT / "research/source_reviews/"
        "shared_source_watch_readonly_2026-10-16.json").read_text(encoding="utf-8-sig"))
    manifest = json.loads((ROOT / "monitor/sources.json").read_text(encoding="utf-8-sig"))
    validate(snapshot, manifest)
    if args.self_test:
        self_test(snapshot, manifest)
    print("KEP_20261016_SOURCE_SCOPE_PASS korea_shared=5 multi_country=2 other_country=5 "
          "unaccepted=12 beta=HOLD")


if __name__ == "__main__":
    main()
