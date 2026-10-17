#!/usr/bin/env python3
"""M32 read-only launch-blocker snapshot: actual Pages source + live redirects.

Observes deployment without changing Pages, accepting source SHA, certifying
official notice contents or authorizing beta OPEN.
"""
from __future__ import annotations
import argparse,copy,json,re,subprocess
from datetime import datetime,timezone
from pathlib import Path
from zoneinfo import ZoneInfo
from audit_indonesia_beta_pages_live import audit,http_first_hop,ASSETS,LEGACY_ENTRYPOINTS
from diagnose_indonesia_beta_pages_source import inspect_live
from report_indonesia_beta_release_preflight import deployment_verified
ROOT=Path(__file__).resolve().parents[1]
DAY="2026-10-17"
OUT=ROOT/"research/source_reviews/indonesia_m32_pages_release_blockers_2026-10-17.json"
SHA=re.compile("[0-9a-f]{40}")
def read(p):
    return json.loads((ROOT/p).read_text(encoding="utf-8-sig"))
def demand(v,reason):
    if not v:raise ValueError("M32_RELEASE_SAFETY_HOLD "+reason)
def originals():
    w=read("research/source_reviews/indonesia_daily_readonly_2026-10-17.json")
    m30=read("research/source_reviews/indonesia_m30_post_skill_notice_candidates_corrected_r1_2026-10-17.json")
    queue=read("research/source_reviews/indonesia_m26_unsigned_review_handoff_2026-10-17.json")
    signed=read("recruitment/ID_BETA_SOURCE_SIGNOFF_20261017.json")
    program=read("docs/data/beta_program_v1.json")
    docs=read("docs/data/document_packs_2026.json")
    route=read("docs/data/id_e9_manufacturing_2026.json")
    demand(w["observedAtDate"]==DAY and w["checked"]==84
        and w["unacceptedBaselineDriftCount"]==12 and w["fetchFailures"]==0,"source monitor")
    demand(m30["correctedCandidateCount"]==9
        and m30["manufacturingExplicitFinalOnlineApplicationTitles"]==0
        and m30["jobDocs"]=="hold" and m30["publicBetaAccess"]=="hold",
        "M30 final-stage documents still missing")
    demand(queue["asOf"]==DAY and len(queue["tasks"])==20
        and queue["pendingSourceAlertCount"]==12
        and queue["humanPolicyReviewApproved"] is False
        and queue["finalManufacturingJobDocs"]=="hold"
        and all(x["decision"]=="pending" and x["humanReviewer"] is None
                and x["reviewedAt"] is None for x in queue["tasks"]),
        "20 manual review decisions still outstanding")
    demand(signed["status"]=="pending_manual_source_signoff"
       and signed["reviewer"] is None and signed["approvedAt"] is None
       and signed["betaAccess"]=="hold","no made-up signoff")
    demand(program["status"]=="hold"
       and program["releaseDecision"]["publicBeta"]=="pending_manual_approval"
       and program["application"]["intakeStatus"]=="open",
       "interest intake separate from user access")
    j=next(x for x in route["stages"] if x["id"]=="job_application")
    p=next(x for x in docs["packs"] if x["id"]=="job_application_manufacturing")
    demand(route["cycle"]==2026 and route["sector"]=="manufacturing"
       and j["brokerReplacement"]=="held_official_notice"
       and p["status"]=="awaiting_sector_notice"
       and p["items"]==[],"no invented exact document list")
    return True
