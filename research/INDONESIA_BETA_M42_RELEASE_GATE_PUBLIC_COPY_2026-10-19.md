# KEP M42 — Indonesia beta public release-gate copy correction (2026-10-19)

Scope: Indonesia → E-9 → General Manufacturing → 2026. Code baseline before M42: `506eb92bc99efeb45ef27e7dd9565ce231cb0e14` (M41). Existing Draft PR #324 only. No merge, deployment, or beta activation.

## Actual defect corrected

The applicant-facing `docs/beta.html` release information contradicted the M33+ fail-closed launch policy. It previously said that the unverified *exact 2026 Manufacturing final online job-application document checklist* was **not** a precondition for beta access. This was unsafe and inconsistent with the independently mandatory `exact_2026_manufacturing_final_job_documents` gate.

Replaced the contradictory paragraphs and three-item release list with Indonesian applicant copy that explicitly requires:
1. Original 2026 **General Manufacturing E-9 post-Skill-Test final online application** announcement and annex evidence (not Fisheries, Root Industry, other years, or optional Skill Test materials).
2. Named accountable human semantic review and release-day source review, not automated SHA acceptance.
3. Same-code-version UI/security/HTTPS/public asset verification and separately authorized candidate deployment.
4. Independent, manual operator OPEN decision.

Interest registration is still OPEN. Direct intake remains separately gated. Actual beta service access stays HOLD. Nothing marks `job_docs` accepted; no one is claimed to have signed.

## Verification on the local Windows development machine

- Clean pre-change git HEAD matched Draft PR #324: `506eb92bc99efeb45ef27e7dd9565ce231cb0e14`.
- New `tests/m42-beta-release-copy.spec.js`: **2/2 Chromium PASS**, exit 0 (check exact final-doc prerequisite, excluded other cohorts, human release approvals, interest OPEN/access HOLD, direct intake hidden).
- `python scripts/check_webapp_contract.py`: **PASS**, 27 stages, 308 exact answers; exit 0.
- Full `npx playwright test --reporter=line` on isolated local port 42892: **83/98 passed; 15 failed**, exit 1, ~4.9 min. Raw local test log: `D:\KEP-M42-FULL-CHROMIUM-20261019.log` (not a pass certificate).
- Failure grouping: four `tests/indonesia-extra-audit.spec.js` and eleven `tests/ui.spec.js`. Representative mismatch: historical tests expect *8* changed official sources and PWA cache `kep-v137`, while current public app text reports *12* still pending human review and cache declares `kep-v140`. Other UI assertion failures need individual root-cause assessment; cannot classify all as harmless without verification.
- Do **not** declare the 98-test suite PASS; investigate or repair test/data compatibility and rerun before release.

## Targeted official source observation (not exhaustive)

Targeted public KP2MI search on 2026-10-19 confirmed 2026-09-10 **first-stage** EPS-TOPIK Manufacturing results, not the final online job-document announcement: https://kp2mi.go.id/gtog-detail/korea/pengumuman-hasil-ujian-kemampuan-bahasa-korea-eps-topik-ubt-umum-sektor-manufaktur-tahun-2026

2026 online application guidance located for Fisheries: https://kp2mi.go.id/gtog-detail/korea/pengumuman-pembagian-sertifikat-kelulusan-digital-e-sertifikat-ujian-eps-topik-ubt-umum-sektor-perikanan-dan-pengajuan-lamaran-online-calon-pekerja-migran-indonesia-g-to-g-korea-tahun-2026

2025 Manufacturing final-stage material was also located, and is excluded due to cohort year. No exact 2026 General Manufacturing *post-Skill-Test* final online job-document official announcement/annex was independently verified in this targeted search. This search is not proof of absence from all notices and attached PDFs.

## Release decisions

M41 retained baseline: 11 gates = **6 PASS / 5 PENDING** (verified 2026-10-19 M41 observation). M42 improves applicant wording only; it does **not** change launch-gate determinations, source SHA baselines, manual approvals, official document status, or deployment. The 15 full-suite failures are an independent technical QA follow-up blocker.

**Current:** 20 human review tasks PENDING; exact final Manufacturing online job docs HOLD; Draft unmerged, not deployed; public beta HOLD. No government endorsement claimed.

## Next work

1. Triage 15 browser assertion failures against current UI, source-review policy and dynamic PWA cache; fix genuine product defects without weakening safety assertions. Rerun identical-head full suite to 100%.
2. Exact 2026 General Manufacturing original final online application evidence and reviewer signoff when available.
3. Authorized same-HEAD deployment 9/9 + HTTPS 6/6, then separate manual beta OPEN.
