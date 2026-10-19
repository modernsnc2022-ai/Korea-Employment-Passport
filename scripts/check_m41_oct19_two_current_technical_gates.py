#!/usr/bin/env python3
"""M41 Oct19 original official source watch to TWO separate technical gates.

Authenticity scope: validated archived read-only fetch observation, not
human source interpretation, official employment documents, or beta approval.
"""
from __future__ import annotations
import argparse,copy,hashlib,json
from datetime import date,datetime,timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
DAY="2026-10-19"
RAW=ROOT/"research/source_reviews/indonesia_m41_oct19_original_source_watch.json"
INDEX=ROOT/"research/source_reviews/indonesia_m40_oct19_live_official_notice_titles.json"
M40=ROOT/"research/source_reviews/indonesia_m40_oct18_notice_handoff.json"
M34=ROOT/"research/source_reviews/indonesia_m34_unsigned_release_review_packet_2026-10-17.json"
OUT=ROOT/"research/source_reviews/indonesia_m41_oct19_technical_release_bridge.json"
def read(path):return json.loads(path.read_text(encoding="utf-8-sig"))
def check(v,why):
    if not v:raise ValueError("M41_FAIL_CLOSED "+why)
def blobhash(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def build():
    raw,head,prior,human=map(read,(RAW,INDEX,M40,M34))
    manifest=read(ROOT/"monitor/sources.json")
    configured=manifest["sources"]
    ids={x["id"] for x in configured}
    check(len(configured)==len(ids)==84,"84 distinct source manifest identities")
    check(raw["configured"]==84 and type(raw["checked"]) is int
       and 0<=raw["checked"]<=84 and not raw["acceptedCurrent"]
       and not raw["reviewManifestAccepted"] and not raw["initialized"]
       and not raw["partialAcceptance"],"read-only unaccepted official watch")
    failures=raw["failures"]
    changes=raw["changed"]
    fids=[x["id"] for x in failures]
    cids=[x["id"] for x in changes]
    check(len(set(fids))==len(fids) and len(set(cids))==len(cids)
       and set(cids+fids).issubset(ids),"no fake or duplicate official source identifiers")
    check(head["asOfJakarta"]==DAY and
       datetime.fromisoformat(head["observedAtUtc"].replace("Z","+00:00")).date().isoformat()==DAY
       and head["rowsInspected"]==320
       and head["generalManufacturing2026NoticeCount"]==7
       and head["finalManufacturing2026ApplicationTitleCandidates"]==0
       and head["ambiguousGenericApplicationTitleCandidates"]==0
       and head["releaseAuthorized"] is False and head["betaAccess"]=="hold",
       "real current-day KP2MI title-index original")
    check(head["titleUrlSha256"]==read(ROOT/
       "research/source_reviews/indonesia_m34_unsigned_release_review_packet_2026-10-17.json")["officialTitleUrlSha256"],
       "current title digest differs from exact verified prior notice scope")
    check(prior["kind"]=="unsigned_current_day_official_notice_reviewer_binding"
       and prior["observationDayJakarta"]=="2026-10-18"
       and prior["kp2miTitlesChecked"]==320
       and len(prior["kp2miManufacturingNotices"])==7
       and prior["humanNoticeContentsSigned"] is False
       and prior["final2026ManufacturingJobDocumentsVerified"] is False
       and prior["betaAccess"]=="hold", "unsigned previous original notice tasks")
    notices=human["reviewTasks"]
    review={x["taskId"]:x for x in notices}
    check(human["pendingReviewTasks"]==20
      and all(t["semanticDecision"]=="pending" and
              t["reviewerName"] is None for t in notices)
      and {x["taskId"] for x in prior["kp2miManufacturingNotices"]}<=set(review),
      "M34 20 actual unsigned human tasks")
    scopes={r["taskId"][4:]:r["scope"] for r in notices
            if r["taskId"].startswith("SRC:")}
    count={"korea_shared":0,"multi_country_eps_schedule":0,
      "other_country":0,"unclassified_requires_manual_scope_review":0}
    for sid in cids:
        group=scopes.get(sid)
        if group in count and group!="unclassified_requires_manual_scope_review":
            count[group]+=1
        else:
            count["unclassified_requires_manual_scope_review"]+=1
    technicalComplete=raw["checked"]==84 and len(failures)==0 and count[
         "unclassified_requires_manual_scope_review"]==0
    return {
      "kind":"M41_UNAPPROVED_SOURCE_AND_NOTICE_RELEASE_EVIDENCE",
      "day":DAY,
      "watch":{
        "version":"1.0.0","kind":"m41_oct19_machine_only_current_watch",
        "observedAtDate":DAY,"configured":84,"checked":raw["checked"],
        "fetchFailures":len(fids),"failedSourceIds":sorted(fids),
        "unacceptedBaselineDriftCount":len(cids),
        "pendingAlertSourceIds":sorted(cids),"groupCounts":count,
        "observedSourceRawSha256":blobhash(RAW),
        "completeOfficialTechnicalRead":technicalComplete,
        "sourceHashAutoAccepted":False,"humanSourcePolicyApproved":False,
        "signedCurrentDayReleaseEvidence":False,
        "manualFinal2026ManufacturingDocumentsApproved":False,
        "productionDeploymentApproved":False,"publicBetaAccess":"hold",
        "releaseAuthorized":False
      },
      "notice":{
        "kind":"m41_oct19_current_kp2mi_notice_index_machine_only",
        "observedAtDate":DAY,"indexRawSha256":blobhash(INDEX),
        "originalIndexUrl":head["officialIndex"],
        "titleUrlSha256":head["titleUrlSha256"],
        "titlesChecked":head["rowsInspected"],
        "sevenOriginalNoticeTaskIds":sorted(x["taskId"] for x in prior["kp2miManufacturingNotices"]),
        "hrdScheduleTaskIds":sorted(x["examNo"] for x in prior["HRDKoreaScheduleObservations"]),
        "finalManufacturing2026ApplicationTitleCandidates":0,
        "humanNoticeContentsSigned":False,"exactFinalJobDocumentsVerified":False,
        "betaAccess":"hold","releaseAuthorized":False
      },
      "all20HumanTasksStillUnsigned":True,
      "final2026GeneralManufacturingJobDocs":"hold",
      "candidateHeadDeployment":"unverified",
      "publicBetaAccess":"hold","releaseAuthorized":False
    }
def validate(packet,manifest):
    check(packet==build(),"committed original raw source and notice hashes/contents are exact")
    w,n=packet["watch"],packet["notice"]
    check(len(manifest["sources"])==84 and
       {x["id"] for x in manifest["sources"]}=={
           x["id"] for x in read(ROOT/"monitor/sources.json")["sources"]},
       "source manifest check")
    check(w["observedAtDate"]==DAY and w["configured"]==84
       and w["fetchFailures"]==len(w["failedSourceIds"])
       and w["unacceptedBaselineDriftCount"]==len(w["pendingAlertSourceIds"])
       and w["completeOfficialTechnicalRead"] == (
         w["checked"]==84 and w["fetchFailures"]==0 and
         w["groupCounts"]["unclassified_requires_manual_scope_review"]==0),
       "never claim complete on partial fetch")
    check(n["observedAtDate"]==DAY and n["titlesChecked"]==320
       and len(n["sevenOriginalNoticeTaskIds"])==7
       and len(n["hrdScheduleTaskIds"])==2
       and n["finalManufacturing2026ApplicationTitleCandidates"]==0,
       "title listing doesn't certify official final docs")
    check(w["sourceHashAutoAccepted"] is False and
       w["humanSourcePolicyApproved"] is False and
       w["signedCurrentDayReleaseEvidence"] is False and
       w["manualFinal2026ManufacturingDocumentsApproved"] is False
       and w["productionDeploymentApproved"] is False and
       w["publicBetaAccess"]=="hold" and w["releaseAuthorized"] is False
       and n["humanNoticeContentsSigned"] is False
       and n["exactFinalJobDocumentsVerified"] is False
       and n["betaAccess"]=="hold" and n["releaseAuthorized"] is False
       and packet["all20HumanTasksStillUnsigned"] is True
       and packet["final2026GeneralManufacturingJobDocs"]=="hold"
       and packet["candidateHeadDeployment"]=="unverified"
       and packet["publicBetaAccess"]=="hold" and packet["releaseAuthorized"] is False,
       "never autoapprove human semantics/release")
    return True
def validate_watch(value,manifest):
    expected=read(OUT)
    validate(expected,manifest)
    check(value==expected["watch"],"exact dated M41 watch required")
    check(value["completeOfficialTechnicalRead"] is True,
         "incomplete current source watch is NOT technical PASS")
def validate_notice(value):
    expected=read(OUT)
    validate(expected,read(ROOT/"monitor/sources.json"))
    check(value==expected["notice"],"exact dated M41 notice required")
def selftest():
    base=read(OUT);validate(base,read(ROOT/"monitor/sources.json"))
    changes=[
      lambda x:x.update(releaseAuthorized=True),
      lambda x:x.update(publicBetaAccess="open"),
      lambda x:x.update(all20HumanTasksStillUnsigned=False),
      lambda x:x["watch"].update(observedAtDate="2026-10-18"),
      lambda x:x["watch"].update(checked=83),
      lambda x:x["watch"].update(fetchFailures=1),
      lambda x:x["watch"].update(sourceHashAutoAccepted=True),
      lambda x:x["watch"].update(humanSourcePolicyApproved=True),
      lambda x:x["watch"].update(completeOfficialTechnicalRead=False),
      lambda x:x["watch"].update(unacceptedBaselineDriftCount=0),
      lambda x:x["watch"].update(observedSourceRawSha256="0"*64),
      lambda x:x["notice"].update(humanNoticeContentsSigned=True),
      lambda x:x["notice"].update(exactFinalJobDocumentsVerified=True),
      lambda x:x["notice"].update(observedAtDate="2026-10-18"),
      lambda x:x["notice"].update(indexRawSha256="0"*64),
      lambda x:x["notice"].update(titlesChecked=319),
      lambda x:x["notice"].update(finalManufacturing2026ApplicationTitleCandidates=1),
      lambda x:x["notice"]["sevenOriginalNoticeTaskIds"].pop()
    ]
    for i,fn in enumerate(changes):
        unsafe=copy.deepcopy(base);fn(unsafe)
        try:validate(unsafe,read(ROOT/"monitor/sources.json"))
        except (KeyError,TypeError,ValueError):pass
        else:raise AssertionError("M41 unsafe source or release record accepted "+str(i))
    print("M41_OCT19_TWO_TECHNICAL_GATES_SELF_TEST_PASS 18_fail_closed_cases machine_only beta_HOLD")
if __name__=="__main__":
    p=argparse.ArgumentParser()
    for a in ("write","check","self-test"):p.add_argument("--"+a,action="store_true")
    args=p.parse_args()
    if args.write:
        check(not OUT.exists(),"append only M41 original evidence")
        val=build();validate(val,read(ROOT/"monitor/sources.json"))
        OUT.write_text(json.dumps(val,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
        print("M41_EVIDENCE_WRITTEN 84-source",val["watch"]["checked"],
          "failures",val["watch"]["fetchFailures"],
          "unaccepted drifts",val["watch"]["unacceptedBaselineDriftCount"])
    if args.check:
        validate(read(OUT),read(ROOT/"monitor/sources.json"))
        print("M41_ORIGINAL_WATCH_INTEGRITY_PASS")
    if args.self_test:selftest()
