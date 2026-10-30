# KEP M23 — KP2MI 2026 Manufacturing P1 official PDF contents / SHA parity

**Observed:** 2026-10-17, Indonesia (Asia/Jakarta) / Korea. **Data class:** machine-only original PDF audit with limited layout spot-checks; no government/operator release signoff.

## Actual new verification

- M22 P1 official list: **7 KP2MI 2026 documents** (three January initial EPS-TOPIK exam-registration files, four September optional Skill Test competency files). Official HTTPS URL validation and source-scope guards succeeded.
- A **single rate-limited HTTP GET attempt per PDF** retrieved **6 complete PDF bodies**, each with valid PDF magic and PyMuPDF page structure. All **28 pages** were opened for text extraction/page evidence; the six PDFs' **SHA-256 and page counts exactly matched the earlier independently archived 2026-10-14 original-PDF evidence**.
- **1 incomplete**: the January 27 right/wrong document-scan example (~8 MB) timed out after partial transmission (curl exit 28). No new valid-PDF SHA; **not proven broken/missing**. Historic 2026-10-14 full body was previously verified at **10 pages** with SHA recorded in the earlier audit.
- First pages of all six complete PDFs were rendered to previews privately; the January initial-registration guide p13 and September competency guide p3 were additionally rendered and visually inspected. This is **not full-page-by-page visual certification**, including the older 10-page mostly visual example.
- Local-only thumbnails, downloaded PDF bytes, illustrative applicant information and temporary system paths were **not added to public repo artifacts**.

## Original six byte-level matches

| Official 2026 PDF | Stage | Pages | SHA-256 |
|---|---|---:|---|
| [27 Jan initial registration technical guide](https://kp2mi.go.id/uploads/gtgkorea/images/data_27-01-2026_JUKNIS_PENDAFTARAN_CPMI_G2G_KOREA_UBT_UMUM_MANUFAKTUR_DAN_PERIKANAN_TAHUN_2026.pdf) | Early **EPS-TOPIK exam registration** | 14 | `31eb8ccdd139fb36c04b1865c84c5083c38dafff9a1a97698bd595915cfd3b72` |
| [27 Jan BNI exam-fee instructions](https://kp2mi.go.id/uploads/gtgkorea/images/data_27-01-2026_Petunjuk_Pembayaran_EPS_TOPIK_Kode_Bayar_BNI_2026.pdf) | **Exam fee billing only** | 2 | `5dcd470f7b50d44ea5ca658f220d87e4e99f1bc27e3131ac1f4d01698a6718e5` |
| [17 Sep conditional competency assessment form](https://kp2mi.go.id/uploads/gtgkorea/images/data_17-09-2026_FORMULIR_UJI_KOMPETENSI.pdf) | Optional Job Capacity Assessment | 2 | `20375fd344b7f6a1bbc9aa51f6e6852e2aaa681586b89ddbdd3baacf984c99cd` |
| [17 Sep competency document technical guide](https://kp2mi.go.id/uploads/gtgkorea/images/data_17-09-2026_JUKNIS_PEMENUHAN_DOKUMEN_UJI_KOMPETENSI_UBT_UMUM_MANUFAKTUR_2026.pdf) | Optional Job Capacity Assessment | 7 | `6a6cad95c43ceea806ed3b713d4c32d7af0c5dcc80dc3c4a1f11b656fd3b8dc0` |
| [17 Sep competency form filling guide](https://kp2mi.go.id/uploads/gtgkorea/images/data_17-09-2026_PETUNJUK_TEKNIS_PENGISIAN_FORMULIR_UJI_KOMPETENSI.pdf) | Optional Job Capacity Assessment | 2 | `afd1c586db3fc799ccda8bce4dc2bb012eb8fb7eabca75e826249bfb3ea46647` |
| [17 Sep employer work-experience form](https://kp2mi.go.id/uploads/gtgkorea/images/data_17-09-2026_SURAT_KETERANGAN_PENGALAMAN_KERJA.pdf) | Conditional work-experience evidence | 1 | `1eb3c077995ee8f7097f35830fc2e78a1eb26d0c28592b09d54085ef6982e1cf` |

**Unverified this run:** [27 Jan scanned document example](https://kp2mi.go.id/uploads/gtgkorea/images/data_27-01-2026_Contoh_Scan_Persyaratan_Dokumen_Pendaftaran_yang_Benar.pdf) — partial transfer, no new SHA. Last original archive: 2026-10-14, 10 pages, SHA `4d7b0f3d387ca5e3d7b1522ea0929f55858e693336116e09601cce830c45b654`.

## Specific original layout cross-checks

1. **17 Sep JUKNIS p3 item 6**: **only IF** an applicant submits one of the four optional competency evidence classes, they must also complete/attach the competency form. This is **not a mandatory application file for all Manufacturing applicants**. The same appendix's screenshot includes Fisheries-labelled example upload fields, which must not override the applicant's original Manufacturing category.
2. **27 Jan JUKNIS p13**: following confirmation/save, the **fingerprint recording location and detailed job field** cannot be changed according to the displayed guidance. The notice does not say the selected period of stay is similarly immutable. This guide concerns **initial examination application**, not the later job registration dossier.
3. The separate 2026-09-10 official Manufacturing EPS-TOPIK result notice states attending **Skill Test is mandatory for those who pass Stage 1**, while **Job Capacity Assessment evidence is optional** for qualified participants. These are separate processes and time windows.

## Verification, unresolved signoffs and next action

- `scripts/audit_m23_p1_original_pdf_bodies.py`: guarded official HTTPS single-try PDF retrieval, PyMuPDF page evidence and private first-page render; M23 source metadata only in repository. **P1 self-test PASS**.
- `scripts/check_m23_pdf_original_lineage.py`: requires previously recorded official PDF SHA/page parity, exact six/one outcome and manual-approval HOLD; **ten mutation tests rejected**.
- `research/source_reviews/indonesia_m23_priority_pdf_body_audit_2026-10-17.json`: body/metadata results and factual capture failure.
- `research/source_reviews/indonesia_m23_pdf_lineage_2026-10-17.json`: cross-date verifiable signed-off-vs-machine evidence boundary.
- **Still PENDING:** responsible human meaning/signature for Korea shared official sources 5, HRD multi-country 2, other countries 5; original PDF visual/scoping signoff; actual 2026 post-Skill-Test General Manufacturing final online job application documents. The linked file's upload/registration periods are **not reopened** by this audit.
- **Next:** skip unnecessary bulk refetch of 8MB visual scan; preserve previous original digest, separately inspect if needed. Assess explicit final Manufacturing job_docs from same-cycle official notices, then perform approved candidate live deployment parity and named signoff **only when separately authorized**.

**Release state:** exact `job_docs=HOLD`; source hashes not auto-accepted; `betaAccess=HOLD`; no main merge, no Pages production deployment, no beta OPEN.
