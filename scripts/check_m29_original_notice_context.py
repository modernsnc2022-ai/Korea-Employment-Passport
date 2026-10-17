#!/usr/bin/env python3
"""M29 independent scope and immutable evidence guard for three SLBFE reads and seven KP2MI notice HTMLs."""
from __future__ import annotations
import argparse,copy,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
EVIDENCE=ROOT/"research/source_reviews/indonesia_m29_slbfe_and_kp2mi_context_2026-10-17.json"
WATCH=ROOT/"research/source_reviews/indonesia_daily_readonly_2026-10-17.json"
M21=ROOT/"research/source_reviews/indonesia_m21_original_html_audit_2026-10-17.json"
M28=ROOT/"research/source_reviews/indonesia_m28_hrd_foreign_source_recheck_2026-10-17.json"
SIGNOFF=ROOT/"recruitment/ID_BETA_SOURCE_SIGNOFF_20261017.json"
DAYS={"17 September 2026","10 September 2026","5 May 2026","27 March 2026",
      "16 February 2026","10 February 2026","27 January 2026"}
def read(f):return json.loads(f.read_text(encoding="utf-8-sig"))
def need(b,s):
    if not b:raise ValueError("M29_RECHECK_EVIDENCE_BLOCKED "+s)
def verify(e,w,h,m28,s):
    need(e["observedAtJakartaDate"]=="2026-10-17" and e["kind"]==
        "read_only_website_volatility_and_scoped_original_notice_excerpts","class/date")
    need(w["checked"]==84 and w["unacceptedBaselineDriftCount"]==12
        and w["fetchFailures"]==0 and len(w["pendingReviews"])==12,"pending sources")
    need(s["reviewer"] is None and s["approvedAt"] is None
        and s["status"]=="pending_manual_source_signoff"
        and s["betaAccess"]=="hold","release signoff")
    refs={row["url"]:row for row in h["manufacturingNoticeHtml"]}
    rows=e["kp2miGeneralManufacturingNotices"]
    need(len(rows)==7 and {row["date"] for row in rows}==DAYS
        and {x["officialUrl"] for x in rows}==set(refs),"seven originals")
    need(e["kp2miOfficialNoticePagesRead"]==7 and
        e["kp2miCurrentTextShaMatchesM21"]==7
        and e["kp2miCurrentTextShaDifferencesM21"]==0,"7/7 normalized original")
    for r in rows:
        need(r["fetch"]=="official_html_read"
          and r["sameAsM21OriginalHtmlSha256"] is True
          and r["currentTextSha256"]==refs[r["officialUrl"]]["textSha256"]
          and r["exactFinalManufacturingJobDocsVerified"] is False
          and r["humanApproval"] is False
          and r["scope"].endswith("_not_final")
          and isinstance(r["lamaranOnlineExactTermCount"],int)
          and bool(re.fullmatch("[0-9a-f]{64}",r["currentTextSha256"])),
          "original HTML scope is NOT final docs")
    jan=next(x for x in rows if x["date"]=="27 January 2026")
    need(jan["lamaranOnlineExactTermCount"]==3
      and all(x["lamaranOnlineExactTermCount"]==0 for x in rows if x is not jan)
      and len([x for x in jan["snippetContext"] if x["term"]=="lamaran online"])==3
      and "MCU I" in jan["snippetContext"][0]["around"],
      "January reference mentions future online application and MCU without exact docs")
    slbfe=next(x for x in m28["items"] if x["sourceId"]=="lk_slbfe_home")
    m19=next(x for x in w["pendingReviews"] if x["id"]=="lk_slbfe_home")
    samples=e["slbfeRepeatedOfficialReads"]
    need(len(samples)==3 and
        [x["attempt"] for x in samples]==[1,2,3]
        and e["slbfeUniqueSuccessfulNormalizedTextHashes"]==1
        and e["slbfeSameAsM28Count"]==0
        and e["slbfeSameAsM19Count"]==0,"three consistent new SHA samples")
    hashes={x["sha256"] for x in samples}
    need(len(hashes)==1 and None not in hashes
      and hashes.isdisjoint({slbfe["currentNormalizedHtmlSha256"],m19["observedSha256"]})
      and all(x["retrieval"]=="official_html_read"
        and x["humanApproval"] is False and x["matchesM28"] is False
        and x["matchesInitialM19"] is False
        for x in samples),"Sri Lanka new stable third SHA must not imply a policy change")
    need(e["sriLankaSemanticPolicyChangeUnverified"] is True
       and e["koreaHRDAndForeignSourceAlertsStillPending"] is True
       and e["onlyThisCohort2026ManufacturingRelevant"] is True
       and e["finalOnlineManufacturingJobDocsOfficialEvidenceEstablished"] is False
       and e["requiredOfficialNextNoticeStillMissingFromProvenEvidence"] is True
       and e["humanSourceSemanticsApproved"] is False
       and e["automaticSourceHashAccept"] is False
       and e["jobDocs"]=="hold" and e["publicBetaAccess"]=="hold"
       and e["releaseAuthorized"] is False,"no policy approval or release")
    return True
def selftest():
    inputs=[read(x) for x in [EVIDENCE,WATCH,M21,M28,SIGNOFF]]
    verify(*inputs)
    negatives=[
      lambda x:x[0].update(releaseAuthorized=True),
      lambda x:x[0].update(publicBetaAccess="open"),
      lambda x:x[0].update(jobDocs="verified"),
      lambda x:x[0].update(humanSourceSemanticsApproved=True),
      lambda x:x[0].update(sriLankaSemanticPolicyChangeUnverified=False),
      lambda x:x[0]["kp2miGeneralManufacturingNotices"][0].update(exactFinalManufacturingJobDocsVerified=True),
      lambda x:x[0]["kp2miGeneralManufacturingNotices"][0].update(lamaranOnlineExactTermCount=9),
      lambda x:x[0]["kp2miGeneralManufacturingNotices"][0].update(currentTextSha256="a"*64),
      lambda x:x[0]["kp2miGeneralManufacturingNotices"][0].update(scope="final_online_application"),
      lambda x:x[0]["slbfeRepeatedOfficialReads"][0].update(sha256="0"*64),
      lambda x:x[0].update(slbfeUniqueSuccessfulNormalizedTextHashes=3),
      lambda x:x[1].update(checked=83),
      lambda x:x[4].update(status="approved"),
    ]
    for n,change in enumerate(negatives):
        x=copy.deepcopy(inputs);change(x)
        try:verify(*x)
        except (ValueError,KeyError,TypeError):pass
        else:raise AssertionError("unsafe mutation "+str(n))
    print("M29_INDEPENDENT_EVIDENCE_SELF_TEST_PASS 13_mutants 7_originals 3_SLBFEs final_job_docs_hold")
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--self-test",action="store_true")
    p.add_argument("--check",action="store_true")
    a=p.parse_args()
    if a.self_test:selftest()
    if a.check:
        verify(*(read(x) for x in [EVIDENCE,WATCH,M21,M28,SIGNOFF]))
        print("M29_SAME_DAY_OFFICIAL_CONTEXT_PASS 7/7_KP2MI_original_SHA 1_January_3_mentions_no_final_docs SLBFE_3_stable_new_sha")
    if not(a.self_test or a.check):p.error("choose action")
if __name__=="__main__":main()
