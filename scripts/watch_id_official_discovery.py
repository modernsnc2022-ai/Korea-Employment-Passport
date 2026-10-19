#!/usr/bin/env python3
"""Read-only official KP2MI announcements + HRD Korea Indonesia EPS schedule watch.

No scheduling, source hash acceptance, user notification or beta access is performed.
A JSON observation is written only with explicit --output outside the repository.
"""
from __future__ import annotations

import argparse
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import sys
from datetime import datetime, timezone
from urllib.parse import urlencode, urljoin, urlsplit
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
KP2MI_INDEX = "https://kp2mi.go.id/gtog-korea/pengumuman"
KP2MI_DATA = "https://kp2mi.go.id/gtog-data/korea/Pengumuman"
HRD_LIST = "https://epstopik.hrdkorea.or.kr/epstopik/abot/exam/selectSechduleDescList.do"
HRD_DETAIL = "https://epstopik.hrdkorea.or.kr/epstopik/abot/exam/sechduleDetail.do"
MAX_HRD_PAGES = 8
CURRENT_COHORT = "2026"
SCHEMA = "kep-id-official-discovery-v1"


def official_url(url: str, hosts: set[str]) -> str:
    p = urlsplit(url)
    if p.scheme != "https" or (p.hostname or "").lower() not in hosts or p.username or p.password:
        raise ValueError("Official HTTPS host required")
    return url


