#!/usr/bin/env python3
"""M37 reconcile seven stage-scoped official PDF original SHA records.
Byte-read proof only: NEVER source-policy signoff or 2026 FINAL job application.
"""
import argparse,copy,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def data(name):return json.loads((ROOT/name).read_text(encoding="utf-8-sig"))
def check(flag,msg):
    if not flag:raise ValueError("M37_PDF_LINEAGE_BLOCK "+msg)
def inputs():
    return [data("research/source_reviews/"+n) for n in (
      "indonesia_m23_priority_pdf_body_audit_2026-10-17.json",
      "indonesia_m36_sept_2026_official_pdf_stage_audit_2026-10-17.json",
      "indonesia_m37_official_late_pdf_retry_2026-10-17.json")]
def verify(a,b,c):
    check(a["fetchedAndOpenedPdfBodies"]==6 and
      a["exactFinalManufacturingJobDocs"]=="hold"
      and a["sourceBaselineAutoAccepted"] is False,"M23")
    check(b["officialAttachmentCount"]==7 and
      b["newSuccessfulOriginalPdfBodies"]==2 and
      b["newInconclusiveOriginalPdfBodies"]==1
      and b["stageOne2026NotFinal"] is True
      and b["optionalSkillsNotFinalJobDocs"] is True
      and b["publicBetaAccess"]=="hold","M36")
    check(c["index"]["sameAsM34"] is True
      and c["index"]["explicitGeneralManufacturingFinalApplicationCandidates"]==0
      and c["retryPdf"]["attempt"]=="official_pdf_bytes_verified"
      and c["retryPdf"]["pdfPages"]==8
      and c["publicBetaAccess"]=="hold"
      and c["releaseAuthorized"] is False
      and c["final2026ManufacturingPostSkillTestJobDocsVerified"] is False,
      "M37 no final docs")
    known={r["originalUrl"]:r for r in a["pdfRecords"] if r.get("pdfBodyRead")}
    seen=set()
    stageone=0
    live_count=0
    prior_count=0
    for record in b["officialAnnexes"]:
        url=record["officialPdfUrl"]
        check(url not in seen,"duplicate PDF")
        seen.add(url)
        check(url.startswith("https://kp2mi.go.id/uploads/gtgkorea/images/")
              and url.endswith(".pdf"),"official PDF URL")
        first=(record["noticeDate"]=="2026-09-10")
        if first:
            stageone+=1
            check(record["noticeAttachmentStage"]==
              "eps_topik_first_stage_pass_list_not_final"
              and record["namesOrIdentifiersCopied"] is False,"private pass list")
        else:
            check(record["noticeDate"]=="2026-09-17" and
              record["noticeAttachmentStage"]==
                "optional_job_capacity_competency_evidence_not_final_job_docs",
              "optional forms not final docs")
        if record["priorM23PdfBodyObserved"]:
            m=known[url]
            check(record["priorM23Sha256"]==m["sha256"] and
              bool(re.fullmatch("[0-9a-f]{64}",m["sha256"]))
              and 1<=m["pages"]<=150,"M23 prior original sha")
            prior_count+=1
        elif record["download"]=="official_original_pdf_body_read":
            check(bool(re.fullmatch("[0-9a-f]{64}",record["currentOriginalSha256"]))
              and record["currentPages"]>=1,"M36 original new")
            live_count+=1
        else:
            check(url==c["retryPdf"]["url"]
              and record["download"]=="inconclusive_timeout_or_network"
              and bool(re.fullmatch("[0-9a-f]{64}",c["retryPdf"]["originalPdfSha256"]))
              and c["retryPdf"]["originalBytes"]>100
              and c["retryPdf"]["pdfPages"]==8,"M37 recovered exact missing pdf")
        check(record["finalOnlineJobApplicationDocsConfirmed"] is False
          and record["officialHumanSignoff"] is False
          and record["namesOrIdentifiersCopied"] is False,
          "PDF byte success cannot approve job docs")
    check(len(seen)==7 and stageone==1 and live_count==2
          and prior_count==4 and c["allSevenRelatedPdfBytesVerified"] is True,
          "7/7 stage-scoped original byte proofs")
def selftest():
    a,b,c=inputs()
    verify(a,b,c)
    mutations=[
      lambda x:x[2].update(publicBetaAccess="open"),
      lambda x:x[2].update(releaseAuthorized=True),
      lambda x:x[2].update(final2026ManufacturingPostSkillTestJobDocsVerified=True),
      lambda x:x[2]["retryPdf"].update(originalPdfSha256="false"),
      lambda x:x[2]["retryPdf"].update(pdfPages=0),
      lambda x:x[2]["retryPdf"].update(url="https://fake.invalid/a.pdf"),
      lambda x:x[2]["index"].update(explicitGeneralManufacturingFinalApplicationCandidates=1),
      lambda x:x[1]["officialAnnexes"][0].update(noticeAttachmentStage="final_docs"),
      lambda x:x[1]["officialAnnexes"][0].update(namesOrIdentifiersCopied=True),
      lambda x:x[1]["officialAnnexes"][1].update(officialHumanSignoff=True),
      lambda x:x[1]["officialAnnexes"][1].update(finalOnlineJobApplicationDocsConfirmed=True),
      lambda x:x[1]["officialAnnexes"].pop(),
      lambda x:next(v for v in x[0]["pdfRecords"] if v["date"]=="2026-09-17" and v.get("pdfBodyRead")).update(sha256="0"*64),
    ]
    for i,fn in enumerate(mutations):
        vals=copy.deepcopy([a,b,c]);fn(vals)
        try:verify(*vals)
        except (ValueError,KeyError,TypeError):pass
        else:raise AssertionError("unsafe alteration accepted "+str(i))
    print("M37_SEVEN_OFFICIAL_PDF_LINEAGE_SELF_TEST_PASS 13_adversarial_cases 7_of_7_byte_metadata stage_segregated beta_HOLD")
if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--self-test",action="store_true")
    ap.add_argument("--check",action="store_true")
    args=ap.parse_args()
    if args.self_test:selftest()
    if args.check:
        verify(*inputs())
        print("M37_ALL_SEVEN_ORIGINAL_PDF_LINEAGE_PASS 4_M23_plus_2_M36_plus_1_M37 metadata_only no_2026_final_job_docs")
    if not(args.self_test or args.check):ap.error("action required")
