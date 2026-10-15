# KEP Indonesia beta — launch-first priority audit (2026-10-15 KST)

**Evidence-based internal execution plan, not permission to publish or approve sources.**
Reviewed candidate HEAD: `82e2b5c30faea9235611c36e85280963d599e05c` on Draft PR #324, unmerged.
Protected state: product beta `hold`; direct HTTPS D1 applicant intake `hold`; email **interest** path `open`; E-9 worker retrospective panel access `hold`.
No real applicant submission, invitations, six-month benefit activation, source signature, PR merge or production release is authorized.

## Confirmed product development state — NOT a release decision

- 27 Indonesia E-9 General Manufacturing 2026 stages, 308 exact answers, 256 broker questions, 13 document packs, 8 form wizards / 113 fields and validators, 5 official-help channels.
- The product/static QA and webapp contract passed on candidate HEAD `82e2b5c`, with the mandatory `PRODUCT_CI_SOURCE_HOLD` warning because source approval is outstanding. SQLite private intake self-test and source-signoff fail-closed mutations also passed.
- Current official-source **observation** on 2026-10-15: 84/84 HTTPS sources fetched, 0 fetch failures, 10 changed hashes (4 Korea-common; 1 multi-country HRD Korea EPS-TOPIK schedule; 5 other sending-country sources). Read-only evidence: `research/source_reviews/shared_source_watch_readonly_2026-10-15.json`. None of those hashes was accepted. **Published gate artifacts still describe 2026-10-14 83/84 and 8 alerts.**
- Read-only published website audit on this candidate: 6/6 secure HTTPS first-hop redirects PASS, **0/9** critical production assets match candidate HEAD (Draft has not been deployed). Do NOT reopen HTTPS settings; plan a separately approved same-HEAD deployment.
- KP2MI 2026 General Manufacturing title inventory: 320 official Pengumuman rows through July 2025, 7 current-cycle Manufacturing-related notices, 3 other-cohort application notices, **0** verified exact current-cycle Manufacturing post-Skill Test job application notices. Broad generic-application title sentinel also returned **0 ambiguous candidates**. An absent title is not proof that a relevant detail/attachment could not exist.

## P0 — beta release prerequisites and correct work order

| Priority | Work | Current evidence | Next safe action | Needs owner/operator approval? |
| --- | --- | --- | --- | --- |
| P0-1 | **Update source review adapter to consume current 84/84 + 10 alerts** | `check_indonesia_release_source_scope.py`, source signoff guard and preflight are currently pinned to the historical 3 Korea + 5 foreign snapshot; 2026-10-15 drift is 4 Korea + 1 multi-country + 5 foreign | Implement fail-closed **dated snapshot selection and all-10-ID classification**, with tests rejecting new/unknown/reclassified sources. Keep 2026-10-14 historical evidence intact. The new snapshot must **not** be treated as human approval. | Code change: no. Real official-content signoff: yes |
| P0-2 | Review current official source substance and record **real dated scope signoff** | Four Korea-shared source facts had narrow read-only checks; multi-country HRD Korea relevance and five country-specific alerts still need explicit scope acknowledgement; all hashes still unaccepted | Named reviewer checks relevant statements, sees ALL ten pending source changes, verifies source-map fingerprint and same-day evidence, signs only what was actually reviewed | **Yes**; never synthesize signatures or claim `clean` |
| P0-3 | **Current KP2MI Manufacturing 2026 index, bodies and annex review** | 320 notice titles scanned; January EPS registration, optional September competency upload, Fisheries, Root Industry and Special EPS do not prove final Manufacturing `job_docs` | Recheck current-cycle official notice bodies/attachments on intended OPEN date; sign the bounded review without fabricating missing final checklist | **Yes** for human review/signoff; no new applicant data |
| P0-4 | Refresh full beta UI and static quality on **same reviewed release candidate** | Static/webapp tests passed on `82e2b5c`; prior Edge suite results are from earlier HEADs | Run full local/isolated Edge tests, mobile-width and safe fallback paths on the final candidate; fix actual P0 defects before merging | No for isolated QA; **yes** for any production deployment |
| P0-5 | **Approved Pages release and exact live parity** | HTTPS 6/6 PASS; latest Draft HEAD live assets **0/9** matching. This is expected while unmerged | After explicit owner approval, perform reviewed merge and Pages deployment; verify 9/9 committed asset SHA against live and 6/6 HTTPS redirects on that same approved release | **Yes** before merge/deploy |
| P0-6 | **Separate final beta OPEN decision** | `status=hold`, `publicBeta=pending_manual_approval`, signoffs pending; read-only preflight `readyForManualLaunchDecision=false` | Only after P0 1–5 real gates PASS, ask owner for actual beta access OPEN with real timestamp; verify final published state separately | **Yes, explicit final OPEN approval** |

## NOT a beta launch blocker by itself

- **Exact `job_docs` HOLD:** `docs/data/beta_program_v1.json.releaseDecision.publicBetaHoldPolicy.safeOfficialEvidenceHoldsMayRemain=true`. The UI must visibly refuse to invent the specific 2026 Manufacturing **final online job-application documents**, point to the appropriate official source/help, and preserve the HOLD. The absence of this one exact item blocks **Broker Replacement Rate 100% route validation**, not a restricted beta when all P0 controls are satisfied.
- **30 active Indonesia applicants and 20 retrospective E-9 worker validators:** These are post-OPEN validation cohorts, not a condition for activating the first restricted beta. The 30-applicant target is soft; approved testers get six free months counted from their own beta activation and subject to feedback.
- **Separate direct HTTPS applicant application form and private D1/OTP integration:** optional for initial email-interest-based beta. The owner-confirmed private Worker deployment and one real OTP confirmation/replay test do not prove a production cross-Worker D1 insertion. Both private worker enable flags and direct-intake release decision must stay OFF until separate approval; do not delay email-fallback beta just to enable direct application intake.
- **Other country packs:** retain research HOLD while Indonesia limited beta is prepared. Their separate 2026 official notifications should never change Indonesia route rules.

## Guardrails and next development action

1. Fix **P0-1 first**: the older source-scope/signoff validator's hard-coded 3+5 alert model does not describe today's 4+1+5 observation. This is a genuine adapter/developer task; do **not** copy today's unapproved hash into `monitor/source_hashes.json` or mark the public `source_review_status.json` clean just to make the old gate green.
2. Continue P0-3 official notice checking in parallel with P0-1 and P0-4 isolated QA. Any unresolved exact `job_docs` answer remains a transparent HOLD, not a fabricated applicant instruction.
3. Owner/operator steps P0-2/P0-3/P0-5/P0-6 are **not done** and must not be checked off by a code commit or this file. No new external outreach, applicant intake, open beta or GitHub Actions spending without separate authorization.

References: `scripts/report_indonesia_beta_release_preflight.py`, `recruitment/BETA_OPEN_READINESS.md`, `recruitment/MANUFACTURING_LAUNCH_CHECK.json`, `docs/data/beta_program_v1.json`, `recruitment/ID_BETA_SOURCE_SIGNOFF.json`, 2026-10-15 read-only official watch audit and 2026-10-15 live Pages first-hop/asset parity check.
