# Indonesia beta launch — operator review packet (2026-10-14)

**Not approved. No release is authorized.** This is an actionable checklist for the person responsible for the official-source review and real beta launch. All approval fields remain empty in tracked JSON; no applicant data is included.

## Current objective

Supported scope: **Indonesia → E-9 → General Manufacturing → South Korea**, 2026 rules. Tester-interest intake is `OPEN`; actual beta access is `HOLD`. The explicit `job_docs` exact 2026 post-Skill Test Manufacturing online job-application upload checklist is still **HOLD** and must not be fabricated from the Fisheries cohort, Root Industry, February examination registration, optional September Skill Test competency evidence, or 2025 notices.

## A. Source-scope review that still requires a named person

The independent 2026-10-14 official watcher fetched **83/84**, with **seven changed** and one Nepal fetch HTTP 500. It records **three changed Korea-common sources** that do affect an Indonesian route and **five unrelated-country alerts** that remain visible in their respective research/launch gates.

For the Indonesia scope, the operator must inspect and either accept the current content or explicitly block for each:

| Monitored ID | Official link | What to confirm |
|---|---|---|
| `labor_standards_wage_statement` | [Law.go.kr Labor Standards Act Art. 48](https://law.go.kr/LSW/lsLinkCommonInfo.do?lsJoLnkSeq=1027161979) | Wage statement delivery obligation is still accurately reflected; no outdated field or unsupported legal advice |
| `kdca_qcode_input` | [KDCA Q-CODE legacy entry](https://qcode.kdca.go.kr/qco/cd/codeInput2.do) | Follow official Travel Health redirection, check current subject criteria and avoid claiming Q-CODE is universally mandatory |
| `moel_1350_contact` | [MOEL 1350](https://1350.moel.go.kr/home/hp/ch/callchat.do) | Current phone/hours and permitted consultation expectations; do not claim Indonesian-language support without evidence |

The other-country alerts `np_eps_notice_index` (HTTP 500), `vn_colab_eps_notices`, `lk_slbfe_home`, `kg_migrant_home`, and `mm_mol_dol_index` **must remain pending** and cannot be silently relabeled clean. A Nepal-only unavailable source does not justify approving Nepal or copying a rule into Indonesia.

After **genuine same-day human review**, the named operator may fill `recruitment/ID_BETA_SOURCE_SIGNOFF.json` *only* with a real `reviewer`, timezone-aware `approvedAt`, matching `sourceSnapshotDate`/`sourceScopeDate`, the exact three reviewed critical IDs and five still-pending foreign IDs. Preserve the monitored-map fingerprint and all changed-source warnings. Test with `python scripts/check_indonesia_source_signoff.py` and `python scripts/report_indonesia_beta_release_preflight.py --json`. **Never** sign on behalf of the operator or automatically promote official hashes.

## B. KP2MI General Manufacturing release-day review

**Correct listing**: [KP2MI G-to-G Korea Pengumuman](https://kp2mi.go.id/gtog-korea/pengumuman), with official server-side DataTables feed [Pengumuman JSON](https://kp2mi.go.id/gtog-data/korea/Pengumuman). The historical mistaken `/gtog-korea/info` listing is **Preliminary Training dan Info**, **not** the current announcement category.

The same-day October 14 audit queried latest 225 records through November 2025, found 184 titles dated 2026 with seven Manufacturing-related titles, and independently confirmed the 184-title digest `18c377871ba987be7fb5afd05a85cce141f6a0ee62edd417c550c09ae42130a5`. All seven official HTML details returned HTTP 200. Full URL list, individual HTML content digests, title exclusions, and the January 27 `lamaran online` context are recorded in `research/ID_MANUFACTURING_2026_7_NOTICE_DETAIL_AUDIT_20261014.md`.

The [September 17 2026 optional Skill Test competency-document notice](https://kp2mi.go.id/gtog-detail/korea/pengumuman-persyaratan-unggah-dokumen-kompetensi-peserta-skill-test-ubt-umum-sektor-manufaktur-eps-topik-tahun-2026) included **six public PDF annexes (21 pages)**. Their SHA digests, forms and conditional two-surety fallback are in `research/ID_MANUFACTURING_2026_OPTIONAL_COMPETENCY_PDF_ANNEX_AUDIT_20261014.md`. It was **optional** and its upload window closed **2026-09-23 at 13:00 WIB**; the Skill Test itself is mandatory. Some PDF scan examples are image-only and have not been exhaustively visually certified; a screenshot has Fisheries labels, which must not override the applicant's EPS exam-card Manufacturing sector.

The operator must **re-read the current official index and relevant current-cycle bodies/attachments on the actual release date**, decide whether a specific 2026 General Manufacturing final application notice has appeared, and sign only what they truly reviewed. Title-only negative search is not proof that such a notice or appendix does not exist. If a new notice is found, record `notice_found_review_required` and defer promotion until the actual structured rules are updated and verified. Do **not** alter `job_docs` based on inference.

The provided helper `scripts/record_manufacturing_launch_check.py` supports `--self-test` and **dry run by default**; `--write` and `--confirm-full-inventory` represent an **explicit operator action after reading official evidence**. The helper now preserves original-dated independent seven-HTML/six-PDF metadata while resetting the *new day's operator-review flag* to false until the new review is genuinely completed.

## C. HTTPS and deployment gate

Owner approved GitHub Pages **Enforce HTTPS** on both `modernsnc2022-ai.github.io` (shared site) and KEP project Pages on October 14; authenticated API reads confirm `https_enforced=true`, certificates approved and both built. The direct secure company and KEP origins work. However GitHub CDN cached older 301 `Location: http://...` responses for certain `github.io` entrypoints despite the new setting.

`scripts/audit_indonesia_beta_pages_live.py --self-test` now checks **six** historical entrypoints including org root, KEP root, `index.html`, `app.html`, `beta.html`, and `?src=epstopik_indonesia`, rejecting **any** HTTP first hop, unexpected destination/path, or dropped source code. On October 14, live review was **3/6 safe**, while the published direct HTTPS site's nine important assets matched production `main` 9/9 and the unmerged Draft PR 1/9 as expected. A nonzero real audit is **correct** until cache entries clear and reviewed release assets are actually deployed.

A launch must independently show: six legacy entrypaths with no insecure first hop; all nine served critical assets byte-identical to the **same reviewed release commit**, the actual Pages deployment evidence, real device/320px/browser QA and product static tests. Earlier 78/78 Edge PASS on changed app code SHA `9ecab220d959e4ab7f814fa619c42cac8fcc722e` is useful but **not** proof of published Pages parity or a final same-HEAD release workflow. Prefer isolated headless checks over GitHub Actions until budget is reviewed.

## D. Actual OPEN — separate, last action

Only after A-C are genuinely PASS, the operator records the explicit manual beta-access release decision with a real timezone-aware timestamp and the existing controlled `scripts/set_beta_release.py` helper. **No merge, deploy, source signoff, release-state write, tester ID activation, six-month entitlement activation, or message blast is authorized by this packet alone.**

Initial validation target: 30 active Indonesia applicants and 20 retrospective Indonesian E-9 worker validators; the 30-person applicant count is not a hard exclusion cap. Six-month free eligibility begins on *actual beta activation*, with feedback as the condition.

**Current status for this packet:** Source review signoff **PENDING**, KP2MI Manufacturing complete human inventory signoff **PENDING**, older CDN redirect paths **PENDING**, latest Draft-to-production deploy parity **PENDING**, beta access **HOLD**. Capture signed release-day outcomes in the unified Google Sheets and PR #324; preserve prior records and evidence.
