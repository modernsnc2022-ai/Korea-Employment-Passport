#!/usr/bin/env python3
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/"docs"/"data"
route=json.loads((DATA/"id_e9_manufacturing_2026.json").read_text(encoding="utf-8"))
questions=json.loads((DATA/"broker_question_catalog_v1.json").read_text(encoding="utf-8"))["questions"]
answers=json.loads((DATA/"exact_answer_rules_v1.json").read_text(encoding="utf-8"))["answers"]
wizards=json.loads((DATA/"form_wizards_2026.json").read_text(encoding="utf-8"))["forms"]

def scopes_for_stage(stage):
    out=set()
    for row in answers:
        if stage in row.get("stages",[]) and row.get("scopeType")=="cohort" and row.get("scopeKey"):
            out.add(row["scopeKey"])
    for form in wizards:
        if stage not in form.get("stages",[]):
            continue
        out.update(x for x in (form.get("scopeKeys") or []) if x)
        if form.get("scopeKey"):
            out.add(form["scopeKey"])
    for row in questions:
        if row.get("stageId")!=stage:
            continue
        out.update(x for x in (row.get("scopeKeys") or []) if x)
        if row.get("scopeKey"):
            out.add(row["scopeKey"])
    return sorted(out)

def exact_ids(stage,scope):
    out=set()
    for row in answers:
        if stage not in row.get("stages",[]):
            continue
        if row.get("scopeType")=="cohort" and row.get("scopeKey")!=scope:
            continue
        out.add(row["id"])
    return out

def wizard_refs(stage,scope):
    out=set()
    for form in wizards:
        if stage not in form.get("stages",[]):
            continue
        keys=form.get("scopeKeys") or ([form.get("scopeKey")] if form.get("scopeKey") else [])
        keys=[x for x in keys if x]
        if keys and scope not in keys:
            continue
        for field in form.get("fields",[]):
            out.add(f"{form['id']}:{field['id']}")
    return out

def question_applies(row,scope):
    keys=row.get("scopeKeys") or []
    if keys:
        return scope in keys
    if row.get("scopeKey"):
        return row["scopeKey"]==scope
    return True

def resolved(row,answer_ids,field_refs):
    candidates=[row.get("answerId"),*(row.get("answerIds") or [])]
    by_answer=any(x and x in answer_ids for x in candidates)
    refs=[x for x in [row.get("wizardRef"),*(row.get("wizardRefs") or [])] if x]
    by_wizard=bool(refs) and all(x in field_refs for x in refs)
    return by_answer or by_wizard

failures=[]
scenario_count=0
for stage in [x["id"] for x in route["stages"]]:
    scopes=scopes_for_stage(stage)
    scenarios=scopes if scopes else [""]
    for scope in scenarios:
        scenario_count+=1
        answer_ids=exact_ids(stage,scope)
        field_refs=wizard_refs(stage,scope)
        blockers=[]
        for row in questions:
            if row.get("stageId")!=stage or not question_applies(row,scope):
                continue
            if row.get("severity")=="high" and row.get("blocksZeroBrokerReady") and not resolved(row,answer_ids,field_refs):
                blockers.append(row["id"])
        if blockers:
            failures.append((stage,scope or "NO_SCOPE",blockers))

print(f"BQC_SCOPE_SCENARIOS={scenario_count}")
if failures:
    print(f"BQC_SCOPE_FAIL scenarios={len(failures)}")
    for stage,scope,blockers in failures:
        print(f"- {stage} / {scope}: {', '.join(blockers)}")
    raise SystemExit(1)
print("BQC_SCOPE_PASS all supported selected-call scenarios have zero unresolved high-severity blockers")
