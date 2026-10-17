#!/usr/bin/env python3
"""M28: re-fetch seven non-Indonesia official source alerts with strict provenance.

Read-only machine evidence, never approval of country policy, source SHA or beta.
"""
from __future__ import annotations
import argparse, copy, hashlib, json, re
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse
from zoneinfo import ZoneInfo
from check_official_sources import _fetch_response, TextExtractor, normalize_source_text

ROOT=Path(__file__).resolve().parents[1]
DAY="2026-10-17"
OUTPUT=ROOT/"research/source_reviews/indonesia_m28_hrd_foreign_source_recheck_2026-10-17.json"
ROUTE="Indonesia > Korea > E-9 > General Manufacturing 2026"
GROUPS={"multi_country_eps_schedule":2,"other_country":5}
HOSTS={
 "mm_hrdk_schedule_index":"epstopik.hrdkorea.or.kr",
 "mm_hrdk_skills_candidates":"epstopik.hrdkorea.or.kr",
 "kg_migrant_home":"migrant.kg",
 "lk_slbfe_home":"slbfe.lk",
 "mm_mol_dol_index":"mol.gov.mm",
 "np_eps_notice_index":"epsnepal.gov.np",
 "vn_colab_eps_notices":"colab.moha.gov.vn",
}
def read(path):
    return json.loads((ROOT/path).read_text(encoding="utf-8-sig"))
def need(value,why):
    if not value: raise ValueError("M28_CROSS_COUNTRY_BOUNDARY_BLOCKED "+why)
def base_inputs():
    watch=read("research/source_reviews/indonesia_daily_readonly_2026-10-17.json")
    m26=read("research/source_reviews/indonesia_m26_unsigned_review_handoff_2026-10-17.json")
    pending=read("recruitment/ID_BETA_SOURCE_SIGNOFF_20261017.json")
    manifest=read("monitor/sources.json")
    return watch,m26,pending,manifest
def safe_url(url,id_,allow_final=False):
    host=(urlparse(url).hostname or "").lower().removeprefix("www.")
    expected=HOSTS[id_]
    need(urlparse(url).scheme=="https" and host==expected,
         "source URL must stay on exact known government/HRD host for "+id_)
    need(not urlparse(url).username and not urlparse(url).password,
         "unexpected credential in source URL")
    return host
def validate_base(watch,m26,pending,manifest):
    need(watch["observedAtDate"]==DAY
         and watch["mode"]=="read_only_official_observation_not_human_signoff"
         and (watch["configured"],watch["checked"],watch["fetchFailures"],
             watch["unacceptedBaselineDriftCount"])==(84,84,0,12),
         "base watch 84/84 and 12 SHA pending")
    need(watch["groupCounts"]["korea_shared"]==5
         and all(watch["groupCounts"][name]==count for name,count in GROUPS.items())
         and watch["groupCounts"]["unclassified_requires_manual_scope_review"]==0,
         "source classifications")
    need(m26["sourceEvidenceAsOf"]==DAY if "sourceEvidenceAsOf" in m26 else m26["asOf"]==DAY,
         "M26 scope observation date")
    need(m26["releaseAuthorized"] is False and m26["betaAccess"]=="hold"
         and m26["humanPolicyReviewApproved"] is False
         and m26["finalManufacturingJobDocs"]=="hold",
         "M26 not a human release signoff")
    need(pending["status"]=="pending_manual_source_signoff"
         and pending["reviewer"] is None and pending["approvedAt"] is None
         and pending["betaAccess"]=="hold","unsigned responsible reviewer")
    records={x["id"]:x for x in watch["pendingReviews"]}
    official={x["id"]:x["url"] for x in manifest["sources"]}
    need(len(official)==84 and len(records)==12 and
         {id_ for id_ in records if records[id_]["scope"]!="korea_shared"}==set(HOSTS),
         "exact seven monitored IDs")
    for id_ in HOSTS:
        row=records[id_]
        need(row["scope"] in GROUPS
           and row["url"]==official[id_]
           and row["semanticReview"]=="pending"
           and row["observedSha256"]!=row["acceptedBaselineSha256"]
           and bool(re.fullmatch(r"[0-9a-f]{64}",row["observedSha256"])),
           "pending manifest-to-watch provenance "+id_)
        safe_url(row["url"],id_)
    return records
