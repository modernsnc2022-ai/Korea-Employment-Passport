#!/usr/bin/env python3
"""Read-only Indonesia beta launch gate summary; never authorizes release.

This script only reads public-safe repository metadata and returns a report.
It never mutates signoffs, source hashes, documents, access, or deployment.
"""
from __future__ import annotations

import argparse
from datetime import datetime
import json
import re
import subprocess
from pathlib import Path
from zoneinfo import ZoneInfo

from check_indonesia_release_source_scope import validate as validate_scope
from check_indonesia_source_signoff import validate_scoped_signoff
from audit_indonesia_beta_pages_live import ASSETS, LEGACY_ENTRYPOINTS

ROOT = Path(__file__).resolve().parents[1]
INDEX = "https://kp2mi.go.id/gtog-korea/pengumuman"
CRITICAL_HOLDS = ["job_docs"]


def read_json(name: str) -> dict:
    return json.loads((ROOT / name).read_text(encoding="utf-8-sig"))


def gate(id_: str, status: str, evidence: str, next_action: str) -> dict:
    assert status in {"PASS", "PENDING", "BLOCKED", "HOLD", "INFO"}
    return {"id": id_, "status": status, "evidence": evidence, "nextAction": next_action}


def deployment_verified(deployed: dict | None, expected_sha: str | None) -> bool:
    """Validate locally observed live HTTPS asset parity; not operator approval.

    Only the CLI's --live path may furnish a trusted report by invoking actual
    HTTP probes. Do not load a user-editable JSON flag as deployment evidence.
    """
    if not deployed or not expected_sha or not re.fullmatch(r"[0-9a-f]{40}", expected_sha):
        return False
    entries = deployed.get("entrypoints")
    assets = deployed.get("assets")
    if not isinstance(entries, list) or not isinstance(assets, list):
        return False
    valid_paths = {name for name in ASSETS}
    valid_entry_ids = {name for name, _, _ in LEGACY_ENTRYPOINTS}
    return (
        deployed.get("mode") == "read_only"
        and deployed.get("authorizesRelease") is False
        and deployed.get("checkedRef") == expected_sha
        and deployed.get("httpsEntrypointSafe") is True
        and deployed.get("criticalAssetsSameRef") is True
        and deployed.get("matchingAssets") == len(ASSETS)
        and deployed.get("totalAssets") == len(ASSETS)
        and len(entries) == len(valid_entry_ids)
        and {row.get("id") for row in entries if isinstance(row, dict)} == valid_entry_ids
        and all(row.get("httpsOnly") is True for row in entries)
        and len(assets) == len(valid_paths)
        and {row.get("path") for row in assets if isinstance(row, dict)} == valid_paths
        and all(
            row.get("sameAsCheckedRef") is True
            and row.get("httpsOnly") is True
            and row.get("status") == 200
            and re.fullmatch(r"[0-9a-f]{64}", str(row.get("liveSha256", "")))
            and row.get("liveSha256") == row.get("expectedSha256")
            for row in assets
        )
    )


