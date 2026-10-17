#!/usr/bin/env python3
"""Read-only M23: official 2026 Indonesia P1 PDF body inspection, no source approval."""
from __future__ import annotations
import argparse, hashlib, json, re, subprocess, tempfile, time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse
from zoneinfo import ZoneInfo
import fitz

ROOT=Path(__file__).resolve().parents[1]
QUEUE=ROOT/"research/source_reviews/indonesia_m22_manual_review_queue_2026-10-17.json"
OUTPUT=ROOT/"research/source_reviews/indonesia_m23_priority_pdf_body_audit_2026-10-17.json"
CACHED=Path(tempfile.gettempdir())/"kep_m23_official_public_pdfs_20261017"
TARGETS={"2026-01-27":3,"2026-09-17":4}
TOKENS=["PENDAFTARAN","EPS-TOPIK","UJIAN","KOMPETENSI","SKILL TEST",
        "SISKOP2MI","LAMARAN ONLINE","MANUFAKTUR","PENGALAMAN KERJA",
        "DOKUMEN","PEMBAYARAN","PILIHAN","OPSIONAL","TIDAK WAJIB"]

def guard(test,msg):
    if not test:raise ValueError("M23_ORIGINAL_PDF_AUDIT_BLOCKED "+msg)

def valid_url(url):
    p=urlparse(url)
    guard(p.scheme=="https" and p.hostname=="kp2mi.go.id"
       and p.path.startswith("/uploads/gtgkorea/")
       and p.path.lower().endswith(".pdf"),"nonofficial PDF URL")
    return p.path.rsplit("/",1)[-1]

def checked_tasks(queue):
    guard(queue["evidenceDate"]=="2026-10-17" and queue["gates"]["officialSignoff"]=="pending"
      and queue["gates"]["publicBetaAccess"]=="hold"
      and queue["gates"]["finalManufacturingJobDocs"]=="hold","manual HOLD")
    tasks=[r for r in queue["pdfTasks"] if r["priority"]=="P1"]
    guard(len(tasks)==7 and
          {x:sum(r["noticeDate"]==x for r in tasks) for x in TARGETS}==TARGETS,
          "priority sources")
    for r in tasks:
        valid_url(r["officialUrl"])
        guard(r["bodyReviewedOnM22"] is False
           and r["qualifiesAsFinalManufacturingJobDocs"] is False,"unsafe approved row")
    guard(len({r["officialUrl"] for r in tasks})==7,"duplicate URL")
    return tasks

