#!/usr/bin/env python3
"""M17 GitHub Pages deployment-source diagnostic. Strictly read-only.

Differentiates expected unpublished Draft-PR assets from accidental drift.
Does not change GitHub Pages settings, source approvals, beta OPEN, or Git.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from audit_indonesia_beta_pages_live import ASSETS, CUSTOM, http_first_hop

ROOT = Path(__file__).resolve().parents[1]
API = "https://api.github.com/repos/modernsnc2022-ai/Korea-Employment-Passport/pages"
EXPECTED_SOURCE = {"branch": "main", "path": "/docs"}


def git(*args: str) -> bytes:
    return subprocess.check_output(["git", "-C", str(ROOT), *args], timeout=20)


def git_ref_file(ref: str, path: str) -> bytes:
    return git("show", ref + ":docs/" + path)


def assess(pages: dict, assets: list[dict], main_sha: str, head_sha: str, remote_main_sha: str) -> dict:
    settings_match = (
        pages.get("source") == EXPECTED_SOURCE
        and pages.get("build_type") == "legacy"
        and pages.get("https_enforced") is True
        and pages.get("status") == "built"
        and pages.get("html_url", "").rstrip("/") == CUSTOM.rstrip("/")
    )
    all_valid = len(assets) == len(ASSETS) and {x.get("path") for x in assets} == set(ASSETS)
    main_matches = sum(x.get("sameAsMain") is True for x in assets)
    head_matches = sum(x.get("sameAsHead") is True for x in assets)
    trustworthy = settings_match and all_valid and main_sha == remote_main_sha
    if not trustworthy:
        state = "BLOCKED_UNVERIFIED_PAGE_SOURCE_OR_GIT_REFS"
    elif main_matches == len(ASSETS) and head_sha != main_sha:
        state = "DEPLOYED_MAIN_DRAFT_HEAD_NOT_PUBLISHED"
    elif main_matches == len(ASSETS) and head_sha == main_sha and head_matches == len(ASSETS):
        state = "DEPLOYED_MAIN_EQUALS_HEAD_ASSETS"
    else:
        state = "BLOCKED_UNEXPECTED_PUBLIC_ASSET_DRIFT"
    return {
        "mode": "read_only",
        "status": state,
        "sourceVerified": trustworthy,
        "deployedMainFilesMatched": main_matches,
        "candidateHeadFilesMatched": head_matches,
        "totalAssets": len(ASSETS),
        "mainRef": main_sha,
        "candidateRef": head_sha,
        "sourceBranch": pages.get("source", {}).get("branch") if isinstance(pages.get("source"), dict) else None,
        "sourceFolder": pages.get("source", {}).get("path") if isinstance(pages.get("source"), dict) else None,
        "sameRefDeploymentConfirmed": state == "DEPLOYED_MAIN_EQUALS_HEAD_ASSETS",
        "remoteChangesMade": False,
        "approvesBetaOpen": False,
        "sourceHashAccepted": False,
    }


def inspect_live() -> dict:
    # GitHub Pages settings can return HTTP 404 anonymously even for a
    # public repository; use the user's already-authorized read-only GH CLI.
    # No GitHub token value is printed, handled or persisted by this script.
    pages = json.loads(subprocess.check_output(
        ["gh", "api", "repos/modernsnc2022-ai/Korea-Employment-Passport/pages"],
        timeout=30, text=True))
    if not isinstance(pages, dict):
        raise ValueError("Invalid GitHub Pages source object")
    main_sha = git("rev-parse", "origin/main").decode().strip()
    head_sha = git("rev-parse", "HEAD").decode().strip()
    remote_lines = git("ls-remote", "origin", "refs/heads/main").decode().strip().splitlines()
    if len(remote_lines) != 1 or "\trefs/heads/main" not in remote_lines[0]:
        raise ValueError("Cannot verify live remote main")
    remote_main_sha = remote_lines[0].split("\t", 1)[0]
    data = []
    for asset in ASSETS:
        # A fresh per-run cache-buster isolates old probe URLs; no browser SW.
        token = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S%f")
        response = http_first_hop(CUSTOM + asset + "?m17_probe=" + token)
        body = response["body"]
        https_safe = (response.get("status") == 200 and not response.get("location")
                      and response.get("finalUrl", "").startswith(CUSTOM))
        main_blob = git_ref_file("origin/main", asset)
        head_blob = git_ref_file("HEAD", asset)
        data.append({
            "path": asset,
            "http": response.get("status"),
            "httpsSafe": bool(https_safe),
            "sameAsMain": bool(https_safe and main_blob == body),
            "sameAsHead": bool(https_safe and head_blob == body),
            "cacheAge": response.get("cacheAge"),
            "liveSha256": hashlib.sha256(body).hexdigest(),
            "mainSha256": hashlib.sha256(main_blob).hexdigest(),
            "headSha256": hashlib.sha256(head_blob).hexdigest(),
        })
    result = assess(pages, data, main_sha, head_sha, remote_main_sha)
    result["observedAtUtc"] = datetime.now(timezone.utc).isoformat()
    result["publicAssets"] = data
    return result


def self_test() -> None:
    pages = {
        "source": dict(EXPECTED_SOURCE), "build_type": "legacy",
        "https_enforced": True, "status": "built",
        "html_url": CUSTOM,
    }
    assets = [{"path": p, "sameAsMain": True, "sameAsHead": False} for p in ASSETS]
    actual = assess(pages, assets, "m" * 40, "h" * 40, "m" * 40)
    assert actual["status"] == "DEPLOYED_MAIN_DRAFT_HEAD_NOT_PUBLISHED"
    assert not actual["sameRefDeploymentConfirmed"] and not actual["approvesBetaOpen"]
    assert assess(pages, assets, "m" * 40, "h" * 40, "x" * 40)["status"].startswith("BLOCKED")
    assert assess({**pages, "source": {"branch": "feature", "path": "/docs"}}, assets,
                  "m" * 40, "h" * 40, "m" * 40)["status"].startswith("BLOCKED")
    assert assess({**pages, "https_enforced": False}, assets,
                  "m" * 40, "h" * 40, "m" * 40)["status"].startswith("BLOCKED")
    assert assess(pages, assets[:-1], "m" * 40, "h" * 40, "m" * 40)["status"].startswith("BLOCKED")
    missing = [dict(x) for x in assets]
    missing[0]["sameAsMain"] = False
    assert assess(pages, missing, "m" * 40, "h" * 40, "m" * 40)["status"] == "BLOCKED_UNEXPECTED_PUBLIC_ASSET_DRIFT"
    deployed = [{"path": p, "sameAsMain": True, "sameAsHead": True} for p in ASSETS]
    assert assess(pages, deployed, "m" * 40, "m" * 40, "m" * 40)["sameRefDeploymentConfirmed"]
    print("KEP_PAGES_SOURCE_DIAGNOSTIC_SELF_TEST_PASS 7_cases fail_closed_no_release")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return 0
    if not args.live:
        parser.error("Specify --live or --self-test; diagnostic is never an implicit network poll")
    if args.output and (args.output.suffix.lower() != ".json" or
                        ROOT.resolve() in args.output.resolve().parents):
        parser.error("Evidence JSON must be a file outside the repository (never modify source approval data)")
    result = inspect_live()
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("KEP_PAGES_SOURCE_READONLY", result["status"],
          "source=", result["sourceBranch"] + result["sourceFolder"] if result["sourceBranch"] else "unknown",
          "main=", str(result["deployedMainFilesMatched"]) + "/9",
          "candidate=", str(result["candidateHeadFilesMatched"]) + "/9",
          "candidateSha=", result["candidateRef"][:12], "NO_DEPLOY_NO_RELEASE")
    return 0 if result["status"] in ("DEPLOYED_MAIN_DRAFT_HEAD_NOT_PUBLISHED",
                                     "DEPLOYED_MAIN_EQUALS_HEAD_ASSETS") else 2


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, KeyError, subprocess.SubprocessError, json.JSONDecodeError) as exc:
        print("KEP_PAGES_SOURCE_DIAGNOSTIC_BLOCKED " + type(exc).__name__ + ": " + str(exc)[:250])
        raise SystemExit(2)
