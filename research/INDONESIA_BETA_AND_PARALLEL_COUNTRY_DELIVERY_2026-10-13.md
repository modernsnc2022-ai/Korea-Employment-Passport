# KEP: Indonesia development-complete -> immediate beta, parallel Country Packs

Decision date: 2026-10-13
Owner direction: finish the **Indonesia E-9 Manufacturing 2026 product functions** before asking real users to validate the product; open a controlled Indonesia beta as soon as release-safety checks pass; collect product feedback during beta; continue development of other countries in parallel.
This document is a plan and change record, not an assertion that the beta is already OPEN.

## Separate the three completion definitions

1. **Feature-development done (product code):** The supported Indonesia E-9 Manufacturing 2026 route and all 27 stages are navigable; source-grounded / held rules, stage navigation, personal data protection, Indonesian copy, document/form assistance, official human help, broker-risk and workplace guidance, tester interest, invitation and feedback workflows work as designed. Existing tests can execute. Known product bugs are closed; no fabricated official rules are inserted to force a numeric completion score.
2. **Beta-release eligible (technical safety):** All required same-HEAD integrity/UI checks and deployment evidence pass, source review is fresh, KP2MI Manufacturing notice has been checked **on the actual release date**, any new notice has been reviewed before promotion, and the manual OPEN decision is recorded. This is not end-user validation, and it must not be waived.
3. **Fully validated broker replacement:** After actual Indonesia beta feedback, collect 30 current-cycle applicant observations and 20 experienced-worker interviews, verify late-stage coverage and 27 government journey stages, resolve broker gaps and the `job_docs` detailed official checklist. **Do not declare 100% broker replacement before this evidence exists.**

## Execution lanes

| Lane | Priority | Work | Delivery constraint |
| --- | --- | --- | --- |
| Indonesia / product | P0 | Close coding regressions and usability gaps, ensure applicant invitation, Indonesian privacy language, intake, feedback loop and safe `job_docs` HOLD | No new invented Manufacturing fee/required document rules |
| Indonesia / release | P0 | Refresh 84 official-source checks, official KP2MI notice review, same-HEAD static + Chromium UI + Pages + beta launch gate, explicit operator OPEN, then activate testers and capture feedback | Never claim release before matching deployed HEAD is live and release state actually OPEN |
| Nepal | P1 | Continue isolated Draft PR #323 research-only navigator, native Nepali copy audit, real mobile screen-reader QA and verified cohort-specific notices | No Nepal beta activation, merge, deploy or school outreach without separate approval |
| Kyrgyzstan | P1 | Extend verified 2026 Manufacturing post-selection journey: employer selection/SLC, post-SLC visa and departure; preserve current-cycle vs country-baseline distinction | Keep research_hold until exact official evidence and independent validation |
| Vietnam / Sri Lanka / Thailand | P2 | Recheck dated 2026 official notices; add precise dated rules only when sources match cohort/sector | Preserve HOLD for unreviewed notices |
| Remaining Country Packs | P3 | Continue conservative E-9 manufacturing translations, current cohort official provenance and downstream documentation | Country Pack registration is not beta readiness |

## Work order and operating rules

- GitHub-first. Prefer Colab/Kaggle/Lightning for heavy tests; no automatic GitHub Actions budget use. Headless test machines must not touch the foreground desktop or unrelated user folders.
- Existing Country Packs stay on their own lifecycle. Changes to Indonesia beta must not accidentally open other countries.
- Applicant interest can remain OPEN before beta access. Actual app beta activation requires explicit readiness evidence; 30 is a soft recruitment target; approved testers get six months free from **individual activation**, conditional on feedback.
- User verification is performed **in** beta after release, not a pre-beta development gate. Official evidence fidelity, privacy and technical release checks are still release conditions.
- At this writing the GitHub default-branch Indonesia release state remains `hold`; the 2026-10-06 official-source baseline and launch-check are historical. A fresh release-day review is not yet recorded.
- Two 2026-10-13 gate defects were identified and patched on the development branch: obsolete 5-HOLD requirement instead of the current 1-HOLD plus 4 safe baselines; fixed 2026-10-06 launch-date assertion instead of an independently verifiable current review date. A third content issue was missing exact privacy disclosure substrings. None of these changes alone approves opening the beta.
