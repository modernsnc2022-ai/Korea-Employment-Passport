#!/usr/bin/env python3
"""M24 official notice-index boundary: live 2026 cohorts, title only, never signoff."""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import re
from zoneinfo import ZoneInfo

from audit_id_manufacturing_notice_index_live import retrieve, validate_snapshot
from audit_kp2mi_pengumuman_2026 import notice_from_row

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "research/source_reviews/indonesia_m24_manufacturing_title_scope_2026-10-17.json"
JAKARTA = ZoneInfo("Asia/Jakarta")
DAY = "2026-10-17"
COHORT = "Indonesia > Korea > E-9 > UBT Umum General Manufacturing 2026"
OTHER = {"fisheries":"PERIKANAN","root_industry":"ROOT INDUSTRY","special_ubt":"UBT KHUSUS"}

def demand(ok,why):
    if not ok:
        raise ValueError("M24_FINAL_JOB_DOCS_SCOPE_BLOCKED " + why)

def classify_other(title):
    upper = title.upper()
    groups = [k for k,term in OTHER.items() if term in upper]
    demand(len(groups)==1,"ambiguous other-cohort title")
    return groups[0]

def build(raw, check_day=DAY):
    stamp = datetime.fromisoformat(raw["checkedAtUtc"])
    observed=stamp.astimezone(JAKARTA).date().isoformat()
    demand(observed==check_day and check_day==DAY,"same-day Jakarta original official snapshot")
    demand(raw["titleOnlyIndex"] is True and raw["humanOperatorSignedOff"] is False
        and raw["exactFinalJobDocumentsVerified"] is False
        and raw["sourceBaselineAccepted"] is False
        and raw["betaReleaseAuthorized"] is False,"no source consent or beta")
    demand(raw["rowsInspected"]==320 and raw["totalHistoricalNotices"]>=320
        and "2026" in raw["newestPostedDate"] and "2025" in raw["oldestPostedDate"],"complete date boundary")
    demand(re.fullmatch("[0-9a-f]{64}",raw["titleUrlDigestSha256"]) is not None,
           "digest")
    main=raw["generalManufacturing2026Notices"]
    others=raw["otherCohortFinalOnlineApplicationNotices"]
    candidates=raw["generalManufacturingFinalApplicationCandidates"]
    generic=raw["ambiguousGenericJobApplicationTitleCandidates"]
    broad=raw["broadJobApplicationTitleCandidates"]
    demand(len({x["url"] for x in main})==len(main) and len(main)>0,
           "unique general manufacturing notices")
    demand(len({x["url"] for x in others})==len(others),"other cohort uniqueness")
    demand(len({x["url"] for x in candidates})==len(candidates),"candidate uniqueness")
    demand(len({x["url"] for x in generic})==len(generic),"ambiguous uniqueness")
    demand(raw["genericCandidateReviewRequired"] is bool(generic),"ambiguous flag")
    demand(len({x["url"] for x in broad})==len(broad),"broad title duplicates")
    known = {r["url"] for r in main}
    for row in main:
        demand(row["generalManufacturing2026"] is True and "2026" in row["date"]
               and row["url"].startswith("https://kp2mi.go.id/gtog-detail/korea/"),
               "manufacturing notice scope")
    for row in others:
        demand(row["otherCohortApplicationNotice"] is True
               and row["url"] not in known and "2026" in row["date"]
               and row["url"].startswith("https://kp2mi.go.id/gtog-detail/korea/"),
               "other cohort exclusion")
    for row in candidates:
        demand(row["generalManufacturingFinalApplicationCandidate"] is True
               and row["url"] in known,"2026 candidate must be in general group")
    for row in generic:
        demand(row["url"] not in {r["url"] for r in candidates}
               and row["url"] not in {r["url"] for r in others},"generic distinct")
    # Metadata classification does not establish documents absent from notice bodies/PDFs.
    separate=[{"date":r["date"],"title":r["title"],"url":r["url"],
               "cohort":classify_other(r["title"]),
               "mustNotImportIntoGeneralManufacturing":True} for r in others]
    return {
        "version":"1.0.0","observedAtJakartaDate":observed,
        "scope":COHORT,"sourceApi":raw["officialAjax"],
        "officialListingUrl":raw["correctOfficialIndex"],
        "observedAtUtc":raw["checkedAtUtc"],"recordsInspected":raw["rowsInspected"],
        "historicalRecordsTotal":raw["totalHistoricalNotices"],
        "firstDate":raw["newestPostedDate"],"boundaryDate":raw["oldestPostedDate"],
        "titleUrlDigestSha256":raw["titleUrlDigestSha256"],
        "generalManufacturingTitlesCount":len(main),
        "generalManufacturingTitles":[{"date":r["date"],"title":r["title"],"url":r["url"]}
                                      for r in main],
        "generalManufacturingFinalOnlineJobApplicationTitleCount":len(candidates),
        "generalManufacturingTitleCandidates":[{"date":r["date"],"title":r["title"],"url":r["url"]}
                                                  for r in candidates],
        "broadOnlineJobApplicationTitleCount":len(broad),
        "otherCohortOnlineApplicationNotices":separate,
        "ambiguousGenericApplicationTitles":[{"date":r["date"],"title":r["title"],"url":r["url"]}
                                              for r in generic],
        "manualTriageRequired":bool(candidates or generic),
        "titleOnlyEvidence":True,"all2026DetailedNoticeContentsRead":False,
        "allRelevantPdfContentsRead":False,
        "humanSemanticReviewApproved":False,"baselineHashAutomaticallyAccepted":False,
        "exact2026ManufacturingFinalJobDocumentsVerified":False,
        "jobDocs":"hold","betaAccess":"hold","authorizesRelease":False,
        "safety":"No title matching is proof of absence from HTML/PDF annexes. Fisheries, Root Industry and special UBT notices never import their job-document lists into General Manufacturing."
    }

