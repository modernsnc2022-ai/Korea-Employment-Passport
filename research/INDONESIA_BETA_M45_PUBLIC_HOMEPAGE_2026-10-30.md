# KEP M45 — Public Indonesian homepage cleanup (2026-10-30)

Scope: Indonesia > E-9 > General Manufacturing 2026. Owner requested an applicant-friendly public entry before replying to EPSTOPIK.id.

## User-facing changes
- Entire source-watch technical review banner removed from the applicant-facing UI, including historic Nepal fetch failure, SHA drift counts, operator signoff status; review evidence remains in machine-readable status and internal operator records.
- No automatic expansion of the optional detail/backup panel. Operational safety is **not relaxed**: document/exact-answer source guards continue to check review state; malformed latest technical observation and missing source-review JSON fail closed.
- Closed 2026 Manufacturing new-registration status now appears exactly once, with guidance separated for already-registered applicants and future applicants, retaining official KP2MI link.
- Route header now shows actionable context rather than stale pack number / historic source-review date.
- Coverage statistics explicitly distinguish all unresolved small questions from the subset of broker-replacement blockers; avoids e.g. 157/163, 5 unresolved misreading.
- Existing safe official submission HOLD, empty Manufacturing exact post-Skill-Test job-docs, and public beta HOLD unchanged.

## Real executed tests
- Updated older browser contract tests which incorrectly required public exposure of internal source diagnostics.
- Added four new M45 Chromium browser cases: clean first impression, held final job documents, unavailable review-feed fail closed, 320px mobile no horizontal overflow.
- Target M44+M45 Chromium 7/7 PASS (port 42913), local log D:\KEP-M45-USER-HOMEPAGE-TARGET2-20261030.log.
- Full Chromium 105/105 PASS, exit 0, 5.2 min (port 42914), local log D:\KEP-M45-USER-HOMEPAGE-FULL-20261030.log.
- Webapp 27 stages / 308 exact answers PASS; 16 country packs PASS; release preflight and beta-release guards self-test PASS; git diff --check PASS.
- PWA cache bumped to kep-v143.

## Policy / release
No unverified 2026 exact Manufacturing job-application checklist added or released. Manual official-source reviews remain pending. Public beta access remains HOLD. This change authorizes a guarded public **DEMO presentation**, not beta OPEN, SLC, job, visa, or departure guarantee. The existing Draft PR stays unmerged; production demo requires separate docs-only main commit and independent live parity verification.
