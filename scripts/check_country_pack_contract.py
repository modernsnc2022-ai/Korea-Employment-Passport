#!/usr/bin/env python3
from __future__ import annotations
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
EXPECTED=[
    "eligibility","registration","exam_fee","biometric","document_verify","exam_card",
    "eps_topik","skill_competency","final_selection","psychology_pre_job","mcu1",
    "job_application","roster","employer_selection","slc","post_slc_requirements",
    "visa_docs","predeparture_training","mcu3_departure","departure",
    "korea_entry_training","employer_handover","residence_registration",
    "eps_insurance_check","first_payroll_check","labor_support_ready","employment_maintenance",
]

def load(path):
    return json.loads((ROOT/path).read_text(encoding="utf-8-sig"))

failures=[]
def require(condition,message):
    if not condition: failures.append(message)

registry=load("docs/data/country_packs_v1.json")
require(registry.get("commonStageIds")==EXPECTED,"registry commonStageIds must preserve the locked 27-stage core")
routes={row.get("routeId"):row for row in registry.get("routes",[])}
require({"id-e9-manufacturing-2026","np-e9-manufacturing-2026"}.issubset(routes),"registry must include Indonesia and Nepal")

for route_id,entry in routes.items():
    pack=load("docs/"+entry["routeFile"])
    locale=load("docs/"+entry["localizationFile"])
    stage_ids=[row.get("id") for row in pack.get("stages",[])]
    require(stage_ids==EXPECTED,f"{route_id}: stage IDs/order must match common core")
    require(pack.get("country")==entry.get("country"),f"{route_id}: country mismatch")
    require(pack.get("visa")==entry.get("visa"),f"{route_id}: visa mismatch")
    require(pack.get("sector")==entry.get("sector"),f"{route_id}: sector mismatch")
    require(set(locale)==set(EXPECTED),f"{route_id}: localization must cover exactly 27 stages")
    for stage in pack.get("stages",[]):
        sid=stage.get("id","<missing>")
        for field in ("title","authority","kind","action","sourceUrl"):
            require(bool(str(stage.get(field,"")).strip()),f"{route_id}/{sid}: missing {field}")
        require(str(stage.get("sourceUrl","")).startswith("https://"),f"{route_id}/{sid}: source must use HTTPS")
        require(bool(str(locale.get(sid,{}).get("title","")).strip()),f"{route_id}/{sid}: localized title missing")
        require(bool(str(locale.get(sid,{}).get("action","")).strip()),f"{route_id}/{sid}: localized action missing")

np_entry=routes["np-e9-manufacturing-2026"]
np_pack=load("docs/data/np_e9_manufacturing_2026.json")
require(np_entry.get("lifecycle")=="research_hold","Nepal must remain research_hold")
require(np_entry.get("publicAvailability")=="preview_only","Nepal registry route must remain preview_only")
require(np_pack.get("lifecycle")=="research_hold","Nepal pack must remain research_hold")
require(np_pack.get("publicAvailability")=="preview_only","Nepal pack must remain preview_only")
require(np_pack.get("safety",{}).get("betaIntakeOpen") is False,"Nepal beta intake must remain closed")
require(np_pack.get("officialSendingAgency",{}).get("url")=="https://epsnepal.gov.np/","Nepal official sending agency URL must remain EPS Nepal")
require(np_pack.get("recruitmentCycleBasis")=="2025-manufacturing-selection-processing-through-2026","Nepal must not mislabel the current 2025 Manufacturing processing as a new 2026 recruitment cycle")

countries=(ROOT/"docs/countries.html").read_text(encoding="utf-8")
nepal=(ROOT/"docs/np.html").read_text(encoding="utf-8")
require("RESEARCH / HOLD" in countries and "preview_only" not in countries,"countries page must visibly label Nepal HOLD")
require("Research HOLD" in nepal and "Beta registration/access अहिले खुला छैन" in nepal,"Nepal page must visibly keep beta closed")
require('href="beta.html"' not in nepal,"Nepal preview must not link to Indonesia beta enrollment")
require('id="betaForm"' not in nepal,"Nepal preview must not contain a beta enrollment form")

if failures:
    print("COUNTRY_PACK_CONTRACT_FAIL")
    for failure in failures: print("- "+failure)
    raise SystemExit(1)

print("COUNTRY_PACK_CONTRACT_PASS routes=%d stages=%d nepal=research_hold" % (len(routes),len(EXPECTED)))