def validate_packet(pkt):
    demand(pkt["observedAtJakartaDate"]==DAY and pkt["scope"]==COHORT,"scope/day")
    demand(pkt["recordsInspected"]==320 and pkt["historicalRecordsTotal"]>=320
           and re.fullmatch("[0-9a-f]{64}",pkt["titleUrlDigestSha256"]),"index completeness")
    demand(pkt["titleOnlyEvidence"] is True
       and pkt["all2026DetailedNoticeContentsRead"] is False
       and pkt["allRelevantPdfContentsRead"] is False
       and pkt["humanSemanticReviewApproved"] is False
       and pkt["baselineHashAutomaticallyAccepted"] is False
       and pkt["exact2026ManufacturingFinalJobDocumentsVerified"] is False
       and pkt["jobDocs"]=="hold" and pkt["betaAccess"]=="hold"
       and pkt["authorizesRelease"] is False,"no launch/signoff")
    demand(pkt["generalManufacturingTitlesCount"]==len(pkt["generalManufacturingTitles"])
       and pkt["generalManufacturingTitlesCount"]>=7,"general list")
    demand(pkt["generalManufacturingFinalOnlineJobApplicationTitleCount"]
         ==len(pkt["generalManufacturingTitleCandidates"]),"final candidates")
    demand(pkt["broadOnlineJobApplicationTitleCount"]>=
      len(pkt["otherCohortOnlineApplicationNotices"]),"all title candidates counted")
    for row in pkt["otherCohortOnlineApplicationNotices"]:
       demand(row["cohort"]==classify_other(row["title"])
          and row["mustNotImportIntoGeneralManufacturing"] is True,
          "cross cohort rule")
    demand(pkt["manualTriageRequired"] is bool(
       pkt["generalManufacturingTitleCandidates"] or pkt["ambiguousGenericApplicationTitles"]),
       "human triage")
    return True

