#!/usr/bin/env python3
"""Fail closed on stale public beta-readiness claims in the operator snapshot.

Pure local integrity guard. This does not query, approve or deploy any source.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
DOCUMENT = "recruitment/BETA_OPEN_READINESS.md"


def load_json(rel: str) -> dict:
    return json.loads((ROOT / rel).read_text(encoding="utf-8-sig"))


def problems(doc: str, *, program: dict, source: dict, route: dict,
             answers: dict, broker: dict, forms: dict, manufacturing: dict) -> list[str]:
    field_count = sum(len(row.get("fields", [])) for row in forms.get("forms", []))
    expected = {
        "Indonesia Manufacturing supported stages": str(len(route.get("stages", []))),
        "Indonesia exact-answer records": str(len(answers.get("answers", []))),
        "Broker question catalog": str(len(broker.get("questions", []))),
        "Form wizards": str(len(forms.get("forms", []))),
        "Form fields": str(field_count),
        "Monitored official sources": f"{source.get('checked')}/{source.get('configured')} fetched",
        "Official source state": str(source.get("state")),
        "Current exact Manufacturing job-application HOLD count":
            str(len(manufacturing.get("heldQuestions", []))),
        "Beta applicant-interest intake": str(program.get("application", {}).get("intakeStatus")),
        "Actual public beta access": str(program.get("status")),
        "Worker validation-panel access": str(program.get("retrospectivePanel", {}).get("status")),
    }
    failures = []
    for name, value in expected.items():
        lines = re.findall(r"^\- " + re.escape(name) + r": \*\*(.*?)\*\*\s*$",
                           doc, flags=re.M)
        if lines != [value]:
            failures.append(f"{name}: expected exactly **{value}**, found {lines!r}")
    holds = manufacturing.get("heldQuestions", [])
    if len(holds) != 1 or holds != ["job_docs"]:
        failures.append("Manufacturing exact HOLD list is not the single protected job_docs")
    if "- Exact held Manufacturing item: `job_docs`" not in doc:
        failures.append("exact job_docs HOLD is missing from operator snapshot")
    if "not yet in" in doc.lower():
        failures.append("ambiguous dated release status in snapshot")
    # These release truths must remain separate from a green code test suite.
    for phrase in (
        "PR #324: Draft/unmerged",
        "beta access",
        "actual release day",
        "same-reviewed-HEAD",
        "6/6",
        "9/9",
        "83 of 84",
        "one genuine external official-evidence HOLD",
    ):
        if phrase.lower() not in doc.lower():
            failures.append(f"missing conservative release guard text: {phrase}")
    if source.get("state") != "clean" and "all official sources clean" in doc.lower():
        failures.append("snapshot falsely claims universally clean official sources")
    return failures


def inputs() -> dict:
    return {
        "program": load_json("docs/data/beta_program_v1.json"),
        "source": load_json("docs/data/source_review_status.json"),
        "route": load_json("docs/data/id_e9_manufacturing_2026.json"),
        "answers": load_json("docs/data/exact_answer_rules_v1.json"),
        "broker": load_json("docs/data/broker_question_catalog_v1.json"),
        "forms": load_json("docs/data/form_wizards_2026.json"),
        "manufacturing": load_json("recruitment/MANUFACTURING_LAUNCH_CHECK.json"),
    }


def self_test() -> None:
    base = (ROOT / DOCUMENT).read_text(encoding="utf-8")
    data = inputs()
    assert not problems(base, **data), problems(base, **data)
    cases = [
        (base.replace("**308**", "**304**", 1), data),
        (base.replace("**83/84 fetched**", "**72/72 fetched**", 1), data),
        (base.replace("**review_required**", "**clean**", 1), data),
        (base.replace("**1**", "**5**", 1), data),
        (base.replace("**hold**", "**open**", 1), data),
    ]
    changed = deepcopy(data)
    changed["answers"]["answers"].pop()
    cases.append((base, changed))
    changed = deepcopy(data)
    changed["source"]["state"] = "clean"
    cases.append((base, changed))
    changed = deepcopy(data)
    changed["manufacturing"]["heldQuestions"].append("job_scan")
    cases.append((base, changed))
    for bad_doc, bad_data in cases:
        assert problems(bad_doc, **bad_data), "stale or contradictory operator snapshot passed"
    print("BETA_OPEN_READINESS_DOC_SELF_TEST_PASS 8 stale_snapshot_fail_closed_cases")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return
    errors = problems((ROOT / DOCUMENT).read_text(encoding="utf-8"), **inputs())
    if errors:
        print("BETA_OPEN_READINESS_DOC_FAIL")
        for item in errors:
            print("-", item)
        raise SystemExit(1)
    print("BETA_OPEN_READINESS_DOC_PASS current_snapshot_consistent; no_release_authorization")


if __name__ == "__main__":
    main()
