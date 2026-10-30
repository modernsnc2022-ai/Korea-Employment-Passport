#!/usr/bin/env python3
"""M24 fail-closed candidate/cohort separation against persisted official evidence."""
from __future__ import annotations
import argparse, copy, json
from pathlib import Path
from report_m24_kp2mi_live_scope import validate_packet
ROOT=Path(__file__).resolve().parents[1]
SNAP=ROOT/"research/source_reviews/indonesia_m24_manufacturing_title_scope_2026-10-17.json"
M21=ROOT/"research/source_reviews/indonesia_m21_original_html_audit_2026-10-17.json"
M23=ROOT/"research/source_reviews/indonesia_m23_pdf_lineage_2026-10-17.json"
WATCH=ROOT/"research/source_reviews/indonesia_daily_readonly_2026-10-17.json"
SIGN=ROOT/"recruitment/ID_BETA_SOURCE_SIGNOFF_20261017.json"

def read(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))

def demand(ok,msg):
    if not ok:raise ValueError("M24_JOBDOCS_RELEASE_HOLD_BLOCKED "+msg)

def verify(snapshot,m21,m23,watch,sign):
    validate_packet(snapshot)
    demand(snapshot["generalManufacturingTitlesCount"]==7
      and snapshot["generalManufacturingFinalOnlineJobApplicationTitleCount"]==0
      and snapshot["broadOnlineJobApplicationTitleCount"]==3
      and len(snapshot["otherCohortOnlineApplicationNotices"])==3
      and not snapshot["ambiguousGenericApplicationTitles"]
      and snapshot["manualTriageRequired"] is False,
      "exact cohort-group title set changed: manual review required")
    domain_set={row["url"] for row in snapshot["generalManufacturingTitles"]}
    recorded_set={row["url"] for row in m21["manufacturingNoticeHtml"]}
    demand(domain_set==recorded_set and len(domain_set)==7,
      "notice URL changed vs seven original HTML pages")
    demand({row["cohort"] for row in snapshot["otherCohortOnlineApplicationNotices"]}==
       {"fisheries","root_industry","special_ubt"},
       "one each other cohort")
    demand(m21["humanOfficialSemanticSignoff"] is False
        and m21["attachmentLinksTotal"]==24
        and m21["betaAccess"]=="hold","original contents unsigned")
    demand(m23["newlyFetchedPDFsWithOriginalSha256Match"]==6
       and m23["newlyUnverifiedPDFs"]==1
       and m23["finalGeneralManufacturingJobDocuments"]=="hold"
       and m23["publicBetaAccess"]=="hold"
       and m23["sourcePolicyHumanSignoff"] is False,"six old PDFs do not establish final docs")
    demand(watch["checked"]==84 and watch["fetchFailures"]==0
       and watch["unacceptedBaselineDriftCount"]==12
       and watch["observedAtDate"]=="2026-10-17","source watch")
    demand(sign["status"]=="pending_manual_source_signoff"
       and sign["reviewer"] is None and sign["approvedAt"] is None
       and sign["betaAccess"]=="hold"
       and sign["exactManufacturingJobDocumentsHeld"] is True,
       "human source approval boundary")
    demand(snapshot["exact2026ManufacturingFinalJobDocumentsVerified"] is False
       and snapshot["authorizesRelease"] is False
       and snapshot["baselineHashAutomaticallyAccepted"] is False,"no auto approval")
    return True

def selftest():
    seeds=[read(path) for path in [SNAP,M21,M23,WATCH,SIGN]]
    verify(*seeds)
    mutations=[
       lambda a:a[0].update(authorizesRelease=True),
       lambda a:a[0].update(betaAccess="open"),
       lambda a:a[0].update(exact2026ManufacturingFinalJobDocumentsVerified=True),
       lambda a:a[0].update(humanSemanticReviewApproved=True),
       lambda a:a[0].update(generalManufacturingFinalOnlineJobApplicationTitleCount=1),
       lambda a:a[0]["generalManufacturingTitles"].pop(),
       lambda a:a[0]["otherCohortOnlineApplicationNotices"][0].update(mustNotImportIntoGeneralManufacturing=False),
       lambda a:a[0]["otherCohortOnlineApplicationNotices"][0].update(cohort="general_manufacturing"),
       lambda a:a[0]["generalManufacturingTitles"][0].update(url="https://evil.invalid/notice"),
       lambda a:a[1]["manufacturingNoticeHtml"][0].update(url="https://evil.invalid/notice"),
       lambda a:a[2].update(finalGeneralManufacturingJobDocuments="verified"),
       lambda a:a[3].update(checked=83),
       lambda a:a[4].update(status="approved"),
    ]
    for mutation in mutations:
        data=copy.deepcopy(seeds);mutation(data)
        try:verify(*data)
        except (ValueError,KeyError,TypeError):pass
        else:raise AssertionError("unsafe M24 review/approval mutation passed")
    print("M24_FINAL_JOBDOCS_SCOPE_SELF_TEST_PASS 13_fail_closed_mutations 7_same_official_notices 3_other_cohorts 12_source_alerts beta_hold")

def main():
    cli=argparse.ArgumentParser()
    cli.add_argument("--self-test",action="store_true")
    cli.add_argument("--check",action="store_true")
    args=cli.parse_args()
    if args.self_test:selftest()
    if args.check:
        inputs=[read(p) for p in [SNAP,M21,M23,WATCH,SIGN]]
        verify(*inputs)
        print("M24_CROSS_EVIDENCE_SCOPE_PASS 7_manufacturing_HTML 3_excluded_other_cohorts 0_exact_final_jobdoc_titles 6_old_PDF_sha_verified JOBDOCS_HOLD_BETA_HOLD")
    if not args.self_test and not args.check:cli.error("choose --self-test or --check")
if __name__=="__main__":main()
