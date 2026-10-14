# KEP Indonesia beta — private email ownership verification

This directory implements server-verified ownership of applicant email before a
private receipt can be created or retrieved. It is a separate **non-public**
Cloudflare Worker used solely through the intake Worker's `EMAIL_VERIFIER`
service binding. Never expose `/action` on a public route.

## Two delivery options (choose one when approved)

- `wrangler.resend.toml.example` — **preferred free beta option**. Resend
  currently allows 100 transactional emails/day and 3,000/month on Free.
  Onboard a sending-only subdomain such as `mail.gdglobal.kr` in Resend,
  confirm DKIM/SPF and sending eligibility, and create a restricted API key
  for Worker secret `RESEND_API_KEY`. Do not change the existing Zoho root
  domain MX or replace unrelated production SPF/DKIM records.
- `wrangler.toml.example` — Cloudflare Email Service `EMAIL` binding.
  Sending to arbitrary unverified recipients may require a Workers Paid plan.
  The sending domain must be onboarded separately. Neither option is activated
  by this repository commit.

The private Worker also locks the sender per transport: Resend uses only
`noreply@mail.gdglobal.kr`; Cloudflare Email Sending uses only
`noreply@gdglobal.kr`. A mismatched sender/provider configuration **fails closed**
with no OTP or applicant receipt. These addresses are policy choices, not
claims that either provider is authorized or live.

Both templates deliberately use `workers_dev = false` and
`VERIFIER_ENABLED = "false"`. Email verification requires separate private
`OTP_DB` (migrations `0001_email_verification.sql` **and**
`0002_resend_daily_quota.sql`) and secrets
`VERIFIER_CALL_SECRET` and `OTP_HMAC_SECRET`. The call secret must equal
the one configured on the intake Worker; the OTP HMAC secret must differ from
the intake HMAC key. Never put either value in Git or a public page.

## Read-only DNS preflight — current state: HOLD

From repository root:

```shell
python scripts/check_beta_mail_dns.py
python scripts/check_beta_mail_dns.py --json
python scripts/test_beta_mail_dns.py
```

The audit uses **public Google DNS-over-HTTPS only**, never a Cloudflare
account token. It checks the three original Zoho MX servers, the root Zoho
SPF and DMARC, plus the **actual Resend 2026-10-14 dashboard** records for
`mail.gdglobal.kr`:

| Type | Cloudflare zone name | Contents |
|---|---|---|
| TXT | `resend._domainkey.mail` | Full DKIM `p=...` copied from Resend |
| CNAME | `rsend.mail` | Resend screenshot: `rsend-apne1.forge.rmta.net`; **DNS only** |
| CNAME | `send.mail` | Full displayed Resend target (do not infer from `rsend`); **DNS only** |

The `rsend.mail` target is now visible in the owner's Cloudflare entry
screenshot; the `send.mail` target and the complete DKIM value are still not
independently visible for exact comparison. **Do not guess either value**. This new sending configuration
uses two CNAMEs, **not** the older `send.mail` MX + TXT model.
`Enable Sending` is ON and `Enable Receiving` is OFF; never add the
receiving MX records unnecessarily.

The checker performs a **public DNS shape check only** (both CNAME targets
end in `.rmta.net` or `.mta.net`; DKIM key present), not an exact target-value comparison.
It never adds or removes records, reads private keys or sends mail. Missing
prerequisites cause exit **2** and HOLD; DNS errors cause exit 1.
If Resend configures a custom Return-Path name instead of `send`, pass
`--return-path <approved-label>`.

The live public DNS audit on 2026-10-14 found the original Zoho MX/SPF and
DMARC present, but Resend records not yet configured: **HOLD**.
Do **not** change `gdglobal.kr` root Zoho MX or append a second root SPF.
Public DNS presence alone is not verification: compare **all three exact**
record values with the operator's Resend dashboard, require Resend's
`verified` sending status, and separately require a synthetic recipient's
actual inbox receipt and account/API binding approval. The release gate
never auto-opens. Resend requests use a HMAC-based `Idempotency-Key`
to avoid duplicate delivery; never log the key.

Provider references:
- https://resend.com/docs/dashboard/domains/introduction
- https://resend.com/docs/api-reference/emails/send-email
- https://developers.cloudflare.com/email-service/api/send-emails/workers-api/

## Approved deployment checklist (not performed)

1. Have the operator approve processor, data locality, data retention,
   consent wording, logging, backups, email cost and abuse policies.
2. Complete provider domain verification and approved synthetic-recipient
   deliverability checks. Use **no real applicants** during QA.
3. Create the *private* D1 database and run the verifier migration; separately
   migrate the intake D1 table. Verify D1 binding IDs without disclosing them.
4. Set secrets from private, authorized management (never CLI arguments,
   repository files or captured logs).
5. Run `node --test email-verifier/test/worker.test.mjs` and
   `python scripts/check_beta_email_verifier.py` from repository root, plus
   existing intake tests and full Playwright.
6. With private binding and outbound email verified, authorize
   `VERIFIER_ENABLED=true` and `INTAKE_ENABLED=true` **separately**.
   Configure public intake endpoint and Turnstile site key only after approval.
7. Recheck all beta product/official-source release gates, six HTTPS links,
   nine deployed files and obtain distinct owner authorization for beta OPEN.

Resend Free-tier delivery additionally has a shared **90 email requests per UTC day**
quota (maximum 2,790 in any 31-day calendar month), enforced by atomic D1
SQL before contacting Resend. The daily quota includes provider failures and
uncertain attempts, so retries never bypass the cap. A missing quota table
causes a fail-closed error, not unmetered sending. The global counters contain
no identifiers and are purged after seven days by the private cron. This
assumes the Resend Free account is dedicated to KEP; other apps sending from
the same Resend account count toward the provider's shared 100/day limit and
must be accounted for separately. The owner must authorize both D1 migrations
and verify the daily cap before any test sending or deployment.

The OTP expires after 10 minutes; there are five total guesses per challenge,
a 60-second resend gap, at most three requests per email per hour, and exactly
one valid redemption. D1 stores keyed hashes, never raw email/OTP. Records are
purged by daily cron once more than 24 hours old. Provider acceptance is not
proof of inbox delivery; release checks must include actual synthetic mailbox
receipt.

`application.directIntake.endpoint` and `turnstileSiteKey` remain empty,
and beta access remains HOLD. GitHub test evidence alone does not change that.
