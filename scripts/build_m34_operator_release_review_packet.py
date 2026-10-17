#!/usr/bin/env python3
"""M34: immutable release-day operator source-review work order, NOT an approval.

Live KP2MI titles, 20 unsigned source/notice tasks, 10 independent release
gates, and an explicit evidence checklist. No writes to operational states.
"""
from __future__ import annotations
import argparse,copy,json,re
from datetime import datetime,timezone
from pathlib import Path
from zoneinfo import ZoneInfo
from audit_id_manufacturing_notice_index_live import retrieve,classify,validate_snapshot
from audit_m30_manufacturing_post_skill_notice_sentinel import tagged
ROOT=Path(__file__).resolve().parents[1]
DAY="2026-10-17"
INDEX="https://kp2mi.go.id/gtog-korea/pengumuman"
OUT=ROOT/"research/source_reviews/indonesia_m34_unsigned_release_review_packet_2026-10-17.json"
REPORT=ROOT/"research/INDONESIA_BETA_M34_OPERATOR_REVIEW_WORK_ORDER_2026-10-17.md"
def read(p):
    return json.loads((ROOT/p).read_text(encoding="utf-8-sig"))
def need(ok,reason):
    if not ok:raise ValueError("M34_OPERATOR_REVIEW_BLOCKED "+reason)
def source_inputs():
    watch=read("research/source_reviews/indonesia_daily_readonly_2026-10-17.json")
    m26=read("research/source_reviews/indonesia_m26_unsigned_review_handoff_2026-10-17.json")
    m30=read("research/source_reviews/indonesia_m30_post_skill_notice_candidates_corrected_r1_2026-10-17.json")
    m32=read("research/source_reviews/indonesia_m32_pages_release_blockers_2026-10-17.json")
    m33=read("research/source_reviews/indonesia_m33_exact_final_job_docs_preflight_2026-10-17.json")
    sign=read("recruitment/ID_BETA_SOURCE_SIGNOFF_20261017.json")
    packs=read("docs/data/document_packs_2026.json")
    beta=read("docs/data/beta_program_v1.json")
    return watch,m26,m30,m32,m33,sign,packs,beta
def validate_inputs(items):
    watch,m26,m30,m32,m33,sign,packs,beta=items
    need(watch["checked"]==84 and watch["fetchFailures"]==0
        and watch["unacceptedBaselineDriftCount"]==12
        and watch["observedAtDate"]==DAY,"84/84 source watcher 12 changed SHA")
    need(m26["asOf"]==DAY and len(m26["tasks"])==20
        and m26["pendingSourceAlertCount"]==12
        and m26["pendingNoticeBodyReviewCount"]==7
        and m26["pendingFinalJobDocsGateCount"]==1
        and all(t["decision"]=="pending" and t["humanReviewer"] is None
                and t["reviewedAt"] is None for t in m26["tasks"]),
        "unsigned M26 20 tasks")
    groups={g:sum(x["scope"]==g for x in watch["pendingReviews"]) for g in (
        "korea_shared","multi_country_eps_schedule","other_country")}
    need(groups=={"korea_shared":5,"multi_country_eps_schedule":2,"other_country":5},
        "country source categories unchanged")
    need(m30["manufacturingExplicitFinalOnlineApplicationTitles"]==0
       and m30["jobDocs"]=="hold" and m30["correctedCandidateCount"]==9,"M30 final notices held")
    need(m32["servedAssetsMatchingDeployedMain"]==9
       and m32["servedAssetsMatchingDraftCandidateBySourceAudit"]==0
       and m32["authorizesRelease"] is False,"M32 main versus Draft")
    ids={g["id"]:g["status"] for g in m33["gates"]}
    need(len(m33["gates"])==10
       and len(ids)==10
       and sum(x=="PASS" for x in ids.values())==5
       and sum(x=="PENDING" for x in ids.values())==5
       and ids["exact_2026_manufacturing_final_job_documents"]=="PENDING"
       and ids["explicit_manual_beta_open"]=="PENDING"
       and m33["readyForManualLaunchDecision"] is False
       and m33["authorizesRelease"] is False,"new M33 nonwaivable gate")
    need(sign["status"]=="pending_manual_source_signoff" and
         sign["reviewer"] is None and sign["approvedAt"] is None
         and sign["exactManufacturingJobDocumentsHeld"] is True
         and sign["betaAccess"]=="hold","real signoff unsigned")
    p=next(x for x in packs["packs"] if x["id"]=="job_application_manufacturing")
    need(p["status"]=="awaiting_sector_notice" and p["items"]==[],"held exact job documents")
    need(beta["status"]=="hold"
       and beta["application"]["intakeStatus"]=="open"
       and beta["releaseDecision"]["publicBeta"]=="pending_manual_approval",
       "actual user beta access closed")
