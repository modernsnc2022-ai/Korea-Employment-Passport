# KEP optional accounts (Supabase Auth)

The 4 core service tabs remain FREE and usable without signup. No beta tester account tier.

## Connect real backend
1. Use a private Supabase project with **email confirmation enabled**, rate limits / CAPTCHA / abuse protection appropriate to public signup, and SMTP delivery configured for real email delivery. Set Auth Site URL and allowed Redirect URLs to the KEP preview URL and any future production KEP path. Use a separate staging project first.
2. Apply `deployment/supabase/001_kep_progress.sql` to the chosen project. Confirm RLS enabled and each user's row is inaccessible from a different account (and from anon).
3. Set `docs/account-config.js` to the project URL and **public publishable key**. This public key is not a secret; NEVER use service_role or secret keys. Publish config only after backend and sign-up abuse protections are ready.
4. Check email confirmation, login, wrong password, logout, password reset and two-device restore. Then approve rollout. No Google Actions required.

## Privacy / sync
- Only existing `makeProgressBackup()` safe fields are synced: stage completion, document checkboxes, scoped notice choices and **wizard progression, not entered field values**, plus quick-start flag.
- Sensitive contract, payroll, personal notes, identity numbers, files, and unverified community posts are never sent to the account database.
- Cloud save / restore require explicit confirmation. Restoring replaces local progress for matching route and may reload the page; save a local JSON backup first. RLS limits each user to their own data.
- Login is optional and separate from official SISKOP2MI / EPS accounts. It does not confirm official application status.
- If config is absent or invalid the account entry point stays hidden; no fake signup or claims of activation.
- Email + password auth is handled by Supabase Auth; KEP never receives/stores raw passwords on its own server.
