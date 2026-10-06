#!/usr/bin/env python3
"""Diagnose text-level volatility for selected changed official sources.

This is diagnostics only. It never updates route data or source baselines.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import time
from difflib import SequenceMatcher
from pathlib import Path

from check_official_sources import (
    TextExtractor,
    _fetch_response,
    normalize_source_text,
)

ROOT = Path(__file__).resolve().parents[1]


def normalized_text(url: str, tls_pins: dict) -> tuple[str, str]:
    raw, _content_type, charset, final_url, _tls_mode = _fetch_response(url, tls_pins)
    html = raw.decode(charset, errors="replace")
    extractor = TextExtractor()
    extractor.feed(html)
    text = normalize_source_text(" ".join(extractor.parts), final_url)
    return text, hashlib.sha256(text.encode("utf-8")).hexdigest()


def clip(text: str, limit: int = 220) -> str:
    text = " ".join(text.split())
    return text if len(text) <= limit else text[:limit] + "…"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--ids",
        default="mm_mol_eps_opportunity,mm_mol_dol_index,vn_colab_eps_notices",
        help="Comma-separated source IDs to diagnose if currently review-required.",
    )
    parser.add_argument("--delay", type=float, default=1.5)
    args = parser.parse_args()

    sources = json.loads((ROOT / "monitor/sources.json").read_text(encoding="utf-8-sig"))["sources"]
    by_id = {row["id"]: row for row in sources}
    status = json.loads((ROOT / "docs/data/source_review_status.json").read_text(encoding="utf-8-sig"))
    tls_path = ROOT / "monitor/tls_pins.json"
    tls_pins = json.loads(tls_path.read_text(encoding="utf-8-sig")) if tls_path.exists() else {"hosts": {}}

    required = set(status.get("reviewRequiredSourceIds", []))
    wanted = [x.strip() for x in args.ids.split(",") if x.strip()]
    targets = [source_id for source_id in wanted if source_id in required and source_id in by_id]

    print(f"SOURCE_TEXT_DIAGNOSTIC targets={len(targets)}")
    for source_id in targets:
        source = by_id[source_id]
        first, first_hash = normalized_text(source["url"], tls_pins)
        time.sleep(max(0.0, args.delay))
        second, second_hash = normalized_text(source["url"], tls_pins)
        stable = first_hash == second_hash
        print(
            "SOURCE_TEXT_STATE "
            f"id={source_id} stable={str(stable).lower()} "
            f"first_sha={first_hash} second_sha={second_hash} "
            f"first_len={len(first)} second_len={len(second)}"
        )
        if stable:
            continue

        first_words = first.split()
        second_words = second.split()
        matcher = SequenceMatcher(a=first_words, b=second_words, autojunk=False)
        emitted = 0
        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == "equal":
                continue
            before = clip(" ".join(first_words[max(0, i1 - 8):min(len(first_words), i2 + 8)]))
            after = clip(" ".join(second_words[max(0, j1 - 8):min(len(second_words), j2 + 8)]))
            print(
                "SOURCE_TEXT_DIFF "
                f"id={source_id} tag={tag} "
                f"before={json.dumps(before, ensure_ascii=False)} "
                f"after={json.dumps(after, ensure_ascii=False)}"
            )
            emitted += 1
            if emitted >= 8:
                break

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
