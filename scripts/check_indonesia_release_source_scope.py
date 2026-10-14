#!/usr/bin/env python3
"""Read-only, fail-closed Indonesia-specific triage for the shared official-source watch.

This is a release planning aid. It never changes hashes, approvals, or beta access.
The global release gate must still pass independently.
"""
from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CRITICAL = {
    "labor_standards_wage_statement",
    "kdca_qcode_input",
    "moel_1350_contact",
}
OTHER_COUNTRY = {
    "np_eps_notice_index",
    "vn_colab_eps_notices",
    "lk_slbfe_home",
    "kg_migrant_home",
    "mm_mol_dol_index",
}


def load(path: str) -> dict:
    return json.loads((ROOT / path).read_text(encoding="utf-8-sig"))


def validate(status: dict, manifest: dict, scope: dict) -> tuple[int, int]:
    def ensure(condition: bool, message: str) -> None:
        if not condition:
            raise ValueError(message)

    all_sources = manifest.get("sources", [])
    by_id = {row.get("id"): row.get("url") for row in all_sources}
    ids = status.get("reviewRequiredSourceIds", [])
    urls = status.get("reviewRequiredUrls", [])
    records = scope.get("records", [])

    ensure(len(by_id) == len(all_sources), "official monitor IDs must be unique")
    ensure(scope.get("sourceWatchState") == status.get("state") == "review_required",
           "triage cannot claim clean status or change live source-watch state")
    ensure(status.get("autoPublishRules") is False, "source auto-publication prohibited")
    ensure(scope.get("monitorBaselineAccepted") is False, "hash baseline acceptance forbidden")
    ensure(scope.get("scopeReviewDoesNotApproveRelease") is True,
           "scope triage must never authorize beta release")
    ensure(scope.get("betaAccess") == "hold" and scope.get("manufacturingOnlineJobDocuments") == "job_docs_hold",
           "beta access and Manufacturing exact job documents must remain HOLD")
    ensure(scope.get("sourceWatchConfigured") == status.get("configured") == len(all_sources),
           "triage must match exact number of configured monitored sources")
    ensure(scope.get("sourceWatchChecked") == status.get("checked") == len(all_sources),
           "triage must match exact number of checked monitored sources")
    ensure(not status.get("fetchFailureUrls"), "source watch fetch failures require review")
    ensure(len(ids) == len(urls) == len(records), "all changed sources must be classified")
    ensure(len(ids) == len(set(ids)), "changed source IDs must be unique")
    ensure(set(ids) == {row.get("id") for row in records}, "changed sources must match triage records")
    ensure(set(ids) == CRITICAL | OTHER_COUNTRY,
           "new or missing changed sources must fail closed pending manual scope review")
    ensure(scope.get("kp2miManufacturingNoticeIndex", {}).get("status")
           == "correct_pengumuman_2026_inventory_read_pending_release_signoff",
           "2026 Pengumuman index review may not be represented as release approval")
    ensure(scope.get("kp2miManufacturingNoticeIndex", {}).get("checkedAt")
           == scope.get("checkedAt"), "index attempt date must match triage date")
    index = scope.get("kp2miManufacturingNoticeIndex", {})
    ensure(index.get("url") == "https://kp2mi.go.id/gtog-korea/pengumuman"
           and index.get("currentCategory") == "Pengumuman"
           and index.get("previouslyMistakenUrl") == "https://kp2mi.go.id/gtog-korea/info"
           and index.get("dataEndpoint") == "https://kp2mi.go.id/gtog-data/korea/Pengumuman"
           and index.get("complete2026IndexRead") is True
           and index.get("operatorConfirmedCompleteReview") is False
           and index.get("inspectedOffsets") == [0, 75, 150]
           and index.get("inspectedRows") == 225
           and index.get("reachedPreviousYear") is True,
           "index review evidence must match the real official 2026 list and remain unsigned")
    notice = index.get("competencyUploadNotice", {})
    ensure(notice.get("date") == "2026-09-17"
           and notice.get("optional") is True
           and notice.get("closed") is True
           and notice.get("notJobApplicationDocuments") is True
           and notice.get("url", "").startswith(
               "https://kp2mi.go.id/gtog-detail/korea/pengumuman-persyaratan-unggah-dokumen-kompetensi"),
           "2026 Manufacturing optional competency notice cannot be presented as job application documents")
    for id_, url in zip(ids, urls):
        ensure(by_id.get(id_) == url, f"{id_}: official source URL changed or is mismatched")
    for row in records:
        id_ = row["id"]
        ensure(row["sourceUrl"] == by_id[id_], f"{id_}: triage URL does not match monitored official URL")
        ensure(isinstance(row.get("notes"), str) and len(row["notes"]) >= 20,
               f"{id_}: reason is insufficient")
        if id_ in CRITICAL:
            ensure(row.get("routeScope") == "indonesia_korea_shared",
                   f"{id_}: Korea-common source cannot be classified out of Indonesia")
            ensure(row.get("reviewStatus") == "content_rechecked_scope_only",
                   f"{id_}: Korea-common official content has not been scope-reviewed")
            ensure(row.get("reviewedAt") == scope.get("checkedAt"),
                   f"{id_}: common source recheck date is stale")
        else:
            ensure(row.get("routeScope") == "other_country",
                   f"{id_}: foreign country notice scope must remain separate")
            ensure(row.get("reviewStatus") == "country_specific_review_pending"
                   and row.get("reviewedAt") is None,
                   f"{id_}: foreign country alert must retain pending status")
    return len(CRITICAL), len(OTHER_COUNTRY)


