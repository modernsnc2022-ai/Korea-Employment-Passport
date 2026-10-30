#!/usr/bin/env python3
"""M40: exactly bind officially observed notice URLs to unsigned reviewer tasks."""
import argparse
import copy
import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "research/source_reviews/indonesia_m40_oct18_notice_handoff.json"
DAY = "2026-10-18"

def load(filename):
    return json.loads((ROOT / filename).read_text(encoding="utf-8-sig"))

def require(value, explanation):
    if not value:
        raise ValueError("M40_NO_AUTOMATIC_REVIEW_APPROVAL: " + explanation)

def build():
    a = load("research/source_reviews/indonesia_m21_original_html_audit_2026-10-17.json")
    b = load("research/source_reviews/indonesia_m34_unsigned_release_review_packet_2026-10-17.json")
    c = load("research/source_reviews/indonesia_m38_oct18_official_beta_handoff.json")
    d = load("research/source_reviews/indonesia_m39_oct18_preflight_live_result.json")
    from audit_m38_oct18_release_sources import verify as verify_m38
    verify_m38(c)
    require(a["observedAtDate"] == "2026-10-17"
        and len(a["manufacturingNoticeHtml"]) == 7
        and a["humanOfficialSemanticSignoff"] is False, "original 7 HTML pages")
    require(b["pendingReviewTasks"] == 20 and len(b["reviewTasks"]) == 20
        and all(t["semanticDecision"] == "pending" and t["reviewerName"] is None
                for t in b["reviewTasks"]), "20 unsigned work orders")
    require(c["asOfJakarta"] == DAY and c["kp2miAnnouncementsRead"] == 320
        and c["kp2mi2026ManufacturingNotices"] == 7
        and c["explicit2026FinalManufacturingApplicationHeadlineCandidates"] == 0
        and c["generic2026FinalApplicationReviewCandidates"] == 0,
        "dated official title observation is not a final checklist")
    gates = {g["id"]: g["status"] for g in d["gates"]}
    require(d["asOf"] == DAY and d["authorizesRelease"] is False
        and gates["kp2mi_manufacturing_release_day_signoff"] == "PENDING"
        and gates["exact_2026_manufacturing_final_job_documents"] == "PENDING",
        "manual notice and final document release gates remain pending")
    notices = {r["url"]: r for r in a["manufacturingNoticeHtml"]}
    tasks = [r for r in b["reviewTasks"] if r["taskId"].startswith("NOTICE:")]
    require(len(tasks) == 7 and {r["officialOriginalUrl"] for r in tasks} == set(notices),
        "seven original URLs bind every reviewer work order")
    reviewed = []
    for task in tasks:
        original = notices[task["officialOriginalUrl"]]
        dt = datetime.fromisoformat(original["date"])
        correct_id = "NOTICE:" + str(dt.day) + "-" + dt.strftime("%B") + "-" + str(dt.year)
        require(task["taskId"] == correct_id, "notice date and reviewer key")
        reviewed.append({
            "taskId": task["taskId"], "sourceStage": task["scope"],
            "noticeUrl": original["url"], "noticeDate": original["date"],
            "noticeTitle": original["title"], "humanOriginalHtmlReviewed": False,
            "annexPageCitation": None, "reviewerFullName": None,
            "reviewedAt": None, "semanticDecision": "pending",
            "isFinal2026ManufacturingJobDocuments": False
        })
    hr = c["hrdKoreaIndonesiaManufacturingScheduleCandidates"]
    require(len(hr) == 2, "two official Indonesia Manufacturing timetables")
    return {
        "kind": "unsigned_current_day_official_notice_reviewer_binding",
        "observationDayJakarta": DAY,
        "officialKP2MIIndex": "https://kp2mi.go.id/gtog-korea/pengumuman",
        "kp2miTitlesChecked": 320, "kp2miManufacturingNotices": reviewed,
        "HRDKoreaScheduleObservations": [{
            "examNo": x["examNo"], "title": x["title"], "url": x["url"],
            "humanApplicabilityReview": "pending", "finalJobDocs": False
        } for x in hr],
        "unassignedOriginalReviewerTasks": 20,
        "unacceptedSourceShaAlerts": 12,
        "newFinalManufacturingJobApplicationTitleCandidates": 0,
        "currentNoticeIndexMachineObserved": True,
        "humanNoticeContentsSigned": False,
        "final2026ManufacturingJobDocumentsVerified": False,
        "sourceHashAutoAccepted": False,
        "candidateDeployed": False, "betaAccess": "hold",
        "releaseAuthorized": False,
        "evidenceLimit": "Dated M38 bounded KP2MI listing and M21 individual original HTML observations; no same-day reread of all 7 full bodies, PDF semantic signoff, official government certification, or final job-doc requirements."
    }

def verify(packet):
    require(packet == build(), "all identities and safety fields must match read-only official evidence")

def selftest():
    record = load("research/source_reviews/indonesia_m40_oct18_notice_handoff.json")
    verify(record)
    attempts = [
        lambda x: x.update(betaAccess="open"),
        lambda x: x.update(releaseAuthorized=True),
        lambda x: x.update(humanNoticeContentsSigned=True),
        lambda x: x.update(final2026ManufacturingJobDocumentsVerified=True),
        lambda x: x.update(sourceHashAutoAccepted=True),
        lambda x: x.update(candidateDeployed=True),
        lambda x: x.update(newFinalManufacturingJobApplicationTitleCandidates=1),
        lambda x: x.update(observationDayJakarta="2026-10-17"),
        lambda x: x["kp2miManufacturingNotices"][0].update(semanticDecision="approved"),
        lambda x: x["kp2miManufacturingNotices"][0].update(reviewerFullName="Invented"),
        lambda x: x["kp2miManufacturingNotices"][0].update(noticeUrl="https://invalid.example"),
        lambda x: x["kp2miManufacturingNotices"].pop(),
        lambda x: x["HRDKoreaScheduleObservations"][0].update(finalJobDocs=True)
    ]
    for i, change in enumerate(attempts):
        modified = copy.deepcopy(record)
        change(modified)
        try: verify(modified)
        except (ValueError, KeyError, TypeError): pass
        else: raise AssertionError("unsafe review promotion " + str(i))
    print("M40_OFFICIAL_REVIEW_BINDING_PASS 13_negative_cases 7_notices 2_HRD 20_unsigned")

if __name__ == "__main__":
    cli = argparse.ArgumentParser()
    cli.add_argument("--check", action="store_true")
    cli.add_argument("--self-test", action="store_true")
    args = cli.parse_args()
    if args.check:
        verify(load("research/source_reviews/indonesia_m40_oct18_notice_handoff.json"))
        print("M40_EXACT_ORIGINAL_SCOPE_CHECK_PASS beta_HOLD")
    if args.self_test:
        selftest()
