# KEP M24 — 2026 Indonesia General Manufacturing exact job_docs cohort-scoping audit

**Source observation:** 2026-10-17T04:44:51 UTC / 11:44:51 WIB / 13:44:51 KST. **Evidence type:** machine read-only live official KP2MI G-to-G Korea `Pengumuman` DataTables title/link index; cross-matched against previous original HTML and PDF archives. **This document is not operator signoff.**

## A. Current official-listing observations

- Official list: https://kp2mi.go.id/gtog-korea/pengumuman
- Official data endpoint: https://kp2mi.go.id/gtog-data/korea/Pengumuman
- **320 rows inspected**, **2,877** historical records reported by server; read from **16 October 2026** back to **16 July 2025**, crossing prior-year boundary. Title/URL metadata SHA-256: `4d67a65b8af983e6567fbc3b55374e30fa10c095954aafbbc8bb15100471a4e6`.
- **Seven** 2026 UBT Umum General Manufacturing-related notice titles, with **seven official detail URLs exactly matching** M21's seven fetched HTML pages. **Zero titles explicitly advertising the final 2026 General Manufacturing online job-application document list**.
- **Three** 2026 other-cohort online job application notices, excluded from the target path:
  1. **17 Sep — Root Industry welding/casting:** https://kp2mi.go.id/gtog-detail/korea/pengumuman-pembagian-sertifikat-kelulusan-digital-e-sertifikat-ujian-eps-topik-dan-pengajuan-lamaran-online-calon-pekerja-migran-indonesia-program-root-industry-bidang-pengelasan-dan-pencetakan-g-to-g-korea-tahun-2026
  2. **19 Aug — UBT Umum Fisheries:** https://kp2mi.go.id/gtog-detail/korea/pengumuman-pembagian-sertifikat-kelulusan-digital-e-sertifikat-ujian-eps-topik-ubt-umum-sektor-perikanan-dan-pengajuan-lamaran-online-calon-pekerja-migran-indonesia-g-to-g-korea-tahun-2026
  3. **21 Jul — special/re-entry UBT Khusus:** https://kp2mi.go.id/gtog-detail/korea/pengumuman-pembagian-sertifikat-kelulusan-digital-e-sertifikat-ujian-eps-topik-ubt-khusus-dan-ketentuan-pengajuan-lamaran-online-calon-pekerja-migran-indonesia-program-g-to-g-korea-tahun-2026
- Ambiguous generic application titles needing 2026 General Manufacturing attribution: **zero in the checked index**. This is a **title search result only**; it does **not establish** that no notice body/annex or later revision can address final documents.

## B. Mandatory boundaries retained

| Source | Narrow verified stage | Forbidden inference |
|---|---|---|
| [27 Jan General Manufacturing/Fisheries EPS-TOPIK enrollment](https://kp2mi.go.id/gtog-detail/korea/pengumuman-pendaftaran-ubt-umum-sektor-perikanan-dan-sektor-manufaktur-progam-g-to-g-ke-korea-selatan-dengan-sistem-poin-tahun-2026) | **Initial examination registration**, early 2026, including Sisko P2MI ID/image/payment and MCU/HIMPSI process clauses | Not a post-Skill Test exact 2026 General Manufacturing final job-application file list |
| [10 Sep Manufacturing first-stage results](https://kp2mi.go.id/gtog-detail/korea/pengumuman-hasil-ujian-kemampuan-bahasa-korea-eps-topik-ubt-umum-sektor-manufaktur-tahun-2026) | First-stage passers **must** attend Skill Test; optional Job Capacity Assessment supporting evidence | Passing stage one or optional credentials does not equal final placement or the job_docs list |
| [17 Sep optional competency submission](https://kp2mi.go.id/gtog-detail/korea/pengumuman-persyaratan-unggah-dokumen-kompetensi-peserta-skill-test-ubt-umum-sektor-manufaktur-eps-topik-tahun-2026) | Optional evidence upload period September 21–23, 2026 **CLOSED**, with conditional form required if evidence chosen | Not mandatory for every candidate; not 2026 final online job-docs |
| Fisheries / Root Industry / UBT Khusus job application | Different sector/cohort path | Never import their document checklist into 2026 UBT Umum Manufacturing |

## C. New machine checks added in M24

- `scripts/report_m24_kp2mi_live_scope.py`: live official AJAX index capture with observed UTC/Jakarta date, candidate-group partition, exact title metadata fingerprint, typed exclusions; **8 hostile input tests PASS**; persisted date-scoped additive observation at `research/source_reviews/indonesia_m24_manufacturing_title_scope_2026-10-17.json`.
- `scripts/check_m24_manufacturing_job_docs_scope.py`: cross-check today's **7 exact notice URLs** with M21 official HTML; cross-check M23 six original PDF SHAs and one 8 MB timeout; retain 12 unaccepted official source fingerprints and pending human signoff. **13 hostile mutation cases PASS**, **no source hash acceptance**.
- M24 source-date freshness is **only valid for 2026-10-17**. It cannot be reused as evidence for an actual later release day.
- Earlier M23 checked **6 of 7 P1 PDF original contents** and SHA/page parity against Oct14 originals; one oversized initial-registration visual sample timed out. This narrower PDF review cannot approve all 2026 KP2MI contents or the final job_docs.

## D. Remaining official decision and release gates

- [ ] A named operator reviews the **exact current-cycle post-Skill Test General Manufacturing final online job-application announcement and any annexes**, if/when published. Verify issuance date, effective cohort, sector, valid periods, mandatory files, exception wording, relevant PDF pages, and original URL.
- [ ] If no exact confirmed list exists, keep the applicant-facing stage at **`held_official_notice`** with helpful official-link instructions. Do not invent upload requirements or reuse old/other-cohort lists.
- [ ] Review Korea-common five SHA drift sources, two multi-country HRD sources, five other-country alerts and sign genuine release-day scope/semantics; no synthetic signoff.
- [ ] Separately review latest deployed GitHub Pages `main` and draft HEAD content parity (9/9 assets, 6/6 HTTPS redirects after authorized deployment), privacy/consent, and explicitly authorize beta access OPEN. Interest intake OPEN is not public beta access OPEN.

**Status:** `job_docs=HOLD`, `betaAccess=HOLD`, `humanSemanticReviewApproved=false`, `sourceBaselineHashPromoted=false`, `productionDeploymentApproved=false`, `authorizesRelease=false`. No official submission, app auto-update, or recruitment outreach.
