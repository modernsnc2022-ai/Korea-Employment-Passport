#!/usr/bin/env python3
"""M39: transform Oct18 M38 REAL machine-only monitor observation to preflight shape.

A complete HTTP source read is never a policy signoff. Only the committed,
validated M38 original observation authorizes a technical 84/84 PASS flag.
No current official original job-docs, deploy or public-beta OPEN are inferred.
"""
from __future__ import annotations
import argparse,copy,hashlib,json
from pathlib import Path
from audit_m38_oct18_release_sources import verify as verify_m38
ROOT=Path(__file__).resolve().parents[1]
M38=ROOT/"research/source_reviews/indonesia_m38_oct18_official_beta_handoff.json"
M34=ROOT/"research/source_reviews/indonesia_m34_unsigned_release_review_packet_2026-10-17.json"
OUT=ROOT/"research/source_reviews/indonesia_m39_oct18_preflight_technical_watch.json"
DATE="2026-10-18"
def read(p):return json.loads(p.read_text(encoding="utf-8-sig"))
def require(condition,msg):
    if not condition:raise ValueError("M39_NO_POLICY_AUTO_SIGNOFF "+msg)
def inputs():
    packet=read(M38);verify_m38(packet)
    tasks=read(M34)["reviewTasks"]
    return packet,tasks,hashlib.sha256(M38.read_bytes()).hexdigest()
def compose():
    m,tasks,digest=inputs()
    source_scopes={x["taskId"].removeprefix("SRC:"):x["scope"] for x in tasks
                   if x["taskId"].startswith("SRC:")}
    ids=[x["sourceId"] for x in m["sourceMonitorCurrentUnacceptedChanges"]]
    require(len(ids)==len(set(ids)) and set(ids).issubset(source_scopes),
            "M38 drift scope must map to M34 reviewer task")
    counts={
        "korea_shared":sum(source_scopes[x]=="korea_shared" for x in ids),
        "multi_country_eps_schedule":sum(source_scopes[x]=="multi_country_eps_schedule" for x in ids),
        "other_country":sum(source_scopes[x]=="other_country" for x in ids),
        "unclassified_requires_manual_scope_review":
           sum(source_scopes[x] not in ("korea_shared","multi_country_eps_schedule","other_country") for x in ids)
    }
    return {
        "version":"1.0.0","kind":"validated_m38_machine_only_technical_release_watch",
        "observedAtDate":DATE,"configured":84,
        "checked":m["sourceMonitorFetched"],
        "fetchFailures":len(m["sourceMonitorFailedIds"]),
        "failedSourceIds":m["sourceMonitorFailedIds"],
        "unacceptedBaselineDriftCount":m["sourceMonitorUnacceptedDriftCount"],
        "groupCounts":counts,
        "pendingAlertSourceIds":sorted(ids),
        "upstreamM38Sha256":digest,
        "upstreamM38ObservedUTC":m["liveOfficialDiscoveryObservedUTC"],
        "completeOfficialTechnicalRead":m["sourceMonitorTechnicallyComplete"],
        "sourceHashAutoAccepted":False,
        "humanSourcePolicyApproved":False,
        "manualFinal2026ManufacturingDocumentsApproved":False,
        "signedCurrentDayReleaseEvidence":False,
        "productionDeploymentApproved":False,
        "publicBetaAccess":"hold",
        "releaseAuthorized":False,
        "safetyExplanation":"Oct18 84/84 source retrieval is a machine observation only. Not same-day semantic signoff, not official final online job-docs, and not current HEAD deployment."
    }
def validate(watch,manifest):
    expected=compose()
    require(isinstance(watch,dict) and watch==expected,
            "preflight watch must EXACTLY match immutable M38 derived adapter")
    configured=manifest["sources"]
    require(len(configured)==84 and len({x["id"] for x in configured})==84,
            "monitor official manifest identity")
    require(watch["configured"]==len(configured)
        and watch["checked"]==84 and watch["fetchFailures"]==0
        and watch["completeOfficialTechnicalRead"] is True
        and watch["unacceptedBaselineDriftCount"]==12
        and watch["groupCounts"]=={
             "korea_shared":5,"multi_country_eps_schedule":2,
             "other_country":5,"unclassified_requires_manual_scope_review":0}
        and set(watch["pendingAlertSourceIds"]).issubset({x["id"] for x in configured})
        and watch["sourceHashAutoAccepted"] is False
        and watch["humanSourcePolicyApproved"] is False
        and watch["signedCurrentDayReleaseEvidence"] is False
        and watch["manualFinal2026ManufacturingDocumentsApproved"] is False
        and watch["productionDeploymentApproved"] is False
        and watch["publicBetaAccess"]=="hold" and watch["releaseAuthorized"] is False,
        "Oct18 technical observation cannot approve policy or release")
    return True
def self_test():
    original=compose();manifest=read(ROOT/"monitor/sources.json");validate(original,manifest)
    mods=[
        lambda x:x.update(observedAtDate="2026-10-17"),
        lambda x:x.update(checked=83),
        lambda x:x.update(fetchFailures=1),
        lambda x:x.update(completeOfficialTechnicalRead=False),
        lambda x:x.update(unacceptedBaselineDriftCount=0),
        lambda x:x.update(groupCounts={"korea_shared":12}),
        lambda x:x.update(pendingAlertSourceIds=[]),
        lambda x:x.update(upstreamM38Sha256="0"*64),
        lambda x:x.update(sourceHashAutoAccepted=True),
        lambda x:x.update(humanSourcePolicyApproved=True),
        lambda x:x.update(signedCurrentDayReleaseEvidence=True),
        lambda x:x.update(manualFinal2026ManufacturingDocumentsApproved=True),
        lambda x:x.update(productionDeploymentApproved=True),
        lambda x:x.update(publicBetaAccess="open"),
        lambda x:x.update(releaseAuthorized=True),
        lambda x:x.update(kind="human_signed"),
    ]
    for i,fn in enumerate(mods):
        fake=copy.deepcopy(original);fn(fake)
        try:validate(fake,manifest)
        except (ValueError,KeyError,TypeError):pass
        else:raise AssertionError("Unsafe M39 watch accepted "+str(i))
    print("M39_TECHNICAL_ONLY_WATCH_SELF_TEST_PASS 16_negative_cases 84_observed 12_alerts still_unsigned beta_HOLD")
def main():
    p=argparse.ArgumentParser()
    for flag in ["write","check","self-test"]:p.add_argument("--"+flag,action="store_true")
    a=p.parse_args()
    if a.write:
        require(not OUT.exists(),"append-only M39 audit already exists")
        val=compose();validate(val,read(ROOT/"monitor/sources.json"))
        OUT.write_text(json.dumps(val,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
        print("M39_MACHINE_ONLY_WATCH_WRITTEN",val["checked"],"/84",val["unacceptedBaselineDriftCount"],"drifts")
    if a.check:
        validate(read(OUT),read(ROOT/"monitor/sources.json"))
        print("M39_MONITOR_ADAPTER_INTEGRITY_PASS source_fresh_machine_only_without_signoff")
    if a.self_test:self_test()
    if not(a.write or a.check or a.self_test):p.error("choose operation")
if __name__=="__main__":main()
