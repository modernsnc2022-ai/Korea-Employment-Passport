#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

from check_indonesia_source_signoff import validate_scoped_signoff
from check_20261015_source_signoff import validate_signoff as validate_current_signoff
from report_indonesia_beta_release_preflight import deployment_verified

ROOT = Path(__file__).resolve().parents[1]
PROGRAM = ROOT / "docs" / "data" / "beta_program_v1.json"
SOURCE = ROOT / "docs" / "data" / "source_review_status.json"
MANUFACTURING_CHECK = ROOT / "recruitment" / "MANUFACTURING_LAUNCH_CHECK.json"
OUTREACH = ROOT / "recruitment" / "OUTREACH_ID.md"


def fail(message: str) -> None:
    raise ValueError(message)


def prepare_open(
    program: dict, source: dict, manufacturing_check: dict, approved_at: str,
    *, source_manifest: dict | None = None, source_scope: dict | None = None,
    source_signoff: dict | None = None, deployment: dict | None = None,
    release_head: str | None = None, current_watch: dict | None = None,
    current_signed: dict | None = None,
) -> dict:
    if program.get("status") != "hold":
        fail("public beta can be opened only from HOLD")
    release = program.get("releaseDecision", {})
    if release.get("publicBeta") != "pending_manual_approval":
        fail("release decision is not pending manual approval")
    try:
        approved_dt = datetime.fromisoformat(approved_at.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("approved-at must use timezone-aware ISO-8601 datetime") from exc
    if approved_dt.tzinfo is None:
        fail("approved-at must include timezone")

    if source.get("state") == "clean":
        if source.get("configured") != source.get("checked"):
            fail("globally clean official sources require every configured source fetched")
        if source.get("fetchFailureUrls") or source.get("reviewRequiredUrls"):
            fail("globally clean official sources cannot contain pending alerts or failures")
    else:
        if source_manifest is None:
            fail("official source state must be clean or have signed Indonesia-scope approval and current inventory")
        try:
            if current_watch is not None:
                # A recorded 2026-10-15 4+1+5 watch MUST have its own signed
                # operator approval, not the superseded 3+5 dated signature.
                if current_signed is None:
                    fail("current official source signature is missing")
                validate_current_signoff(
                    current_watch, source_manifest, current_signed,
                    approved_dt.date().isoformat(),
                )
            else:
                if approved_dt.date().isoformat() >= "2026-10-15":
                    fail("legacy eight-alert source scope is superseded; current dated signoff required")
                if not (source_scope and source_signoff):
                    fail("official source state must be clean or have signed Indonesia-scope approval")
                validate_scoped_signoff(
                    source, source_manifest, source_scope, source_signoff,
                    approved_dt.date().isoformat(),
                )
        except ValueError as exc:
            fail(str(exc))

    coverage = manufacturing_check.get("noticeIndexCoverage", {})
    inventory_url = str(coverage.get("officialManufacturingInventoryUrl") or "")
    parsed = urlparse(inventory_url)
    index_path = parsed.path.lower()
    if not (
        coverage.get("status") == "verified_complete_general_manufacturing_index_review"
        and coverage.get("completeGeneralManufacturingInventory") is True
        and coverage.get("operatorConfirmedCompleteReview") is True
        and coverage.get("checkedAt") == approved_dt.date().isoformat()
        and parsed.scheme == "https"
        and parsed.hostname in {"kp2mi.go.id", "www.kp2mi.go.id"}
        and index_path.rstrip("/") == "/gtog-korea/pengumuman"
        and not parsed.query and not parsed.fragment
    ):
        fail("complete current KP2MI Manufacturing announcement inventory requires same-day official source review and explicit coverage signoff; Preliminary Training is not sufficient")
    if manufacturing_check.get("checkedAt") != approved_dt.date().isoformat():
        fail("Manufacturing launch check must be recorded on the same date as OPEN approval")
    if manufacturing_check.get("result") != "no_current_manufacturing_job_application_notice":
        fail(
            "Manufacturing launch check found/requires review of a notice; "
            "do not OPEN until route rules and launch checks are updated"
        )
    if manufacturing_check.get("heldQuestions") != ["job_docs"]:
        fail("Manufacturing launch check must preserve the one unresolved exact HOLD: job_docs")
    expected_baselines = {"job_scan", "job_name", "job_edit", "job_submit"}
    baselines = manufacturing_check.get("safePlatformBaselines", [])
    if (
        not isinstance(baselines, list)
        or len(baselines) != 4
        or {x.get("questionId") for x in baselines if isinstance(x, dict)}
        != expected_baselines
    ):
        fail("Four separately verified safe platform baselines must remain present")
    same_day = manufacturing_check.get("sameDayOfficialRecheck", {})
    if (
        same_day.get("checkedAt") != approved_dt.date().isoformat()
        or same_day.get("status") != "completed_no_detailed_manufacturing_notice_found"
    ):
        fail("Manufacturing same-day official recheck record must match OPEN approval")

    # Official/manual source signoff alone must never bypass live deployment
    # parity. Only the CLI's live six-redirect/nine-asset HTTPS audit supplies
    # actual evidence, not a user-editable JSON flag.
    if not deployment_verified(deployment, release_head):
        fail("same-HEAD live Pages proof is required: 6/6 secure HTTPS entrypoints "
             "and 9/9 public assets must match the reviewed Git HEAD")

    updated = json.loads(json.dumps(program))
    updated["status"] = "open"
    updated.setdefault("releaseDecision", {})["publicBeta"] = "approved_manual"
    updated["releaseDecision"]["approvedAt"] = approved_at
    return updated


def outreach_open_text(text: str) -> str:
    if "Application intake status: **OPEN**" not in text:
        fail("OUTREACH_ID.md must keep application intake OPEN")
    if "Beta access status: **HOLD" not in text:
        fail("OUTREACH_ID.md does not contain the expected beta-access HOLD marker")
    return text.replace(
        "Beta access status: **HOLD",
        "Beta access status: **OPEN",
        1,
    )


def self_test() -> None:
    program = {
        "status": "hold",
        "releaseDecision": {
            "publicBeta": "pending_manual_approval",
            "approvedAt": None,
        },
    }
    source = {
        "state": "clean",
        "configured": 72,
        "checked": 72,
        "reviewRequiredUrls": [],
        "fetchFailureUrls": [],
    }
    manufacturing_check = {
        "checkedAt": "2026-10-04",
        "noticeIndexCoverage": {
            "status": "verified_complete_general_manufacturing_index_review",
            "checkedAt": "2026-10-04",
            "officialManufacturingInventoryUrl": "https://kp2mi.go.id/gtog-korea/pengumuman",
            "completeGeneralManufacturingInventory": True,
            "operatorConfirmedCompleteReview": True,
        },
        "result": "no_current_manufacturing_job_application_notice",
        "heldQuestions": ["job_docs"],
        "safePlatformBaselines": [
            {"questionId": x} for x in ["job_scan", "job_name", "job_edit", "job_submit"]
        ],
        "sameDayOfficialRecheck": {
            "status": "completed_no_detailed_manufacturing_notice_found",
            "checkedAt": "2026-10-04",
        },
    }
    approved_at = "2026-10-04T18:30:00+09:00"
    from audit_indonesia_beta_pages_live import ASSETS, LEGACY_ENTRYPOINTS
    release_head = "a" * 40
    fake_deployment = {
        "mode": "read_only", "authorizesRelease": False,
        "checkedRef": release_head, "httpsEntrypointSafe": True,
        "criticalAssetsSameRef": True,
        "matchingAssets": len(ASSETS), "totalAssets": len(ASSETS),
        "entrypoints": [{"id": name, "httpsOnly": True}
                        for name, _, _ in LEGACY_ENTRYPOINTS],
        "assets": [
            {"path": name, "httpsOnly": True, "status": 200,
             "sameAsCheckedRef": True, "liveSha256": "0" * 64,
             "expectedSha256": "0" * 64}
            for name in ASSETS
        ],
    }
    opened = prepare_open(program, source, manufacturing_check, approved_at,
                          deployment=fake_deployment, release_head=release_head)
    assert opened["status"] == "open"
    assert opened["releaseDecision"]["publicBeta"] == "approved_manual"
    assert opened["releaseDecision"]["approvedAt"] == approved_at
    # Missing, wrong-HEAD, stale or insecure live results must block even if
    # official human approvals have been synthetically fulfilled in memory.
    try:
        prepare_open(program, source, manufacturing_check, approved_at)
    except ValueError as exc:
        assert "same-HEAD live Pages" in str(exc)
    else:
        raise AssertionError("beta OPEN permitted without live deployed-HEAD proof")
    from copy import deepcopy
    for mutation in (
        lambda a: a.update(checkedRef="b" * 40),
        lambda a: a["entrypoints"][1].update(httpsOnly=False),
        lambda a: a["assets"][0].update(liveSha256="1" * 64),
        lambda a: a.update(matchingAssets=8),
    ):
        bad_proof = deepcopy(fake_deployment)
        mutation(bad_proof)
        try:
            prepare_open(program, source, manufacturing_check, approved_at,
                         deployment=bad_proof, release_head=release_head)
        except ValueError as exc:
            assert "same-HEAD live Pages" in str(exc)
        else:
            raise AssertionError("beta OPEN permitted with invalid deployed-HEAD proof")

    incomplete_index = json.loads(json.dumps(manufacturing_check))
    incomplete_index["noticeIndexCoverage"]["status"] = "unverified_preliminary_training_category_only"
    incomplete_index["noticeIndexCoverage"]["completeGeneralManufacturingInventory"] = False
    try:
        prepare_open(program, source, incomplete_index, approved_at)
    except ValueError as exc:
        assert "complete current KP2MI" in str(exc)
    else:
        raise AssertionError("OPEN permitted with unverified Preliminary Training index")
    bad_index_url = json.loads(json.dumps(manufacturing_check))
    bad_index_url["noticeIndexCoverage"]["officialManufacturingInventoryUrl"] = (
        "https://kp2mi.go.id/gtog-korea/info"
    )
    try:
        prepare_open(program, source, bad_index_url, approved_at)
    except ValueError as exc:
        assert "Preliminary Training" in str(exc)
    else:
        raise AssertionError("OPEN permitted when the only index is Preliminary Training")
    bad_source = dict(source)
    bad_source["state"] = "review_required"
    try:
        prepare_open(program, bad_source, manufacturing_check, approved_at)
    except ValueError as exc:
        assert "must be clean" in str(exc)
    else:
        raise AssertionError("OPEN was allowed with non-clean official-source state")

    try:
        prepare_open(program, source, manufacturing_check, "2026-10-04T18:30:00")
    except ValueError as exc:
        assert "include timezone" in str(exc)
    else:
        raise AssertionError("OPEN was allowed without an approval timezone")

    stale_check = dict(manufacturing_check)
    stale_check["checkedAt"] = "2026-10-03"
    try:
        prepare_open(program, source, stale_check, approved_at)
    except ValueError as exc:
        assert "same date" in str(exc)
    else:
        raise AssertionError("OPEN was allowed with a stale Manufacturing launch check")

    found_check = dict(manufacturing_check)
    found_check["result"] = "notice_found_review_required"
    try:
        prepare_open(program, source, found_check, approved_at)
    except ValueError as exc:
        assert "requires review" in str(exc)
    else:
        raise AssertionError("OPEN was allowed after a Manufacturing notice was found")

    stale_recheck = json.loads(json.dumps(manufacturing_check))
    stale_recheck["sameDayOfficialRecheck"]["checkedAt"] = "2026-10-03"
    try:
        prepare_open(program, source, stale_recheck, approved_at)
    except ValueError as exc:
        assert "same-day official recheck" in str(exc)
    else:
        raise AssertionError("OPEN was allowed with stale nested same-day evidence")

    obsolete_holds = dict(manufacturing_check)
    obsolete_holds["heldQuestions"] = [
        "job_docs", "job_scan", "job_name", "job_edit", "job_submit"
    ]
    try:
        prepare_open(program, source, obsolete_holds, approved_at)
    except ValueError as exc:
        assert "one unresolved exact HOLD" in str(exc)
    else:
        raise AssertionError("OPEN was allowed with obsolete five-HOLD logic")

    missing_baseline = dict(manufacturing_check)
    missing_baseline["safePlatformBaselines"] = []
    try:
        prepare_open(program, source, missing_baseline, approved_at)
    except ValueError as exc:
        assert "Four separately verified" in str(exc)
    else:
        raise AssertionError("OPEN was allowed without four safe baselines")

    # Integration-only: simulate a future explicit Indonesia-only source
    # signoff in memory. This MUST NOT update the actual PENDING signoff,
    # Manufacturing launch check, official hashes or beta status.
    from check_indonesia_source_signoff import data as load_source_data
    from copy import deepcopy
    day = "2026-10-14"
    global_source = load_source_data("docs/data/source_review_status.json")
    global_source["detectedAt"] = day  # simulated same-day watcher only
    manifest = load_source_data("monitor/sources.json")
    scope = load_source_data("recruitment/ID_RELEASE_SOURCE_SCOPE_20261014.json")
    signoff = load_source_data("recruitment/ID_BETA_SOURCE_SIGNOFF.json")
    assert signoff["status"] in {"pending_manual_source_signoff", "approved_manual_indonesia_scope"}
    signed = deepcopy(signoff)
    signed.update({
        "status": "approved_manual_indonesia_scope",
        "reviewer": "Synthetic release operator",
        "approvedAt": day + "T17:30:00+09:00",
        "sourceSnapshotDate": day,
        "sourceScopeDate": day,
    })
    same_day_check = deepcopy(manufacturing_check)
    same_day_check["checkedAt"] = day
    same_day_check["noticeIndexCoverage"]["checkedAt"] = day
    same_day_check["sameDayOfficialRecheck"]["checkedAt"] = day
    fake_timestamp = day + "T18:00:00+09:00"
    scoped_open = prepare_open(
        program, global_source, same_day_check, fake_timestamp,
        source_manifest=manifest, source_scope=scope, source_signoff=signed,
        deployment=fake_deployment, release_head=release_head,
    )
    assert scoped_open["status"] == "open"
    for field, wrong in [
        ("status", "pending_manual_source_signoff"),
        ("sourceSnapshotDate", "2026-10-13"),
    ]:
        bad_signed = deepcopy(signed)
        bad_signed[field] = wrong
        try:
            prepare_open(
                program, global_source, same_day_check, fake_timestamp,
                source_manifest=manifest, source_scope=scope,
                source_signoff=bad_signed,
            )
        except ValueError as exc:
            assert "ID_SOURCE_RELEASE_BLOCKED" in str(exc)
        else:
            raise AssertionError("invalid country-scoped signoff permitted beta OPEN")
    # Additional current 2026-10-15 signed-source path. These synthetic
    # approvals live ONLY inside this test and never alter real approval JSON.
    current_watch = load_source_data("research/source_reviews/shared_source_watch_readonly_2026-10-15.json")
    pending_current = load_source_data("recruitment/ID_BETA_SOURCE_SIGNOFF_20261015.json")
    new_day = "2026-10-15"
    current_check = deepcopy(manufacturing_check)
    current_check["checkedAt"] = new_day
    current_check["noticeIndexCoverage"]["checkedAt"] = new_day
    current_check["sameDayOfficialRecheck"]["checkedAt"] = new_day
    new_stamp = new_day + "T15:00:00+07:00"
    valid_current = deepcopy(pending_current)
    valid_current.update(
        status="approved_manual_indonesia_scope",
        reviewer="Synthetic Operator QA", approvedAt=new_day + "T14:00:00+07:00",
        sourceSnapshotDate=new_day, sourceScopeDate=new_day,
    )
    validated = prepare_open(
        program, global_source, current_check, new_stamp,
        source_manifest=manifest, current_watch=current_watch,
        current_signed=valid_current, deployment=fake_deployment,
        release_head=release_head,
    )
    assert validated["status"] == "open"
    for invalid_current in (pending_current, {**valid_current, "contentReviewedSourceIds": [
        "labor_standards_wage_statement", "kdca_qcode_input", "moel_1350_contact"
    ]}):
        try:
            prepare_open(
                program, global_source, current_check, new_stamp,
                source_manifest=manifest, current_watch=current_watch,
                current_signed=invalid_current, deployment=fake_deployment,
                release_head=release_head,
            )
        except ValueError as exc:
            assert "ID_CURRENT_SOURCE_SIGNOFF_BLOCKED" in str(exc)
        else:
            raise AssertionError("new ten-alert source approval was bypassed")
    try:
        prepare_open(
            program, global_source, current_check, new_stamp,
            source_manifest=manifest, source_scope=scope,
            source_signoff=signed, deployment=fake_deployment,
            release_head=release_head,
        )
    except ValueError as exc:
        assert "legacy eight-alert source scope is superseded" in str(exc)
    else:
        raise AssertionError("legacy eight-alert signature permitted current beta OPEN")
    print("BETA_CURRENT_TEN_ALERT_SIGNOFF_GUARD_SELF_TEST_PASS")
    print("BETA_SCOPED_SOURCE_SYNTHETIC_INTEGRATION_TEST_PASS")

    changed = outreach_open_text(
        "Application intake status: **OPEN**\n"
        "Beta access status: **HOLD until gate passes.**"
    )
    assert "Application intake status: **OPEN**" in changed
    assert "Beta access status: **OPEN" in changed
    print("BETA_RELEASE_STATE_SELF_TEST_PASS deployed_head_proof_mutations_fail_closed")


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Prepare the explicit public-beta HOLD -> OPEN release-state change. "
            "This does not bypass same-HEAD CI or the required manual decision."
        )
    )
    parser.add_argument("--approved-at")
    parser.add_argument(
        "--confirm-open",
        action="store_true",
        help="Required explicit operator confirmation for the OPEN transition.",
    )
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    if args.self_test:
        self_test()
        return 0

    if not args.confirm_open:
        raise SystemExit("BETA_RELEASE_BLOCKED --confirm-open is required")
    if not args.approved_at:
        parser.error("--approved-at is required")

    program = json.loads(PROGRAM.read_text(encoding="utf-8-sig"))
    source = json.loads(SOURCE.read_text(encoding="utf-8-sig"))
    manufacturing_check = json.loads(MANUFACTURING_CHECK.read_text(encoding="utf-8-sig"))
    source_manifest = json.loads((ROOT / "monitor/sources.json").read_text(encoding="utf-8-sig"))
    source_scope = json.loads((ROOT / "recruitment/ID_RELEASE_SOURCE_SCOPE_20261014.json").read_text(encoding="utf-8-sig"))
    source_signoff = json.loads((ROOT / "recruitment/ID_BETA_SOURCE_SIGNOFF.json").read_text(encoding="utf-8-sig"))
    approval_day = datetime.fromisoformat(str(args.approved_at).replace("Z", "+00:00")).date().isoformat()
    current_watch = (json.loads((ROOT / "research/source_reviews/shared_source_watch_readonly_2026-10-15.json").read_text(encoding="utf-8-sig"))
                     if approval_day == "2026-10-15" else None)
    current_signed = (json.loads((ROOT / "recruitment/ID_BETA_SOURCE_SIGNOFF_20261015.json").read_text(encoding="utf-8-sig"))
                      if current_watch is not None else None)
    outreach = OUTREACH.read_text(encoding="utf-8")

    # First validate cheap approval guards. A deliberate missing deployment
    # proof is the only expected error at this point; any other issue blocks.
    try:
        prepare_open(
            program, source, manufacturing_check, str(args.approved_at),
            source_manifest=source_manifest, source_scope=source_scope,
            source_signoff=source_signoff,
            current_watch=current_watch, current_signed=current_signed,
        )
    except ValueError as exc:
        if "same-HEAD live Pages proof is required" not in str(exc):
            raise SystemExit("BETA_RELEASE_BLOCKED " + str(exc)) from exc

    # A Draft, dirty checkout or out-of-date local main is never valid for
    # final beta OPEN even when the underlying tests were previously green.
    branch_name = subprocess.check_output(
        ["git", "-C", str(ROOT), "branch", "--show-current"], text=True
    ).strip()
    if branch_name != "main":
        raise SystemExit("BETA_RELEASE_BLOCKED state write requires checked-out main")
    if subprocess.check_output(
        ["git", "-C", str(ROOT), "status", "--porcelain"], text=True
    ).strip():
        raise SystemExit("BETA_RELEASE_BLOCKED release checkout must be clean")
    release_head = subprocess.check_output(
        ["git", "-C", str(ROOT), "rev-parse", "HEAD"], text=True
    ).strip()
    remote_line = subprocess.check_output(
        ["git", "-C", str(ROOT), "ls-remote", "--heads", "origin", "main"],
        text=True, timeout=25
    ).split()
    if len(remote_line) != 2 or remote_line[0] != release_head:
        raise SystemExit("BETA_RELEASE_BLOCKED HEAD differs from remote origin/main")

    # Read-only live proof is never loaded from a forgeable JSON file.
    from audit_indonesia_beta_pages_live import audit, http_first_hop

    def committed_blob(name: str) -> bytes:
        return subprocess.check_output(
            ["git", "-C", str(ROOT), "show", "HEAD:docs/" + name]
        )

    try:
        live_proof = audit(
            http_first_hop, ROOT / "docs", release_head,
            asset_loader=committed_blob
        )
        updated_program = prepare_open(
            program, source, manufacturing_check, str(args.approved_at),
            source_manifest=source_manifest, source_scope=source_scope,
            source_signoff=source_signoff,
            current_watch=current_watch, current_signed=current_signed,
            deployment=live_proof, release_head=release_head,
        )
        updated_outreach = outreach_open_text(outreach)
    except (OSError, ValueError) as exc:
        raise SystemExit("BETA_RELEASE_BLOCKED " + str(exc)) from exc

    print(
        "BETA_RELEASE_DRY_RUN "
        f"status={updated_program['status']} "
        f"decision={updated_program['releaseDecision']['publicBeta']} "
        f"approved_at={updated_program['releaseDecision']['approvedAt']}"
    )
    print("SAME_HEAD_LIVE_PROOF VERIFIED six HTTPS redirects and nine exact live assets")
    print("FILE_STAGE_ONLY: OPEN commit must be separately deployed and reverified; "
          "this command does not deploy or grant remote applicant access")

    if not args.write:
        print("DRY_RUN_ONLY no release files were changed")
        return 0

    PROGRAM.write_text(
        json.dumps(updated_program, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    OUTREACH.write_text(updated_outreach, encoding="utf-8")
    print("BETA_RELEASE_FILES_STAGED_NOT_DEPLOYED public_beta_access=open "
          "application_intake=open POST_WRITE_DEPLOYMENT_RECHECK_REQUIRED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
