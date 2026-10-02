#!/usr/bin/env python3
import json
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
html = (ROOT / "docs" / "app.html").read_text(encoding="utf-8")
js = (ROOT / "docs" / "app-runtime.js").read_text(encoding="utf-8")
route = json.loads((ROOT / "docs" / "data" / "id_e9_manufacturing_2026.json").read_text(encoding="utf-8"))
i18n = json.loads((ROOT / "docs" / "data" / "id_e9_manufacturing_2026_id.json").read_text(encoding="utf-8"))
document_packs = json.loads((ROOT / "docs" / "data" / "document_packs_2026.json").read_text(encoding="utf-8"))
exact_answers = json.loads((ROOT / "docs" / "data" / "exact_answer_rules_v1.json").read_text(encoding="utf-8"))
document_examples = json.loads((ROOT / "docs" / "data" / "document_examples_v1.json").read_text(encoding="utf-8"))
broker_questions = json.loads((ROOT / "docs" / "data" / "broker_question_catalog_v1.json").read_text(encoding="utf-8"))
form_wizards = json.loads((ROOT / "docs" / "data" / "form_wizards_2026.json").read_text(encoding="utf-8"))

errors = []

# Keep the default user journey simple even as the internal rules grow.
if 'class="how-to-use"' not in html:
    errors.append("simple UX lock missing 3-step usage strip")
if '<details id="contextTools"' not in html:
    errors.append("simple UX lock requires contextual tools collapsed by default")
if '<details class="trust-panel"' not in html:
    errors.append("simple UX lock requires technical trust details collapsed")
if 'id="formWizardCard"' not in html:
    errors.append("simple UX lock requires one-field-at-a-time form wizard")
if "cohort" in html.lower():
    errors.append("user-facing HTML contains internal jargon: cohort")

ids = re.findall(r'\bid="([^"]+)"', html)
dupes = [key for key, count in Counter(ids).items() if count > 1]
if dupes:
    errors.append("duplicate HTML ids: " + ", ".join(sorted(dupes)))

id_set = set(ids)
literal_refs = set(re.findall(r"\$\(['\"]([A-Za-z0-9_-]+)['\"]\)", js))
missing_refs = sorted(literal_refs - id_set)
if missing_refs:
    errors.append("JS references missing HTML ids: " + ", ".join(missing_refs))

view_ids = set(re.findall(r'<section\s+id="([^"]+)"\s+class="view(?:\s+active)?"', html))
nav_targets = set(re.findall(r'data-view="([^"]+)"', html))
missing_views = sorted(nav_targets - view_ids)
if missing_views:
    errors.append("navigation targets missing views: " + ", ".join(missing_views))

stage_ids = [stage["id"] for stage in route.get("stages", [])]
stage_dupes = [key for key, count in Counter(stage_ids).items() if count > 1]
if stage_dupes:
    errors.append("duplicate route stage ids: " + ", ".join(stage_dupes))

missing_i18n = sorted(set(stage_ids) - set(i18n))
if missing_i18n:
    errors.append("stages missing Indonesian copy: " + ", ".join(missing_i18n))

bad_sources = [
    stage["id"] for stage in route.get("stages", [])
    if not str(stage.get("sourceUrl", "")).startswith("http")
]
if bad_sources:
    errors.append("stages missing official/source URL: " + ", ".join(bad_sources))

bad_action_urls = [
    stage["id"] for stage in route.get("stages", [])
    if stage.get("officialActionUrl") and not str(stage["officialActionUrl"]).startswith("http")
]
if bad_action_urls:
    errors.append("invalid official action URL: " + ", ".join(bad_action_urls))

missing_action_labels = [
    stage["id"] for stage in route.get("stages", [])
    if stage.get("officialActionUrl") and not stage.get("officialActionLabel")
]
if missing_action_labels:
    errors.append("official action URL missing label: " + ", ".join(missing_action_labels))

known_stage_ids = set(stage_ids)
pack_ids = []
item_ids = []
bad_pack_stage_refs = []
bad_pack_sources = []
bad_pack_scope = []
for pack in document_packs.get("packs", []):
    pack_ids.append(pack.get("id", ""))
    if not str(pack.get("sourceUrl", "")).startswith("http"):
        bad_pack_sources.append(pack.get("id", "<missing>"))
    if pack.get("scopeType") == "cohort" and (not pack.get("scopeKey") or not pack.get("scopeLabel")):
        bad_pack_scope.append(pack.get("id", "<missing>"))
    for stage_id in pack.get("appliesTo", []):
        if stage_id not in known_stage_ids:
            bad_pack_stage_refs.append(f"{pack.get('id')}->{stage_id}")
    for item in pack.get("items", []):
        item_ids.append(item.get("id", ""))

