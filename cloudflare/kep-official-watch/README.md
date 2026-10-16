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

## 2026-10-16 actual workerd + Wrangler local-only staging verification

**This section is about localhost, not Cloudflare production.** Wrangler 4.151.0 was installed in a separately isolated Windows Temp directory; its scripts, configs, local D1 DBs and test workers were never committed. All Wrangler commands used the explicit \`--local\` flag; no remote resource API call, migration or deployment was performed.

1. **Real D1 local migration:** \`wrangler d1 migrations apply MONITOR_DB --local --config <local-temp-config> --persist-to <local-temp-storage>\` returned 0001_init.sql **PASS**. Verified 3-table schema in D1.
2. **Production entrypoint failed first runtime compile:** real workerd complained about named module exports of string constants \`KP\`, \`HR\`, \`HD\` (\`Incorrect type for map entry 'HD'\`). Those exports were changed to private constants accessible in tests via a callable \`sourceUrls()\` function; \`wrangler dev --test-scheduled\` then reported **Ready**.
3. **Disabled local Worker \`MONITOR_ENABLED=false\`:** HTTP \`GET /\` returned **404**, local simulated \`GET /cdn-cgi/local/scheduled\` returned **200**. This validates only trigger entry/disabled guard, not actual internet or D1 writes.
4. **Enabled Worker fetching actual public official sites:** a local simulated scheduled event returned **500**, revealing a second workerd runtime incompatibility: Cloudflare fetch does not support \`redirect: "error"\`. Fixed to \`redirect: "manual"\` plus explicit 3xx rejection without unsafe following. With this fix, a second enabled local real-official-fetch test still returned **500** with workerd \`internal error; reference ...\`, cause **NOT YET RESOLVED** in the Windows local network runtime. The local D1 health table correctly showed **2 consecutive errors, no successful snapshot**. **Do not claim the real-source Cron path works or that it has been deployed.**
5. **Synthetic end-to-end workerd integration in separate local-only test entrypoint** \`test/workerd-staging-entry.mjs\`: it imports the **same production \`processSchedule\` function** and substitutes static synthetic official-shaped test responses to isolate network transport from D1 and Cron. A separate temporary local Wrangler config with \`MONITOR_ENABLED=true\` and local-only D1 was migrated; two explicit \`/cdn-cgi/local/scheduled\` calls returned **HTTP 200**. Queried actual local D1 with Wrangler after the second run: \`snapshots=1, queued=0, failures=0\`. The first run seeded one complete snapshot without old-news flood, the repeated identical revision did not generate a review event. This is **synthetic data**, not a newly discovered real KP2MI announcement or policy change.
6. The Node offline unit suite includes manual-redirect/3xx reject regression, in addition to disabled-mode, cohort and host isolation, duplicates and errors. Test source does not depend on network; \`test/live-readonly.mjs\` is deliberately excluded from \`npm test\`.

**Next non-production work:** diagnose real-official egress from local workerd (do not turn off TLS); implement an operator-accessible failed-scan watchdog and an isolated Cloudflare staging-only setup upon **explicit separate owner consent**, verify Free CPU/subrequest limits on the actual account, and prove at least one real Cron scan plus D1 transaction end-to-end before calling continuous official monitoring operational. Never merge beta PR or turn on applicant intake as part of monitor deployment.

## 2026-10-16 confirmed KP2MI origin TLS chain defect and independent source recovery

- **Root-cause evidence:** On the authorized Windows PC, OpenSSL 3.6.3 \`openssl s_client -connect kp2mi.go.id:443 -servername kp2mi.go.id -verify_return_error\` produced \`verify error:num=20:unable to get local issuer certificate\`. The origin presented **only 1 leaf certificate**, subject CN \`*.kp2mi.go.id\`, issued by \`GeoTrust TLS RSA CA G1\`, valid **2026-05-20 through 2026-12-03**. The intermediate chain needed to establish trust was absent from the server-provided handshake. HRD Korea presented **3 certificates** and OpenSSL validation returned success. A Windows OS trust store or cached intermediate may allow curl/Node \`--use-system-ca\` to reach KP2MI, but Cloudflare local \`workerd\` failed with \`internal error; reference ...\`. **Do not circumvent TLS authentication, follow insecure redirects, trust an arbitrary mirror or interpret a failed fetch as fresh policy evidence.** Cloudflare production egress behavior remains unproven.
- **Security-respecting solution while origin is not fixed:** schema \`migrations/0002_source_isolation.sql\` creates **separate \`monitor_source_snapshot\` and \`monitor_source_health\` records for \`kp2mi\` and \`hrdk\`**. The scheduled Worker now uses exported \`processSchedulePartitioned()\`. An unavailable government host increments *its own* failure count and preserves its old checkpoint, while an independently successful host may atomically checkpoint and enqueue reviewer-only changes. An aggregate \`status: degraded\` causes the scheduled event to fail visibly; **it never signals that all official sources are current**. No user notification, official-source SHA acceptance or application publication is automatic.
- **Source change isolation tests:** synthetic Node regression includes (a) failure KP2MI / real-shaped HRD content revisions enqueue review, (b) failure HRD / KP2MI revised notice independently enqueues review, (c) first-run with one source offline followed by recovery seeds the previously missing source without a historical alert flood, (d) disabled config fetches nothing.
- **Real \`workerd\` staging with separate temp D1**: Applied 0002 migration using **\`wrangler d1 migrations apply --local\`** (PASS). A *test-only* synthetic Worker endpoint forced KP2MI failure and introduced a 2026 HRD manufacturing schedule change. Two \`--test-scheduled\` invocations completed; local D1 SQL showed **2 review queue events, both route-relevant**, HRD success and KP2MI 1 failure with its previous snapshot retained. These synthetic records are **not current public announcements**.
- **Real official network attempt with new production split scheduler, local-only:** Cron returned HTTP 500 deliberately because KP2MI is still untrusted, but **the genuine HRD Korea public schedule observation was independently stored** in its source checkpoint; source health read-back showed HRD Korea success/zero failures and KP2MI no success/one failure. This demonstrates partial real-source continuity and explicit degraded alerting. It does **not** prove official KP2MI is safely retrievable from Cloudflare, an unattended Cron installation or any approved KEP product changes.
- **Remediation dependency:** the operator of **kp2mi.go.id** should install the proper DigiCert/GeoTrust intermediate certificate(s) and serve the complete verified TLS certificate chain. An informational technical-support request can be considered, but **no message was sent** by this development work. Independently retest with OpenSSL and actual Cloudflare staging before any production claim. The existing separate ChatGPT official-notice condition-watch remains a provisional safety net; it is not a deployed Cloudflare app and has no ability to accept rules or open beta.
