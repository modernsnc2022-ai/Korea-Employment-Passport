# KEP worker-panel outreach — Korean foreign-worker support centers

Snapshot: 2026-10-06

## 1. Hwaseong Immigrants Community Service Center
- Source code: `hwaseong_foreign_welfare`
- Channel: email
- Attribution link: `https://modernsnc2022-ai.github.io/Korea-Employment-Passport/?src=hwaseong_foreign_welfare`
- Status: sent_2026-10-06
- Fit: local foreign-resident support center serving migrant workers in a major industrial area; ask the center to share the worker-panel interest link with relevant Indonesian E-9 workers.
- Public contact evidence: center website/domain and public organization mailbox were rechecked before staging.
- Privacy: do not ask the center to disclose worker names, phone numbers, ARC/passport/KTP numbers, home/dormitory addresses, or identity-document images.

## 2. Yangsan Support Center for Foreign Workers
- Source code: `yangsan_foreign_worker_center`
- Channel: email
- Attribution link: `https://modernsnc2022-ai.github.io/Korea-Employment-Passport/?src=yangsan_foreign_worker_center`
- Status: sent_2026-10-06
- Fit: the center publicly states that it supports E-9/H-2 workers and lists Indonesian among supported counseling languages.
- Privacy: do not ask the center to disclose worker identity/contact data. Request only voluntary link sharing to relevant Indonesian E-9 workers.

## Pre-send gate
Pre-send checks completed before the initial emails were sent:

1. Confirm the source code is present in `docs/data/beta_recruitment_sources_v1.json`.
2. Confirm the source routes to `beta.html?...#worker-panel`.
3. Confirm static-check and UI smoke pass on the same deployment candidate.
4. Run:
   `python scripts/check_outreach_send_guard.py --source <sourceCode> --mode initial`
5. Both initial emails were sent once on 2026-10-06 after the guard returned allowed.
6. Immediate bounce check after send found none. Do not send another initial outreach; any later contact must use an explicit follow-up-ready ledger state.

## Boundaries
- Worker interest intake is open, but worker-panel access remains manual/held until separately approved.
- KEP is independent and must not imply government affiliation.
- Never promise employment, employer selection, SLC, visa, or departure.
- Never store applicant/worker PII in GitHub.
