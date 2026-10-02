#!/usr/bin/env python3
import argparse
import hashlib
import json
import re
import sys
import urllib.request
from html.parser import HTMLParser
from pathlib import Path

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

def fetch_text(url):
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Korea-Employment-Passport-SourceMonitor/1.0 (+GitHub Actions)",
            "Accept-Language": "ko,en;q=0.8,id;q=0.7",
        },
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        raw = resp.read()
        charset = resp.headers.get_content_charset() or "utf-8"
    html = raw.decode(charset, errors="replace")
    extractor = TextExtractor()
    extractor.feed(html)
    normalized = re.sub(r"\s+", " ", " ".join(extractor.parts)).strip()
    return normalized

def digest(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--sources", default="monitor/sources.json")
    p.add_argument("--baseline", default="monitor/source_hashes.json")
    p.add_argument("--output", default="monitor/check_result.json")
    p.add_argument("--accept-current", action="store_true")
    p.add_argument("--init-if-empty", action="store_true")
    args = p.parse_args()

    sources = json.loads(Path(args.sources).read_text(encoding="utf-8"))["sources"]
    baseline_path = Path(args.baseline)
    baseline = json.loads(baseline_path.read_text(encoding="utf-8")) if baseline_path.exists() else {}

    current = {}
    failures = []
    for source in sources:
        try:
            text = fetch_text(source["url"])
            current[source["id"]] = {
                "sha256": digest(text),
                "agency": source["agency"],
                "url": source["url"],
                "textLength": len(text),
            }
        except Exception as exc:
            failures.append({"id": source["id"], "url": source["url"], "error": str(exc)})

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
    if (args.init_if_empty and not baseline and current) or args.accept_current:
        baseline_path.write_text(json.dumps(current, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        initialized = not baseline
        accepted = args.accept_current

    result = {
        "initialized": initialized,
        "acceptedCurrent": accepted,
        "changed": changed,
        "failures": failures,
        "checked": len(current),
        "configured": len(sources),
    }
    Path(args.output).write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False))
    if not current:
        return 2
    return 0

if __name__ == "__main__":
    sys.exit(main())
