#!/usr/bin/env python3
"""M38: new-day KP2MI+HRD read-only observation vs old source/release gates.

No writes to app, official hash baseline, person approval, Pages or beta.
"""
from __future__ import annotations
import argparse,copy,json,re
from datetime import datetime,timezone
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT=Path(__file__).resolve().parents[1]
DAY="2026-10-18"
OUT=ROOT/"research/source_reviews/indonesia_m38_oct18_official_beta_handoff.json"
REPORT=ROOT/"research/INDONESIA_BETA_M38_OCT18_OFFICIAL_WATCH_AND_BLOCKERS.md"
def read(p):return json.loads(Path(p).read_text(encoding="utf-8-sig"))
def source(name):return read(ROOT/"research/source_reviews"/name)
def need(value,why):
    if not value:raise ValueError("M38_OCT18_OFFICIAL_NO_RELEASE "+why)
def oct18(value):
    return datetime.fromisoformat(value.replace("Z","+00:00")).astimezone(
        ZoneInfo("Asia/Jakarta")).date().isoformat()==DAY
def build(discovery,watch,mtime):
    old=source("indonesia_m37_official_late_pdf_retry_2026-10-17.json")
    packet=source("indonesia_m34_unsigned_release_review_packet_2026-10-17.json")
    signed=read(ROOT/"recruitment/ID_BETA_SOURCE_SIGNOFF_20261017.json")
    # A 2026-10-17 unsigned review is NOT a 2026-10-18 approval.
    need(packet["pendingReviewTasks"]==20
      and all(t["semanticDecision"]=="pending" and t["reviewerName"] is None
         for t in packet["reviewTasks"]), "20 unsigned review tasks")
    need(old["index"]["sameAsM34"] is True
      and old["index"]["explicitGeneralManufacturingFinalApplicationCandidates"]==0
      and old["publicBetaAccess"]=="hold", "previous notice baseline")
    need(signed["status"]=="pending_manual_source_signoff"
      and signed["reviewer"] is None and signed["approvedAt"] is None
      and signed["betaAccess"]=="hold","human signoff absent")
    need(discovery["schema"]=="kep-id-official-discovery-v1"
      and set(discovery["sourcesComplete"])=={"kp2mi","hrdk"}
      and discovery["status"]=="observed_not_approved"
      and discovery["sourceHashAutoAccepted"] is False
      and discovery["betaOpenAuthorized"] is False
      and oct18(discovery["observedAtUtc"]), "fresh dual-provider observations")
    rows=discovery["records"]
    need(len({x["key"] for x in rows})==len(rows),"distinct official IDs")
    kp=[x for x in rows if x["provider"]=="kp2mi"]
    hr=[x for x in rows if x["provider"]=="hrdk"]
    need(len(kp)==320 and len(hr)>=2 and len(hr)<=120, "bounded official source pages")
    known={t["officialOriginalUrl"] for t in packet["reviewTasks"]
          if t["taskId"].startswith("NOTICE:")}
    kpurls={x["url"] for x in kp if x.get("generalManufacturing2026")}
    need(len(known)==7 and kpurls==known,"seven 2026 Manufacturing original URLs intact")
    relevant_hr=[x for x in hr if x.get("generalManufacturing2026")]
    need(len(relevant_hr)==2 and all(x["year"]=="2026" and
         "manufacturing" in x["title"].lower() and
         "Indonesia" in x["title"] for x in relevant_hr),
         "two verified official Indonesia Manufacturing schedule identities")
    target=[x for x in kp if x.get("generalManufacturingFinalCandidate")]
    generic=[x for x in kp if x.get("genericApplicationReview") and
             not x.get("generalManufacturingFinalCandidate")]
    need(not target and not generic,"new target headline requires independent manual scope")
    # Technical official source state; no baseline mutation or significance signoff.
    need(watch["configured"]==84 and 0<=watch["checked"]<=84
       and isinstance(watch["changed"],list) and isinstance(watch["failures"],list)
       and watch["acceptedCurrent"] is False
       and watch["initialized"] is False
       and watch["reviewManifestAccepted"] is False
       and watch["partialAcceptance"] is False
       and oct18(datetime.fromtimestamp(mtime,timezone.utc).isoformat()),
       "only new-day non-accepted 84-source fetch output")
    errors=watch["failures"]
    complete=watch["checked"]==84 and not errors
    need(len({r["id"] for r in watch["changed"]})==len(watch["changed"]),
         "duplicate drift source")
    allowed={x["id"] for x in read(ROOT/"monitor/sources.json")["sources"]}
    changes=[{"sourceId":x["id"],"reason":x["reason"],
              "humanPolicyReview":"pending"}
             for x in watch["changed"]]
    need(all(x["sourceId"] in allowed for x in changes),"unconfigured source alert")
    observed_ids=[x["sourceId"] for x in changes]
    older=source("indonesia_daily_readonly_2026-10-17.json")
    prev_ids=[x["id"] for x in older["pendingReviews"]]
    now=set(observed_ids);before=set(prev_ids)
    report={
        "version":"1.0.0","asOfJakarta":DAY,
        "kind":"new_day_official_kp2mi_hrd_source_triage_unsigned",
        "liveOfficialDiscoveryObservedUTC":discovery["observedAtUtc"],
        "kp2miAnnouncementsRead":len(kp),
        "kp2mi2026ManufacturingNotices":len(kpurls),
        "explicit2026FinalManufacturingApplicationHeadlineCandidates":len(target),
        "generic2026FinalApplicationReviewCandidates":len(generic),
        "hrdKoreaScheduleRowsRead":len(hr),
        "hrdKoreaIndonesiaManufacturingScheduleCandidates":[
            {"year":x["year"],"examNo":x["examNo"],"title":x["title"],
             "url":x["url"],"humanStageReview":"pending"} for x in relevant_hr
        ],
        "hrdScheduleChangesSince17":"not_comparable_first_complete_today_snapshot",
        "sourceMonitorConfigured":84,"sourceMonitorFetched":watch["checked"],
        "sourceMonitorFailedIds":[x["id"] for x in errors],
        "sourceMonitorTechnicallyComplete":complete,
        "sourceMonitorUnacceptedDriftCount":len(changes),
        "sourceMonitorCurrentUnacceptedChanges":changes,
        "sourceAlertPreviouslyPendingOnOct17":len(prev_ids),
        "sameAlertIdsVsOct17":sorted(now&before),
        "newOrOtherDriftIdsVsOct17":sorted(now-before),
        "noLongerSameShaDriftIdsVsOct17":sorted(before-now),
        "previous20HumanReviewOrders":"PENDING_UNASSIGNED_FROM_2026_10_17",
        "operatorRevalidationRequiredOnCurrentDay":True,
        "currentDayReleasedApprovedSourceHashes":False,
        "official2026FinalManufacturingJobDocListConfirmed":False,
        "existingMainPagesAssetProofOnlyFromOct17":True,
        "sameHeadCandidateDeployedNow":False,
        "humanOfficialSourceSignoff":False,
        "actualPublicBetaOpenAuthorized":False,
        "betaAccess":"hold",
        "releaseAuthorized":False,
        "requiredNextActions":[
            "Await/verify 2026 same-cohort General Manufacturing final online job application original and PDF pages; never import older/other-sector docs.",
            "Review currently changed official source text and 20 unsigned reviewer tasks with a named responsible human, exact original source/date/semantic rationale.",
            "Require independently approved same-HEAD Pages deployment 9/9 and live HTTPS 6/6, then a distinct manual beta OPEN decision.",
        ],
        "evidenceLimits":"Today-only KP2MI/HRD complete listing; 84-source monitor is technical only and may contain errors. Matching text SHA does not prove unchanged policy, HRD historical previous-day change count unknown, and title-only absence does not prove no relevant annex."
    }
    verify(report)
    return report
