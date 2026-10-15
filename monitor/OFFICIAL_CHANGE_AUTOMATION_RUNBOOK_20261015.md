# Korea Employment Passport — official change monitoring operations (design, NOT deployed)

**Status (2026-10-15 KST): PROPOSAL / NOT RUNNING ON A CLOCK.** Maintained in Draft PR #324. No cron, Cloudflare worker, source hash acceptance, application rule change, notifications, PR merge or beta OPEN is authorized by this document.

## Verified existing implementation and critical gaps

- `monitor/sources.json`: **84 monitored source ID→URL targets**. `scripts/check_official_sources.py` fetches normalized text/PDF hashes and compares against the reviewed baseline. `scripts/write_source_review_status.py` emits fail-closed public data status; `autoPublishRules=false`.
- `.github/workflows/official-source-monitor.yml`: **`workflow_dispatch` only**, no `schedule` stanza. Its GitHub issue alert/commit workflow operates **only when manually invoked**; it is not unattended 24/7 surveillance. Avoid scheduling hosted GitHub Actions, given prior GitHub Actions budget pressure.
- `kp2mi_gtog_korea_info_index` currently targets **https://kp2mi.go.id/gtog-korea/info**, a **Preliminary Training dan Info** category rather than the core **https://kp2mi.go.id/gtog-korea/pengumuman** announcement index. The real `Pengumuman` listing is populated via **https://kp2mi.go.id/gtog-data/korea/Pengumuman** (server-side DataTables JSON), so a static hash of `/info` or a blank HTML shell **cannot detect every new notice**.
- `mm_hrdk_schedule_index` tracks an HRD Korea **multi-country** exam schedule. Treat country/cycle/sector/exam-type metadata as part of the event key, not the misleading `mm_` prefix. Confirmed 2026 Indonesia General Manufacturing CBT Jakarta and Semarang records; specialized Root Industry and other-country announcements must not be promoted into this route.
- `scripts/audit_id_manufacturing_notice_index_live.py` is an existing **read-only, on-demand** bounded listing check; last Oct 15 inventory was 320 rows crossing the 2025 boundary, seven general Manufacturing 2026 notices, three other-cohort application notices, zero exact general Manufacturing 2026 post-Skill-Test application-title candidates. It has **no continuous scheduler or durable new-notice checkpoint**.
- Public source fetch or fingerprint drift is **not official-fact approval**, and a failed fetch is **unknown**, never clean.

## Deployment design — independent of paid GitHub Actions

Use a **dedicated isolated Cloudflare Worker Cron Trigger** for a lightweight fast discovery job, plus a durable **separate D1/KV monitoring namespace**. Do not reuse or turn on the disabled private beta-verifier/intake Workers. Free Workers currently have small per-invocation CPU and subrequest quotas; verify actual account limits, use bounded paginated and rate-limited batches, and record explicit failures instead of swallowing them. Cron runs in UTC; convert source dates and user presentation in Asia/Jakarta (WIB) and Asia/Seoul (KST) as appropriate.

| Proposed cadence | Source | Detect / persist |
| --- | --- | --- |
| Every 1–2 hours while time-sensitive | **KP2MI `Pengumuman` public DataTables** | New/removed/edited notice IDs, official publication date/title/details link; fetch newly discovered relevant article HTML and appendix links, original publication timestamp and source digest |
| Every 1–2 hours | **HRD Korea EPS-TOPIK schedules**, scoped listing and detail | New exam record or changed signup dates, exam dates, result dates, country, cohort/sector and type; reconcile official KP2MI notice for Indonesia applicants |
| Daily | **84 source targets**, batched by host | Validated TLS/HTTP availability, stable normalized hash, substantive text changes, changes in selected official PDF bytes; important unchanged sources still checked |
| Weekly; release-day mandatory | Korea E-9 law/benefits/immigration and notices | Effective date/version, changed legal conditions, employment rights, sector applicability and retroactivity |
| After every relevant official publication | Affected stages/country pack | Revision log, review ticket, negative tests and deployment parity; push or email user alerts **only after content is validated and user has opted in** |

Initial rollout may use daily fast discovery instead of hourly if rate limits demand it; do **not** claim an SLA faster than the actual selected deployment schedule.

## Comparison, alerts and change classification

