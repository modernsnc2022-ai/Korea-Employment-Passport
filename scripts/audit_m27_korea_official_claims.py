#!/usr/bin/env python3
"""M27: inspect exact public Korea-common official HTML vs applicant answer bindings.

A second independent machine observation is NOT legal/policy content signoff.
Never change accepted hashes or beta access.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from datetime import datetime,timezone
from pathlib import Path
from urllib.parse import urlparse
from zoneinfo import ZoneInfo
from check_official_sources import _fetch_response,TextExtractor,normalize_source_text
ROOT=Path(__file__).resolve().parents[1]
DAY="2026-10-17"
OUT=ROOT/"research/source_reviews/indonesia_m27_korea_common_claim_audit_2026-10-17.json"
CLAIMS={
 "minimum_wage":["minimum_wage_2026"],
 "labor_standards_wage_statement":["payslip_required_items","pay_compare_slc_to_statement_components"],
 "moel_wage_arrears_2026":["labor_unpaid_wage_first_action_current"],
 "kdca_qcode_input":["departure_qcode_current_official"],
 "moel_1350_contact":["labor_1350_scope_current"],
}
def read(file):
    return json.loads((ROOT/file).read_text(encoding="utf-8-sig"))
def need(x,message):
    if not x:raise ValueError("M27_KOREA_CLAIM_AUDIT_BLOCKED "+message)
def inputs():
    history=read("research/source_reviews/indonesia_daily_readonly_2026-10-17.json")
    h=read("research/source_reviews/indonesia_m21_original_html_audit_2026-10-17.json")
    sign=read("recruitment/ID_BETA_SOURCE_SIGNOFF_20261017.json")
    manifest=read("monitor/sources.json")
    rules=read("docs/data/exact_answer_rules_v1.json")
    helpdata=read("docs/data/official_help_channels_v1.json")
    return history,h,sign,manifest,rules,helpdata
def inspect_bindings():
    history,h,sign,manifest,rules,helpdata=inputs()
    need(history["observedAtDate"]==DAY and history["checked"]==84
         and history["unacceptedBaselineDriftCount"]==12
         and all(x["semanticReview"]=="pending" for x in history["pendingReviews"]),
         "official watch remains unsigned")
    need(sign["status"]=="pending_manual_source_signoff"
         and sign["reviewer"] is None and sign["betaAccess"]=="hold",
         "human signoff")
    expected={x["id"]:x for x in history["pendingReviews"] if x["scope"]=="korea_shared"}
    earlier={x["id"]:x for x in h["koreaOfficialText"]}
    urls={x["id"]:x["url"] for x in manifest["sources"]}
    answers={x["id"]:x for x in rules["answers"]}
    need(set(expected)==set(earlier)==set(CLAIMS) and len(urls)==84,"five ids and 84 official sources")
    for sid,claim_ids in CLAIMS.items():
        need(urls[sid]==expected[sid]["url"],"source URL changed "+sid)
        need(earlier[sid]["normalizedTextSha256"]==expected[sid]["observedSha256"],
             "historical same-day original SHA mismatch "+sid)
        need(earlier[sid]["matches20261017SourceMonitorSha"] is True
             and earlier[sid]["semanticReview"]=="pending_named_human_review",
             "machine evidence not signoff "+sid)
        for cid in claim_ids:need(cid in answers and answers[cid]["sourceUrl"].startswith("https://"),
                                  "missing applicant claim "+cid)
    need(answers["minimum_wage_2026"]["sourceUrl"]==urls["minimum_wage"],
         "wage canonical official binding")
    need(answers["departure_qcode_current_official"]["sourceUrl"]==
         earlier["kdca_qcode_input"]["finalUrl"],"KDCA official redirect")
    need("10.320" in answers["minimum_wage_2026"]["answer"]
         and "2.156.880" in answers["minimum_wage_2026"]["answer"]
         and "209 jam" in answers["minimum_wage_2026"]["writeExactly"],"wage 209h basis")
    need("tidak boleh dinyatakan wajib bagi setiap" in answers["departure_qcode_current_official"]["answer"],
         "no universal Q-CODE obligation")
    help1350=next(x for x in helpdata["channels"] if x["id"]=="moel_1350")
    need(help1350["sourceUrl"]==urls["moel_1350_contact"]
       and "berbayar" in help1350["hours"]
       and "09:00" in help1350["hours"] and "18:00" in help1350["hours"],
       "paid phone 1350 and working hours")
    return history,earlier,urls,answers
def selftest():
    history,old,urls,answers=inspect_bindings()
    checks={
      "2026_wage_formula":answers["minimum_wage_2026"]["answer"].count("10.320")==1,
      "labor_payslip_statutory_reference":answers["payslip_required_items"]["sourceUrl"]==urls["labor_standards_wage_statement"],
      "arrears_claim_original":answers["labor_unpaid_wage_first_action_current"]["sourceUrl"]==urls["moel_wage_arrears_2026"],
      "qcode_redirect_alias":answers["departure_qcode_current_official"]["sourceUrl"]==old["kdca_qcode_input"]["finalUrl"],
      "1350_verified_url":answers["labor_1350_scope_current"]["sourceUrl"]==urls["moel_1350_contact"],
    }
    need(all(checks.values()),"claim-to-official URL")
    for url in list(urls.values()):
        need(urlparse(url).scheme=="https","official source HTTPS")
    print("M27_KOREA_CLAIM_BINDINGS_SELF_TEST_PASS 5_claim_groups source_review_pending job_docs_HOLD beta_HOLD")
def audit():
    day=datetime.now(timezone.utc).astimezone(ZoneInfo("Asia/Jakarta")).date().isoformat()
    need(day==DAY and not OUT.exists(),"append-only current Jakarta day")
    history,earlier,urls,answers=inspect_bindings()
    tls=read("monitor/tls_pins.json")
    records=[]
    for sid in CLAIMS:
        origin=urls[sid]
        need(urlparse(origin).scheme=="https","source URL scheme")
        row={"id":sid,"officialSource":origin,
             "priorOct17OriginalSha256":earlier[sid]["normalizedTextSha256"],
             "claimIds":CLAIMS[sid],"humanSemanticsReview":"pending",
             "sourceHashAccepted":False,"bodyRead":False,
             "newOriginalTextSha256":None,"sameAsEarlierOct17":None,
             "appClaimMatchesURLScope":True}
        try:
            raw,kind,charset,final,tlsmode=_fetch_response(origin,tls)
            need(urlparse(final).scheme=="https" and
                 (urlparse(final).hostname or "").endswith(".go.kr"),
                 "redirect to non-government host "+sid)
            html=raw.decode(charset,errors="replace")
            extractor=TextExtractor();extractor.feed(html)
            normalized=normalize_source_text(" ".join(extractor.parts),final)
            sha=hashlib.sha256(normalized.encode()).hexdigest()
            row.update(bodyRead=True,finalUrl=final,kind=kind,
                tlsVerification=tlsmode,
                newOriginalTextSha256=sha,
                sameAsEarlierOct17=sha==earlier[sid]["normalizedTextSha256"],
                textLength=len(normalized))
        except Exception as exc:
            row["readError"]=type(exc).__name__+": "+str(exc)[:120]
        records.append(row)
        print("M27_KOREA_OFFICIAL_HTML",sid,
              "body="+str(row["bodyRead"]).lower(),
              "same_prior_sha="+str(row["sameAsEarlierOct17"]).lower(),flush=True)
    result={"version":"1.0.0","observedAtDate":DAY,
        "readOnlyOfficialHTMLRecheck":True,
        "sources":[*records],"successfulBodyFetches":sum(r["bodyRead"] for r in records),
        "sameDayShaMatchesM21":sum(r["sameAsEarlierOct17"] is True for r in records),
        "humanSemanticSignoff":False,
        "actualPolicyChangeVerified":False,
        "officialHashAutoAccepted":False,
        "jobDocs":"hold","betaAccess":"hold","releaseAuthorized":False,
        "limitations":"Machine normalized text SHA comparison + applicant source binding only. A matching HTML fingerprint is not the named human legal/health/labor semantic signoff."}
    OUT.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("M27_KOREA_HTML_RECHECK_RESULT",result["successfulBodyFetches"],
         "/5 sha_same="+str(result["sameDayShaMatchesM21"]),
         "HUMAN_APPROVAL_PENDING BETA_HOLD")
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--self-test",action="store_true")
    p.add_argument("--run",action="store_true")
    args=p.parse_args()
    if args.self_test:selftest()
    if args.run:audit()
    if not (args.self_test or args.run):p.error("choose --self-test/--run")
if __name__=="__main__":main()
