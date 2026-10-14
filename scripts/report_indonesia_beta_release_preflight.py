#!/usr/bin/env python3
"""Read-only Indonesia beta launch gate summary; never authorizes release.

This script only reads public-safe repository metadata and returns a report.
It never mutates signoffs, source hashes, documents, access, or deployment.
"""
from __future__ import annotations

import argparse
from datetime import datetime
import json
from pathlib import Path
from zoneinfo import ZoneInfo

from check_indonesia_release_source_scope import validate as validate_scope
from check_indonesia_source_signoff import validate_scoped_signoff

ROOT = Path(__file__).resolve().parents[1]
INDEX = "https://kp2mi.go.id/gtog-korea/pengumuman"
CRITICAL_HOLDS = ["job_docs"]


def read_json(name: str) -> dict:
    return json.loads((ROOT / name).read_text(encoding="utf-8-sig"))


def gate(id_: str, status: str, evidence: str, next_action: str) -> dict:
    assert status in {"PASS", "PENDING", "BLOCKED", "HOLD", "INFO"}
    return {"id": id_, "status": status, "evidence": evidence, "nextAction": next_action}


def build_report(as_of: str, *, program: dict, source: dict, manifest: dict,
                 scope: dict, signed: dict, manufacturing: dict, route: dict) -> dict:
    # The report must never use a baseline recorded before the requested day
    # to claim that release-day official evidence has been reviewed.
    from datetime import date
    date.fromisoformat(as_of)
    result = []
    emit = result.append
    stages = route.get("stages", [])
    competency = next((x for x in stages if x.get("id") == "skill_competency"), {})
    notice = competency.get("competencyUploadNotice", {})
    conditional = notice.get("conditionalSubmission", {})
    job = next((x for x in stages if x.get("id") == "job_application"), {})
    safe = (
        route.get("country") == "ID"
        and route.get("visa") == "E-9"
        and route.get("sector") == "manufacturing"
        and route.get("cycle") == 2026
        and len(stages) == 27
        and job.get("brokerReplacement") == "held_official_notice"
        and notice.get("optional") is True and notice.get("status") == "closed"
        and notice.get("notJobApplicationDocuments") is True
        and conditional.get("competencyFormRequiredWithAnyUploadedEvidence") is True
        and conditional.get("workExperienceFallbackRequiresTwoNonRelativeSureties") is True
        and conditional.get("notFinalManufacturingJobApplicationChecklist") is True
    )
    emit(gate("route_safety", "PASS" if safe else "BLOCKED",
              "27-stage 2026 Indonesia E-9 Manufacturing; Skill Test mandatory, optional evidence closed; job_docs held"
              if safe else "Official route, conditional annex or exact-document HOLD has changed",
              "Retain official-only fallback for final Manufacturing documents." if safe
              else "Stop: restore current-cycle route and optional-document protections."))

    try:
        n_shared, n_foreign = validate_scope(source, manifest, scope)
        scope_ok = (n_shared, n_foreign) == (3, 5)
        scope_message = (f"{source.get('checked')}/{source.get('configured')} official sources fetched; "
                         f"{n_shared} Korea-common + {n_foreign} other-country alerts; "
                         f"failures={','.join(source.get('fetchFailureSourceIds', [])) or 'none'}")
    except (ValueError, TypeError, KeyError) as exc:
        scope_ok = False
        scope_message = "Invalid source scope: " + str(exc)
    emit(gate("country_source_classification", "PASS" if scope_ok else "BLOCKED",
              scope_message,
              "Do not silently accept source hashes or hide foreign-country notices."))

    source_fresh = source.get("detectedAt") == as_of and scope.get("checkedAt") == as_of
    emit(gate("official_monitor_today",
              "PASS" if scope_ok and source_fresh else "BLOCKED",
              f"snapshot={source.get('detectedAt')}, countryScope={scope.get('checkedAt')}, asOf={as_of}",
              "Re-run read-only 84-source monitor and classify any changed/unavailable notices on actual release day."
              if not source_fresh else "Snapshot available; source signoff is still separate."))

    try:
        validate_scoped_signoff(source, manifest, scope, signed, as_of)
        source_approved = True
        source_reason = "Valid named, same-day manual Indonesia-only scope signature."
    except (ValueError, TypeError, KeyError) as exc:
        source_approved = False
        source_reason = str(exc)
    emit(gate("indonesia_source_manual_signoff",
              "PASS" if source_approved else ("PENDING" if signed.get("status") == "pending_manual_source_signoff" else "BLOCKED"),
              source_reason,
              "Operator must review three Korea-common items, acknowledge five foreign alerts, then sign dated official scope."
              if not source_approved else "Preserve signed evidence for deploy review."))

    index = manufacturing.get("noticeIndexCoverage", {})
    index_today = index.get("checkedAt") == as_of
    index_path_ok = index.get("officialManufacturingInventoryUrl") == INDEX
    review_signed = (
        index.get("status") == "verified_complete_general_manufacturing_index_review"
        and index.get("operatorConfirmedCompleteReview") is True
        and index.get("completeGeneralManufacturingInventory") is True
        and index_today and index_path_ok
        and manufacturing.get("checkedAt") == as_of
        and manufacturing.get("sameDayOfficialRecheck", {}).get("checkedAt") == as_of
        and manufacturing.get("sameDayOfficialRecheck", {}).get("status") ==
        "completed_no_detailed_manufacturing_notice_found"
        and manufacturing.get("result") == "no_current_manufacturing_job_application_notice"
        and manufacturing.get("heldQuestions") == CRITICAL_HOLDS
    )
    emit(gate("kp2mi_manufacturing_release_day_signoff",
              "PASS" if review_signed else "PENDING",
              (f"KP2MI Pengumuman indexChecked={index.get('checkedAt')}; "
               f"historicalJobCheck={manufacturing.get('checkedAt')}; "
               f"manualApproval={index.get('operatorConfirmedCompleteReview')}; "
               f"currentIndex={index.get('currentListingUrl') or INDEX}"),
              "Human must review the current 2026 general Manufacturing notice contents/attachments and record a genuine same-day signoff."
              if not review_signed else "Keep signed notice review evidence."))

    annex = index.get("latestIndependentEvidence", {}).get("optionalCompetencyPdfAnnexReview", {})
    evidence_ready = (annex.get("officialPdfLinksFetched") == 6
                      and annex.get("allFilesVerifiedPdf") is True
                      and annex.get("submissionStatus") == "closed"
                      and annex.get("exactFinalJobDocumentsVerified") is False)
    emit(gate("optional_skill_annex_evidence", "PASS" if evidence_ready else "BLOCKED",
              "Six PDF annexes indexed with closed optional upload; never final Manufacturing job_docs"
              if evidence_ready else "Official optional evidence attachments not adequately documented",
              "Do not promote the optional annexes into final job-application requirements."))

    emit(gate("same_head_pages_deployment", "PENDING",
              "This offline preflight has no trusted live deployed SHA or Pages release proof.",
              "After approved merge/deploy, independently verify served Pages assets match reviewed commit."))
    status = program.get("status")
    decision = program.get("releaseDecision", {}).get("publicBeta")
    emit(gate("explicit_manual_beta_open",
              "PENDING" if status == "hold" and decision == "pending_manual_approval" else "BLOCKED",
              f"betaAccess={status}; decision={decision}; intake={program.get('application', {}).get('intakeStatus')}",
              "Do not change beta access before same-day official signoffs and same-HEAD deployed-site verification."))

    required_ids = {"route_safety", "country_source_classification", "official_monitor_today",
                    "indonesia_source_manual_signoff", "kp2mi_manufacturing_release_day_signoff",
                    "same_head_pages_deployment", "explicit_manual_beta_open"}
    ready = all(item["status"] == "PASS" for item in result if item["id"] in required_ids)
    return {
        "version": "1.0.0",
        "scope": "Indonesia > Korea > E-9 > General Manufacturing 2026",
        "asOf": as_of,
        "mode": "read_only_evidence_summary",
        "authorizesRelease": False,
        "readyForManualLaunchDecision": ready,
        "exactManufacturingJobDocumentsHeld": job.get("brokerReplacement") == "held_official_notice",
        "gates": result,
    }