def verify_pdf(file_path):
    signature=file_path.read_bytes()[:5]
    guard(signature==b"%PDF-","not actual PDF bytes")
    digest=hashlib.sha256(file_path.read_bytes()).hexdigest()
    doc=fitz.open(file_path)
    try:
        guard(0<len(doc)<=150,"PDF invalid page count")
        rows=[]
        for i in range(len(doc)):
            page=doc.load_page(i)
            body=re.sub(r"\s+"," ",page.get_text("text")).strip()
            markers=[word for word in TOKENS if word.lower() in body.lower()]
            rows.append({"page":i+1,"characters":len(body),"tokens":markers,
                         "textExtractable":len(body)>=35})
        pix=doc[0].get_pixmap(matrix=fitz.Matrix(0.6,0.6),alpha=False)
        CACHED.mkdir(parents=True,exist_ok=True)
        thumbnail=CACHED/(file_path.stem[:52]+"_page1.png")
        pix.save(str(thumbnail))
        return {"sha256":digest,"lengthBytes":file_path.stat().st_size,
                "pages":len(doc),"pageEvidence":rows,
                "firstPageRendered":True,
                "pagesWithExtractableText":sum(r["textExtractable"] for r in rows)}
    finally:doc.close()

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--self-test",action="store_true")
    ap.add_argument("--run",action="store_true")
    args=ap.parse_args()
    if args.self_test:
        for bad in ["https://evil.invalid/a.pdf","http://kp2mi.go.id/uploads/gtgkorea/a.pdf",
                    "https://kp2mi.go.id/other/a.pdf"]:
            try:valid_url(bad)
            except ValueError:pass
            else:raise AssertionError("unsafe PDF origin accepted")
        q=json.loads(QUEUE.read_text(encoding="utf-8"))
        checked_tasks(q)
        guard(q["gates"]["releaseAuthorized"] is False,"release guard")
        print("M23_P1_PDF_AUDIT_SELF_TEST_PASS 3_unsafe_URLs_rejected 7_priority_tasks beta_HOLD")
    if not args.run:return
    Jakarta=datetime.now(timezone.utc).astimezone(ZoneInfo("Asia/Jakarta")).date().isoformat()
    guard(Jakarta=="2026-10-17","observation date mismatch")
    guard(not OUTPUT.exists(),"append-only output already exists")
    tasks=checked_tasks(json.loads(QUEUE.read_text(encoding="utf-8")))
    CACHED.mkdir(parents=True,exist_ok=True)
    records=[]
    for idx,task in enumerate(tasks,1):
        url=task["officialUrl"]
        name=valid_url(url)
        destination=CACHED/name
        result={"date":task["noticeDate"],"priority":task["priority"],
                "applicationStage":task["proceduralScope"],"originalUrl":url,
                "download":"inconclusive","pdfBodyRead":False,"sourcePolicySigned":False,
                "finalJobDocsVerified":False}
        if destination.exists():
            try:
                audit=verify_pdf(destination)
                result.update(audit)
                result["download"]="previously_fetched_local_readonly_validated"
                result["pdfBodyRead"]=True
            except Exception:destination.unlink(missing_ok=True)
        if not result["pdfBodyRead"]:
            call=["curl.exe","--fail","--location","--connect-timeout","9",
                  "--max-time","27","--max-filesize","16000000","--retry","0",
                  "--silent","--show-error","--output",str(destination),url]
            try:
                run=subprocess.run(call,timeout=32,capture_output=True,text=True)
                if run.returncode==0 and destination.exists() and destination.stat().st_size>100:
                    audit=verify_pdf(destination)
                    result.update(audit)
                    result["download"]="official_pdf_body_verified"
                    result["pdfBodyRead"]=True
                else:
                    result["errorType"]="curl_exit_"+str(run.returncode)
                    result["errorDetail"]=run.stderr.strip()[:135]
            except Exception as exc:
                result["errorType"]=type(exc).__name__
                result["errorDetail"]=str(exc)[:130]
        records.append(result)
        print("M23_P1_PDF",idx,"/",len(tasks),task["date"] if "date" in task else task["noticeDate"],
           name[:58],"result="+result["download"],
           "pages="+str(result.get("pages","?")),flush=True)
        if idx<len(tasks):time.sleep(2.4)
    report={"version":"1.0.0","observedAtDate":"2026-10-17",
      "basis":"M22_7_P1_official_pdf_link_metadata_inconclusive",
      "configuredP1":7,"fetchedAndOpenedPdfBodies":sum(x["pdfBodyRead"] for x in records),
      "stillInconclusive":sum(not x["pdfBodyRead"] for x in records),
      "pdfRecords":records,"allSevenContentsSemanticallySigned":False,
      "sourceBaselineAutoAccepted":False,"exactFinalManufacturingJobDocs":"hold",
      "humanReviewer":None,"signedAt":None,"publicBetaAccess":"hold","authorizesRelease":False,
      "caveat":"Page text extraction and PDF structural opening are machine evidence. Original image/layout and application scope still require human review. These files relate to exam registration and optional competency evidence, not the final job application."}
    OUTPUT.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("M23_P1_PDF_BODY_SUMMARY",report["fetchedAndOpenedPdfBodies"],"/7",
         "inconclusive",report["stillInconclusive"],"NO_SOURCE_SIGNOFF_JOBDOCS_HOLD_BETA_HOLD")
if __name__=="__main__":main()