def build_report(as_of: str, *, program: dict, source: dict, manifest: dict,
                 scope: dict, signed: dict, manufacturing: dict, route: dict,
                 deployed: dict | None = None, release_head: str | None = None) -> dict:
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

    deployment_pass = deployment_verified(deployed, release_head)
    emit(gate("same_head_pages_deployment", "PASS" if deployment_pass else "PENDING",
              (f"Live checked HEAD={release_head}; exact HTTPS assets=9/9; "
               f"legacy redirects=6/6, all same committed SHA"
               if deployment_pass else
               "No trusted current live 9/9 HEAD parity + 6/6 HTTPS redirects on approved candidate."),
              "Run --live in a clean reviewed checkout after approved Pages deployment; "
              "independently review the actual deployment event. This check never authorizes OPEN."))
    status = program.get("status")
    decision = program.get("releaseDecision", {}).get("publicBeta")
    manual_still_pending = (
        status == "hold" and decision == "pending_manual_approval"
        and program.get("application", {}).get("intakeStatus") == "open"
    )
    emit(gate("explicit_manual_beta_open",
              "PENDING" if manual_still_pending else "BLOCKED",
              f"betaAccess={status}; decision={decision}; intake={program.get('application', {}).get('intakeStatus')}",
              "A responsible operator must explicitly authorize public beta OPEN after every "
              "technical/official gate passes. HOLD is the expected pre-approval state."))

    required_ids = {"route_safety", "country_source_classification", "official_monitor_today",
                    "indonesia_source_manual_signoff", "kp2mi_manufacturing_release_day_signoff",
                    "optional_skill_annex_evidence", "same_head_pages_deployment"}
    ready = (manual_still_pending and all(
        item["status"] == "PASS" for item in result if item["id"] in required_ids
    ))
    return {
        "version": "1.1.0",
        "scope": "Indonesia > Korea > E-9 > General Manufacturing 2026",
        "asOf": as_of,
        "mode": "read_only_evidence_summary",
        "authorizesRelease": False,
        "readyForManualLaunchDecision": ready,
        "manualOpenDecisionStillRequired": manual_still_pending,
        "liveDeploymentEvidenceChecked": deployment_pass,
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
    test_sha = "a" * 40
    fake_deploy = {
        "mode": "read_only",
        "authorizesRelease": False,
        "checkedRef": test_sha,
        "httpsEntrypointSafe": True,
        "criticalAssetsSameRef": True,
        "matchingAssets": len(ASSETS),
        "totalAssets": len(ASSETS),
        "entrypoints": [
            {"id": name, "httpsOnly": True}
            for name, _, _ in LEGACY_ENTRYPOINTS
        ],
        "assets": [
            {"path": name, "httpsOnly": True, "status": 200,
             "sameAsCheckedRef": True, "liveSha256": "0" * 64,
             "expectedSha256": "0" * 64}
            for name in ASSETS
        ],
    }
    assert deployment_verified(fake_deploy, test_sha) is True
    for mutation in (
        lambda d: d.update(checkedRef="b" * 40),
        lambda d: d["entrypoints"][3].update(httpsOnly=False),
        lambda d: d["entrypoints"].pop(),
        lambda d: d["assets"][0].update(sameAsCheckedRef=False),
        lambda d: d["assets"][0].update(liveSha256="1" * 64),
        lambda d: d.update(matchingAssets=8),
        lambda d: d.update(authorizesRelease=True),
    ):
        mutated = copy.deepcopy(fake_deploy)
        mutation(mutated)
        assert deployment_verified(mutated, test_sha) is False
    # Synthetic all-official approvals, not written to actual files: this
    # demonstrates reaching READY *while access remains HOLD*. The final
    # human OPEN is a separate action and NEVER auto-approved by this tool.
    synthetic_source = copy.deepcopy(source)
    synthetic_scope = copy.deepcopy(scope)
    synthetic_signed = copy.deepcopy(signed)
    synthetic_manufacturing = copy.deepcopy(manufacturing)
    synthetic_source["detectedAt"] = "2026-10-14"
    synthetic_scope["checkedAt"] = "2026-10-14"
    synthetic_signed.update(
        status="approved_manual_indonesia_scope",
        reviewer="Synthetic authorised operator",
        approvedAt="2026-10-14T17:30:00+09:00",
        sourceSnapshotDate="2026-10-14", sourceScopeDate="2026-10-14"
    )
    index = synthetic_manufacturing["noticeIndexCoverage"]
    index.update(
        status="verified_complete_general_manufacturing_index_review",
        operatorConfirmedCompleteReview=True, completeGeneralManufacturingInventory=True,
        checkedAt="2026-10-14",
    )
    synthetic_manufacturing["checkedAt"] = "2026-10-14"
    synthetic_manufacturing["sameDayOfficialRecheck"]["checkedAt"] = "2026-10-14"
    hypothetical = build_report(
        "2026-10-14",
        **(args | {"source": synthetic_source, "scope": synthetic_scope,
                   "signed": synthetic_signed, "manufacturing": synthetic_manufacturing}),
        deployed=fake_deploy, release_head=test_sha,
    )
    assert hypothetical["readyForManualLaunchDecision"] is True
    assert hypothetical["manualOpenDecisionStillRequired"] is True
    assert hypothetical["authorizesRelease"] is False
    missing_proof = build_report(
        "2026-10-14",
        **(args | {"source": synthetic_source, "scope": synthetic_scope,
                   "signed": synthetic_signed, "manufacturing": synthetic_manufacturing}),
    )
    assert missing_proof["readyForManualLaunchDecision"] is False
    already_open = copy.deepcopy(program)
    already_open["status"] = "open"
    assert build_report(
        "2026-10-14",
        **(args | {"source": synthetic_source, "scope": synthetic_scope,
                   "signed": synthetic_signed, "manufacturing": synthetic_manufacturing,
                   "program": already_open}),
        deployed=fake_deploy, release_head=test_sha,
    )["readyForManualLaunchDecision"] is False
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
    print("ID_BETA_RELEASE_PREFLIGHT_SELF_TEST_PASS synthetic_READY_requires_live_sha_and_manual_OPEN_still_pending; 7 deployment fail-closed states")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--as-of", help="Local review day YYYY-MM-DD, default Asia/Jakarta today")
    parser.add_argument("--json", action="store_true", help="Print machine-readable report to stdout")
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--live", action="store_true",
                        help="Independently fetch 6 legacy HTTPS redirect entries and compare 9 served assets to HEAD")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return
    as_of = args.as_of or datetime.now(ZoneInfo("Asia/Jakarta")).date().isoformat()
    # No user-editable --deployment-proof flag: the only trusted audit report
    # comes from an actual fresh live read-only request in this same process.
    deployed = None
    release_head = None
    if args.live:
        from audit_indonesia_beta_pages_live import audit, http_first_hop
        release_head = subprocess.check_output(
            ["git", "-C", str(ROOT), "rev-parse", "HEAD"], text=True,
        ).strip()

        def committed_blob(name: str) -> bytes:
            return subprocess.check_output(
                ["git", "-C", str(ROOT), "show", "HEAD:docs/" + name]
            )

        deployed = audit(http_first_hop, ROOT / "docs", release_head,
                         asset_loader=committed_blob)
    report = build_report(
        as_of,
        program=read_json("docs/data/beta_program_v1.json"),
        source=read_json("docs/data/source_review_status.json"),
        manifest=read_json("monitor/sources.json"),
        scope=read_json("recruitment/ID_RELEASE_SOURCE_SCOPE_20261014.json"),
        signed=read_json("recruitment/ID_BETA_SOURCE_SIGNOFF.json"),
        manufacturing=read_json("recruitment/MANUFACTURING_LAUNCH_CHECK.json"),
        route=read_json("docs/data/id_e9_manufacturing_2026.json"),
        deployed=deployed, release_head=release_head,
    )
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(f"INDONESIA_BETA_PREFLIGHT date={as_of} releaseAuthorized=FALSE")
        for item in report["gates"]:
            print(f"[{item['status']}] {item['id']}: {item['evidence']}")
            if item["status"] != "PASS":
                print("  NEXT:", item["nextAction"])
        print(f"READY_FOR_MANUAL_DECISION={report['readyForManualLaunchDecision']} "
              f"MANUAL_DECISION_REQUIRED={report['manualOpenDecisionStillRequired']} "
              f"LIVE_DEPLOYMENT_VERIFIED={report['liveDeploymentEvidenceChecked']}")
        print("NO_AUTO_SIGNOFF_NO_HASH_ACCEPTANCE_NO_RELEASE")


if __name__ == "__main__":
    main()