def make_record(row,tls=None,perform_get=False):
    id_=row["id"]
    safe_url(row["url"],id_)
    rec={"sourceId":id_,"sourceScope":row["scope"],"requestedOfficialUrl":row["url"],
         "acceptedBaselineSha256":row["acceptedBaselineSha256"],
         "oct17FirstObservationSha256":row["observedSha256"],
         "retrieval":"not_requested","caTlsMode":None,"effectiveOfficialUrl":None,
         "currentNormalizedHtmlSha256":None,"currentMatchesEarlierOct17Observation":None,
         "normalizedCharacters":None,"officialOriginalRead":False,
         "appliesToIndonesiaManufacturingRules":False,
         "manualSemanticsReview":"pending","humanReviewer":None,"sourceBaselineAccepted":False,
         "canAuthorizeRelease":False}
    if not perform_get:return rec
    try:
        raw,kind,charset,final,tls_mode=_fetch_response(row["url"],tls)
        safe_url(final,id_,True)
        need(kind in ("text/html","application/xhtml+xml","text/plain",""),
             "unexpected response type "+id_)
        extractor=TextExtractor()
        extractor.feed(raw.decode(charset,errors="replace"))
        text=normalize_source_text(" ".join(extractor.parts),final)
        need(len(text)>40,"too little official page text "+id_)
        sha=hashlib.sha256(text.encode("utf-8")).hexdigest()
        rec.update(retrieval="success_html_observed",caTlsMode=tls_mode,
            effectiveOfficialUrl=final,
            currentNormalizedHtmlSha256=sha,
            currentMatchesEarlierOct17Observation=sha==row["observedSha256"],
            normalizedCharacters=len(text),officialOriginalRead=True)
    except Exception as exc:
        rec.update(retrieval="inconclusive_network_or_source_format",
                   readErrorType=type(exc).__name__,
                   readErrorSummary=str(exc)[:150])
    return rec
def build(watch,m26,pending,manifest,tls=None,perform_get=False):
    records=validate_base(watch,m26,pending,manifest)
    out=[make_record(records[id_],tls,perform_get) for id_ in sorted(HOSTS)]
    return {
      "version":"1.0.0","observedAtJakartaDate":DAY,
      "type":"readonly_original_html_observation_not_policy_signoff",
      "sourceIds":[x["sourceId"] for x in out],"originalSourceCount":7,
      "multiCountryHRDSources":2,"otherCountrySources":5,
      "successfulHtmlBodies":sum(x["officialOriginalRead"] for x in out),
      "sameShaAsEarlierOct17":sum(x["currentMatchesEarlierOct17Observation"] is True for x in out),
      "differentShaFromEarlierOct17":sum(x["currentMatchesEarlierOct17Observation"] is False for x in out),
      "inconclusiveBodies":sum(not x["officialOriginalRead"] for x in out),
      "items":out,
      "otherCountryPolicyImportedIntoIndonesia":False,
      "multiCountryScheduleDeclaredMyanmarOnly":False,
      "allSourceAlertsRemainPending":True,
      "sourceShaAutoPromoted":False,"manualHumanSourceSignoff":False,
      "officialJobDocumentsManufacturing2026":"hold","publicBetaAccess":"hold",
      "releaseAuthorized":False,
      "explanation":"A same-day HTML digest may change from website counters/updates and cannot by itself prove a legal or policy change. This is not an approval or a live beta release."}
def validate_packet(p,original):
    need(p["observedAtJakartaDate"]==DAY and
         p["originalSourceCount"]==7 and p["multiCountryHRDSources"]==2
         and p["otherCountrySources"]==5,
         "seven sources and group scope")
    rows=p["items"]
    need(len(rows)==7 and {x["sourceId"] for x in rows}==set(HOSTS),
         "unique source IDs")
    need(p["successfulHtmlBodies"]==sum(x["officialOriginalRead"] for x in rows)
       and p["sameShaAsEarlierOct17"]==sum(x["currentMatchesEarlierOct17Observation"] is True for x in rows)
       and p["differentShaFromEarlierOct17"]==sum(x["currentMatchesEarlierOct17Observation"] is False for x in rows)
       and p["inconclusiveBodies"]==sum(not x["officialOriginalRead"] for x in rows),
       "accurate read-only outcome count")
    lookup={x["id"]:x for x in original["pendingReviews"]}
    for r in rows:
        ref=lookup[r["sourceId"]]
        need(r["requestedOfficialUrl"]==ref["url"]
           and r["acceptedBaselineSha256"]==ref["acceptedBaselineSha256"]
           and r["oct17FirstObservationSha256"]==ref["observedSha256"]
           and r["sourceScope"]==ref["scope"],
           "source provenance not modified")
        safe_url(r["requestedOfficialUrl"],r["sourceId"])
        if r["officialOriginalRead"]:
            need(r["retrieval"]=="success_html_observed"
              and r["currentNormalizedHtmlSha256"] is not None
              and bool(re.fullmatch(r"[0-9a-f]{64}",r["currentNormalizedHtmlSha256"]))
              and r["currentMatchesEarlierOct17Observation"] ==
                (r["currentNormalizedHtmlSha256"]==ref["observedSha256"]),
                "current digest verified")
            safe_url(r["effectiveOfficialUrl"],r["sourceId"],True)
        else:
            need(r["retrieval"]=="inconclusive_network_or_source_format"
                 and r["currentNormalizedHtmlSha256"] is None
                 and r["currentMatchesEarlierOct17Observation"] is None,
                 "do not call inaccessible source broken or verified")
        need(r["manualSemanticsReview"]=="pending"
           and r["humanReviewer"] is None
           and r["sourceBaselineAccepted"] is False
           and r["canAuthorizeRelease"] is False
           and r["appliesToIndonesiaManufacturingRules"] is False,
           "source cannot auto approve or import")
    need(p["otherCountryPolicyImportedIntoIndonesia"] is False
       and p["multiCountryScheduleDeclaredMyanmarOnly"] is False
       and p["allSourceAlertsRemainPending"] is True
       and p["sourceShaAutoPromoted"] is False
       and p["manualHumanSourceSignoff"] is False
       and p["officialJobDocumentsManufacturing2026"]=="hold"
       and p["publicBetaAccess"]=="hold" and p["releaseAuthorized"] is False,
       "country/policy/release HOLD")
    return True
