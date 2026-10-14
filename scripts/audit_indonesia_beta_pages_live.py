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
            }
    except HTTPError as error:
        # urllib represents blocked redirects as HTTPError; the first hop is
        # still evidence and must NOT be followed, especially into HTTP.
        return {
            "status": error.code, "location": error.headers.get("Location"),
            "finalUrl": url, "body": b"",
        }


def scheme_safe(target: str) -> bool:
    return urlsplit(target).scheme == "https"


def audit(fetch, docs: Path, revision: str) -> dict:
    first_url = PUBLIC + "app.html?kep_audit=20261014"
    report = {
        "version": "1.0.0", "mode": "read_only",
        "checkedRef": revision, "authorizesRelease": False,
        "canonical": PUBLIC, "directHttps": CUSTOM, "assets": [],
    }
    try:
        first = fetch(first_url)
        location = first.get("location")
        final_target = urljoin(first_url, location) if location else first.get("finalUrl", first_url)
        redirect_ok = (first.get("status") == 200 and scheme_safe(first.get("finalUrl", first_url))) or (
            first.get("status") in (301, 302, 307, 308)
            and bool(location) and scheme_safe(final_target)
        )
        report["entrypoint"] = {
            "httpStatus": first.get("status"),
            "redirectTarget": final_target if location else None,
            "httpsOnly": bool(redirect_ok),
        }
    except (OSError, ValueError, URLError) as exc:
        report["entrypoint"] = {"httpsOnly": False, "error": type(exc).__name__ + ": " + str(exc)[:200]}

    for name in ASSETS:
        local = docs / name
        if not local.is_file():
            report["assets"].append({"path": name, "sameAsCheckedRef": False, "error": "missing local asset"})
            continue
        expected = local.read_bytes()
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

        def build_fake(*, downgrade: bool = False, stale: bool = False):
            def get(url: str) -> dict:
                if "github.io" in url:
                    return {"status": 301, "location": (
                        ("http://" if downgrade else "https://") + "www.gdglobal.kr/Korea-Employment-Passport/app.html"
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
        old_assets = audit(build_fake(stale=True), docs, "self-test-sha")
        assert old_assets["criticalAssetsSameRef"] is False
        assert old_assets["matchingAssets"] == len(ASSETS) - 1
        assert old_assets["readyForSeparateOperatorDeployReview"] is False
        assert all(not x["authorizesRelease"] for x in (passing, insecure, old_assets))
        print("ID_PAGES_LIVE_PARITY_SELF_TEST_PASS https_downgrade_and_stale_assets_fail_closed")


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
    result = audit(http_first_hop, ROOT / "docs", revision)
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(
            f"ID_PAGES_LIVE_AUDIT sha={revision[:12]} "
            f"httpsSafe={result['httpsEntrypointSafe']} "
            f"fileParity={result['matchingAssets']}/{result['totalAssets']} "
            f"readyForSeparateOperatorDeployReview={result['readyForSeparateOperatorDeployReview']}"
        )
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
