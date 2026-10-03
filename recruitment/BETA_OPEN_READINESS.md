# Beta OPEN readiness — Indonesia → Korea E-9 Manufacturing 2026

Status: **READY FOR RELEASE DECISION — recruitment remains HOLD**

Reviewed: 2026-10-04 KST

## Automated readiness

- Locked 27-stage route: PASS
- Broker-question catalog: 256 questions, no unresolved HIGH blocker outside the five explicit Manufacturing 2026 evidence HOLDs
- Form guidance: 8 forms / 113 fields / 113 validators
- Official-source monitor: 72/72 checked, clean, no review-required source, no fetch failure
- Static product integrity: PASS
- Strict beta-launch gate: PASS
- Mobile/desktop UI smoke: PASS on the current product code line
- GitHub Pages deployment: PASS on the current product code line
- Public beta slots: 30 pseudonymous KEP IDs prepared
- E-9 worker validator slots: 20 separate pseudonymous KEP IDs prepared
- Public-beta slot helper and E-9 worker-panel slot helper: self-tested in CI
- Workplace worker-evidence registry: privacy validation enabled
- Progress/feedback reporting: privacy-safe aggregate reporting enabled

## Explicit official-evidence HOLD

A 2026 Manufacturing-specific detailed e-certificate / online job-application notice has still not been verified.

These five questions remain intentionally held rather than guessed:
- `job_docs`
- `job_scan`
- `job_name`
- `job_edit`
- `job_submit`

This is tracked in GitHub issue #2 and is an external official-evidence dependency, not a known product-code defect.

## Before changing recruitment from HOLD to OPEN

1. Re-check the KP2MI Korea information index and official search **on the day of the OPEN decision** for a new 2026 Manufacturing-specific online job-application notice.
2. If a new notice exists, review it before changing any held rules.
3. Make an explicit release decision for either or both:
   - 30-person active-applicant public beta
   - 20-person E-9 worker retrospective validation panel
4. Change only the intended status switch; do not silently open the other panel.
5. Re-run strict beta-launch gate, UI smoke, and Pages after the switch.

## After OPEN — evidence collection, not a launch prerequisite

The following are required before declaring the supported route a Broker Replacement Rate 100% PASS:
- 30 active Indonesian G-to-G applicants
- 20 Indonesian E-9 workers in Korea
- at least one active tester in each late-stage bucket: roster/employer selection, SLC/post-SLC, visa/OPP/final medical, departure
- every reported Broker Gap resolved or documented as an official/licensed-only dependency

See `docs/MVP_VALIDATION.md`.

## Current switch state

- Public beta: **HOLD**
- E-9 worker validator panel: **HOLD**
- No participant slot has been activated or enrolled yet.
