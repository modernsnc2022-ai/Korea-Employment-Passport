#!/usr/bin/env python3
"""Read-only 2026 KP2MI Pengumuman notice inventory; never authorizes beta OPEN.

Pages through the *actual* G-to-G Korea /pengumuman DataTables collection
until reaching the preceding year. No protected applicant data or attachments.
This audit lists candidate notices for a human reviewer; it cannot prove
that a notice's detailed contents or all 2026 rules have been verified.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import html
import json
from pathlib import Path
import re
from urllib.parse import urlencode, urlparse
from urllib.request import Request, urlopen

PAGE_URL = "https://kp2mi.go.id/gtog-korea/pengumuman"
FEED = "https://kp2mi.go.id/gtog-data/korea/Pengumuman"
PAGE_SIZE = 75
MONTHS = {
    "january": 1, "february": 2, "march": 3, "april": 4,
    "may": 5, "june": 6, "july": 7, "august": 8,
    "september": 9, "october": 10, "november": 11, "december": 12,
}
TAG = re.compile(r"<[^>]+>")
LINK = re.compile(r"""href\s*=\s*["']([^"']+)""", re.I)


def clean(value: object) -> str:
    return " ".join(html.unescape(TAG.sub(" ", str(value or ""))).split())


def date_iso(value: object) -> str:
    parts = re.fullmatch(r"\s*(\d{1,2})\s+([a-zA-Z]+)\s+(\d{4})\s*", str(value))
    if not parts or parts.group(2).lower() not in MONTHS:
        raise ValueError(f"Unrecognized official date: {value!r}")
    return datetime(int(parts.group(3)), MONTHS[parts.group(2).lower()],
                    int(parts.group(1))).date().isoformat()


def notice_from_row(row: dict) -> dict:
    title = clean(row.get("judul"))
    if not title:
        raise ValueError("Empty official announcement title")
    markup = str(row.get("judul") or "")
    link_match = LINK.search(markup)
    if not link_match:
        raise ValueError(f"No official announcement href for {title[:80]}")
    href = html.unescape(link_match.group(1))
    if href.startswith("/gtog-detail/korea/"):
        url = "https://kp2mi.go.id" + href
    elif href.startswith("https://"):
        parsed = urlparse(href)
        if parsed.hostname not in {"kp2mi.go.id", "www.kp2mi.go.id"}:
            raise ValueError("External announcement URL detected")
        url = href
    else:
        raise ValueError("Unrecognized/unsafe official announcement URL")
    date = date_iso(row.get("tanggal"))
    key = title.casefold()
    year = int(date[:4])
    kind = "other_official_notice"
    if year == 2026:
        if "root industry" in key or "root industri" in key:
            kind = "root_industry_not_general_manufacturing"
        elif ("perikanan" in key or "fisheries" in key) and "manufaktur" not in key:
            kind = "fisheries_not_manufacturing"
        elif "manufaktur" in key:
            if "lamaran" in key and "online" in key:
                kind = "possible_2026_manufacturing_online_application_review_required"
            elif "skill test" in key or "kompetensi" in key:
                kind = "2026_manufacturing_skill_or_optional_competency"
            else:
                kind = "2026_manufacturing_other_notice"
        elif "skill test" in key and "manufaktur" not in key:
            kind = "other_or_unspecified_skill_test"
    return {"date": date, "title": title, "url": url, "reviewCategory": kind}


def fetch_page(start: int, size: int) -> dict:
    query = urlencode({"draw": 1 + start // size, "start": start, "length": size})
    url = FEED + "?" + query
    req = Request(url, headers={
        "User-Agent": "Mozilla/5.0 (compatible; KEP-official-notice-review/1.0)",
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "X-Requested-With": "XMLHttpRequest",
    })
    with urlopen(req, timeout=25) as response:
        if response.status != 200:
            raise ValueError(f"Official announcement data HTTP {response.status}")
        data = json.loads(response.read(4_000_000).decode("utf-8-sig"))
        if not isinstance(data, dict):
            raise ValueError("Official announcement response is not a JSON object")
        return data


def inventory(fetch, *, year: int = 2026, page_size: int = PAGE_SIZE,
              max_pages: int = 15) -> dict:
    if year != 2026 or page_size <= 0:
        raise ValueError("Audit must remain scoped to 2026 KP2MI notices")
    checked, notices, encountered_prior_year = 0, [], False
    total_expected, previous_date = None, None
    for page_index in range(max_pages):
        start = page_index * page_size
        page = fetch(start, page_size)
        rows = page.get("data", [])
        count = page.get("recordsTotal")
        if not isinstance(rows, list) or not isinstance(count, int):
            raise ValueError("Official listing returned malformed DataTables payload")
        if total_expected is None:
            total_expected = count
        elif count != total_expected:
            raise ValueError("Official listing total changed during pagination")
        if not rows or len(rows) > page_size or start >= count:
            raise ValueError("Official listing unexpectedly exhausted before prior year")
        checked += len(rows)
        for row in rows:
            if not isinstance(row, dict):
                raise ValueError("Invalid official notice entry")
            item = notice_from_row(row)
            if previous_date is not None and item["date"] > previous_date:
                raise ValueError("Notice date order changed; cannot certify 2026 coverage")
            previous_date = item["date"]
            if int(item["date"][:4]) < year:
                encountered_prior_year = True
                break
            if int(item["date"][:4]) == year:
                notices.append(item)
        if encountered_prior_year:
            break
        if len(rows) < page_size:
            raise ValueError("Unexpected end of official listing before 2025")
    if not encountered_prior_year:
        raise ValueError("Did not reach previous-year boundary; index review incomplete")
    if not notices:
        raise ValueError("No 2026 notices found, do not assume no new notices")
    specific = [x for x in notices if x["reviewCategory"].startswith("2026_manufacturing_")
                or x["reviewCategory"].startswith("possible_2026_manufacturing_")]
    candidates = [x for x in notices if x["reviewCategory"] ==
                  "possible_2026_manufacturing_online_application_review_required"]
    digest = hashlib.sha256(
        json.dumps(notices, ensure_ascii=False, sort_keys=True,
                   separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    return {
        "generatedUtc": datetime.now(timezone.utc).isoformat(),
        "listingUrl": PAGE_URL,
        "dataEndpoint": FEED,
        "targetYear": 2026,
        "rowsRequestedPerPage": page_size,
        "recordsTotalAsReported": total_expected,
        "rawRowsFetchedThroughBoundary": checked,
        "priorYearBoundaryReached": encountered_prior_year,
        "indexed2026Count": len(notices),
        "manufacturingRelevantTitleCount": len(specific),
        "possibleManufacturingJobApplicationTitles": candidates,
        "manufacturingNoticesForManualReview": specific,
        "noticesSha256": digest,
        "reviewStatus": "inventory_titles_collected_requires_manual_notice_review",
        "releaseAuthorized": False,
        "jobDocsVerified": False,
        "operatorApproved": False,
        "caveat": (
            "Public official notice titles and links only. Even a complete "
            "2026 index does not verify the contents/attachments of all notices "
            "or authorize a Manufacturing 2026 online job document checklist."
        ),
        "all2026NoticeMetadata": notices,
    }


def self_test() -> None:
    def record(date: str, title: str) -> dict:
        return {
            "tanggal": date,
            "judul": f'<a href="/gtog-detail/korea/unit-test">{title}</a>',
        }
    fake = [
        record("9 October 2026", "PENGUMUMAN TERBARU"),
        record("17 September 2026", "SKILL TEST MANUFAKTUR TAHUN 2026"),
        record("10 September 2026", "LAMARAN ONLINE MANUFAKTUR TAHUN 2026"),
        record("19 August 2026", "LAMARAN ONLINE PERIKANAN TAHUN 2026"),
        record("17 July 2026", "LAMARAN ONLINE ROOT INDUSTRY TAHUN 2026"),
        record("30 November 2025", "LAMA"),
    ]
    def fetch(start: int, size: int) -> dict:
        return {"recordsTotal": 100, "data": fake[start:start + size]}
    report = inventory(fetch, page_size=3)
    assert report["indexed2026Count"] == 5
    assert report["priorYearBoundaryReached"] is True
    assert len(report["possibleManufacturingJobApplicationTitles"]) == 1
    assert report["releaseAuthorized"] is False
    assert report["jobDocsVerified"] is False

    bad = [
        (lambda s, n: {"recordsTotal": 100, "data": []}),
        (lambda s, n: {"recordsTotal": 100, "data": list(reversed(fake[s:s+n]))}),
        (lambda s, n: {"recordsTotal": 100, "data": fake[:3]}),
        (lambda s, n: {"recordsTotal": 100, "data": [
            {**fake[0], "judul": '<a href="javascript:evil()">notice</a>'},
            *fake[1:3]]}),
    ]
    for mutation in bad:
        try:
            inventory(mutation, page_size=3, max_pages=3)
        except ValueError:
            pass
        else:
            raise AssertionError("Unsafe/incomplete KP2MI index accepted")
    print("KP2MI_NOTICE_INDEX_SELF_TEST_PASS 4 hostile mutations rejected")


def main() -> None:
    cli = argparse.ArgumentParser()
    cli.add_argument("--self-test", action="store_true")
    cli.add_argument("--output", type=Path)
    args = cli.parse_args()
    if args.self_test:
        self_test()
        return
    if args.output is None:
        cli.error("--output is required; never write to the official source/hash baseline")
    report = inventory(fetch_page)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n",
                           encoding="utf-8")
    print("KP2MI_2026_NOTICE_INVENTORY_READ_OK "
          f"notices={report['indexed2026Count']} "
          f"manufacturing={report['manufacturingRelevantTitleCount']} "
          f"candidates={len(report['possibleManufacturingJobApplicationTitles'])} "
          f"review_status={report['reviewStatus']}")
    print(f"INVENTORY_JSON={args.output}")
    print("RELEASE_HOLD=TRUE; exact job_docs HOLD; operator signoff not provided")


if __name__ == "__main__":
    main()