def collect(source, live, head, now):
    originals()
    demand(now.astimezone(ZoneInfo("Asia/Jakarta")).date().isoformat()==DAY,
           "same-day evidence")
    demand(bool(SHA.fullmatch(head)),"git HEAD commit identity")
    # Source validation uses authenticated live GitHub Pages settings and
    # original Git blobs, not arbitrary user-provided authorization flags.
    src_pass=(source.get("mode")=="read_only"
       and source.get("sourceVerified") is True
       and source.get("status")=="DEPLOYED_MAIN_DRAFT_HEAD_NOT_PUBLISHED"
       and source.get("sourceBranch")=="main"
       and source.get("sourceFolder")=="/docs"
       and source.get("candidateRef")==head
       and source.get("mainRef")!=head
       and source.get("deployedMainFilesMatched")==len(ASSETS)
       and source.get("candidateHeadFilesMatched")==0
       and source.get("remoteChangesMade") is False
       and source.get("approvesBetaOpen") is False
       and source.get("sourceHashAccepted") is False)
    asset_ids={x["path"] for x in live["assets"] if isinstance(x,dict)}
    entry_ids={x["id"] for x in live["entrypoints"] if isinstance(x,dict)}
    demand(live["checkedRef"]==head and live["mode"]=="read_only"
       and live["authorizesRelease"] is False
       and len(live["assets"])==len(ASSETS)
       and asset_ids==set(ASSETS)
       and len(live["entrypoints"])==len(LEGACY_ENTRYPOINTS)
       and entry_ids=={x[0] for x in LEGACY_ENTRYPOINTS},"exact 9+6 live paths")
    secure_entries=sum(x["httpsOnly"] is True for x in live["entrypoints"])
    current_candidate_matches=sum(x["sameAsCheckedRef"] is True for x in live["assets"])
    # Never allow technical current-main observation to masquerade as HEAD deployment.
    demand(not deployment_verified(live,head) or not src_pass,
           "inconsistent main-only observation reports candidate HEAD deployed")
    block={
       "version":"1.0.0",
       "observedAtUTC":now.isoformat(),"observationDateJakarta":DAY,
       "type":"read_only_actual_live_pages_and_official_manual_gate_triage",
       "verifiedCandidateSHA":head,
       "publicBranch":"main","publicFolder":"/docs",
       "publicMainSHA":source.get("mainRef"),
       "pagesSourceVerdict":source.get("status"),
       "pagesSourceVerified":src_pass,
       "servedAssetsMatchingDeployedMain":source.get("deployedMainFilesMatched"),
       "servedAssetsMatchingDraftCandidateBySourceAudit":source.get("candidateHeadFilesMatched"),
       "assetsMatchingDraftCandidateByHttpAudit":current_candidate_matches,
       "criticalAssetCount":len(ASSETS),
       "httpsLegacyEntryPointsVerified":secure_entries,
       "httpsLegacyEntryPointsTotal":len(LEGACY_ENTRYPOINTS),
       "httpsDowngradeOrRedirectProblem":secure_entries!=len(LEGACY_ENTRYPOINTS),
       "releaseGates":[
        {"id":"applicant_route_and_2026_doc_hold","status":"PASS",
         "evidence":"27-stage app holds exact job documents and cross-year imports"},
        {"id":"source_monitor_retrieval","status":"PASS",
         "evidence":"84/84 official sources read-only Oct17; 12 drifts not accepted"},
        {"id":"official_source_human_semantic_signoff","status":"PENDING",
         "evidence":"12 source alerts, 20 distinct reviewer tasks, 0 signed"},
        {"id":"current_2026_manufacturing_final_documents","status":"PENDING",
         "evidence":"zero explicit final online Manufacturing notice titles in M30 corrected scope, exact official final annex not verified"},
        {"id":"published_main_source_integrity","status":"PASS" if src_pass else "BLOCKED",
         "evidence":"authenticated GH Pages main/docs vs current served files 9/9" if src_pass else "source verification not proven"},
        {"id":"candidate_head_deployment","status":"PENDING",
         "evidence":str(current_candidate_matches)+"/9 exact candidate served assets; live source "+str(source.get("candidateHeadFilesMatched"))+"/9"},
        {"id":"legacy_https_redirects","status":"PASS" if secure_entries==len(LEGACY_ENTRYPOINTS) else "BLOCKED",
         "evidence":str(secure_entries)+"/"+str(len(LEGACY_ENTRYPOINTS))+" HTTPS-only redirects, independently checked"},
        {"id":"manual_public_beta_open","status":"PENDING",
         "evidence":"candidate beta access HOLD, expression of interest intake OPEN"},
       ],
       "humanPolicyReviewApproved":False,
       "sourceHashBaselineAccepted":False,
       "finalManufacturingJobDocsVerified":False,
       "sameHeadCandidateDeploymentVerified":False,
       "productionChangesMade":False,"manualPublicBetaOpenApproved":False,
       "readyForManualReleaseDecision":False,
       "betaAccess":"hold","authorizesRelease":False,
       "note":"Even 9/9 published main and secure redirects do NOT show the Draft candidate is published. This report has no operator signoff or release authority.",
    }
    validate(block)
    return block
def validate(q):
    demand(q["observationDateJakarta"]==DAY and bool(SHA.fullmatch(q["verifiedCandidateSHA"])),
       "source date and exact git head")
    demand(q["publicBranch"]=="main" and q["publicFolder"]=="/docs",
       "not a feature branch publication")
    demand(len(q["releaseGates"])==8
       and {x["id"] for x in q["releaseGates"]}=={
        "applicant_route_and_2026_doc_hold","source_monitor_retrieval",
        "official_source_human_semantic_signoff","current_2026_manufacturing_final_documents",
        "published_main_source_integrity","candidate_head_deployment",
        "legacy_https_redirects","manual_public_beta_open"},"all blocker gates")
    statuses={x["id"]:x["status"] for x in q["releaseGates"]}
    demand(statuses["candidate_head_deployment"]=="PENDING"
       and statuses["official_source_human_semantic_signoff"]=="PENDING"
       and statuses["current_2026_manufacturing_final_documents"]=="PENDING"
       and statuses["manual_public_beta_open"]=="PENDING","responsible human gates")
    demand(q["criticalAssetCount"]==9 and q["httpsLegacyEntryPointsTotal"]==6
       and 0<=q["httpsLegacyEntryPointsVerified"]<=6
       and q["httpsDowngradeOrRedirectProblem"]==(q["httpsLegacyEntryPointsVerified"]!=6),
       "HTTPS evidence counts")
    demand(q["assetsMatchingDraftCandidateByHttpAudit"]<=9
       and q["servedAssetsMatchingDraftCandidateBySourceAudit"]==0
       and q["servedAssetsMatchingDeployedMain"]==9
       and q["pagesSourceVerified"] is True
       and q["pagesSourceVerdict"]=="DEPLOYED_MAIN_DRAFT_HEAD_NOT_PUBLISHED"
       and q["publicMainSHA"]!=q["verifiedCandidateSHA"],
       "real current published main not draft")
    demand(q["humanPolicyReviewApproved"] is False
       and q["sourceHashBaselineAccepted"] is False
       and q["finalManufacturingJobDocsVerified"] is False
       and q["sameHeadCandidateDeploymentVerified"] is False
       and q["productionChangesMade"] is False
       and q["manualPublicBetaOpenApproved"] is False
       and q["readyForManualReleaseDecision"] is False
       and q["betaAccess"]=="hold"
       and q["authorizesRelease"] is False,"do not simulate final release")
    return True
