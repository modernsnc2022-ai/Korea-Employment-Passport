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
from check_20261015_source_triage_snapshot import validate as validate_current_watch
from check_20261015_source_signoff import validate_signoff as validate_current_signoff
from check_20261016_source_triage_snapshot import validate as validate_oct16_watch
from check_20261016_source_signoff import validate_signoff as validate_oct16_signoff

def validate_dated_watch(watch: dict, manifest: dict) -> None:
    day = watch.get("observedAtDate")
    if day == "2026-10-15":
        validate_current_watch(watch, manifest)
    elif day == "2026-10-16":
        validate_oct16_watch(watch, manifest)
    else:
        raise ValueError("No dated reviewed source-scope validator for this day")

def validate_dated_signoff(watch: dict, manifest: dict, signed: dict, day: str) -> None:
    if day == "2026-10-15":
        validate_current_signoff(watch, manifest, signed, day)
    elif day == "2026-10-16":
        validate_oct16_signoff(watch, manifest, signed, day)
    else:
        raise ValueError("No dated source-scope signoff validator for release day")

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
                 deployed: dict | None = None, release_head: str | None = None,
                 current_watch: dict | None = None,
                 current_signed: dict | None = None,
                 pages_source: dict | None = None) -> dict:
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

    # Today's observed source-watch can supersede the *displayed* historical
    # 3+5 scope, but NOT yesterday's human signature or official SHA baseline.
    # A dated, validated 4+1+5 snapshot is distinct from operator authorization.
    use_current = current_watch is not None and current_watch.get("observedAtDate") == as_of
    if use_current:
        try:
            validate_dated_watch(current_watch, manifest)
            scope_ok = True
            scope_message = (
                f"{current_watch['checked']}/{current_watch['configured']} official sources fetched; "
                f"{len(current_watch['candidateKoreaSharedIds'])} Korea-common + "
                f"{len(current_watch['candidateMultiCountryScheduleIds'])} multi-country HRD Korea EPS + "
                f"{len(current_watch['candidateOtherCountryIds'])} other-country alerts; "
                f"{current_watch['changed']} unaccepted baseline drifts; fetch failures=none"
            )
        except (ValueError, TypeError, KeyError) as exc:
            scope_ok = False
            scope_message = "Invalid current dated source-watch: " + str(exc)
        source_fresh = scope_ok
        stamp = f"read-only observed={current_watch.get('observedAtDate')}, asOf={as_of}"
    else:
        try:
            n_shared, n_foreign = validate_scope(source, manifest, scope)
            scope_ok = (n_shared, n_foreign) == (3, 5)
            scope_message = (
                f"{source.get('checked')}/{source.get('configured')} official sources fetched; "
                f"{n_shared} Korea-common + {n_foreign} other-country alerts; "
                f"failures={','.join(source.get('fetchFailureSourceIds', [])) or 'none'}"
            )
        except (ValueError, TypeError, KeyError) as exc:
            scope_ok = False
            scope_message = "Invalid historical source scope: " + str(exc)
        source_fresh = (
            scope_ok and source.get("detectedAt") == as_of and scope.get("checkedAt") == as_of
            # Never reuse the historical 3+5 listing after the newer 10-drift
            # snapshot has appeared, even if someone changes old dates.
            and (current_watch is None or current_watch.get("observedAtDate", "") < as_of)
        )
        stamp = f"snapshot={source.get('detectedAt')}, countryScope={scope.get('checkedAt')}, asOf={as_of}"
    emit(gate("country_source_classification", "PASS" if scope_ok else "BLOCKED",
              scope_message,
              "All current source alerts must remain visible; never accept changed hashes automatically."))
    emit(gate("official_monitor_today",
              "PASS" if source_fresh else "BLOCKED",
              stamp,
              "A real same-day 84-source watch and scoped review are required; no past snapshot reuse."
              if not source_fresh else "Current read-only watch classified; separate named approval still required."))

    try:
        if use_current:
            if current_signed is None:
                raise ValueError("Current dated source signoff record is not supplied")
            validate_dated_signoff(current_watch, manifest, current_signed, as_of)
        else:
            validate_scoped_signoff(source, manifest, scope, signed, as_of)
            # When a newer monitored set is present, a historical 3+5
            # signature is never sufficient for the present or later day.
            if current_watch and current_watch.get("observedAtDate", "") >= as_of:
                raise ValueError("Historical source signoff superseded by current alerts")
        source_approved = scope_ok and source_fresh
        source_reason = (
            "Current dated, named, manual Indonesia-only source-scope signoff."
            if source_approved else "Official watch is not ready for a signed release day."
        )
    except (ValueError, TypeError, KeyError) as exc:
        source_approved = False
        source_reason = str(exc)
    pending_signed = current_signed if use_current else signed
    emit(gate("indonesia_source_manual_signoff",
              "PASS" if source_approved else
              ("PENDING" if pending_signed and pending_signed.get("status") == "pending_manual_source_signoff"
               else "BLOCKED"),
              source_reason,
              f"Operator must review {len(current_watch.get('candidateKoreaSharedIds', [])) if use_current else 3} Korea-common, acknowledge multi-country HRD Korea and foreign-country alerts, then sign the actual date."
              if not source_approved else "Keep authentic human approval evidence; separate KP2MI and deployment gates remain."))

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

    # The published source itself must be independently verified. A clean
    # main/docs publication is not proof that the unmerged candidate is live.
    published_main_ok = (
        isinstance(pages_source, dict)
        and pages_source.get("mode") == "read_only"
        and pages_source.get("sourceVerified") is True
        and pages_source.get("sourceBranch") == "main"
        and pages_source.get("sourceFolder") == "/docs"
        and pages_source.get("deployedMainFilesMatched") == len(ASSETS)
        and pages_source.get("totalAssets") == len(ASSETS)
        and pages_source.get("status") in {
            "DEPLOYED_MAIN_DRAFT_HEAD_NOT_PUBLISHED",
            "DEPLOYED_MAIN_EQUALS_HEAD_ASSETS",
        }
        and pages_source.get("approvesBetaOpen") is False
        and pages_source.get("sourceHashAccepted") is False
        and pages_source.get("remoteChangesMade") is False
    )
    emit(gate(
        "published_main_source_integrity",
        "PASS" if published_main_ok else ("PENDING" if pages_source is None else "BLOCKED"),
        ("Configured GitHub Pages main/docs matches 9/9 published assets; "
         "this does not imply Draft candidate publication."
         if published_main_ok else "Trusted live main/docs source and 9/9 asset match not established."),
        "Use authenticated read-only Pages source diagnostics; never change Pages branch to bypass review.",
    ))
    same_ref_published = (
        published_main_ok
        and pages_source.get("status") == "DEPLOYED_MAIN_EQUALS_HEAD_ASSETS"
        and pages_source.get("sameRefDeploymentConfirmed") is True
        and pages_source.get("mainRef") == release_head
        and pages_source.get("candidateRef") == release_head
    )
    deployment_pass = same_ref_published and deployment_verified(deployed, release_head)
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
                    "optional_skill_annex_evidence", "published_main_source_integrity",
                    "same_head_pages_deployment"}
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
        "publishedMainSourceIntegrityVerified": published_main_ok,
        "candidateHeadPublished": same_ref_published,
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
    # The new watch is valid MACHINE observation, not a substitute for dated
    # manual signoff. Its 4+1+5 sources must never pass the old 3+5 signature.
    fresh_watch = read_json("research/source_reviews/shared_source_watch_readonly_2026-10-15.json")
    fresh_pending = read_json("recruitment/ID_BETA_SOURCE_SIGNOFF_20261015.json")
    fresh_args = args | {"current_watch": fresh_watch, "current_signed": fresh_pending}
    observed = build_report("2026-10-15", **fresh_args)
    fresh_gates = {g["id"]: g["status"] for g in observed["gates"]}
    assert fresh_gates["country_source_classification"] == "PASS"
    assert fresh_gates["official_monitor_today"] == "PASS"
    assert fresh_gates["indonesia_source_manual_signoff"] == "PENDING"
    assert observed["readyForManualLaunchDecision"] is False
    assert observed["authorizesRelease"] is False
    assert "4 Korea-common + 1 multi-country" in next(
        g["evidence"] for g in observed["gates"] if g["id"] == "country_source_classification"
    )
    tomorrow = build_report("2026-10-16", **fresh_args)
    assert next(g for g in tomorrow["gates"]
                if g["id"] == "official_monitor_today")["status"] == "BLOCKED"
    assert tomorrow["readyForManualLaunchDecision"] is False
    # M16: A genuinely fresh read-only 84/84 source observation improves ONLY
    # the monitor gate; none of the 12 SHA differences is accepted automatically.
    day16 = read_json("research/source_reviews/shared_source_watch_readonly_2026-10-16.json")
    signed16 = read_json("recruitment/ID_BETA_SOURCE_SIGNOFF_20261016.json")
    actual16 = build_report("2026-10-16",
        **(args | {"current_watch": day16, "current_signed": signed16}))
    g16={g["id"]:g["status"] for g in actual16["gates"]}
    assert g16["country_source_classification"]=="PASS"
    assert g16["official_monitor_today"]=="PASS"
    assert g16["indonesia_source_manual_signoff"]=="PENDING"
    assert g16["kp2mi_manufacturing_release_day_signoff"]=="PENDING"
    assert g16["same_head_pages_deployment"]=="PENDING"
    assert actual16["readyForManualLaunchDecision"] is False
    assert actual16["authorizesRelease"] is False
    forged16=copy.deepcopy(day16)
    forged16["candidateKoreaSharedIds"].remove("minimum_wage")
    corrupt16=build_report("2026-10-16",
       **(args | {"current_watch":forged16, "current_signed":signed16}))
    assert next(g for g in corrupt16["gates"] if g["id"]=="official_monitor_today")["status"]=="BLOCKED"
    previous_day=build_report("2026-10-17",
       **(args | {"current_watch":day16,"current_signed":signed16}))
    assert next(g for g in previous_day["gates"] if g["id"]=="official_monitor_today")["status"]=="BLOCKED"

    for mutate in (
        lambda w: w["records"][4].update(routeScope="other_country"),
        lambda w: w["records"][0].update(url="https://example.invalid/tampered"),
        lambda w: w.update(betaAccess="open"),
        lambda w: w.update(checked=83),
    ):
        unsafe = copy.deepcopy(fresh_watch)
        mutate(unsafe)
        found = build_report("2026-10-15", **(fresh_args | {"current_watch": unsafe}))
        assert next(g for g in found["gates"]
                    if g["id"] == "country_source_classification")["status"] == "BLOCKED"
        assert found["readyForManualLaunchDecision"] is False
    # Legacy signature with a synthetic approved timestamp is *insufficient*
    # without a fresh 4+1+5 named source review.
    wrong_sign = copy.deepcopy(signed)
    wrong_sign.update(status="approved_manual_indonesia_scope", reviewer="Legacy Operator QA",
                      approvedAt="2026-10-15T13:00:00+07:00",
                      sourceSnapshotDate="2026-10-15", sourceScopeDate="2026-10-15")
    blocked = build_report("2026-10-15", **(fresh_args | {"signed": wrong_sign}))
    assert next(g for g in blocked["gates"]
                if g["id"] == "indonesia_source_manual_signoff")["status"] == "PENDING"
    # A synthetic valid 4+1+5 signature proves signoff logic can reach PASS
    # without changing any actual approvals, deploys or release-state files.
    synthetic_fresh_signed = copy.deepcopy(fresh_pending)
    synthetic_fresh_signed.update(
        status="approved_manual_indonesia_scope", reviewer="Synthetic Operator QA",
        approvedAt="2026-10-15T13:00:00+07:00",
        sourceSnapshotDate="2026-10-15", sourceScopeDate="2026-10-15",
    )
    simulated = build_report("2026-10-15",
        **(fresh_args | {"current_signed": synthetic_fresh_signed}))
    assert next(g for g in simulated["gates"]
                if g["id"] == "indonesia_source_manual_signoff")["status"] == "PASS"
    assert simulated["readyForManualLaunchDecision"] is False
    assert simulated["authorizesRelease"] is False
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
    fake_pages = {
        "mode": "read_only",
        "sourceVerified": True,
        "sourceBranch": "main",
        "sourceFolder": "/docs",
        "deployedMainFilesMatched": len(ASSETS),
        "totalAssets": len(ASSETS),
        "status": "DEPLOYED_MAIN_DRAFT_HEAD_NOT_PUBLISHED",
        "mainRef": "b" * 40,
        "candidateRef": test_sha,
        "sameRefDeploymentConfirmed": False,
        "approvesBetaOpen": False,
        "sourceHashAccepted": False,
        "remoteChangesMade": False,
    }
    unpublished = build_report("2026-10-14", **args,
                               pages_source=fake_pages, deployed=fake_deploy,
                               release_head=test_sha)
    unpublished_gates = {g["id"]: g["status"] for g in unpublished["gates"]}
    assert unpublished_gates["published_main_source_integrity"] == "PASS"
    assert unpublished_gates["same_head_pages_deployment"] == "PENDING"
    assert unpublished["publishedMainSourceIntegrityVerified"] is True
    assert unpublished["candidateHeadPublished"] is False
    fake_pages = copy.deepcopy(fake_pages)
    fake_pages.update(status="DEPLOYED_MAIN_EQUALS_HEAD_ASSETS",
                      mainRef=test_sha, sameRefDeploymentConfirmed=True)
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
        deployed=fake_deploy, release_head=test_sha, pages_source=fake_pages,
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
        deployed=fake_deploy, release_head=test_sha, pages_source=fake_pages,
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
    pages_source = None
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
        from diagnose_indonesia_beta_pages_source import inspect_live
        try:
            pages_source = inspect_live()
        except (OSError, ValueError, KeyError, subprocess.SubprocessError,
                json.JSONDecodeError) as exc:
            # Fail closed. An unavailable authenticated Pages source is not
            # grounds to claim that matching static files prove deployment.
            pages_source = {
                "mode": "read_only",
                "status": "BLOCKED_PAGES_SOURCE_CHECK_ERROR",
                "sourceVerified": False,
                "error": type(exc).__name__ + ": " + str(exc)[:160],
            }
    # Selection is date-exact. This filed 2026-10-15 snapshot is NEVER
    # sufficient for 2026-10-16 or any future beta release day.
    dated_evidence = {
        "2026-10-15": ("research/source_reviews/shared_source_watch_readonly_2026-10-15.json",
                       "recruitment/ID_BETA_SOURCE_SIGNOFF_20261015.json"),
        "2026-10-16": ("research/source_reviews/shared_source_watch_readonly_2026-10-16.json",
                       "recruitment/ID_BETA_SOURCE_SIGNOFF_20261016.json"),
    }
    selected = dated_evidence.get(as_of)
    latest_watch = read_json(selected[0]) if selected else None
    latest_signed = read_json(selected[1]) if selected else None
    report = build_report(
        as_of,
        current_watch=latest_watch, current_signed=latest_signed,
        program=read_json("docs/data/beta_program_v1.json"),
        source=read_json("docs/data/source_review_status.json"),
        manifest=read_json("monitor/sources.json"),
        scope=read_json("recruitment/ID_RELEASE_SOURCE_SCOPE_20261014.json"),
        signed=read_json("recruitment/ID_BETA_SOURCE_SIGNOFF.json"),
        manufacturing=read_json("recruitment/MANUFACTURING_LAUNCH_CHECK.json"),
        route=read_json("docs/data/id_e9_manufacturing_2026.json"),
        deployed=deployed, release_head=release_head,
        pages_source=pages_source,
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
