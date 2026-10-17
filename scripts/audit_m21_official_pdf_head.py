#!/usr/bin/env python3
"""M21 official KP2MI PDF link HEAD integrity only; never reads PDF bodies."""
from __future__ import annotations
import argparse
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo

ROOT=Path(__file__).resolve().parents[1]
SRC=ROOT/"research/source_reviews/indonesia_m21_original_html_audit_2026-10-17.json"
OUT=ROOT/"research/source_reviews/indonesia_m21_pdf_head_metadata_2026-10-17.json"
DAY="2026-10-17"

def check_link(url):
    u=urlparse(url)
    if (u.scheme!="https" or u.hostname not in {"kp2mi.go.id","www.kp2mi.go.id"}
        or not u.path.lower().startswith("/uploads/gtgkorea/")
        or not u.path.lower().endswith(".pdf")):
        raise ValueError("Unsafe/non-official PDF appendix URL")
    return True

def probe(link):
    try:
        check_link(link)
        req=Request(link,method="HEAD",headers={
            "User-Agent":"Mozilla/5.0 (KEP-public-pdf-metadata-check/1.0)"})
        with urlopen(req,timeout=22) as res:
            final=res.url
            check_link(final)
            typ=(res.headers.get("Content-Type") or "").split(";")[0].strip().lower()
            clen=res.headers.get("Content-Length")
            return {"url":link,"statusCode":res.status,"contentType":typ,
                    "contentLengthBytes":int(clen) if clen and clen.isdecimal() else None,
                    "success":res.status==200 and typ=="application/pdf",
                    "error":None}
    except Exception as err:
        return {"url":link,"statusCode":None,"contentType":None,
                "contentLengthBytes":None,"success":False,
                "error":type(err).__name__+":"+str(err)[:100]}

def self_test():
    urls=["https://evil.example/uploads/gtgkorea/a.pdf",
          "http://kp2mi.go.id/uploads/gtgkorea/a.pdf",
          "https://kp2mi.go.id/gtog-detail/korea/x.pdf",
          "https://kp2mi.go.id/uploads/gtgkorea/a.html"]
    for u in urls:
        try:check_link(u)
        except ValueError:pass
        else:raise AssertionError("unsafe PDF link allowed")
    check_link("https://kp2mi.go.id/uploads/gtgkorea/images/a.pdf")
    print("M21_OFFICIAL_PDF_LINK_HEAD_SELF_TEST_PASS 4_unsafe_urls_rejected")

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--self-test",action="store_true")
    args=parser.parse_args()
    if args.self_test:return self_test()
    local=datetime.now(timezone.utc).astimezone(ZoneInfo("Asia/Jakarta")).date().isoformat()
    if local!=DAY or OUT.exists():raise ValueError("Day mismatch or existing append-only evidence")
    index=json.loads(SRC.read_text(encoding="utf-8"))
    if (index.get("observedAtDate")!=DAY or index.get("kp2miManufacturingDetailCount")!=7
        or index.get("attachmentLinksTotal")!=24 or index.get("humanOfficialSemanticSignoff") is not False):
        raise ValueError("Refusing unvalidated official notice PDF metadata")
    links=sorted({u for n in index["manufacturingNoticeHtml"] for u in n["attachmentUrls"]})
    if len(links)!=24:raise ValueError("PDF links not exactly unique 24")
    for u in links:check_link(u)
    output=[]
    with ThreadPoolExecutor(max_workers=3) as pool:
        tasks={pool.submit(probe,u):u for u in links}
        for task in as_completed(tasks):
            row=task.result()
            output.append(row)
            print("M21_PDF_HEAD", "PASS" if row["success"] else "UNVERIFIED",
                  row["url"].rsplit("/",1)[-1][:90],flush=True)
    output.sort(key=lambda x:x["url"])
    report={
       "version":"1.0.0","observedAtDate":DAY,"mode":"read_only_http_head_metadata_no_pdf_body_download",
       "pdfLinkCount":len(output),
       "reachablePdfMetadataCount":sum(x["success"] for x in output),
       "unverifiedMetadataCount":sum(not x["success"] for x in output),
       "headRequestsOnly":True,
       "allPdfContentReviewedToday":False,"humanSourceSignoff":False,
       "finalManufacturingJobDocsVerified":False,
       "jobDocs":"hold","betaAccess":"hold","authorizesRelease":False,
       "rows":output,
       "caveat":"HTTP HEAD 200 application/pdf does not prove PDF readability, completeness, job-application scope, or legal/policy accuracy."
    }
    OUT.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("M21_PDF_LINK_HEAD_SUMMARY",f"reachable={report['reachablePdfMetadataCount']}/24",
          "NO_PDF_CONTENT_REVIEW_NO_SIGNOFF_BETA_HOLD")
if __name__=="__main__":main()
