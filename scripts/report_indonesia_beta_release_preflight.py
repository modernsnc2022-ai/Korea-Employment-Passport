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
    elif day == "2026-10-17":
        from report_daily_indonesia_source_watch import validate_committed_snapshot
        validate_committed_snapshot(watch, manifest,
                                    read_json("monitor/source_hashes.json"), day)
    elif day == "2026-10-18":
        from check_m39_oct18_preflight_watch import validate as validate_m39_machine_watch
        validate_m39_machine_watch(watch, manifest)
    else:
        raise ValueError("No dated reviewed source-scope validator for this day")

def validate_dated_signoff(watch: dict, manifest: dict, signed: dict, day: str) -> None:
    if day == "2026-10-15":
        validate_current_signoff(watch, manifest, signed, day)
    elif day == "2026-10-16":
        validate_oct16_signoff(watch, manifest, signed, day)
    elif day == "2026-10-17":
        from report_daily_indonesia_source_watch import validate_daily_source_signoff
        validate_daily_source_signoff(watch, manifest,
                                      read_json("monitor/source_hashes.json"),
                                      signed, day)
    elif day == "2026-10-18":
        # Machine-only M38/M39 records must NEVER be promoted to a human
        # approval, even if a caller inserts synthetic reviewer fields.
        raise ValueError("2026-10-18 M39 is technical monitoring only; 20 named human review decisions remain unsigned")
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


def required_gates_all_pass(gates: list[dict], required_ids: set[str]) -> bool:
    """No vacuous PASS when a critical gate was omitted or duplicated."""
    if not isinstance(gates, list) or not isinstance(required_ids, set):
        return False
    ids = [row.get("id") for row in gates if isinstance(row, dict)]
    if len(ids) != len(gates) or len(ids) != len(set(ids)):
        return False
    if not required_ids.issubset(set(ids)):
        return False
    lookup = {row["id"]: row.get("status") for row in gates}
    return all(lookup.get(name) == "PASS" for name in required_ids)


