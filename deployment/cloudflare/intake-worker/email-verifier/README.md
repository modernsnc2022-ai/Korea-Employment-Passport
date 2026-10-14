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

Both templates deliberately use `workers_dev = false` and
`VERIFIER_ENABLED = "false"`. Email verification requires separate private
`OTP_DB` (migration `0001_email_verification.sql`) and secrets
`VERIFIER_CALL_SECRET` and `OTP_HMAC_SECRET`. The call secret must equal
the one configured on the intake Worker; the OTP HMAC secret must differ from
the intake HMAC key. Never put either value in Git or a public page.

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

The OTP expires after 10 minutes; there are five total guesses per challenge,
a 60-second resend gap, at most three requests per email per hour, and exactly
one valid redemption. D1 stores keyed hashes, never raw email/OTP. Records are
purged by daily cron once more than 24 hours old. Provider acceptance is not
proof of inbox delivery; release checks must include actual synthetic mailbox
receipt.

`application.directIntake.endpoint` and `turnstileSiteKey` remain empty,
and beta access remains HOLD. GitHub test evidence alone does not change that.
