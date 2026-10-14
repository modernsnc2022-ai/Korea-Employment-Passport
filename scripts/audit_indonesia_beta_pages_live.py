#!/usr/bin/env python3
"""Read-only live Pages security + critical asset parity check for Indonesia beta.

Does not deploy, write to the website, change Pages settings, or sign a release.
HTTP downgrade from a published HTTPS campaign URL is a release blocker.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin, urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

ROOT = Path(__file__).resolve().parents[1]
PUBLIC = "https://modernsnc2022-ai.github.io/Korea-Employment-Passport/"
CUSTOM = "https://www.gdglobal.kr/Korea-Employment-Passport/"
LEGACY_ENTRYPOINTS = (
    ("org_root", "https://modernsnc2022-ai.github.io/", "https://www.gdglobal.kr/"),
    ("kep_root", PUBLIC, CUSTOM),
    ("kep_home", PUBLIC + "index.html", CUSTOM + "index.html"),
    ("kep_app", PUBLIC + "app.html", CUSTOM + "app.html"),
    ("kep_beta", PUBLIC + "beta.html", CUSTOM + "beta.html"),
    ("old_campaign", PUBLIC + "?src=epstopik_indonesia",
     CUSTOM + "?src=epstopik_indonesia"),
)
ASSETS = (
    "index.html", "app.html", "app-runtime.js", "sw.js",
    "data/id_e9_manufacturing_2026.json",
    "data/id_e9_manufacturing_2026_id.json",
    "data/exact_answer_rules_v1.json",
    "data/source_review_status.json",
    "data/beta_program_v1.json",
)


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, message, headers, next_url):
        return None


def http_first_hop(url: str, *, max_bytes: int = 2_000_000) -> dict:
    opener = build_opener(NoRedirect)
    request = Request(url, headers={
        "User-Agent": "KEP-read-only-release-parity/1.0",
        "Cache-Control": "no-cache",
        "Accept-Encoding": "identity",
    })
    try:
        with opener.open(request, timeout=20) as response:
            raw = response.read(max_bytes + 1)
            if len(raw) > max_bytes:
                raise ValueError("oversized response")
            return {
                "status": response.status, "location": response.headers.get("Location"),
                "finalUrl": response.url, "body": raw,
                "cacheAge": response.headers.get("Age"),
                "cacheState": response.headers.get("X-Cache"),
            }
    except HTTPError as error:
        # urllib represents blocked redirects as HTTPError; the first hop is
        # still evidence and must NOT be followed, especially into HTTP.
        return {
            "status": error.code, "location": error.headers.get("Location"),
            "finalUrl": url, "body": b"",
            "cacheAge": error.headers.get("Age"),
            "cacheState": error.headers.get("X-Cache"),
        }


def scheme_safe(target: str) -> bool:
    return urlsplit(target).scheme == "https"


def audit(fetch, docs: Path, revision: str, *, asset_loader=None) -> dict:
    report = {
        "version": "1.1.0", "mode": "read_only",
        "checkedRef": revision, "authorizesRelease": False,
        "canonical": PUBLIC, "directHttps": CUSTOM,
        "entrypoints": [], "assets": [],
    }
    for label, url, expected_url in LEGACY_ENTRYPOINTS:
        try:
            first = fetch(url)
            location = first.get("location")
            target = urljoin(url, location) if location else first.get("finalUrl", url)
            got = urlsplit(target)
            expected = urlsplit(expected_url)
            # Check *the first hop*, not merely that a later HTTP->HTTPS hop
            # eventually reaches HTTPS. Also protect path + campaign source
            # code: dropping ?src causes user acquisition misattribution.
            correct_destination = (
                got.scheme == "https"
                and got.hostname == expected.hostname
                and got.path == expected.path
                and got.query == expected.query
            )
            safe = (
                first.get("status") in (301, 302, 307, 308)
                and bool(location) and correct_destination
            )
            report["entrypoints"].append({
                "id": label, "url": url,
                "status": first.get("status"),
                "target": target if location else None,
                "httpsOnly": bool(safe),
                "cacheAge": first.get("cacheAge"),
                "cacheState": first.get("cacheState"),
            })
        except (OSError, ValueError, URLError) as exc:
            report["entrypoints"].append({
                "id": label, "url": url, "httpsOnly": False,
                "error": type(exc).__name__ + ": " + str(exc)[:200],
            })
    # Historical singular field preserved for existing audit clients, but
    # now safely means *all* known legacy entrypoints must be secure.
    report["entrypoint"] = {
        "httpsOnly": all(row["httpsOnly"] for row in report["entrypoints"]),
        "verified": len(report["entrypoints"]),
    }

    for name in ASSETS:
        local = docs / name
        if not local.is_file():
            report["assets"].append({"path": name, "sameAsCheckedRef": False, "error": "missing local asset"})
            continue
        # Use the exact committed Git blob, not Windows checkout bytes:
        # core.autocrlf may rewrite LF to CRLF without changing HEAD.
        expected = asset_loader(name) if asset_loader is not None else local.read_bytes()
        if len(expected) > 2_000_000:
            report["assets"].append({"path": name, "sameAsCheckedRef": False, "error": "local asset oversized"})
            continue
        url = CUSTOM + name + "?kep_audit=20261014"
        try:
            got = fetch(url)
            status = got.get("status")
            location = got.get("location")
            final_url = got.get("finalUrl", url)
            good_https = scheme_safe(final_url) and (not location) and (
                urlsplit(final_url).hostname == "www.gdglobal.kr"
            )
            body = got.get("body", b"")
            same = status == 200 and good_https and body == expected
            record = {
                "path": name, "status": status, "httpsOnly": good_https,
                "sameAsCheckedRef": bool(same), "liveSha256": hashlib.sha256(body).hexdigest(),
                "expectedSha256": hashlib.sha256(expected).hexdigest(),
            }
            if name == "sw.js":
                record["liveCacheVersion"] = body.decode("utf-8", errors="replace").splitlines()[0] if body else None
                record["checkedCacheVersion"] = expected.decode("utf-8", errors="replace").splitlines()[0]
            if name == "data/beta_program_v1.json" and status == 200:
                record["liveBetaStatus"] = json.loads(body).get("status")
                record["checkedBetaStatus"] = json.loads(expected).get("status")
            if location:
                record["location"] = urljoin(url, location)
            report["assets"].append(record)
        except (OSError, ValueError, URLError, UnicodeError) as exc:
            report["assets"].append({
                "path": name, "sameAsCheckedRef": False,
                "error": type(exc).__name__ + ": " + str(exc)[:200],
            })

    report["matchingAssets"] = sum(row["sameAsCheckedRef"] for row in report["assets"])
    report["totalAssets"] = len(ASSETS)
    report["httpsEntrypointSafe"] = report["entrypoint"]["httpsOnly"]
    report["criticalAssetsSameRef"] = report["matchingAssets"] == len(ASSETS)
    report["readyForSeparateOperatorDeployReview"] = (
        report["httpsEntrypointSafe"] and report["criticalAssetsSameRef"]
    )
    report["betaAccessChanged"] = False
    return report


def self_test() -> None:
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        docs = Path(tmp)
        for name in ASSETS:
            p = docs / name
            p.parent.mkdir(parents=True, exist_ok=True)
            if name == "data/beta_program_v1.json":
                p.write_text('{"status":"hold"}', encoding="utf-8")
            else:
                p.write_text("safe file: " + name, encoding="utf-8")

        def build_fake(*, downgrade: bool = False, stale: bool = False,
                       insecure_entry: str | None = None, strip_campaign: bool = False):
            def get(url: str) -> dict:
                if "github.io" in url:
                    expected = next(dest for _, old, dest in LEGACY_ENTRYPOINTS if url == old)
                    use_http = downgrade or (insecure_entry is not None and insecure_entry in url)
                    if strip_campaign and "?src=" in expected:
                        expected = expected.split("?", 1)[0]
                    return {"status": 301, "location": (
                        ("http://" if use_http else "https://") + expected.split("://", 1)[1]
                    ), "finalUrl": url, "body": b""}
                path = url.split("/Korea-Employment-Passport/", 1)[1].split("?", 1)[0]
                body = (docs / path).read_bytes()
                if stale and path == "sw.js":
                    body = b"const CACHE='kep-old';"
                return {"status": 200, "location": None, "finalUrl": url, "body": body}
            return get

        passing = audit(build_fake(), docs, "self-test-sha")
        assert passing["readyForSeparateOperatorDeployReview"] is True
        insecure = audit(build_fake(downgrade=True), docs, "self-test-sha")
        assert insecure["httpsEntrypointSafe"] is False
        assert insecure["readyForSeparateOperatorDeployReview"] is False
        # Real-world bug: the campaign root is updated, but an *old app
        # deep link* still hits a 301 with Location: http://...
        deep_only = audit(build_fake(insecure_entry="/app.html"), docs, "self-test-sha")
        assert deep_only["httpsEntrypointSafe"] is False
        assert any(row["id"] == "kep_app" and not row["httpsOnly"] for row in deep_only["entrypoints"])
        missing_src = audit(build_fake(strip_campaign=True), docs, "self-test-sha")
        assert missing_src["httpsEntrypointSafe"] is False
        redirected_to_other_site = audit(
            lambda url: (
                {"status": 301, "location": "https://unrelated.example/app.html", "finalUrl": url, "body": b""}
                if "github.io" in url else build_fake()(url)
            ), docs, "self-test-sha"
        )
        assert redirected_to_other_site["httpsEntrypointSafe"] is False
        old_assets = audit(build_fake(stale=True), docs, "self-test-sha")
        assert old_assets["criticalAssetsSameRef"] is False
        assert old_assets["matchingAssets"] == len(ASSETS) - 1
        assert old_assets["readyForSeparateOperatorDeployReview"] is False
        assert all(not x["authorizesRelease"] for x in (passing, insecure, old_assets))
        assert len(passing["entrypoints"]) == len(LEGACY_ENTRYPOINTS)
        assert all(row["httpsOnly"] for row in passing["entrypoints"])
        print("ID_PAGES_LIVE_PARITY_SELF_TEST_PASS 6_legacy_entrypoints deep_link_downgrade campaign_code_and_stale_assets_fail_closed")


def main() -> None:
    cli = argparse.ArgumentParser()
    cli.add_argument("--self-test", action="store_true")
    cli.add_argument("--json", action="store_true")
    args = cli.parse_args()
    if args.self_test:
        self_test()
        return
    revision = subprocess.check_output(
        ["git", "-C", str(ROOT), "rev-parse", "HEAD"], text=True
    ).strip()
    def read_committed_asset(name: str) -> bytes:
        return subprocess.check_output(
            ["git", "-C", str(ROOT), "show", "HEAD:docs/" + name]
        )

    result = audit(http_first_hop, ROOT / "docs", revision, asset_loader=read_committed_asset)
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(
            f"ID_PAGES_LIVE_AUDIT sha={revision[:12]} "
            f"httpsSafe={result['httpsEntrypointSafe']} "
            f"legacyEntrySafe={sum(r['httpsOnly'] for r in result['entrypoints'])}/{len(result['entrypoints'])} "
            f"fileParity={result['matchingAssets']}/{result['totalAssets']} "
            f"readyForSeparateOperatorDeployReview={result['readyForSeparateOperatorDeployReview']}"
        )
        for entry in result["entrypoints"]:
            print(f"REDIRECT {entry['id']} status={entry.get('status', 'ERROR')} "
                  f"httpsOnly={entry['httpsOnly']} age={entry.get('cacheAge')} "
                  f"cache={entry.get('cacheState')} target={entry.get('target', '')}")
        for item in result["assets"]:
            print(
                f"{item['path']} status={item.get('status', 'ERROR')} "
                f"matches={item['sameAsCheckedRef']} "
                f"{item.get('error', '')}"
            )
        print("NO_RELEASE_NO_PAGES_CHANGE_NO_SOURCE_SIGNOFF")
    if not result["readyForSeparateOperatorDeployReview"]:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
