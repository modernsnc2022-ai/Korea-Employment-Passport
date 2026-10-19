#!/usr/bin/env python3
"""M20: add validated read-only monitoring evidence without erasing historic source status.

No official SHA baseline, signed source-review record, beta access state, or
release decision is modified. A dated observation remains monitoring evidence.
"""
from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path

from report_daily_indonesia_source_watch import validate_committed_snapshot

ROOT = Path(__file__).resolve().parents[1]
STATUS = ROOT / "docs/data/source_review_status.json"
EVIDENCE = ROOT / "research/source_reviews/indonesia_daily_readonly_2026-10-17.json"
MANIFEST = ROOT / "monitor/sources.json"
BASELINE = ROOT / "monitor/source_hashes.json"
DAY = "2026-10-17"
HISTORICAL_DAY = "2026-10-14"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def require(value: bool, reason: str) -> None:
    if not value:
        raise ValueError("M20_SOURCE_VISIBILITY_BLOCKED " + reason)


def make_display(original: dict, observation: dict,
                 manifest: dict, baseline: dict) -> dict:
    validate_committed_snapshot(observation, manifest, baseline, DAY)
    # These preexisting records describe an OCT14 observation and do NOT
    # authorize overwriting it with machine-only OCT17 observations.
    require(original.get("detectedAt") == HISTORICAL_DAY
            and original.get("checked") == 83 and original.get("configured") == 84,
            "historical source observation must retain actual date and 83/84")
    require(original.get("state") == "review_required"
            and original.get("autoPublishRules") is False
            and original.get("currentScan", {}).get("acceptedCurrent") is False
            and original.get("fetchFailureSourceIds") == ["np_eps_notice_index"],
            "existing historical source alert or its HOLD was changed")
    require(original.get("reviewRequiredSourceIds")
            and len(original["reviewRequiredSourceIds"]) == 8,
            "historical eight pending alerts were lost")
    paths = {s["id"]:s["url"] for s in manifest["sources"]}
    alerts = observation["pendingReviews"]
    source_ids = [s["id"] for s in alerts]
    source_urls = [paths[sid] for sid in source_ids]
    require(len(set(source_ids)) == len(source_ids) == 12,
            "expected twelve distinct pending baseline alerts")
    latest = {
        "schemaVersion": 1,
        "observedAtDate": DAY,
        "evidenceKind": "machine_observation_only_not_manual_signoff",
        "evidenceFile": "research/source_reviews/indonesia_daily_readonly_2026-10-17.json",
        "configured": observation["configured"],
        "checked": observation["checked"],
        "fetchFailures": observation["fetchFailures"],
        "fetchFailureSourceIds": [],
        "reviewRequiredSourceIds": source_ids,
        "reviewRequiredUrls": source_urls,
        "unacceptedBaselineDriftCount": observation["unacceptedBaselineDriftCount"],
        "groupCounts": copy.deepcopy(observation["groupCounts"]),
        "humanSemanticReviewApproved": False,
        "hashBaselineAutoAccepted": False,
        "exactManufacturingJobDocuments": "hold",
        "betaAccess": "hold",
        "authorizesRelease": False,
        "notice": (
            "This is a dated, read-only technical source fetch. "
            "The 12 observed SHA differences are versus the last approved baseline, "
            "not 12 new policy changes. A clean fetch is NOT a human source approval. "
            "Older 2026-10-14 failures and pending alerts remain in the historical record."
        ),
    }
    require(latest["checked"] == 84 and latest["fetchFailures"] == 0
            and sum(latest["groupCounts"].values()) == 12,
            "cannot claim complete current 84/84 evidence")
    output = copy.deepcopy(original)
    if "latestReadOnlyObservation" in output:
        require(output["latestReadOnlyObservation"] == latest,
                "refusing to overwrite a different retained source observation")
    else:
        output["latestReadOnlyObservation"] = latest
    return output


def self_test() -> None:
    status, evidence, manifest, baseline = (
        load(STATUS), load(EVIDENCE), load(MANIFEST), load(BASELINE)
    )
    result = make_display(status, evidence, manifest, baseline)
    assert result["checked"] == 83 and result["detectedAt"] == HISTORICAL_DAY
    assert result["fetchFailureSourceIds"] == ["np_eps_notice_index"]
    latest = result["latestReadOnlyObservation"]
    assert latest["checked"] == 84 and latest["fetchFailures"] == 0
    assert len(latest["reviewRequiredSourceIds"]) == 12
    assert latest["humanSemanticReviewApproved"] is False
    assert latest["authorizesRelease"] is False
    assert make_display(result, evidence, manifest, baseline) == result
    mutations = [
        lambda s, e: s.update(checked=84),
        lambda s, e: s.update(detectedAt=DAY),
        lambda s, e: s.update(state="clean"),
        lambda s, e: s.update(reviewRequiredSourceIds=[]),
        lambda s, e: e.update(observedAtDate=HISTORICAL_DAY),
        lambda s, e: e.update(humanSemanticReviewApproved=True),
        lambda s, e: e.update(authorizesRelease=True),
        lambda s, e: e["pendingReviews"][0].update(url="https://wrong.invalid"),
        lambda s, e: e.update(checked=83),
        lambda s, e: s.update(latestReadOnlyObservation={"checked":84}),
    ]
    for mutate in mutations:
        s, e = copy.deepcopy(status), copy.deepcopy(evidence)
        mutate(s, e)
        try:
            make_display(s, e, manifest, baseline)
        except ValueError:
            continue
        raise AssertionError("mutation wrongly accepted")
    print("M20_SOURCE_VISIBILITY_SELF_TEST_PASS 10_fail_closed_cases")


def main() -> None:
    cli = argparse.ArgumentParser()
    cli.add_argument("--self-test", action="store_true")
    cli.add_argument("--write", action="store_true")
    args = cli.parse_args()
    if args.self_test:
        self_test()
        return
    if not args.write:
        cli.error("use --write after read-only inspection or --self-test")
    before, evidence, manifest, baseline = (
        load(STATUS), load(EVIDENCE), load(MANIFEST), load(BASELINE)
    )
    result = make_display(before, evidence, manifest, baseline)
    if result == before:
        print("M20_SOURCE_VISIBILITY_UNCHANGED_ALREADY_PRESENT")
        return
    # Only additive latest observation; all historical key-value pairs stay exact.
    assert all(result[k] == v for k, v in before.items())
    STATUS.write_text(json.dumps(result, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    print("M20_SOURCE_VISIBILITY_WRITTEN original=2026-10-14:83/84 latest=2026-10-17:84/84 "
          "pending_drift=12 no_semantic_approval no_hash_acceptance beta_hold")


if __name__ == "__main__":
    main()
