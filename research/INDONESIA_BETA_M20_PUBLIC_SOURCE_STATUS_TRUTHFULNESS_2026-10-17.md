# Korea Employment Passport — M20 Source-Status UI Truthfulness & Launch HOLD

**Date:** 2026-10-17 (Indonesia-local official watch).
**Scope:** Indonesia → Korea → E-9 → General Manufacturing 2026.
**Branch:** Draft PR #324, candidate not merged or publicly deployed.
**Status:** technical data-display changes only; **NO human official source signoff, NO beta OPEN**.

## Problem resolved

The existing `docs/data/source_review_status.json` faithfully recorded a 2026-10-14 **83/84** monitoring run, one then-failing Nepal EPS page, and **8** review alerts. The independent **2026-10-17** live machine monitoring later fetched **84/84** with **0** fetch failures and found **12** SHA differences **versus the last manually accepted baseline** (5 Korea-common, 2 multi-country HRD EPS, 5 other-country). Replacing the historical record with new numbers would falsify the original history, and treating successful fetching as human acceptance would be unsafe.

## Changes

- `scripts/publish_m20_readonly_source_visibility.py`: verifies the real October 17 machine-observed evidence against configured monitor URLs and the accepted SHA baseline, preserves every historical key/value pair, and additively records `latestReadOnlyObservation` with date, 84/84 fetch, 0 failures, 12 pending SHA differences, four scope categories, official source IDs/URLs, `humanSemanticReviewApproved=false`, `hashBaselineAutoAccepted=false`, `exactManufacturingJobDocuments=hold`, `betaAccess=hold`, `authorizesRelease=false`. Refuses changed historical records or different preexisting observations.
- `docs/data/source_review_status.json`: historical 2026-10-14 `checked=83`, `fetchFailureSourceIds=["np_eps_notice_index"]` and eight prior review IDs remain unchanged; the latest unsigned observation is **separate**, not a new accepted baseline.
- `docs/app-runtime.js`: app trust panel explicitly differentiates "**Pemantauan teknis 2026-10-17: 84/84**" from older 2026-10-14 83/84; shows 12 pending unapproved fingerprint differences with 5/2/5 scope, and unequivocally says manual approval, exact final Manufacturing `job_docs`, and beta remain **HOLD**. Exact Answer source protection uses the union of historical + latest pending source URLs; verified current 0-failure scan does not reuse the older Nepal failure as a current error. Malformed or forged latest evidence fails closed to warning and blocks ALL source-dependent exact answers.
- `docs/sw.js`: candidate service-worker cache revision bumped to `kep-v138` so **an eventual separately authorized deployment** can refresh source-status assets. **No deploy performed.**
- `scripts/check_beta_launch_readiness.py`: static checker requires the additive display to match the retained dated and unsigned original snapshot exactly, and labels the **historic 83/84** and **latest 84/84** separately in its console output. The release guard still maintains `PRODUCT_CI_SOURCE_HOLD`.
- `scripts/test_m20_source_visibility_ui.js`: executes shipped app render/trust helpers via Node VM without any network or browser telemetry, asserting Indonesian text, prior vs latest date, 12 pending scope counts, historical failure handling and nine hostile mutated source-status cases.

## Test expectations and observed safety

- Pure metadata evidence does **NOT** resolve outstanding manual semantic approval of five Korea-common, two multi-country HRD, or five other-country sources.
- `job_docs` final 2026 General Manufacturing online registration file list remains **HOLD**, even though the KP2MI headline inventory was fetched.
- The standalone beta form's **interest intake** can remain open independently of access to the beta product; this code does not change either state.
- Historical `sources=83/84` in earlier QA logs represented the **archived** 2026-10-14 dataset; M20 explicitly labels both dates. The Oct 17 machine read-only observation is **not** a new accepted policy decision.

## Follow-up required

A real authorized reviewer must inspect the original relevant official HTML/PDF annexes and sign sources on the correct release day. Only then may a separately approved candidate SHA be merged/deployed and verified (9/9 candidate assets, 6/6 HTTPS redirects). Explicit beta OPEN remains a separate operator decision.

**No production deployment, main merge, source-hash acceptance, test recruitment message, or GitHub Actions run was performed in this M20 work.**
