# KEP M44 — Applicant route-loading recovery (2026-10-19)

**Product scope:** Indonesia → E-9 → General Manufacturing → 2026
**Previous HEAD:** `891caf17daec07df1594825159808a9f8cc9b8ac` (M43)
**PR:** Draft #324; no merge, approval, production deployment or beta OPEN.

## User-facing defect and implementation

Before M44, a failure of any mandatory country-route JSON file ended with a static `routeMeta` error string. The page did not offer any way to retry from the app itself, leaving first-time Indonesian applicants unable to recover without manually reloading the browser. Meanwhile, unrelated navigation could still be visible despite incomplete data.

M44 changes:
- `docs/app.html`: add `routeLoadRecovery` alert panel in Bahasa Indonesia with `Coba muat lagi` retry button and an explicit warning not to infer any official files or submit final documents from an incomplete screen.
- `docs/app-runtime.js`: retry the existing `boot()` data-fetch/render pipeline on user action without resetting browser local progress. A single `bootInFlight` guard prevents concurrent repeated retries. During loading and after required data errors, hide incomplete route controls via `route-unavailable`; on successful load, restore full 27-stage journey. Error recovery never approves source semantics, exact job docs, or public beta.
- `docs/app-shell.css`: accessible focusable retry control and mobile-safe error panel styling; suppress half-loaded action tabs, document forms and stage controls until load succeeds.
- `docs/sw.js`: increment PWA cache key from `kep-v141` to `kep-v142`, to avoid stale assets after a separately approved future deployment.
- `tests/m44-route-load-recovery.spec.js`: three end-to-end regression cases: offline required country route fails closed after retry budget; user-initiated retry restores all 27 stages and retains existing local storage progress; persistent failure after repeated retry continues to block navigation and documents.

## Real local testing on 2026-10-19

- M44 new Playwright Chromium tests: **3/3 PASS**, exit 0; isolated local port 42895. Local evidence log `D:\KEP-M44-TARGET-20261019.log`.
- M44 complete Chromium suite: **101/101 PASS**, exit 0, 3.8 minutes, isolated port 42896. Local evidence log `D:\KEP-M44-FULL-CHROMIUM-20261019.log`.
- `python scripts/check_webapp_contract.py`: **PASS**, 222 IDs, 9 views, 27 Indonesian stages, 308 exact answers.
- `python scripts/check_country_pack_contract.py`: **PASS**, 16 country routes.
- `python scripts/report_indonesia_beta_release_preflight.py --self-test`: **PASS**, final 2026 Manufacturing post-Skill-Test job docs still mandatory; synthetic approvals cannot bypass HOLD.
- `python scripts/set_beta_release.py --self-test`: **PASS**, same-HEAD/approval forgery stays blocked.
- JavaScript syntax and `git diff --check`: **PASS**.

These tests are technical checks of the local Draft candidate only. They are not a production deploy verification or an institution's endorsement. The public `main/docs` does not thereby contain this code.

## Immutable release HOLD and next

The last fully verified M41 launch gate classification remains **11 gates: 6 PASS / 5 PENDING**. Technical source observation 84/84 and KP2MI headline index checking do not constitute human semantic signoff. Twenty review tasks remain PENDING; exact 2026 General Manufacturing *post-Skill-Test* final online application original announcement, annex, required/optional files and page evidence remain HOLD. The candidate version is not deployed to the official beta web URL, and manual operator public beta OPEN has not been authorized.

Interest intake may remain OPEN, but true beta access must remain HOLD.

**M45 proposed next:** improve Indonesian onboarding and applicant-friendly clarification UX without assuming unverified official documents. Keep exact scope and approval barriers unchanged.
