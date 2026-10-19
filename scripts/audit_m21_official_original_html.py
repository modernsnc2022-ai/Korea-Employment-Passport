#!/usr/bin/env python3
"""M21 machine-only official original HTML/appendix LINK inventory (not PDF semantic signoff)."""
from __future__ import annotations
import argparse
import hashlib
import html
import json
import re
import sys
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo

from check_official_sources import _fetch_response, TextExtractor, normalize_source_text

ROOT=Path(__file__).resolve().parents[1]
DAY="2026-10-17"
KP_HOST="kp2mi.go.id"
SHARED=[
  ("minimum_wage", ("10,320", "2026")),
  ("labor_standards_wage_statement", ("제48조", "임금명세서")),
  ("moel_wage_arrears_2026", ("임금체불", "진정")),
  ("kdca_qcode_input", ("검역",)),
  ("moel_1350_contact", ("1350", "09:00", "18:00")),
]
EXPECTED_ATTACHMENTS={
 "2026-09-17":6, "2026-09-10":1,"2026-05-05":2,
 "2026-03-27":7,"2026-02-16":3,"2026-02-10":1,"2026-01-27":4,
}
def load(p):return json.loads(Path(p).read_text(encoding="utf-8-sig"))
def demand(ok,msg):
    if not ok:raise ValueError("M21_OFFICIAL_HTML_SCOPE_BLOCKED "+msg)

class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.hrefs=[]
    def handle_starttag(self,tag,attrs):
        if tag.lower()=="a":
            for k,v in attrs:
                if k.lower()=="href" and v:self.hrefs.append(html.unescape(v))

def make_record(note, official_html, final_url, old_hash):
    clean=TextExtractor()
    clean.feed(official_html)
    text=normalize_source_text(" ".join(clean.parts), final_url)
    links=Links()
    links.feed(official_html)
    attachments=sorted({u for u in links.hrefs
         if urlparse(u).hostname in {KP_HOST,"www."+KP_HOST}
         and urlparse(u).path.lower().endswith(".pdf")
         and "/uploads/gtgkorea/" in urlparse(u).path.lower()})
    # Metadata only; every linked PDF retains pending human semantic review.
    return {
     "date":note["date"],"title":note["title"],"url":note["url"],
     "category":note["reviewCategory"],"textSha256":hashlib.sha256(text.encode()).hexdigest(),
     "normalizedTextLength":len(text),
     "lamaranOnlineOccurrencesRawPageText":len(re.findall(r"lamaran\s+online",text,re.I)),
     "attachmentUrls":attachments,"attachmentCount":len(attachments),
     "previouslyIndexedAttachmentCount":EXPECTED_ATTACHMENTS.get(note["date"]),
     "attachmentLinkCountConsistentWithPriorReview":
       len(attachments)==EXPECTED_ATTACHMENTS.get(note["date"]),
     "historicalHtmlTextSha256":old_hash,
     "semanticReview":"pending_named_human_review",
     "attachmentPdfContentsReviewedToday":False,
     "exactFinalManufacturingJobDocsVerified":False
    }

def self_test():
    note={"date":"2026-09-17","title":"MANUFAKTUR SKILL TEST 2026",
        "url":"https://kp2mi.go.id/gtog-detail/korea/fixture",
        "reviewCategory":"2026_manufacturing_skill_or_optional_competency"}
    test='<html><body>Lamaran online <a href="https://kp2mi.go.id/uploads/gtgkorea/demo.pdf">A</a></body></html>'
    r=make_record(note,test,note["url"],None)
    demand(r["lamaranOnlineOccurrencesRawPageText"]==1,"lamaran count")
    demand(r["attachmentCount"]==1,"one official PDF link")
    demand(not r["attachmentPdfContentsReviewedToday"] and not r["exactFinalManufacturingJobDocsVerified"],"no PDF signoff")
    for url in [
      "https://evil.invalid/uploads/gtgkorea/a.pdf",
      "javascript:alert(1)",
      "https://kp2mi.go.id/not-an-upload/a.pdf",
    ]:
      f=make_record(note,'<a href="'+url+'">A</a>',note["url"],None)
      demand(f["attachmentCount"]==0,"malicious / unrelated PDF link excluded")
    print("M21_OFFICIAL_HTML_METADATA_SELF_TEST_PASS 4_negative_link_cases")