def verify(o):
    need(o["asOfJakarta"]==DAY
      and o["kind"]=="new_day_official_kp2mi_hrd_source_triage_unsigned"
      and oct18(o["liveOfficialDiscoveryObservedUTC"]),"Oct18 scoped evidence")
    need(o["kp2miAnnouncementsRead"]==320
      and o["kp2mi2026ManufacturingNotices"]==7
      and o["explicit2026FinalManufacturingApplicationHeadlineCandidates"]==0
      and o["generic2026FinalApplicationReviewCandidates"]==0
      and o["hrdKoreaScheduleRowsRead"]>=2
      and len(o["hrdKoreaIndonesiaManufacturingScheduleCandidates"])==2,
      "no fake current-cycle notice")
    need(o["sourceMonitorConfigured"]==84
      and 0<=o["sourceMonitorFetched"]<=84
      and o["sourceMonitorTechnicallyComplete"]==
          (o["sourceMonitorFetched"]==84 and len(o["sourceMonitorFailedIds"])==0),
      "no false 84/84 success when source incomplete")
    need(o["sourceMonitorUnacceptedDriftCount"]==
      len(o["sourceMonitorCurrentUnacceptedChanges"])
      and all(x["humanPolicyReview"]=="pending" for x in o["sourceMonitorCurrentUnacceptedChanges"])
      and len({x["sourceId"] for x in o["sourceMonitorCurrentUnacceptedChanges"]})==
          o["sourceMonitorUnacceptedDriftCount"],
      "changed SHA is NEVER human policy approval")
    need(o["sourceAlertPreviouslyPendingOnOct17"]==12
      and o["hrdScheduleChangesSince17"]=="not_comparable_first_complete_today_snapshot"
      and o["previous20HumanReviewOrders"]=="PENDING_UNASSIGNED_FROM_2026_10_17"
      and o["operatorRevalidationRequiredOnCurrentDay"] is True,
      "no stale source signoff")
    need(o["currentDayReleasedApprovedSourceHashes"] is False
      and o["official2026FinalManufacturingJobDocListConfirmed"] is False
      and o["existingMainPagesAssetProofOnlyFromOct17"] is True
      and o["sameHeadCandidateDeployedNow"] is False
      and o["humanOfficialSourceSignoff"] is False
      and o["actualPublicBetaOpenAuthorized"] is False
      and o["betaAccess"]=="hold"
      and o["releaseAuthorized"] is False,
      "no launch by stale or machine-only data")
