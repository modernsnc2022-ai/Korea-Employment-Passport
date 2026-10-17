#!/usr/bin/env python3
"""M30: read-only 2026 KP2MI post-Skill-Test & e-certificate candidate discovery.

Title metadata creates MANUAL REVIEW candidates only. No final Manufacturing
job_docs determination; no SHA baseline acceptance, no signed release, no beta.
"""
from __future__ import annotations
import argparse, copy, json, re
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
from urllib.parse import urlsplit
from zoneinfo import ZoneInfo
from audit_id_manufacturing_notice_index_live import (
    retrieve, validate_snapshot, classify, title_text, year_from_row,
)
ROOT=Path(__file__).resolve().parents[1]
DAY="2026-10-17"
OUTPUT=ROOT/"research/source_reviews/indonesia_m30_post_skill_notice_candidates_2026-10-17.json"
INDEX="https://kp2mi.go.id/gtog-korea/pengumuman"
SECTOR=re.compile(r"MANUFAKTUR|MANUFACTURING|PABRIK",re.I)
MFG_ROUTE=re.compile(r"UBT\s*UMUM|EPS[\s-]*TOPIK|G[\s-]*TO[\s-]*G|KOREA|SKILL\s*TEST",re.I)
FINISH=re.compile(r"HASIL\s+AKHIR|HASIL\s+(UJIAN|PENILAIAN)\s+(?:SKILL\s*TEST|TAHAP\s*(?:2|II))|"
                  r"(?:PENGUMUMAN\s+)?KELULUSAN\s+(?:AKHIR|SKILL\s*TEST)|LULUS\s+SKILL\s*TEST",re.I)
APPLY=re.compile(r"LAMARAN\s+ONLINE|PENGAJUAN\s+LAMARAN|"
                 r"BERKAS\s+LAMARAN|DOKUMEN\s+LAMARAN|"
                 r"E[\s-]?SERTIFIKAT|SERTIFIKAT\s+KELULUSAN",re.I)
SKILL=re.compile(r"SKILL\s*TEST|UJI\s*KOMPETENSI|PENILAIAN\s+KOMPETENSI",re.I)
OTHER=re.compile(r"PERIKANAN|FISHERIES|ROOT\s+INDUSTRY|UBT\s+KHUSUS|"
                 r"PERTANIAN|KONSTRUKSI|GALANGAN\s+KAPAL",re.I)
EXPLICIT_FINAL=re.compile(r"LAMARAN\s+ONLINE|PENGAJUAN\s+LAMARAN|"
                          r"BERKAS\s+LAMARAN|DOKUMEN\s+LAMARAN",re.I)
def require(x,msg):
    if not x:raise ValueError("M30_FUTURE_NOTICE_FAIL_CLOSED "+msg)
def read(p):return json.loads((ROOT/p).read_text(encoding="utf-8-sig"))
def tagged(row):
    c=classify(row)
    title=c["title"]
    if year_from_row(row)!=2026 or not re.search(r"\b2026\b",title):
        return None
    sector=bool(SECTOR.search(title))
    other=bool(OTHER.search(title))
    # A mixed sector/title is never automatically assigned to Manufacturing.
    mixed=sector and other
    process=bool(FINISH.search(title) or APPLY.search(title) or SKILL.search(title))
    if not process:return None
    match=bool(MFG_ROUTE.search(title))
    if sector and not other and match:
        stage=("manufacturing_final_application_title_candidate" if EXPLICIT_FINAL.search(title)
          else "manufacturing_final_result_or_certificate_review" if FINISH.search(title) or APPLY.search(title)
          else "manufacturing_skill_test_related_review")
        urgency="P1" if stage!="manufacturing_skill_test_related_review" else "P2"
        reason="sector-title-only_2026_no_document_inference"
    elif other and not mixed:
        stage="other_cohort_excluded";urgency="P3";reason="different_country_sector_or_exam_cohort"
    elif mixed:
        stage="mixed_sector_requires_manual_attribution";urgency="P1";reason="mixed_fisheries_manufacturing_do_not_import"
    elif APPLY.search(title) or FINISH.search(title):
        stage="generic_final_application_or_certificate_manual_scope_review";urgency="P1"
        reason="title_omits_exact_indonesia_general_manufacturing_cohort"
    else:
        return None
    parsed=urlsplit(c["url"])
    require(parsed.scheme=="https" and parsed.hostname in {"kp2mi.go.id","www.kp2mi.go.id"}
         and parsed.path.startswith("/gtog-detail/korea/"),"official detail URL")
    return {"noticeId":str(c["id"]),"date":c["date"],"title":title,
            "url":c["url"],"screeningStage":stage,"priority":urgency,"why":reason,
            "humanReviewer":None,"verifiedExactFinalJobDocuments":False,
            "authorizesAppRuleUpdate":False,"semanticReview":"pending"}
