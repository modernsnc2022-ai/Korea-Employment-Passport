#!/usr/bin/env python3
"""M29 targeted same-day official evidence: SLBFE volatility and 2026 KP2MI original notice contexts.
Machine extraction ONLY, not government policy signoff, final job-docs verification or beta release.
"""
from __future__ import annotations
import argparse,copy,hashlib,json,re,time
from datetime import datetime,timezone
from pathlib import Path
from urllib.parse import urlparse
from zoneinfo import ZoneInfo
from check_official_sources import _fetch_response,TextExtractor,normalize_source_text
ROOT=Path(__file__).resolve().parents[1]
DAY="2026-10-17"
OUT=ROOT/"research/source_reviews/indonesia_m29_slbfe_and_kp2mi_context_2026-10-17.json"
SOURCE_ID="lk_slbfe_home"
SLBFE="https://www.slbfe.lk/"
KP="kp2mi.go.id"
SCOPE={
 "17 September 2026":"conditional_competency_upload_not_final",
 "10 September 2026":"first_stage_eps_topik_results_not_final",
 "5 May 2026":"exam_fee_refund_not_final",
 "27 March 2026":"eps_topik_exam_schedule_not_final",
 "16 February 2026":"exam_registration_biometrics_not_final",
 "10 February 2026":"initial_exam_enrollment_adjustment_not_final",
 "27 January 2026":"initial_eps_topik_exam_registration_not_final",
}
TERMS=["lamaran online","pengajuan lamaran","dokumen lamaran","berkas lamaran","e-sertifikat"]
def read(p):return json.loads((ROOT/p).read_text(encoding="utf-8-sig"))
def require(b,msg):
    if not b:raise ValueError("M29_CONTEXT_SCOPE_BLOCKED "+msg)
def seed():
    watch=read("research/source_reviews/indonesia_daily_readonly_2026-10-17.json")
    m21=read("research/source_reviews/indonesia_m21_original_html_audit_2026-10-17.json")
    m24=read("research/source_reviews/indonesia_m24_manufacturing_title_scope_2026-10-17.json")
    m28=read("research/source_reviews/indonesia_m28_hrd_foreign_source_recheck_2026-10-17.json")
    sign=read("recruitment/ID_BETA_SOURCE_SIGNOFF_20261017.json")
    return watch,m21,m24,m28,sign
def check_seed(watch,m21,m24,m28,sign):
    require(watch["observedAtDate"]==DAY and watch["checked"]==84
        and watch["unacceptedBaselineDriftCount"]==12
        and watch["fetchFailures"]==0,"source watch")
    require(m21["kp2miManufacturingDetailCount"]==7
        and m21["humanOfficialSemanticSignoff"] is False
        and m21["jobDocs"]=="hold","M21")
    require(m24["observedAtJakartaDate"]==DAY
        and m24["generalManufacturingTitlesCount"]==7
        and m24["generalManufacturingFinalOnlineJobApplicationTitleCount"]==0
        and m24["titleOnlyEvidence"] is True
        and m24["authorizesRelease"] is False,"M24 title only")
    require(m28["observedAtJakartaDate"]==DAY and
        m28["successfulHtmlBodies"]==7
        and m28["differentShaFromEarlierOct17"]==1 and
        m28["sameShaAsEarlierOct17"]==6
        and m28["manualHumanSourceSignoff"] is False,"M28 seven")
    require(sign["status"]=="pending_manual_source_signoff"
        and sign["reviewer"] is None and sign["approvedAt"] is None
        and sign["betaAccess"]=="hold","human release absent")
    slbfe=next(x for x in m28["items"] if x["sourceId"]==SOURCE_ID)
    require(slbfe["officialOriginalRead"] is True and slbfe["requestedOfficialUrl"]==SLBFE
        and slbfe["currentMatchesEarlierOct17Observation"] is False,"Sri Lanka metadata")
    titles=m24["generalManufacturingTitles"]
    require({x["date"] for x in titles}==set(SCOPE)
        and {x["url"] for x in titles}==
            {x["url"] for x in m21["manufacturingNoticeHtml"]},"same seven official 2026 URLs")
    return slbfe, sorted(titles,key=lambda x:x["date"])
