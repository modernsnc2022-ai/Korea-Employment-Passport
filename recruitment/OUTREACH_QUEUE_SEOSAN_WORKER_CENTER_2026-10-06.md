# KEP worker-panel outreach — Seosan Foreign Worker Support Center

Snapshot: 2026-10-06

## Target
- Source code: `seosan_foreign_worker_center`
- Channel: email
- Public organization mailbox: `seosan@korcham.net`
- Attribution link: `https://modernsnc2022-ai.github.io/Korea-Employment-Passport/?src=seosan_foreign_worker_center`
- Status: sent_2026-10-06

## Fit evidence
- Seosan City states that the Seosan Foreign Worker Support Center serves foreign workers and has counselors for Chinese, Indonesian, Nepali and Mongolian workers.
- The center is entrusted to and operated by the Seosan Chamber of Commerce and Industry.
- The Seosan Chamber publicly lists `seosan@korcham.net` as its organization inquiry mailbox.
- A September 2026 chamber notice confirms the center is still operating and handles foreign-worker counseling, education and events.

## Outreach intent
Ask the operating organization to forward or share the KEP E-9 worker-validator interest link with Indonesian E-9 workers who voluntarily want to compare KEP guidance against their real G-to-G/EPS experience.

Do not ask the organization to disclose names, phone numbers, residence addresses, ARC/passport/KTP numbers, identity-document images, or any worker list.

## Send evidence
1. Same HEAD passed static-check, ui-smoke, Pages deployment and beta-launch-gate.
2. Actual Pages contained the source code and worker-panel route before send.
3. The pre-send guard returned `initial_send_allowed`.
4. Gmail SENT contained no earlier message to the organization mailbox before send.
5. The initial email was sent once on 2026-10-06.
6. Immediate bounce check found none. Do not send another initial outreach.

## Boundaries
- Worker interest intake is OPEN; worker-panel access remains HOLD/manual.
- KEP is independent and is not a government body or placement agency.
- Do not promise employment, employer selection, SLC, visa, or departure.
- Do not store applicant/worker PII in GitHub.
