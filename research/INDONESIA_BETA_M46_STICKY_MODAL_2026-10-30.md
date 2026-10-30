# KEP M46 — Fixed close control & footer in stage dialog (2026-10-30)

Scope: Indonesia E-9 General Manufacturing 2026 — single native stage detail dialog containing all stage instructions, official source links, FAQ, document scope, and pre-submit warning.

## Issue
When scrolling through long modal content, the only X button scrolled off the top of the dialog, requiring users to return to the top to dismiss the modal. The primary 'complete and continue' action likewise sat below long FAQ content.

## Implementation
- Restructured `docs/app.html` single native `<dialog id="stageDialog">` into a fixed-height flex form, stable `stage-dialog-header` with a 44px minimum-target X button and accessible Indonesian close label, independently scrolling `stage-dialog-body`, and visible `stage-dialog-footer` with existing `stageDoneBtn`.
- `docs/app-shell.css` limits dialog height using vh and dynamic dvh, gives the body its own internal scrolling, keeps the X and action footer outside the scroll region, and handles desktop / 390px / 320px / reduced viewport heights. Prevents root site footer rules from styling the new modal footer.
- `docs/sw.js`: PWA static cache v144.
- New `tests/m46-sticky-dialog.spec.js`: scroll/geometry assertions on long FAQ desktop, small mobile sizes and short viewport, native close/Escape, and pre-submit warning while keeping close and footer present.
- No changes to eligibility, source review state, application submission safeguards or beta launch access.

## Validation
- Targeted new M46 browser tests **4/4 PASS** (2026-10-30, `D:\KEP-M46-STICKY-DIALOG-TARGET2-20261030.log`).
- Contract: 27 stages, 308 exact answers, 16 country routes PASS. Beta launch guards and release preflight self-tests PASS. Official final Manufacturing job documents unverified and left `awaiting_sector_notice`, `items=[]`; beta access `hold`.
- Full Chromium regression **109/109 PASS**, exit 0, 3.3 minutes (2026-10-30, `D:\KEP-M46-STICKY-DIALOG-FULL-20261030.log`).

## Release discipline
Source PR #324 stays Draft/unmerged. Only safe public `docs/` UI assets should sync to production `main/docs` through separate fast-forward update after complete test success, followed by independent live HTTPS asset + browser UI verification. No GitHub Actions manually triggered.
