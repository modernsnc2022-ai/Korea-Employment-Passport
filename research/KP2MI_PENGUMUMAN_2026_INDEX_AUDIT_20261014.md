# KP2MI official G-to-G Korea Pengumuman inventory — 2026-10-14

**Evidence status: machine-read official index titles and links; operator signoff still pending.** This is a read-only *candidate notice audit*, not an authorization to release KEP beta, and not a verification of every announcement's PDF attachments.

## Correct, verified KP2MI category

- [Official G-to-G Korea **Pengumuman** index](https://kp2mi.go.id/gtog-korea/pengumuman).
- Actual server-side DataTables feed: `https://kp2mi.go.id/gtog-data/korea/Pengumuman` (queries `draw`, `start`, `length`).
- The earlier `/gtog-korea/info` URL is **Preliminary Training dan Info**, not the comprehensive announcement category; it must never substitute for the actual `Pengumuman` index.

## Reproducible machine-read inventory

Script added: `scripts/audit_kp2mi_pengumuman_2026.py`. It reads the official endpoint, checks dates are newest-first, extracts only official-host links and titles, and pages until it reaches 2025. It cannot automatically claim notice bodies were reviewed.

| Property | Observed read-only result |
| --- | --- |
| Retrieved at (UTC) | 2026-10-14 02:35:07Z |
| Retrieval route | Authorized Windows remote, Python standard library HTTPS to official endpoint |
| Official server total, **all years** | 2,876 notice records (not all 2026) |
| Rows actually fetched | 225 (three pages of 75) |
| Previous-year boundary reached | Yes: 2025 notices reached |
| 2026 notice titles read | **184** |
| Titles explicitly mentioning General/Fisheries Manufacturing 2026 | **7** |
| 2026 General Manufacturing *online job-application* candidate titles | **0 by title classification only**, **not proof that no such notice/attachment exists** |
| SHA-256 of normalized 184 notice metadata | `18c377871ba987be7fb5afd05a85cce141f6a0ee62edd417c550c09ae42130a5` |
| Latest listed 2026 notice | 2026-10-09 (Oct 19–20 Korea G-to-G departures) |
| Oldest indexed 2026 notice before previous-year boundary | 2026-01-05 |
| Output file | `D:\KEP-ID-LIVE-NOTICE-AUDIT-20261014.json` (local QA evidence; no applicant PII) |

### Seven 2026 titles that mention Manufacturing

| Published | Official notice and route relevance |
| --- | --- |
| Sep 17 | [Optional Manufacturing 2026 Skill Test **competency evidence upload**](https://kp2mi.go.id/gtog-detail/korea/pengumuman-persyaratan-unggah-dokumen-kompetensi-peserta-skill-test-ubt-umum-sektor-manufaktur-eps-topik-tahun-2026). KP2MI PENG.2522 dated Sep 17. Optional upload Sep 21 09:00–Sep 23 13:00 WIB **CLOSED**, not the online job-application document checklist. |
| Sep 10 | [2026 Manufacturing General EPS-TOPIK stage-one result](https://kp2mi.go.id/gtog-detail/korea/pengumuman-hasil-ujian-kemampuan-bahasa-korea-eps-topik-ubt-umum-sektor-manufaktur-tahun-2026). 2,020 language passers, Skill Test compulsory, not final selection. |
| May 5 | [First phase 2026 EPS-TOPIK examination fee refunds (Fisheries and Manufacturing)](https://kp2mi.go.id/gtog-detail/korea/pengumuman-pengembalian-biaya-ujian-eps-topik-ubt-umum-sektor-perikanan-dan-sektor-manufaktur-tahun-2026-tahap-pertama). A specific refund notice; not a general employment fee rule. |
| Mar 27 | [2026 EPS-TOPIK UBT examination execution (Fisheries and Manufacturing)](https://kp2mi.go.id/gtog-detail/korea/pengumuman-pelaksanaan-ujian-eps-topik-ubt-umum-sektor-perikanan-dan-sektor-manufaktur-tahun-2026). Earlier testing phase. |
| Feb 16 | [2026 Manufacturing/Fisheries biometrics and applicant online-document verification call](https://kp2mi.go.id/gtog-detail/korea/pengumuman-pemanggilan-perekaman-biometrik-dan-verifikasi-dokumen-online-peserta-pendaftar-program-g-to-g-korea-eps-topik-ubt-umum-sektor-perikanan-dan-sektor-manufaktur-tahun-2026). Examination registration/identity scope, not post-pass job application. |
| Feb 10 | [2026 UBT General registration-time adjustment](https://kp2mi.go.id/gtog-detail/korea/pengumuman-penyesuaian-waktu-pendaftaran-ubt-umum-sektor-perikanan-dan-sektor-manufaktur-program-g-to-g-ke-korea-selatan-tahun-2026). Registration period, already historical. |
| Jan 27 | [2026 General UBT Fisheries and Manufacturing recruitment notice](https://kp2mi.go.id/gtog-detail/korea/pengumuman-pendaftaran-ubt-umum-sektor-perikanan-dan-sektor-manufaktur-progam-g-to-g-ke-korea-selatan-dengan-sistem-poin-tahun-2026). Initial official applicant baseline. |

**Explicit exclusions:** the September 17 *Root Industry* e-certificate/online-application notice is a **separate Root Industry cohort**; the August 19 online-application notice is **Fisheries**; the December 2025 Manufacturing online-application notice is a **2025 cohort**. None can be used as exact online job-application fields, specifications or a compulsory document checklist for **General Manufacturing 2026**.

### Test and release meaning

- Script `--self-test` **PASS**, including 4 fail-closed synthetic mutations (reversed dates, bad links, incomplete and empty pages), Python syntax **PASS**, actual official inventory fetch **PASS** on code SHA `2a31ef5c07725696ec86aa5fa9418ed2af59f66b`.
- This audit records the list titles and URLs, **not a definitive review of all 184 bodies and attachments**. It always writes `releaseAuthorized=false`, `jobDocsVerified=false`, `operatorApproved=false`.
- `recruitment/MANUFACTURING_LAUNCH_CHECK.json` retains `operatorConfirmedCompleteReview=false`; `recruitment/ID_BETA_SOURCE_SIGNOFF.json` retains `pending_manual_source_signoff`. The 2026 exact `job_docs` remains HOLD. Current source monitor: 83/84 fetched with Nepal notice index HTTP 500, Korea-common sources fetched, global alerts still visible, no auto hash acceptance.
- The latest 76/76 headless Edge browser regression was verified on an earlier application-code SHA `69c2cc6476bd411b04725a46064ca83291374307`. This added script does not alter app runtime or accepted source facts; it does not imply that this later GitHub commit was E2E tested.
- Manual release requires reviewing the official notice inventory **again on the actual launch date**, confirming relevant notice contents, selectively signing current-day official sources and reviewing same-HEAD deployment. Never promote release by this title-only audit.