def build(rows,total,baseline,sign,review_ledger,now_iso):
    now=datetime.fromisoformat(now_iso)
    require(now.astimezone(ZoneInfo("Asia/Jakarta")).date().isoformat()==DAY,"Jakarta observation day")
    report=validate_snapshot(rows,total,checked_at=now_iso)
    require(len(rows)==320 and total>=len(rows) and year_from_row(rows[0])==2026
       and year_from_row(rows[-1])==2025,"official index period coverage and pagination")
    require(sign["status"]=="pending_manual_source_signoff"
       and sign["reviewer"] is None and sign["approvedAt"] is None
       and sign["betaAccess"]=="hold","official sources unsigned")
    require(baseline["observedAtJakartaDate"]==DAY
       and baseline["generalManufacturingTitlesCount"]==7
       and baseline["generalManufacturingFinalOnlineJobApplicationTitleCount"]==0
       and baseline["jobDocs"]=="hold" and baseline["betaAccess"]=="hold","M24 same-cohort HOLD")
    require(review_ledger["asOf"]==DAY and len(review_ledger["tasks"])==20
       and review_ledger["pendingSourceAlertCount"]==12
       and review_ledger["pendingNoticeBodyReviewCount"]==7
       and review_ledger["pendingFinalJobDocsGateCount"]==1
       and review_ledger["finalManufacturingJobDocs"]=="hold"
       and review_ledger["humanPolicyReviewApproved"] is False,"M26 20 unsigned tasks")
    classified=[classify(x) for x in rows]
    known_urls={x["url"] for x in baseline["generalManufacturingTitles"]}
    exclude_urls={x["url"] for x in baseline["otherCohortOnlineApplicationNotices"]}
    all_urls={x["url"] for x in classified}
    require(known_urls <= all_urls and exclude_urls <= all_urls,"previous 2026 cohort notices absent")
    candidates=[x for r in rows if (x:=tagged(r)) is not None]
    candidates.sort(key=lambda x:(x["priority"],x["date"],x["noticeId"]))
    require(len({x["noticeId"] for x in candidates})==len(candidates),"duplicate official IDs")
    target=[x for x in candidates if x["screeningStage"].startswith("manufacturing_")]
    mixed=[x for x in candidates if x["screeningStage"]=="mixed_sector_requires_manual_attribution"]
    generic=[x for x in candidates if x["screeningStage"]=="generic_final_application_or_certificate_manual_scope_review"]
    excluded=[x for x in candidates if x["screeningStage"]=="other_cohort_excluded"]
    explicit=[x for x in target if x["screeningStage"]=="manufacturing_final_application_title_candidate"]
    # Genuine new alerts must not be silently declared approved, even with candidate titles.
    packet={
     "version":"1.0.0","observationDateJakarta":DAY,"source":INDEX,
     "observedAtUtc":now_iso,"officialIndexRowsChecked":len(rows),
     "officialHistoricalNoticeCount":total,
     "firstPostedDate":str(rows[0]["tanggal"]),"oldestPostedDate":str(rows[-1]["tanggal"]),
     "titleUrlSha256":report["titleUrlDigestSha256"],
     "previousM24TitleUrlSha256":baseline["titleUrlDigestSha256"],
     "titleIndexChangedFromM24":report["titleUrlDigestSha256"]!=baseline["titleUrlDigestSha256"],
     "known2026ManufacturingUrlsPreserved":len(known_urls),
     "targetRelatedTitles":len(target),
     "targetExplicitFinalApplicationTitles":len(explicit),
     "genericAmbiguousTitles":len(generic),
     "mixedSectorTitles":len(mixed),
     "otherCohortTitlesExcluded":len(excluded),
     "titleCandidates":candidates,
     "humanPolicySemanticsApproved":False,
     "exactManufacturingFinalJobDocuments":"hold",
     "currentCycleFinalDocsVerified":False,
     "sourceHashAutoAccepted":False,
     "allowApplicantFinalJobApplicationSubmit":False,
     "betaAccess":"hold","releaseAuthorized":False,
     "warning":"Title detection for final results, e-certificates, generic and mixed-sector notices ONLY queues human review. A headline cannot verify post-Skill Test Manufacturing job files, PDF page contents, release date or authorized beta.",
    }
    validate(packet)
    return packet
