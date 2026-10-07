# KEP beta direct-intake Worker

This Worker is an optional private intake backend for the Indonesia active-applicant beta form.

## Safety/operations

- The public site stays on email fallback until `docs/data/beta_program_v1.json -> application.directIntake.endpoint` is set to a verified HTTPS endpoint.
- No GitHub Actions deployment is required.
- Applicant records are stored only in the private `KEP_BETA_APPLICATIONS` KV namespace.
- Stored fields are limited to contact email, EPS stage/cycle, recruitment source, confirmations, submission ID, and timestamp.
- Client IP is not copied into the application record.
- Records expire automatically after 90 days by default.
- Passport/KTP/ARC images, identity numbers, phone, address, health and bank data are not accepted by this endpoint.

## One-time Cloudflare setup

1. Authenticate Wrangler interactively: `npx wrangler login`.
2. Create a KV namespace: `npx wrangler kv namespace create KEP_BETA_APPLICATIONS`.
3. Copy `wrangler.toml.example` to `wrangler.toml` and replace the placeholder KV namespace ID.
4. Deploy from this directory: `npx wrangler deploy`.
5. Verify `GET https://<worker>.workers.dev/health` returns `{"ok":true,...}`.
6. Test a POST from the allowed GitHub Pages origin.
7. Only after the storage and CORS test passes, set `application.directIntake.endpoint` to `https://<worker>.workers.dev/v1/beta/applicant`.
8. Run the KEP static/UI checks outside GitHub Actions, then publish the frontend change.

Do not commit `wrangler.toml` if it contains account-specific resource IDs unless the repository policy explicitly permits it. Never commit Cloudflare tokens or secrets.
