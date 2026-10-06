#!/usr/bin/env python3
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
WRITER=ROOT/"scripts/write_source_review_status.py"

sample={
  "acceptedCurrent":False,
  "partialAcceptance":False,
  "acceptanceBlocked":False,
  "configured":2,
  "checked":2,
  "changed":[
    {
      "id":"new_watch",
      "url":"https://example.gov/new",
      "reason":"new_unbaselined_source",
      "before":None,
      "after":"abc"
    },
    {
      "id":"changed_watch",
      "url":"https://example.gov/changed",
      "reason":"content_changed",
      "before":"old",
      "after":"new"
    }
  ],
  "failures":[]
}

with tempfile.TemporaryDirectory(prefix="kep-source-status-") as td:
    td=Path(td)
    inp=td/"result.json"
    out=td/"status.json"
    inp.write_text(json.dumps(sample),encoding="utf-8")
    subprocess.run(
      [sys.executable,str(WRITER),"--result",str(inp),"--output",str(out)],
      cwd=ROOT,check=True,capture_output=True,text=True
    )
    status=json.loads(out.read_text(encoding="utf-8"))
    assert status["state"]=="review_required"
    assert status["configured"]==2 and status["checked"]==2
    assert status["pendingBaselineSourceIds"]==["new_watch"]
    assert status["pendingBaselineUrls"]==["https://example.gov/new"]
    assert set(status["reviewRequiredSourceIds"])=={"new_watch","changed_watch"}
    assert "baseline" in status["message"].lower()

    sample["acceptedCurrent"]=True
    inp.write_text(json.dumps(sample),encoding="utf-8")
    subprocess.run(
      [sys.executable,str(WRITER),"--result",str(inp),"--output",str(out)],
      cwd=ROOT,check=True,capture_output=True,text=True
    )
    accepted=json.loads(out.read_text(encoding="utf-8"))
    assert accepted["pendingBaselineSourceIds"]==[]
    assert accepted["pendingBaselineUrls"]==[]
    assert accepted["reviewRequiredSourceIds"]==[]
    assert accepted["reviewRequiredUrls"]==[]

print("SOURCE_REVIEW_STATUS_SELFTEST_PASS")
