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
- Assignment initializes `interview_status=new`, a blank `experience_year`, and `workplace_evidence_status=pending`.
- After the interview, use `scripts/record_worker_interview.py` without `--write` first. It accepts only categorical/non-identifying values: experience year, route stage, broker-used yes/no/unknown, workplace-info-needed yes/no/unknown, gap status, retest status, and workplace-evidence decision.
- Add `--write` only after checking the dry-run line. This helper—not the WPE publisher—sets `interview_status=completed`.
- Choose `workplace_evidence_status=declined` when the worker does not consent to public workplace evidence, or `not_publishable` when the interview cannot safely produce a public WPE record. Only `pending` can later be published.
- Worker validators do **not** receive the public-beta application queue or six-month entitlement fields.
- Contact details and narrative/raw interview notes remain outside this public repository.

- In the app, retrospective validators must record the year of the EPS process/departure they actually experienced (or “do not remember exactly”) before saving stage-validation evidence. This year is context for evidence quality, not identity data.
- Never treat a pre-2026 worker recollection as proof that a 2026 notice-specific rule is correct. Official 2026 facts still come from official sources.


## Publishing verified workplace evidence

Worker interviews and contact details stay outside this public repository. Do not save a completed intake file under the repository tree.

1. Copy `recruitment/WORKER_EVIDENCE_INTAKE_TEMPLATE.json` to a private/local path.
2. Fill only de-identified workplace facts. Do not include worker name, email, phone, passport/KTP/ARC, exact dorm/home address, raw interview text, or private contact details.
3. Set `reviewConfirmed=true` only after a human privacy/fact review.
4. For photos/videos, require `consent=true`, `privacyReviewed=true`, and `metadataRemoved=true`.
5. Run `python scripts/publish_worker_evidence.py --intake <private-file.json>` first. This is dry-run only.
6. Check the proposed WPE-#### record. The helper verifies that the KEP ID is an assigned KEP-0031..0050 worker-validator slot, removes the tester ID from the public record, and only permits `single_verified_worker` for this single-interview publishing path. Do not label one interview as multi-worker or worker-plus-public verification.
7. The tracker interview must already be `completed`, its `experience_year` must match the intake, and `workplace_evidence_status` must still be `pending`. A `declined` or `not_publishable` interview cannot be published.
8. Re-run with `--write` only after the dry-run output is approved. The helper appends the sanitized record to `docs/data/workplace_worker_evidence_v1.json` and changes only `workplace_evidence_status` to `published_single_verified_worker`; it does **not** complete the interview.
9. Commit only the sanitized registry/tracker changes. Never commit the completed private intake file.

The static CI separately checks the registry for forbidden identity/private fields and rejects worker media unless metadata removal is explicitly confirmed.

## Retrospective worker evidence and cycle scope

KEP-0031..KEP-0050 validators must record the year of the EPS process/departure they actually experienced before saving stage validation.

- A validator whose experience year matches the current route cycle (2026) can contribute a current-cycle device checkpoint.
- A validator whose experience is from an earlier year, or whose year is unknown, is **retrospective evidence only**. Their feedback is valuable for finding broker gaps, confusing steps, and real-world differences, but it must not be counted as PASS evidence for the 2026 route.
- Never copy a past-cycle rule into 2026 merely because a retrospective worker remembers that rule.
- Final product/route PASS still requires cohort-level evidence and official-current-source verification; a single device checkpoint is never the final product PASS.


### Tracker fields for worker evidence

For KEP-0031..KEP-0050, keep these states separate:

- `experience_year`: the EPS process/departure year actually experienced, or `unknown`.
- `interview_status`: interview workflow only.
- `workplace_evidence_status`: whether a privacy-reviewed workplace record has actually been published.

Publishing a WPE record sets `workplace_evidence_status=published_single_verified_worker`; it must not be inferred merely from `interview_status=completed`. The public WPE record also carries `experienceYear` so older experience is visibly retrospective.

The public CSV is deliberately categorical. Keep `notes` empty. If `broker_tasks`, `documents_confusing`, or `official_process_gap` are used, store only semicolon-separated 27-stage IDs; never store a broker/person name or narrative interview text in those cells.


### Public-summary consent

