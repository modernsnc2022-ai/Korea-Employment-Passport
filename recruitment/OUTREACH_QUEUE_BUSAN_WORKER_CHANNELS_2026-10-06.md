# KEP worker-panel outreach — Busan official support channels

Snapshot: 2026-10-06

## 1. Busan Global City Foundation — Indonesian counseling desk
- Source code: `busan_global_indonesian_desk`
- Channel: email
- Public mailbox: `putri@bgcf.or.kr`
- Attribution link: `https://modernsnc2022-ai.github.io/Korea-Employment-Passport/?src=busan_global_indonesian_desk`
- Status: ready_not_sent
- Fit: the foundation officially operates foreign-resident counseling in Indonesian, including employment/wage/immigration and daily-life topics.
- Ask: voluntarily share the worker-panel interest link with relevant Indonesian E-9 workers or direct KEP to an appropriate worker-community channel.
- Privacy: never request names, phone numbers, ARC/passport/KTP numbers, home/dormitory addresses, or identity-document images.

## 2. Busan Foreign Residents Center
- Source code: `busan_foreign_resident_center`
- Channel: email
- Public mailbox: `somi3438@gmail.com`
- Attribution link: `https://modernsnc2022-ai.github.io/Korea-Employment-Passport/?src=busan_foreign_resident_center`
- Status: ready_not_sent
- Fit: the center provides migrant labor counseling, outreach/mobile counseling, interpretation, education and community-network programs; its public materials include Indonesian-language support.
- Ask: voluntarily share the worker-panel interest link with relevant Indonesian E-9 workers.
- Privacy: do not ask the center to disclose worker identity/contact data.

## Pre-send gate
1. Source code must be in the controlled catalog.
2. Landing must route the source to `beta.html?...#worker-panel`.
3. static-check, ui-smoke, Pages and beta-launch-gate must pass on the same main HEAD.
4. Run `python scripts/check_outreach_send_guard.py --source <sourceCode> --mode initial`.
5. Send each initial email only once, then immediately seal the ledger.
6. Record any bounce and do not retry without a newly verified public mailbox.

## Boundaries
- Worker interest intake is open; worker-panel access remains separately held/manual.
- KEP is independent and must not imply government affiliation.
- Never promise employment, employer selection, SLC, visa or departure.
- Never store applicant/worker PII in GitHub.
