# KEP account deployment (existing Google Cloud account; no Supabase)

The public app is served at https://kepassport.gdglobal.kr/. All four menus are free. Official guidance is open to guests. Personal tools and cloud progress use a verified KEP account.

## Backend in Google Cloud
1. Select a **separate KEP Google Cloud project under the existing Google account/billing**. Do not put KEP's user data in `simple-printer-pro` (currently selected on the Windows gcloud local configuration). Alternatively choose an existing project dedicated to KEP if one already exists.
2. Enable Firebase on that Google Cloud project in the Firebase console. Accept applicable terms. Firebase Auth belongs to Google Cloud, it is not another independent account provider.
3. Register a WEB app, enable Authentication **Email/Password**, email verification and reset email. Add the exact preview domain `www.gdglobal.kr` and final production host to Auth authorized domains, and configure approved email action redirect paths. Configure email template, abuse controls and rate limits.
4. Create Cloud Firestore in an appropriate approved region and publish `deployment/gcp/firestore.rules` (deny all other collections). Validate rules in the Emulator Suite: unauthorized, another uid, unverified email and unrestricted fields all denied; verified own record get/set/delete allowed. The rules are not live until deployed.
5. Copy the web app's **public** Firebase `apiKey`, `authDomain`, `projectId` and `appId` into `docs/account-config.js` for preview ONLY after Auth, Firestore rules and email verification are tested. The Firebase browser key is public but should be restricted by API and use-appropriate protections. NEVER store service account JSON/private key in repository.
6. Verify real email signup/verification, wrong-password behavior, reset link, cloud save/restore on second device, logout, deletion and fresh-login requirement. Account deletion requires password reauthentication; if deletion fails after progress removal, the client attempts to restore the prior progress document. Validate privacy/consent and final production rollout separately.

## Data minimization
The account sync uses `window.KEPAccountProgress.backup()` only: stage IDs, document checkbox IDs, notice selections and wizard step/index. It never uploads contract contents, payroll, identity numbers, photos, or free-form documents. Restore always asks before overwriting local progress. Individual progress is readable only by a verified owner UID under Firestore rules.

Production web configuration selects `korea-employment-passport`. The Playwright fixture serves an empty configuration for public UI tests and the account tests use an isolated mock SDK. Run `npm run test:firestore` for local rules verification. Real email delivery, deployed rules and second-device restoration require a separate check with dedicated test accounts. Official-source release decisions are tracked separately.
