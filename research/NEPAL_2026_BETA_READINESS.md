# Nepal 2026 EPS Country Pack — research preview verification

Status: **RESEARCH / HOLD** — not an open applicant beta. This page tracks safeguards in [P0 issue #322](https://github.com/modernsnc2022-ai/Korea-Employment-Passport/issues/322) and [Draft PR #323](https://github.com/modernsnc2022-ai/Korea-Employment-Passport/pull/323).

## Scope and live links

- Research preview: `docs/np.html`
- Unpublished branch-only stage selector: `docs/nepal-journey.html` and `docs/nepal-journey.js`
- Source data: `docs/data/np_*.json`
- Cohort provenance: `docs/data/np_notice_provenance_2026.json`
- The public GitHub Pages site **does not contain the branch's new stage selector unless the PR is reviewed and deployed**.

## Safety invariants

1. Nepal `np-e9-manufacturing-2026` is 2026 first-phase general Manufacturing, not Root Industry and not an Indonesia translation. Government actions stay on official government websites.
2. The 2026-07-21 Nepal primary notice originally ended on 2026-08-02. The official July 30 supplementary image **explicitly extended the first-phase online-registration deadline to 2026-08-05**; the HRD Korea row corroborates it. That historical window is closed and cannot be reused for later cohorts.
3. 2026 first-phase EPS-TOPIK exam assignment/results, Skill & Competency, medical/employment application, post-SLC and visa/departure steps must not be promoted without a cohort-identifiable reviewed official notice. A 2025-cohort notice describes prior process only.
4. 2026 Root Industry alternative-selection notices and later departure notices for workers with unknown recruitment cohort cannot be shown as first-phase Manufacturing applicant notices.
5. On 2026-10-13 the official July 26 15-page PDF was obtained; its first three scanned notice pages were visually reviewed for anti-duplicate payment/account and application-correction safeguards (remaining user-guide appendix kept as historical reference). The official July 30 inline-image notice was visually reviewed for the deadline extension and expired-passport exception; a **valid passport is required by the later Job Application Form** after passing language and skills. These limited findings do not promote current exam, medical, job, visa or future-cohort rules.
6. `research_hold`, `preview_only`, `betaState=blocked` and `betaIntakeOpen=false` remain in effect across pack, dashboard, and stage readiness. Do not ask for personal documents or display a beta application/fee collection flow.
7. Screens that cannot load or verify essential gate data fail closed.

## Repeatable checks without GitHub Actions

From a clean checkout in a permitted compute environment with Node.js 22+:

```sh
npm run test:nepal-gate
```

This invokes a Node stdlib-only audit of current checked-in Nepal JSON and injection tests that protect the reviewed 2026-07-30 extension provenance, expired passport exception, no beta opening, cross-program isolation and non-current documents. It does **not** install dependencies, run Chrome or trigger GitHub Actions.

For actual browser testing, once an isolated remote runner with working Chromium and npm dependencies is available:

```sh
npm ci
npx playwright install chromium
npx playwright test tests/nepal-journey.spec.js
```

On 2026-10-13 reviewed-data commit `5360a4fa56d2af5d9a830344c976e9e12df89660`, the actual Node research gate passed **12/12**, headless Microsoft Edge Chromium browser navigator **16/16**, and offline Chromium **7/7** (total **35/35**, exit code 0 for all suites). A subsequent documentation/provenance-only commit should rerun the gate and regression suite before any launch or merge. GitHub Actions are manual-dispatch only and should not be triggered for this verification unless budget approval is obtained.

## Offline Chromium regression without localhost

The browser's `page.goto('http://127.0.0.1:4173/...')` can fail in restricted execution hosts.
An additional browser suite reads checked-in HTML, JavaScript and **the exact Nepal JSON
assets** from the repository and injects them via `page.setContent`, mocks only the
JSON fetch transport, and runs Chromium DOM assertions without serving any website:

```sh
npm ci
npx playwright install chromium
npm run test:nepal:offline
```

With a preinstalled system Chromium browser, use `CHROMIUM_PATH` to point at
the executable before the command. The offline suite checks 2026 registration closure,
future/different-cohort isolation, suppression of obsolete fees and checklists,
and fail-closed handling for unsafe notice flags or missing mandatory data.

**Limit:** Browser-tested offline injected assets do not prove hosted URLs, CSP, public
GitHub Pages deployment, routing, or network availability. The full browser
suite and manual product-review gates remain necessary; this is a faster intermediate test,
not a beta-launch permission. The extended offline suite passed 7/7 with the official July 26/30 review data on commit `5360a4fa`.

## Promotion checklist

- [x] July 30 official inline image visually reviewed: August 5 deadline and original-expired-passport exception verified.
- [x] July 26 official PDF downloaded (15 pages) and first three scanned notice pages reviewed: duplicate registration/payment and correction guidance.
- [ ] Assess attached July 26 user guide pages 4–15 individually before treating details as operating instructions; continue scanning for later cohort-specific notices.
- [ ] Confirm same-cohort announcement/result dates for the specific 2026 first-phase E-9 Manufacturing route.
- [ ] Verify current-cohort documents, medical providers, job application, CCVI/visa service-fee location and PDOT/departure rules; leave volatile values unknown otherwise.
- [x] Re-run current-branch gate and both actual Chromium suites after 2026-07-26/30 rule promotion: 12+16+7 = 35/35 PASS on commit `5360a4fa`.
- [ ] Obtain independent Nepali language/accessibility review by consenting educators who were already contacted (no new Nepal outreach).
- [ ] Reassess feature-by-feature beta readiness with a clear scope, then obtain explicit approval before opening Nepal beta or resuming recruitment.

## 2026-10-13 official evidence reconciliation

- [EPS Nepal July 26 first-phase urgent notice](https://epsnepal.gov.np/postdetails/137) — original 24,459,715-byte, 15-page attachment downloaded. Its scanned first three pages are reviewed. Registration site guide pages 4–15 remain reference-only and must not be advertised as live instructions.
- [EPS Nepal July 30 official inline passport/deadline image](https://epsnepal.gov.np/postdetails/143) — source image visually inspected and hash recorded in reviewer workspace; direct notice confirms registration extension through **2026-08-05** and allows original expired passport details at initial registration, with valid passport for later job application after language/skill passing.
- Existing primary notice remains separately preserved as original baseline of 2026-08-02. The July 30 supplement changes that end date only; original first-phase recruitment is closed now. No unverified fees, exam dates, future application rounds, or job forms may be promoted.
- Node fail-closed and real Chromium suites extended and executed successfully (12 + 16 + 7 = 35 PASS, 0 FAIL) on reviewed-code commit `5360a4fa`; repeat on any subsequent functional changes.
