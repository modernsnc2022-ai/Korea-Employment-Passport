# Official-source review — KP2MI common template shift

Review date: 2026-10-04 (KST)

## Trigger

The scheduled official-source monitor detected changes in 22 KP2MI HTML sources and correctly moved the app source state to `review_required`. No rules were auto-published.

## Diagnostic result

All 22 changed sources were fetched twice in immediate succession by the source-volatility diagnostic.

- Sources tested: 22/22
- Stable across immediate repeated fetches: 22/22
- Volatile across repeated fetches: 0/22
- Content-length delta versus reviewed baseline: exactly **-2 characters for every one of the 22 sources**
- Fetch failures: 0 in the scheduled monitor
- Classification: **common KP2MI page/template text shift; no evidence of 22 independent rule changes**

The identical -2 delta spans unrelated pages including registration, psychology, EPS-TOPIK, MCU/visa, OPP, departure notices, old roster guidance, the Korea information index, and the KP2MI contact page.

Diagnostic workflow evidence:
- full 22-source run: workflow run 37158621460 / job 111307149578
- representative 5-source run: workflow run 37158798745 / job 111307672987

## Semantic spot checks

Current official/crawled content was compared against the structured rules used by the app:

1. **2026 registration / Manufacturing + Fisheries**
   - Official page still describes the 2026 psychology/MCU requirements in the online-application flow.
   - Source: https://www.kp2mi.go.id/gtog-detail/korea/pengumuman-pendaftaran-ubt-umum-sektor-perikanan-dan-sektor-manufaktur-progam-g-to-g-ke-korea-selatan-dengan-sistem-poin-tahun-2026

2. **2026 psychology**
   - Current page still states HIMPSI psychologist selection, Sisko P2MI ID, Rp350.000 fee, SIAP HIMPSI → Sisko P2MI result transfer, and the 2026 graduate psychology → MCU I → FIT TO WORK → online application gate.
   - Source: https://www.kp2mi.go.id/gtog-detail/korea/pengumuman-ketentuan-pelaksanaan-pemeriksaan-psikologi-bagi-calon-pekerja-migran-indonesia-program-g-to-g-ke-korea-selatan-kelulusan-sebelum-tahun-2026-dan-kelulusan-tahun-2026

3. **MCU II / visa preparation**
   - Current notices continue to carry the existing 2026 psychology/MCU II and visa-document preparation structure.
   - Source: https://kp2mi.go.id/gtog-detail/korea/pengumuman-panggilan-pemeriksaan-medical-check-up-mcu-ii-tanggal-08-september-2026-dan-persiapan-pemberkasan-dokumen-visa-bagi-calon-pekerja-migran-indonesia-reguler-program-g-to-g-ke-korea-selatan

4. **Departure**
   - The 15 September 2026 notice still states the 14 September 08:00 WIB preparation attendance and 15 September departure flow used by the app.
   - Source: https://kp2mi.go.id/gtog-detail/korea/pengumuman-pemberangkatan-pekerja-migran-indonesia-program-g-to-g-korea-selatan-tanggal-15-september-2026

5. **KP2MI contact**
   - Current official contact listing remains the basis for the KP2MI Human Help route.
   - Source: https://kp2mi.go.id/index.php/profil-kontak

## Manufacturing 2026 job-application watch

The review did **not** verify a Manufacturing-specific 2026 e-certificate / online job-application notice that answers the five held submission-detail questions.

The currently discoverable 2026 detailed online-application notice is sector-specific to Fisheries. It must not be copied into Manufacturing 2026.

Therefore these remain on explicit HOLD:
- `job_docs`
- `job_scan`
- `job_name`
- `job_edit`
- `job_submit`

GitHub issue #2 remains open until Manufacturing 2026 official evidence explicitly resolves them.

## Decision

Accept the new fingerprints for only the 22 reviewed KP2MI HTML sources as a **reviewed common-template baseline shift**.

- No route-rule change is approved by this review.
- No Exact Answer content is changed by this review.
- No form/document requirements are changed by this review.
- Manufacturing 2026 job-application HOLD remains unchanged.
- After baseline update, the official-source monitor must run again and independently confirm a clean state.
