#!/usr/bin/env python3
"""Fail closed unless Myanmar has reviewed, official 2026 Manufacturing evidence."""

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


dossier = load("docs/data/mm_manufacturing_verification_2026.json")
registry = load("docs/data/country_packs_v1.json")
coverage = load("docs/data/country_coverage_matrix_2026.json")
readiness = load("docs/data/country_readiness_dashboard_2026.json")
sources = load("monitor/sources.json")

gate = dossier.get("promotionGate", {})
monitoring = dossier.get("monitoring", {})
route = next((row for row in registry.get("routes", []) if row.get("country") == "MM"), None)
coverage_row = next((row for row in coverage.get("countries", []) if row.get("country") == "MM"), {})
readiness_row = next((row for row in readiness.get("rows", []) if row.get("country") == "MM"), {})
source_by_id = {row.get("id"): row for row in sources.get("sources", [])}

require(dossier.get("status") == "pending_manufacturing_verification", "Myanmar dossier must remain pending until promotion gate passes")
require(gate.get("status") in {"blocked", "passed"}, "Myanmar promotion gate must have an explicit blocked/passed status")
require(isinstance(gate.get("promotionAllowed"), bool), "Myanmar promotionAllowed must be explicit boolean")
require(isinstance(gate.get("currentManufacturingArtifactPresent"), bool), "Myanmar current Manufacturing artifact presence must be explicit")
require(len(gate.get("requiredAll", [])) >= 4, "Myanmar promotion gate must preserve all required evidence dimensions")
require(len(gate.get("forbiddenAsPromotionProof", [])) >= 5, "Myanmar promotion gate must preserve forbidden-inference rules")

required_ids = set(monitoring.get("requiredSourceIds", []))
expected_ids = {
    "mm_mol_eps_opportunity",
    "mm_hrdk_schedule_index",
    "mm_hrdk_skills_candidates",
    "mm_hrdk_final_results",
}
require(required_ids == expected_ids, "Myanmar monitor source IDs must match the four reviewed official watch targets")
require(expected_ids.issubset(source_by_id), "All Myanmar watch targets must be registered in monitor/sources.json")

expected_hosts = {
    "mm_mol_eps_opportunity": "www.mol.gov.mm",
    "mm_hrdk_schedule_index": "epstopik.hrdkorea.or.kr",
    "mm_hrdk_skills_candidates": "epstopik.hrdkorea.or.kr",
    "mm_hrdk_final_results": "epstopik.hrdkorea.or.kr",
}
for source_id, host in expected_hosts.items():
    row = source_by_id.get(source_id, {})
    parsed = urlparse(row.get("url", ""))
    require(parsed.scheme == "https" and parsed.hostname == host, f"{source_id} must remain on reviewed official HTTPS host {host}")

review = gate.get("currentReview", {})
qualifying = review.get("qualifyingArtifacts", [])
require(set(review.get("observedCurrentOfficialSectors", [])) == {"Agriculture·Livestock", "Construction", "Forestry"},
        "Myanmar current observed official sectors must remain the three verified non-Manufacturing sectors")
require(all(item.get("promotable") is False for item in review.get("historicalManufacturingArtifacts", [])),
        "Historical Myanmar Manufacturing artifacts must stay non-promotable")

allowed_hosts = {"epstopik.hrdkorea.or.kr", "mol.gov.mm", "www.mol.gov.mm"}
accepted_types = {"recruitment", "registration", "schedule", "skills_candidate", "result", "final_result"}

def artifact_qualifies(item):
    host = (urlparse(item.get("sourceUrl", "")).hostname or "").lower()
    return (
        item.get("reviewed") is True
        and item.get("cycle") == 2026
        and str(item.get("sector", "")).strip().lower() == "manufacturing"
        and item.get("artifactType") in accepted_types
        and host in allowed_hosts
    )

qualified = [item for item in qualifying if artifact_qualifies(item)]
if gate.get("promotionAllowed"):
    require(gate.get("status") == "passed", "promotionAllowed requires gate status passed")
    require(gate.get("currentManufacturingArtifactPresent") is True, "promotionAllowed requires a current Manufacturing artifact")
    require(bool(qualified), "promotionAllowed requires at least one reviewed qualifying official 2026 Manufacturing artifact")
    require(route is not None, "A passed Myanmar promotion gate requires a registered Country Pack route")
    require(coverage_row.get("status") == "country_pack_registered", "A passed Myanmar gate requires registered coverage state")
    require(readiness_row.get("routeId"), "A passed Myanmar gate requires a readiness routeId")
else:
    require(gate.get("status") == "blocked", "promotion disallowed requires gate status blocked")
    require(gate.get("currentManufacturingArtifactPresent") is False, "Blocked Myanmar gate must not claim a current Manufacturing artifact")
    require(not qualified, "Blocked Myanmar gate must not contain a qualifying official 2026 Manufacturing artifact")
    require(route is None, "Myanmar route must not exist while promotion gate is blocked")
    require(coverage_row.get("status") == "pending_manufacturing_verification", "Myanmar coverage must remain pending while gate is blocked")
    require(readiness_row.get("routeId") is None, "Myanmar readiness routeId must remain null while gate is blocked")
    require(readiness_row.get("packState") == "pending_manufacturing_verification", "Myanmar readiness state must remain pending")

if failures:
    print("MYANMAR_PROMOTION_GATE_FAIL")
    for failure in failures:
        print("- " + failure)
    sys.exit(1)

print(
    "MYANMAR_PROMOTION_GATE_PASS "
    f"allowed={str(gate.get('promotionAllowed')).lower()} "
    f"qualifyingArtifacts={len(qualified)} "
    f"monitoredSources={len(expected_ids)}"
)
