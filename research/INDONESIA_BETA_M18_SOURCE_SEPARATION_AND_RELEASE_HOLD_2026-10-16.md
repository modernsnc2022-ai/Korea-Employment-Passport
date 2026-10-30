# KEP M18 — Published Main versus Unpublished Candidate (READ ONLY)

**Checked 2026-10-16 KST; route:** Indonesia > E-9 > General Manufacturing 2026.
**Authority:** technical audit only. No official fact approval, source hash acceptance, beta OPEN, PR merge, Pages setting modification or external applicant contact.

## 1. Repository and shared record

- GitHub PR #324 remains OPEN / Draft / unmerged.
- Tested candidate before M18 changes: `9ad2d1e30262658205ff5659487a80cc456974ae`; deployed main: `29fde41e697814154e4ebfba2a53ef3a56dbf8b7`.
- Local Windows branch `feature/kep-official-index-watch-20261015` had a clean worktree at the original M17 HEAD.
- The central Google Sheet activity-history row 1155 **already includes M17**; do not duplicate that row.

## 2. Separate Pages publication gates — M18 code

Updated `scripts/report_indonesia_beta_release_preflight.py`:

1. New `published_main_source_integrity` gate accepts an authenticated, fresh, read-only GitHub Pages source diagnosis only when configuration is `main/docs` and nine published assets match the deployed main commit. Its PASS is **not** proof that Draft code is deployed.
2. `same_head_pages_deployment` now demands *both* the independent HTTPS asset audit (9/9 assets, six secure legacy redirects) **and** a source diagnosis confirming that the tested release HEAD equals the actual published main ref. An unpublished candidate or ambiguous branch identity cannot authorize the deployment gate.
3. `readyForManualLaunchDecision` includes the source-integrity gate in its hard requirements; `authorizesRelease` remains false. If the Pages source diagnosis cannot be fetched, the new gate fails closed; no manual data flag can substitute for the `--live` probe.
4. New descriptive read-only report booleans: `publishedMainSourceIntegrityVerified`, `candidateHeadPublished`. Synthetic self-test exercises a published main with an unpublished candidate, and an all-conditions-approved hypothetical **without** writing any approvals.

## 3. Actual Windows live checks

| Check | Observed result |
|---|---|
| Preflight self-test (M18) | PASS, process exit 0 |
| Normal `--as-of 2026-10-16` | exit 0; official watch PASS, signoffs PENDING |
| Fresh `--as-of 2026-10-16 --live` | exit 0; `published_main_source_integrity=PASS`, `same_head_pages_deployment=PENDING` |
| Independent M17 Pages source live diagnosis | `DEPLOYED_MAIN_DRAFT_HEAD_NOT_PUBLISHED`; main **9/9**, candidate **0/9**, exit 0 |
| Product static gate `--allow-source-review-pending` | PASS; reports `PRODUCT_CI_SOURCE_HOLD` |
| `git diff --check` | PASS (no reported whitespace errors) |

Both `READY_FOR_MANUAL_DECISION` and `LIVE_DEPLOYMENT_VERIFIED` remain **False**. There is no evidence of a Pages deployment failure, and no reason to purge caches or switch the source branch.

## 4. Official-source evidence and handoff to human reviewer

The **2026-10-16** official-source observation already fetched **84/84**; **12** fingerprints differ from the last *accepted* baseline: five Korea-common, two multi-country HRD EPS, five other-country. These are not twelve new changes within one day, and **none has been approved**. Named signoff is still `pending_manual_source_signoff`.

KP2MI `Pengumuman` 2026 index already contains **185** dated 2026 titles through 2025 boundary and **seven** Manufacturing-related headlines. The existing detailed audit `research/ID_MANUFACTURING_2026_7_NOTICE_DETAIL_AUDIT_20261014.md` had fetched all **7** notice HTML bodies; separate 2026-09-17 optional competency PDF review recorded **6 files / 21 pages**, while 2026-01-27 registration annex review recorded **4 files / 27 pages**. These prior read-only technical audits are reused rather than repeated. They **do not** constitute signed review of every relevant appendix or proof of complete current-cycle job application requirements.

Applicable exclusions remain:
- 2026-09-17 Skill Test *optional* Job Capacity Assessment supporting documents: not final job-register `job_docs`; its submission period is closed.
- 2026-09-10 Manufacturing EPS-TOPIK language first-stage success: 2,020 language-test passers, mandatory Skill Test, **not final selection**.
- 2026 Fisheries online application instructions and 2025 Manufacturing submission details: wrong cohort/sector, never copy into 2026 General Manufacturing exact uploads.
- January 2026 initial EPS-TOPIK registration documents, MCU I and HIMPSI baseline: **not** final post-Skill Test Manufacturing job-application checklist.

The missing **2026 General Manufacturing final online job-application detailed upload list** was not established in existing indexed headlines or audited HTML. An absence from headline/title searches is not proof that an official rule does not exist. The `job_docs` Rule Engine item stays `HOLD`, with no speculative additions.

## 5. Remaining explicit human/owner decisions

1. On the **actual** release date, review full original 2026 KP2MI Manufacturing notices/linked PDFs and current official-source fingerprints; obtain a named human source signoff. A past-day observation cannot silently approve a future day.
2. Preserve `job_docs` HOLD until a matching official source supports exact documents, or keep submission support visibly blocked while considering a separately scoped product beta.
3. Only after separate authorization, deliberately deploy an approved release SHA to GitHub Pages `main/docs`, then repeat 9/9 parity and 6/6 redirect verification on the deployed SHA.
4. Obtain a **separate** explicit public beta OPEN decision. **Nothing in M18 authorizes launch, applicant invitations or automatic source fact promotion.**