def render(q):
    complete=q["sourceMonitorTechnicallyComplete"]
    lines=[
      "# KEP M38 — 2026-10-18 공식 공고·시험 일정 및 출시 차단 재검토",
      "",
      "**성격:** 오늘 직접 읽은 KP2MI 및 HRD Korea 공식 목록과 84개 출처 기술 감시의 읽기 전용 증거. 실제 담당자 법·정책 승인이나 실서비스 배포 아님.",
      "",
      "## 오늘의 실제 공식 관측",
      "",
      "- KP2MI 제목/URL "+str(q["kp2miAnnouncementsRead"])+"건 읽음. 2026 일반 제조업 관련 "+str(q["kp2mi2026ManufacturingNotices"])+"건. **최종 온라인 구직등록 제목 후보 "+str(q["explicit2026FinalManufacturingApplicationHeadlineCandidates"])+"건**, 분야가 불명확한 검토 후보 "+str(q["generic2026FinalApplicationReviewCandidates"])+"건.",
      "- HRD Korea 공식 EPS 시험 일정 "+str(q["hrdKoreaScheduleRowsRead"])+"건 조회, 인도네시아 2026 일반 제조업 관련 "+str(len(q["hrdKoreaIndonesiaManufacturingScheduleCandidates"]))+"건(자카르타·스마랑). 이 두 일정은 최종 구직등록 공고가 아님.",
      "- HRD 이중 소스 결합 감시의 오늘 최초 관측에서는 비교 가능한 10월 17일 동일 형식 전체 원장이 없어 **어제 대비 변경 없음**이라고 단정하지 않음.",
      "- 공식 출처 84개 기술 조회: **"+str(q["sourceMonitorFetched"])+"/84** 수집, 실패 "+str(len(q["sourceMonitorFailedIds"]))+"건; 완전 관측 "+("PASS" if complete else "BLOCKED — 미수집 재확인 필요")+". 현재 미승인 원문 지문 경고 "+str(q["sourceMonitorUnacceptedDriftCount"])+"건.",
      "",
      "## 전날 미승인 출처 경고와의 관계 — 정책 승인 아님",
      "",
      "- 10/17 미승인 경고 12건 중 오늘도 SHA 관측 경고: "+str(len(q["sameAlertIdsVsOct17"]))+"건.",
      "- 새롭게 나타났거나 기존 12건 밖의 SHA 경고: "+str(len(q["newOrOtherDriftIdsVsOct17"]))+"건.",
      "- 10/17 경고였으나 오늘 SHA 경고 목록에서 빠진 출처: "+str(len(q["noLongerSameShaDriftIdsVsOct17"]))+"건. 이는 사이트 재변동·일시 접근 실패·원문 복구 가능성 모두를 포함하며 **사람의 실제 의미 검토 면제가 아님**.",
      "- 명확한 미수집 출처 ID: "+(", ".join(q["sourceMonitorFailedIds"]) if q["sourceMonitorFailedIds"] else "없음")+".",
      "",
      "## 실제 출시 차단 및 다음 담당 작업",
      "",
      "| 차단 조건 | 10/18 판정 | 필요한 근거/담당 작업 |",
      "|---|---|---|",
      "| 2026 General Manufacturing 최종 구직등록 | **HOLD** | Skill Test 최종 결과 후 공식 원문·PDF·서류별 의무 여부·기한 확보 및 사람 확인 |",
      "| 공식자료 의미 검토 | **PENDING** | 10/17 미서명 20개 검토 지시서에 오늘 원문 기준의 담당자·시각·근거 기록 |",
      "| 84개 공식자료 기술 관측 | "+("관측 완료, 검토 필요" if complete else "**미완료**")+" | 실패 출처는 재확인, SHA 변동은 문구별 정책 의미 검토 후에만 판단 |",
      "| 후보 GitHub Pages 배포 | **PENDING** | 지난 10/17의 main/docs 9/9 증거를 오늘 후보 HEAD 배포 증거로 사용하지 말 것 |",
      "| 실제 공개 베타 OPEN | **HOLD** | 위 모든 조건 충족 후 별도 운영자 명시적 결정 |",
      "",
      "**절대 금지:** 2025년 제조업 제출서류, 2026년 어업/Root Industry/특별시험, 최초 EPS-TOPIK 등록 및 선택적 Skill Test 증빙을 2026년 일반 제조업 **최종** 서류로 사용하지 않습니다.",
      "",
      "**현재:** 관심 신청 접수 OPEN / 최종 구직등록 단계 HOLD / 담당자 승인 없음 / Draft PR 미병합 / 신규 코드 실서비스 미배포 / 공개 베타 접근 HOLD."
    ]
    return "\n".join(lines)+"\n"

