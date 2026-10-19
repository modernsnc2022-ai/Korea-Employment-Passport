#!/usr/bin/env python3
"""M23 read-only compare: new P1 official PDF bytes versus October 14 original evidence."""
from __future__ import annotations
import argparse, copy, json, re
from pathlib import Path
from urllib.parse import urlparse
ROOT=Path(__file__).resolve().parents[1]
SRC=ROOT/"research/source_reviews/indonesia_m23_priority_pdf_body_audit_2026-10-17.json"
OUT=ROOT/"research/source_reviews/indonesia_m23_pdf_lineage_2026-10-17.json"
OLD=[
 ROOT/"research/ID_MANUFACTURING_2026_OPTIONAL_COMPETENCY_PDF_ANNEX_AUDIT_20261014.md",
 ROOT/"research/ID_MANUFACTURING_2026_JANUARY_EPS_REGISTRATION_4_PDF_ANNEX_20261014.md"
]
SHA=re.compile(chr(96)+r"([0-9a-f]{64})"+chr(96))
URL=re.compile(r"\]\((https://kp2mi\.go\.id/uploads/gtgkorea/[^)]+\.pdf)\)")

def demand(ok,msg):
    if not ok:raise ValueError("M23_PDF_LINEAGE_BLOCKED "+msg)

def past_evidence():
    refs={}
    for path in OLD:
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.startswith("|"):continue
            sha=SHA.search(line);url=URL.search(line)
            if not sha or not url:continue
            cols=[c.strip() for c in line.strip("|").split("|")]
            nums=[int(c) for c in cols if c.isdigit()]
            demand(nums and 1<=nums[0]<=150 and url.group(1) not in refs,
                   "historic source PDF count")
            refs[url.group(1)]={"sha":sha.group(1),"pages":nums[0],"date":"2026-10-14"}
    demand(len(refs)==10,"prior six September + four January PDF originals")
    return refs

def review(doc,refs):
    demand(doc.get("observedAtDate")=="2026-10-17"
       and doc.get("configuredP1")==7
       and doc.get("fetchedAndOpenedPdfBodies")==6
       and doc.get("stillInconclusive")==1
       and doc.get("humanReviewer") is None
       and doc.get("signedAt") is None
       and doc.get("allSevenContentsSemanticallySigned") is False
       and doc.get("sourceBaselineAutoAccepted") is False
       and doc.get("exactFinalManufacturingJobDocs")=="hold"
       and doc.get("publicBetaAccess")=="hold"
       and doc.get("authorizesRelease") is False,"release safety")
    rows=doc["pdfRecords"]
    demand(len(rows)==7 and len({r["originalUrl"] for r in rows})==7,
           "7 distinct originals")
    verified=[];inconclusive=[]
    for rec in rows:
        url=rec["originalUrl"];parsed=urlparse(url)
        demand(parsed.scheme=="https" and parsed.hostname=="kp2mi.go.id"
               and parsed.path.startswith("/uploads/gtgkorea/")
               and parsed.path.lower().endswith(".pdf") and url in refs,
               "source URL not official original")
        demand(rec["sourcePolicySigned"] is False
               and rec["finalJobDocsVerified"] is False,"no policy autoapproval")
        old=refs[url]
        if rec["pdfBodyRead"]:
            demand(rec["download"]=="official_pdf_body_verified"
               and rec["sha256"]==old["sha"] and rec["pages"]==old["pages"]
               and len(rec["pageEvidence"])==old["pages"]
               and rec["lengthBytes"]>100 and rec["firstPageRendered"] is True,"PDF byte hash or page count mismatch")
            demand(all(item["page"]==i+1 for i,item in enumerate(rec["pageEvidence"])),
                   "page indexing")
            verified.append({"officialUrl":url,"stage":rec["applicationStage"],
                "pages":rec["pages"],"sha256":rec["sha256"],
                "matchesOriginalRetrievedOn20261014":True,"signedOff":False})
        else:
            demand(rec["download"]=="inconclusive"
               and rec.get("errorType")=="curl_exit_28"
               and "timed out" in rec.get("errorDetail","")
               and "sha256" not in rec,"timeout incorrectly labeled")
            inconclusive.append({"officialUrl":url,"stage":rec["applicationStage"],
               "currentOriginalVerification":"not_completed_timeout",
               "previous20261014Sha256":old["sha"],
               "previous20261014Pages":old["pages"],"currentSha256":None})
    demand(len(verified)==6 and len(inconclusive)==1,"6 pass 1 timeout")
    return {
      "version":"1.0.0","observationDate":"2026-10-17",
      "priorOriginalVerificationDate":"2026-10-14",
      "newlyFetchedPDFsWithOriginalSha256Match":6,
      "newlyUnverifiedPDFs":1,
      "priorAndCurrentOriginalPageCountsMatched":6,
      "firstPagePreviewImagesProduced":6,
      "wholePDFPageTextExtractionAttempted":True,
      "allPagesVisuallySignedOff":False,
      "verified":verified,"inconclusive":inconclusive,
      "sourcePolicyHumanSignoff":False,"automaticSourceBaselineAcceptance":False,
      "finalGeneralManufacturingJobDocuments":"hold",
      "publicBetaAccess":"hold","authorizesRelease":False,
      "note":"Six read-only PDF bodies exactly match 2026-10-14 bytes; 8MB illustrative scan timed out, NOT missing. This is registration and optional competency stage evidence, never final post-Skill-Test job_doc proof."
    }

def selftest(original,refs):
    review(original,refs)
    cases=[
      lambda x:x.update(authorizesRelease=True),
      lambda x:x.update(publicBetaAccess="open"),
      lambda x:x.update(sourceBaselineAutoAccepted=True),
      lambda x:x.update(fetchedAndOpenedPdfBodies=7),
      lambda x:x["pdfRecords"][1].update(sha256="a"*64),
      lambda x:x["pdfRecords"][1].update(pages=27),
      lambda x:x["pdfRecords"][0].update(pdfBodyRead=True),
      lambda x:x["pdfRecords"][2].update(originalUrl="https://evil.example/fake.pdf"),
      lambda x:x["pdfRecords"][3]["pageEvidence"].pop(),
      lambda x:x["pdfRecords"][4].update(sourcePolicySigned=True),
    ]
    for f in cases:
        d=copy.deepcopy(original);f(d)
        try:review(d,refs)
        except (ValueError,KeyError,TypeError):pass
        else:raise AssertionError("incorrect result autoaccepted")
    print("M23_PDF_LINEAGE_SELF_TEST_PASS 10_mutations 6_verified_sha 1_inconclusive_hold")

def main():
    p=argparse.ArgumentParser();p.add_argument("--self-test",action="store_true")
    p.add_argument("--write",action="store_true");a=p.parse_args()
    past=past_evidence();source=json.loads(SRC.read_text(encoding="utf-8"))
    if a.self_test:selftest(source,past)
    if a.write:
        report=review(source,past)
        demand(not OUT.exists(),"append-only evidence already exists")
        OUT.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
        print("M23_PDF_LINEAGE_WRITTEN 6_SHA_PARITY 1_TIMEOUT JOBDOCS_HOLD")
    if not a.self_test and not a.write:p.error("choose --self-test or --write")
if __name__=="__main__":main()