def validate(packet, *, allow_original_legacy_psychology=False):
    # Read-only ORIGINAL M30 evidence predates the narrower psychology filter.
    # Legacy compatibility is explicitly permitted only for its exact saved
    # original 320-row digest and two named psychology-only false positives.
    if allow_original_legacy_psychology:
        prior=read("research/source_reviews/indonesia_m24_manufacturing_title_scope_2026-10-17.json")
        require(packet["titleUrlSha256"]==prior["titleUrlDigestSha256"]
            and packet["genericAmbiguousTitles"]==2
            and len(packet["titleCandidates"])==11,
            "legacy M30 only allowed for original observation")
    require(packet["observationDateJakarta"]==DAY and packet["officialIndexRowsChecked"]==320
       and packet["known2026ManufacturingUrlsPreserved"]==7
       and re.fullmatch("[0-9a-f]{64}",packet["titleUrlSha256"]),"official range")
    all_=packet["titleCandidates"]
    require(len({x["noticeId"] for x in all_})==len(all_),"duplicate candidates")
    for x in all_:
        updated=tagged({"id":x["noticeId"],"tanggal":x["date"],
          "judul":'<a href="'+x["url"]+'">'+x["title"]+"</a>"})
        legacy=(allow_original_legacy_psychology and updated is None
          and x["date"] in {"15 July 2026","4 September 2026"}
          and "PSIKOLOGI" in x["title"].upper()
          and "KELULUSAN" in x["title"].upper()
          and x["screeningStage"]=="generic_final_application_or_certificate_manual_scope_review")
        require((updated==x or legacy)
          and x["humanReviewer"] is None and x["semanticReview"]=="pending"
          and x["verifiedExactFinalJobDocuments"] is False
          and x["authorizesAppRuleUpdate"] is False,"no automatic policy decision")
    require(packet["targetRelatedTitles"]==sum(x["screeningStage"].startswith("manufacturing_") for x in all_)
        and packet["targetExplicitFinalApplicationTitles"]==
           sum(x["screeningStage"]=="manufacturing_final_application_title_candidate" for x in all_)
        and packet["genericAmbiguousTitles"]==
           sum(x["screeningStage"]=="generic_final_application_or_certificate_manual_scope_review" for x in all_)
        and packet["mixedSectorTitles"]==
           sum(x["screeningStage"]=="mixed_sector_requires_manual_attribution" for x in all_)
        and packet["otherCohortTitlesExcluded"]==
           sum(x["screeningStage"]=="other_cohort_excluded" for x in all_),
         "candidate count integrity")
    require(packet["humanPolicySemanticsApproved"] is False and
       packet["currentCycleFinalDocsVerified"] is False
       and packet["sourceHashAutoAccepted"] is False
       and packet["exactManufacturingFinalJobDocuments"]=="hold"
       and packet["allowApplicantFinalJobApplicationSubmit"] is False
       and packet["betaAccess"]=="hold"
       and packet["releaseAuthorized"] is False,"release/approval guards")
    return True
