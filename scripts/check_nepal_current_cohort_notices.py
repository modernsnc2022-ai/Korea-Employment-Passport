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
    "User-Agent": "Korea-Employment-Passport-Nepal-Notice-Watch/1.1 (+GitHub Actions)",
    "Accept-Language": "ne,en;q=0.8,ko;q=0.5",
}

GENERIC_LINK_TEXT = {
    "",
    "read more",
    "more",
    "details",
    "view",
    "view details",
    "सम्पूर्ण विवरण",
}

DATE_PATTERNS = [
    re.compile(
        r"^(?:jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|"
        r"jul(?:y)?|aug(?:ust)?|sep(?:tember)?|oct(?:ober)?|nov(?:ember)?|"
        r"dec(?:ember)?)\s+\d{1,2},?\s+20\d{2}$",
        re.I,
    ),
    re.compile(r"^\d{1,2}[-/.]\d{1,2}[-/.]20\d{2}$"),
    re.compile(r"^20\d{2}[-/.]\d{1,2}[-/.]\d{1,2}$"),
]


def norm(value: str) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def title_key(value: str) -> str:
    return norm(value).casefold()


def looks_like_date(value: str) -> bool:
    text = norm(value)
    return any(pattern.match(text) for pattern in DATE_PATTERNS)


def usable_context_title(value: str) -> bool:
    text = norm(value)
    if not text:
        return False
    if title_key(text) in GENERIC_LINK_TEXT:
        return False
    if looks_like_date(text):
        return False
    if re.fullmatch(r"[\d\s:./-]+", text):
        return False
    return len(text) >= 4


def context_title(parts: list[str]) -> str:
    for value in reversed(parts[-16:]):
        if usable_context_title(value):
            return norm(value)
    return ""


class LinkParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.current_href = None
        self.current_parts: list[str] = []
        self.context_before: list[str] = []
        self.recent_text: list[str] = []
        self.links: list[tuple[str | None, str, str]] = []

    def _remember(self, value: str) -> None:
        text = norm(value)
        if not text:
            return
        self.recent_text.append(text)
        if len(self.recent_text) > 40:
            self.recent_text = self.recent_text[-40:]

    def handle_starttag(self, tag, attrs):
        if tag.lower() == "a":
            self.current_href = dict(attrs).get("href")
            self.current_parts = []
            self.context_before = list(self.recent_text)

    def handle_data(self, data):
        text = norm(data)
        if not text:
            return
        if self.current_href is not None:
            self.current_parts.append(text)
        else:
            self._remember(text)

    def handle_endtag(self, tag):
        if tag.lower() != "a" or self.current_href is None:
            return
        anchor_text = norm(" ".join(self.current_parts))
        nearby_title = context_title(self.context_before)
        self.links.append((self.current_href, anchor_text, nearby_title))
        # Remember non-generic anchor text so later "Read more" links can use it as context.
        if anchor_text and title_key(anchor_text) not in GENERIC_LINK_TEXT:
            self._remember(anchor_text)
        self.current_href = None
        self.current_parts = []
        self.context_before = []


def extract_posts(html: str, base_url: str) -> dict[int, dict]:
    parser = LinkParser()
    parser.feed(html)
    posts: dict[int, dict] = {}
    for href, anchor_text, nearby_title in parser.links:
        if not href:
            continue
        match = re.search(r"/postdetails/(\d+)", href)
        if not match:
            continue
        post_id = int(match.group(1))
        anchor_key = title_key(anchor_text)
        title = (
            nearby_title
            if anchor_key in GENERIC_LINK_TEXT
            else norm(anchor_text)
        )
        if not title:
            continue
        row = {
            "id": post_id,
            "title": title,
            "url": urljoin(base_url, href),
        }
        existing = posts.get(post_id)
        if existing is None:
            posts[post_id] = row
            continue
        # Prefer a more descriptive title when the same post appears on multiple surfaces.
        if len(title) > len(str(existing.get("title", ""))):
            posts[post_id] = row
    return posts


def is_candidate(title: str, keywords: list[str]) -> bool:
    folded = title_key(title)
    return any(title_key(keyword) in folded for keyword in keywords)


