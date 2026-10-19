#!/usr/bin/env python3
"""M36 official PDF original-byte stage audit (no personal pass-list data persisted).

Never infer final job application documents from first-stage pass-list, optional
competency supporting forms, or PDF filename. HTTPS originals only; append-only.
"""
from __future__ import annotations
import argparse, copy, hashlib, json, re, subprocess, tempfile
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit
from zoneinfo import ZoneInfo
import fitz

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"research/source_reviews/indonesia_m36_sept_2026_official_pdf_stage_audit_2026-10-17.json"
DAY="2026-10-17"
TEMP=Path(tempfile.gettempdir())/"kep_m36_public_official_20261017"
LIST_STAGES={"2026-09-10":"eps_topik_first_stage_pass_list_not_final",
             "2026-09-17":"optional_job_capacity_competency_evidence_not_final_job_docs"}
def read(name):
    return json.loads((ROOT/name).read_text(encoding="utf-8-sig"))
def need(value,msg):
    if not value:raise ValueError("M36_ORIGINAL_PDF_STAGE_BLOCKED "+msg)
def uri_check(u):
    p=urlsplit(u)
    need(p.scheme=="https" and p.hostname=="kp2mi.go.id"
       and p.path.startswith("/uploads/gtgkorea/images/")
       and p.path.lower().endswith(".pdf") and not p.fragment
       and p.username is None and p.password is None,
       "official PDF URL only")
    return p.path.rsplit("/",1)[-1]
def audit_inputs():
    m21=read("research/source_reviews/indonesia_m21_original_html_audit_2026-10-17.json")
    m23=read("research/source_reviews/indonesia_m23_priority_pdf_body_audit_2026-10-17.json")
    m35=read("research/source_reviews/indonesia_m35_final_job_docs_evidence_template_2026-10-17.json")
    need(m21["observedAtDate"]==DAY and m21["jobDocs"]=="hold" and
         m21["humanOfficialSemanticSignoff"] is False,"M21 original notices")
    notice={x["date"]:x for x in m21["manufacturingNoticeHtml"] if x["date"] in LIST_STAGES}
    need(len(notice)==2 and notice["2026-09-10"]["attachmentCount"]==1
         and notice["2026-09-17"]["attachmentCount"]==6,"exact 2026 sources")
    need(m23["fetchedAndOpenedPdfBodies"]==6 and
         m23["exactFinalManufacturingJobDocs"]=="hold","M23 prior PDF body")
    need(m35["sourceEvidenceStatus"]=="official_2026_final_notice_not_established"
         and m35["source"]["requiredDocuments"]==[]
         and m35["betaAccess"]=="hold","M35 applicant documents remain empty")
    prior={x["originalUrl"]:x for x in m23["pdfRecords"] if x.get("pdfBodyRead")}
    urls=set()
    rows=[]
    for date,src in sorted(notice.items()):
        for url in src["attachmentUrls"]:
            name=uri_check(url)
            stamp=datetime.fromisoformat(date).strftime("%d-%m-%Y")
            need(url not in urls and stamp in name,"unique date-bound official PDF")
            urls.add(url)
            old=prior.get(url)
            records={
               "noticeDate":date,"noticeOriginalUrl":src["url"],
               "noticeTitle":src["title"],"officialPdfUrl":url,
               "noticeAttachmentStage":LIST_STAGES[date],
               "priorM23PdfBodyObserved":bool(old),
               "priorM23Sha256":old.get("sha256") if old else None,
               "download":"not_requested","currentOriginalSha256":None,
               "currentByteSize":None,"currentPages":None,
               "pdfHeaderVerified":False,"visualFirstPageRenderedToLocalTempOnly":False,
               "namesOrIdentifiersCopied":False,"pageTextOrImagesCommitted":False,
               "finalOnlineJobApplicationDocsConfirmed":False,
               "officialHumanSignoff":False}
            rows.append(records)
    need(len(rows)==7 and sum(x["priorM23PdfBodyObserved"] for x in rows)==4,
         "exact one stage-one and six competency PDFs, four already opened")
    return rows