def selftest():
    def row(n,title,date="17 October 2026"):
        return {"id":n,"tanggal":date,
                "judul":'<a href="/gtog-detail/korea/demo-'+str(n)+'">'+title+'</a>'}
    cases=[
      ("HASIL AKHIR SKILL TEST UBT UMUM SEKTOR MANUFAKTUR 2026",
       "manufacturing_final_result_or_certificate_review"),
      ("PEMBAGIAN E-SERTIFIKAT UBT UMUM SEKTOR MANUFAKTUR 2026",
       "manufacturing_final_result_or_certificate_review"),
      ("PENGAJUAN LAMARAN ONLINE SEKTOR MANUFAKTUR EPS TOPIK 2026",
       "manufacturing_final_application_title_candidate"),
      ("PENGAJUAN LAMARAN ONLINE G-TO-G KOREA 2026",
       "generic_final_application_or_certificate_manual_scope_review"),
      ("PENGAJUAN LAMARAN ONLINE SEKTOR PERIKANAN 2026","other_cohort_excluded"),
      ("HASIL AKHIR SKILL TEST UBT UMUM MANUFAKTUR DAN PERIKANAN 2026",
       "mixed_sector_requires_manual_attribution"),
      ("UJIAN SKILL TEST UBT UMUM MANUFAKTUR 2026",
       "manufacturing_skill_test_related_review"),
      ("PENGAJUAN LAMARAN ONLINE UBT KHUSUS 2026","other_cohort_excluded")
    ]
    for i,(title,expected) in enumerate(cases,1):
        t=tagged(row(i,title));require(t and t["screeningStage"]==expected,"classification case "+str(i))
        require(t["verifiedExactFinalJobDocuments"] is False,"no fake documents")
    require(tagged(row(91,"PENGAJUAN LAMARAN ONLINE MANUFAKTUR 2025",
       "17 October 2026")) is None,"2025 cohort must not be considered 2026")
    require(tagged(row(92,"2026 UBT UMUM MANUFAKTUR TANPA PROSES", "17 October 2026")) is None,
       "generic passive headline must not create final-doc evidence")
    require(tagged(row(93,"PENGUMUMAN KETENTUAN PEMERIKSAAN PSIKOLOGI KELULUSAN SEBELUM TAHUN 2026 DAN KELULUSAN 2026")) is None,
       "psychology guidance cannot imply final skill test or online application")
    require(tagged(row(94,"PENGAJUAN SECOND OPINION PEMERIKSAAN PSIKOLOGI KELULUSAN SEBELUM TAHUN 2026")) is None,
       "psychology appeal does not establish final job documents")
    invalid=tagged(row(101,cases[0][0]))
    require(invalid is not None,"sample candidate")
    baseline={"version":"1.0.0","observationDateJakarta":DAY,"source":INDEX,
       "observedAtUtc":"2026-10-17T05:10:00+00:00","officialIndexRowsChecked":320,
       "officialHistoricalNoticeCount":2877,"firstPostedDate":"17 October 2026",
       "oldestPostedDate":"16 July 2025","titleUrlSha256":"1"*64,
       "previousM24TitleUrlSha256":"1"*64,"titleIndexChangedFromM24":False,
       "known2026ManufacturingUrlsPreserved":7,"targetRelatedTitles":1,
       "targetExplicitFinalApplicationTitles":0,"genericAmbiguousTitles":0,
       "mixedSectorTitles":0,"otherCohortTitlesExcluded":0,"titleCandidates":[invalid],
       "humanPolicySemanticsApproved":False,
       "exactManufacturingFinalJobDocuments":"hold","currentCycleFinalDocsVerified":False,
       "sourceHashAutoAccepted":False,"allowApplicantFinalJobApplicationSubmit":False,
       "betaAccess":"hold","releaseAuthorized":False}
    validate(baseline)
    changes=[
       lambda a:a.update(releaseAuthorized=True),
       lambda a:a.update(betaAccess="open"),
       lambda a:a.update(allowApplicantFinalJobApplicationSubmit=True),
       lambda a:a.update(exactManufacturingFinalJobDocuments="approved"),
       lambda a:a.update(currentCycleFinalDocsVerified=True),
       lambda a:a.update(humanPolicySemanticsApproved=True),
       lambda a:a.update(sourceHashAutoAccepted=True),
       lambda a:a["titleCandidates"][0].update(humanReviewer="fake"),
       lambda a:a["titleCandidates"][0].update(semanticReview="approved"),
       lambda a:a["titleCandidates"][0].update(verifiedExactFinalJobDocuments=True),
       lambda a:a["titleCandidates"][0].update(authorizesAppRuleUpdate=True),
       lambda a:a.update(known2026ManufacturingUrlsPreserved=6),
       lambda a:a.update(targetExplicitFinalApplicationTitles=1)
    ]
    for i,change in enumerate(changes):
        temp=copy.deepcopy(baseline);change(temp)
        try:validate(temp)
        except (ValueError,KeyError,TypeError):pass
        else:raise AssertionError("unsafe M30 mutation case "+str(i))
    print("M30_FINAL_NOTICE_SENTINEL_SELF_TEST_PASS 8_future_notice_examples 13_fail_closed_mutations")
