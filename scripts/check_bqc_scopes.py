#!/usr/bin/env python3
import argparse
import json
from collections import Counter
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/"docs"/"data"
route=json.loads((DATA/"id_e9_manufacturing_2026.json").read_text(encoding="utf-8"))
questions=json.loads((DATA/"broker_question_catalog_v1.json").read_text(encoding="utf-8"))["questions"]
answers=json.loads((DATA/"exact_answer_rules_v1.json").read_text(encoding="utf-8"))["answers"]
wizards=json.loads((DATA/"form_wizards_2026.json").read_text(encoding="utf-8"))["forms"]

p=argparse.ArgumentParser()
p.add_argument("--report-all",action="store_true",help="Print all unresolved questions, including medium/low, without changing the high-severity CI gate.")
args=p.parse_args()

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
        if not str(form.get("verificationStatus","")).startswith("verified_"):
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
all_unresolved=[]
scenario_count=0
for stage in [x["id"] for x in route["stages"]]:
    scopes=scopes_for_stage(stage)
    scenarios=scopes if scopes else [""]
    for scope in scenarios:
        scenario_count+=1
        answer_ids=exact_ids(stage,scope)
        field_refs=wizard_refs(stage,scope)
        blockers=[]
        unresolved=[]
        for row in questions:
            if row.get("stageId")!=stage or not question_applies(row,scope):
                continue
            if resolved(row,answer_ids,field_refs):
                continue
            unresolved.append(row)
            if row.get("severity")=="high" and row.get("blocksZeroBrokerReady"):
                blockers.append(row["id"])
        if blockers:
            failures.append((stage,scope or "NO_SCOPE",blockers))
        if unresolved:
            all_unresolved.append((stage,scope or "NO_SCOPE",unresolved))

print(f"BQC_SCOPE_SCENARIOS={scenario_count}")
if args.report_all:
    unique={}
    scenario_unresolved=0
    for stage,scope,rows in all_unresolved:
        scenario_unresolved+=len(rows)
        for row in rows:
            unique[row["id"]]=row
    counts=Counter(row.get("severity","unknown") for row in unique.values())
    print(
        "BQC_ALL_UNRESOLVED "
        f"unique={len(unique)} scenario_instances={scenario_unresolved} "
        f"high={counts.get('high',0)} medium={counts.get('medium',0)} low={counts.get('low',0)}"
    )
    by_stage=Counter(row.get("stageId","unknown") for row in unique.values())
    for stage,count in by_stage.most_common():
        print(f"  STAGE {stage}: {count}")
    for qid,row in sorted(unique.items(),key=lambda item:(item[1].get("stageId",""),item[1].get("severity",""),item[0])):
        print(f"  - [{row.get('severity','?')}] {row.get('stageId','?')} / {qid}: {row.get('question','')}")

if failures:
    print(f"BQC_SCOPE_FAIL scenarios={len(failures)}")
    for stage,scope,blockers in failures:
        print(f"- {stage} / {scope}: {', '.join(blockers)}")
    raise SystemExit(1)
print("BQC_SCOPE_PASS all supported selected-call scenarios have zero unresolved high-severity blockers")