def retrieve(row):
    u=row["officialPdfUrl"]
    name=uri_check(u)
    TEMP.mkdir(parents=True,exist_ok=True)
    dest=TEMP/name
    fetched=False
    if dest.exists():
        try:
            need(dest.stat().st_size<24000000 and dest.read_bytes()[:5]==b"%PDF-",
                 "local cached file invalid")
            fetched=True
            row["download"]="previous_same_day_temp_pdf_validated"
        except Exception:dest.unlink(missing_ok=True)
    if not fetched:
        cmd=["curl.exe","--fail","--location","--connect-timeout","8",
             "--max-time","35","--max-filesize","22000000","--retry","0",
             "--silent","--show-error","--output",str(dest),u]
        try:
            p=subprocess.run(cmd,timeout=42,capture_output=True,text=True)
            if p.returncode!=0:
                row.update(download="inconclusive_timeout_or_network",fetchError="curl_exit_"+str(p.returncode))
                dest.unlink(missing_ok=True)
                return
        except Exception as ex:
            row.update(download="inconclusive_timeout_or_network",fetchError=type(ex).__name__)
            dest.unlink(missing_ok=True)
            return
    try:
        data=dest.read_bytes()
        need(len(data)<22000000 and data.startswith(b"%PDF-"),"PDF original bytes")
        doc=fitz.open(stream=data,filetype="pdf")
        try:
            need(1<=len(doc)<=400,"PDF page count")
            first=doc[0]
            first.get_pixmap(matrix=fitz.Matrix(0.55,0.55),alpha=False).save(
                str(TEMP/(dest.stem[:52]+"_temp_visual_check.png")))
            # For the 2020 first-stage pass-list, NO names or row text
            # are logged, copied into JSON, sent to GitHub, or shared.
            pages=len(doc)
        finally:doc.close()
        sha=hashlib.sha256(data).hexdigest()
        if row["priorM23Sha256"] is not None:
            need(sha==row["priorM23Sha256"],"previously archived PDF SHA changed")
        row.update(download="official_original_pdf_body_read",currentOriginalSha256=sha,
            currentByteSize=len(data),currentPages=pages,pdfHeaderVerified=True,
            visualFirstPageRenderedToLocalTempOnly=True)
    except Exception as ex:
        row.update(download="inconclusive_invalid_pdf",fetchError=type(ex).__name__)
        dest.unlink(missing_ok=True)
def snapshot(run=False):
    entries=audit_inputs()
    # Do not waste PDF re-downloads: only 3 not-yet-observed original bodies.
    chosen=[r for r in entries if not r["priorM23PdfBodyObserved"]]
    need(len(chosen)==3 and sum(r["noticeDate"]=="2026-09-10" for r in chosen)==1,
         "bounded new work: first stage result + two optional evidence PDFs")
    if run:
        for i,r in enumerate(chosen,1):
            retrieve(r)
            print("M36_OFFICIAL_PDF",i,"of",len(chosen),r["noticeDate"],
                  r["download"],r["currentPages"],flush=True)
    return {
       "version":"1.0.0","observedAtJakartaDate":DAY,
       "kind":"readonly_original_pdf_stage_separation_without_personal_list_data",
       "sourceNoticeCount":2,"officialAttachmentCount":7,
       "firstStagePassListAttachments":1,"optionalCompetencyAttachments":6,
       "previouslyVerifiedM23OfThese":4,"newTargets":3,
       "newSuccessfulOriginalPdfBodies":sum(x["download"]=="official_original_pdf_body_read" for x in entries),
       "newInconclusiveOriginalPdfBodies":sum(x["download"].startswith("inconclusive") for x in entries),
       "officialAnnexes":entries,
       "firstStagePassListPersonalDataPersisted":False,
       "stageOne2026NotFinal":True,"optionalSkillsNotFinalJobDocs":True,
       "finalJobDocsOriginalNoticeEstablished":False,
       "sourceSHAApproved":False,"humanOfficialSourceSignoff":False,
       "applicantDocumentPackChanged":False,
       "publicBetaAccess":"hold","releaseAuthorized":False,
       "scopeWarning":"This is a limited PDF original-byte check of seven linked annexes for two already stage-classified official notices. It does not inspect the complete official announcement universe, certify all scanned PDF pages semantically, or infer any final post-Skill-Test 2026 Manufacturing job application requirement."
    }
