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
2. The first-phase application window in the Nepal 2026-07-21 *primary* notice has ended. HRD Korea's different end-date listing is documented as a cross-source discrepancy, **not** proof of an extension.
3. 2026 first-phase EPS-TOPIK exam assignment/results, Skill & Competency, medical/employment application, post-SLC and visa/departure steps must not be promoted without a cohort-identifiable reviewed official notice. A 2025-cohort notice describes prior process only.
4. 2026 Root Industry alternative-selection notices and later departure notices for workers with unknown recruitment cohort cannot be shown as first-phase Manufacturing applicant notices.
5. 2026-07-26 urgent registration PDF (large) and 2026-07-30 passport/application notice (image content) were found but not fully reviewed; they cannot silently change passport, eligibility or payment instructions.
6. `research_hold`, `preview_only`, `betaState=blocked` and `betaIntakeOpen=false` remain in effect across pack, dashboard, and stage readiness. Do not ask for personal documents or display a beta application/fee collection flow.
7. Screens that cannot load or verify essential gate data fail closed.

## Repeatable checks without GitHub Actions

From a clean checkout in a permitted compute environment with Node.js 22+:

```sh
npm run test:nepal-gate
```

This invokes a Node stdlib-only audit of current checked-in Nepal JSON, then seven `node:test` tests including unsafe beta-opening, cross-program promotion, unreviewed passport changes, unfounded registration extension, Indonesia-only psychology leakage and lack of document warnings. It does **not** install dependencies, run Chrome or trigger GitHub Actions.

For actual browser testing, once an isolated remote runner with working Chromium and npm dependencies is available:

```sh
npm ci
npx playwright install chromium
npx playwright test tests/nepal-journey.spec.js
```

The Playwright suite is **written but unexecuted** in a real Chromium session. Do not merge or advertise beta readiness on the basis of mocked DOM smoke tests alone. GitHub Actions are manual-dispatch only and should not be triggered for this verification unless budget approval is obtained.

## Promotion checklist

- [ ] Review all current 2026 primary/supplementary Nepal official notice attachments in full, including July 26 and 30, documenting their actual effect.
- [ ] Confirm same-cohort announcement/result dates for the specific 2026 first-phase E-9 Manufacturing route.
- [ ] Verify current-cohort documents, medical providers, job application, CCVI/visa service-fee location and PDOT/departure rules; leave volatile values unknown otherwise.
- [ ] Run local-data gate and actual remote Chromium Playwright test suite.
- [ ] Obtain independent Nepali language/accessibility review by consenting educators who were already contacted (no new Nepal outreach).
- [ ] Reassess feature-by-feature beta readiness with a clear scope, then obtain explicit approval before opening Nepal beta or resuming recruitment.
