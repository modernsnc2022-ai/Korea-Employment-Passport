# Indonesia beta: public Pages HTTPS and exact-asset audit — 2026-10-14

## Scope and authorization

Read-only inspection of the already-public Korea Employment Passport Pages site, authenticated **read-only** GitHub Pages configuration queries, and the source Git branches. No official-source baseline was accepted, no owner Pages setting changed, no PR merged, no public deployment made, no applicant or worker activated, and no beta status changed. Current `docs/data/beta_program_v1.json.status` remains `hold`.

## Critical HTTPS downgrade (reproduced independently)

1. `GET https://modernsnc2022-ai.github.io/Korea-Employment-Passport/app.html` **HTTP 301** with `Location: http://www.gdglobal.kr/Korea-Employment-Passport/app.html`.
2. `GET https://www.gdglobal.kr/Korea-Employment-Passport/app.html` returns **HTTP 200 under valid HTTPS**.
3. `GET https://gdglobal.kr/Korea-Employment-Passport/app.html` redirects to HTTPS `www.gdglobal.kr`; direct HTTP `www.gdglobal.kr` also responds with HTTP 200.
4. The `github.io` root also redirects to **HTTP** `www.gdglobal.kr`. The downgrade affects previously shared `github.io` recruitment links and is not resolved solely by having a working direct HTTPS alternative.

Authorized `gh api` read-only check:
- `repos/modernsnc2022-ai/modernsnc2022-ai.github.io/pages`: `cname=www.gdglobal.kr`, `https_certificate.state=approved`, **`https_enforced=false`**, `status=built`, `html_url=http://www.gdglobal.kr/`.
- `repos/modernsnc2022-ai/Korea-Employment-Passport/pages`: `https_enforced=false`, `status=built`, `html_url=http://www.gdglobal.kr/Korea-Employment-Passport/`.

**Launch blocker:** existing campaign links follow an HTTPS → HTTP first hop, permitting downgrade to an unencrypted origin. The user/operator must explicitly authorize the relevant GitHub Pages **Enforce HTTPS** setting(s), checking the organization-wide shared custom-domain impact first. No setting was toggled in this audit. Recheck every old campaign URL after authorized HTTPS enforcement and ensure the first redirect remains HTTPS throughout.

## Code deployment identity: production is correct for main, not yet beta draft

Git main was fetched read-only. Current `origin/main` commit:
`29fde41e697814154e4ebfba2a53ef3a56dbf8b7`.

Exact public **HTTPS** response-byte comparison against committed Git blobs:

| Comparison | Critical assets matching (of 9) | Meaning |
|---|---:|---|
| `https://www.gdglobal.kr/Korea-Employment-Passport/` ↔ `origin/main` | **9/9** | Current production content matches intended `main`; not a failed or partial main deployment |
| Public HTTPS origin ↔ current Indonesia Draft PR #324 | **1/9** | Draft's latest content has **not been merged or deployed**; the common matching asset is `beta_program_v1.json` showing `hold` |

Critical files: `index.html`, `app.html`, `app-runtime.js`, `sw.js`, `data/id_e9_manufacturing_2026.json`, `data/id_e9_manufacturing_2026_id.json`, `data/exact_answer_rules_v1.json`, `data/source_review_status.json`, and `data/beta_program_v1.json`.

At audit time, public `sw.js` was `kep-v124`; the improved Draft includes `kep-v132` following secure-link meta updates. The fact that the Draft's nine files are not live is **expected while PR #324 is Draft/unmerged** and must not be mislabeled as a deployment outage.

## New fail-closed Pages auditing code and communication safeguards

- `scripts/audit_indonesia_beta_pages_live.py`: read-only first-hop redirect audit and **exact committed-Git-blob** comparison of nine critical public HTTPS assets; uses no GitHub Actions or state changes. Required, because Windows `core.autocrlf` may change checkout bytes without changing the committed content.
- `--self-test` checks a valid setup, downgrade to HTTP, unexpected HTTPS redirect host, and a stale `sw.js`. A live mismatch exits nonzero; **its PASS does not approve beta** or substitute for source review, actual Pages workflow evidence or user release decision.
- `docs/index.html` social sharing OG URL updated in the Draft to the **verified directly secure** `https://www.gdglobal.kr/Korea-Employment-Passport/` origin; `docs/sw.js` cache is `kep-v132`; `tests/indonesia-extra-audit.spec.js` checks secure OG metadata and the cache version.
- `recruitment/OUTREACH_ID.md` uses direct HTTPS custom-domain links for **future** source-attributed outreach. Preserve historical sent-message text but avoid newly copying stale insecure `github.io` links until the redirect is fixed; use only allowlisted non-identifying `src` codes.
- `recruitment/BETA_LAUNCH_GATE.md` now explicitly blocks OPEN on an HTTPS-to-HTTP hop or missing deployment parity.

## Operational next steps (owner approval required for production-impacting changes)

1. Check mixed-content impact of enabling **Enforce HTTPS** in both the Pages-project repository and the `modernsnc2022-ai.github.io` organization Pages site; the latter shares the `www.gdglobal.kr` domain beyond KEP.
2. After explicit owner authorization, enable the needed HTTPS enforcement through GitHub Pages settings, then verify all old `github.io` links reach **HTTPS** with no downgrade and the direct custom origin serves normally.
3. Finish current-day KP2MI Manufacturing list and human signature plus Indonesia/Korea source-scope manual signature. Preserve `job_docs` exact HOLD until cohort-specific evidence exists.
4. On the intended release HEAD, repeat strict app static checks and 320px/full browser QA; obtain same-HEAD Pages build/deployment evidence, independently run nine-asset audit, **then** record the explicit authorized beta OPEN. Do not activate tester IDs early.

**Current release state:** beta interest intake OPEN; actual access HOLD; Draft PR #324 unmerged; no owner settings changed and no GitHub Actions usage. This evidence is specific to 2026-10-14 and must be refreshed if live Pages configuration changes.
