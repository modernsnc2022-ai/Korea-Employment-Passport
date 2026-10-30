# KEP 최신 UI 통합 검증 후속 기록 — 2026-10-30

Branch: `ux/indonesian-ui-copy-20261030`, tested at commit `fee1241af7c98dbefa0184034fe0bf9626d26490`.

## 첫 전체 실행
Windows Desktop Commander temp checkout, Playwright default Edge channel, 104 tests total:
- 91 PASS, 13 FAIL.
- Failure category A: 8 tests from accessibility, public surfaces, installation control could not import `axe-core/axe.min.js`; stale `node_modules` from earlier branch had not been reinstalled. The current `package.json`/lock already declares `axe-core=4.10.3`. This is local setup, not production behavior.
- Failure category B: 5 UI tests were unable to fetch `source_review_status.json` owing to `ECONNREFUSED 127.0.0.1:4173` late in the lengthy run. This is an HTTP test server lifecycle failure; underlying app function still requires full regression confirmation.
- Reporter JSON written from PowerShell output redirection is UTF-16 by default; Python reader using UTF-8 failed. Use `encoding='utf-16'` for that local log, or write report natively to UTF-8 without PowerShell encoding conversion.
- Do NOT claim the first suite passed.

## Targeted reruns after environment repair
- `npm ci --no-audit --no-fund` reinstalled 4 packages. `axe-core` confirmed 4.10.3.
- `PLAYWRIGHT_PORT=4197 npx playwright test tests/accessibility.spec.js tests/public-surfaces.spec.js tests/install-control.spec.js --reporter=line`: **10/10 PASS**. Includes eight formerly missing-module cases.
- `PLAYWRIGHT_PORT=4198 npx playwright test tests/ui.spec.js -g 'unexperienced beta stage|workplace reality check separates|manufacturing job application cannot complete|scout request excludes|review-required official source suppresses' --reporter=line`: **5/5 PASS**.
- These are **separate targeted reruns**, not one full 104/104 execution. A single clean end-to-end 104-test run in an isolated environment remains necessary for release evidence.
- No product code/official source status changed as a result. No merge, production deployment, beta OPEN, or human approval.

## Outstanding release gates
1. Full 104-test continuous suite (or currently enumerated count) with lockfile-installed deps, one server lifecycle, dedicated isolated port, complete UTF-8 artifact.
2. Official source status remains `review_required`; historical monitor 83/84 checked; human change evaluation/approval required.
3. Actual Android/iOS keyboard/scroll/screen reader and Indonesian native-speaker review.
4. Same-commit staging HTTPS/assets check, approval and rollback before production.
