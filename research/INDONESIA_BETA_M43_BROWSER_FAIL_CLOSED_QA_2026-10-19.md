# Korea Employment Passport M43 — Official source fail-closed and Chromium regression repair

**Date:** 2026-10-19 KST
**Base code commit:** `336edace3630a21062db52b93f662b866761fb89` (M42)
**Draft PR:** #324; Indonesia → E-9 → General Manufacturing → 2026
**Release:** HOLD. No manual approval, merger, production deployment or public beta activation.

## Root cause of all 15 M42 browser failures

The 15 failing cases were reproduced on the previous code (98 total, 83 pass/15 fail). Four were in `tests/indonesia-extra-audit.spec.js`: legacy 2026-10-14 eight-alert counts conflicted with the newer technical-only 12-alert observation; the expected service worker cache v137 was obsolete (actual v140); and a synthetic unexpected historical source ID was not rejected by the newer evidence adapter. Eleven were in `tests/ui.spec.js`: the test fixture fabricated a `clean` or single-source `review_required` root status but left a mutually inconsistent `latestReadOnlyObservation` attached. The app correctly opened its invalid-evidence trust warning and withheld controlled official document guidance; these test expectations were invalid.

## Real product hardening, without weakening HOLD

1. `docs/app-runtime.js`: require every historical source-ID/URL pair to be contained in the latest read-only technical observation under the same normalized URL. Unknown/modified historical evidence produces `BUKTI PEMANTAUAN TIDAK VALID`, opens the warning panel and suppresses official-source-dependent guidance until validated, instead of silently trusting a stale later snapshot. This complements the existing 84/84, 12 source alerts, schema, timestamp, unaccepted drift, no human approval, no auto-accept and beta HOLD checks.
2. `docs/sw.js`: advance offline cache version v140 → v141 so new current-copy and runtime are picked up after the candidate is eventually deployed.
3. `tests/ui.spec.js`: isolate deliberately synthetic verified and one-source-review fixtures from the real 12-alert read-only observation. This is test-only and does not alter real policy evidence.
4. `tests/indonesia-extra-audit.spec.js`: assert immutable historic 83/84 and current 84/84/12-alert technical-only properties, human approval false, hash acceptance false, final job documents HOLD, beta HOLD, and reject a newly unrecognized historical source through the stronger invalid-evidence path. Validate a versioned cache rather than a permanently fixed old version.

## Verification, actually executed on local Windows PC

- Baseline M42 full Chromium run: **83/98 pass, 15 fail**, exit 1. Local log `D:\KEP-M42-FULL-CHROMIUM-20261019.log`.
- M43 previously failing 15 scenarios: **15/15 PASS**, exit 0 on isolated port `42893`, 29.4 seconds. Local log `D:\KEP-M43-TARGET15-20261019.log`.
- M43 all Chromium tests: **98/98 PASS**, exit 0 on isolated port `42894`, 3.2 minutes. Local log `D:\KEP-M43-FULL-CHROMIUM-20261019.log`.
- Web contract: `WEBAPP_CONTRACT_PASS` (27 stages, 308 exact answers), exit 0.
- Country-pack contract: `COUNTRY_PACK_CONTRACT_PASS`, 16 routes, exit 0.
- `report_indonesia_beta_release_preflight.py --self-test`: `ID_BETA_RELEASE_PREFLIGHT_SELF_TEST_PASS`, exit 0; exact final `job_docs` still mandatory.
- `set_beta_release.py --self-test`: `BETA_RELEASE_STATE_SELF_TEST_PASS`, exit 0; no false same-HEAD deployment proof or fake beta OPEN.
- `git diff --check`: exit 0.

## Release gates and next

**M41's last real current-day preflight remains** 11 launch gates: 6 PASS / 5 PENDING. This M43 test pass does not substitute for:
- Exact 2026 Indonesian General Manufacturing *post-Skill-Test final online job application* notice, annex, required vs optional documents and accountable human signoff.
- 20 unsigned human review tasks, including 12 changed-source fingerprint alerts and manufacturing notices.
- New candidate same-HEAD public deployment, HTTPS 6/6 and asset parity 9/9, with explicit separate approval.
- Operator manual beta OPEN.

Real interest registration remains OPEN, while final Manufacturing job_docs, direct official submission and public beta access remain HOLD. No policy baseline SHA promotion; no GitHub Actions or Production deployment. Next milestone: M44 review outstanding user-facing Indonesia workflow quality and prepare human source-review packet without authorizing a release.
