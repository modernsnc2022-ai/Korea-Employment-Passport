#!/usr/bin/env python3
"""Validate KEP beta outreach ledger consistency."""

from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
METRICS = ROOT / "recruitment" / "OUTREACH_METRICS_2026-10-06.json"
SOURCES = ROOT / "docs" / "data" / "beta_recruitment_sources_v1.json"

failures: list[str] = []


def require(condition: bool, message: str) -> None:
    if not condition:
        failures.append(message)


def walk(value, found: list[tuple[str, str, str]], path: str = "root") -> None:
    if isinstance(value, list):
        for index, item in enumerate(value):
            walk(item, found, f"{path}[{index}]")
    elif isinstance(value, dict):
        source = value.get("sourceCode")
        status = value.get("status")
        if isinstance(source, str) and isinstance(status, str):
            found.append((source, status, path))
        for key, item in value.items():
            walk(item, found, f"{path}.{key}")


metrics = json.loads(METRICS.read_text(encoding="utf-8-sig"))
catalog = json.loads(SOURCES.read_text(encoding="utf-8-sig"))
allowed = set(catalog.get("codes", []))
found: list[tuple[str, str, str]] = []
walk(metrics, found)

for source, status, path in found:
    require(source in allowed, f"{path}: sourceCode not in catalog: {source}")
    require(status.strip() != "", f"{path}: empty outreach status for {source}")

legacy = metrics.get("legacyEmailReconciliation", [])
legacy_sources = [row.get("sourceCode") for row in legacy]
require(len(legacy_sources) == len(set(legacy_sources)), "legacyEmailReconciliation sourceCode values must be unique")
require(len(legacy) >= 20, "legacy Gmail reconciliation must preserve the recovered historical outreach rows")

expected_failed = {"hanguk_hakwon", "human_initiative_korea"}
observed_failed = {
    row.get("sourceCode")
    for row in legacy
    if str(row.get("status", "")).startswith("delivery_failed_")
}
require(expected_failed.issubset(observed_failed), "known failed legacy mailboxes must stay marked delivery_failed")

by_source: dict[str, set[str]] = defaultdict(set)
for source, status, _ in found:
    by_source[source].add(status)

initial_pending = {
    "manual_send_pending",
    "ready_not_sent",
    "draft_pending",
    "gmail_draft_prepared_not_sent",
}
terminal_prefixes = (
    "sent_",
    "email_sent_",
    "delivery_failed_",
    "closed_",
)
for source, statuses in by_source.items():
    has_initial_pending = any(status in initial_pending for status in statuses)
    has_terminal = any(status.startswith(terminal_prefixes) for status in statuses)
    require(
        not (has_initial_pending and has_terminal),
        f"{source}: initial-outreach pending state conflicts with already sent/failed/closed history: {sorted(statuses)}",
    )

dup_sources = {
    row.get("sourceCode")
    for row in metrics.get("duplicateIncidents", [])
    if row.get("action") == "do_not_recontact_until_inbound_reply_or_new_verified_need"
}
for source in dup_sources:
    require(source in allowed, f"duplicate incident source is not in catalog: {source}")

policy = metrics.get("conversionPolicy", {})
require(
    "Follow-up requires an explicit follow-up-ready ledger entry" in str(policy.get("preSendGuard", "")),
    "preSendGuard must preserve explicit follow-up gating",
)
recon_policy = metrics.get("ledgerReconciliationPolicy", {})
require(
    "must not be treated as a fresh initial-outreach target" in str(recon_policy.get("rule", "")),
    "ledger reconciliation must block fresh outreach to sent/closed/failed sources",
)

if failures:
    print("OUTREACH_LEDGER_FAIL")
    for failure in failures:
        print("- " + failure)
    sys.exit(1)

print(f"OUTREACH_LEDGER_PASS tracked_rows={len(found)} legacy_rows={len(legacy)}")
