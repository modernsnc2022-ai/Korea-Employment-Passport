#!/usr/bin/env python3
"""M26: unsigned 2026 Indonesia official-review queue. Never approves policy or beta."""
from __future__ import annotations
import argparse
import copy
import json
from pathlib import Path
from urllib.parse import urlparse

from check_m24_manufacturing_job_docs_scope import verify as verify_m24
from check_m22_manual_review_packet import validate as verify_m22

ROOT=Path(__file__).resolve().parents[1]
DAY="2026-10-17"
INDEX="https://kp2mi.go.id/gtog-korea/pengumuman"
INPUT={
 "watch":"research/source_reviews/indonesia_daily_readonly_2026-10-17.json",
 "html":"research/source_reviews/indonesia_m21_original_html_audit_2026-10-17.json",
 "m22":"research/source_reviews/indonesia_m22_manual_review_queue_2026-10-17.json",
 "pdf":"research/source_reviews/indonesia_m23_pdf_lineage_2026-10-17.json",
 "notice":"research/source_reviews/indonesia_m24_manufacturing_title_scope_2026-10-17.json",
 "sign":"recruitment/ID_BETA_SOURCE_SIGNOFF_20261017.json",
 "route":"docs/data/id_e9_manufacturing_2026.json",
 "packs":"docs/data/document_packs_2026.json",
 "beta":"docs/data/beta_program_v1.json",
}
DEST=ROOT/"research/source_reviews/indonesia_m26_unsigned_review_handoff_2026-10-17.json"
DOC=ROOT/"research/INDONESIA_BETA_M26_OFFICIAL_REVIEW_HANDOFF_2026-10-17.md"
STAGES={
 "17 September 2026":"optional_skill_test_evidence",
 "10 September 2026":"eps_topik_stage_1_result",
 "5 May 2026":"exam_fee_refund",
 "27 March 2026":"exam_schedule",
 "16 February 2026":"exam_enrollment_biometrics",
 "10 February 2026":"exam_registration_adjustment",
 "27 January 2026":"initial_exam_registration",
}
SCOPE_COUNTS={"korea_shared":5,"multi_country_eps_schedule":2,"other_country":5}
def need(v,s):
    if not v:raise ValueError("M26_REVIEW_HANDOFF_BLOCKED "+s)
def read_all():
    return {k:json.loads((ROOT/v).read_text(encoding="utf-8-sig")) for k,v in INPUT.items()}
def task(id_,group,priority,url,scope,instruction,old_sha=None,new_sha=None):
    p=urlparse(url)
    need(p.scheme=="https" and p.hostname is not None,"official HTTPS task source required")
    return {
        "id":id_,"group":group,"priority":priority,"officialUrl":url,
        "scope":scope,"instruction":instruction,
        "priorAcceptedTextSha256":old_sha,"observedTextSha256":new_sha,
        "decision":"pending","humanReviewer":None,"reviewedAt":None,
        "originalPageEvidence":None,"actualPolicyChange":None,
        "automaticBaselineAcceptance":False,"authorizesRelease":False,
    }
