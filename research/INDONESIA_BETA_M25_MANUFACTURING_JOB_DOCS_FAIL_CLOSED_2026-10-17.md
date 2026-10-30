# KEP M25 — 2026 Indonesia Manufacturing final job application fail-closed user guidance

**Evidence day:** 2026-10-17. **Change type:** draft candidate application safety fix, not approval or publication. **Source:** independent M24 live KP2MI `Pengumuman` inventory at https://kp2mi.go.id/gtog-korea/pengumuman (320 titles checked, 7 General Manufacturing titles, 0 explicit current-cohort final online job document checklist titles, 3 other-cohort online application notices).

## Defect observed

Applicant-facing job application stage and associated document pack were still linking to https://kp2mi.go.id/gtog-korea/info despite a later verified official index https://kp2mi.go.id/gtog-korea/pengumuman. This could misdirect a candidate while the exact required 2026 General Manufacturing final documents remain unconfirmed. No source evidence justified upgrading `job_docs` or the release.

## M25 scoped changes

1. **`docs/data/id_e9_manufacturing_2026.json`** — corrected *both* `job_application.sourceUrl` and `job_application.officialActionUrl` to the actually checked official `Pengumuman` index. Clarified Indonesian link text: candidates must choose a notice specifically applying to 2026 Manufacturing. The route keeps `brokerReplacement=held_official_notice`, and its warning still tells candidates not to submit until the exact checklist is verified.
2. **`docs/data/document_packs_2026.json`** — fixed `job_application_manufacturing.sourceUrl` to the same official `Pengumuman` index. Retained `status=awaiting_sector_notice`, `items=[]`, and the older `lastChecked=2026-10-06` because the 2026-10-17 title scan is **not** a verified final document checklist. An unrelated visa-related `/info` link is intentionally untouched; the M25 evidence does not establish a replacement for it.
3. **`docs/app-runtime.js`** — added an **independent route-level fail-closed rule** within the real `evaluatePreSubmit(stage)` function: a `job_application` stage marked `held_official_notice` **cannot pass the pre-submit check even if a document pack status is erroneously set to `verified` and all checklist questions appear answered**. Existing document-pack checklist guards remain intact. Exact-answer status badges now explicitly label cross-cohort safety guidance as **not** the exact Manufacturing 2026 requirements and the final document list as HOLD.
4. **`docs/sw.js`** — prepared offline cache `kep-v139` to refresh this candidate when a *separately approved* deployment occurs. This does **not** perform deployment.
5. **`scripts/test_m25_job_docs_safe_links_and_submit.js`** — executes real shipped `safeDocumentPack`, `documentPackForStage`, `evaluatePreSubmit`, and `exactVerificationLabel` functions in a sandbox with the actual candidate JSON. Tests verified the official link three times, real job-stage HOLD, intentionally poisoned `verified` pack state, source-review risk, three Indonesian status labels, live M24 scope boundaries and 12 hostile data mutations. Confirms the real stage complete button still uses the pre-submit gate.

## Policy boundaries

- Jan 27 original EPS-TOPIK registration documents **do not** become post-Skill Test final online job application requirements.
- Sep 17 optional competency evidence window is CLOSED; conditional forms are never mandatory for everyone.
- Fisheries 2026, Root Industry 2026 and Special UBT 2026 online application announcements do not authorize General Manufacturing 2026 exact job documents.
- At release time, current official original pages/appendices, accountable human source semantic review, and explicit approval are still required. No synthetic signoff or automatic source hash acceptance.
- Existing public interest intake OPEN is distinct from applicant **beta access HOLD**.

**M25 expected operational gates:** `job_docs=held_official_notice`, `betaAccess=HOLD`, Draft PR #324 unmerged, no GitHub Actions, no Cloudflare/Pages production deployment, no public beta OPEN.