def self_test() -> None:
    manifest = {"sources": [{"id": x, "url": f"https://gov.example/{x}"}
                            for x in sorted(CRITICAL | OTHER_COUNTRY)]}
    ids = list(sorted(CRITICAL | OTHER_COUNTRY))
    status = {
        "state": "review_required", "autoPublishRules": False,
        "configured": len(ids), "checked": len(ids),
        "reviewRequiredSourceIds": ids,
        "reviewRequiredUrls": [f"https://gov.example/{x}" for x in ids],
        "fetchFailureUrls": [],
    }
    scope = {
        "sourceWatchState": "review_required", "monitorBaselineAccepted": False,
        "scopeReviewDoesNotApproveRelease": True, "betaAccess": "hold",
        "manufacturingOnlineJobDocuments": "job_docs_hold",
        "sourceWatchConfigured": len(ids), "sourceWatchChecked": len(ids),
        "checkedAt": "2026-10-14",
        "kp2miManufacturingNoticeIndex": {
            "status": "correct_pengumuman_2026_inventory_read_pending_release_signoff", "checkedAt": "2026-10-14",
            "url": "https://kp2mi.go.id/gtog-korea/pengumuman",
            "currentCategory": "Pengumuman",
            "previouslyMistakenUrl": "https://kp2mi.go.id/gtog-korea/info",
            "dataEndpoint": "https://kp2mi.go.id/gtog-data/korea/Pengumuman",
            "complete2026IndexRead": True, "operatorConfirmedCompleteReview": False,
            "inspectedOffsets": [0,75,150], "inspectedRows": 225,
            "reachedPreviousYear": True,
            "competencyUploadNotice": {
                "date": "2026-09-17", "optional": True, "closed": True,
                "notJobApplicationDocuments": True,
                "url": "https://kp2mi.go.id/gtog-detail/korea/pengumuman-persyaratan-unggah-dokumen-kompetensi-peserta-skill-test-ubt-umum-sektor-manufaktur-eps-topik-tahun-2026"
            }
        },
        "records": [
            {
                "id": x, "sourceUrl": f"https://gov.example/{x}",
                "routeScope": "indonesia_korea_shared" if x in CRITICAL else "other_country",
                "reviewStatus": "content_rechecked_scope_only" if x in CRITICAL
                                else "country_specific_review_pending",
                "reviewedAt": "2026-10-14" if x in CRITICAL else None,
                "notes": "This is a manually reviewed test scope classification.",
            } for x in ids
        ]
    }
    assert validate(status, manifest, scope) == (3, 5)
    for mutant in [
        lambda a, b, c: c["records"].pop(),
        lambda a, b, c: c["records"][0].update(routeScope="other_country"),
        lambda a, b, c: c.update(monitorBaselineAccepted=True),
        lambda a, b, c: c.update(betaAccess="open"),
        lambda a, b, c: c["kp2miManufacturingNoticeIndex"].update(status="verified"),
        lambda a, b, c: b["sources"][0].update(url="https://tampered.example"),
        lambda a, b, c: a["reviewRequiredSourceIds"].append("new_notice"),
    ]:
        a, b, c = copy.deepcopy(status), copy.deepcopy(manifest), copy.deepcopy(scope)
        mutant(a, b, c)
        try:
            validate(a, b, c)
        except ValueError:
            pass
        else:
            raise AssertionError("Unsafe mutation was accepted by source-scope triage")
    print("ID_SOURCE_SCOPE_SELF_TEST_PASS 7 fail-closed mutations")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return
    shared, foreign = validate(
        load("docs/data/source_review_status.json"),
        load("monitor/sources.json"),
        load("recruitment/ID_RELEASE_SOURCE_SCOPE_20261014.json"),
    )
    print(f"ID_SOURCE_SCOPE_TRIAGE_PASS shared_content_rechecked={shared} "
          f"other_country_pending={foreign} changed_total={shared+foreign}")
    print("ID_BETA_RELEASE_BLOCKED official-index-unverified / global-source-watch-review-required")
    print("No hashes accepted; no source state changed; no applicant action authorized")


if __name__ == "__main__":
    main()