def main():
    p=argparse.ArgumentParser()
    for key in ("self-test","run","check"):p.add_argument("--"+key,action="store_true")
    a=p.parse_args()
    if a.self_test:selftest()
    if a.run:
       require(not OUTPUT.exists(),"append-only snapshot exists")
       time=datetime.now(timezone.utc).isoformat()
       require(datetime.fromisoformat(time).astimezone(ZoneInfo("Asia/Jakarta")).date().isoformat()==DAY,"Jakarta date")
       rows,total=retrieve()
       prior=read("research/source_reviews/indonesia_m24_manufacturing_title_scope_2026-10-17.json")
       sign=read("recruitment/ID_BETA_SOURCE_SIGNOFF_20261017.json")
       work=read("research/source_reviews/indonesia_m26_unsigned_review_handoff_2026-10-17.json")
       snapshot=build(rows,total,prior,sign,work,time)
       OUTPUT.write_text(json.dumps(snapshot,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
       print("M30_OFFICIAL_INDEX_SNAPSHOT",snapshot["officialIndexRowsChecked"],"of",total,
           "mfg_related",snapshot["targetRelatedTitles"],
           "explicit_final_title_candidates",snapshot["targetExplicitFinalApplicationTitles"],
           "generic",snapshot["genericAmbiguousTitles"],
           "mixed",snapshot["mixedSectorTitles"],"other",snapshot["otherCohortTitlesExcluded"],
           "changed_vs_M24",snapshot["titleIndexChangedFromM24"],
           "job_docs_HOLD beta_HOLD",flush=True)
       for cand in snapshot["titleCandidates"]:
           print("M30",cand["screeningStage"],cand["date"],cand["title"][:165],flush=True)
    if a.check:
       packet=read("research/source_reviews/indonesia_m30_post_skill_notice_candidates_2026-10-17.json")
       validate(packet, allow_original_legacy_psychology=True)
       print("M30_POST_SKILL_SENTINEL_RECORD_PASS unchanged_final_docs_hold")
    if not (a.self_test or a.run or a.check):p.error("choose action")
if __name__=="__main__":main()