def selftest():
    sha="a"*40
    pages={"mode":"read_only","sourceVerified":True,
      "status":"DEPLOYED_MAIN_DRAFT_HEAD_NOT_PUBLISHED","sourceBranch":"main",
      "sourceFolder":"/docs","candidateRef":sha,"mainRef":"b"*40,
      "deployedMainFilesMatched":9,"candidateHeadFilesMatched":0,
      "remoteChangesMade":False,"approvesBetaOpen":False,"sourceHashAccepted":False}
    site={"checkedRef":sha,"mode":"read_only","authorizesRelease":False,
      "assets":[{"path":p,"sameAsCheckedRef":False} for p in ASSETS],
      "entrypoints":[{"id":x[0],"httpsOnly":True} for x in LEGACY_ENTRYPOINTS]}
    q=collect(pages,site,sha,datetime(2026,10,17,8,0,tzinfo=timezone.utc))
    tests=[
       lambda x:x.update(betaAccess="open"),
       lambda x:x.update(authorizesRelease=True),
       lambda x:x.update(manualPublicBetaOpenApproved=True),
       lambda x:x.update(humanPolicyReviewApproved=True),
       lambda x:x.update(finalManufacturingJobDocsVerified=True),
       lambda x:x.update(sourceHashBaselineAccepted=True),
       lambda x:x.update(productionChangesMade=True),
       lambda x:x.update(sameHeadCandidateDeploymentVerified=True),
       lambda x:x.update(readyForManualReleaseDecision=True),
       lambda x:x.update(pagesSourceVerified=False),
       lambda x:x.update(servedAssetsMatchingDeployedMain=8),
       lambda x:x.update(servedAssetsMatchingDraftCandidateBySourceAudit=9),
       lambda x:x["releaseGates"][2].update(status="PASS"),
       lambda x:x.update(publicBranch="feature"),
       lambda x:x.update(httpsLegacyEntryPointsVerified=7),
       lambda x:x.update(httpsDowngradeOrRedirectProblem=True),
    ]
    for i,change in enumerate(tests):
        b=copy.deepcopy(q);change(b)
        try:validate(b)
        except (ValueError,KeyError,TypeError):pass
        else:raise AssertionError("unsafe release gate mutation "+str(i))
    print("M32_RELEASE_BLOCKER_SELF_TEST_PASS 16_negative_states 8_explicit_gates unpublished_Draft_beta_HOLD")
def main():
    cli=argparse.ArgumentParser()
    for flag in ("self-test","write","check"):cli.add_argument("--"+flag,action="store_true")
    args=cli.parse_args()
    if args.self_test:selftest()
    if args.write:
        demand(not OUT.exists(),"append-only record already exists")
        now=datetime.now(timezone.utc)
        demand(now.astimezone(ZoneInfo("Asia/Jakarta")).date().isoformat()==DAY,"current local date")
        sha=subprocess.check_output(["git","-C",str(ROOT),"rev-parse","HEAD"],text=True).strip()
        source=inspect_live()
        def load(name):
            return subprocess.check_output(["git","-C",str(ROOT),"show","HEAD:docs/"+name])
        live=audit(http_first_hop,ROOT/"docs",sha,asset_loader=load)
        result=collect(source,live,sha,now)
        OUT.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
        for x in result["releaseGates"]:
            print("M32_GATE",x["id"],x["status"],x["evidence"],flush=True)
        print("M32_LIVE_PAGES_RELEASE_HOLD",str(result["servedAssetsMatchingDeployedMain"])+"/9",
            "HEAD_MATCH="+str(result["assetsMatchingDraftCandidateByHttpAudit"]),
            "HTTPS="+str(result["httpsLegacyEntryPointsVerified"])+"/6",
            "BETA_HOLD NO_MERGE_NO_DEPLOY")
    if args.check:
        q=read("research/source_reviews/indonesia_m32_pages_release_blockers_2026-10-17.json")
        validate(q)
        print("M32_LIVE_GATES_INTEGRITY_PASS main_9/9 unpublished_Draft beta_HOLD")
    if not (args.self_test or args.write or args.check):cli.error("select action")
if __name__=="__main__":main()
