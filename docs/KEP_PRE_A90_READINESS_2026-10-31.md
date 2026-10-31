# KEP pre-A90 readiness — 2026-10-31

## Technical evidence
- Current branch: `ux/country-preview-reading-layout-20261031`.
- Existing Playwright full suite: **170/170 PASS** in Edge/Chromium on 2026-10-31 (before the additional three pre-device tests).
- Added `tests/pre-device-readiness.spec.js` (three checks): preserves beta `hold`, source `review_required` and `autoPublishRules=false`; keyboard Enter/Space expansion of optional help at 320px and 390px; no horizontal overflow.
- Pre-device targeted collection: 32/33 PASS on first grouped run; `offline-cache.spec.js` timed out once in grouped run then **1/1 PASS on isolated retry**. Treat as intermittent/environment-sensitive; do not claim stable offline testing without more repetitions.
- No alternative Playwright WebKit/Firefox bundles found on connected Windows PC. Browser cross-engine coverage remains unverified; device/browser testing is not substituted by Chromium desktop viewport simulation.

## Release restrictions (do not override)
- Official source snapshot data remains `review_required` with no automatic rule publishing; the snapshot is dated 2026-10-14, not a same-day official semantic review.
- 2026 Indonesian manufacturing final post-Skill-Test job-document requirements: human original-source verification **PENDING**.
- Operator source signoff, approved candidate deployment parity, public beta authorization: **PENDING**.
- No GitHub Actions, production deployment, Pages branch change, or beta OPEN is authorized by this checklist.

## Tasks requiring A90 or responsible human
1. A90 Chrome/Edge first-time and returning-user flows, touch targets, keyboard, zoom, dialogs, offline reconnect, orientation, notifications where applicable.
2. Manual official-source and current-cycle manufacturing documents review with named accountable signoff.
3. Fresh approved release candidate parity and beta OPEN decision only after explicit approval.

This record distinguishes test automation from human signoff and real-device evidence.