def compare(posts: dict[int, dict], baseline: dict) -> dict:
    min_id = int(baseline.get("minPostId", 0))
    keywords = [str(x) for x in baseline.get("keywords", [])]
    known_rows = baseline.get("known", [])

    known_titles: dict[str, dict] = {}
    expected_by_id: dict[int, str] = {}
    declared_ids_by_title: dict[str, set[int]] = {}
    for row in known_rows:
        key = title_key(row.get("title", ""))
        if not key:
            continue
        known_titles[key] = row
        ids = {int(row["id"])}
        ids.update(int(x) for x in row.get("aliasPostIds", []) if x is not None)
        declared_ids_by_title[key] = ids
        for post_id in ids:
            expected_by_id[post_id] = key

    matched = [
        row for post_id, row in sorted(posts.items())
        if post_id >= min_id and is_candidate(row["title"], keywords)
    ]

    new_candidates = [
        row for row in matched
        if title_key(row["title"]) not in known_titles
    ]

    observed_aliases = []
    for row in matched:
        key = title_key(row["title"])
        if key not in known_titles:
            continue
        declared = declared_ids_by_title.get(key, set())
        if row["id"] not in declared:
            observed_aliases.append({
                "id": row["id"],
                "title": row["title"],
                "url": row["url"],
                "knownPrimaryId": int(known_titles[key]["id"]),
                "reason": "same_normalized_title_new_post_id",
            })

    # A title change is only actionable when a known primary/alias ID itself now
    # exposes a different route-relevant title that is not already a known title.
    title_changes = []
    for row in matched:
        expected_key = expected_by_id.get(row["id"])
        actual_key = title_key(row["title"])
        if (
            expected_key
            and actual_key != expected_key
            and actual_key not in known_titles
        ):
            title_changes.append({
                "id": row["id"],
                "url": row["url"],
                "before": known_titles[expected_key]["title"],
                "after": norm(row["title"]),
            })

    return {
        "matchedCandidates": matched,
        "newCandidates": new_candidates,
        "knownTitleChanges": title_changes,
        "observedAliases": observed_aliases,
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
            {
                "id": 139,
                "title": "अनलाईन दरखास्त प्रणाली पुन: सुचारु",
                "aliasPostIds": [141],
            },
        ],
    }

    clean_html = """
    <a href="/postdetails/136">सन् २०२६ भाषा परीक्षा</a>
    <a href="/postdetails/139">अनलाईन दरखास्त प्रणाली पुन: सुचारु</a>
    <a href="/postdetails/141">अनलाईन दरखास्त प्रणाली पुन: सुचारु</a>
    <a href="/postdetails/150">कोरिया जाने कामदारहरुको सूचना</a>
    """
    result = compare(
        extract_posts(clean_html, "https://epsnepal.gov.np/notices"),
        baseline,
    )
    assert not result["newCandidates"]
    assert not result["knownTitleChanges"]

    # Same known title under an undeclared duplicate post ID is informational only.
    alias_html = clean_html + (
        '<a href="/postdetails/142">'
        'अनलाईन दरखास्त प्रणाली पुन: सुचारु'
        '</a>'
    )
    result = compare(
        extract_posts(alias_html, "https://epsnepal.gov.np/notices"),
        baseline,
    )
    assert not result["newCandidates"]
    assert [row["id"] for row in result["observedAliases"]] == [142]

    # Notice-list cards often put the actual title before a generic "Read more" link.
    read_more_html = """
    <div class="notice-card">
      <h4>Skill & Competency Test सम्बन्धी सूचना</h4>
      <div>October 5, 2026</div>
      <a href="/postdetails/151">Read more</a>
    </div>
    """
    posts = extract_posts(read_more_html, "https://epsnepal.gov.np/notices")
    assert posts[151]["title"] == "Skill & Competency Test सम्बन्धी सूचना"
    result = compare(posts, baseline)
    assert [row["id"] for row in result["newCandidates"]] == [151]

    # A genuinely changed title on a known ID remains review-required.
    renamed_html = """
    <a href="/postdetails/136">सन् २०२६ भाषा परीक्षा संशोधित</a>
    """
    result = compare(
        extract_posts(renamed_html, "https://epsnepal.gov.np/notices"),
        baseline,
    )
    assert [row["id"] for row in result["knownTitleChanges"]] == [136]
    assert [row["id"] for row in result["newCandidates"]] == [136]

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
            "observedAliases": [],
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
        "identityStrategy": "normalized_title",
        "state": "review_required" if review_required else "clean",
        "fetchError": error,
        **comparison,
        "message": (
            "Nepal current-cohort notice change requires manual review; no route rule was auto-promoted."
            if review_required else
            "No new matching Nepal current-cohort notice title was detected."
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
