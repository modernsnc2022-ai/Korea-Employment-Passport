# Korea Employment Passport — M16 Indonesia Official-Source Recheck (READ ONLY)

**Observation date:** 2026-10-16 (Asia/Jakarta) — **scope:** Indonesia → E-9 → General Manufacturing 2026.
**IMPORTANT:** This is evidence collection, not approval of source hashes, job-application document rules, Cloudflare deployment, applicant registration or beta access.

## 1. All 84 official sources

| Item | Actual observed |
|---|---|
| Configured and fetched sources | **84/84** |
| Fetch failures | **0** |
| Content fingerprint differences from persisted accepted baseline | **12** |
| Korea-shared candidate changes | **5** |
| Multi-country HRD Korea EPS candidate changes | **2** |
| Other-country changes, kept independently pending | **5** |
| Manual semantic review and source-hash acceptance | **PENDING / none accepted** |

The 12 differences are **relative to the last accepted source-hash baseline**, NOT twelve newly published notices since the preceding day. A hash difference does not prove a meaningful legal or EPS policy change.

### Pending source IDs

**Korea shared (5):** `minimum_wage`, `labor_standards_wage_statement`, `moel_wage_arrears_2026`, `kdca_qcode_input`, `moel_1350_contact`.

**Multi-country HRD Korea EPS (2):** `mm_hrdk_schedule_index`, `mm_hrdk_skills_candidates`. The `mm_` prefix must not be treated as Myanmar-only when the content spans multiple countries.

**Other-country (5):** `np_eps_notice_index`, `vn_colab_eps_notices`, `lk_slbfe_home`, `kg_migrant_home`, `mm_mol_dol_index`.

Source URLs and unaccepted baseline/observed SHA256 pairs are retained in `research/source_reviews/shared_source_watch_readonly_2026-10-16.json`. The prior 2026-10-15 record and accepted `monitor/source_hashes.json` were not altered.

## 2. KP2MI Pengumuman 2026 listing

| Read-only indicator | Actual observation |
|---|---|
| 2026 titles indexed | **185** |
| Rows read until 2025 boundary | **225** |
| 2026 Manufacturing-related headlines | **7** |
| Explicit 2026 General Manufacturing final job-application document announcement titles | **0 detected** |
| Full source body and annex PDF human signoff | **PENDING** |

Seven official Manufacturing-related title/URL/date records are listed in `research/source_reviews/kp2mi_2026_manufacturing_index_readonly_2026-10-16.json`. The 2026-09-17 Skill Test supporting competency-document upload announcement is **NOT** the final job-registration `job_docs` notice. This title inventory does not verify that all original notice bodies or annex PDFs have been reviewed.

## 3. Release preflight

| Gate | After this read-only observation |
|---|---|
| `route_safety` | PASS, 27 steps, exact `job_docs` HOLD |
| `country_source_classification` | PASS (12 candidates scoped, none accepted) |
| `official_monitor_today` | **PASS** after validated Oct 16 84/84 observation |
| `indonesia_source_manual_signoff` | **PENDING** |
| `kp2mi_manufacturing_release_day_signoff` | **PENDING** |
| `optional_skill_annex_evidence` | PASS — never final `job_docs` |
| `same_head_pages_deployment` | **PENDING** |
| `explicit_manual_beta_open` | **PENDING / beta HOLD** |

**READY_FOR_MANUAL_DECISION=False. LIVE_DEPLOYMENT_VERIFIED=False.**

## 4. Required operator actions

1. The responsible reviewer personally examines the five Korea-common sources and acknowledges the two multi-country HRD sources; five foreign-country records remain independently pending. Only a genuine signed release-day review can clear source signoff.
2. A reviewer opens the seven current-cycle Manufacturing official notice pages and any source attachments. Keep final `job_docs` HOLD unless a specifically applicable current 2026 official announcement documents that stage.
3. Separately approve an appropriate Pages deployment and independently confirm the same HEAD on nine live assets and six redirects.
4. Only after all gates pass may a responsible operator make a **new, explicit** public beta OPEN decision. Nothing in this M16 report authorizes it.
