# Beta launch gate — Indonesia E-9 Manufacturing

Public tester-interest intake may be **OPEN before launch**. Actual beta access, KEP ID activation, and the 6-month benefit must remain **HOLD** until every required item below is PASS.

## 1. Core product flow
- [ ] All 27 supported-route stages are navigable in order.
- [ ] A user can set their current stage and continue from there.
- [ ] Each stage clearly distinguishes official fact, app guidance, and unresolved official detail.
- [ ] No unsupported guess is shown as an exact instruction.

## 2. Zero-broker coverage
- [ ] No unresolved HIGH broker-replacement blocker exists for the supported route.
- [ ] Known broker-like micro questions have an exact answer, official help route, or explicit HOLD.
- [ ] The four Manufacturing 2026 safe-platform/identity questions use conservative verified non-exact baselines; only the precise final job-application checklist (`job_docs`) remains on explicit HOLD. That HOLD blocks final Broker Replacement Rate PASS, not a safely restricted beta OPEN.
- [ ] Broker Replacement Rate measurement can be captured from beta feedback.

## 3. Forms and document guidance
- [ ] All current form wizards and validators pass automated checks.
- [ ] Required/optional document distinctions are visible.
- [ ] Users are warned not to submit when an official requirement is not confirmed.

## 4. Official-source freshness
- [ ] The official-source watch is refreshed on launch day, and either **all monitored sources are manually reviewed and clean** or the strict **Indonesia-only manual source-scope signoff** passes. Three Korea-shared alerts must be checked; five unrelated-country alerts, including an acknowledged country-only fetch failure, remain visible and must never be auto-accepted.
- [ ] No unresolved source failure affects a current user action.
- [ ] The actual KP2MI G-to-G Korea **Pengumuman** index (not the historical `/gtog-korea/info` Preliminary Training page) and relevant 2026 General Manufacturing notice bodies/attachments are checked again on the real launch day with an explicit named operator signoff. A title-only scan or previously closed optional Skill Test upload does not certify exact `job_docs`.

## 5. Beta UX and privacy
- [ ] Beta ID accepts the reserved base IDs plus contiguous overflow active-applicant IDs KEP-0051 and upward.
- [ ] Beta evidence is isolated by tester ID.
- [ ] Sanitized feedback can be copied/shared without identity fields.
- [ ] Public beta copy clearly states: initial target at least 30 eligible active applicants, 30 is not an automatic rejection cap, approved testers receive 6 months free from activation, and feedback participation is required.
- [ ] Public beta copy clearly states there is no job, visa, SLC, or departure guarantee.
- [ ] No passport/KTP/ARC number or other sensitive identifier is required to receive the beta benefit.

## 6. Workplace Reality Check
- [ ] Public workplace-information view is usable without worker testimonials.
- [ ] Missing or unverified workplace claims are labeled as such.
- [ ] Worker reviews/photos/videos, when added, have a verification and privacy rule.
- [ ] E-9 worker interviews can be converted to WPE-#### records through the dry-run-first privacy-safe publisher; completed private intake files are never committed.

## 7. Release quality
- [ ] Static checks PASS on release HEAD.
- [ ] UI smoke tests PASS on release HEAD.
- [ ] GitHub Pages deployment PASS on release HEAD.
- [ ] Mobile-width smoke review PASS.
- [ ] No known critical or high-severity product defect remains open. Confirm the 2026 optional Job Capacity Assessment supporting documents are **conditional**, their September 21–23 window is **closed**, and `Formulir Uji Kompetensi` is required only when an applicant elects to upload eligible competency evidence in a valid official window.

## Read-only release preflight (does not approve anything)

On the intended beta release day, run `python scripts/report_indonesia_beta_release_preflight.py` (or `--json` for a local machine-readable report). This shows a dated snapshot of the 27-stage route, eight official-source alerts (three Korea-shared / five other-country), current-day monitor freshness, two separate manual signoffs, optional annex safeguards, the still-unverified Pages deployment parity, and the explicit beta HOLD/OPEN switch. The command is **strictly read-only** and never writes official hash baselines or approval files. Its PASS on an older day is **not** launch authorization; rerun and verify the actual date and real deployed site. `--self-test` exercises four fail-closed cases.

## Automated gate behavior

The `beta-launch-gate` workflow is an aggregator, not just a data-only check. For the same `main` HEAD it requires:
- strict beta prelaunch readiness;
- `static-check` SUCCESS;
- `ui-smoke` SUCCESS, including mobile-width tests;
- GitHub Pages `pages build and deployment` SUCCESS.

A green beta-launch-gate must not be interpreted as valid when one of those sibling checks failed on the same commit.

## Beta OPEN vs route PASS

The **at least 30 active applicants + 20 E-9 workers are not prerequisites for opening beta access**. They are the evidence cohort collected after opening and are required before declaring the supported route a Broker Replacement Rate 100% PASS.

Beta access OPEN requires sections 1–7 to pass plus a final same-day check for any new Manufacturing 2026 official notice. Application intake may already be OPEN. Route PASS remains governed by `docs/MVP_VALIDATION.md`.

## 8. Access approval switch
Application intake can remain OPEN while access is HOLD.

When sections 1–7 all PASS:
1. after an explicit manual release decision, use the release-state helper to change **beta access** from HOLD to OPEN and record the approval timestamp;
2. review the applications already collected while access was HOLD;
3. approve eligible active applicants and assign KEP-0001 through KEP-0030 as the base cohort;
4. if more eligible applicants are approved, continue with KEP-0051 upward; do not reject someone solely because the count exceeded 30;
5. keep KEP-0031 through KEP-0050 reserved for the separate E-9 worker retrospective panel;
6. grant every approved beta tester 6 months free from their actual beta activation date.

## Launch principle
The beta should start only when the product is complete enough that testers are primarily finding **real-world process gaps**, not obvious unfinished-product defects. Do not claim same-HEAD production verification using historical draft-branch tests, and do not treat an unapproved source scan as an operator signature.
