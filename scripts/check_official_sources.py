#!/usr/bin/env python3
import argparse
import hashlib
import http.client
import json
import re
import shutil
import ssl
import subprocess
import sys
import tempfile
import time
import urllib.request
from datetime import date
from concurrent.futures import ThreadPoolExecutor, as_completed
from html.parser import HTMLParser
from pathlib import Path
from threading import Semaphore
from urllib.parse import urljoin, urlparse

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

REQUEST_HEADERS = {
    "User-Agent": "Korea-Employment-Passport-SourceMonitor/1.3 (+GitHub Actions)",
    "Accept-Language": "ko,en;q=0.8,id;q=0.7",
}
REQUEST_TIMEOUT_SECONDS = 12
NORMALIZATION_REVISION = "cross-site-volatile-widget-v3"
KP2MI_DYNAMIC_DATE_RE = re.compile(
    r"^(?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday),\s+"
    r"\d{1,2}\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4}\b",
    flags=re.I,
)

def _verified_fetch(url):
    req = urllib.request.Request(url, headers=REQUEST_HEADERS)
    with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT_SECONDS) as resp:
        raw = resp.read()
        content_type = (resp.headers.get_content_type() or "").lower()
        charset = resp.headers.get_content_charset() or "utf-8"
        final_url = resp.geturl()
    return raw, content_type, charset, final_url, "ca_verified"

def _curl_verified_fetch(url):
    curl = shutil.which("curl") or shutil.which("curl.exe")
    if not curl:
        raise RuntimeError("curl is unavailable for CA-verified TLS compatibility fallback")
    with tempfile.TemporaryDirectory(prefix="kep-source-") as temp_dir:
        body_path = Path(temp_dir) / "body.bin"
        completed = subprocess.run(
            [
                curl,
                "--location",
                "--fail",
                "--silent",
                "--show-error",
                "--max-time",
                str(REQUEST_TIMEOUT_SECONDS),
                "--header",
                f"User-Agent: {REQUEST_HEADERS['User-Agent']}",
                "--header",
                f"Accept-Language: {REQUEST_HEADERS['Accept-Language']}",
                "--output",
                str(body_path),
                "--write-out",
                "%{content_type}\\n%{url_effective}",
                url,
            ],
            capture_output=True,
            text=True,
            timeout=REQUEST_TIMEOUT_SECONDS + 5,
            check=False,
        )
        if completed.returncode != 0:
            raise RuntimeError("CA-verified curl fallback failed: " + completed.stderr.strip())
        meta = completed.stdout.splitlines()
        content_header = meta[0].strip() if meta else ""
        final_url = meta[1].strip() if len(meta) > 1 else url
        content_type = content_header.split(";", 1)[0].strip().lower()
        charset_match = re.search(r"charset=([^;\\s]+)", content_header, flags=re.I)
        charset = charset_match.group(1).strip('"') if charset_match else "utf-8"
        return body_path.read_bytes(), content_type, charset, final_url, "curl_ca_verified"


def _pin_record(host, tls_pins):
    return (tls_pins or {}).get("hosts", {}).get(host.lower())

def _validate_pin_record(host, pin):
    if not pin:
        raise ssl.SSLCertVerificationError(f"No reviewed TLS pin is configured for {host}")
    valid_until = pin.get("validUntil")
    if not valid_until:
        raise ssl.SSLCertVerificationError(f"TLS pin for {host} has no validUntil")
    if date.today() > date.fromisoformat(valid_until):
        raise ssl.SSLCertVerificationError(f"Reviewed TLS pin for {host} expired on {valid_until}")
    hashes = {str(x).lower() for x in pin.get("leafSha256", []) if x}
    if not hashes:
        raise ssl.SSLCertVerificationError(f"TLS pin for {host} has no leafSha256")
    return hashes