Completing a retrospective interview does not by itself authorize public company-level publication. Before `publish_worker_evidence.py` can prepare a WPE record, the private intake must record `contributorConsent=true` for the de-identified public summary. Keep the consent record outside the public registry. Media still requires its own explicit consent, privacy review, and metadata removal.


## Public beta feedback ingestion

Do not edit narrative beta feedback directly into `BETA_TESTER_TRACKER.csv`.

A KEP ID is pseudonymous routing metadata, not authentication. Before writing feedback to the public tracker, confirm that it came from the same private enrollment email/thread or another private contact channel explicitly linked to that participant outside this repository.

1. Read the participant's combined feedback privately.
2. Confirm the `KEP-####` ID and the exact `ID tahap sekarang` from the bundle.
3. Map only actionable findings to the locked 27 route stage IDs.
4. Dry-run `python scripts/record_beta_feedback.py ...`.
5. Review the categorical/stage-only output.
6. Re-run with `--write` only after the mapping is correct.

The recorder never accepts free-text notes. Narrative email content remains outside the public repository. Use `feedback_status=active` while feedback is ongoing and `complete` only when the participant's planned beta feedback cycle is complete.


## Public beta release transition

The public beta must stay HOLD until there is an explicit manual OPEN decision. Do not hand-edit only `status`.

1. Confirm same-HEAD `static-check`, `ui-smoke`, Pages deployment, and `beta-launch-gate` are green.
2. Re-check the official Manufacturing 2026 notice on the same day.
3. Dry-run `python scripts/set_beta_release.py --approved-at YYYY-MM-DD --confirm-open`.
4. Review that the source state is still clean and the proposed transition is HOLD → OPEN.
5. Only after explicit release approval, re-run with `--write` and commit both the program state and outreach status together.

OPEN is valid only when `releaseDecision.publicBeta=approved_manual` and `approvedAt` is present. This prevents future CI from treating a legitimately opened beta as an invalid prelaunch state.


## Stage-level zero-broker evidence

The public tracker preserves route evidence only as stage IDs:

- `zero_broker_pass_stages`: stages the participant actually completed without private help.
- `zero_broker_fail_stages`: stages where private help was still required.

The same stage must never appear in both columns for one participant. Use the exact stage IDs included in the app's combined feedback bundle; do not infer IDs from translated titles.

For KEP-0001..KEP-0030, verified feedback from the active 2026 route can contribute current-cycle evidence. For KEP-0031..KEP-0050, stage evidence is preserved for every validated experience year, but only completed worker interviews whose `experience_year` equals the route cycle can contribute current-cycle route PASS coverage. Prior-year/unknown worker evidence remains retrospective gap evidence.

Route evidence review is not ready until all 27 stages have current-cycle PASS coverage, no current-cycle FAIL stage remains, all Broker Gaps are resolved or official/licensed-only, and the other cohort/late-stage gates are satisfied.


### Follow-up stage evidence after initial intake

A participant may continue using the app after the initial public-beta feedback or worker interview. Do not reopen or overwrite the interview workflow just to capture later stage results.

After verifying the same private participant channel, use:

`python scripts/record_zero_broker_evidence.py --tester-id KEP-#### --pass-stage <stage> ... --fail-stage <stage> ...`

Run without `--write` first. The supplied PASS/FAIL lists are treated as the latest complete stage-evidence snapshot for that participant. For E-9 worker validators, the worker interview must already be completed and `experience_year` must already be recorded. The helper changes only the two zero-broker stage-list fields and keeps narrative notes empty.


## Broker-gap assessment state

`broker_gap_status` describes assessment state, not a default accusation that a broker gap exists:

- `pending` — participant has not yet been fully assessed.
- `none_reported` — assessed; no private-broker dependency was reported.
- `open` — a real private-broker dependency remains unresolved.
- `resolved` — a previously reported broker gap has been replaced/resolved.
- `official_or_licensed_only` — the remaining helper/service is an unavoidable official or legally licensed role, not a replaceable private broker.

New beta/worker assignments start at `pending`. Route PASS review remains blocked while any evidence participant is still `pending` or any real gap remains `open`. Public applicants must also complete their planned beta feedback cycle before route evidence can become ready.