def validate(q,actual=False):
    need(q["observedAtJakartaDate"]==DAY and
         q["kind"]=="readonly_original_pdf_stage_separation_without_personal_list_data"
         and q["sourceNoticeCount"]==2 and q["officialAttachmentCount"]==7
         and q["firstStagePassListAttachments"]==1 and q["optionalCompetencyAttachments"]==6
         and q["previouslyVerifiedM23OfThese"]==4 and q["newTargets"]==3,
         "two original notice annex boundaries")
    existing=audit_inputs()
    originals={x["officialPdfUrl"]:x for x in existing}
    rows=q["officialAnnexes"]
    need(len(rows)==7 and {r["officialPdfUrl"] for r in rows}==set(originals)
         and len({r["officialPdfUrl"] for r in rows})==7,"seven immutable PDF URL identities")
    for row in rows:
        old=originals[row["officialPdfUrl"]]
        for key in ("noticeDate","noticeTitle","noticeOriginalUrl",
                    "noticeAttachmentStage","priorM23PdfBodyObserved","priorM23Sha256"):
            need(row[key]==old[key],"annex original metadata tampered "+key)
        uri_check(row["officialPdfUrl"])
        if row["download"]=="official_original_pdf_body_read":
            need(not row["priorM23PdfBodyObserved"]
                 and isinstance(row["currentOriginalSha256"],str)
                 and bool(re.fullmatch("[0-9a-f]{64}",row["currentOriginalSha256"]))
                 and type(row["currentByteSize"]) is int and row["currentByteSize"]>100
                 and type(row["currentPages"]) is int and 1<=row["currentPages"]<=400
                 and row["pdfHeaderVerified"] is True
                 and row["visualFirstPageRenderedToLocalTempOnly"] is True,
                 "exact original-body evidence required")
        elif row["priorM23PdfBodyObserved"]:
            need(row["download"]=="not_requested","M23 verified PDF should not be re-downloaded")
        else:
            need(row["download"] in {"not_requested","inconclusive_timeout_or_network",
                                    "inconclusive_invalid_pdf"} and
                 row["currentOriginalSha256"] is None,"failed original PDF cannot claim body verification")
        need(row["finalOnlineJobApplicationDocsConfirmed"] is False
             and row["officialHumanSignoff"] is False
             and row["namesOrIdentifiersCopied"] is False
             and row["pageTextOrImagesCommitted"] is False,"no false final rules or personal data")
    need(q["newSuccessfulOriginalPdfBodies"]==sum(x["download"]=="official_original_pdf_body_read" for x in rows)
         and q["newInconclusiveOriginalPdfBodies"]==sum(x["download"].startswith("inconclusive") for x in rows),
         "exact audit success/failure count")
    need(q["firstStagePassListPersonalDataPersisted"] is False
       and q["stageOne2026NotFinal"] is True
       and q["optionalSkillsNotFinalJobDocs"] is True
       and q["finalJobDocsOriginalNoticeEstablished"] is False
       and q["sourceSHAApproved"] is False
       and q["humanOfficialSourceSignoff"] is False
       and q["applicantDocumentPackChanged"] is False
       and q["publicBetaAccess"]=="hold" and q["releaseAuthorized"] is False,
       "human official release never assumed")
def selftest():
    q=snapshot()
    validate(q)
    mutations=[
      lambda a:a.update(publicBetaAccess="open"),
      lambda a:a.update(releaseAuthorized=True),
      lambda a:a.update(finalJobDocsOriginalNoticeEstablished=True),
      lambda a:a.update(humanOfficialSourceSignoff=True),
      lambda a:a.update(sourceSHAApproved=True),
      lambda a:a.update(firstStagePassListPersonalDataPersisted=True),
      lambda a:a.update(stageOne2026NotFinal=False),
      lambda a:a.update(optionalSkillsNotFinalJobDocs=False),
      lambda a:a.update(newSuccessfulOriginalPdfBodies=2),
      lambda a:a["officialAnnexes"][0].update(officialPdfUrl="https://evil.invalid/a.pdf"),
      lambda a:a["officialAnnexes"][0].update(finalOnlineJobApplicationDocsConfirmed=True),
      lambda a:a["officialAnnexes"][0].update(download="official_original_pdf_body_read"),
      lambda a:a["officialAnnexes"][0].update(noticeAttachmentStage="final_online_docs"),
      lambda a:a["officialAnnexes"][0].update(namesOrIdentifiersCopied=True),
      lambda a:a["officialAnnexes"].pop(),
    ]
    for i,mutation in enumerate(mutations):
        bad=copy.deepcopy(q);mutation(bad)
        try:validate(bad)
        except (KeyError,TypeError,ValueError):pass
        else:raise AssertionError("M36 unsafe altered original PDF state "+str(i))
    print("M36_OFFICIAL_PDF_STAGE_SELF_TEST_PASS 15_fail_closed 7_official_attachments first_stage_no_PII beta_HOLD")
def main():
    p=argparse.ArgumentParser()
    for flag in ("self-test","run","check"):p.add_argument("--"+flag,action="store_true")
    a=p.parse_args()
    if a.self_test:selftest()
    if a.run:
        need(not OUT.exists(),"append-only official PDF record already exists")
        now=datetime.now(timezone.utc).astimezone(ZoneInfo("Asia/Jakarta")).date().isoformat()
        need(now==DAY,"same-day official source reference")
        q=snapshot(run=True)
        validate(q)
        OUT.write_text(json.dumps(q,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
        print("M36_RESULT new_pdf_success",q["newSuccessfulOriginalPdfBodies"],
              "new_pdf_inconclusive",q["newInconclusiveOriginalPdfBodies"],
              "job_docs_HOLD",flush=True)
    if a.check:
        q=read("research/source_reviews/indonesia_m36_sept_2026_official_pdf_stage_audit_2026-10-17.json")
        validate(q)
        print("M36_ORIGINAL_PDF_STAGE_RECORD_INTEGRITY_PASS appended_PDF_bytes_metadata_only")
    if not(a.self_test or a.run or a.check):p.error("choose action")
if __name__=="__main__":main()