def build(d):
    w,h,m22,p,n,s,r,packs,beta=(d[k] for k in INPUT)
    verify_m22(m22)
    verify_m24(n,h,p,w,s)
    need(w["observedAtDate"]==DAY and w["checked"]==84
       and w["fetchFailures"]==0 and w["unacceptedBaselineDriftCount"]==12
       and all(w["groupCounts"][k]==v for k,v in SCOPE_COUNTS.items()),
       "Oct17 12 pending source drifts")
    alerts=w["pendingReviews"]
    need(len(alerts)==12 and len({x["id"] for x in alerts})==12
       and all(x["semanticReview"]=="pending"
         and x["acceptedBaselineSha256"]!=x["observedSha256"] for x in alerts),
       "source review not manually decided")
    korea_sha={x["id"]:x["normalizedTextSha256"] for x in h["koreaOfficialText"]}
    need(len(korea_sha)==5 and all(korea_sha[x["id"]]==x["observedSha256"]
       for x in alerts if x["scope"]=="korea_shared"),
       "Korea original-text hash must match current watch before reviewer handoff")
    need(s["status"]=="pending_manual_source_signoff"
       and s["reviewer"] is None and s["approvedAt"] is None
       and s["betaAccess"]=="hold","source signoff must be truly unsigned")
    need(p["newlyFetchedPDFsWithOriginalSha256Match"]==6
       and p["newlyUnverifiedPDFs"]==1 and p["sourcePolicyHumanSignoff"] is False,
       "M23 PDF read is machine evidence")
    j=next(row for row in r["stages"] if row["id"]=="job_application")
    dp=next(row for row in packs["packs"] if row["id"]=="job_application_manufacturing")
    need(r["country"]=="ID" and r["visa"]=="E-9" and r["sector"]=="manufacturing"
       and r["cycle"]==2026 and len(r["stages"])==27
       and j["brokerReplacement"]=="held_official_notice"
       and j["sourceUrl"]==INDEX and j["officialActionUrl"]==INDEX
       and dp["status"]=="awaiting_sector_notice" and dp["sourceUrl"]==INDEX
       and not dp["items"],"M25 route-level final documents HOLD")
    need(beta["status"]=="hold"
       and beta["releaseDecision"]["publicBeta"]=="pending_manual_approval",
       "beta has no signed release")
    need(n["observedAtJakartaDate"]==DAY
       and n["generalManufacturingFinalOnlineJobApplicationTitleCount"]==0
       and n["generalManufacturingTitlesCount"]==7
       and {x["date"] for x in n["generalManufacturingTitles"]}==set(STAGES)
       and {x["url"] for x in n["generalManufacturingTitles"]}
           =={x["url"] for x in h["manufacturingNoticeHtml"]},
       "same-cycle notice evidence cannot be widened")
    items=[]
    for src in alerts:
        scope=src["scope"]
        need(scope in SCOPE_COUNTS,"unknown source scope")
        priority={"korea_shared":"P1","multi_country_eps_schedule":"P2",
                  "other_country":"P3"}[scope]
        how={"korea_shared":"Manually compare the live original Korean page and applicant-facing meaning, effective date and exact law/health/labor scope.",
             "multi_country_eps_schedule":"Manually check multi-country HRD EPS schedule applicability; do not treat it as Myanmar-only.",
             "other_country":"Retain this other-country alert and refer to that country owner; do not import it into Indonesia."}[scope]
        items.append(task("SRC:"+src["id"],"official_source",priority,
            src["url"],scope,how,src["acceptedBaselineSha256"],src["observedSha256"]))
    for notice in n["generalManufacturingTitles"]:
        items.append(task("NOTICE:"+notice["date"].replace(" ","-"),"manufacturing_notice",
            "P2",notice["url"],STAGES[notice["date"]],
            "Human must check the notice body, original PDFs and applicable cohort; this is NOT the final post-Skill Test Manufacturing job_docs checklist."))
    items.append(task("GATE:final_manufacturing_job_docs","unresolved_final_documents","P1",
        INDEX,"2026_ubt_umum_manufacturing_post_skill_test",
        "Obtain an explicitly applicable 2026 General Manufacturing final online job-doc notice with exact files, dates, and original annex pages; otherwise keep HOLD."))
    items.sort(key=lambda x:(x["priority"],x["group"],x["id"]))
    need(len(items)==20 and len({x["id"] for x in items})==20,"12+7+1 task identity")
    return {
       "version":"1.0.0","asOf":"2026-10-17",
       "type":"unsigned_official_source_review_handoff_not_signoff",
       "route":"Indonesia > Korea > E-9 > General Manufacturing 2026",
       "officialIndex":INDEX,"sourceEvidence":INPUT,
       "tasks":items,"pendingSourceAlertCount":12,
       "pendingNoticeBodyReviewCount":7,
       "pendingFinalJobDocsGateCount":1,
       "koreaSharedCurrentHtmlShaMatches":5,"m23PdfBodiesVerified":6,
       "m23PdfBodiesInconclusive":1,
       "releaseOperator":None,"operatorSignedAt":None,
       "humanPolicyReviewApproved":False,
       "sourceHashAutoAccepted":False,
       "finalManufacturingJobDocs":"hold",
       "betaAccess":"hold","deploymentApproved":False,"releaseAuthorized":False,
       "roleBoundary":"Approved content reviewer / beta tester is not an appointed official-source or production release reviewer.",
       "note":"Recorded status and old machine evidence alone can never count as a human release-day approval.",
    }
def check(packet,inputs):
    need(packet==build(inputs),"output differs from trusted original evidence")
    need(packet["releaseOperator"] is None and packet["operatorSignedAt"] is None
       and packet["releaseAuthorized"] is False
       and packet["finalManufacturingJobDocs"]=="hold"
       and packet["betaAccess"]=="hold"
       and all(x["decision"]=="pending"
         and x["humanReviewer"] is None and x["reviewedAt"] is None
         and x["authorizesRelease"] is False for x in packet["tasks"]),
       "auto approval or fabricated reviewer")
