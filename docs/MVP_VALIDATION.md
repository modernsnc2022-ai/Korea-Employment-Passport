# MVP validation checklist

Supported route: Indonesia → E-9 → Manufacturing → 2026

## Zero-broker acceptance
- User can identify the correct official route.
- User can identify the next action at every supported stage.
- User can find the official source for every mutable rule.
- User can prepare required documents without a replaceable private intermediary.
- User can distinguish official fees from unexplained payments.
- User understands that roster/EPS pass does not guarantee employer selection.
- User can review SLC without relying on a private broker.
- User can finish visa/OPP/departure preparation through official channels.
- User can continue through Korea arrival, employer handover, Residence Card, EPS insurance, first payroll, labor support, and employment maintenance without a replaceable private broker.
- User can report any remaining private-broker dependency as a Broker Gap.

## Failure rule
Any required replaceable private-broker task = route FAIL.

A structured rule that is still on `answered_hold` because the official route detail is not verified also blocks **final** Broker Replacement Rate 100% PASS. Beta recruitment may still open with an explicit HOLD when the app refuses to guess and routes the user safely.

## Evidence needed before final PASS
- All 30 active Indonesian G-to-G public-beta slots are filled, activated, and their planned beta feedback cycle is complete.
- All 20 Indonesian E-9 worker-validator slots are filled and their privacy-safe interview is complete.
- Every worker validator has an experience year (or explicit `unknown`) recorded.
- Prior-cycle/unknown worker experience is retrospective gap evidence only; it does not prove a 2026 route rule.
- At least one active tester covers each late-stage bucket: roster/employer selection, SLC/post-SLC, visa/OPP/final medical, departure.
- All 27 route stages have at least one **current-cycle** zero-broker PASS observation.
- No current-cycle zero-broker FAIL observation remains for any of the 27 stages.
- Every beta participant's Broker Gap assessment is complete: no `pending` assessment remains.
- Every reported Broker Gap is resolved or documented as official/licensed-only; no `open` private-broker dependency remains.
- No structured `blocksZeroBrokerReady=true` question remains on `answered_hold`.
- Official-source review is current and clean for the rules used to declare PASS.

## Current Manufacturing 2026 official-evidence dependency
One Manufacturing online job-application question remains an explicit exact official-evidence HOLD until a Manufacturing-specific 2026 detailed notice is verified:

- `job_docs`

Four additional questions now have conservative official safety baselines and no longer count as unresolved zero-broker blockers:

- `job_scan`: supporting documents are scanned rather than photographed; this does not define the exact Manufacturing 2026 checklist or file specs.
- `job_name`: preserve registered identity exactly; copy document numbers from the corresponding official document; if address/document-source fields are ambiguous, do not guess—use official help. This is not a Manufacturing 2026 field-by-field map.
- `job_edit`: treat final send as non-editable.
- `job_submit`: upload through Menu Pemenuhan Dokumen, confirm the application/documents are actually sent and monitor progress in Sisko; if status is unclear, use the official sendingkorea@gmail.com channel. The exact Manufacturing 2026 button label is not claimed.

The identity baseline preserves registered identity and routes ambiguous field-source questions to official help; it does not claim a Manufacturing 2026 field-by-field map. These safe baselines do not replace the one remaining exact Manufacturing document checklist HOLD.

They do **not** require the beta itself to stay closed, because the app intentionally refuses to guess. They **do** prevent final Broker Replacement Rate 100% PASS until each is resolved from official evidence or explicitly routed to official Human Help under the reviewed rule set.

## Workplace worker evidence
The 20-worker retrospective validation cohort is required for validation. Public WPE-#### publication is separate and requires contributor consent; a worker declining public company-level publication does not invalidate their privacy-safe validation interview and does not by itself block route PASS.

## Timing of this evidence
The 30+20 evidence is collected **after the beta is opened**. It is required before declaring the supported route a 100% broker-replacement PASS, not before starting recruitment itself.

The privacy-safe aggregate is produced by `scripts/report_beta_progress.py`. That report is a readiness signal, not the final declaration by itself; the sanitized underlying evidence must still be reviewed before declaring PASS.
