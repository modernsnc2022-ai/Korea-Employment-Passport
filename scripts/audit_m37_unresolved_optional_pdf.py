#!/usr/bin/env python3
"""M37 official 2026 Manufacturing index parity + bounded PDF recovery.
Original PDF bytes stay in temporary local cache; no private candidate data
or human source approval; never an application job-doc rule.
"""
from __future__ import annotations
import argparse,copy,hashlib,json,re,subprocess,tempfile
from datetime import datetime,timezone
from pathlib import Path
from urllib.parse import urlsplit
from zoneinfo import ZoneInfo
import fitz
from audit_id_manufacturing_notice_index_live import retrieve,validate_snapshot
from audit_m30_manufacturing_post_skill_notice_sentinel import tagged
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"research/source_reviews/indonesia_m37_official_late_pdf_retry_2026-10-17.json"
DAY="2026-10-17"
RETRY="https://kp2mi.go.id/uploads/gtgkorea/images/data_17-09-2026_CONTOH_SCAN_DOKUMEN_KOMPTENSI_YANG_BENAR.pdf"
INDEX="https://kp2mi.go.id/gtog-korea/pengumuman"
TMP=Path(tempfile.gettempdir())/"kep_m37_official_recovery_20261017"
def data(p):return json.loads((ROOT/p).read_text(encoding="utf-8-sig"))
def ensure(x,name):
    if not x:raise ValueError("M37_OFFICIAL_PDF_NO_AUTO_RELEASE "+name)
def history():
    old=data("research/source_reviews/indonesia_m36_sept_2026_official_pdf_stage_audit_2026-10-17.json")
    m34=data("research/source_reviews/indonesia_m34_unsigned_release_review_packet_2026-10-17.json")
    m35=data("research/source_reviews/indonesia_m35_final_job_docs_evidence_template_2026-10-17.json")
    m33=data("research/source_reviews/indonesia_m33_exact_final_job_docs_preflight_2026-10-17.json")
    signer=data("recruitment/ID_BETA_SOURCE_SIGNOFF_20261017.json")
    ensure(old["newSuccessfulOriginalPdfBodies"]==2 and old["newInconclusiveOriginalPdfBodies"]==1
        and old["officialAttachmentCount"]==7 and old["publicBetaAccess"]=="hold","M36 6/7 read")
    missing=[x for x in old["officialAnnexes"] if x["download"].startswith("inconclusive")]
    ensure(len(missing)==1 and missing[0]["officialPdfUrl"]==RETRY
       and missing[0]["noticeDate"]=="2026-09-17"
       and missing[0]["noticeAttachmentStage"]=="optional_job_capacity_competency_evidence_not_final_job_docs",
       "one optional competency preview only")
    ensure(m34["matchesM30TitleUrlSha256"] and
       len(m34["explicitFinalManufacturingApplicationHeadlineCandidates"])==0
       and len(m34["reviewTasks"])==20
       and m34["publicBetaAccess"]=="hold","prior official index")
    ensure(m35["sourceEvidenceStatus"]=="official_2026_final_notice_not_established"
       and m35["source"]["requiredDocuments"]==[]
       and m35["releaseAuthorized"] is False,"no job documents")
    ensure(next(x for x in m33["gates"]
       if x["id"]=="exact_2026_manufacturing_final_job_documents")["status"]=="PENDING"
       and m33["authorizesRelease"] is False,"independent gate")
    ensure(signer["reviewer"] is None and signer["approvedAt"] is None
       and signer["betaAccess"]=="hold","no original signoff")
    return m34,missing[0]
def urls_checked():
    u=urlsplit(RETRY)
    ensure(u.scheme=="https" and u.hostname=="kp2mi.go.id"
       and u.path.startswith("/uploads/gtgkorea/images/")
       and u.path.lower().endswith(".pdf") and not u.fragment,
       "exact official PDF host/path")
