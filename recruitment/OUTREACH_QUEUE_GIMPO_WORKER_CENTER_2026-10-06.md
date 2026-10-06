# KEP worker-panel outreach — Gimpo Foreign Residents Support Center

Snapshot: 2026-10-06

- Source code: `gimpo_foreign_resident_center`
- Channel: email
- Public mailbox: `gimpofc@naver.com`
- Attribution link: `https://modernsnc2022-ai.github.io/Korea-Employment-Passport/?src=gimpo_foreign_resident_center`
- Status: sent_2026-10-07

## Fit
- Gimpo officially operates foreign-resident communities that include an Indonesian community.
- The center provides multilingual counseling/interpretation including Indonesian.
- The center operates labor, legal and resident-support counseling and a direct foreign-resident community network.
- The ask is only voluntary link sharing to relevant Indonesian E-9 workers; KEP must not request private worker lists or contact details.

## Pre-send gate
- Duplicate-mailbox check on 2026-10-06: no prior Gmail message to `gimpofc@naver.com` was found before staging.
1. Controlled source code present in the catalog.
2. Source routes to `beta.html?...#worker-panel`.
3. static-check, ui-smoke, Pages and beta-launch-gate pass on the same main HEAD.
4. Run `python scripts/check_outreach_send_guard.py --source gimpo_foreign_resident_center --mode initial`.
5. Send the initial email once only, then seal the ledger.
6. Record a bounce if one appears; never retry without a newly verified public mailbox.

## Boundaries
- Worker interest intake is open; worker-panel access remains separately held/manual.
- KEP is independent, not a government service or placement agency.
- Never promise employment, employer selection, SLC, visa or departure.
- Never store applicant/worker PII in GitHub.

## Send result
- Deployment gate SHA: `14e4976e24803b43d74d5346e6468c80f1e025c3`; static-check, ui-smoke, Pages and beta-launch-gate all passed on this same HEAD before send.
- Initial email sent once on 2026-10-07 KST after same-HEAD gates, deployed routing, duplicate-mailbox recheck, and the pre-send guard passed.
- Immediate bounce check: none observed.
- Do not send another initial outreach. Any later contact requires an explicit follow-up-ready ledger state.
