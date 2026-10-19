# KEP M17 — GitHub Pages Deployment Source Diagnosis (READ ONLY)

**Observed:** 2026-10-16 KST. **Product:** Indonesia → E-9 → General Manufacturing. **Beta:** HOLD.

## Confirmed cause of the apparent 0/9 Pages parity failure

An authenticated read-only `gh api .../pages` call confirmed that public GitHub Pages publication uses **source `main` / `/docs`**, build type **`legacy`**, publishing status **`built`**, and **HTTPS enforced**.

| Compared ref | SHA at inspection | Live critical asset content matches |
|---|---|---|
| Published source `origin/main` | `29fde41e697814154e4ebfba2a53ef3a56dbf8b7` | **9/9** |
| Development Draft PR #324 HEAD | `7d4f44475a4b66dca4c624dbe87e9b6dde92d17f` | **0/9** |

The nine public assets return HTTP 200. Independent per-asset GET requests with new cache-busting query keys had no stale Age (`Age: 0`) and each file exactly matched the committed **main** Git blob, but none matched the unmerged Draft PR. This is an **expected unpublished candidate**, not evidence that GitHub Pages failed to update its currently configured `main` source. No attempt was made to purge caches, change publication settings, force-push, merge the Draft PR, or publish the candidate.

Existing read-only HTTPS check: six known legacy redirects remain HTTPS-only (6/6), while approved-candidate same-HEAD file parity is correctly **NOT VERIFIED (0/9)**. Production code QA (previous Edge 96/96) applies to the candidate branch only, NOT to public deployed `main`.

## Permanent checks added in M17

- `scripts/diagnose_indonesia_beta_pages_source.py`: reads current GitHub Pages settings using the existing authorized GitHub CLI **GET** endpoint, verifies remote `main` SHA matches locally referenced `origin/main`, compares nine HTTPS live assets with both `main` and current candidate HEAD, and returns a precise status: `DEPLOYED_MAIN_DRAFT_HEAD_NOT_PUBLISHED` versus unexpectedly diverged files. Seven synthetic fail-closed checks protect source mismatch, missing asset, Git-ref mismatch, HTTPS not enforced and manual release separation. It has **no deployment capabilities**.
- `scripts/audit_indonesia_beta_pages_live.py`: each audit invocation now uses a fresh UTC cache-buster, rather than the former static `?kep_audit=20261014` value; existing HTTPS and live candidate SHA checks remain fail-closed.
- Local live probe on this development HEAD: `DEPLOYED_MAIN_DRAFT_HEAD_NOT_PUBLISHED`, 9/9 exact deployed main and 0/9 candidate; operator beta remains **HOLD**.

## Release decision and safe sequence

1. Continue original official-source human review and current 2026 General Manufacturing notice/attachment signoff. `job_docs` remains HOLD. Do not accept SHA changes by digest alone.
2. Once explicitly authorized, review PR #324, confirm source and product safety checks, choose a release commit and merge/release deliberately into the configured GitHub Pages source `main`/`docs` (or use an independently approved deployment procedure). **DO NOT change Pages publishing branch to the unreviewed Draft feature branch.**
3. After GitHub Pages publication is independently confirmed, re-run `python scripts/diagnose_indonesia_beta_pages_source.py --live` and `python scripts/audit_indonesia_beta_pages_live.py`. Require the approved HEAD to match all **9/9 critical assets** and all **6/6 legacy HTTPS redirects**. At present this gate **remains PENDING**.
4. Only after remaining source, live deployment and applicant safety gates pass, obtain a separate explicit responsible operator `beta OPEN` decision. Do not auto-open or contact beta applicants.

**M17 changes DO NOT deploy, merge, accept source facts, send GitHub #325 alerts, mutate applicant data or change public beta settings.**