def retry(run=False):
    record={"url":RETRY,"scope":"2026_09_17_optional_job_capacity_document_scan_example",
      "attempt":"not_started","originalPdfSha256":None,"originalBytes":None,"pdfPages":None,
      "firstPageRenderedToLocalTempOnly":False,"individualNamesStored":False,
      "applicationDocumentsEstablished":False,"officialPolicySigned":False}
    if not run:return record
    urls_checked()
    TMP.mkdir(parents=True,exist_ok=True)
    p=TMP/"M37_PUBLIC_OPTIONAL_COMPETENCY_ORIGINAL.pdf"
    command=["curl.exe","--fail","--location","--connect-timeout","9",
      "--max-time","78","--max-filesize","18000000","--retry","0",
      "--silent","--show-error","--output",str(p),RETRY]
    try:
        completed=subprocess.run(command,capture_output=True,text=True,timeout=86)
        if completed.returncode!=0:
            record.update(attempt="inconclusive_remote_timeout_or_error",
                curlExitCode=completed.returncode)
            return record
        original=p.read_bytes()
        ensure(original.startswith(b"%PDF-") and 100<len(original)<=18000000,"full PDF")
        pdf=fitz.open(stream=original,filetype="pdf")
        try:
            ensure(0<len(pdf)<=180,"PDF readable pages")
            pages=len(pdf)
            pdf[0].get_pixmap(matrix=fitz.Matrix(0.65,0.65),alpha=False).save(
                str(TMP/"M37_PUBLIC_OPTIONAL_COMPETENCY_TEMP_PREVIEW.png"))
        finally:pdf.close()
        record.update(attempt="official_pdf_bytes_verified",
            originalPdfSha256=hashlib.sha256(original).hexdigest(),
            originalBytes=len(original),pdfPages=pages,
            firstPageRenderedToLocalTempOnly=True)
    except Exception as err:
        record.update(attempt="inconclusive_remote_timeout_or_error",
                      errorClass=type(err).__name__)
    finally:
        # Ensure no binary or rendered page is retained or shared.
        p.unlink(missing_ok=True)
        (TMP/"M37_PUBLIC_OPTIONAL_COMPETENCY_TEMP_PREVIEW.png").unlink(missing_ok=True)
    return record
def make(do_live=False):
    m34,_=history()
    timestamp=datetime.now(timezone.utc).isoformat()
    ensure(datetime.fromisoformat(timestamp).astimezone(
        ZoneInfo("Asia/Jakarta")).date().isoformat()==DAY,"2026-10-17 WIB")
    notice={"retrieval":"not_requested","titleRows":None,"historicalTotal":None,
      "titleUrlSha256":None,"sameAsM34":None,
      "explicitGeneralManufacturingFinalApplicationCandidates":None,
      "unscopedReviewCandidates":None,"sourceReviewedByHuman":False}
    if do_live:
        rows,total=retrieve()
        summary=validate_snapshot(rows,total,checked_at=timestamp)
        latest=[tagged(r) for r in rows]
        ensure(len(rows)==320,"live bounded index cannot silently shift")
        notice.update(retrieval="official_index_read_only",titleRows=len(rows),
          historicalTotal=total,titleUrlSha256=summary["titleUrlDigestSha256"],
          sameAsM34=summary["titleUrlDigestSha256"]==m34["officialTitleUrlSha256"],
          explicitGeneralManufacturingFinalApplicationCandidates=sum(
             x is not None and x["screeningStage"]=="manufacturing_final_application_title_candidate" for x in latest),
          unscopedReviewCandidates=sum(x is not None and x["screeningStage"] in
             {"generic_final_application_or_certificate_manual_scope_review",
              "mixed_sector_requires_manual_attribution"} for x in latest))
    pdf=retry(run=do_live)
    obj={"version":"1.0.0","evidenceDateJakarta":DAY,
       "sourceType":"original_official_index_and_optional_scan_example_retry",
       "timestampUtc":timestamp,"officialIndexUrl":INDEX,"index":notice,
       "retryPdf":pdf,"previouslyVerifiedRelatedOfficialPdfBytes":6,
       "allSevenRelatedPdfBytesVerified":False,
       "final2026ManufacturingPostSkillTestJobDocsVerified":False,
       "manualSourceInterpretationApproved":False,"automaticSourceShaAcceptance":False,
       "candidateDeployed":False,"publicBetaAccess":"hold","releaseAuthorized":False,
       "limitations":"Exactly one 2026-09-17 optional Job Capacity Assessment scan-example PDF retried. A PDF fetch does not prove semantic applicability to final post-Skill-Test Manufacturing job application requirements. Bounded official title index also does not inspect all original notice annexes."}
    obj["allSevenRelatedPdfBytesVerified"]=pdf["attempt"]=="official_pdf_bytes_verified"
    validate(obj)
    return obj