def build(items,rows,total,checked_at):
    validate_inputs(items)
    watch,m26,m30,m32,m33,sign,packs,beta=items
    need(datetime.fromisoformat(checked_at).astimezone(
         ZoneInfo("Asia/Jakarta")).date().isoformat()==DAY,"WIB observation day")
    snap=validate_snapshot(rows,total,checked_at=checked_at)
    original_digest=m30["originalTitleUrlSha256"]
    parsed=[classify(r) for r in rows]
    urls={x["url"] for x in parsed}
    known={t["officialUrl"] for t in m26["tasks"] if t["group"]=="manufacturing_notice"}
    need(known.issubset(urls) and len(known)==7,"seven original 2026 notices retained")
    candidates=[q for r in rows if (q:=tagged(r)) is not None]
    final_headlines=[c for c in candidates if c["screeningStage"]==
                     "manufacturing_final_application_title_candidate"]
    ambiguous=[c for c in candidates if c["screeningStage"] in (
      "generic_final_application_or_certificate_manual_scope_review",
      "mixed_sector_requires_manual_attribution")]
    op_tasks=[]
    for q in m26["tasks"]:
        op_tasks.append({
         "taskId":q["id"],"scope":q["scope"],"priority":q["priority"],
         "officialOriginalUrl":q["officialUrl"],
         "inspectionRequirement":q["instruction"],
         "reviewerName":None,"reviewedAt":None,"originalPageCitation":None,
         "currentCohortApplicability":None,"semanticDecision":"pending",
         "approvedOfficialSourceHash":False,
         "evidenceReadyToUnlockBeta":False,
        })
    packet={
      "version":"1.0.0","kind":"unsigned_manual_operator_handoff_not_approval",
      "asOfJakarta":DAY,"observedAtUTC":checked_at,"route":"Indonesia > Korea > E-9 > General Manufacturing 2026",
      "officialIndex":INDEX,"officialIndexCheckedRows":len(rows),
      "officialIndexTotalRecords":total,"officialTitleUrlSha256":snap["titleUrlDigestSha256"],
      "matchesM30TitleUrlSha256":snap["titleUrlDigestSha256"]==original_digest,
      "knownManufacturing2026OriginalNotices":7,
      "explicitFinalManufacturingApplicationHeadlineCandidates":final_headlines,
      "ambiguousOrMixedSectorHeadlineCandidates":ambiguous,
      "reviewTasks":op_tasks,"pendingReviewTasks":len(op_tasks),
      "sourceAlertCount":12,"sourceAlertGroups":{"KoreanCommon":5,"MultiCountryHRD":2,"OtherCountry":5},
      "liveGateCount":len(m33["gates"]),
      "releaseGates":[{"id":g["id"],"observedStatus":g["status"],
         "evidence":g["evidence"],"nextAction":g["nextAction"],
         "reviewerName":None,"reviewedAt":None,
         "humanDecision":"pending"} for g in m33["gates"]],
      "reviewRoles":{
        "appointedOfficialSourceInterpreter":"internal_human_reviewer_not_government_endorsement",
        "betaLaunchOwner":"separate_named_responsible_operator",
        "existingContentReviewerIsNotReleaseApprover":True
      },
      "operatorEvidenceRequirements":[
        "Check each dated official URL ORIGINAL body and relevant PDF pages, including 2026 cohort and sector.",
        "Preserve 12 unaccepted source changes with separate Korean, multi-country HRD, and other-country triage.",
        "Record reviewer legal name, actual timezone-aware review time, page or paragraph quote, scope, date and rationale for each applicable rule.",
        "Find a real 2026 General Manufacturing FINAL post-Skill-Test online job-doc original list; exam registration, optional skills, 2025 and Fisheries are insufficient.",
        "Re-run actual release-day official index, exact original attachments, candidate same-SHA Pages 9/9 and HTTPS 6/6 after separately approved deployment.",
        "After all evidence, obtain a separate human beta OPEN decision; never infer approval from interest intake."
      ],
      "officialSourceInterpretationSigned":False,
      "official2026FinalManufacturingDocumentChecklistVerified":False,
      "sourceHashAutoAccepted":False,"manualReviewerName":None,"manualApprovalTimestamp":None,
      "mainMergeDone":False,"candidateDeployed":False,"publicBetaAccess":"hold",
      "releaseAuthorized":False,
      "limitations":"Title+URL feed is a bounded public index observation. It cannot prove no relevant annex/PDF or authorize an official source interpretation, release-day signoff, production deploy or applicant final document upload."
    }
    verify(packet,items)
    return packet
