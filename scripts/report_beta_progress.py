#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TRACKER = ROOT / "recruitment" / "BETA_TESTER_TRACKER.csv"
ROUTE = ROOT / "docs" / "data" / "id_e9_manufacturing_2026.json"
ROUTE_STAGE_IDS = [
    row["id"] for row in json.loads(ROUTE.read_text(encoding="utf-8-sig")).get("stages", [])
]

LATE_STAGE_BUCKETS = {
    "roster": {"roster", "employer_selection"},
    "slc": {"slc", "post_slc_requirements"},
    "visa_opp": {"visa_docs", "predeparture_training", "mcu3_departure"},
    "departure": {"departure"},
}

def nonempty(row: dict[str, str], key: str) -> bool:
    return bool((row.get(key) or "").strip())

def count_value(rows: list[dict[str, str]], key: str, value: str) -> int:
    return sum(1 for row in rows if (row.get(key) or "").strip() == value)

def safe_counter(rows: list[dict[str, str]], key: str) -> Counter[str]:
    counter: Counter[str] = Counter()
    for row in rows:
        value = (row.get(key) or "").strip()
        if value:
            counter[value] += 1
    return counter

def stage_evidence_counter(rows: list[dict[str, str]], key: str) -> Counter[str]:
    counter: Counter[str] = Counter()
    for row in rows:
        values = [part.strip() for part in (row.get(key) or "").split(";") if part.strip()]
        for stage_id in values:
            counter[stage_id] += 1
    return counter

