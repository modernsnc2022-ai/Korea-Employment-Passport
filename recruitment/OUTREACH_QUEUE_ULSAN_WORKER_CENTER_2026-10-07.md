# KEP worker-panel outreach — Ulsan Foreign Residents Support Center

Snapshot: 2026-10-07 KST

- Source code: `ulsan_foreign_resident_center`
- Channel: email
- Public mailbox: `ulsanscfw@naver.com`
- Gmail state: sent once
- Attribution link: `https://modernsnc2022-ai.github.io/Korea-Employment-Passport/?src=ulsan_foreign_resident_center`
- Status: sent_2026-10-07

## Fit
- Ulsan City links the Foreign Residents Support Center as an official resident-support service.
- The center's public website exposes `ulsanscfw@naver.com` as its contact mailbox.
- Ulsan official materials identify Indonesian among the center's multilingual counseling languages.
- The request is voluntary link sharing to relevant Indonesian E-9 workers; KEP does not request worker lists or private contact data.

## Duplicate-mailbox precheck
- Gmail search on 2026-10-07 KST found no prior sent message to `ulsanscfw@naver.com` before the draft was created.

## Pre-send gate
1. Controlled source code is present in the catalog.
2. Source routes to `beta.html?...#worker-panel`.
3. static-check, ui-smoke, Pages and beta-launch-gate pass on the same main HEAD.
4. Deployed Pages contains `ulsan_foreign_resident_center`.
5. Run `python scripts/check_outreach_send_guard.py --source ulsan_foreign_resident_center --mode initial`.
6. Recheck Gmail for any prior sent message to the public mailbox.
7. Send the initial email once only, then seal the ledger.
8. Record a bounce if one appears; never retry without a newly verified public mailbox.

## Boundaries
- Worker interest intake is open; worker-panel access remains separately held/manual.
- KEP is independent, not a government service or placement agency.
- Never promise employment, employer selection, SLC, visa or departure.
- Never store applicant/worker PII in GitHub.

## Send result
- Initial email sent once on 2026-10-07 KST after same-HEAD static/UI/Pages/beta-launch gates passed.
- Pages deployment artifact for the same HEAD contained the Ulsan worker source, worker-panel route and worker form.
- Pre-send guard-equivalent fail-closed check returned `initial_send_allowed` against the same main HEAD; local runner was unavailable, so the checked-in guard contract and same-HEAD ledger/catalog were evaluated directly.
- Final Gmail `in:sent` duplicate check before send: 0 prior messages.
- Immediate bounce check: none observed.
- Do not send another initial outreach. Any later contact requires an explicit follow-up-ready ledger state.