def verify(q,inputs):
    validate_inputs(inputs)
    need(q["kind"]=="unsigned_manual_operator_handoff_not_approval"
      and q["asOfJakarta"]==DAY and q["officialIndex"]==INDEX
      and q["officialIndexCheckedRows"]>=320
      and q["officialIndexTotalRecords"]>=q["officialIndexCheckedRows"]
      and q["knownManufacturing2026OriginalNotices"]==7
      and bool(re.fullmatch("[0-9a-f]{64}",q["officialTitleUrlSha256"]))
      and q["matchesM30TitleUrlSha256"] == (q["officialTitleUrlSha256"] ==
           inputs[2]["originalTitleUrlSha256"])
      and q["liveGateCount"]==10,"official title input counts")
    if q["matchesM30TitleUrlSha256"]:
        need(len(q["explicitFinalManufacturingApplicationHeadlineCandidates"])==0
          and len(q["ambiguousOrMixedSectorHeadlineCandidates"])==0,
          "matching M30 source digest cannot inject a false Manufacturing application title")
    original_tasks={x["id"]:x for x in inputs[1]["tasks"]}
    need(len(q["reviewTasks"])==q["pendingReviewTasks"]==20
       and {x["taskId"] for x in q["reviewTasks"]}==set(original_tasks)
       and q["sourceAlertCount"]==12
       and q["sourceAlertGroups"]=={"KoreanCommon":5,"MultiCountryHRD":2,"OtherCountry":5},
       "20 queued source/manual assignments")
    for t in q["reviewTasks"]:
        old=original_tasks[t["taskId"]]
        need(t["scope"]==old["scope"] and t["officialOriginalUrl"]==old["officialUrl"]
         and t["semanticDecision"]=="pending" and t["reviewerName"] is None
         and t["reviewedAt"] is None and t["originalPageCitation"] is None
         and t["approvedOfficialSourceHash"] is False
         and t["evidenceReadyToUnlockBeta"] is False,"false source reviewer")
    original_gates={x["id"]:x["status"] for x in inputs[4]["gates"]}
    need(len(q["releaseGates"])==10 and
        {x["id"] for x in q["releaseGates"]}==set(original_gates),"all release gates")
    for g in q["releaseGates"]:
        need(g["observedStatus"]==original_gates[g["id"]]
           and g["reviewerName"] is None and g["reviewedAt"] is None
           and g["humanDecision"]=="pending","launch reviewer signatures")
    need(q["reviewRoles"]["existingContentReviewerIsNotReleaseApprover"] is True
        and q["officialSourceInterpretationSigned"] is False
        and q["official2026FinalManufacturingDocumentChecklistVerified"] is False
        and q["sourceHashAutoAccepted"] is False and q["manualReviewerName"] is None
        and q["manualApprovalTimestamp"] is None and q["mainMergeDone"] is False
        and q["candidateDeployed"] is False and q["publicBetaAccess"]=="hold"
        and q["releaseAuthorized"] is False,"no synthetic approval")
    need(all(c["humanReviewer"] is None and c["verifiedExactFinalJobDocuments"] is False
       for c in (q["explicitFinalManufacturingApplicationHeadlineCandidates"]+
                 q["ambiguousOrMixedSectorHeadlineCandidates"])),
       "titles cannot authorize exact docs")