pack_dupes = [key for key, count in Counter(pack_ids).items() if key and count > 1]
if pack_dupes:
    errors.append("duplicate document pack ids: " + ", ".join(sorted(pack_dupes)))

item_dupes = [key for key, count in Counter(item_ids).items() if key and count > 1]
if item_dupes:
    errors.append("duplicate document item ids: " + ", ".join(sorted(item_dupes)))

if bad_pack_stage_refs:
    errors.append("document packs reference unknown stages: " + ", ".join(sorted(bad_pack_stage_refs)))

if bad_pack_sources:
    errors.append("document packs missing source URL: " + ", ".join(sorted(bad_pack_sources)))

if bad_pack_scope:
    errors.append("cohort document packs missing scope metadata: " + ", ".join(sorted(bad_pack_scope)))

exact_ids = []
bad_exact_stage_refs = []
bad_exact_sources = []
bad_exact_content = []
bad_exact_scope = []
allowed_scope_types = {"route_2026", "current_rule", "cohort"}
for item in exact_answers.get("answers", []):
    item_id = item.get("id", "")
    exact_ids.append(item_id)
    scope_type = item.get("scopeType")
    if scope_type not in allowed_scope_types:
        bad_exact_scope.append(f"{item_id}:scopeType")
    if scope_type == "cohort" and (not item.get("scopeKey") or not item.get("scopeLabel")):
        bad_exact_scope.append(f"{item_id}:cohort_metadata")
    for stage_id in item.get("stages", []):
        if stage_id not in known_stage_ids:
            bad_exact_stage_refs.append(f"{item_id}->{stage_id}")
    if not str(item.get("sourceUrl", "")).startswith("http"):
        bad_exact_sources.append(item_id or "<missing>")
    for required in ("question", "answer", "writeExactly", "why", "verifiedAt", "verificationStatus"):
        if not str(item.get(required, "")).strip():
            bad_exact_content.append(f"{item_id}:{required}")

exact_dupes = [key for key, count in Counter(exact_ids).items() if key and count > 1]
if exact_dupes:
    errors.append("duplicate exact-answer ids: " + ", ".join(sorted(exact_dupes)))

if bad_exact_stage_refs:
    errors.append("exact answers reference unknown stages: " + ", ".join(sorted(bad_exact_stage_refs)))

if bad_exact_sources:
    errors.append("exact answers missing source URL: " + ", ".join(sorted(bad_exact_sources)))

if bad_exact_content:
    errors.append("exact answers missing required content: " + ", ".join(sorted(bad_exact_content)))

if bad_exact_scope:
    errors.append("exact answers missing/invalid scope metadata: " + ", ".join(sorted(bad_exact_scope)))

sample_ids = []
bad_sample_stage_refs = []
bad_sample_sources = []
bad_sample_content = []
bad_sample_scope = []
for sample in document_examples.get("samples", []):
    sample_id = sample.get("id", "")
    sample_ids.append(sample_id)
    if sample.get("scopeType") == "cohort" and (not sample.get("scopeKey") or not sample.get("scopeLabel")):
        bad_sample_scope.append(sample_id or "<missing>")
    for stage_id in sample.get("stages", []):
        if stage_id not in known_stage_ids:
            bad_sample_stage_refs.append(f"{sample_id}->{stage_id}")
    if not str(sample.get("sourceUrl", "")).startswith("http"):
        bad_sample_sources.append(sample_id or "<missing>")
    if not str(sample.get("title", "")).strip():
        bad_sample_content.append(f"{sample_id}:title")
    if not sample.get("rows"):
        bad_sample_content.append(f"{sample_id}:rows")
    for file in sample.get("officialFiles", []):
        if not str(file.get("url", "")).startswith("http"):
            bad_sample_content.append(f"{sample_id}:officialFiles.url")
        if not str(file.get("label", "")).strip():
            bad_sample_content.append(f"{sample_id}:officialFiles.label")

sample_dupes = [key for key, count in Counter(sample_ids).items() if key and count > 1]
if sample_dupes:
    errors.append("duplicate document example ids: " + ", ".join(sorted(sample_dupes)))

if bad_sample_stage_refs:
    errors.append("document examples reference unknown stages: " + ", ".join(sorted(bad_sample_stage_refs)))

if bad_sample_sources:
    errors.append("document examples missing source URL: " + ", ".join(sorted(bad_sample_sources)))

if bad_sample_content:
    errors.append("document examples missing required content: " + ", ".join(sorted(bad_sample_content)))

if bad_sample_scope:
    errors.append("cohort document examples missing scope metadata: " + ", ".join(sorted(bad_sample_scope)))

