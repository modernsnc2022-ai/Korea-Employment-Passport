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
    f"js_literal_refs={len(literal_refs)}",
)