def render(q):
    txt=["# KEP M34 — 실제 담당자 공식자료 검토 인계 (서명 전 작업 지시서)",
      "",
      "**일자:** 2026-10-17 (Jakarta). **성격:** 내부 운영자 검토 패킷이며 정부 기관의 제품 승인서가 아닙니다.",
      "",
      "**결론:** 공식 공고 제목/URL "+str(q["officialIndexCheckedRows"])+"건 재조회, 이전 M30 지문 "+
        ("일치" if q["matchesM30TitleUrlSha256"] else "변경 — 원문 재검토 요구")+
        ". 정확한 일반 제조업 최종 구직등록 파일 목록 미확정, 실제 공개 베타 HOLD.",
      "",
      "## 운영 책임 구분",
      "",
      "기존 콘텐츠 리뷰어·베타 테스터는 공식 노동/검역/EPS 자료의 자동 승인권자가 아닙니다. "+
      "공식자료 내용을 읽고 확인하는 사람은 지정된 **내부 검토 책임자**이고, "+
      "국가기관이 KEP 서비스를 승인했다는 뜻이 아닙니다. 배포·베타 OPEN은 별도의 책임자 결정입니다.",
      "",
      "## 필수 사람 검토 항목 — 총 "+str(q["pendingReviewTasks"])+"건",
      "",
      "| 우선 | 항목 | 적용범위 | 실제 공식 원문 | 사람 검토 |",
      "|---|---|---|---|---|"]
    for t in q["reviewTasks"]:
        txt.append("| "+t["priority"]+" | "+t["taskId"]+" | "+t["scope"]
                   +" | [원문]("+t["officialOriginalUrl"]+") | PENDING |")
    txt.extend(["",
      "## 기술 출시 게이트 — 담당자 서명 전",
      "",
      "| 게이트 | 실제 검증 상태 | 담당자 직접 해야 할 확인 |",
      "|---|---|---|"])
    for g in q["releaseGates"]:
        txt.append("| "+g["id"]+" | "+g["observedStatus"]+" | "+g["nextAction"].replace("|","/")+" |")
    txt.extend(["","## 증거 기록 원칙",
      "",
      "- 담당자가 실제 URL, 본문 조항/부속 PDF 페이지, 적용 국가·직종·모집연도·발표일을 확인하고 실명·시간대 있는 확인 일시·판단 사유 기록",
      "- 한국 공통 출처 5개는 우선 심사, HRD Korea 다국가 출처 2건은 인도네시아 적용 범위 확인, 다른 나라 5개는 해당 국가 담당 검토 항목으로 유지",
      "- 시험등록 서류, 2025 제조업, 2026 어업/Root Industry/특별시험, 9월 선택적 Skill Test 첨부는 2026 일반 제조업 **최종** 구직등록 서류로 승격 금지",
      "- 실제 공식 최종 목록과 서명된 서류별 판정을 확보하기 전에는 `job_docs` HOLD 해제 금지",
      "- 서명 후에도 별도 승인된 후보 실서비스 배포, 동일 SHA 9/9, HTTPS 6/6, 운영자 베타 OPEN 승인 필요",
      "",
      "**현재:** 전 항목 사람 검토 PENDING / 최종 2026 제조업 구직신청 서류 HOLD / Draft PR 미병합 / 공개 베타 HOLD.",
      ""])
    return "\n".join(txt)
