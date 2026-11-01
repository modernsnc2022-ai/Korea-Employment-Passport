# KEP account deployment (existing Google Cloud account; no Supabase)

KEP remains on existing Cloudflare/GitHub Pages preview and keeps all 4 menus FREE without login.

## Backend in Google Cloud
1. Select a **separate KEP Google Cloud project under the existing Google account/billing**. Do not put KEP's user data in `simple-printer-pro` (currently selected on the Windows gcloud local configuration). Alternatively choose an existing project dedicated to KEP if one already exists.
2. Enable Firebase on that Google Cloud project in the Firebase console. Accept applicable terms. Firebase Auth belongs to Google Cloud, it is not another independent account provider.
3. Register a WEB app, enable Authentication **Email/Password**, email verification and reset email. Add the exact preview domain `www.gdglobal.kr` and final production host to Auth authorized domains, and configure approved email action redirect paths. Configure email template, abuse controls and rate limits.
4. Create Cloud Firestore in an appropriate approved region and publish `deployment/gcp/firestore.rules` (deny all other collections). Validate rules in the Emulator Suite: unauthorized, another uid, unverified email and unrestricted fields all denied; verified own record get/set/delete allowed. The rules are not live until deployed.
5. Copy the web app's **public** Firebase `apiKey`, `authDomain`, `projectId` and `appId` into `docs/account-config.js` for preview ONLY after Auth, Firestore rules and email verification are tested. The Firebase browser key is public but should be restricted by API and use-appropriate protections. NEVER store service account JSON/private key in repository.
6. Verify real email signup/verification, wrong-password behavior, reset link, cloud save/restore on second device, logout, deletion and fresh-login requirement. Account deletion requires password reauthentication; if deletion fails after progress removal, the client attempts to restore the prior progress document. Validate privacy/consent and final production rollout separately.

## Data minimization
The account sync uses `window.KEPAccountProgress.backup()` only: stage IDs, document checkbox IDs, notice selections and wizard step/index. It never uploads contract contents, payroll, identity numbers, photos, or free-form documents. Restore always asks before overwriting local progress. Individual progress is readable only by a verified owner UID under Firestore rules.

A missing config hides the account entry point entirely. Existing preview currently has **no live account backend**, so account creation and cloud sync are NOT active yet. Government EPS/SiskoP2MI accounts are independent. Public beta remains HOLD.