def official_get(url,kind,tls):
    host=(urlparse(url).hostname or "").lower()
    require(urlparse(url).scheme=="https","official source HTTPS")
    if kind=="slbfe":require(host in {"www.slbfe.lk","slbfe.lk"},"SLBFE host")
    if kind=="kp2mi":require(host in {"www.kp2mi.go.id","kp2mi.go.id"}
        and urlparse(url).path.startswith("/gtog-detail/korea/"),"KP2MI notice URL")
    raw,ctype,charset,final,mode=_fetch_response(url,tls)
    h=(urlparse(final).hostname or "").lower()
    if kind=="slbfe":require(h in {"www.slbfe.lk","slbfe.lk"},"SLBFE final HTTPS")
    if kind=="kp2mi":require(h in {"www.kp2mi.go.id","kp2mi.go.id"},"KP2MI final HTTPS")
    require(urlparse(final).scheme=="https" and ctype in ("text/html","application/xhtml+xml",""),
            "HTML source")
    dec=TextExtractor();dec.feed(raw.decode(charset,errors="replace"))
    normalized=normalize_source_text(" ".join(dec.parts),final)
    require(len(normalized)>=100,"official HTML too short")
    return normalized,hashlib.sha256(normalized.encode("utf-8")).hexdigest(),final,mode
def snippets(text):
    spans=[]
    for term in TERMS:
        matches=list(re.finditer(re.escape(term),text,re.I))
        for match in matches[:4]:
            spans.append({"term":term,"around":text[max(0,match.start()-105):min(len(text),match.end()+130)]})
    return spans[:16]
def build(tls=None,perform_get=False):
    w,h,n,m,s=seed()
    slbfe,titles=check_seed(w,h,n,m,s)
    m21_map={x["url"]:x for x in h["manufacturingNoticeHtml"]}
    sample=[]
    for idx in range(3):
        row={"attempt":idx+1,"retrieval":"not_requested","sha256":None,
             "matchesM28":None,"matchesInitialM19":None,"humanApproval":False}
        if perform_get:
            try:
                text,sha,final,mode=official_get(SLBFE,"slbfe",tls)
                row.update(retrieval="official_html_read",sha256=sha,
                    matchesM28=sha==slbfe["currentNormalizedHtmlSha256"],
                    matchesInitialM19=sha==slbfe["oct17FirstObservationSha256"],
                    characters=len(text),finalUrl=final,tlsMode=mode,
                    containsKoreaKeyword=bool(re.search(r"korea|EPS-TOPIK",text,re.I)))
            except Exception as exc:
                row.update(retrieval="inconclusive_fetch",
                    errorType=type(exc).__name__,errorShort=str(exc)[:110])
        sample.append(row)
        if perform_get and idx<2:time.sleep(2.1)
    notices=[]
    for title in titles:
        original=m21_map[title["url"]]
        stage=SCOPE[title["date"]]
        item={"date":title["date"],"title":title["title"],"officialUrl":title["url"],
              "scope":stage,"fetch":"not_requested",
              "currentTextSha256":None,"sameAsM21OriginalHtmlSha256":None,
              "lamaranOnlineExactTermCount":None,"snippetContext":[],"humanApproval":False,
              "exactFinalManufacturingJobDocsVerified":False}
        if perform_get:
            try:
                text,sha,final,mode=official_get(title["url"],"kp2mi",tls)
                contexts=snippets(text)
                item.update(fetch="official_html_read",currentTextSha256=sha,
                    sameAsM21OriginalHtmlSha256=sha==original["textSha256"],
                    lamaranOnlineExactTermCount=len(list(re.finditer("lamaran online",text,re.I))),
                    snippetContext=contexts,normalizedCharacters=len(text),
                    tlsMode=mode,effectiveUrl=final)
            except Exception as exc:
                item.update(fetch="inconclusive_fetch",
                    errorType=type(exc).__name__,errorShort=str(exc)[:110])
        notices.append(item)
    return {
      "version":"1.0.0","observedAtJakartaDate":DAY,
      "kind":"read_only_website_volatility_and_scoped_original_notice_excerpts",
      "slbfeRepeatedOfficialReads":sample,
      "slbfeUniqueSuccessfulNormalizedTextHashes":len({x["sha256"] for x in sample if x["sha256"]}),
      "slbfeSameAsM28Count":sum(x["matchesM28"] is True for x in sample),
      "slbfeSameAsM19Count":sum(x["matchesInitialM19"] is True for x in sample),
      "kp2miGeneralManufacturingNotices":notices,
      "kp2miOfficialNoticePagesRead":sum(x["fetch"]=="official_html_read" for x in notices),
      "kp2miCurrentTextShaMatchesM21":sum(x["sameAsM21OriginalHtmlSha256"] is True for x in notices),
      "kp2miCurrentTextShaDifferencesM21":sum(x["sameAsM21OriginalHtmlSha256"] is False for x in notices),
      "koreaHRDAndForeignSourceAlertsStillPending":True,
      "sriLankaSemanticPolicyChangeUnverified":True,
      "onlyThisCohort2026ManufacturingRelevant":True,
      "finalOnlineManufacturingJobDocsOfficialEvidenceEstablished":False,
      "requiredOfficialNextNoticeStillMissingFromProvenEvidence":True,
      "humanSourceSemanticsApproved":False,
      "automaticSourceHashAccept":False,"jobDocs":"hold","publicBetaAccess":"hold",
      "releaseAuthorized":False,
      "caveat":"Same-day official HTML text and keyword contexts are review aids. Page counters, dynamic text, or repeated SHA differences do not establish policy changes. This audit does not inspect every official PDF or certify final Manufacturing online job documents."}