def _pinned_fetch(url, tls_pins, redirects=3):
    if redirects < 0:
        raise RuntimeError("Too many redirects while using pinned TLS fallback")
    parsed = urlparse(url)
    if parsed.scheme.lower() != "https":
        raise RuntimeError("Pinned TLS fallback is only allowed for HTTPS URLs")
    host = parsed.hostname or ""
    pin = _pin_record(host, tls_pins)
    allowed_hashes = _validate_pin_record(host, pin)

    context = ssl._create_unverified_context()
    conn = http.client.HTTPSConnection(host, port=parsed.port or 443, timeout=REQUEST_TIMEOUT_SECONDS, context=context)
    try:
        conn.connect()
        der = conn.sock.getpeercert(binary_form=True)
        actual_hash = hashlib.sha256(der).hexdigest().lower()
        if actual_hash not in allowed_hashes:
            raise ssl.SSLCertVerificationError(
                f"TLS pin mismatch for {host}: expected one of {sorted(allowed_hashes)}, got {actual_hash}"
            )

        path = parsed.path or "/"
        if parsed.query:
            path += "?" + parsed.query
        conn.request("GET", path, headers=REQUEST_HEADERS)
        resp = conn.getresponse()
        raw = resp.read()
        location = resp.getheader("Location")
        status = resp.status
        content_type = (resp.headers.get_content_type() or "").lower()
        charset = resp.headers.get_content_charset() or "utf-8"
    finally:
        conn.close()

    if status in {301, 302, 303, 307, 308} and location:
        return _fetch_response(urljoin(url, location), tls_pins, redirects=redirects - 1)
    if status >= 400:
        raise RuntimeError(f"HTTP {status} from pinned official source {url}")
    return raw, content_type, charset, url, "pinned_leaf"

def _fetch_response(url, tls_pins, redirects=3):
    try:
        return _verified_fetch(url)
    except Exception as exc:
        message = str(exc)
        if "HANDSHAKE_FAILURE" in message.upper():
            return _curl_verified_fetch(url)
        if "CERTIFICATE_VERIFY_FAILED" not in message:
            raise
        host = (urlparse(url).hostname or "").lower()
        if not _pin_record(host, tls_pins):
            raise
        return _pinned_fetch(url, tls_pins, redirects=redirects)

def normalize_source_text(text, final_url):
    normalized = re.sub(r"\s+", " ", text).strip()
    host = (urlparse(final_url).hostname or "").lower()
    if host.startswith("www."):
        host = host[4:]
    if host == "kp2mi.go.id":
        # KP2MI renders today's date in the common page header. It is not
        # notice content and changes every day across unrelated official pages.
        normalized = KP2MI_DYNAMIC_DATE_RE.sub("<dynamic-page-date>", normalized, count=1)
    # Ignore volatile counters that change on every fetch but do not alter the official rule.
    normalized = re.sub(r"(조회(?:수)?)\s*[:：]?\s*[0-9][0-9,]*", r"\1 <dynamic-count>", normalized)
    normalized = re.sub(r"(Views?|Hits?)\s*[:：]?\s*[0-9][0-9,]*", r"\1 <dynamic-count>", normalized, flags=re.I)
    if host == "mol.gov.mm":
        # Myanmar Ministry of Labour pages expose request-specific traffic/IP widgets.
        # They are presentation telemetry, not recruitment or eligibility content.
        normalized = re.sub(
            r"(Users\s+Today)\s*[:：]?\s*[0-9][0-9,]*",
            r"\1 <dynamic-count>",
            normalized,
            flags=re.I,
        )
        normalized = re.sub(
            r"(Views\s+This\s+Month)\s*[:：]?\s*[0-9][0-9,]*",
            r"\1 <dynamic-count>",
            normalized,
            flags=re.I,
        )
        normalized = re.sub(
            r"(Your\s+IP\s+Address)\s*[:：]?\s*(?:[0-9a-f:.]+)",
            r"\1 <dynamic-ip>",
            normalized,
            flags=re.I,
        )
    if host == "colab.moha.gov.vn":
        # COLAB's EPS notice index renders live visitor statistics in Vietnamese.
        # Normalize only the labelled statistics block so notice text remains hashed.
        for label in ("Trực tuyến", "Hôm nay", "Tháng này", "Tổng số"):
            normalized = re.sub(
                rf"({label})\s*[:：]?\s*[0-9][0-9,.]*",
                rf"\1 <dynamic-count>",
                normalized,
                flags=re.I,
            )
    # KP2MI detail pages render: HH.MM DD Month YYYY <view-count> TITLE...
    normalized = re.sub(
        r"(\b\d{2}\.\d{2}\s+\d{1,2}\s+[A-Za-z]+\s+\d{4})\s+[0-9][0-9,]*\b",
        r"\1 <dynamic-count>",
        normalized,
    )
    # KP2MI footer prints Total Visitors as space-separated digits.
    normalized = re.sub(
        r"(Total\s+Visitors)\s+(?:\d\s*){3,}",
        r"\1 <dynamic-total>",
        normalized,
        flags=re.I,
    )
    return normalized

