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

errors = []

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
for pack in document_packs.get("packs", []):
    pack_ids.append(pack.get("id", ""))
    if not str(pack.get("sourceUrl", "")).startswith("http"):
        bad_pack_sources.append(pack.get("id", "<missing>"))
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

exact_ids = []
bad_exact_stage_refs = []
bad_exact_sources = []
bad_exact_content = []
for item in exact_answers.get("answers", []):
    item_id = item.get("id", "")
    exact_ids.append(item_id)
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

sample_ids = []
bad_sample_stage_refs = []
bad_sample_sources = []
bad_sample_content = []
for sample in document_examples.get("samples", []):
    sample_id = sample.get("id", "")
    sample_ids.append(sample_id)
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
    f"js_literal_refs={len(literal_refs)}",
)
