# KEP M19 — 2026-10-17 Official Watch And Release Hold (READ ONLY)

**Scope:** Indonesia → E-9 → General Manufacturing 2026. **Day:** 2026-10-17 Asia/Jakarta.
**Authorization:** machine observations only. This is NOT a human semantic source approval, manufacturing final-doc approval, deployment approval, or public beta OPEN.

## 1. GitHub and existing QA

- Previous M18 candidate HEAD before this work: `d27f94245654e4efb5df64a4b55a51512be374bc`; Draft PR #324 stays open/unmerged; Pages remains `main/docs` and public `main` matches nine core published assets.
- Historic 96/96 Edge UI candidate QA still applies to that candidate's verified code, not the public Pages `main` branch.
- Existing local M18 2026-10-16 official observation is a historical baseline, **not** an Oct 17 approval.

## 2. Today: actual 84-source scan

The official monitor was actually executed on the authorized Windows PC on **2026-10-17**, read-only with workers=6, perHost=1, retries=1. Result:

| Field | Actual observation |
|---|---|
| Configured | **84** |
| Fetched successfully | **84/84** |
| Fetch failures | **0** |
| Differences versus last *approved* source SHA baseline | **12** |
| Scope breakdown | 5 Korea-common, 2 multi-country HRD EPS, 5 other-country; 0 unclassified |
| `acceptedCurrent` | **false** |
| Source-hash baseline modified / operator signoff | **No / No** |

Exactly **three observed fingerprint values** differ from the **October 16 observation**: `lk_slbfe_home` (Sri Lanka), `np_eps_notice_index` (Nepal), and `vn_colab_eps_notices` (Vietnam). The remaining nine pending source fingerprints have the same observed SHA as October 16. This is a **comparison between two machine observations**, not a claim that exactly three substantive policies changed on October 17. All 12 continue to need semantic review against their accepted baseline.

Full unaccepted SHA pairs and source URLs are in `research/source_reviews/indonesia_daily_readonly_2026-10-17.json`. Raw probe output is kept outside the repo at `D:\KEP-M19-SOURCE-WATCH-20261017.readonly.json`. Neither official hashes nor rules were accepted or updated.

## 3. Today: KP2MI Pengumuman official index

The official `https://kp2mi.go.id/gtog-korea/pengumuman` DataTables source was re-fetched directly; pagination reached the previous-year boundary.

| Field | Actual observation |
|---|---|
| 2026 dated notice titles | **185** |
| General Manufacturing-related titles | **7** |
| Headline candidates explicitly naming final 2026 General Manufacturing online job application documents | **0** |
| Normalized title-list digest | `66793a544d0eed3859c4b3e8c50cd2f77ee90558081934ea6a3b45bbec49e13d` |
| Latest title in the inspected listing | Dated **2026-10-16**; worker departure on October 26/27, **not** the Manufacturing-specific exact `job_docs` checklist |
| Job-application content/attachment human review | **pending** |

This title digest matches the previous day's indexed titles, but a headline inventory cannot establish that all original HTML or annex PDFs are unchanged. Existing 2026-10-14 audits of seven HTML notices, optional Skill Test supporting PDFs and January initial-registration PDFs remain valid **prior technical review evidence only**, not human source signoff. Separate the mandatory Skill Test from optional Job Capacity Assessment; neither substitutes for final `job_docs`. Official 2026 Fisheries final online application and 2025 Manufacturing templates are different cohorts and MUST NOT be promoted as exact current-cycle Manufacturing requirements.

## 4. M19 reusable evidence gate

- Added `scripts/report_daily_indonesia_source_watch.py` to validate original raw scan and KP2MI results, date-align both observations in **Asia/Jakarta**, compare changed SHA pairs to accepted `monitor/source_hashes.json`, fail closed on unknown official source URL/duplicate ID, ensure no automatic approval, and generate a date-stamped append-only review artifact. The script cannot write into official SHA baselines or public app rules.
- Added offline committed-snapshot and manual-signoff validators, including rejection of stale dates, altered group counts, forged digest/URLs, and unsanctioned status flips.
- `scripts/report_indonesia_beta_release_preflight.py` now reads the M19 **actual-date** review-only snapshot separately from the still-**unsigned** `recruitment/ID_BETA_SOURCE_SIGNOFF_20261017.json` record.
- Historical October 16 watch **does not** satisfy October 17 or 18. A genuine 84/84 machine watch permits `official_monitor_today=PASS` but **never** elevates `indonesia_source_manual_signoff`, final Manufacturing annex signoff, Pages deployment or beta OPEN.

## 5. Observed release result — October 17

| Gate | Status |
|---|---|
| Route safety and official 27-step flow | PASS |
| Current-day official monitor & country grouping | **PASS** |
| Human source semantic signoff | **PENDING** |
| KP2MI Manufacturing final notice/attachment signoff | **PENDING** |
| `job_docs` exact evidence | **HOLD** |
| Published Pages `main/docs` 9/9 | **PASS** (healthy currently configured source) |
| Candidate release HEAD public parity | **PENDING** |
| Explicit beta OPEN | **HOLD** |

`READY_FOR_MANUAL_DECISION=False`, `LIVE_DEPLOYMENT_VERIFIED=False`, `authorizesRelease=False`.

## 6. Next responsible step

Review five Korea-common changed sources for rule impact, acknowledge the two multi-country HRD source pages and five other-country pending alerts, and have the actual authorized reviewer sign a scoped, dated manual review. For the seven Manufacturing notices, review missing original contents/annexes without copying 2026 Fisheries, 2025 Manufacturing or optional competency documents into final `job_docs`. Only a separate owner-approved production deploy followed by independent approved-HEAD 9/9 and HTTPS redirects 6/6 may progress release; final public beta OPEN needs its own explicit approval.

**No approval, production deployment, source hash promotion, public beta OPEN, applicant outreach or GitHub Actions spend from this M19 work.**