1. **Observation checkpoint, not an approval baseline:** Store `sourceId, country, sector, cohort, examType, noticeId, publishedAt, retrievedAtUTC, link, normalizedSHA, optionalAttachmentsDigest, previousObservationId` and a `new|edited|deleted|fetch_failed|unchanged` event. `fetch_failed` must keep the last known evidence but flag freshness failure.
2. **Two-stage classifier:** bounded automatic title+HTML metadata triage, then person/AI-assisted semantic review. `Indonesia + 2026 + General Manufacturing` must never be inferred from title substring alone; check official notice body/annex and route applicability. Special, Fishery, Root/Mold and another year are different records.
3. **Priority levels:** P0 immediate = new opening/closing/change of application, exam schedule or mandatory docs; P1 same day = important process/eligibility/fee/legal update; P2 batch = general page change/site maintenance; fetch/security failures show a separate warning, **never as a policy change**.
4. **Deduplication:** One event for the same official notice revision, alert only on new revision or meaningful priority change. Preserve original sources, before/after diffs, timestamps and reviewer identity. No repeated daily alert for unchanged items.
5. **Operator inbox:** Create a review queue in the single KEP Google Sheet and/or GitHub issue (use secure server-side credentials, never public JS). A production monitoring dashboard must be designed so it does not expose applicant personal data.
6. **Publish gate:** P0/P1 rules are **not published automatically**. Reviewer verifies official source, cohort scope, pdf details, effective date and draft translation; structured rule edits undergo country/sector regression, reviewed PR, approved deploy, 9/9 live asset parity and HTTPS safeguards. User notices are only sent after verified publication.
7. **Candidate-facing truthfulness:** show each date's official link, published/last-checked timestamp, timezone, upcoming/closed status and **uncertain** if evidence cannot be refreshed; never label a past window as open. Keep `job_docs` HOLD pending a verified 2026 general Manufacturing post-Skill-Test final application notice.
8. **Urgent rollback:** when a new official notice conflicts with a critical displayed instruction, temporarily mark the affected step `review_required`, visibly direct applicants to the government website and escalate; do not silently continue outdated guidance.

## Required development milestones (NOT completed)

- M1: add correct `Pengumuman` **JSON listing discovery with stable notice identity and date-bound pagination**, not just a hash of a 200-status HTML shell. Keep legacy `/info` as separate info-channel target if useful. Attach route-scope tests.
- M2: add HRD Korea **country/cycle/sector/type-aware** schedule discovery and detail change identification, including existing Jakarta and Semarang general Manufacturing records. Test specialized Root/Mold and other-country exclusions.
- M3: build persistent observations and fail-closed regression tests for first run, new notice, changed notice, retraction, 502/timeout, time zones, malicious link and duplicated notices. Observation checkpoint **must not modify approved source hashes**.
- M4: design Cloudflare Cron Worker scheduled handler, secrets, D1/KV and bounded fetch budget; test without enabling public prod or private applicant intake. Do not use GitHub Actions for frequent scans.
- M5: add operator daily digest and **P0 push on real material changes**, plus no-change heartbeat and watchdog for scheduler failure. Real outbound sends require owner authorization, secure provider, deduplication and meaningful subscription settings.
- M6: after separate owner approval, deploy monitor only (not the beta app), verify actual timed schedule, change notifications, deduplication, freshness and failure escalation. Record observations to the integrated ledger.

**Current actual state: code can perform manual checks; automatic schedule NOT deployed; all beta and official-approval HOLD gates preserved.**
## Implementation checkpoint: 2026-10-15 (Draft PR, no scheduler)