def self_test() -> None:
    program = read_json("docs/data/beta_program_v1.json")
    source = read_json("docs/data/source_review_status.json")
    manifest = read_json("monitor/sources.json")
    scope = read_json("recruitment/ID_RELEASE_SOURCE_SCOPE_20261014.json")
    signed = read_json("recruitment/ID_BETA_SOURCE_SIGNOFF.json")
    manufacturing = read_json("recruitment/MANUFACTURING_LAUNCH_CHECK.json")
    route = read_json("docs/data/id_e9_manufacturing_2026.json")
    args = dict(program=program, source=source, manifest=manifest, scope=scope,
                signed=signed, manufacturing=manufacturing, route=route)
    report = build_report("2026-10-14", **args)
    by_id = {g["id"]: g["status"] for g in report["gates"]}
    assert by_id["route_safety"] == "PASS"
    assert by_id["country_source_classification"] == "PASS"
    assert by_id["official_monitor_today"] == "PASS"
    assert by_id["optional_skill_annex_evidence"] == "PASS"
    assert by_id["indonesia_source_manual_signoff"] == "PENDING"
    assert by_id["kp2mi_manufacturing_release_day_signoff"] == "PENDING"
    assert by_id["same_head_pages_deployment"] == "PENDING"
    assert report["authorizesRelease"] is False
    assert report["readyForManualLaunchDecision"] is False
    next_day = build_report("2026-10-15", **args)
    assert next(g for g in next_day["gates"] if g["id"] == "official_monitor_today")["status"] == "BLOCKED"
    import copy
    bad_route = copy.deepcopy(route)
    bad_route["stages"][7]["competencyUploadNotice"]["status"] = "open"
    assert next(g for g in build_report("2026-10-14", **(args | {"route": bad_route}))["gates"]
                if g["id"] == "route_safety")["status"] == "BLOCKED"
    bad_monitor = copy.deepcopy(source)
    bad_monitor["reviewRequiredSourceIds"].append("unknown_source")
    assert next(g for g in build_report("2026-10-14", **(args | {"source": bad_monitor}))["gates"]
                if g["id"] == "country_source_classification")["status"] == "BLOCKED"
    bad_signoff = copy.deepcopy(signed)
    bad_signoff["status"] = "approved_manual_indonesia_scope"
    assert next(g for g in build_report("2026-10-14", **(args | {"signed": bad_signoff}))["gates"]
                if g["id"] == "indonesia_source_manual_signoff")["status"] == "BLOCKED"
    print("ID_BETA_RELEASE_PREFLIGHT_SELF_TEST_PASS current pending and 4 fail-closed states")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--as-of", help="Local review day YYYY-MM-DD, default Asia/Jakarta today")
    parser.add_argument("--json", action="store_true", help="Print machine-readable report to stdout")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return
    as_of = args.as_of or datetime.now(ZoneInfo("Asia/Jakarta")).date().isoformat()
    report = build_report(
        as_of,
        program=read_json("docs/data/beta_program_v1.json"),
        source=read_json("docs/data/source_review_status.json"),
        manifest=read_json("monitor/sources.json"),
        scope=read_json("recruitment/ID_RELEASE_SOURCE_SCOPE_20261014.json"),
        signed=read_json("recruitment/ID_BETA_SOURCE_SIGNOFF.json"),
        manufacturing=read_json("recruitment/MANUFACTURING_LAUNCH_CHECK.json"),
        route=read_json("docs/data/id_e9_manufacturing_2026.json"),
    )
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(f"INDONESIA_BETA_PREFLIGHT date={as_of} releaseAuthorized=FALSE")
        for item in report["gates"]:
            print(f"[{item['status']}] {item['id']}: {item['evidence']}")
            if item["status"] != "PASS":
                print("  NEXT:", item["nextAction"])
        print("NO_AUTO_SIGNOFF_NO_HASH_ACCEPTANCE_NO_RELEASE")


if __name__ == "__main__":
    main()
