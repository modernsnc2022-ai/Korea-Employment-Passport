#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.request
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BASELINE = ROOT / "monitor" / "np_current_cohort_notice_baseline.json"
DEFAULT_OUTPUT = ROOT / "monitor" / "np_current_cohort_notice_result.json"

HEADERS = {
    "User-Agent": "Korea-Employment-Passport-Nepal-Notice-Watch/1.0 (+GitHub Actions)",
    "Accept-Language": "ne,en;q=0.8,ko;q=0.5",
}

def norm(value: str) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()

class LinkParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.current_href = None
        self.current_parts = []
        self.links = []

    def handle_starttag(self, tag, attrs):
        if tag.lower() == "a":
            self.current_href = dict(attrs).get("href")
            self.current_parts = []

    def handle_data(self, data):
        if self.current_href is not None:
            text = norm(data)
            if text:
                self.current_parts.append(text)

    def handle_endtag(self, tag):
        if tag.lower() == "a" and self.current_href is not None:
            self.links.append((self.current_href, norm(" ".join(self.current_parts))))
            self.current_href = None
            self.current_parts = []

def extract_posts(html: str, base_url: str) -> dict[int, dict]:
    parser = LinkParser()
    parser.feed(html)
    posts = {}
    for href, title in parser.links:
        if not href:
            continue
        match = re.search(r"/postdetails/(\d+)", href)
        if not match:
            continue
        post_id = int(match.group(1))
        if not title:
            continue
        posts[post_id] = {
            "id": post_id,
            "title": title,
            "url": urljoin(base_url, href),
        }
    return posts

def is_candidate(title: str, keywords: list[str]) -> bool:
    folded = title.casefold()
    return any(str(keyword).casefold() in folded for keyword in keywords)

def compare(posts: dict[int, dict], baseline: dict) -> dict:
    min_id = int(baseline.get("minPostId", 0))
    keywords = [str(x) for x in baseline.get("keywords", [])]
    known_rows = baseline.get("known", [])
    known = {int(row["id"]): norm(row.get("title", "")) for row in known_rows}

    matched = [
        row for post_id, row in sorted(posts.items())
        if post_id >= min_id and is_candidate(row["title"], keywords)
    ]
    new_candidates = [row for row in matched if row["id"] not in known]
    title_changes = []
    for row in matched:
        expected = known.get(row["id"])
        if expected and norm(row["title"]) != expected:
            title_changes.append({
                "id": row["id"],
                "url": row["url"],
                "before": expected,
                "after": norm(row["title"]),
            })
    return {
        "matchedCandidates": matched,
        "newCandidates": new_candidates,
        "knownTitleChanges": title_changes,
    }

def fetch(url: str) -> str:
    request = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(request, timeout=20) as response:
        charset = response.headers.get_content_charset() or "utf-8"
        return response.read().decode(charset, errors="replace")

def self_test() -> int:
    baseline = {
        "minPostId": 136,
        "keywords": ["भाषा परीक्षा", "Skill", "राहदानी", "अनलाईन दरखास्त"],
        "known": [
            {"id": 136, "title": "सन् २०२६ भाषा परीक्षा"},
            {"id": 139, "title": "अनलाईन दरखास्त प्रणाली पुन: सुचारु"},
        ],
    }
    clean_html = """
    <a href="/postdetails/136">सन् २०२६ भाषा परीक्षा</a>
    <a href="/postdetails/139">अनलाईन दरखास्त प्रणाली पुन: सुचारु</a>
    <a href="/postdetails/150">कोरिया जाने कामदारहरुको सूचना</a>
    """
    result = compare(extract_posts(clean_html, "https://epsnepal.gov.np/notices"), baseline)
    assert not result["newCandidates"]
    assert not result["knownTitleChanges"]

    changed_html = clean_html + '<a href="/postdetails/151">Skill & Competency Test सम्बन्धी सूचना</a>'
    result = compare(extract_posts(changed_html, "https://epsnepal.gov.np/notices"), baseline)
    assert [row["id"] for row in result["newCandidates"]] == [151]

    renamed_html = clean_html.replace("सन् २०२६ भाषा परीक्षा", "सन् २०२६ भाषा परीक्षा संशोधित")
    result = compare(extract_posts(renamed_html, "https://epsnepal.gov.np/notices"), baseline)
    assert [row["id"] for row in result["knownTitleChanges"]] == [136]

    print("NEPAL_CURRENT_COHORT_NOTICE_WATCH_SELF_TEST_PASS")
    return 0

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--baseline", default=str(DEFAULT_BASELINE))
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT))
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    if args.self_test:
        return self_test()

    baseline_path = Path(args.baseline)
    baseline = json.loads(baseline_path.read_text(encoding="utf-8-sig"))
    index_url = baseline["officialNoticeIndex"]

    try:
        html = fetch(index_url)
        posts = extract_posts(html, index_url)
        comparison = compare(posts, baseline)
        error = None
    except Exception as exc:
        comparison = {
            "matchedCandidates": [],
            "newCandidates": [],
            "knownTitleChanges": [],
        }
        error = str(exc)

    review_required = bool(
        error
        or comparison["newCandidates"]
        or comparison["knownTitleChanges"]
    )
    result = {
        "routeId": baseline.get("routeId"),
        "checkedAt": datetime.now(timezone.utc).isoformat(),
        "officialNoticeIndex": index_url,
        "state": "review_required" if review_required else "clean",
        "fetchError": error,
        **comparison,
        "message": (
            "Nepal current-cohort notice change requires manual review; no route rule was auto-promoted."
            if review_required else
            "No new matching Nepal current-cohort notice was detected."
        ),
    }
    Path(args.output).write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(result, ensure_ascii=False))

    if error:
        return 2
    if comparison["newCandidates"] or comparison["knownTitleChanges"]:
        return 1
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