- Added `scripts/watch_id_official_discovery.py` as a **read-only on-demand** KP2MI official announcement index / HRD Korea EPS-TOPIK listing-detail comparison tool.
- Fetches **actual official KP2MI DataTables JSON**, not the misleading `/info` page or an empty HTML shell. Keeps only notice metadata and normalized body digest; never saves the raw body or applicant example personal data. Uses existing 2026 Manufacturing title/other-cohort classifier as a separate route guard.
- Paginates six published HRD Korea schedule pages and independently pins currently discoverable 2026 Indonesia General Manufacturing Jakarta (`examNot=14`) and Semarang (`examNot=15`) **official detail pages** because these older schedules are not reliably listed among recent pages. Does not turn Root Industry/Mold or other sending-country exams into General Manufacturing instructions.
- Produces a canonical `observation`, not an accepted official-source baseline. On first run no mass alerts; on later runs only new/modified notice IDs or schedule keys are review events. A notice missing from a bounded listing window is **not called deleted**. Wrong official hosts, bad pagination, missing data and failed detail fetches fail closed.
- The first authorized-Windows live execution returned **KP2MI 320 rows + HRD Korea 59 schedule records + 9 relevant Indonesia General Manufacturing items**, in an **external local temp JSON observation**. No backend writes, notifications, prod deployment or SHA approvals. Offline dedicated regression **9/9 PASS**, plus built-in structural self-test PASS. `node_modules` or GitHub Actions are not needed for the watcher test.
- Running the script manually:
  - `python scripts/watch_id_official_discovery.py --self-test`
  - `python tests/test_official_discovery.py`
  - `python scripts/watch_id_official_discovery.py --live --output <external-temp-file.json>`
  - Subsequent difference check: `python scripts/watch_id_official_discovery.py --live --previous <previous-external-temp-file.json> --output <new-external-temp-file.json>`. Keep previous and new paths distinct; never write the accepted manifest.
- **Not complete:** scheduled Cloudflare worker, persistent independent D1/KV checkpoint, retry/recovery watchdog, human-review notifications, admin approval control, full 84-source unified operations, and approved production deployment. Present source-scope and beta release HOLD gates remain unchanged. A future annual cohort rollover must receive separate review/coverage updates.

## Local durable queue implementation checkpoint (2026-10-15, Draft only)

- `scripts/official_discovery_state.py` adds a **standalone SQLite observation checkpoint, immutable deduplicated pending-review events and monitor health** outside the repository. This is not the beta applicant D1/OTP database, not a Cloudflare Worker and **not a human/official approval record**.
- `scripts/watch_id_official_discovery.py` adds `--state-db <external.sqlite3>`, `--list-pending`, `--health` and `--stale-hours 4`. The live scan runs **before** changing the checkpoint; a successful full KP2MI+HRD scan is atomically committed with its review events. Failed or incomplete scans preserve the last successful snapshot and set a consecutive-failure flag; the health check exits non-zero if unhealthy/stale. KP2MI must supply the full requested 320 row bounded window while the official historical total is larger.
- First observation seeds the checkpoint without creating a historical notification flood. Each unique source-ID+revision content creates at most one pending review event, even if it reappears; moving out of a bounded listing window is **not treated as government deletion**. The script cannot approve laws, update app rules, accept source SHA, or send messages.
- Offline regression suite: `python tests/test_official_discovery_state.py` and `python tests/test_official_discovery.py`. Include first seed, new notice, changed notice body, repeated observation, revert/repeated revision, bad source identity, stale timestamps, fetch failures and recovery, wrong country/sector and no automated beta.
- Manual isolated operator examples (choose external private local paths, and run only when requested):
  - `python scripts/watch_id_official_discovery.py --live --state-db C:\\path\\outside-repo\\monitor.sqlite3`
  - `python scripts/watch_id_official_discovery.py --state-db C:\\path\\outside-repo\\monitor.sqlite3 --health`
  - `python scripts/watch_id_official_discovery.py --state-db C:\\path\\outside-repo\\monitor.sqlite3 --list-pending`
- **Never treat these commands as an enabled scheduler.** Cloudflare Cron + external D1/KV operations store, secure review queue integration with the existing unified Sheet and actual outbound notification delivery are **not deployed or scheduled**, and require separate owner approval. Free GitHub Actions budget remains untouched. Existing source-manual-signoff, deployment parity and beta OPEN HOLD controls remain unchanged.

### Live SQLite checkpoint smoke test — 2026-10-15 (manual only)

Executed against **current official public sources**, no scheduled or production monitoring: `python scripts/watch_id_official_discovery.py --live --state-db <external-temporary-sqlite>` followed by `--health` and `--list-pending`. Output **KP2MI 320 + HRD 59**, nine total 2026 Indonesia General Manufacturing related entries (KP2MI seven + pinned HRD Jakarta/Semarang two); first observation `eventsDetected=0, newQueued=0, pendingTotal=0`, monitor health `healthy=true`, consecutiveFailures=0, latest successful UTC observation **2026-10-15T08:01:28.593265+00:00**. All data stored only on the authorized PC in a local temp SQLite file, not in GitHub or public app. This proves **manual persistent checkpoint operation**, **not** unattended scheduled scanning, actual alert delivery, or all 84-source monitoring. No live rule changes or signoff occurred.
