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
- [ ] GitHub Pages deployment PASS on release HEAD. Independently verify live served assets rather than assuming a successful workflow equals the correct public bytes.
- [ ] **HTTPS-only entry:** the public campaign URL must not redirect from HTTPS to HTTP. Check both the `modernsnc2022-ai.github.io` project URL and the verified `https://www.gdglobal.kr/Korea-Employment-Passport/` origin. A working HTTPS custom URL alone does **not** excuse an HTTP downgrade from already-shared `github.io` links. The GitHub Pages `https_enforced` toggle must be checked explicitly before beta OPEN.
- [ ] Mobile-width smoke review PASS.
- [ ] No known critical or high-severity product defect remains open. Confirm the 2026 optional Job Capacity Assessment supporting documents are **conditional**, their September 21–23 window is **closed**, and `Formulir Uji Kompetensi` is required only when an applicant elects to upload eligible competency evidence in a valid official window.

## Read-only release preflight (does not approve anything)

**2026-10-14 release-tool safety fix:** The earlier readiness calculation could never report `readyForManualLaunchDecision=true`: it required the final manual OPEN action to have already happened while beta must remain HOLD. The corrected tool distinguishes `readyForManualLaunchDecision` from `explicit_manual_beta_open`. A fully simulated, genuinely signed official-source/Manufacturing review **plus live deployment parity** now reaches technical READY **with beta access still HOLD and `authorizesRelease=false`**; without such evidence the real result remains PENDING. `python scripts/report_indonesia_beta_release_preflight.py --self-test` covers seven injected live-deployment failures. `--live --json` makes **fresh HTTP requests** to verify six old campaign HTTPS redirects and exact SHA-256 bytes of nine served Git assets; it never consumes editable third-party green-status JSON or authorizes a release.

**Independent final state-writer guard:** `scripts/set_beta_release.py` now enforces the same fresh six-redirect/nine-asset proof, and requires a clean checked-out `main` HEAD **identical to the current GitHub remote `origin/main` SHA** before preparing HOLD→OPEN. Both `--confirm-open` and timezone-aware `--approved-at` remain explicitly required; source and cohort signoffs must pass first. A local `--write` **stages two changed local files only**; it does not deploy them. The resulting new OPEN commit is a new SHA, so operator must reverify that *new* published HEAD independently after the approved release. Never count pre-write 9/9 parity as proof that the new OPEN state has reached the public site, and never imply this local action automatically grants external access. `--self-test` rejects missing/wrong HEAD, insecure deep link, mismatched asset and 8/9 asset cases without touching real beta files.

On the intended beta release day, run `python scripts/report_indonesia_beta_release_preflight.py` (or `--json` for a local machine-readable report). This shows a dated snapshot of the 27-stage route, eight official-source alerts (three Korea-shared / five other-country), current-day monitor freshness, two separate manual signoffs, optional annex safeguards, the still-unverified Pages deployment parity, and the explicit beta HOLD/OPEN switch. The command is **strictly read-only** and never writes official hash baselines or approval files. Its PASS on an older day is **not** launch authorization; rerun and verify the actual date and real deployed site. `--self-test` exercises four fail-closed cases.

## Live HTTPS redirect and deployed asset parity

**2026-10-14 actual result: BLOCKED (read-only audit).** GitHub Pages at `https://modernsnc2022-ai.github.io/Korea-Employment-Passport/app.html` returns a **301** whose `Location` starts with `http://www.gdglobal.kr/...`; `https://www.gdglobal.kr/Korea-Employment-Passport/app.html` itself is valid HTTPS and returns HTTP 200. Authenticated read-only `gh api` inspection showed that `modernsnc2022-ai/modernsnc2022-ai.github.io` has `https_certificate.state=approved` but `https_enforced=false`; the KEP repository's Pages config also has `https_enforced=false`. Those are *existing settings*, not changes performed by this audit. **Fix requires separately authorized Pages settings changes**, scoped to each affected site with potential shared-domain impact review; do not silently alter org-wide Pages.

The published direct HTTPS site currently matched **9/9 key assets from `main` SHA `29fde41e697814154e4ebfba2a53ef3a56dbf8b7`**, and **only 1/9 from Draft PR #324** (the shared `beta_program_v1.json` still reports `status=hold`). That mismatch is expected while the PR is unmerged; it is **not** a production deploy failure. The live service-worker uses `kep-v124`, while the Draft's new secure-sharing metadata and content use `kep-v132` (prior content-only Draft had `kep-v131`).

Run `python scripts/audit_indonesia_beta_pages_live.py --self-test` first and then `python scripts/audit_indonesia_beta_pages_live.py --json` in a **clean checkout of the proposed release HEAD**. The real run compares exact *committed Git blob bytes* against nine HTTPS-served assets, avoiding Windows checkout CRLF false mismatches, and rejects HTTP downgrades, redirects to unrelated hosts, and mismatched assets. An expected launch-blocking mismatch gives a nonzero exit code. The script is read-only and **never** enables HTTPS, merges a PR, deploys, signs an official notice, flips beta access or assumes route PASS.

After owner-approved HTTPS enforcement and deployment, independently re-run the live audit on the **same committed release HEAD** and confirm `httpsEntrypointSafe=true`, `criticalAssetsSameRef=true`, no unexpected redirects, plus official same-day manual signoffs and the existing product/PWA/browser gates. New campaign links should use `https://www.gdglobal.kr/Korea-Employment-Passport/` until the original `github.io` entrypoint no longer downgrades; preserving already-sent messages is intentional.

**HTTPS follow-up on 2026-10-14 at 14:22 KST:** the earlier cached HTTP redirections described above **subsequently converged**, and all **six existing `github.io` first-hop links** (including project root, app, beta, index and attributed campaign URL) were independently observed redirecting directly to HTTPS with intact paths/query. Both Pages configurations now have approved certificates and `https_enforced=true` following explicit owner authorization. The earlier paragraph is a historical *pre-fix* snapshot only, not the current condition. Recheck the six links on the actual beta launch day. **Live parity to the *unmerged Draft PR* remains 1/9**, expected until approved deployment; do not confuse secure legacy routing with deployed beta readiness.

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
