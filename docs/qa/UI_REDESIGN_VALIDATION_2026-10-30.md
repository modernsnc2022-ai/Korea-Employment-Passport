# KEP UI redesign validation — 2026-10-30

## Baseline comparison

- Main: `dc40ecbdaf29c33edeaf5165f4f26f84fcd062fa`.
- PR #326: `2bfb5aff51e593c9bc3f6b4aa4d7182219542bb0`.
- Cloud Linux, Node 24.22.1, Playwright 1.55.0, Chromium 140.0.7339.16, one worker, no retries, blocked service workers.
- Each checkout ran its own Python HTTP server and unchanged `tests/ui.spec.js`. Main used port 4174; PR used 4173. No GitHub Actions or user-device execution.
- Both: **46 passed / 10 failed / 0 skipped**. Failure names match exactly; see `ui-baseline-2026-10-30.json`.
- An initial run overlapped browser installation and is excluded (missing executable / ETXTBSY). Installation was completed and browser launch verified before both comparable runs.
- No ECONNREFUSED in either comparable baseline. Previous session's connection refusal cannot be assigned to an app regression. A server launched in a separate cloud command was unreachable from another command; browser and server must run under the same command or Playwright webServer lifecycle.

## Failure classification

1. Seven failures (two form wizard, cohort answer, four document packs): the clean-source fixture retained `latestReadOnlyObservation` from live data while changing its parent state and historical warnings. `latestReadOnlyObservation()` correctly rejects that inconsistent combination. `sourceNeedsReview()` then suppresses all affected guidance. Stage and scope events work; the hidden attribute follows the safety condition, not a CSS regression. Delete the observation **only in the scenario fixture**. Never modify production source data to make a test pass.
2. Departure registry assertion expects the old `/gtog-korea/info` URL; current data uses `/gtog-korea/pengumuman`. Preserve the official current destination and the no-cross-cohort checks.
3. Beta form identity assertion counts the new email OTP as an identity field. Exclude exactly `#applicantEmailCode`; retain all identity exclusions. The direct-intake suite separately exercises the OTP request and confirmation using mocked responses only.
4. Source-review test expects a deliberately retired global operator alert. Assert the warning in affected document context and continued suppression instead.
5. The additional direct-intake suite has an outdated fixture lacking explicit approval, public widget configuration and email verification. Update the mock to exercise the real guarded flow; production approval state stays untouched.

## Server isolation

Playwright now owns server startup/shutdown and refuses an occupied port instead of silently testing a different checkout. `PLAYWRIGHT_PORT` selects an isolated port. Wait for browser installation before starting tests. Commands and logs must stay alive until the suite completes.

## Release status

No merge, production deployment, beta activation or source approval. Local-language review, independent novice/experienced-user task evaluation, physical-device keyboard checks and user design approval remain release requirements.
