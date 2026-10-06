#!/usr/bin/env python3
import argparse
import json
from pathlib import Path

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--result",default="monitor/check_result.json")
    p.add_argument("--output",default="docs/data/source_review_status.json")
    args=p.parse_args()

    result=json.loads(Path(args.result).read_text(encoding="utf-8-sig"))
    changed=result.get("changed",[])
    failures=result.get("failures",[])
    pending_baseline=[x for x in changed if x.get("reason")=="new_unbaselined_source"]
    accepted=bool(result.get("acceptedCurrent",False))
    partial_acceptance=bool(result.get("partialAcceptance",False))
    acceptance_blocked=bool(result.get("acceptanceBlocked",False))

    state = (
      "fetch_warning" if accepted and (failures or partial_acceptance) else
      "clean" if accepted else
      "review_required" if changed else
      "fetch_warning" if failures or acceptance_blocked else
      "clean"
    )

    status={
      "version":"1.1.0",
      "state":state,
      "autoPublishRules":False,
      "configured":result.get("configured",0),
      "checked":result.get("checked",0),
      "reviewRequiredUrls":[] if accepted else sorted({x.get("url","") for x in changed if x.get("url")}),
      "reviewRequiredSourceIds":[] if accepted else sorted({x.get("id","") for x in changed if x.get("id")}),
      "pendingBaselineUrls":[] if accepted else sorted({x.get("url","") for x in pending_baseline if x.get("url")}),
      "pendingBaselineSourceIds":[] if accepted else sorted({x.get("id","") for x in pending_baseline if x.get("id")}),
      "fetchFailureUrls":sorted({x.get("url","") for x in failures if x.get("url")}),
      "fetchFailureSourceIds":sorted({x.get("id","") for x in failures if x.get("id")}),
      "message":(
        "Reviewed changes were accepted for successfully fetched sources; failed sources keep their previous reviewed baseline and remain under fetch warning."
        if accepted and (failures or partial_acceptance) else
        "Reviewed official-source changes were accepted and no unreviewed changes remain."
        if accepted else
        "New official watch targets have no accepted baseline yet; fetch and review them before baseline acceptance or route promotion."
        if pending_baseline else
        "Official source changed; affected guidance must be reviewed before being treated as exact."
        if changed else
        "One or more official sources could not be checked; published rules were not changed automatically."
        if failures or acceptance_blocked else
        "No unreviewed official-source changes are currently recorded."
      )
    }
    Path(args.output).write_text(json.dumps(status,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(status,ensure_ascii=False))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
