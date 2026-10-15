# KEP beta applicant-interest private intake (Cloudflare Workers + D1)

**2026-10-15 owner dashboard setup — Cloudflare `kep-beta-intake` shell exists, but the actual applicant-intake code has NOT been deployed or enabled.** The owner has created a separate private D1 `kep-beta-applications` table and bound `KEP_BETA_DB`; the `EMAIL_VERIFIER` service binding points at the separately deployed private `kep-beta-email-verifier` with default entrypoint. Owner confirmed `INTAKE_ENABLED=false`, the encrypted `INTAKE_HMAC_SECRET` and matching-call-secret name (equality to the verifier cannot be read back from Cloudflare), and allowlisted origins. Both Workers' public production/preview URLs are OFF. **A completed binding or passing offline test is not evidence of a live integration test.** The public `docs/data/beta_program_v1.json` retains `application.directIntake.endpoint=""`, `turnstileSiteKey=""`, beta access `status="hold"`; the approved interest path remains email fallback. Turnstile creation, intake code deployment, authorized synthetic-only QA and explicit intake/beta OPEN remain separate future gates.

## Why D1 instead of the earlier KV draft

The earlier KV Worker generated a new receipt for every submit and wrote records under random keys, so it did **not** deduplicate the same applicant and could not serialize concurrent duplicates. This implementation replaces KV with a private Cloudflare **D1** SQLite table. `email_hmac` is an HMAC-SHA256 digest from a **private secret** and a normalized contact email, protected with the SQL `PRIMARY KEY` uniqueness constraint. Atomic SQLite `INSERT ... ON CONFLICT... WHERE expires_at_ms<=... RETURNING` inserts a new receipt or preserves the original receipt for an unexpired duplicate. A genuine duplicate returns HTTP 200 with the same receipt. D1 failed writes never return a positive receipt.

**Do not import historical KV entries** without a separate owner-approved private-data migration and privacy review; the publicly configured direct Worker endpoint has never been enabled. Never confuse a test receipt with an issued KEP participant identifier or beta activation.

## Server enforcement

- **Fail closed by default:** `INTAKE_ENABLED=false`, no real production URL in `beta_program_v1.json`. Missing database, HMAC signing secret, Turnstile secret, or HTTPS origin allowlist returns HTTP 503. `/health` reports `acceptingApplications=false`; a working health check is NOT permission to receive personal data.
- **HTTPS exact origins:** `ALLOWED_ORIGINS` uses `https://www.gdglobal.kr` and, for legacy site compatibility, `https://modernsnc2022-ai.github.io`. No wildcard CORS, no credentials or unauthenticated state-changing GET requests. **CORS by itself is not spam protection**; Cloudflare Turnstile's `siteverify` response also must have `success=true` and hostname equal to the allowed Origin hostname.
- **No remote IP:** Turnstile is called **without** `remoteip`, and no client-IP header, URL, user agent, cookies, device fingerprint, Turnstile response token, or raw request body is included in the D1 record. Cloudflare account/network logs and backups have separate provider-level privacy/retention controls which still need owner review.
- **Data minimization:** only contact email, known route stage ID, EPS cycle (`2026`/`2025`/`2024`/`unknown`), non-identifying source code, private HMAC hash, opaque submission receipt, original receipt timestamp, and expiry timestamp. Browser-supplied free-text `stageTitle` is not retained. Reject unknown fields, identity numbers, address, medical, passport/KTP/ARC images or arbitrary attachment/file data. Request size limit **4 KiB**, verified against the actual UTF-8 body even when Content-Length is absent.
- **Automatic retention:** `expires_at_ms` is exactly original receipt time + **90 days**; a daily UTC cron deletes expired rows. Re-submission after expiration can create a fresh record even before scheduled deletion. D1 point-in-time backups/platform logging require a separate policy check.
- **Duplicate receipt privacy:** only a Turnstile-cleared requester who knows the same email can get the existing receipt. This does **not** verify ownership of that email. **Do not approve KEP IDs, send private data, or enable real intake until the owner approves an email-ownership verification/invitation and anti-abuse workflow.** Use Cloudflare dashboard/WAF/rate controls and monitor abuse before a real public POST.
- **No automatic KEP ID or beta OPEN:** receipt format is `KEP-I-[A-F0-9]{32}`, distinct from approved participant KEP-0001 etc. Records stay private; a real operator reviews and contacts applicants by an approved private workflow. Never commit email or token/payload to public Git or the shared spreadsheet.

## Run offline tests (no Cloudflare login or Actions budget)

From `deployment/cloudflare/intake-worker`:

```bash
node --test test/worker.test.mjs
```

The 12 Node-native tests verify health fail-closed, explicit CORS, sensitive field rejection, body-size limits, honeypot, fake Turnstile and hostname failure, absence of IP persistence, actual receipt and duplicate behavior, concurrent duplicate attempts in a controlled fake-D1 state machine, 90-day replacement/deletion and safe D1 errors. Also validate the **actual SQL schema and UPSERT statement against local SQLite** with the separate integrity script before deployment; mock results alone are not proof of a live D1 instance.

## Deployment preparation (DO NOT RUN WITHOUT EXPLICIT OWNER APPROVAL)

1. Confirm Cloudflare account, billing/free-tier and personal-data jurisdiction, privacy notice, private review workflow, email-ownership verification, WAF/rate-limiting and 90-day backups/log policies.
2. After approval, from this directory run `npx wrangler login` and `npx wrangler d1 create kep-beta-applications` using your own Cloudflare account. Do not paste tokens or real emails into the terminal transcript.
3. Copy `wrangler.toml.example` to your **private** `wrangler.toml` and set the private D1 database ID. Never commit account/resource IDs or secrets.
4. Apply `npx wrangler d1 migrations apply kep-beta-applications --remote`; verify private table and unique index exist before configuring intake.
5. Set `npx wrangler secret put INTAKE_HMAC_SECRET` (cryptographically random >=32 characters) and `npx wrangler secret put TURNSTILE_SECRET` (Turnstile secret from the correct site). **Do not rotate the HMAC secret without a reviewed data migration**: a new secret changes all deduplication keys.
6. Keep `INTAKE_ENABLED="false"` and deploy to an isolated test URL only after approval. Verify `GET /health` says `acceptingApplications:false`; no real personal data is sent.
7. Configure the public Turnstile **site key** in `beta_program_v1.json` *only after* site-hostname ownership and test confirmation; the beta page loads the Turnstile widget dynamically **only in direct mode**. Exercise mock and authorized synthetic D1 POST tests, CORS, mobile access, error handling, Cron retention and duplicate behavior on an isolated environment.
8. Only with a second explicit approval and completed email-ownership/abuse/privacy review, switch `INTAKE_ENABLED=true`, configure the correct HTTPS endpoint, and publish the updated frontend. This activates **interest intake only**, **never beta product access**. Verify real published frontend and backend together; keep `beta_program_v1.json.status="hold"` until the separate official source/deployment release gates and manual OPEN are satisfied.

A failed POST shows “Data belum dianggap terkirim” and preserves the form for the user's Gmail/copy fallback. A successful D1 insert returns `{"ok":true,"submissionId":"KEP-I-..."}` with HTTP 201; unexpired duplicate returns the same receipt with HTTP 200 and `duplicate:true`. Frontend requires a validated receipt and never claims a clicked email composer was sent.

**Never deploy from the unmerged Draft PR, create a real Cloudflare resource, enable direct intake, activate the 6-month entitlement or use GitHub Actions without the relevant owner approval.**
