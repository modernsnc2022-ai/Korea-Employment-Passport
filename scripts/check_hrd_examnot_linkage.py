#!/usr/bin/env python3
"""Validate KEP's HRD Korea examNot linkage evidence and route references."""

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "docs/data/hrd_examnot_linkage_2026.json"

failures = []


def require(condition, message):
    if not condition:
        failures.append(message)


def load(rel):
    return json.loads((ROOT / rel).read_text(encoding="utf-8"))


doc = json.loads(EVIDENCE.read_text(encoding="utf-8"))
mappings = doc.get("mappings", [])
method = doc.get("method", {})

require(doc.get("checkedAt") == "2026-10-06", "examNot evidence checkedAt must remain 2026-10-06 for this snapshot")
require("examNot" in method.get("rule", ""), "examNot method rule must name the official join key")
require("never used as the cycle join key" in method.get("rule", ""), "public ordinal labels must never be used as the cycle join key")
require(method.get("candidateIndex", "").startswith("https://epstopik.hrdkorea.or.kr/"), "candidate index must remain HRD Korea")
require(method.get("finalResultIndex", "").startswith("https://epstopik.hrdkorea.or.kr/"), "final-result index must remain HRD Korea")

expected = {"MN", "KH", "CN", "TL", "TH", "UZ", "TJ"}
countries = [row.get("country") for row in mappings]
require(set(countries) == expected, "examNot evidence must cover the seven verified 2026 Manufacturing linkages")
require(len(countries) == len(set(countries)), "examNot evidence country mappings must be unique")

date_re = re.compile(r"^2026-\d{2}-\d{2}$")
pack_files = {
    "MN": "docs/data/mn_e9_manufacturing_2026.json",
    "KH": "docs/data/kh_e9_manufacturing_2026.json",
    "CN": "docs/data/cn_e9_manufacturing_2026.json",
    "TL": "docs/data/tl_e9_manufacturing_2026.json",
    "TH": "docs/data/th_e9_manufacturing_2026.json",
    "UZ": "docs/data/uz_e9_manufacturing_2026.json",
    "TJ": "docs/data/tj_e9_manufacturing_2026.json",
}

for row in mappings:
    country = row.get("country")
    require(row.get("examYear") == "2026", f"{country}: examYear must be 2026")
    require(row.get("lcnsId") == "001", f"{country}: lcnsId must remain 001")
    require(str(row.get("examNation", "")).isdigit(), f"{country}: examNation must be numeric")
    require("Manufacturing" in row.get("scheduleTitle", "") or row.get("manufacturing"), f"{country}: mapping must preserve Manufacturing identity")

    linked = set()
    if row.get("examNot") is not None:
        linked.add(str(row["examNot"]))
        require(str(row["examNot"]).isdigit(), f"{country}: examNot must be numeric")
        skills = row.get("skillsCandidate")
        if skills:
            require(date_re.match(skills.get("publicationDate", "")) is not None, f"{country}: skills publication date must be an exact 2026 date")
        final = row.get("finalResult")
        if final:
            require(date_re.match(final.get("publicationDate", "")) is not None, f"{country}: final-result publication date must be an exact 2026 date")
    else:
        manufacturing = row.get("manufacturing", [])
        require(bool(manufacturing), f"{country}: site/sector mapping must include Manufacturing rows")
        for item in manufacturing:
            exam_not = str(item.get("examNot", ""))
            require(exam_not.isdigit(), f"{country}: Manufacturing examNot must be numeric")
            require(exam_not not in linked, f"{country}: duplicate Manufacturing examNot {exam_not}")
            linked.add(exam_not)
            require("Manufacturing" in item.get("scheduleTitle", ""), f"{country}: site row must explicitly remain Manufacturing")
            require(date_re.match(item.get("publicationDate", "")) is not None, f"{country}: site candidate publication date must be exact")

    excluded = set()
    for key in ("excludedRows", "excludedFishery"):
        for item in row.get(key, []):
            excluded.add(str(item.get("examNot", "")))
    excluded.update(str(x) for x in row.get("excludedOtherSectorExamNot", []))
    require(not (linked & excluded), f"{country}: linked and excluded examNot sets must be disjoint")

    pack = load(pack_files[country])
    require(pack.get("examNotLinkageEvidenceFile") == "data/hrd_examnot_linkage_2026.json", f"{country}: route pack must reference shared examNot evidence")

kh = next(row for row in mappings if row.get("country") == "KH")
require(kh.get("examNot") == "46", "Cambodia linkage must remain examNot=46")
require("not normalized" in kh.get("warning", ""), "Cambodia mapping must preserve the ordinal-normalization firewall")

th = next(row for row in mappings if row.get("country") == "TH")
require({x.get("examNot") for x in th.get("manufacturing", [])} == {"57", "64"}, "Thailand Manufacturing linkage must stay limited to examNot 57/64")
require(set(th.get("excludedOtherSectorExamNot", [])) == {"56", "58", "63", "65"}, "Thailand other-sector exclusions must remain explicit")

tl = next(row for row in mappings if row.get("country") == "TL")
require({x.get("examNot") for x in tl.get("manufacturing", [])} == {"42", "43"}, "Timor-Leste Manufacturing linkage must stay limited to examNot 42/43")
require({x.get("examNot") for x in tl.get("excludedFishery", [])} == {"44", "45"}, "Timor-Leste Fishery exclusions must remain explicit")

if failures:
    print("HRD_EXAMNOT_LINKAGE_FAIL")
    for failure in failures:
        print("- " + failure)
    sys.exit(1)

print(f"HRD_EXAMNOT_LINKAGE_PASS countries={len(mappings)}")
