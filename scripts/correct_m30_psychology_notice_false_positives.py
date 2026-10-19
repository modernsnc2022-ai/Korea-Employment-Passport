#!/usr/bin/env python3
"""M30 correction R1: re-screen original 11 title candidates, keep original read-only.

NO 320-row re-fetch is claimed. Correction narrows a known psychology false-positive
without approving source digests, applicant job documents or beta access.
"""
from __future__ import annotations
import argparse, copy, hashlib, html, json
from pathlib import Path
from audit_m30_manufacturing_post_skill_notice_sentinel import tagged,validate as validate_original
ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/"research/source_reviews/indonesia_m30_post_skill_notice_candidates_2026-10-17.json"
M24=ROOT/"research/source_reviews/indonesia_m24_manufacturing_title_scope_2026-10-17.json"
SIGN=ROOT/"recruitment/ID_BETA_SOURCE_SIGNOFF_20261017.json"
OUT=ROOT/"research/source_reviews/indonesia_m30_post_skill_notice_candidates_corrected_r1_2026-10-17.json"
FALSE_DATES={"15 July 2026","4 September 2026"}

def need(condition,message):
    if not condition:raise ValueError("M30_R1_FAIL_CLOSED "+message)
def read(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))
def rerun(old_row):
    # Use only exact observed original title, date, official URL and source ID.
    url=old_row["url"]
    need(url.startswith("https://kp2mi.go.id/gtog-detail/korea/"),
         "url was not a KP2MI original notice")
    row={"id":old_row["noticeId"],"tanggal":old_row["date"],
         "judul":'<a href="'+html.escape(url,quote=True)+'">'+html.escape(old_row["title"])+"</a>"}
    new=tagged(row)
    if new is not None:
        for key in ["noticeId","date","title","url"]:
            need(new[key]==old_row[key],"original candidate identity changed "+key)
    return new
def build(old,prior,sign):
    # The original 11-candidate packet was valid under its ORIGINAL classifier.
    # Its old validation routine now imports the narrower detector, so it must
    # not retroactively reject the two known psychology false positives.
    need(old["humanPolicySemanticsApproved"] is False
       and old["currentCycleFinalDocsVerified"] is False
       and old["sourceHashAutoAccepted"] is False
       and old["allowApplicantFinalJobApplicationSubmit"] is False
       and old["exactManufacturingFinalJobDocuments"]=="hold"
       and old["betaAccess"]=="hold" and old["releaseAuthorized"] is False
       and all(x["humanReviewer"] is None and x["semanticReview"]=="pending"
          and x["verifiedExactFinalJobDocuments"] is False
          and x["authorizesAppRuleUpdate"] is False
          for x in old["titleCandidates"]),
       "original candidate observation was never a policy or release approval")
    need(old["observationDateJakarta"]=="2026-10-17"
       and old["officialIndexRowsChecked"]==320
       and old["officialHistoricalNoticeCount"]>=320
       and old["titleUrlSha256"]==prior["titleUrlDigestSha256"]
       and old["previousM24TitleUrlSha256"]==prior["titleUrlDigestSha256"]
       and old["titleIndexChangedFromM24"] is False
       and old["targetRelatedTitles"]==1
       and old["targetExplicitFinalApplicationTitles"]==0
       and old["genericAmbiguousTitles"]==2
       and old["mixedSectorTitles"]==0
       and old["otherCohortTitlesExcluded"]==8
       and len(old["titleCandidates"])==11,
       "must start with exact original 11 candidate same source SHA")
    need(sign["status"]=="pending_manual_source_signoff"
       and sign["reviewer"] is None
       and sign["approvedAt"] is None
       and sign["betaAccess"]=="hold",
       "unsigned official source approval")
    kept=[];dropped=[]
    for row in old["titleCandidates"]:
        updated=rerun(row)
        if updated is None:
            need(row["date"] in FALSE_DATES
               and "PSIKOLOGI" in row["title"].upper()
               and "KELULUSAN" in row["title"].upper()
               and row["screeningStage"]=="generic_final_application_or_certificate_manual_scope_review",
               "unexpected dropped candidate might be real final notice")
            dropped.append({"noticeId":row["noticeId"],"date":row["date"],
               "title":row["title"],"officialUrl":row["url"],
               "oldClassifierStage":row["screeningStage"],
               "newClassifierStage":None,
               "reason":"psychology_referral_or_second_opinion_not_final_skill_test_or_job_application"})
        else:
            # A purportedly improved detector cannot silently reclassify
            # any other original notice; requires explicit new audit.
            need(updated==row,"unexpected reclassification in retained candidate")
            kept.append(updated)
    need(len(dropped)==2 and {x["date"] for x in dropped}==FALSE_DATES
       and len(kept)==9 and len({x["noticeId"] for x in kept})==9,
       "must be exactly two psychology false positives")
    need(sum(x["screeningStage"].startswith("manufacturing_") for x in kept)==1
       and sum(x["screeningStage"]=="other_cohort_excluded" for x in kept)==8,
       "future notices remain correctly separated")
    payload={
      "version":"1.0.0","revision":"M30_R1_psychology_false_positive_correction",
      "originalObservationDateJakarta":old["observationDateJakarta"],
      "originSource":"M30 original preserved without rewriting",
      "originSourceUrl":old["source"],"originalRowsInspected":320,
      "rawFull320RowFeedRequeriedForCorrection":False,
      "correctionBasis":"Re-screen original M30 saved 11 candidate metadata; exact original 320 row title+URL digest unchanged",
      "originalTitleUrlSha256":old["titleUrlSha256"],
      "sameAsM24TitleUrlSha256":True,
      "originalCandidateCount":11,"correctedCandidateCount":9,
      "removedPsychologyFalsePositives":2,
      "removedCandidates":dropped,"remainingCandidates":kept,
      "manufacturingRelatedTitleCandidates":1,
      "manufacturingExplicitFinalOnlineApplicationTitles":0,
      "otherSectorCandidatesExcluded":8,
      "genericAmbiguousFinalCandidates":0,
      "mixedSectorCandidates":0,
      "humanReviewer":None,"humanSignedAt":None,
      "semanticApproval":False,"automaticSourceBaselineAcceptance":False,
      "confirmedPostSkillTestManufacturingFinalDocumentChecklist":False,
      "allowFinalApplicationSubmission":False,
      "jobDocs":"hold","publicBetaAccess":"hold",
      "productionDeploymentAuthorized":False,"releaseAuthorized":False,
      "limitations":"This is a corrective rescreen of the 11 original candidate titles, not a new fetch or all-PDF/body search. Previously excluded non-candidates from the 320-row index are not reclassified. New official notices demand a separate live index observation, original-body/annex review and named human source signoff.",
    }
    return payload