def validate(report):
    require(report["observedAtJakartaDate"]==DAY
        and report["kind"]=="read_only_website_volatility_and_scoped_original_notice_excerpts",
        "record class")
    samples=report["slbfeRepeatedOfficialReads"]
    notices=report["kp2miGeneralManufacturingNotices"]
    require(len(samples)==3 and [x["attempt"] for x in samples]==[1,2,3],
        "SLBFE bounded recheck")
    require(len(notices)==7 and {x["date"] for x in notices}==set(SCOPE),"2026 notice scope")
    for x in samples:
        if x["retrieval"]=="official_html_read":
            require(bool(re.fullmatch("[0-9a-f]{64}",x["sha256"]))
                    and x["characters"]>=100
                    and x["humanApproval"] is False,"SLBFE valid observation")
        else:
            require(x["retrieval"] in {"not_requested","inconclusive_fetch"}
                    and x["sha256"] is None,"unsuccessful SLBFE not marked valid")
    for x in notices:
        require(x["scope"]==SCOPE[x["date"]]
            and x["humanApproval"] is False
            and x["exactFinalManufacturingJobDocsVerified"] is False
            and urlparse(x["officialUrl"]).hostname in {"kp2mi.go.id","www.kp2mi.go.id"},
            "notice scope and approval")
        if x["fetch"]=="official_html_read":
            require(bool(re.fullmatch("[0-9a-f]{64}",x["currentTextSha256"]))
                and isinstance(x["snippetContext"],list)
                and isinstance(x["lamaranOnlineExactTermCount"],int),"original HTML")
        else:
            require(x["fetch"] in {"not_requested","inconclusive_fetch"}
                and x["currentTextSha256"] is None,"inconclusive no SHA")
    require(report["slbfeUniqueSuccessfulNormalizedTextHashes"]==
         len({x["sha256"] for x in samples if x["sha256"]}),"unique observation count")
    require(report["kp2miOfficialNoticePagesRead"]==
         sum(x["fetch"]=="official_html_read" for x in notices),"notice count")
    require(report["kp2miCurrentTextShaMatchesM21"]==
         sum(x["sameAsM21OriginalHtmlSha256"] is True for x in notices),"matches")
    require(report["kp2miCurrentTextShaDifferencesM21"]==
         sum(x["sameAsM21OriginalHtmlSha256"] is False for x in notices),"differences")
    require(report["humanSourceSemanticsApproved"] is False
       and report["automaticSourceHashAccept"] is False
       and report["sriLankaSemanticPolicyChangeUnverified"] is True
       and report["koreaHRDAndForeignSourceAlertsStillPending"] is True
       and report["finalOnlineManufacturingJobDocsOfficialEvidenceEstablished"] is False
       and report["requiredOfficialNextNoticeStillMissingFromProvenEvidence"] is True
       and report["jobDocs"]=="hold" and report["publicBetaAccess"]=="hold"
       and report["releaseAuthorized"] is False,"release status")
