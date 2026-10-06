#!/usr/bin/env python3
"""Fail-closed pre-send guard for KEP outreach source codes."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
METRICS = ROOT / "recruitment/OUTREACH_METRICS_2026-10-06.json"
SOURCES = ROOT / "docs/data/beta_recruitment_sources_v1.json"

SENT_TOKENS = ("sent_", "email_sent_", "followup_sent_")
CLOSED_TOKENS = ("closed_", "do_not_retry")
READY_INITIAL = {"ready_not_sent", "draft_pending", "gmail_draft_prepared_not_sent", "manual_send_pending"}
READY_FOLLOWUP = {"followup_ready_not_sent"}


def walk(value):
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from walk(child)
    elif isinstance(value, list):
        for child in value:
            yield from walk(child)


def source_rows(metrics, source):
    return [row for row in walk(metrics) if isinstance(row, dict) and row.get("sourceCode") == source]


def decide(metrics, source, mode):
    rows = source_rows(metrics, source)
    statuses = [str(row.get("status", "")) for row in rows if row.get("status")]

    if mode == "initial":
        if any(any(token in status for token in SENT_TOKENS + CLOSED_TOKENS) for status in statuses):
            return False, "already_sent_or_closed"
        if statuses and not any(status in READY_INITIAL for status in statuses):
            return False, "not_initial_send_ready"
        return True, "initial_send_allowed"

    if mode == "followup":
        if any(status in READY_FOLLOWUP for status in statuses):
            return True, "followup_allowed"
        return False, "followup_not_explicitly_ready"

    return False, "unsupported_mode"


def self_test():
    sample = {
        "a": [{"sourceCode":"alpha","status":"sent_2026-10-06"}],
        "b": [{"sourceCode":"beta","status":"ready_not_sent"}],
        "c": [{"sourceCode":"gamma","status":"followup_ready_not_sent"}],
        "d": [{"sourceCode":"delta","status":"closed_declined_external_service_policy"}],
    }
    assert decide(sample, "alpha", "initial") == (False, "already_sent_or_closed")
    assert decide(sample, "beta", "initial") == (True, "initial_send_allowed")
    assert decide(sample, "gamma", "followup") == (True, "followup_allowed")
    assert decide(sample, "alpha", "followup") == (False, "followup_not_explicitly_ready")
    assert decide(sample, "delta", "initial") == (False, "already_sent_or_closed")
    print("OUTREACH_SEND_GUARD_SELF_TEST_PASS")


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--source")
    ap.add_argument("--mode", choices=["initial","followup"], default="initial")
    ap.add_argument("--self-test", action="store_true")
    args=ap.parse_args()

    if args.self_test:
        self_test()
        return 0
    if not args.source:
        ap.error("--source is required")

    metrics=json.loads(METRICS.read_text(encoding="utf-8-sig"))
    sources=set(json.loads(SOURCES.read_text(encoding="utf-8-sig")).get("codes", []))
    if args.source not in sources:
        print("OUTREACH_SEND_BLOCKED unsupported_source")
        return 2

    allowed, reason=decide(metrics,args.source,args.mode)
    if not allowed:
        print("OUTREACH_SEND_BLOCKED "+reason)
        return 3
    print("OUTREACH_SEND_ALLOWED "+reason)
    return 0


if __name__=="__main__":
    raise SystemExit(main())