def render(rows: list[dict[str, str]]) -> str:
    active = [row for row in rows if row.get("target_group", "").strip() == "active_applicant"]
    workers = [row for row in rows if row.get("target_group", "").strip() == "e9_worker_korea"]

    applications = sum(nonempty(row, "application_received_at") for row in active)
    accepted = count_value(active, "eligibility_status", "accepted")
    activated = sum(nonempty(row, "activated_at") for row in active)
    feedback_started = sum(
        (row.get("feedback_status") or "").strip() in {"active", "complete"}
        for row in active
    )
    feedback_complete = count_value(active, "feedback_status", "complete")

    enrolled_workers = [row for row in workers if nonempty(row, "created_at")]
    assigned_active = [row for row in active if nonempty(row, "application_received_at")]
    evidence_rows = assigned_active + enrolled_workers

    interviews_completed = count_value(enrolled_workers, "interview_status", "completed")
    worker_year_context = sum(nonempty(row, "experience_year") for row in enrolled_workers)
    completed_workers = [
        row for row in enrolled_workers
        if (row.get("interview_status") or "").strip() == "completed"
    ]
    current_cycle_worker_rows = [
        row for row in completed_workers
        if (row.get("experience_year") or "").strip() == "2026"
    ]
    current_cycle_workers = len(current_cycle_worker_rows)
    prior_cycle_workers = sum(
        (row.get("experience_year") or "").strip().isdigit()
        and (row.get("experience_year") or "").strip() != "2026"
        for row in completed_workers
    )
    unknown_cycle_workers = sum(
        (row.get("experience_year") or "").strip() == "unknown"
        for row in completed_workers
    )
    workplace_evidence_published = count_value(
        enrolled_workers, "workplace_evidence_status", "published_single_verified_worker"
    )

    current_cycle_evidence_rows = assigned_active + current_cycle_worker_rows
    zero_pass_counts = stage_evidence_counter(current_cycle_evidence_rows, "zero_broker_pass_stages")
    zero_fail_counts = stage_evidence_counter(current_cycle_evidence_rows, "zero_broker_fail_stages")
    zero_fail_stage_ids = [stage_id for stage_id in ROUTE_STAGE_IDS if zero_fail_counts[stage_id] > 0]
    zero_pass_ready_stage_ids = [
        stage_id for stage_id in ROUTE_STAGE_IDS
        if zero_pass_counts[stage_id] > 0 and zero_fail_counts[stage_id] == 0
    ]
    zero_uncovered_stage_ids = [
        stage_id for stage_id in ROUTE_STAGE_IDS
        if zero_pass_counts[stage_id] == 0 and zero_fail_counts[stage_id] == 0
    ]
    zero_broker_stage_ready = (
        len(zero_pass_ready_stage_ids) == len(ROUTE_STAGE_IDS)
        and not zero_fail_stage_ids
    )

    broker_gaps_resolved = count_value(evidence_rows, "broker_gap_status", "resolved")
    broker_gaps_open = count_value(evidence_rows, "broker_gap_status", "open")
    retest_passed = count_value(evidence_rows, "retest_status", "passed")

    late_stage = {}
    for bucket, stages in LATE_STAGE_BUCKETS.items():
        late_stage[bucket] = sum(
            1 for row in active if (row.get("current_stage") or "").strip() in stages
        )

    active_stage_counts = safe_counter(active, "current_stage")
    worker_stage_counts = safe_counter(workers, "current_stage")

    late_ready = all(late_stage[bucket] >= 1 for bucket in LATE_STAGE_BUCKETS)
    cohort_ready = len(active) == 30 and len(workers) == 20
    evidence_ready = (
        applications >= 30
        and activated >= 30
        and len(enrolled_workers) >= 20
        and interviews_completed >= 20
        and worker_year_context >= 20
        and workplace_evidence_published >= 1
        and late_ready
        and broker_gaps_open == 0
        and zero_broker_stage_ready
    )

    lines = [
        "# Beta progress — privacy-safe aggregate",
        "",
        "This report contains counts only. It must not include participant names, contact details, identity numbers, addresses, or free-text notes.",
        "",
        "## Cohort",
        f"- Public beta slots: {len(active)}/30",
        f"- E-9 worker validation slots: {len(workers)}/20",
        f"- Cohort structure ready: {'YES' if cohort_ready else 'NO'}",
        "",
        "## Public beta funnel",
        f"- Applications received after OPEN: {applications}/30",
        f"- Eligibility accepted: {accepted}/30",
        f"- Beta accounts activated: {activated}/30",
        f"- Feedback started: {feedback_started}/30",
        f"- Feedback completed: {feedback_complete}/30",
        "",
        "## Retrospective validation",
        f"- E-9 worker validators enrolled: {len(enrolled_workers)}/20",
        f"- E-9 worker interviews completed: {interviews_completed}/20",
        f"- Experience-year context captured: {worker_year_context}/20",
        f"- Completed interviews from 2026 experience: {current_cycle_workers}",
        f"- Completed interviews from prior-cycle experience: {prior_cycle_workers}",
        f"- Completed interviews with unknown experience year: {unknown_cycle_workers}",
        "- Prior-cycle/unknown worker interviews are retrospective gap evidence only; they are not 2026 route-rule PASS evidence.",
        f"- Privacy-reviewed workplace evidence published: {workplace_evidence_published}",
        "",
        "## Broker replacement evidence",
        f"- Broker gaps open: {broker_gaps_open}",
        f"- Broker gaps resolved: {broker_gaps_resolved}",
        f"- Retests passed: {retest_passed}",
        f"- Current-cycle evidence rows: {len(current_cycle_evidence_rows)}",
        f"- Zero-broker stage PASS coverage: {len(zero_pass_ready_stage_ids)}/{len(ROUTE_STAGE_IDS)}",
        "- Current-cycle FAIL stages: " + (
            ", ".join(zero_fail_stage_ids) if zero_fail_stage_ids else "none"
        ),
        "- Stages with no current-cycle PASS/FAIL evidence yet: " + (
            ", ".join(zero_uncovered_stage_ids) if zero_uncovered_stage_ids else "none"
        ),
        f"- Stage-level zero-broker evidence ready: {'YES' if zero_broker_stage_ready else 'NO'}",
        "",
        "## Required late-stage coverage among active applicants",
        f"- Roster / employer selection: {late_stage['roster']}",
        f"- SLC / post-SLC: {late_stage['slc']}",
        f"- Visa / OPP / final medical: {late_stage['visa_opp']}",
        f"- Departure: {late_stage['departure']}",
        f"- Late-stage coverage ready: {'YES' if late_ready else 'NO'}",
        "",
        "## Stage distribution",
        "- Active applicants: " + (
            ", ".join(f"{key}={value}" for key, value in sorted(active_stage_counts.items()))
            if active_stage_counts else "no stages recorded"
        ),
        "- E-9 workers: " + (
            ", ".join(f"{key}={value}" for key, value in sorted(worker_stage_counts.items()))
            if worker_stage_counts else "no stages recorded"
        ),
        "",
        "## Evidence gate",
        f"- Real-user evidence ready for route PASS review: {'YES' if evidence_ready else 'NO'}",
        "- This aggregate does not itself declare Broker Replacement Rate PASS; route PASS still requires reviewing the actual sanitized beta evidence and confirming every necessary private-broker task is replaced.",
        "",
    ]
    return "\n".join(lines)

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", help="Optional markdown output path")
    args = parser.parse_args()

    with TRACKER.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))

    if len(rows) != 50:
        raise SystemExit(f"BETA_PROGRESS_FAIL expected 50 tracker rows, found {len(rows)}")

    report = render(rows)
    if args.output:
        path = Path(args.output)
        if not path.is_absolute():
            path = ROOT / path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(report + "\n", encoding="utf-8")
    print(report)
    print("BETA_PROGRESS_PASS privacy_safe_counts_only=true")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
