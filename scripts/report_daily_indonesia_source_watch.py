#!/usr/bin/env python3
"""M19: archive same-day *read-only* official watch evidence; never approve facts.

Inputs are externally produced monitor and KP2MI title-scan JSON files. This
script does not fetch URLs, sign policies, touch hash baselines or open beta.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
SHA = re.compile(r"[0-9a-f]{64}\Z")
JAKARTA = ZoneInfo("Asia/Jakarta")
SHARED = {
    "minimum_wage", "labor_standards_wage_statement",
    "moel_wage_arrears_2026", "kdca_qcode_input", "moel_1350_contact",
}
HRD = {"mm_hrdk_schedule_index", "mm_hrdk_skills_candidates"}
OTHER = {
    "np_eps_notice_index", "vn_colab_eps_notices", "lk_slbfe_home",
    "kg_migrant_home", "mm_mol_dol_index",
}


def fail(message: str) -> None:
    raise ValueError("M19_DAILY_SOURCE_EVIDENCE_BLOCKED " + message)


def classify(source_id: str) -> str:
    if source_id in SHARED:
        return "korea_shared"
    if source_id in HRD:
        return "multi_country_eps_schedule"
    if source_id in OTHER:
        return "other_country"
    return "unclassified_requires_manual_scope_review"


def review(as_of: str, watch: dict, index: dict, manifest: dict,
           baseline: dict, watch_mtime: float) -> dict:
    try:
        date = datetime.strptime(as_of, "%Y-%m-%d").date()
        fetched_date = datetime.fromtimestamp(watch_mtime, tz=timezone.utc).astimezone(JAKARTA).date()
        index_date = datetime.fromisoformat(index["generatedUtc"].replace("Z", "+00:00")).astimezone(JAKARTA).date()
    except (ValueError, TypeError, KeyError, OverflowError) as exc:
        fail("invalid source/index observation date: " + str(exc)[:150])
    if date != fetched_date or date != index_date:
        fail("monitor and index must both be freshly observed on as-of date in Jakarta")
    sources = manifest.get("sources")
    if not isinstance(sources, list) or len(sources) != 84:
        fail("source manifest must contain exactly 84 URLs")
    source_by_id = {x["id"]: x["url"] for x in sources}
    if len(source_by_id) != 84 or not all(x.startswith("https://") for x in source_by_id.values()):
        fail("duplicate source ID or non-HTTPS official origin")
    if (watch.get("configured") != 84 or watch.get("checked") not in range(85)
        or watch.get("acceptedCurrent") is not False
        or watch.get("initialized") is not False
        or watch.get("reviewManifestAccepted") is not False
        or watch.get("partialAcceptance") is not False):
        fail("monitor scope incomplete or unsafe source-hash acceptance attempt")
    changes = watch.get("changed")
    failures = watch.get("failures")
    if not isinstance(changes, list) or not isinstance(failures, list):
        fail("monitor result missing change/failure arrays")
    if watch["checked"] + len(failures) != 84:
        fail("checked plus failures must equal configured sources")
    seen, reviews = set(), []
    for row in changes:
        sid = row.get("id")
        if sid not in source_by_id or sid in seen or row.get("url") != source_by_id[sid]:
            fail("unknown, duplicated or re-targeted changed official source")
        seen.add(sid)
        previous = baseline.get(sid)
        before, after = row.get("before"), row.get("after")
        if not isinstance(after, str) or not SHA.fullmatch(after):
            fail("invalid observed SHA")
        if previous is None:
            if before is not None or row.get("reason") != "new_unbaselined_source":
                fail("unreviewed baseline inconsistency")
        elif (before != previous.get("sha256")
              or not isinstance(before, str) or not SHA.fullmatch(before)
              or (before == after and source_by_id[sid] == previous.get("url"))):
            fail("changed SHA does not match the accepted baseline")
        reviews.append({
            "id": sid, "scope": classify(sid), "url": row["url"],
            "acceptedBaselineSha256": before, "observedSha256": after,
            "reason": row.get("reason"), "semanticReview": "pending",
        })
    failure_ids = []
    for item in failures:
        sid = item.get("id")
        if sid not in source_by_id or sid in seen or sid in failure_ids or item.get("url") != source_by_id[sid]:
            fail("invalid official fetch failure row")
        failure_ids.append(sid)
    if (index.get("targetYear") != 2026 or index.get("priorYearBoundaryReached") is not True
        or index.get("releaseAuthorized") is not False
        or index.get("operatorApproved") is not False
        or index.get("jobDocsVerified") is not False
        or index.get("listingUrl") != "https://kp2mi.go.id/gtog-korea/pengumuman"):
        fail("KP2MI index does not provide safe 2026 title-only evidence")
    items = index.get("all2026NoticeMetadata")
    if not isinstance(items, list) or len(items) != index.get("indexed2026Count"):
        fail("KP2MI title inventory metadata inconsistency")
    manufacturing = index.get("manufacturingNoticesForManualReview")
    candidates = index.get("possibleManufacturingJobApplicationTitles")
    if not isinstance(manufacturing, list) or not isinstance(candidates, list):
        fail("missing manufacturing / candidate title scope")
    if len(manufacturing) != index.get("manufacturingRelevantTitleCount"):
        fail("manufacturing headline count mismatch")
    ready = (watch["checked"] == 84 and not failures)
    return {
        "version": "1.0.0", "observedAtDate": as_of,
        "mode": "read_only_official_observation_not_human_signoff",
        "monitorTodayComplete": ready, "configured": 84,
        "checked": watch["checked"], "fetchFailures": len(failures),
        "failedSourceIds": sorted(failure_ids),
        "unacceptedBaselineDriftCount": len(reviews),
        "groupCounts": {
            k: sum(r["scope"] == k for r in reviews)
            for k in ("korea_shared", "multi_country_eps_schedule", "other_country",
                      "unclassified_requires_manual_scope_review")
        },
        "pendingReviews": sorted(reviews, key=lambda x: x["id"]),
        "officialIndex": index["listingUrl"],
        "indexed2026Count": len(items),
        "manufacturingHeadlineCount": len(manufacturing),
        "possibleFinalApplicationHeadlineCount": len(candidates),
        "kp2miTitleMetadataSha256": index["noticesSha256"],
        "indexCheckedAtUtc": index["generatedUtc"],
        "sourceBaselineModified": False, "sourceHashAutoAccepted": False,
        "humanSemanticReviewApproved": False, "manufacturingHumanSignoff": False,
        "jobDocsExactRule": "hold", "betaAccess": "hold",
        "readyForManualLaunchDecision": False, "authorizesRelease": False,
        "caution": "Title inventory does not replace full official article/PDF review; "
                   "fingerprint differences are since accepted baseline, not yesterday.",
    }


def self_test() -> None:
    import copy
    day = "2026-10-17"
    sources = [{"id": f"source_{i}", "url": f"https://official.example/{i}"} for i in range(84)]
    manifest = {"sources": sources}
    old = {"source_0": {"sha256": "a" * 64, "url": sources[0]["url"]}}
    monitor = {"configured": 84, "checked": 84, "changed": [
        {"id": "source_0", "url": sources[0]["url"], "before": "a" * 64,
         "after": "b" * 64, "reason": "content_changed"}
    ], "failures": [], "acceptedCurrent": False, "initialized": False,
    "reviewManifestAccepted": False, "partialAcceptance": False}
    idx = {"generatedUtc": "2026-10-17T01:00:00+00:00", "targetYear": 2026,
           "priorYearBoundaryReached": True, "releaseAuthorized": False,
           "operatorApproved": False, "jobDocsVerified": False,
           "listingUrl": "https://kp2mi.go.id/gtog-korea/pengumuman",
           "all2026NoticeMetadata": [{}], "indexed2026Count": 1,
           "manufacturingNoticesForManualReview": [], "manufacturingRelevantTitleCount": 0,
           "possibleManufacturingJobApplicationTitles": [], "noticesSha256": "c" * 64}
    mtime = datetime(2026, 10, 17, 1, tzinfo=timezone.utc).timestamp()
    valid = review(day, monitor, idx, manifest, old, mtime)
    assert valid["monitorTodayComplete"] is True
    assert valid["authorizesRelease"] is False and valid["jobDocsExactRule"] == "hold"
    for mutate in (
        lambda m, i: m.update(acceptedCurrent=True),
        lambda m, i: m["changed"][0].update(before="c" * 64),
        lambda m, i: m["changed"][0].update(url="https://wrong.example/"),
        lambda m, i: m.update(checked=83),
        lambda m, i: i.update(jobDocsVerified=True),
        lambda m, i: i.update(generatedUtc="2026-10-16T01:00:00+00:00"),
    ):
        m, i = copy.deepcopy(monitor), copy.deepcopy(idx)
        mutate(m, i)
        try:
            review(day, m, i, manifest, old, mtime)
        except ValueError:
            continue
        raise AssertionError("Unsafe candidate observation passed")
    try:
        review("2026-10-16", monitor, idx, manifest, old, mtime)
    except ValueError:
        pass
    else:
        raise AssertionError("Previous-day reuse was not blocked")
    print("M19_DAILY_SOURCE_OBSERVATION_SELF_TEST_PASS 7_fail_closed_cases")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--watch")
    parser.add_argument("--index")
    parser.add_argument("--as-of")
    parser.add_argument("--output")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return
    if not all([args.watch, args.index, args.as_of, args.output]):
        parser.error("--watch, --index, --as-of and --output are mandatory")
    watch_file, index_file, output = Path(args.watch), Path(args.index), Path(args.output)
    evidence_dir = (ROOT / "research" / "source_reviews").resolve()
    if output.suffix.lower() != ".json" or output.resolve().parent != evidence_dir:
        fail("output must be a JSON review artifact in research/source_reviews only")
    if output.exists():
        fail("append-only daily audit: refusing to overwrite existing evidence file")
    for path in (watch_file, index_file):
        if ROOT.resolve() == path.resolve() or ROOT.resolve() in path.resolve().parents:
            fail("raw observation inputs must remain outside the repository")
    out = review(args.as_of,
                 json.loads(watch_file.read_text(encoding="utf-8-sig")),
                 json.loads(index_file.read_text(encoding="utf-8-sig")),
                 json.loads((ROOT / "monitor/sources.json").read_text(encoding="utf-8-sig")),
                 json.loads((ROOT / "monitor/source_hashes.json").read_text(encoding="utf-8-sig")),
                 watch_file.stat().st_mtime)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("M19_DAILY_SOURCE_OBSERVATION_RECORDED", out["observedAtDate"],
          f"checked={out['checked']}/{out['configured']}",
          f"fetchFailures={out['fetchFailures']}",
          f"unacceptedDrifts={out['unacceptedBaselineDriftCount']}",
          f"kp2miManufacturing={out['manufacturingHeadlineCount']}",
          "NO_SIGNOFF_NO_RELEASE")


if __name__ == "__main__":
    main()
