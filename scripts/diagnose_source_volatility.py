#!/usr/bin/env python3
from __future__ import annotations

import json
import time
from pathlib import Path

from check_official_sources import fetch_fingerprint

ROOT = Path(__file__).resolve().parents[1]
SOURCES = ROOT / "monitor" / "sources.json"
BASELINE = ROOT / "monitor" / "source_hashes.json"
STATUS = ROOT / "docs" / "data" / "source_review_status.json"
TLS_PINS = ROOT / "monitor" / "tls_pins.json"

sources = json.loads(SOURCES.read_text(encoding="utf-8-sig"))["sources"]
baseline = json.loads(BASELINE.read_text(encoding="utf-8-sig"))
status = json.loads(STATUS.read_text(encoding="utf-8-sig"))
tls_pins = json.loads(TLS_PINS.read_text(encoding="utf-8-sig")) if TLS_PINS.exists() else {"hosts": {}}

changed_ids = set(status.get("reviewRequiredSourceIds", []))
targets = [row for row in sources if row.get("id") in changed_ids and "kp2mi.go.id" in row.get("url", "")]

print(f"SOURCE_VOLATILITY_DIAGNOSTIC targets={len(targets)}")
if not targets:
    raise SystemExit(0)

volatile = []
stable = []
rows = []

for index, source in enumerate(targets, start=1):
    source_id = source["id"]
    first = fetch_fingerprint(source["url"], tls_pins)
    time.sleep(1.4)
    second = fetch_fingerprint(source["url"], tls_pins)
    before = baseline.get(source_id, {})
    same = first["sha256"] == second["sha256"]
    row = {
        "id": source_id,
        "sameAcrossImmediateFetches": same,
        "baselineLength": before.get("contentLength"),
        "currentLength": second.get("contentLength"),
        "lengthDelta": (
            second.get("contentLength", 0) - before.get("contentLength", 0)
            if isinstance(before.get("contentLength"), int)
            else None
        ),
        "baselineSha": before.get("sha256"),
        "currentSha": second.get("sha256"),
        "tlsMode": second.get("tlsMode"),
    }
    rows.append(row)
    (stable if same else volatile).append(source_id)
    print(json.dumps(row, ensure_ascii=False))
    if index < len(targets):
        time.sleep(1.4)

deltas = [row["lengthDelta"] for row in rows if isinstance(row["lengthDelta"], int)]
print(
    "SOURCE_VOLATILITY_SUMMARY "
    f"stable_immediate={len(stable)} volatile_immediate={len(volatile)} "
    f"min_delta={min(deltas) if deltas else 'n/a'} "
    f"max_delta={max(deltas) if deltas else 'n/a'}"
)
if volatile:
    print("VOLATILE_IDS " + ",".join(volatile))