def selftest():
    q=read(OUT);verify(q)
    mods=[
      lambda a:a.update(betaAccess="open"),
      lambda a:a.update(releaseAuthorized=True),
      lambda a:a.update(actualPublicBetaOpenAuthorized=True),
      lambda a:a.update(official2026FinalManufacturingJobDocListConfirmed=True),
      lambda a:a.update(humanOfficialSourceSignoff=True),
      lambda a:a.update(currentDayReleasedApprovedSourceHashes=True),
      lambda a:a.update(sameHeadCandidateDeployedNow=True),
      lambda a:a.update(operatorRevalidationRequiredOnCurrentDay=False),
      lambda a:a.update(kp2mi2026ManufacturingNotices=8),
      lambda a:a.update(explicit2026FinalManufacturingApplicationHeadlineCandidates=1),
      lambda a:a.update(sourceMonitorTechnicallyComplete=not a["sourceMonitorTechnicallyComplete"]),
      lambda a:a.update(hrdScheduleChangesSince17="unchanged_verified"),
      lambda a:a["hrdKoreaIndonesiaManufacturingScheduleCandidates"].pop(),
      lambda a:a.update(sourceMonitorUnacceptedDriftCount=0),
      lambda a:a.update(asOfJakarta="2026-10-17"),
      lambda a:a.update(previous20HumanReviewOrders="APPROVED"),
    ]
    for i,change in enumerate(mods):
        candidate=copy.deepcopy(q);change(candidate)
        try:verify(candidate)
        except (KeyError,ValueError,TypeError):pass
        else:raise AssertionError("unsafe M38 source state accepted "+str(i))
    print("M38_NEW_DAY_RELEASE_SAFETY_SELF_TEST_PASS 16_negative_cases 320_KP2MI 58_HRD no_final_2026_job_docs")
def main():
    cli=argparse.ArgumentParser()
    cli.add_argument("--discovery",type=Path)
    cli.add_argument("--watch",type=Path)
    cli.add_argument("--write",action="store_true")
    cli.add_argument("--check",action="store_true")
    cli.add_argument("--self-test",action="store_true")
    a=cli.parse_args()
    if a.write:
        need(a.discovery is not None and a.watch is not None,"need two original external sources")
        need(not OUT.exists() and not REPORT.exists(),"append-only current date snapshots already exist")
        for p in (a.discovery,a.watch):
            resolved=p.resolve()
            need(resolved!=ROOT.resolve() and ROOT.resolve() not in resolved.parents,
                 "raw full original source not in git repository")
        report=build(read(a.discovery),read(a.watch),a.watch.stat().st_mtime)
        OUT.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
        REPORT.write_text(render(report),encoding="utf-8")
        print("M38_OCT18_OBSERVED KP2MI",report["kp2miAnnouncementsRead"],
              "HRD",report["hrdKoreaScheduleRowsRead"],
              "sources",report["sourceMonitorFetched"],"/84",
              "failures",len(report["sourceMonitorFailedIds"]),
              "unaccepted_drifts",report["sourceMonitorUnacceptedDriftCount"],
              "beta_HOLD")
    if a.check:
        q=read(OUT)
        verify(q)
        need(REPORT.read_text(encoding="utf-8")==render(q),"generated operator report does not match evidence")
        print("M38_OCT18_EVIDENCE_INTEGRITY_PASS no_auto_approval_no_cross_day_reuse")
    if a.self_test:selftest()
    if not(a.write or a.check or a.self_test):cli.error("choose action")
if __name__=="__main__":main()