def fetch_fingerprint(url, tls_pins=None):
    raw, content_type, charset, final_url, tls_mode = _fetch_response(url, tls_pins or {})

    if content_type == "application/pdf" or final_url.lower().split("?", 1)[0].endswith(".pdf"):
        return {
            "sha256": hashlib.sha256(raw).hexdigest(),
            "contentLength": len(raw),
            "mode": "binary",
            "contentType": content_type or "application/pdf",
            "tlsMode": tls_mode,
        }

    html = raw.decode(charset, errors="replace")
    extractor = TextExtractor()
    extractor.feed(html)
    normalized = normalize_source_text(" ".join(extractor.parts), final_url)
    return {
        "sha256": hashlib.sha256(normalized.encode("utf-8")).hexdigest(),
        "contentLength": len(normalized),
        "mode": "normalized_text",
        "contentType": content_type or "text/html",
        "tlsMode": tls_mode,
    }

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--sources", default="monitor/sources.json")
    p.add_argument("--baseline", default="monitor/source_hashes.json")
    p.add_argument("--output", default="monitor/check_result.json")
    p.add_argument("--tls-pins", default="monitor/tls_pins.json")
    p.add_argument("--accept-current", action="store_true")
    p.add_argument("--review-manifest", default=None, help="Optional one-time reviewed acceptance manifest")
    p.add_argument("--init-if-empty", action="store_true")
    p.add_argument("--workers", type=int, default=4, help="Concurrent source fetches across independent hosts (1-8)")
    p.add_argument("--per-host", type=int, default=1, help="Maximum concurrent fetches to the same canonical host (1-3)")
    p.add_argument("--retries", type=int, default=3, help="Attempts for transient network failures (1-3)")
    args = p.parse_args()
    workers = max(1, min(args.workers, 8))
    per_host = max(1, min(args.per_host, 3))
    attempts = max(1, min(args.retries, 3))

    sources = json.loads(Path(args.sources).read_text(encoding="utf-8-sig"))["sources"]
    tls_pins_path = Path(args.tls_pins)
    tls_pins = json.loads(tls_pins_path.read_text(encoding="utf-8-sig")) if tls_pins_path.exists() else {"hosts": {}}
    baseline_path = Path(args.baseline)
    baseline = json.loads(baseline_path.read_text(encoding="utf-8-sig")) if baseline_path.exists() else {}

    fingerprints = {}
    failure_by_id = {}

    def canonical_host(url):
        host = (urlparse(url).hostname or "").lower()
        if host.startswith("www."):
            host = host[4:]
        return host

    fragile_hosts = {"kp2mi.go.id"}
    host_gates = {
        canonical_host(source["url"]): Semaphore(
            1 if canonical_host(source["url"]) in fragile_hosts else per_host
        )
        for source in sources
    }
    host_last_request = {}

    def fetch_source(source):
        url = source["url"]
        host = canonical_host(url)
        last_error = None
        with host_gates[host]:
            for attempt in range(1, attempts + 1):
                if host in fragile_hosts:
                    elapsed = time.monotonic() - host_last_request.get(host, 0.0)
                    min_gap = 1.25 if attempt == 1 else 2.0 * attempt
                    if elapsed < min_gap:
                        time.sleep(min_gap - elapsed)
                try:
                    result = fetch_fingerprint(url, tls_pins)
                    host_last_request[host] = time.monotonic()
                    return source["id"], result
                except Exception as exc:
                    host_last_request[host] = time.monotonic()
                    last_error = exc
                    if "CERTIFICATE_VERIFY_FAILED" in str(exc) or attempt >= attempts:
                        break
                    time.sleep(1.5 * attempt)
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
            "tlsMode": fingerprint.get("tlsMode", "ca_verified"),
        }

    changed = []
    for source_id, now in current.items():
        before = baseline.get(source_id)
        if not before:
            changed.append({
                "id": source_id,
                "agency": now["agency"],
                "url": now["url"],
                "before": None,
                "after": now["sha256"],
                "reason": "new_unbaselined_source",
            })
            continue
        old_hash = before.get("sha256")
        old_url = before.get("url")
        hash_changed = old_hash != now["sha256"]
        url_changed = old_url != now["url"]
        if hash_changed or url_changed:
            reason = (
                "source_url_and_content_changed" if hash_changed and url_changed else
                "source_url_changed" if url_changed else
                "content_changed"
            )
            changed.append({
                "id": source_id,
                "agency": now["agency"],
                "url": now["url"],
                "before": old_hash,
                "after": now["sha256"],
                "beforeUrl": old_url,
                "afterUrl": now["url"],
                "reason": reason,
            })

    review_manifest_accepted = False
    review_manifest_id = None
    if args.review_manifest:
        manifest_path = Path(args.review_manifest)
        if manifest_path.exists() and changed and not failures:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
            expected_ids = set(manifest.get("expectedChangedSourceIds", []))
            changed_ids = {row.get("id") for row in changed if row.get("id")}
            expected_hashes = manifest.get("expectedBaselineSha256", {})
            expected_new_hashes = manifest.get("expectedNewSourceSha256", {})
            expected_current_hashes = manifest.get("expectedCurrentSha256", {})
            changed_by_id = {row.get("id"): row for row in changed if row.get("id")}
            baseline_ids = set(expected_hashes)
            new_ids = set(expected_new_hashes)
            partition_matches = (
                not (baseline_ids & new_ids)
                and (baseline_ids | new_ids) == expected_ids
            )
            baseline_matches = all(
                baseline.get(source_id, {}).get("sha256") == expected_hashes.get(source_id)
                for source_id in baseline_ids
            )
            new_sources_match = all(
                source_id not in baseline
                and changed_by_id.get(source_id, {}).get("reason") == "new_unbaselined_source"
                and changed_by_id.get(source_id, {}).get("after") == expected_new_hashes.get(source_id)
                for source_id in new_ids
            )
            reviewed_new_sources_allowed = (
                not new_ids
                or manifest.get("safety", {}).get("allowReviewedNewSources") is True
            )
            require_current_hashes = manifest.get("safety", {}).get("requireExactCurrentHashes") is True
            current_hashes_match = (
                not require_current_hashes
                or (
                    set(expected_current_hashes) == baseline_ids
                    and all(
                        changed_by_id.get(source_id, {}).get("after") == expected_current_hashes.get(source_id)
                        for source_id in baseline_ids
                    )
                )
            )
            manifest_matches = (
                manifest.get("active") is True
                and manifest.get("normalizationRevision") == NORMALIZATION_REVISION
                and manifest.get("safety", {}).get("requireNoFetchFailures") is True
                and manifest.get("safety", {}).get("requireExactChangedSourceSet") is True
                and manifest.get("safety", {}).get("requireExactBaselineHashes") is True
                and manifest.get("safety", {}).get("oneTimeByBaselineHash") is True
                and changed_ids == expected_ids
                and partition_matches
                and baseline_matches
                and new_sources_match
                and reviewed_new_sources_allowed
                and current_hashes_match
            )
            if manifest_matches:
                review_manifest_accepted = True
                review_manifest_id = manifest.get("reviewId")

    initialized = False
    accepted = False
    partial_acceptance = False
    acceptance_blocked = False
    accepted_source_ids = []
    preserved_failure_source_ids = []
    complete_fetch = len(current) == len(sources) and not failures

    if args.init_if_empty and not baseline and current:
        # Initial baseline must be complete so that no source begins life silently untracked.
        if complete_fetch:
            baseline_path.write_text(json.dumps(current, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            initialized = True
            changed = []
        else:
            acceptance_blocked = True

    if args.accept_current or review_manifest_accepted:
        # Manual review may approve the sources that were fetched successfully while
        # preserving the last reviewed fingerprint for unrelated temporary failures.
        # Failed sources are never overwritten or treated as reviewed.
        if current:
            merged = dict(baseline)
            merged.update(current)
            baseline_path.write_text(json.dumps(merged, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            accepted = True
            partial_acceptance = not complete_fetch
            accepted_source_ids = sorted(current.keys())
            preserved_failure_source_ids = sorted(x["id"] for x in failures if x.get("id"))
        else:
            acceptance_blocked = True

    result = {
        "initialized": initialized,
        "acceptedCurrent": accepted,
        "reviewManifestAccepted": review_manifest_accepted,
        "reviewManifestId": review_manifest_id,
        "normalizationRevision": NORMALIZATION_REVISION,
        "partialAcceptance": partial_acceptance,
        "acceptanceBlocked": acceptance_blocked,
        "acceptedSourceIds": accepted_source_ids,
        "preservedFailureSourceIds": preserved_failure_source_ids,
        "changed": changed,
        "failures": failures,
        "checked": len(current),
        "configured": len(sources),
        "workers": workers,
        "perHost": per_host,
        "attempts": attempts,
        "pinnedFallbacks": [source_id for source_id, row in current.items() if row.get("tlsMode") == "pinned_leaf"],
        "curlCaVerifiedFallbacks": [source_id for source_id, row in current.items() if row.get("tlsMode") == "curl_ca_verified"],
    }
    Path(args.output).write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False))
    if not current:
        return 2
    return 0

if __name__ == "__main__":
    sys.exit(main())
