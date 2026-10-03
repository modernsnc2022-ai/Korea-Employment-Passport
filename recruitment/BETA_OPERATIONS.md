# Beta operations — public 30-person cohort

This file covers operational handling only. The public beta remains **HOLD** until BETA_LAUNCH_GATE.md passes.

## Slot order

- Do not assign KEP IDs while recruitment status is HOLD.
- Review eligibility first outside the public repository.
- After OPEN, assign KEP-0001 through KEP-0030 in the received-timestamp order of eligible applications.
- Activation timing never changes queue order.
- The 6-month free period starts from that participant's actual beta activation date.
- Do not put email addresses, names, phone numbers, passport/KTP/ARC numbers, exact home addresses, or identity-document images in this repository.

## Assignment helper

Use scripts/assign_beta_slot.py only after the beta program status is OPEN. It accepts an eligible application received timestamp with timezone, activation date, current route stage, and a non-identifying source-channel label.

Run without --write for a dry run. Add --write only after checking the proposed KEP ID and free-until date.

The script selects the next contiguous public KEP slot, computes the six-calendar-month end date, and refuses an application timestamp earlier than the last assigned eligible application.

Direct contact information stays in the access-controlled communication system and is matched to the pseudonymous KEP ID outside this public repository.


## E-9 worker validator panel

The 20-person retrospective panel uses KEP-0031 through KEP-0050 and remains separate from the 30-person public beta.

- Do not assign worker-validator KEP IDs while `retrospectivePanel.status` is HOLD.
- After the worker panel becomes OPEN, assign KEP-0031 through KEP-0050 contiguously in validator enrollment order.
- Use `scripts/assign_worker_validator.py` for dry-run first, then `--write` after checking the proposed KEP ID.
- The helper records only a non-identifying source channel, supported route stage, in-Korea confirmation, E-9 experience confirmation, and panel status fields.
- Worker validators do **not** receive the public-beta application queue or six-month entitlement fields.
- Contact details remain outside this public repository.


## Publishing verified workplace evidence

Worker interviews and contact details stay outside this public repository. Do not save a completed intake file under the repository tree.

1. Copy `recruitment/WORKER_EVIDENCE_INTAKE_TEMPLATE.json` to a private/local path.
2. Fill only de-identified workplace facts. Do not include worker name, email, phone, passport/KTP/ARC, exact dorm/home address, raw interview text, or private contact details.
3. Set `reviewConfirmed=true` only after a human privacy/fact review.
4. For photos/videos, require `consent=true`, `privacyReviewed=true`, and `metadataRemoved=true`.
5. Run `python scripts/publish_worker_evidence.py --intake <private-file.json>` first. This is dry-run only.
6. Check the proposed WPE-#### record. The helper verifies that the KEP ID is an assigned KEP-0031..0050 worker-validator slot and removes the tester ID from the public record.
7. Re-run with `--write` only after the dry-run output is approved. The helper appends the sanitized record to `docs/data/workplace_worker_evidence_v1.json` and marks the tracker interview status `completed`.
8. Commit only the sanitized registry/tracker changes. Never commit the completed private intake file.

The static CI separately checks the registry for forbidden identity/private fields and rejects worker media unless metadata removal is explicitly confirmed.