def self_test():
    baseline={
        "checkedAtUtc":"2026-10-17T04:32:00+00:00",
        "titleOnlyIndex":True,"humanOperatorSignedOff":False,
        "exactFinalJobDocumentsVerified":False,"sourceBaselineAccepted":False,
        "betaReleaseAuthorized":False,"rowsInspected":320,"totalHistoricalNotices":2876,
        "newestPostedDate":"17 October 2026","oldestPostedDate":"16 July 2025",
        "titleUrlDigestSha256":"b"*64,
        "generalManufacturing2026Notices":[{
          "date":"17 September 2026","title":"2026 UBT UMUM MANUFAKTUR SKILL TEST",
          "url":"https://kp2mi.go.id/gtog-detail/korea/test",
          "generalManufacturing2026":True}],
        "otherCohortFinalOnlineApplicationNotices":[{
          "date":"19 August 2026","title":"LAMARAN ONLINE PERIKANAN 2026",
          "url":"https://kp2mi.go.id/gtog-detail/korea/fisheries",
          "otherCohortApplicationNotice":True}],
        "generalManufacturingFinalApplicationCandidates":[],
        "ambiguousGenericJobApplicationTitleCandidates":[],
        "broadJobApplicationTitleCandidates":[{
          "date":"19 August 2026","title":"LAMARAN ONLINE PERIKANAN 2026",
          "url":"https://kp2mi.go.id/gtog-detail/korea/fisheries"}],
        "genericCandidateReviewRequired":False,
        "officialAjax":"https://kp2mi.go.id/gtog-data/korea/Pengumuman",
        "correctOfficialIndex":"https://kp2mi.go.id/gtog-korea/pengumuman"
    }
    def clone():return json.loads(json.dumps(baseline))
    good=build(clone())
    demand(good["jobDocs"]=="hold" and good["otherCohortOnlineApplicationNotices"][0]["cohort"]=="fisheries","safe classifier")
    import copy
    mutations=[
      lambda a:a.update(humanOperatorSignedOff=True),
      lambda a:a.update(exactFinalJobDocumentsVerified=True),
      lambda a:a.update(betaReleaseAuthorized=True),
      lambda a:a.update(rowsInspected=319),
      lambda a:a.update(oldestPostedDate="16 July 2026"),
      lambda a:a["otherCohortFinalOnlineApplicationNotices"][0].update(title="AMBIGUOUS ROLE"),
      lambda a:a["otherCohortFinalOnlineApplicationNotices"][0].update(url="https://evil.com/a"),
      lambda a:a.update(genericCandidateReviewRequired=True),
    ]
    for change in mutations:
        test=clone();change(test)
        try:build(test)
        except (ValueError,KeyError):pass
        else:raise AssertionError("M24 unsafe live index accepted")
    print("M24_LIVE_TITLE_SCOPE_SELF_TEST_PASS 8_fail_closed_cases")

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--self-test",action="store_true")
    ap.add_argument("--write",action="store_true")
    args=ap.parse_args()
    if args.self_test:self_test()
    if args.write:
        day=datetime.now(timezone.utc).astimezone(JAKARTA).date().isoformat()
        demand(day==DAY,"not today's release-day observation")
        demand(not OUTPUT.exists(),"append-only output exists")
        rows,total=retrieve()
        raw=validate_snapshot(rows,total,checked_at=datetime.now(timezone.utc).isoformat())
        packet=build(raw);validate_packet(packet)
        OUTPUT.write_text(json.dumps(packet,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
        print("M24_KP2MI_LIVE_TITLE_SCOPE_PASS rows="+str(packet["recordsInspected"])
            +" general="+str(packet["generalManufacturingTitlesCount"])
            +" manufacturing_final_titles="+str(packet["generalManufacturingFinalOnlineJobApplicationTitleCount"])
            +" other_cohort="+str(len(packet["otherCohortOnlineApplicationNotices"]))
            +" ambiguous="+str(len(packet["ambiguousGenericApplicationTitles"]))
            +" JOBDOCS_HOLD BETA_HOLD NO_HUMAN_SIGNOFF")
    if not args.self_test and not args.write:ap.error("use --self-test or --write")

if __name__=="__main__":main()
