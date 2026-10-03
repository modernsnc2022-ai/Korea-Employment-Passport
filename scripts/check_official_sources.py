#!/usr/bin/env python3
import argparse
import hashlib
import json
import re
import sys
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from html.parser import HTMLParser
from pathlib import Path
from threading import Semaphore
from urllib.parse import urlparse

class TextExtractor(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.skip = 0
        self.parts = []

    def handle_starttag(self, tag, attrs):
        if tag.lower() in {"script", "style", "noscript", "svg"}:
            self.skip += 1

    def handle_endtag(self, tag):
        if tag.lower() in {"script", "style", "noscript", "svg"} and self.skip:
            self.skip -= 1

    def handle_data(self, data):
        if not self.skip:
            text = " ".join(data.split())
            if text:
                self.parts.append(text)

def fetch_fingerprint(url):
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Korea-Employment-Passport-SourceMonitor/1.1 (+GitHub Actions)",
            "Accept-Language": "ko,en;q=0.8,id;q=0.7",
        },
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        raw = resp.read()
        content_type = (resp.headers.get_content_type() or "").lower()
        charset = resp.headers.get_content_charset() or "utf-8"

    if content_type == "application/pdf" or url.lower().split("?", 1)[0].endswith(".pdf"):
        return {
            "sha256": hashlib.sha256(raw).hexdigest(),
            "contentLength": len(raw),
            "mode": "binary",
            "contentType": content_type or "application/pdf",
        }

    html = raw.decode(charset, errors="replace")
    extractor = TextExtractor()
    extractor.feed(html)
    normalized = re.sub(r"\s+", " ", " ".join(extractor.parts)).strip()
    # Ignore volatile page counters that change on every fetch but do not alter the official rule.
    normalized = re.sub(r"(조회(?:수)?)\s*[:：]?\s*[0-9][0-9,]*", r"\1 <dynamic-count>", normalized)
    normalized = re.sub(r"(Views?|Hits?)\s*[:：]?\s*[0-9][0-9,]*", r"\1 <dynamic-count>", normalized, flags=re.I)
    return {
        "sha256": hashlib.sha256(normalized.encode("utf-8")).hexdigest(),
        "contentLength": len(normalized),
        "mode": "normalized_text",
        "contentType": content_type or "text/html",
    }

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--sources", default="monitor/sources.json")
    p.add_argument("--baseline", default="monitor/source_hashes.json")
    p.add_argument("--output", default="monitor/check_result.json")
    p.add_argument("--accept-current", action="store_true")
    p.add_argument("--init-if-empty", action="store_true")
    p.add_argument("--workers", type=int, default=4, help="Concurrent source fetches across different hosts (1-8)")
    p.add_argument("--retries", type=int, default=2, help="Attempts for transient network failures (1-3)")
    args = p.parse_args()
    workers = max(1, min(args.workers, 8))
    attempts = max(1, min(args.retries, 3))

    sources = json.loads(Path(args.sources).read_text(encoding="utf-8-sig"))["sources"]
    baseline_path = Path(args.baseline)
    baseline = json.loads(baseline_path.read_text(encoding="utf-8-sig")) if baseline_path.exists() else {}

    fingerprints = {}
    failure_by_id = {}
    host_gates = {
        urlparse(source["url"]).netloc.lower(): Semaphore(1)
        for source in sources
    }

    def fetch_source(source):
        url = source["url"]
        host = urlparse(url).netloc.lower()
        last_error = None
        with host_gates[host]:
            for attempt in range(1, attempts + 1):
                try:
                    return source["id"], fetch_fingerprint(url)
                except Exception as exc:
                    last_error = exc
                    if "CERTIFICATE_VERIFY_FAILED" in str(exc) or attempt >= attempts:
                        break
                    time.sleep(0.75 * attempt)
        raise last_error

    with ThreadPoolExecutor(max_workers=workers) as executor:
        future_to_source = {executor.submit(fetch_source, source): source for source in sources}
        for future in as_completed(future_to_source):
            source = future_to_source[future]
            try:
                source_id, fingerprint = future.result()
                fingerprints[source_id] = fingerprint
            except Exception as exc:
                failure_by_id[source["id"]] = str(exc)

    current = {}
    failures = []
    for source in sources:
        source_id = source["id"]
        fingerprint = fingerprints.get(source_id)
        if fingerprint is None:
            failures.append({"id": source_id, "url": source["url"], "error": failure_by_id.get(source_id, "unknown fetch failure")})
            continue
        current[source_id] = {
            "sha256": fingerprint["sha256"],
            "agency": source["agency"],
            "url": source["url"],
            "contentLength": fingerprint["contentLength"],
            "mode": fingerprint["mode"],
            "contentType": fingerprint["contentType"],
        }

    changed = []
    for source_id, now in current.items():
        before = baseline.get(source_id, {})
        old_hash = before.get("sha256")
        if old_hash and old_hash != now["sha256"]:
            changed.append({
                "id": source_id,
                "agency": now["agency"],
                "url": now["url"],
                "before": old_hash,
                "after": now["sha256"],
            })

    initialized = False
    accepted = False
    acceptance_blocked = False
    complete_fetch = len(current) == len(sources) and not failures

    if args.init_if_empty and not baseline and current:
        if complete_fetch:
            baseline_path.write_text(json.dumps(current, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            initialized = True
        else:
            acceptance_blocked = True

    if args.accept_current:
        if complete_fetch:
            baseline_path.write_text(json.dumps(current, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            accepted = True
        else:
            acceptance_blocked = True

    result = {
        "initialized": initialized,
        "acceptedCurrent": accepted,
        "acceptanceBlocked": acceptance_blocked,
        "changed": changed,
        "failures": failures,
        "checked": len(current),
        "configured": len(sources),
        "workers": workers,
        "attempts": attempts,
    }
    Path(args.output).write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False))
    if not current:
        return 2
    return 0

if __name__ == "__main__":
    sys.exit(main())