wizard_ref_set = {
    f"{form.get('id')}:{field.get('id')}"
    for form in form_wizards.get("forms", [])
    for field in form.get("fields", [])
}
question_ids = []
bad_question_stage_refs = []
bad_question_answer_refs = []
bad_question_wizard_refs = []
bad_question_content = []
exact_id_set = set(exact_ids)
for question in broker_questions.get("questions", []):
    question_id = question.get("id", "")
    question_ids.append(question_id)
    stage_id = question.get("stageId")
    if stage_id not in known_stage_ids:
        bad_question_stage_refs.append(f"{question_id}->{stage_id}")
    answer_id = question.get("answerId")
    if answer_id and answer_id not in exact_id_set:
        bad_question_answer_refs.append(f"{question_id}->{answer_id}")
    for answer_ref in question.get("answerIds", []):
        if answer_ref not in exact_id_set:
            bad_question_answer_refs.append(f"{question_id}->{answer_ref}")
    wizard_ref = question.get("wizardRef")
    if wizard_ref and wizard_ref not in wizard_ref_set:
        bad_question_wizard_refs.append(f"{question_id}->{wizard_ref}")
    for required in ("question", "severity", "category"):
        if not str(question.get(required, "")).strip():
            bad_question_content.append(f"{question_id}:{required}")
    if question.get("severity") not in {"high", "medium", "low"}:
        bad_question_content.append(f"{question_id}:severity_invalid")
    if question.get("severity") == "high" and not question.get("blocksZeroBrokerReady", False):
        bad_question_content.append(f"{question_id}:high_not_blocking")

question_dupes = [key for key, count in Counter(question_ids).items() if key and count > 1]
if question_dupes:
    errors.append("duplicate broker-question ids: " + ", ".join(sorted(question_dupes)))

if bad_question_stage_refs:
    errors.append("broker questions reference unknown stages: " + ", ".join(sorted(bad_question_stage_refs)))

if bad_question_answer_refs:
    errors.append("broker questions reference missing exact answers: " + ", ".join(sorted(bad_question_answer_refs)))

if bad_question_wizard_refs:
    errors.append("broker questions reference missing form-wizard fields: " + ", ".join(sorted(bad_question_wizard_refs)))

if bad_question_content:
    errors.append("broker questions missing/invalid required content: " + ", ".join(sorted(bad_question_content)))

form_ids = []
wizard_field_ids = []
bad_form_stage_refs = []
bad_form_sources = []
bad_form_content = []
for form in form_wizards.get("forms", []):
    form_id = form.get("id", "")
    form_ids.append(form_id)
    if not str(form.get("sourceUrl", "")).startswith("http"):
        bad_form_sources.append(f"{form_id}:sourceUrl")
    if not str(form.get("guidanceUrl", "")).startswith("http"):
        bad_form_sources.append(f"{form_id}:guidanceUrl")
    for stage_id in form.get("stages", []):
        if stage_id not in known_stage_ids:
            bad_form_stage_refs.append(f"{form_id}->{stage_id}")
    if not str(form.get("title", "")).strip():
        bad_form_content.append(f"{form_id}:title")
    if not form.get("fields"):
        bad_form_content.append(f"{form_id}:fields")
    for field in form.get("fields", []):
        field_id = field.get("id", "")
        wizard_field_ids.append(f"{form_id}:{field_id}")
        for required in ("id", "label", "instruction", "example"):
            if not str(field.get(required, "")).strip():
                bad_form_content.append(f"{form_id}:{field_id}:{required}")

form_dupes = [key for key, count in Counter(form_ids).items() if key and count > 1]
if form_dupes:
    errors.append("duplicate form-wizard ids: " + ", ".join(sorted(form_dupes)))

field_dupes = [key for key, count in Counter(wizard_field_ids).items() if key and count > 1]
if field_dupes:
    errors.append("duplicate form-wizard field ids: " + ", ".join(sorted(field_dupes)))

if bad_form_stage_refs:
    errors.append("form wizards reference unknown stages: " + ", ".join(sorted(bad_form_stage_refs)))

if bad_form_sources:
    errors.append("form wizards missing official URLs: " + ", ".join(sorted(bad_form_sources)))

if bad_form_content:
    errors.append("form wizards missing required content: " + ", ".join(sorted(bad_form_content)))

if errors:
    print("WEBAPP_CONTRACT_FAIL")
    for error in errors:
        print("- " + error)
    sys.exit(1)

print(
    "WEBAPP_CONTRACT_PASS",
    f"html_ids={len(ids)}",
    f"views={len(view_ids)}",
    f"stages={len(stage_ids)}",
    f"document_packs={len(document_packs.get('packs', []))}",
    f"exact_answers={len(exact_answers.get('answers', []))}",
    f"document_examples={len(document_examples.get('samples', []))}",
    f"broker_questions={len(broker_questions.get('questions', []))}",
    f"form_wizards={len(form_wizards.get('forms', []))}",
    f"form_fields={sum(len(form.get('fields', [])) for form in form_wizards.get('forms', []))}",
    f"js_literal_refs={len(literal_refs)}",
)