def self_test():
    w,m,s,manifest=base_inputs()
    draft=build(w,m,s,manifest)
    need(len(draft["items"])==7,"base read-only records")
    mutants=[
      lambda x:x.update(publicBetaAccess="open"),
      lambda x:x.update(releaseAuthorized=True),
      lambda x:x.update(manualHumanSourceSignoff=True),
      lambda x:x.update(sourceShaAutoPromoted=True),
      lambda x:x.update(otherCountryPolicyImportedIntoIndonesia=True),
      lambda x:x.update(multiCountryScheduleDeclaredMyanmarOnly=True),
      lambda x:x.update(officialJobDocumentsManufacturing2026="verified"),
      lambda x:x["items"][0].update(sourceScope="korea_shared"),
      lambda x:x["items"][0].update(acceptedBaselineSha256="0"*64),
      lambda x:x["items"][0].update(canAuthorizeRelease=True),
      lambda x:x["items"][0].update(manualSemanticsReview="approved"),
      lambda x:x["items"][0].update(requestedOfficialUrl="https://evil.invalid/a"),
      lambda x:x["items"][1].update(retrieval="success_html_observed"),
    ]
    for fn in mutants:
        packet=copy.deepcopy(draft)
        fn(packet)
        try:validate_packet(packet,w)
        except (ValueError,KeyError,TypeError):pass
        else:raise AssertionError("unsafe M28 packet mutation accepted")
    for fake in ["http://epstopik.hrdkorea.or.kr/a","https://fake.example/x",
                 "https://epstopik.hrdkorea.or.kr.evil.example/a"]:
        try:safe_url(fake,"mm_hrdk_schedule_index")
        except ValueError:pass
        else:raise AssertionError("untrusted redirect URL permitted")
    print("M28_HRD_FOREIGN_SOURCE_SELF_TEST_PASS 16_adversarial_cases seven_unsigned_sources 5_other_country_hold")
def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--self-test",action="store_true")
    parser.add_argument("--run",action="store_true")
    parser.add_argument("--check",action="store_true")
    args=parser.parse_args()
    if args.self_test:self_test()
    if args.run:
        now=datetime.now(timezone.utc).astimezone(ZoneInfo("Asia/Jakarta")).date().isoformat()
        need(now==DAY and not OUTPUT.exists(),"current-day append-only snapshot")
        w,m,s,manifest=base_inputs()
        report=build(w,m,s,manifest,tls=read("monitor/tls_pins.json"),perform_get=True)
        validate_packet(report,w)
        OUTPUT.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
        for r in report["items"]:
            print("M28_SOURCE",r["sourceId"],"retrieval="+r["retrieval"],
                  "same_prior_SHA="+str(r["currentMatchesEarlierOct17Observation"]),flush=True)
        print("M28_CROSS_COUNTRY_SNAPSHOT",
              "read="+str(report["successfulHtmlBodies"])+"/7",
              "same="+str(report["sameShaAsEarlierOct17"]),
              "different="+str(report["differentShaFromEarlierOct17"]),
              "inconclusive="+str(report["inconclusiveBodies"]),
              "HUMAN_PENDING_NO_POLICY_IMPORT_BETA_HOLD")
    if args.check:
        w,_,_,_=base_inputs()
        report=read("research/source_reviews/indonesia_m28_hrd_foreign_source_recheck_2026-10-17.json")
        validate_packet(report,w)
        print("M28_SNAPSHOT_INTEGRITY_PASS READ_ONLY_SOURCE_7 CROSS_COUNTRY_SAFE")
    if not (args.self_test or args.run or args.check):parser.error("choose action")
if __name__=="__main__":main()