def main():
    cli=argparse.ArgumentParser()
    cli.add_argument("--self-test",action="store_true")
    cli.add_argument("--index",type=Path)
    cli.add_argument("--output",type=Path)
    args=cli.parse_args()
    if args.self_test:
        self_test();return
    demand(args.index is not None and args.output is not None,"explicit index/output required")
    local_day=datetime.now(timezone.utc).astimezone(ZoneInfo("Asia/Jakarta")).date().isoformat()
    demand(local_day==DAY,"this M21 observation is only valid on 2026-10-17 Jakarta date")
    index=load(args.index)
    index_day=datetime.fromisoformat(index["generatedUtc"]).astimezone(ZoneInfo("Asia/Jakarta")).date().isoformat()
    demand(index_day==DAY and index.get("targetYear")==2026
       and index.get("priorYearBoundaryReached") is True
       and index.get("manufacturingRelevantTitleCount")==7
       and index.get("releaseAuthorized") is False
       and index.get("operatorApproved") is False,"same-day official 2026 index required")
    notes=index["manufacturingNoticesForManualReview"]
    demand(len(notes)==7 and {n["date"] for n in notes}==set(EXPECTED_ATTACHMENTS),
           "current official manufacturing set changed: require new scope review")
    prior=load(ROOT/"research/source_reviews/indonesia_daily_readonly_2026-10-17.json")
    demand(prior["checked"]==84 and prior["fetchFailures"]==0
           and prior["humanSemanticReviewApproved"] is False,"previous source evidence invalid")
    ids={row["id"] for row in prior["pendingReviews"] if row["scope"]=="korea_shared"}
    demand(ids=={name for name,_ in SHARED},"five Korea shared source IDs no longer match")
    manifest={x["id"]:x["url"] for x in load(ROOT/"monitor/sources.json")["sources"]}
    previous={x["id"]:x["observedSha256"] for x in prior["pendingReviews"]}
    tls=load(ROOT/"monitor/tls_pins.json")
    korean=[]
    for sid,phrases in SHARED:
        url=manifest[sid]
        raw,kind,charset,final,tls_mode=_fetch_response(url,tls)
        demand(urlparse(url).scheme=="https" and urlparse(final).scheme=="https"
          and (urlparse(final).hostname or "").endswith(".go.kr"),"Korea official HTTPS host required: "+sid)
        extractor=TextExtractor()
        extractor.feed(raw.decode(charset,errors="replace"))
        text=normalize_source_text(" ".join(extractor.parts),final)
        digest=hashlib.sha256(text.encode()).hexdigest()
        rec={"id":sid,"url":url,"finalUrl":final,
            "normalizedTextSha256":digest,"matches20261017SourceMonitorSha":digest==previous[sid],
            "normalizedTextLength":len(text),"safeTlsMode":tls_mode,
            "officialTextAnchorsPresent":{key:key in text for key in phrases},
            "semanticReview":"pending_named_human_review",
            "autoRuleUpdate":False}
        korean.append(rec)
        print("M21_KOREA_SOURCE_OBSERVED",sid,
              "matches_watch_sha="+str(rec["matches20261017SourceMonitorSha"]).lower(),
              "anchors="+str(sum(rec["officialTextAnchorsPresent"].values()))+"/"+str(len(phrases)),flush=True)
    notice_rows=[]
    for note in notes:
        url=note["url"]
        demand(urlparse(url).hostname in {KP_HOST,"www."+KP_HOST}
               and urlparse(url).path.startswith("/gtog-detail/korea/"),"KP2MI official notice domain")
        req=Request(url,headers={"User-Agent":"Mozilla/5.0 (KEP-human-review-support/1.0)",
                                 "Accept":"text/html"})
        with urlopen(req,timeout=23) as response:
            demand(response.status==200 and urlparse(response.url).hostname in {KP_HOST,"www."+KP_HOST},
                   "official detail GET failed "+note["date"])
            raw=response.read(600000)
        content=raw.decode("utf-8",errors="replace")
        row=make_record(note,content,url,None)
        notice_rows.append(row)
        print("M21_KP2MI_NOTICE_OBSERVED",note["date"],
              "pdf_links="+str(row["attachmentCount"]),
              "vs_prior="+str(row["attachmentLinkCountConsistentWithPriorReview"]).lower(),flush=True)
    report={
      "version":"1.0.0","observedAtDate":DAY,"mode":"read_only_12_original_html_pages",
      "koreaSourceCount":len(korean),"kp2miManufacturingDetailCount":len(notice_rows),
      "koreaOfficialText":korean,"manufacturingNoticeHtml":notice_rows,
      "attachmentLinksTotal":sum(n["attachmentCount"] for n in notice_rows),
      "appendixContentReviewedToday":False,"allOriginalPageContentManuallyReviewed":False,
      "sourceHashAutomaticallyAccepted":False,"humanOfficialSemanticSignoff":False,
      "jobDocs":"hold","betaAccess":"hold","authorizesRelease":False,
      "caveat":"HTML original-text anchors and PDF LINK counts only, not policy interpretation, PDF content verification, signed decision, or final online job-document checklist."
    }
    output=args.output.resolve()
    demand(output.parent==(ROOT/"research/source_reviews").resolve()
       and output.name=="indonesia_m21_original_html_audit_2026-10-17.json"
       and not output.exists(),"append-only review output must be new fixed evidence filename")
    output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("M21_ORIGINAL_HTML_REVIEW_SUPPORT_OK korea=5 notices=7 pdf_links="+str(report["attachmentLinksTotal"])+" SIGNOFF_PENDING JOB_DOCS_HOLD BETA_HOLD")
if __name__=="__main__":main()
