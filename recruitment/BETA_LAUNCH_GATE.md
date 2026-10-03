# Beta launch gate — Indonesia E-9 Manufacturing

Public beta recruitment must remain **HOLD** until every required item below is PASS.

## 1. Core product flow
- [ ] All 27 supported-route stages are navigable in order.
- [ ] A user can set their current stage and continue from there.
- [ ] Each stage clearly distinguishes official fact, app guidance, and unresolved official detail.
- [ ] No unsupported guess is shown as an exact instruction.

## 2. Zero-broker coverage
- [ ] No unresolved HIGH broker-replacement blocker exists for the supported route.
- [ ] Known broker-like micro questions have an exact answer, official help route, or explicit HOLD.
- [ ] The five Manufacturing 2026 job-application questions remain blocked from guessed answers until official evidence is sufficient.
- [ ] Broker Replacement Rate measurement can be captured from beta feedback.

## 3. Forms and document guidance
- [ ] All current form wizards and validators pass automated checks.
- [ ] Required/optional document distinctions are visible.
- [ ] Users are warned not to submit when an official requirement is not confirmed.

## 4. Official-source freshness
- [ ] Official-source monitor is green at launch review.
- [ ] No unresolved source failure affects a current user action.
- [ ] Manufacturing 2026 notices are checked again immediately before launch.

## 5. Beta UX and privacy
- [ ] Beta ID accepts only KEP-0001 through KEP-0050.
- [ ] Beta evidence is isolated by tester ID.
- [ ] Sanitized feedback can be copied/shared without identity fields.
- [ ] Public beta copy clearly states: first 30 eligible active applicants, free for 6 months from beta activation, feedback participation required.
- [ ] Public beta copy clearly states there is no job, visa, SLC, or departure guarantee.
- [ ] No passport/KTP/ARC number or other sensitive identifier is required to receive the beta benefit.

## 6. Workplace Reality Check
- [ ] Public workplace-information view is usable without worker testimonials.
- [ ] Missing or unverified workplace claims are labeled as such.
- [ ] Worker reviews/photos/videos, when added, have a verification and privacy rule.

## 7. Release quality
- [ ] Static checks PASS on release HEAD.
- [ ] UI smoke tests PASS on release HEAD.
- [ ] GitHub Pages deployment PASS on release HEAD.
- [ ] Mobile-width smoke review PASS.
- [ ] No known critical or high-severity product defect remains open.

## Beta OPEN vs route PASS

The **30 active applicants + 20 E-9 workers are not prerequisites for opening the beta**. They are the evidence cohort collected after opening and are required before declaring the supported route a Broker Replacement Rate 100% PASS.

Beta OPEN requires sections 1–7 to pass plus a final same-day check for any new Manufacturing 2026 official notice. Route PASS remains governed by `docs/MVP_VALIDATION.md`.

## 8. Recruitment switch
When sections 1–7 all PASS:
1. change recruitment status from HOLD to OPEN;
2. open the first-30 active-applicant beta;
3. assign KEP-0001 through KEP-0030 to eligible applicants in application-received timestamp order after recruitment becomes OPEN;
4. activation timing must not change queue order; grant each accepted beta account 6 months free from its actual activation date;
5. continue recruiting KEP-0031 through KEP-0050 separately as the E-9 worker retrospective validation panel.

## Launch principle
The beta should start only when the product is complete enough that testers are primarily finding **real-world process gaps**, not obvious unfinished-product defects.
