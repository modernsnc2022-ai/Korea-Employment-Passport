#!/usr/bin/env python3
"""Require current-operational next-review sources to be monitored while keeping future designations separate."""

import json
import sys
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
failures = []


def load(rel):
    return json.loads((ROOT / rel).read_text(encoding="utf-8"))


def require(condition, message):
    if not condition:
        failures.append(message)


sources_doc = load("monitor/sources.json")
readiness = load("docs/data/country_readiness_dashboard_2026.json")
source_hashes = load("monitor/source_hashes.json")
review_status = load("docs/data/source_review_status.json")

sources = sources_doc.get("sources", [])
rows = readiness.get("rows", [])
ids = [row.get("id") for row in sources]
urls = [row.get("url") for row in sources]
source_ids = set(ids)
source_urls = set(urls)

require(len(ids) == len(set(ids)), "monitor/sources.json source ids must be unique")
require(len(urls) == len(set(urls)), "monitor/sources.json URLs must be unique")
require(review_status.get("configured") == len(sources), "source_review_status configured count must match monitor/sources.json")

expected_countries = {
    "ID","NP","VN","PH","TH","BD","LK","LA","UZ","MN","CN","KH","TL","PK","KG","MM","TJ","KZ"
}
actual_countries = {row.get("country") for row in rows}
require(actual_countries == expected_countries, "readiness dashboard must cover all 18 officially designated EPS sending countries")

review_urls = set()
for row in rows:
    country = row.get("country")
    next_review = row.get("nextReview") or {}
    review_type = next_review.get("type")
    official_sources = next_review.get("officialSources") or []
    require(bool(official_sources), f"{country} nextReview must include at least one official source")
    future_designation = review_type == "future_operational_setup"
    if future_designation:
        require(country == "KZ", "future_operational_setup is reserved for Kazakhstan in the 2026 snapshot")
        require(row.get("packState") == "future_designated", "Kazakhstan future review type requires future_designated packState")
        require(row.get("plannedIntroductionYear") == 2028, "Kazakhstan future review must preserve planned 2028 introduction")
    for url in official_sources:
        parsed = urlparse(url)
        require(parsed.scheme == "https" and bool(parsed.hostname), f"{country} nextReview source must be official HTTPS: {url}")
        if not future_designation:
            require(url in source_urls, f"{country} nextReview source is not monitored: {url}")
            review_urls.add(url)

missing_hash_ids = source_ids - set(source_hashes)
pending_ids = set(review_status.get("pendingBaselineSourceIds", []))
failure_ids = set(review_status.get("fetchFailureSourceIds", []))
review_required_ids = set(review_status.get("reviewRequiredSourceIds", []))

require(missing_hash_ids.issubset(pending_ids | failure_ids),
        "Every unbaselined monitored source must be pending baseline review or recorded as a fetch failure")
require(pending_ids.issubset(source_ids), "pending baseline ids must exist in monitor/sources.json")
require(failure_ids.issubset(source_ids), "fetch failure ids must exist in monitor/sources.json")
require(review_required_ids.issubset(source_ids), "review-required ids must exist in monitor/sources.json")

if pending_ids:
    require(review_status.get("state") == "review_required",
            "Pending source baselines require source_review_status.state=review_required")

# Myanmar gets one extra broad discovery source beyond its four hard promotion-gate sources.
mm_dossier = load("docs/data/mm_manufacturing_verification_2026.json")
supplemental_mm = set(mm_dossier.get("monitoring", {}).get("supplementalDiscoverySourceIds", []))
require("mm_mol_dol_index" in supplemental_mm, "Myanmar Department of Labour index must remain a supplemental discovery watch")
require(supplemental_mm.issubset(source_ids), "Myanmar supplemental discovery sources must be registered in monitor/sources.json")
supplemental_review = mm_dossier.get("promotionGate", {}).get("currentReview", {}).get("supplementalDiscoveryReview", {})
require(supplemental_review.get("sourceId") == "mm_mol_dol_index", "Myanmar supplemental discovery review must identify mm_mol_dol_index")
require(supplemental_review.get("qualifiesForPromotion") is False, "Myanmar broad Department of Labour index must never promote Manufacturing by itself")

if failures:
    print("NEXT_REVIEW_MONITOR_COVERAGE_FAIL")
    for failure in failures:
        print("- " + failure)
    sys.exit(1)

print(
    "NEXT_REVIEW_MONITOR_COVERAGE_PASS "
    f"countries={len(rows)} monitoredSources={len(sources)} "
    f"nextReviewUrls={len(review_urls)} pendingBaselines={len(pending_ids)}"
)