def check(payload,old,prior,sign):
    expected=build(old,prior,sign)
    need(payload==expected,"corrected M30 packet must match re-executed classifier exactly")
    need(payload["humanReviewer"] is None
      and payload["semanticApproval"] is False
      and payload["automaticSourceBaselineAcceptance"] is False
      and payload["confirmedPostSkillTestManufacturingFinalDocumentChecklist"] is False
      and payload["allowFinalApplicationSubmission"] is False
      and payload["jobDocs"]=="hold"
      and payload["publicBetaAccess"]=="hold"
      and payload["releaseAuthorized"] is False,
      "cannot infer release from title correction")

def selftest():
    inputs=[read(SOURCE),read(M24),read(SIGN)]
    good=build(*inputs)
    check(good,*inputs)
    attacks=[
      lambda p:p.update(publicBetaAccess="open"),
      lambda p:p.update(jobDocs="confirmed"),
      lambda p:p.update(releaseAuthorized=True),
      lambda p:p.update(automaticSourceBaselineAcceptance=True),
      lambda p:p.update(semanticApproval=True),
      lambda p:p.update(humanReviewer="fabricated person"),
      lambda p:p.update(confirmedPostSkillTestManufacturingFinalDocumentChecklist=True),
      lambda p:p.update(allowFinalApplicationSubmission=True),
      lambda p:p.update(correctedCandidateCount=11),
      lambda p:p["remainingCandidates"][0].update(screeningStage="manufacturing_final_application_title_candidate"),
      lambda p:p["removedCandidates"][0].update(newClassifierStage="approved"),
      lambda p:p.update(rawFull320RowFeedRequeriedForCorrection=True),
      lambda p:p.update(originalTitleUrlSha256="a"*64),
    ]
    for i,fn in enumerate(attacks):
        p=copy.deepcopy(good);fn(p)
        try:check(p,*inputs)
        except (ValueError,KeyError,TypeError):pass
        else:raise AssertionError("unsafe correction mutation accepted "+str(i))
    mutated=copy.deepcopy(inputs)
    mutated[0]["titleCandidates"][0]["date"]="31 December 2026"
    try:build(*mutated)
    except (ValueError,KeyError,TypeError):pass
    else:raise AssertionError("invalid source candidate not rejected")
    print("M30_R1_CORRECTION_SELF_TEST_PASS 14_fail_closed_cases 2_psychology_dropped original_index_digest_preserved BETA_HOLD")
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--self-test",action="store_true")
    p.add_argument("--write",action="store_true")
    p.add_argument("--check",action="store_true")
    a=p.parse_args()
    if a.self_test:selftest()
    if a.write:
        need(not OUT.exists(),"append-only correction already exists")
        packet=build(read(SOURCE),read(M24),read(SIGN))
        OUT.write_text(json.dumps(packet,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
        print("M30_R1_CORRECTED_APPEND_ONLY original11 corrected9 psychology2 final_manufacturing0 betaHOLD")
    if a.check:
        check(read(OUT),read(SOURCE),read(M24),read(SIGN))
        print("M30_R1_CORRECTION_INTEGRITY_PASS 9_candidates exact_2_false_positives source_digest_unchanged")
    if not (a.self_test or a.write or a.check):p.error("choose action")
if __name__=="__main__":main()
