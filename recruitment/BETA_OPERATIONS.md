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
