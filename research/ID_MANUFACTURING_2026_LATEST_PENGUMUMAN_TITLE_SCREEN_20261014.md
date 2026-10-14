# KP2MI 2026 General Manufacturing — read-only latest notice-index scan

**Scan:** 2026-10-14, retrieved from the official `https://kp2mi.go.id/gtog-data/korea/Pengumuman` under the current [Pengumuman listing](https://kp2mi.go.id/gtog-korea/pengumuman).

- HTTPS **HTTP 200**, server-side DataTables `GET` (`draw=1;start=0;length=320`), **2,876** historical items reported, **320** newest rows actually inspected. The sample reaches **15 July 2025**, past the January 2026 general exam registration entries.
- Exact title/date/official-URL digest for these 320 inspected rows: **SHA-256 `5fe9918d95c2676222265a3169d3dfb626d65b4bfe2f076dfe6b4241c7ce3d04`**. This digest is a read-only inventory fingerprint, **not** an approved rules-source baseline.
- **7** notices had titles explicitly identifying **2026 UBT Umum General Manufacturing**, alone or with Fisheries. **0** titles were classified as an exact **2026 General Manufacturing post-Skill Test final online job-application notice**.
- **3** 2026 online-applications titles were found for **different cohorts** and must **never** be used as 2026 General Manufacturing final job-application requirements:
  1. September 17 2026 **Root Industry welding/casting**, 
  2. August 19 2026 **UBT Umum Fisheries**, 
  3. July 21 2026 **UBT Khusus special exam**.
- By contrast, the December 5 2025 **General Manufacturing online application** announcement belongs to **2025**, and a 2026 publishing date alone would not make a 2025-cohort title applicable.

## Seven actual 2026 UBT Umum Manufacturing-related titles

| Date | Official notice | Classification |
|---|---|---|
| 17 Sep | [Optional 2026 Manufacturing Skill Test competency documents](https://kp2mi.go.id/gtog-detail/korea/pengumuman-persyaratan-unggah-dokumen-kompetensi-peserta-skill-test-ubt-umum-sektor-manufaktur-eps-topik-tahun-2026) | closed optional upload; **not** final job-application documents |
| 10 Sep | [2026 Manufacturing first-stage EPS-TOPIK result](https://kp2mi.go.id/gtog-detail/korea/pengumuman-hasil-ujian-kemampuan-bahasa-korea-eps-topik-ubt-umum-sektor-manufaktur-tahun-2026) | results and mandatory Skill Test |
| 5 May | [2026 Manufacturing/Fisheries exam fee refund](https://kp2mi.go.id/gtog-detail/korea/pengumuman-pengembalian-biaya-ujian-eps-topik-ubt-umum-sektor-perikanan-dan-sektor-manufaktur-tahun-2026-tahap-pertama) | exam-fee refund |
| 27 Mar | [2026 General Manufacturing/Fisheries EPS-TOPIK exam](https://kp2mi.go.id/gtog-detail/korea/pengumuman-pelaksanaan-ujian-eps-topik-ubt-umum-sektor-perikanan-dan-sektor-manufaktur-tahun-2026) | examination |
| 16 Feb | [2026 biometric recording and verification](https://kp2mi.go.id/gtog-detail/korea/pengumuman-pemanggilan-perekaman-biometrik-dan-verifikasi-dokumen-online-peserta-pendaftar-program-g-to-g-korea-eps-topik-ubt-umum-sektor-perikanan-dan-sektor-manufaktur-tahun-2026) | examination registration verification |
| 10 Feb | [2026 general registration schedule adjustment](https://kp2mi.go.id/gtog-detail/korea/pengumuman-penyesuaian-waktu-pendaftaran-ubt-umum-sektor-perikanan-dan-sektor-manufaktur-program-g-to-g-ke-korea-selatan-tahun-2026) | closed initial examination registration |
| 27 Jan | [2026 initial UBT Umum Manufacturing/Fisheries registration](https://kp2mi.go.id/gtog-detail/korea/pengumuman-pendaftaran-ubt-umum-sektor-perikanan-dan-sektor-manufaktur-progam-g-to-g-ke-korea-selatan-dengan-sistem-poin-tahun-2026) | closed initial exam registration only |

This **title-level read-only follow-up does not re-certify all source bodies or their attached files**. Seven 2026 HTML pages and their attachment URLs were previously retrieved in `research/ID_MANUFACTURING_2026_7_NOTICE_DETAIL_AUDIT_20261014.md`. Four Jan/Feb exam registration PDFs and six Sep Skill Test *optional* PDF annexes were independently downloaded/examined with limited selected-page visual checks and SHA digests recorded in the corresponding research documents. None is verified as a final 2026 General Manufacturing post-Skill Test job application checklist.

## Tool, restrictions and release decision

New reproducible **read-only** tool: `python scripts/audit_id_manufacturing_notice_index_live.py --self-test`, then `python scripts/audit_id_manufacturing_notice_index_live.py` or `--json`. It uses HTTPS official notice DataTables, avoids printing applicant/worker names or source body lists, and enforces a full year boundary (2026 followed by 2025). Tests deliberately reject a **2025** UBT Umum Manufacturing online application, a **2026** publication about a 2025 cohort, and other 2026 Fisheries/Root Industry/special exam online registrations as valid General Manufacturing 2026 final documents. If a future matching title appears, it is reported as a **review candidate**, **not** an approved form checklist.

**Safety status:** `operatorConfirmedCompleteReview=false`, `exactFinalJobDocumentsVerified=false`, `sourceBaselineAccepted=false`, `betaReleaseAuthorized=false`. Keep `job_docs=held_official_notice`. The actual official same-day human content/attachment review and separate signature remain required; the beta PR remains Draft/unmerged. No Pages deployment or GitHub Actions were triggered by this scan.