class Visible(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self.skip = 0

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style", "noscript"):
            self.skip += 1

    def handle_endtag(self, tag):
        if tag in ("script", "style", "noscript") and self.skip:
            self.skip -= 1

    def handle_data(self, data):
        if not self.skip:
            self.parts.append(data)

    def text(self):
        return re.sub(r"\s+", " ", " ".join(self.parts)).strip()


def stripped(value: str) -> str:
    p = Visible()
    p.feed(value)
    return p.text()


def sha(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def fetch(url: str) -> bytes:
    p = urlsplit(url)
    official_url(url, {"kp2mi.go.id", "epstopik.hrdkorea.or.kr"})
    request = Request(url, headers={"User-Agent": "Mozilla/5.0 (KEP read-only official discovery)",
                                    "Accept-Language": "en,ko;q=0.9,id;q=0.8"})
    with urlopen(request, timeout=30) as response:
        official_url(response.url, {"kp2mi.go.id", "epstopik.hrdkorea.or.kr"})
        if response.status != 200:
            raise ValueError("Official request returned non-200")
        body = response.read(14_000_001)
    if len(body) > 14_000_000 or len(body) < 100:
        raise ValueError("Unexpected official response size")
    return body


def canonical_kp2mi(data: dict) -> list[dict]:
    rows = data.get("data")
    if not isinstance(rows, list) or not rows or len(rows) > 320 or int(data.get("recordsTotal", 0)) < len(rows):
        raise ValueError("Missing/inconsistent KP2MI rows")
    from audit_id_manufacturing_notice_index_live import classify
    items = []
    for row in rows:
        if not isinstance(row, dict) or not isinstance(row.get("id"), int) or not row.get("judul"):
            raise ValueError("Malformed official notice")
        c = classify(row)
        if not c["url"]:
            raise ValueError("Official notice missing HTTPS detail link")
        official_url(c["url"], {"kp2mi.go.id", "www.kp2mi.go.id"})
        # The official JSON includes article bodies (which can include personal details).
        # Preserve ONLY the normalized body digest, not content, sample ID or applicant text.
        body = stripped(str(row.get("gtgkorea") or ""))
        item = {"key": "kp2mi:" + str(row["id"]), "provider": "kp2mi",
                "id": row["id"], "date": c["date"], "title": c["title"],
                "url": c["url"], "bodyDigest": sha(body),
                "generalManufacturing2026": c["generalManufacturing2026"],
                "generalManufacturingFinalCandidate": c["generalManufacturingFinalApplicationCandidate"],
                "genericApplicationReview": c["possibleJobApplicationTitle"]
                    and not c["otherCohortApplicationNotice"]
                    and not c["generalManufacturingFinalApplicationCandidate"]}
        items.append(item)
    keys = [x["key"] for x in items]
    if len(keys) != len(set(keys)):
        raise ValueError("Duplicate KP2MI notice IDs")
    # Do not accept an empty/partial or non-2026 page as a clean official inventory.
    from audit_id_manufacturing_notice_index_live import validate_snapshot
    validate_snapshot(rows, int(data["recordsTotal"]), checked_at="read-only")
    return items


class HrdTable(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.items: list[dict] = []
        self.current: dict | None = None
        self.in_td = 0
        self.cells: list[list[str]] = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "tr" and a.get("id", "").startswith("tr_"):
            required = ("lcnsid", "examyear", "examnot", "examnation")
            aa = {k.lower(): v for k, v in a.items()}
            if not all(aa.get(k) for k in required):
                raise ValueError("Incomplete HRD schedule identity")
            self.current = aa
            self.cells = []
        if self.current is not None and tag == "td":
            self.in_td += 1
            if self.in_td == 1:
                self.cells.append([])

    def handle_endtag(self, tag):
        if tag == "td" and self.current is not None:
            self.in_td = max(0, self.in_td - 1)
        if tag == "tr" and self.current is not None:
            if len(self.cells) != 6:
                raise ValueError("Malformed HRD schedule table cells")
            vals = [re.sub(r"\s+", " ", " ".join(parts)).strip() for parts in self.cells]
            a = self.current
            key = ":".join([a["examnation"], a["examyear"], a["examnot"], a["lcnsid"]])
            url = HRD_DETAIL + "?" + urlencode({"examNation": a["examnation"],
                "examNot": a["examnot"], "examYear": a["examyear"],
                "lang": "ko", "lcnsId": a["lcnsid"]})
            title = vals[1]
            relevant = (a["examnation"] == "012" and a["examyear"] == CURRENT_COHORT
                and "indonesia" in title.lower() and "manufacturing" in title.lower()
                and not re.search(r"root industry|mold|ubt khusus|special", title, re.I))
            self.items.append({"key": "hrdk:" + key, "provider": "hrdk", "nation": a["examnation"],
                "year": a["examyear"], "examNo": a["examnot"], "lcnsId": a["lcnsid"],
                "type": vals[0], "title": title, "countryName": vals[2],
                "period": vals[3], "testDate": vals[4], "resultDate": vals[5],
                "url": official_url(url, {"epstopik.hrdkorea.or.kr"}),
                "generalManufacturing2026": relevant})
            self.current = None
            self.cells = []
            self.in_td = 0

    def handle_data(self, data):
        if self.current is not None and self.in_td and self.cells:
            self.cells[-1].append(data)


def parse_hrd_page(html: str, page: int) -> tuple[list[dict], int]:
    marker = re.search(r'<input[^>]*\bid="pageIndex"[^>]*\bvalue="(\d+)"', html)
    if not marker or int(marker.group(1)) != page:
        raise ValueError("Wrong HRD pagination page")
    parser = HrdTable()
    parser.feed(html)
    if not parser.items:
        raise ValueError("Empty HRD schedule page")
    # HRD renders all 6 page links in HTML. A count beyond bound must fail.
    pages = [int(x) for x in re.findall(r'href="\?pageIndex=(\d+)"', html)]
    number = max([page] + pages)
    if number > MAX_HRD_PAGES:
        raise ValueError("HRD page count exceeds audited bound")
    return parser.items, number


def snapshot(kp2mi: list[dict], hrd: list[dict], *, observed: str) -> dict:
    k1 = {x["key"] for x in kp2mi}
    h1 = {x["key"] for x in hrd}
    if len(k1) != len(kp2mi) or len(h1) != len(hrd) or not kp2mi or not hrd:
        raise ValueError("Incomplete/duplicate source snapshot")
    if not any(x.get("generalManufacturing2026") for x in kp2mi):
        raise ValueError("General Manufacturing index missing")
    if not any(x.get("generalManufacturing2026") for x in hrd):
        raise ValueError("HRD Indonesia General Manufacturing schedule missing")
    return {"schema": SCHEMA, "observedAtUtc": observed, "status": "observed_not_approved",
            "sourceHashAutoAccepted": False, "betaOpenAuthorized": False,
            "sourcesComplete": ["kp2mi", "hrdk"],
            "records": sorted(kp2mi + hrd, key=lambda a: a["key"])}


def diff(old: dict | None, new: dict) -> dict:
    if old is None:
        return {"initial": True, "events": [], "suppressedFirstRun": len(new["records"])}
    if old.get("schema") != SCHEMA or set(old.get("sourcesComplete", [])) != {"kp2mi", "hrdk"}:
        raise ValueError("Prior snapshot is not a complete compatible observation")
    prev = {x["key"]: x for x in old["records"]}
    now = {x["key"]: x for x in new["records"]}
    if len(prev) != len(old["records"]) or not prev:
        raise ValueError("Duplicate/empty previous source observations")
    events = []
    for key, item in now.items():
        past = prev.get(key)
        if past is None:
            kind = "new_notice_or_exam"
        elif {k: v for k, v in item.items() if k not in ("key",)} != {k: v for k, v in past.items() if k not in ("key",)}:
            kind = "changed_notice_or_exam"
        else:
            continue
        events.append({"kind": kind, "key": key, "title": item["title"],
            "url": item["url"], "needsHumanReview": True, "routeRelevant": bool(item.get("generalManufacturing2026")),
            "maybeFinalApplication": bool(item.get("generalManufacturingFinalCandidate") or item.get("genericApplicationReview"))})
    # Bounded KP2MI/HRD windows can move older records out of scope.
    # Never interpret disappearance as an authoritative deletion.
    missing = len(set(prev) - set(now))
    return {"initial": False, "events": sorted(events, key=lambda x: x["key"]),
        "notSeenInBoundedWindow": missing}


def live() -> dict:
    params = urlencode({"draw": 1, "start": 0, "length": 320, "search[value]": "",
                        "search[regex]": "false"})
    kp2mi = canonical_kp2mi(json.loads(fetch(KP2MI_DATA + "?" + params)))
    # With thousands of official historical rows, a shorter result than the
    # requested full 320-item window is a partial observation, not success.
    if len(kp2mi) != 320:
        raise ValueError("Incomplete KP2MI announcement window")
    first = fetch(HRD_LIST + "?lang=en").decode("utf-8", errors="replace")
    pages, count = parse_hrd_page(first, 1)
    all_hrd = pages[:]
    for num in range(2, count + 1):
        html = fetch(HRD_LIST + "?" + urlencode({"lang": "en", "pageIndex": num})).decode("utf-8", errors="replace")
        records, reported = parse_hrd_page(html, num)
        if reported != count:
            raise ValueError("Inconsistent HRD schedule pagination")
        all_hrd.extend(records)
    if len(all_hrd) != len({x["key"] for x in all_hrd}):
        raise ValueError("Duplicate HRD list items across pages")
    # The public list presents only its newest six pages (older 2026 Jakarta/
    # Semarang records are still accessible by official detail URL but absent
    # from those pages). Keep BOTH exact verified cohort IDs pinned; a missing
    # current-year schedule on the truncated list must not be reported clean.
    for exam_no, city in (("14", "Jakarta"), ("15", "Semarang")):
        key = "hrdk:012:2026:" + exam_no + ":001"
        if not any(x["key"] == key for x in all_hrd):
            url = HRD_DETAIL + "?" + urlencode({"examNation": "012", "examNot": exam_no,
                 "examYear": "2026", "lang": "ko", "lcnsId": "001"})
            all_hrd.append({"key": key, "provider": "hrdk", "nation": "012",
                "year": "2026", "examNo": exam_no, "lcnsId": "001",
                "type": "CBT", "title": "The 13th recruitment of the point system in Indonesia(Manufacturing)_" + city,
                "countryName": "Indonesia", "period": "", "testDate": "", "resultDate": "",
                "url": official_url(url, {"epstopik.hrdkorea.or.kr"}),
                "generalManufacturing2026": True})
    # Fetch matching detail pages to identify actual timeline changes, not just titles.
    for item in all_hrd:
        if item["generalManufacturing2026"]:
            html = fetch(item["url"]).decode("utf-8", errors="replace")
            txt = stripped(html)
            if "Indonesia(Manufacturing)" not in txt or item["title"] not in txt:
                raise ValueError("HRD detail no longer matches Indonesia General Manufacturing")
            item["detailDates"] = sorted(set(re.findall(r"\b20\d{2}-\d{2}-\d{2}\b", txt)))
            if not item["detailDates"]:
                raise ValueError("HRD detail contains no parseable dates")
    return snapshot(kp2mi, all_hrd, observed=datetime.now(timezone.utc).isoformat())


def self_test():
    from audit_id_manufacturing_notice_index_live import self_test as prior_test
    prior_test()
    row = {"id": 123, "tanggal": "15 October 2026",
        "judul": '<a href="/gtog-detail/korea/sample">PENGUMUMAN UBT UMUM SEKTOR MANUFAKTUR TAHUN 2026</a>',
        "gtgkorea": "<p>Notice text</p>"}
    old = {"id": 122, "tanggal": "31 December 2025",
        "judul": '<a href="/gtog-detail/korea/prior">Old general notice</a>', "gtgkorea": ""}
    kp = canonical_kp2mi({"data": [row, old], "recordsTotal": 200})
    assert len(kp) == 2 and kp[0]["generalManufacturing2026"]
    page = """<form><input id="pageIndex" value="1"/></form><table>
<tr id="tr_1" lcnsId="001" examYear="2026" examNot="14" examNation="012">
<td>CBT</td><td>Indonesia(Manufacturing)_Jakarta</td><td>Indonesia</td>
<td>2026-02-10 ~ 2026-02-12</td><td>2026-06-04 ~ 2026-06-29</td><td>2026-09-10</td></tr>
<tr id="tr_2" lcnsId="001" examYear="2026" examNot="54" examNation="012">
<td>CBT</td><td>Indonesia(Root Industry Mold)</td><td>Indonesia</td>
<td>Undecided</td><td>Undecided</td><td>Undecided</td></tr></table>"""
    hrd, n = parse_hrd_page(page, 1)
    assert n == 1 and len(hrd) == 2 and hrd[0]["generalManufacturing2026"]
    assert not hrd[1]["generalManufacturing2026"]
    snap = snapshot(kp, hrd, observed="2026-10-15T10:00:00+00:00")
    assert diff(None, snap)["events"] == []
    assert not diff(snap, snap)["events"]
    changed = json.loads(json.dumps(snap))
    changed["records"][0]["title"] += " UPDATED"
    d = diff(snap, changed)
    assert len(d["events"]) == 1 and d["events"][0]["needsHumanReview"]
    try:
        canonical_kp2mi({"data": [row, row, old], "recordsTotal": 200})
        raise AssertionError("duplicate notice allowed")
    except ValueError:
        pass
    try:
        parse_hrd_page(page.replace('value="1"', 'value="2"'), 1)
        raise AssertionError("wrong HRD page allowed")
    except ValueError:
        pass
    try:
        official_url("https://evil.test/gtog-detail/korea/sample", {"kp2mi.go.id"})
        raise AssertionError("wrong host allowed")
    except ValueError:
        pass
    # Scoped old/new differences never set beta open or source hash acceptance.
    assert not snap["betaOpenAuthorized"] and not snap["sourceHashAutoAccepted"]
    print("KEP_OFFICIAL_DISCOVERY_SELF_TEST_PASS no_auto_release cohort_scope duplicate_and_page_guards")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true", help="Fetch official sources read-only")
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--previous", type=Path, help="Read a previous observation JSON (no acceptance)")
    parser.add_argument("--output", type=Path, help="Write observation JSON outside repository explicitly")
    parser.add_argument("--state-db", type=Path, help="External SQLite observation checkpoint, never an approval store")
    parser.add_argument("--list-pending", action="store_true", help="Inspect persistent review queue without sending alerts")
    parser.add_argument("--health", action="store_true", help="Fail on stale/failed checkpoint, useful for watchdog")
    parser.add_argument("--stale-hours", type=int, default=4)
    args = parser.parse_args()

    if args.self_test:
        self_test()
        return 0
    if args.state_db:
        from official_discovery_state import safe_external_path
        args.state_db = safe_external_path(args.state_db, ROOT)
    if args.list_pending or args.health:
        if not args.state_db or args.live or args.previous or args.output:
            parser.error("--list-pending/--health require --state-db alone")
        from official_discovery_state import pending_events, health
        if args.list_pending:
            for event in pending_events(args.state_db):
                print(json.dumps(event, ensure_ascii=False))
        if args.health:
            result = health(args.state_db, stale_hours=args.stale_hours)
            print("KEP_MONITOR_HEALTH " + json.dumps(result, ensure_ascii=False))
            if not result["healthy"]:
                return 2
        return 0
    if not args.live:
        parser.error("Use --live or --self-test; no automatic network polling")
    if args.previous and args.state_db:
        parser.error("--previous and --state-db represent distinct observation storage modes")
    previous = json.loads(args.previous.read_text(encoding="utf-8")) if args.previous else None
    try:
        current = live()  # fetch exceptions do NOT mutate any last-good observation
    except Exception as exc:
        if args.state_db:
            from official_discovery_state import record_failure
            failures = record_failure(args.state_db, exc)
            print(f"KEP_DISCOVERY_FETCH_FAILURE count={failures} checkpoint_preserved=TRUE", file=sys.stderr)
        raise
    if args.state_db:
        from official_discovery_state import record_success
        report = record_success(args.state_db, current, diff)
        print("KEP_DURABLE_REVIEW_QUEUE " + json.dumps(report, ensure_ascii=False))
    else:
        report = diff(previous, current)
    if args.output:
        target = args.output.resolve()
        if ROOT.resolve() == target or ROOT.resolve() in target.parents or target.suffix.lower() != ".json":
            raise ValueError("Observation output must be an external JSON file, never repository approval data")
        target.write_text(json.dumps(current, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    events = report.get("events", [])
    print(f"KEP_DISCOVERY_READONLY kp2mi={sum(x['provider']=='kp2mi' for x in current['records'])} "
          f"hrdk={sum(x['provider']=='hrdk' for x in current['records'])} "
          f"id_general={sum(x.get('generalManufacturing2026', False) for x in current['records'])} "
          f"events={len(events) if events else report.get('eventsDetected', 0)} "
          f"initial={report.get('initial', report.get('firstRun', False))}")
    for event in events:
        print(json.dumps(event, ensure_ascii=False))
    print("NO_AUTO_APPROVAL_NO_NOTIFICATIONS_NO_BETA_RELEASE")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ValueError, OSError, TimeoutError, KeyError, json.JSONDecodeError) as exc:
        print(f"KEP_DISCOVERY_FAIL_CLOSED {type(exc).__name__}: {exc}", file=sys.stderr)
        raise SystemExit(2)
