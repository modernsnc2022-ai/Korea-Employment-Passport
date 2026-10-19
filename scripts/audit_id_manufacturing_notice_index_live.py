#!/usr/bin/env python3
"""Read-only KP2MI 2026 General Manufacturing official notice index inventory.

This intentionally cannot sign the official index, infer a post-Skill Test
document checklist, update a source fingerprint or open beta access.
"""
from __future__ import annotations

import argparse
from datetime import datetime
from hashlib import sha256
from html.parser import HTMLParser
import json
import re
from urllib.parse import urlencode, urljoin, urlsplit
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo

API = "https://kp2mi.go.id/gtog-data/korea/Pengumuman"
INDEX = "https://kp2mi.go.id/gtog-korea/pengumuman"
MAX_ROWS = 320


class TextCollector(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []

    def handle_data(self, text: str) -> None:
        self.parts.append(text)


def title_text(value: str) -> str:
    parser = TextCollector()
    parser.feed(value)
    return re.sub(r"\s+", " ", " ".join(parser.parts)).strip()


def year_from_row(row: dict) -> int | None:
    # A headline may mention an earlier graduation/departure year even when
    # the official posting itself is new. Classify from posting date ONLY.
    match = re.search(r"\b(?:20[12]\d)\b", str(row.get("tanggal", "")))
    return int(match.group()) if match else None


def classify(row: dict) -> dict:
    raw_title = str(row.get("judul", ""))
    title = title_text(raw_title)
    posting_year = year_from_row(row)
    html_url = re.search(r'href=["\']([^"\']+)', raw_title)
    url = urljoin("https://kp2mi.go.id", html_url.group(1)) if html_url else ""
    if url:
        parsed = urlsplit(url)
        if parsed.scheme != "https" or parsed.hostname not in {"kp2mi.go.id", "www.kp2mi.go.id"}:
            raise ValueError("untrusted official notice link")
    normalized = title.upper()
    mentions_manufacturing = "MANUFAKTUR" in normalized
    general = (
        posting_year == 2026
        and mentions_manufacturing
        and "UBT UMUM" in normalized
        and "2026" in normalized
        and "2025" not in normalized
        and not re.search(r"ROOT INDUSTRY|UBT KHUSUS", normalized)
    )
    other_cohort = posting_year == 2026 and (
        "PERIKANAN" in normalized or "ROOT INDUSTRY" in normalized
        or "UBT KHUSUS" in normalized
    )
    final_submission = bool(re.search(r"PENGAJUAN LAMARAN ONLINE|LAMARAN ONLINE|BERKAS LAMARAN", normalized))
    # Broad title-only sentinel: a generic job-application/document notice may
    # apply to Manufacturing even when the title omits "UBT UMUM"/"MANUFAKTUR".
    # These are manual review candidates, NEVER verified document requirements.
    possible_job_application = bool(
        posting_year == 2026 and re.search(
            r"LAMARAN ONLINE|BERKAS LAMARAN|DOKUMEN LAMARAN|"
            r"PEMENUHAN DOKUMEN|PENGIRIMAN BERKAS LAMARAN|"
            r"E.SERTIFIKAT.*LAMARAN|LAMARAN.*E.SERTIFIKAT",
            normalized,
        )
    )
    return {
        "date": str(row.get("tanggal") or ""),
        "title": title,
        "url": url,
        "id": row.get("id"),
        "generalManufacturing2026": bool(general),
        "generalManufacturingFinalApplicationCandidate": bool(general and final_submission),
        "otherCohortApplicationNotice": bool(posting_year == 2026 and other_cohort and final_submission),
        "possibleJobApplicationTitle": bool(possible_job_application),
    }


def validate_snapshot(rows: list[dict], total: int, *, checked_at: str) -> dict:
    if not rows or not isinstance(total, int) or total < len(rows):
        raise ValueError("empty/inconsistent official index")
    if not all(isinstance(x, dict) and x.get("id") and x.get("judul") for x in rows):
        raise ValueError("incomplete source rows")
    classified = [classify(row) for row in rows]
    if year_from_row(rows[0]) != 2026 or not any(year_from_row(r) == 2025 for r in rows):
        raise ValueError("2026 index period not bounded by 2025; review pagination")
    if not any(x["generalManufacturing2026"] for x in classified):
        raise ValueError("2026 General Manufacturing cohort not identifiable")
    manufacturer = [x for x in classified if x["generalManufacturing2026"]]
    other = [x for x in classified if x["otherCohortApplicationNotice"]]
    hits = [x for x in manufacturer if x["generalManufacturingFinalApplicationCandidate"]]
    broad = [x for x in classified if x["possibleJobApplicationTitle"]]
    # Review generic titles even when "Manufaktur" and "UBT Umum" are absent.
    # Explicit Fisheries/Root/Special applications remain isolated.
    ambiguous = [
        x for x in broad
        if not x["generalManufacturingFinalApplicationCandidate"]
        and not x["otherCohortApplicationNotice"]
    ]
    summary = {
        "checkedAtUtc": checked_at,
        "correctOfficialIndex": INDEX,
        "officialAjax": API,
        "totalHistoricalNotices": total,
        "rowsInspected": len(rows),
        "newestPostedDate": str(rows[0].get("tanggal")),
        "oldestPostedDate": str(rows[-1].get("tanggal")),
        "generalManufacturing2026Notices": manufacturer,
        "otherCohortFinalOnlineApplicationNotices": other,
        "generalManufacturingFinalApplicationCandidates": hits,
        "broadJobApplicationTitleCandidates": broad,
        "ambiguousGenericJobApplicationTitleCandidates": ambiguous,
        "genericCandidateReviewRequired": bool(ambiguous),
        "titleOnlyIndex": True,
        "humanOperatorSignedOff": False,
        "exactFinalJobDocumentsVerified": False,
        "sourceBaselineAccepted": False,
        "betaReleaseAuthorized": False,
        "titleUrlDigestSha256": sha256(json.dumps(
            [(x["id"], x["date"], x["title"], x["url"]) for x in classified],
            ensure_ascii=False, separators=(",", ":")
        ).encode("utf-8")).hexdigest(),
    }
    return summary


def self_test() -> None:
    def row(i: int, title: str, date: str = "14 October 2026") -> dict:
        return {
            "id": i, "judul": '<a href="/gtog-detail/korea/notice-' + str(i) + '">' + title + "</a>",
            "tanggal": date,
        }

    base = [
        row(1, "PENGUMUMAN PERSYARATAN SKILL TEST UBT UMUM SEKTOR MANUFAKTUR 2026"),
        row(2, "PEMBAGIAN E-SERTIFIKAT DAN PENGAJUAN LAMARAN ONLINE SEKTOR PERIKANAN 2026"),
        row(3, "PENGAJUAN LAMARAN ONLINE ROOT INDUSTRY 2026"),
        row(4, "PENGAJUAN LAMARAN ONLINE UBT KHUSUS 2026"),
        row(5, "PENGAJUAN LAMARAN ONLINE UBT UMUM SEKTOR MANUFAKTUR 2025", "10 December 2025"),
    ]
    report = validate_snapshot(base, 30, checked_at="2026-10-14T06:00:00+00:00")
    assert len(report["generalManufacturing2026Notices"]) == 1
    assert not report["generalManufacturingFinalApplicationCandidates"]
    assert len(report["otherCohortFinalOnlineApplicationNotices"]) == 3
    assert report["humanOperatorSignedOff"] is False
    assert report["exactFinalJobDocumentsVerified"] is False
    # A real subsequent 2026 general Manufacturing final-submission title must
    # be marked as a NEW candidate, not silently treated as already approved.
    fresh = row(6, "PENGAJUAN LAMARAN ONLINE UBT UMUM SEKTOR MANUFAKTUR 2026")
    found = validate_snapshot([fresh] + base, 31, checked_at="2026-10-14T06:01:00+00:00")
    assert len(found["generalManufacturingFinalApplicationCandidates"]) == 1
    assert found["exactFinalJobDocumentsVerified"] is False
    # A generic notice without sector/cohort keywords must still be surfaced
    # for a human review; neither it nor a specialized notice may approve rules.
    generic = row(8, "PENGUMUMAN PENGAJUAN LAMARAN ONLINE G TO G KOREA 2026")
    generic_report = validate_snapshot(
        [generic] + base, 31, checked_at="2026-10-15T06:01:00+00:00"
    )
    assert len(generic_report["ambiguousGenericJobApplicationTitleCandidates"]) == 1
    assert generic_report["ambiguousGenericJobApplicationTitleCandidates"][0]["id"] == 8
    assert not generic_report["generalManufacturingFinalApplicationCandidates"]
    assert generic_report["genericCandidateReviewRequired"] is True
    assert generic_report["exactFinalJobDocumentsVerified"] is False
    assert generic_report["betaReleaseAuthorized"] is False
    assert len(report["broadJobApplicationTitleCandidates"]) == 3
    assert not report["ambiguousGenericJobApplicationTitleCandidates"]
    # A 2026 post discussing the 2025 cohort is not a 2026 final notice.
    mislabeled = row(7, "UBT UMUM SEKTOR MANUFAKTUR 2025 LAMARAN ONLINE")
    assert not classify(mislabeled)["generalManufacturingFinalApplicationCandidate"]
    try:
        validate_snapshot(base[:-1], 30, checked_at="2026-10-14T06:00:00+00:00")
    except ValueError:
        pass
    else:
        raise AssertionError("Missing prior-year boundary was wrongly accepted")
    print("ID_MANUFACTURING_LIVE_INDEX_SELF_TEST_PASS cohort_isolation_and_future_notice_fail_closed")


def retrieve() -> tuple[list[dict], int]:
    params = urlencode({
        "draw": 1, "start": 0, "length": MAX_ROWS,
        "search[value]": "", "search[regex]": "false"
    })
    req = Request(
        API + "?" + params,
        headers={
            "User-Agent": "Mozilla/5.0 (KEP-readonly-official-notice-index)",
            "Referer": INDEX,
            "Accept": "application/json",
        },
    )
    with urlopen(req, timeout=65) as response:
        if response.status != 200 or urlsplit(response.url).scheme != "https":
            raise ValueError("Official HTTPS listing unavailable")
        raw = response.read(14_000_000)
    data = json.loads(raw)
    return data["data"], int(data["recordsTotal"])


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return
    rows, total = retrieve()
    report = validate_snapshot(
        rows, total,
        checked_at=datetime.now(ZoneInfo("UTC")).isoformat()
    )
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(
            f"ID_MANUFACTURING_INDEX_READONLY 2026_general={len(report['generalManufacturing2026Notices'])} "
            f"other_cohort_online={len(report['otherCohortFinalOnlineApplicationNotices'])} "
            f"general_manufacturing_final_candidate={len(report['generalManufacturingFinalApplicationCandidates'])} "
            f"broad_job_application_titles={len(report['broadJobApplicationTitleCandidates'])} "
            f"ambiguous_generic_titles={len(report['ambiguousGenericJobApplicationTitleCandidates'])} "
            f"rows={report['rowsInspected']} oldest={report['oldestPostedDate']} "
            f"sha256={report['titleUrlDigestSha256']}"
        )
        for row in report["generalManufacturing2026Notices"]:
            print("GENERAL", row["date"], row["title"], row["url"])
        for row in report["otherCohortFinalOnlineApplicationNotices"]:
            print("OTHER_COHORT", row["date"], row["title"])
        for row in report["ambiguousGenericJobApplicationTitleCandidates"]:
            print("GENERIC_REVIEW_REQUIRED", row["date"], row["title"], row["url"])
        print("READ_ONLY_NO_SIGNOFF_NO_DOCUMENT_PROMOTION_NO_BETA_RELEASE")


if __name__ == "__main__":
    main()