def selftest():
    inp=source_inputs()
    # Use stored dated M30 original feed identity via a generated synthetic
    # 320-row list is deliberately NOT used; only actual retrieved output may be
    # saved. Test strict validation of the actual prior M34 packet after --run.
    if not OUT.exists():
        validate_inputs(inp)
        print("M34_SIGNOFF_INPUTS_SELF_TEST_PASS 20_unsigned_tasks 10_release_gates source_12 beta_HOLD")
        return
    p=read("research/source_reviews/indonesia_m34_unsigned_release_review_packet_2026-10-17.json")
    verify(p,inp)
    attacks=[
       lambda x:x.update(releaseAuthorized=True),
       lambda x:x.update(publicBetaAccess="open"),
       lambda x:x.update(officialSourceInterpretationSigned=True),
       lambda x:x.update(official2026FinalManufacturingDocumentChecklistVerified=True),
       lambda x:x.update(manualReviewerName="invented"),
       lambda x:x.update(sourceHashAutoAccepted=True),
       lambda x:x.update(candidateDeployed=True),
       lambda x:x["reviewTasks"][0].update(semanticDecision="approved"),
       lambda x:x["reviewTasks"][0].update(reviewerName="invented"),
       lambda x:x["reviewTasks"][0].update(approvedOfficialSourceHash=True),
       lambda x:x["reviewTasks"][0].update(officialOriginalUrl="https://fake.invalid"),
       lambda x:x["releaseGates"][0].update(observedStatus="PENDING"),
       lambda x:x["releaseGates"].pop(),
       lambda x:x["releaseGates"].append(copy.deepcopy(x["releaseGates"][0])),
       lambda x:x.update(officialIndexCheckedRows=319),
       lambda x:x.update(matchesM30TitleUrlSha256=False),
       lambda x:x["explicitFinalManufacturingApplicationHeadlineCandidates"].append({"humanReviewer":None,"verifiedExactFinalJobDocuments":False}),
    ]
    for i,fn in enumerate(attacks):
        fake=copy.deepcopy(p);fn(fake)
        try:verify(fake,inp)
        except (ValueError,KeyError,TypeError):pass
        else:raise AssertionError("dangerous reviewer packet mutation accepted "+str(i))
    print("M34_SIGNOFF_HANDOFF_SELF_TEST_PASS 17_fail_closed_cases 20_human_Pending 10_release_gates BETA_HOLD")
def main():
    cli=argparse.ArgumentParser()
    for field in ["self-test","run","check"]:cli.add_argument("--"+field,action="store_true")
    a=cli.parse_args()
    if a.self_test:selftest()
    if a.run:
        need(not OUT.exists() and not REPORT.exists(),"append-only outputs must be new")
        now=datetime.now(timezone.utc).isoformat()
        need(datetime.fromisoformat(now).astimezone(ZoneInfo("Asia/Jakarta")).date().isoformat()==DAY,
             "today Jakarta")
        rows,total=retrieve()
        packet=build(source_inputs(),rows,total,now)
        OUT.write_text(json.dumps(packet,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
        REPORT.write_text(render(packet),encoding="utf-8")
        print("M34_REVIEW_PACKET_WRITTEN",packet["officialIndexCheckedRows"],"titles",
              packet["pendingReviewTasks"],"tasks",packet["liveGateCount"],"gates",
              "same_old_digest",packet["matchesM30TitleUrlSha256"],
              "explicit_final_candidates",len(packet["explicitFinalManufacturingApplicationHeadlineCandidates"]),
              "beta_HOLD",flush=True)
    if a.check:
        packet=read("research/source_reviews/indonesia_m34_unsigned_release_review_packet_2026-10-17.json")
        verify(packet,source_inputs())
        need(REPORT.read_text(encoding="utf-8")==render(packet),"operator memo mismatch")
        print("M34_REVIEW_PACKET_INTEGRITY_PASS 20_unsigned_tasks 10_release_gates beta_HOLD")
    if not(a.self_test or a.run or a.check):cli.error("select action")
if __name__=="__main__":main()