def validate(o):
    m34,_=history()
    ensure(o["evidenceDateJakarta"]==DAY and o["officialIndexUrl"]==INDEX
        and o["sourceType"]=="original_official_index_and_optional_scan_example_retry"
        and o["previouslyVerifiedRelatedOfficialPdfBytes"]==6,
        "M36->M37 lineage")
    index=o["index"];pdf=o["retryPdf"]
    ensure(pdf["url"]==RETRY
        and pdf["scope"]=="2026_09_17_optional_job_capacity_document_scan_example"
        and pdf["individualNamesStored"] is False
        and pdf["applicationDocumentsEstablished"] is False
        and pdf["officialPolicySigned"] is False,"PDF scope no personal data")
    if pdf["attempt"]=="official_pdf_bytes_verified":
        ensure(isinstance(pdf["originalPdfSha256"],str) and
            bool(re.fullmatch("[0-9a-f]{64}",pdf["originalPdfSha256"]))
            and type(pdf["originalBytes"]) is int and 100<pdf["originalBytes"]<=18000000
            and type(pdf["pdfPages"]) is int and 1<=pdf["pdfPages"]<=180
            and pdf["firstPageRenderedToLocalTempOnly"] is True,
            "successful PDF byte evidence")
    else:
        ensure(pdf["attempt"] in {"not_started","inconclusive_remote_timeout_or_error"}
            and pdf["originalPdfSha256"] is None and pdf["pdfPages"] is None
            and pdf["originalBytes"] is None,
            "inconclusive cannot fabricate SHA or page count")
    if index["retrieval"]=="official_index_read_only":
        ensure(index["titleRows"]==320 and index["historicalTotal"]>=320
            and index["titleUrlSha256"]==m34["officialTitleUrlSha256"]
            and index["sameAsM34"] is True
            and index["explicitGeneralManufacturingFinalApplicationCandidates"]==0
            and index["unscopedReviewCandidates"]==0,
            "official index unchanged, no final applicant notice")
    else:
        ensure(index["retrieval"]=="not_requested" and index["titleRows"] is None,
               "inconclusive index not assumed")
    ensure(index["sourceReviewedByHuman"] is False
        and o["allSevenRelatedPdfBytesVerified"]==(pdf["attempt"]=="official_pdf_bytes_verified")
        and o["final2026ManufacturingPostSkillTestJobDocsVerified"] is False
        and o["manualSourceInterpretationApproved"] is False
        and o["automaticSourceShaAcceptance"] is False
        and o["candidateDeployed"] is False and o["publicBetaAccess"]=="hold"
        and o["releaseAuthorized"] is False,"release/status safety")
def selftest():
    ex=make()
    changes=[
      lambda x:x.update(publicBetaAccess="open"),
      lambda x:x.update(releaseAuthorized=True),
      lambda x:x.update(final2026ManufacturingPostSkillTestJobDocsVerified=True),
      lambda x:x.update(manualSourceInterpretationApproved=True),
      lambda x:x.update(automaticSourceShaAcceptance=True),
      lambda x:x.update(allSevenRelatedPdfBytesVerified=True),
      lambda x:x["retryPdf"].update(attempt="official_pdf_bytes_verified"),
      lambda x:x["retryPdf"].update(url="https://fake.invalid/doc.pdf"),
      lambda x:x["retryPdf"].update(applicationDocumentsEstablished=True),
      lambda x:x["retryPdf"].update(individualNamesStored=True),
      lambda x:x["index"].update(retrieval="official_index_read_only"),
      lambda x:x.update(previouslyVerifiedRelatedOfficialPdfBytes=7),
    ]
    for n,f in enumerate(changes):
        z=copy.deepcopy(ex);f(z)
        try:validate(z)
        except (ValueError,KeyError,TypeError):pass
        else:raise AssertionError("unsafe M37 status accepted "+str(n))
    print("M37_ORIGINAL_PDF_RETRY_SELF_TEST_PASS 12_fail_closed_cases beta_HOLD")
def main():
    a=argparse.ArgumentParser()
    for v in ["self-test","run","check"]:a.add_argument("--"+v,action="store_true")
    options=a.parse_args()
    if options.self_test:selftest()
    if options.run:
        ensure(not OUT.exists(),"append-only prior output must not overwrite")
        z=make(do_live=True)
        OUT.write_text(json.dumps(z,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
        print("M37_LIVE_RESULT index_sha_same",z["index"]["sameAsM34"],
           "manufacturing_final_title",z["index"]["explicitGeneralManufacturingFinalApplicationCandidates"],
           "optional_pdf",z["retryPdf"]["attempt"],
           "pages",z["retryPdf"]["pdfPages"],
           "releaseAuthorized",z["releaseAuthorized"],flush=True)
    if options.check:
        z=data("research/source_reviews/indonesia_m37_official_late_pdf_retry_2026-10-17.json")
        validate(z)
        print("M37_ORIGINAL_EVIDENCE_RECORD_INTEGRITY_PASS no_policy_import")
    if not(options.self_test or options.run or options.check):a.error("select action")
if __name__=="__main__":main()
