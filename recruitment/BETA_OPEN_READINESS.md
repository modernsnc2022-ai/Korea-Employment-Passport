# Beta OPEN readiness — Indonesia → Korea E-9 General Manufacturing 2026

**Snapshot reviewed:** 2026-10-14 KST. **This is a development-and-release evidence snapshot, NOT a release approval.** Update and independently retest on the actual beta release day.

**Product development:** supported route and primary user workflows implemented and independently tested. **Tester interest intake: OPEN; actual public beta access: HOLD; E-9 worker validation-panel access: HOLD; PR #324: Draft/unmerged.** Product-code test success does not imply approved official evidence, or that the latest Draft code is already live on GitHub Pages.

## Machine-checked snapshot (must match current tracked JSON)

- Indonesia Manufacturing supported stages: **27**
- Indonesia exact-answer records: **308**
- Broker question catalog: **256**
- Form wizards: **8**
- Form fields: **113**
- Monitored official sources: **83/84 fetched**
- Official source state: **review_required**
- Current exact Manufacturing job-application HOLD count: **1**
- Exact held Manufacturing item: `job_docs`
- Beta applicant-interest intake: **open**
- Actual public beta access: **hold**
- Worker validation-panel access: **hold**

Those counts are checked against the current GitHub source data by `scripts/check_beta_open_readiness_doc.py`, which is also invoked from the standard `check_beta_launch_readiness.py` product integrity gate. The snapshot is not a certification that all 84 official sources are fresh or reviewed for an arbitrary future date.

## Implementation evidence — development only

- Supported route: **Indonesia → E-9 → General Manufacturing → 2026**, 27 stages; separate Country Pack contracts exist for 16 sending countries, with the other countries still in `research_hold`/not promoted.
- Indonesian applicant content: **308** exact-answer rules; **256** structured broker questions; 13 document packs; 8 form wizards / 113 fields and 113 validators; 2026 optional Skill Test annex upload closed, with safeguards preventing its evidence from becoming the later job-application checklist.
- The 2026 initial EPS-TOPIK registration guide and sample PDF annexes are documented and narrowly reflected in Indonesian registration help; source-dated facts are not copied across Fisheries/Root Industry/special exams or 2025 cohorts.
- The current last independently executed **real Windows Edge full browser regression** was **79/79 PASS**, on applicant app/test code SHA `1c3ea182a75bbe1081472645657463f6f8f61c00`. Subsequent Draft commits changed release tooling, official evidence metadata and documents, not the applicant JS/PWA route behavior. Static/source-safety tests have separately passed on the later HEAD. Do not claim a successful production Pages build or live-HEAD parity from those results.
- Local/isolated Windows checks replace discretionary GitHub Actions spending where possible. Do not consume limited Actions budget merely to restate product-code tests.

## Release-day gates — NOT YET SATISFIED

1. **Fresh official source monitoring and named Indonesia review.** Last configured source scan fetched **83 of 84** (one Nepal fetch HTTP 500). There are **three changed Korea-common source alerts** needing named Indonesia-scope review: wage statements under Labor Standards Act Article 48, KDCA Travel Health Q-CODE categories and MOEL 1350 contact. Keep the five other-country warnings visible and pending. The local machine fetched all three official HTTPS pages and documented their contents, but this does **not** fill the manual signoff. Recheck the official monitor on the actual release day; October 14 evidence cannot be silently reused tomorrow.
2. **Same-day KP2MI 2026 General Manufacturing notice-body and attachments human review.** The correct official category is [KP2MI Pengumuman](https://kp2mi.go.id/gtog-korea/pengumuman), **not** `/gtog-korea/info` Preliminary Training. A read-only 2026 title survey of 320 recent records found seven General Manufacturing-related items and three *other-cohort* online job-application notices. The known notice titles do not yet establish the precise 2026 General Manufacturing **post-Skill Test** online application documents. Six September optional competency PDF annexes and four January/February initial examination registration PDF annexes have separate, dated limited-visual evidence. They are **not** final job-application forms. `job_docs` remains deliberately withheld pending applicable official notice, so no private-broker workaround or guessed upload checklist is permissible.
3. **HTTPS entrypoint and same-reviewed-HEAD deployment proof.** The owner approved GitHub Pages HTTPS enforcement on both shared site and KEP project. On **2026-10-14 at 14:22 KST**, **all 6/6** previously sent `github.io` entrypoint patterns redirected directly to matching **HTTPS `www.gdglobal.kr`** paths with attribution query intact. Recheck at release time. The live HTTPS production site's nine critical assets were independently matched **9/9 to existing `main`** SHA `29fde41e697814154e4ebfba2a53ef3a56dbf8b7`, **only 1/9 to the unmerged Indonesia Draft**. This mismatch is expected before a reviewed merge/deployment and is **not** a main production outage. After approved deployment, verify **9/9** real served assets against that exact release commit SHA and confirm actual Pages deployment evidence.
4. **A separate, explicit OPEN decision.** The read-only `scripts/report_indonesia_beta_release_preflight.py --live --json` reports whether all official/technical preconditions are ready for an operator decision, but **cannot authorize release**. Its READY indicator is distinct from manual OPEN. `scripts/set_beta_release.py` must independently require dated human signoffs, clean checked-out `main` matching the live remote commit, six secure first hops, nine exact live assets and an explicit approval time. Its local `--write` does **not** deploy the new OPEN state; a newly approved release commit must be published and rechecked after deployment. Do not merge, activate testers or change the beta switch without explicit authorization.

## Why one exact question is still HELD

The unresolved item is **only `job_docs`**: the precise list of files the 2026 General Manufacturing applicant must upload for the final online job application *after* the mandatory Skill Test. Four adjacent questions (`job_scan`, `job_name`, `job_edit`, `job_submit`) have separately reviewed conservative official-platform/identity safety baselines and **must not** be counted as four additional current HOLDs. The one genuine external official-evidence HOLD blocks declaring **Broker Replacement Rate 100% PASS**, but does not by itself forbid a restricted beta if all technical/official/manual release gates pass and guidance continues refusing unsupported details.

## After OPEN — user validation, not a prelaunch product-code prerequisite

- Recruit at least **30 current-cycle active Indonesia applicants**, and separately **20 Indonesian E-9 workers already in Korea** for retrospective worker validation. The 30-person count is a soft recruitment target, not a hard signup cap; applicant overflow IDs begin at KEP-0051.
- Approved beta users receive six free months starting **from their individual beta activation date**, conditional on useful feedback.
- Capture later-stage coverage (roster, employer selection, SLC, visa, medical/departure), prove private-broker replacement or official-only alternatives, and close exact `job_docs` on genuinely applicable current-cycle evidence before claiming full validated route PASS.
- Never put personal emails, identity documents, addresses, bank or health details in GitHub or public Google Sheets. Worker evidence requires separate consent and review.

## Actual current switch state

**Intake OPEN; beta access HOLD; worker panel access HOLD.** No participant KEP ID is activated solely from interest registration. A failed or missing official/manual/deployment gate cannot be papered over by a successful browser test. Continue development in the Draft PR without accidentally deploying or activating any of the other sending countries.

References: `recruitment/ID_BETA_OPERATOR_SIGNOFF_PACKET_20261014.md`, `recruitment/BETA_LAUNCH_GATE.md`, `research/INDONESIA_BETA_PAGES_HTTPS_LIVE_PARITY_AUDIT_20261014.md`, and `docs/MVP_VALIDATION.md`.