def self_test():
    base=build()
    validate(base)
    mutants=[
      lambda x:x.update(releaseAuthorized=True),
      lambda x:x.update(publicBetaAccess="open"),
      lambda x:x.update(jobDocs="verified"),
      lambda x:x.update(humanSourceSemanticsApproved=True),
      lambda x:x.update(automaticSourceHashAccept=True),
      lambda x:x.update(sriLankaSemanticPolicyChangeUnverified=False),
      lambda x:x.update(finalOnlineManufacturingJobDocsOfficialEvidenceEstablished=True),
      lambda x:x["kp2miGeneralManufacturingNotices"][0].update(exactFinalManufacturingJobDocsVerified=True),
      lambda x:x["kp2miGeneralManufacturingNotices"][0].update(scope="final_job_docs"),
      lambda x:x["kp2miGeneralManufacturingNotices"][0].update(fetch="official_html_read"),
      lambda x:x["slbfeRepeatedOfficialReads"][0].update(retrieval="official_html_read"),
      lambda x:x["slbfeRepeatedOfficialReads"].pop(),
    ]
    for i,fn in enumerate(mutants):
        x=copy.deepcopy(base);fn(x)
        try:validate(x)
        except (ValueError,KeyError,TypeError):pass
        else:raise AssertionError("unsafe M29 mutation accepted "+str(i))
    print("M29_TARGETED_OFFICIAL_CONTEXT_SELF_TEST_PASS 12_fail_closed_cases seven_2026_notice_scopes jobdocs_HOLD")
def main():
    p=argparse.ArgumentParser()
    for name in ["self-test","run","check"]:p.add_argument("--"+name,action="store_true")
    a=p.parse_args()
    if a.self_test:self_test()
    if a.run:
        now=datetime.now(timezone.utc).astimezone(ZoneInfo("Asia/Jakarta")).date().isoformat()
        require(now==DAY and not OUT.exists(),"date or append-only data exists")
        q=build(tls=read("monitor/tls_pins.json"),perform_get=True)
        validate(q)
        OUT.write_text(json.dumps(q,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
        for x in q["slbfeRepeatedOfficialReads"]:
            print("M29_SLBFE",x["attempt"],x["retrieval"],"sha",x["sha256"],flush=True)
        for x in q["kp2miGeneralManufacturingNotices"]:
            print("M29_KP2MI",x["date"],x["scope"],
                  "fetch",x["fetch"],"lamaran",x["lamaranOnlineExactTermCount"],
                  "same_original_sha",x["sameAsM21OriginalHtmlSha256"],flush=True)
        print("M29_SUMMARY slbfe_unique",q["slbfeUniqueSuccessfulNormalizedTextHashes"],
              "kp2mi_original_bodies",q["kp2miOfficialNoticePagesRead"],
              "job_docs_HOLD beta_HOLD human_unsigned")
    if a.check:
        q=read("research/source_reviews/indonesia_m29_slbfe_and_kp2mi_context_2026-10-17.json")
        validate(q)
        print("M29_ORIGINAL_CONTEXT_INTEGRITY_PASS")
    if not (a.self_test or a.run or a.check):p.error("choose --self-test, --run or --check")
if __name__=="__main__":main()
