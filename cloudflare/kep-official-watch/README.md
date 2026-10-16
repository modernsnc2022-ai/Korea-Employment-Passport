# KEP official change monitor — M4 Cloudflare Worker (DISABLED, not deployed)

This independent Worker watches **KP2MI Pengumuman new/edited notices** and **HRD Korea EPS-TOPIK schedules**, including still-accessible official 2026 Indonesia General Manufacturing Jakarta/Semarang details absent from the newest six-page HRD index. This is discovery only: **it cannot approve laws or publish country-pack rules**, turn on beta, send applicants email, or accept monitored source hashes.

## Explicit operational state

- Code and migration are **not deployed**; no Cloudflare account, database, credentials or scheduled Cron trigger were created or altered.
- The example Wrangler config is intentionally named \`wrangler.example.jsonc\`, not active. It contains \`triggers.crons=[]\`, \`MONITOR_ENABLED=false\`, an unusable D1 UUID placeholder, \`workers_dev=false\`, and \`preview_urls=false\`. Public Worker HTTP requests return 404 even after eventual deployment.
- D1 binding **MONITOR_DB** must point to a newly created *separate* monitor-only D1. Do not bind the private \`kep-beta-intake\`, \`kep-beta-email-verifier\`, applicant D1 or OTP secrets.
- A scheduled invocation does not perform any fetch until \`MONITOR_ENABLED\` is explicitly true and a real D1 binding exists. **Never deploy or enable** on an implicit "next"; the owner must authorize the isolated monitor deployment and regular official-site traffic.
- The script reads **50 most recent** KP2MI notice rows and six HRD pages plus relevant pinned Indonesian official details per run, with 12-second request timeouts and 5MB body cap per response. No whole-year or all-84-source coverage is claimed.
- Every source fetch must complete successfully before a single transactional D1 batch updates the last-good complete snapshot and deduped **review-only queue**. A source failure records the failure type and preserves the previous success. A disappearing notice from a bounded listing is **not** treated as official cancellation.
- On first run, all current records seed a baseline without creating alerts. Afterward each unique source-record revision is inserted at most once even if it reappears. There is no operator dashboard/Google Sheet sync yet. **No notifications** are sent by this Worker. The existing ChatGPT monitoring automation is separate.
- Cloudflare D1 batch transactions are all-or-rollback. Wrangler's scheduled handler uses UTC Cron timing. See [Cloudflare D1 database batch](https://developers.cloudflare.com/d1/worker-api/d1-database/#batch), [scheduled handlers](https://developers.cloudflare.com/workers/runtime-apis/handlers/scheduled/).

## Offline tests

Run from this directory:

\`node --check src/index.mjs\`

\`node --test test/*.test.mjs\`

No \`npm install\`, paid GitHub Actions or Cloudflare login required.

## Later owner-approved activation plan (NOT EXECUTED)

1. Security/code review and confirmation of allowed official source polling frequency; inspect any official robots/traffic rules.
2. Create a **new isolated** monitor D1 in Cloudflare, apply \`migrations/0001_init.sql\`, and replace the UUID in a real private Wrangler config. **No existing Worker modifications.**
3. Start with a guarded **hourly or 2-hourly** UTC Cron (e.g. \`0 */2 * * *\`) only after owner approves it. Set \`MONITOR_ENABLED=true\` only after migration verification. No public routes.
4. Validate one authorized synthetic scheduled invocation with \`wrangler dev --test-scheduled\`, then real Cron invocation, observed D1 last-success timestamp, queue dedup and failure health. Cloudflare Free per-invocation network-subrequest/CPU quotas and official site rate limits must be verified for the actual account and workload.
5. Add a **private** operator alert transport and fail-closed scheduler-health watchdog before relying on it for deadlines. Keep all regulatory/source signoffs and beta release gates independent.

**Current P0 state:** official human review/signoff PENDING, \`job_docs\` HOLD, beta access HOLD, direct HTTPS intake OFF, Draft PR unmerged.

## 2026-10-16 manual Windows runtime smoke (read-only; not a Cloudflare deployment)

- Node 24.18.0 offline test command: \`npm test\`: **6/6 PASS**.
- Independent Python SQLite executes \`migrations/0001_init.sql\` against a temporary SQLite DB: **PASS** for the three tables and unique-review-revision deduplication.
- Direct Node.js \`fetch\` on the authorized Windows PC initially failed with \`UNABLE_TO_VERIFY_LEAF_SIGNATURE\` using Node's bundled CA store. It was **not** resolved by disabling TLS validation. Running \`node --use-system-ca test/live-readonly.mjs\` preserved TLS validation and returned **KP2MI 50 records, HRD Korea 58 schedules, PASS**. Local Windows certificate setup differs from the real Cloudflare Workers runtime; this does **not** prove a deployed Worker will connect successfully.
- Current official-site scan is deliberately bounded: 50 newest KP2MI notices, 6 HRD Korea schedule pages, and pinned 2026 Indonesia General Manufacturing Jakarta/Semarang official details. It is not the legacy 84-source monitor and cannot guarantee alerts for older, backfilled notices.
- All tests are offline by default; \`test/live-readonly.mjs\` is **manually invoked only** and is excluded from \`npm test\` by filename. No outbound alert, Cron activation, source signoff or KEP beta release was performed.