def build_report(as_of: str, *, program: dict, source: dict, manifest: dict,
                 scope: dict, signed: dict, manufacturing: dict, route: dict,
                 deployed: dict | None = None, release_head: str | None = None,
                 current_watch: dict | None = None,
                 current_signed: dict | None = None,
                 pages_source: dict | None = None,
                 current_notice: dict | None = None) -> dict:
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
            if current_watch.get("groupCounts") is not None:
                groups = current_watch["groupCounts"]
                shared, multi, other = (
                    groups["korea_shared"], groups["multi_country_eps_schedule"],
                    groups["other_country"])
                unknown = groups["unclassified_requires_manual_scope_review"]
                drift_count = current_watch["unacceptedBaselineDriftCount"]
            else:
                shared = len(current_watch["candidateKoreaSharedIds"])
                multi = len(current_watch["candidateMultiCountryScheduleIds"])
                other = len(current_watch["candidateOtherCountryIds"])
                unknown = 0
                drift_count = current_watch["changed"]
            scope_message = (
                f"{current_watch['checked']}/{current_watch['configured']} official sources fetched; "
                f"{shared} Korea-common + {multi} multi-country HRD Korea EPS + "
                f"{other} other-country + {unknown} unclassified alerts; "
                f"{drift_count} unaccepted baseline drifts; fetch failures=none"
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
              f"Operator must review {current_watch.get('groupCounts', {}).get('korea_shared', len(current_watch.get('candidateKoreaSharedIds', []))) if use_current else 3} Korea-common, acknowledge multi-country HRD Korea and foreign-country alerts, then sign the actual date."
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

    # M40: today's index TITLE/URL observation is a separate machine-only
    # gate. Matching notice IDs do not approve their bodies or final job docs.
    if current_notice is None:
        notice_status = "PENDING"
        notice_reason = "No independently bound current-day notice index record"
    else:
        try:
            if as_of != "2026-10-18":
                raise ValueError("M40 source date cannot be reused")
            from verify_m40_oct18_human_notice_handoff import verify as verify_m40
            verify_m40(current_notice)
            notice_status = "PASS"
            notice_reason = "M40 320 KP2MI titles, 7 unsigned notice tasks, 2 HRD timetable refs"
        except (ValueError, TypeError, KeyError) as exc:
            notice_status = "BLOCKED"
            notice_reason = "Invalid M40 notice evidence: " + str(exc)
    emit(gate("kp2mi_current_notice_index_observed", notice_status,
              notice_reason, "Machine observation is not an official content signoff. "
              "Review exact original notice bodies/PDF annexes and current-cycle job_docs."))

    # M33 CRITICAL: a signed statement that the operator found NO final
    # Manufacturing notice is NOT a verified final online job-doc checklist.
    # Keep a separate non-waivable release blocker until a later intentionally
    # reviewed code/data revision provides the exact applicable 2026 official
    # original body/annex, named human approval and audited required files.
    # Do not infer documents from optional Skill Test, initial exam enrollment,
    # Fisheries / Special UBT, historical 2025 documents, or a notice TITLE.
    final_docs_holding = (
        job.get("brokerReplacement") == "held_official_notice"
        and manufacturing.get("heldQuestions") == CRITICAL_HOLDS
        and manufacturing.get("result") == "no_current_manufacturing_job_application_notice"
    )
    emit(gate("exact_2026_manufacturing_final_job_documents",
              "PENDING" if final_docs_holding else "BLOCKED",
              "Exact current-cycle post-Skill-Test General Manufacturing online application files and annexes are not verified; an absence notice signoff is not approval."
              if final_docs_holding else "Unexpected change to held job documents without an independently reviewed official 2026 checklist.",
              "Do not enable beta or final submission. Obtain exact KP2MI 2026 General Manufacturing job-doc original notice + attachments, review required files, and implement an explicit independently tested release-day signoff path."))

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
                    "kp2mi_current_notice_index_observed",
                    "exact_2026_manufacturing_final_job_documents",
                    "optional_skill_annex_evidence", "published_main_source_integrity",
                    "same_head_pages_deployment"}
    ready = (manual_still_pending and required_gates_all_pass(result, required_ids))
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
    # M39: a genuine Oct18 machine-only 84/84 source observation is eligible
    # for technical monitoring, not for semantic approval or release.
    today18=read_json("research/source_reviews/indonesia_m39_oct18_preflight_technical_watch.json")
    unsigned18=read_json("recruitment/ID_BETA_SOURCE_SIGNOFF_20261017.json")
    ctx18=args | {"current_watch":today18,"current_signed":unsigned18}
    report18=build_report("2026-10-18",**ctx18)
    g18={x["id"]:x["status"] for x in report18["gates"]}
    assert g18["country_source_classification"]=="PASS"
    assert g18["official_monitor_today"]=="PASS"
    assert g18["indonesia_source_manual_signoff"]=="PENDING"
    assert g18["kp2mi_manufacturing_release_day_signoff"]=="PENDING"
    assert g18["exact_2026_manufacturing_final_job_documents"]=="PENDING"
    assert g18["same_head_pages_deployment"]=="PENDING"
    assert report18["readyForManualLaunchDecision"] is False
    assert report18["authorizesRelease"] is False
    # M40: dated machine-only KP2MI evidence MUST NOT sign notice contents,
    # final online documents or beta. A counterfeit record cannot pass.
    official40=read_json("research/source_reviews/indonesia_m40_oct18_notice_handoff.json")
    linked40=build_report("2026-10-18",**ctx18,current_notice=official40)
    linked_gates={x["id"]:x["status"] for x in linked40["gates"]}
    assert linked_gates["kp2mi_current_notice_index_observed"]=="PASS"
    assert linked_gates["kp2mi_manufacturing_release_day_signoff"]=="PENDING"
    assert linked_gates["exact_2026_manufacturing_final_job_documents"]=="PENDING"
    assert linked40["readyForManualLaunchDecision"] is False
    corrupt40=copy.deepcopy(official40)
    corrupt40["humanNoticeContentsSigned"]=True
    bad40=build_report("2026-10-18",**ctx18,current_notice=corrupt40)
    assert next(x for x in bad40["gates"]
       if x["id"]=="kp2mi_current_notice_index_observed")["status"]=="BLOCKED"
    assert bad40["authorizesRelease"] is False
    stale40=build_report("2026-10-19",**ctx18,current_notice=official40)
    assert next(x for x in stale40["gates"]
       if x["id"]=="kp2mi_current_notice_index_observed")["status"]=="BLOCKED"
    forged18=copy.deepcopy(today18)
    forged18["sourceHashAutoAccepted"]=True
    invalid18=build_report("2026-10-18",**(ctx18 | {"current_watch":forged18}))
    assert next(x for x in invalid18["gates"]
      if x["id"]=="official_monitor_today")["status"]=="BLOCKED"
    assert invalid18["readyForManualLaunchDecision"] is False
    forged_signed=copy.deepcopy(unsigned18)
    forged_signed["status"]="approved_manual_indonesia_scope"
    forged_signed["reviewer"]="Invented Responsible Reviewer"
    counterfeit=build_report("2026-10-18",**(ctx18 | {"current_signed":forged_signed}))
    assert next(x for x in counterfeit["gates"]
      if x["id"]=="indonesia_source_manual_signoff")["status"]=="BLOCKED"
    assert counterfeit["readyForManualLaunchDecision"] is False
    stale18=build_report("2026-10-19",**ctx18)
    assert next(x for x in stale18["gates"]
      if x["id"]=="official_monitor_today")["status"]=="BLOCKED"
    assert stale18["authorizesRelease"] is False
    forged16=copy.deepcopy(day16)
    forged16["candidateKoreaSharedIds"].remove("minimum_wage")
    corrupt16=build_report("2026-10-16",
       **(args | {"current_watch":forged16, "current_signed":signed16}))
    assert next(g for g in corrupt16["gates"] if g["id"]=="official_monitor_today")["status"]=="BLOCKED"
    previous_day=build_report("2026-10-17",
       **(args | {"current_watch":day16,"current_signed":signed16}))
    assert next(g for g in previous_day["gates"] if g["id"]=="official_monitor_today")["status"]=="BLOCKED"
    # M19 current-day full 84-source watch and KP2MI 2026 title inventory.
    # Only the machine observation is fresh; named human signoff remains pending.
    day17 = read_json("research/source_reviews/indonesia_daily_readonly_2026-10-17.json")
    signed17 = read_json("recruitment/ID_BETA_SOURCE_SIGNOFF_20261017.json")
    actual17 = build_report("2026-10-17",
        **(args | {"current_watch": day17, "current_signed": signed17}))
    g17 = {g["id"]:g["status"] for g in actual17["gates"]}
    assert g17["country_source_classification"] == "PASS"
    assert g17["official_monitor_today"] == "PASS"
    assert g17["indonesia_source_manual_signoff"] == "PENDING"
    assert g17["kp2mi_manufacturing_release_day_signoff"] == "PENDING"
    assert g17["same_head_pages_deployment"] == "PENDING"
    assert actual17["readyForManualLaunchDecision"] is False
    assert actual17["authorizesRelease"] is False
    stale17 = build_report("2026-10-18",
        **(args | {"current_watch": day17, "current_signed": signed17}))
    assert next(g for g in stale17["gates"] if g["id"]=="official_monitor_today")["status"]=="BLOCKED"
    forged17 = copy.deepcopy(day17)
    forged17["pendingReviews"][0]["semanticReview"] = "approved"
    rejected17 = build_report("2026-10-17",
        **(args | {"current_watch": forged17, "current_signed": signed17}))
    assert next(g for g in rejected17["gates"]
                if g["id"]=="country_source_classification")["status"]=="BLOCKED"

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
    # Synthetic approvals, never written to actual records: all other
    # technical/manual checks may pass, but absent exact 2026 Manufacturing
    # final online application files must independently BLOCK readiness.
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
    # M33 regression: even with synthetic valid official-source signoff,
    # a signed no-notice review and perfectly deployed 9/9 + 6/6 Pages,
    # absence of the exact 2026 Manufacturing final job-doc notice is fatal.
    assert next(g for g in hypothetical["gates"]
        if g["id"] == "kp2mi_manufacturing_release_day_signoff")["status"] == "PASS"
    assert next(g for g in hypothetical["gates"]
        if g["id"] == "exact_2026_manufacturing_final_job_documents")["status"] == "PENDING"
    assert hypothetical["liveDeploymentEvidenceChecked"] is True
    assert hypothetical["readyForManualLaunchDecision"] is False
    assert hypothetical["manualOpenDecisionStillRequired"] is True
    assert hypothetical["authorizesRelease"] is False
    # Critical-gate presence invariant: removing the documents gate must NEVER
    # make the remaining all-PASS list look release-ready (vacuous truth bug).
    test_required = {
        "route_safety", "country_source_classification", "official_monitor_today",
        "indonesia_source_manual_signoff", "kp2mi_manufacturing_release_day_signoff",
        "kp2mi_current_notice_index_observed",
        "exact_2026_manufacturing_final_job_documents", "optional_skill_annex_evidence",
        "published_main_source_integrity", "same_head_pages_deployment",
    }
    all_green_synthetic = copy.deepcopy(hypothetical["gates"])
    for entry in all_green_synthetic:
        if entry["id"] in test_required:
            entry["status"] = "PASS"
    assert required_gates_all_pass(all_green_synthetic, test_required) is True
    dropped_critical = [g for g in all_green_synthetic
                        if g["id"] != "exact_2026_manufacturing_final_job_documents"]
    assert required_gates_all_pass(dropped_critical, test_required) is False
    doubled_critical = all_green_synthetic + [copy.deepcopy(all_green_synthetic[0])]
    assert required_gates_all_pass(doubled_critical, test_required) is False
    blocked_critical = copy.deepcopy(all_green_synthetic)
    next(g for g in blocked_critical if g["id"] ==
         "exact_2026_manufacturing_final_job_documents")["status"] = "PENDING"
    assert required_gates_all_pass(blocked_critical, test_required) is False
    assert required_gates_all_pass([], test_required) is False
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
    print("ID_BETA_RELEASE_PREFLIGHT_SELF_TEST_PASS synthetic_SIGNOFF_AND_DEPLOY_still_BLOCKED_without_exact_2026_manufacturing_job_docs; manual_OPEN_remains_separate")


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
        "2026-10-17": ("research/source_reviews/indonesia_daily_readonly_2026-10-17.json",
                       "recruitment/ID_BETA_SOURCE_SIGNOFF_20261017.json"),
        "2026-10-18": ("research/source_reviews/indonesia_m39_oct18_preflight_technical_watch.json",
                       "recruitment/ID_BETA_SOURCE_SIGNOFF_20261017.json"),
    }
    selected = dated_evidence.get(as_of)
    latest_watch = read_json(selected[0]) if selected else None
    latest_signed = read_json(selected[1]) if selected else None
    current_notice = (read_json("research/source_reviews/indonesia_m40_oct18_notice_handoff.json")
                      if as_of == "2026-10-18" else None)
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
        current_notice=current_notice,
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