def markdown(q):
    out=[
     "# KEP M26 — 인도네시아 제조업 공식자료 심사 인계 (미승인)",
     "",
     "공식 관측 기준: 2026-10-17 WIB. 아래 목록은 담당자에게 전달할 검토 대기표이며 정책 승인이 아닙니다.",
     "기존 승인 콘텐츠 리뷰어/베타 테스터와 공식자료 의미 검토·출시 책임자는 별개의 역할입니다.",
     "",
     "한국 공통 5건은 우선 검토(P1), HRD Korea 다국가 자료 2건은 P2, 기타 국가 5건은 P3.",
     "제조업 관련 공고 7건은 본문·PDF 적용 범위를 확인하되 시험등록/선택적 역량증빙을 최종 구직등록 서류로 사용하지 않습니다.",
     "별도 P1 차단 항목: 2026 일반 제조업 post-Skill-Test 최종 온라인 구직등록 첨부서류 공식 근거 미확정.",
     "",
     "| 우선순위 | 작업 ID | 적용 범위 | 공식 원문 | 담당자 판단 |",
     "|---|---|---|---|---|"
    ]
    for x in q["tasks"]:
        out.append("| "+x["priority"]+" | "+x["id"]+" | "+x["scope"]
          +" | [공식 출처]("+x["officialUrl"]+") | PENDING |")
    out+=["","## 별도 담당자 서명 전 조건",
          "- [ ] 각 원문에서 실제 의미·적용 국가·법령/공고 효력일·문서 페이지 확인 후 심사자 실명과 확인 시각 기록",
          "- [ ] 변경 지문 12건 전부 범위 판정; SHA 자동 승인은 불가",
          "- [ ] 2026 일반 제조업 최종 구직신청 제출서류의 정확한 원문이 없으면 계속 HOLD",
          "- [ ] 출시 당일 별도 공식자료 서명 완료, 승인된 후보 배포 이후 실서비스 9/9 자산·6/6 HTTPS 전환 확인",
          "- [ ] 베타 공개 결정은 위 검증과 별도의 명시적 사람 승인 필요",
          "",
          "상태: source semantic signoff PENDING / job_docs HOLD / beta HOLD / draft PR unmerged / no deployment.",
          ""]
    return "\n".join(out)
def selftest():
    d=read_all();p=build(d);check(p,d)
    mutations=[
      lambda a:a["watch"].update(checked=83),
      lambda a:a["watch"]["groupCounts"].update(korea_shared=4),
      lambda a:a["watch"]["pendingReviews"][0].update(semanticReview="approved"),
      lambda a:a["watch"]["pendingReviews"][0].update(observedSha256="0"*64),
      lambda a:a["notice"].update(generalManufacturingFinalOnlineJobApplicationTitleCount=1),
      lambda a:a["notice"]["generalManufacturingTitles"][0].update(url="https://evil.invalid/fake"),
      lambda a:a["pdf"].update(newlyUnverifiedPDFs=0),
      lambda a:a["sign"].update(status="approved"),
      lambda a:a["sign"].update(reviewer="Fake reviewer"),
      lambda a:next(x for x in a["route"]["stages"] if x["id"]=="job_application").update(brokerReplacement="complete"),
      lambda a:next(x for x in a["packs"]["packs"] if x["id"]=="job_application_manufacturing").update(status="verified"),
      lambda a:a["beta"].update(status="open"),
    ]
    for index,change in enumerate(mutations):
        b=copy.deepcopy(d);change(b)
        try:build(b)
        except (ValueError,KeyError,TypeError):pass
        else:raise AssertionError("unsafe source/release state accepted at case "+str(index))
    for field,value in [("releaseAuthorized",True),("betaAccess","open"),("releaseOperator","fake")]:
        b=copy.deepcopy(p);b[field]=value
        try:check(b,d)
        except ValueError:pass
        else:raise AssertionError("unsafe result mutation accepted")
    print("M26_UNSIGNED_REVIEW_SELF_TEST_PASS 15_fail_closed_cases 12_sources 7_notices 1_jobdocs_HOLD")
def main():
    pa=argparse.ArgumentParser()
    for cmd in ["self-test","write","check"]:pa.add_argument("--"+cmd,action="store_true")
    a=pa.parse_args()
    if getattr(a,"self_test"):selftest()
    if a.write:
        need(not DEST.exists() and not DOC.exists(),"append-only files already exist")
        d=read_all();q=build(d);check(q,d)
        DEST.write_text(json.dumps(q,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
        DOC.write_text(markdown(q),encoding="utf-8")
        print("M26_HANDOFF_WRITTEN sources=12 notices=7 jobdoc_gate=1 no_human_signature")
    if a.check:
        d=read_all();q=json.loads(DEST.read_text(encoding="utf-8"))
        check(q,d)
        need(DOC.read_text(encoding="utf-8")==markdown(q),"human checklist differs from JSON")
        print("M26_HANDOFF_INTEGRITY_PASS sources=12 notices=7 jobdocs_HOLD beta_HOLD")
    if not (getattr(a,"self_test") or a.write or a.check):pa.error("choose an action")
if __name__=="__main__":main()
