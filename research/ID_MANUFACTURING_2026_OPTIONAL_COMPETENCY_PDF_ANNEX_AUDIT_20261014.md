# Indonesia 2026 General Manufacturing — optional Skill Test competency PDF annex audit

**Reviewed:** 2026-10-14, by read-only retrieval of six **public KP2MI PDF annexes** linked from [KP2MI notice PENG.2522/04.04/PP.02.04/IX/2026](https://kp2mi.go.id/gtog-detail/korea/pengumuman-persyaratan-unggah-dokumen-kompetensi-peserta-skill-test-ubt-umum-sektor-manufaktur-eps-topik-tahun-2026). **Human final release signoff: PENDING**. The exact optional upload window **2026-09-21 09:00–2026-09-23 13:00 WIB is CLOSED**. Current implementation must not encourage uploads outside an official period.

## Annexes retrieved (public originals, unmodified)

| Official PDF | Pages | PDF SHA-256 | Review role |
|---|---:|---|---|
| [Petunjuk Teknis Pemenuhan Dokumen Uji Kompetensi](https://kp2mi.go.id/uploads/gtgkorea/images/data_17-09-2026_JUKNIS_PEMENUHAN_DOKUMEN_UJI_KOMPETENSI_UBT_UMUM_MANUFAKTUR_2026.pdf) | 7 | `6a6cad95c43ceea806ed3b713d4c32d7af0c5dcc80dc3c4a1f11b656fd3b8dc0` | Optional evidence submission instructions; p3 item 6 is critical |
| [Formulir Uji Kompetensi](https://kp2mi.go.id/uploads/gtgkorea/images/data_17-09-2026_FORMULIR_UJI_KOMPETENSI.pdf) | 2 | `20375fd344b7f6a1bbc9aa51f6e6852e2aaa681586b89ddbdd3baacf984c99cd` | Conditional application form accompanying chosen evidence |
| [Konfirmasi Dasar Faktual Pengalaman Kerja](https://kp2mi.go.id/uploads/gtgkorea/images/data_17-09-2026_FORMULIR_SURAT_KONFIRMASI_DASAR_FAKTUAL_PENGALAMAN_KERJA.pdf) | 1 | `daaa82864dfc7fe3e49cacb7d224de81d3cf66bec256655fa815290ce72c2ffe` | Employer-unavailable / bankrupt work-experience fallback |
| [Surat Keterangan Pengalaman Kerja](https://kp2mi.go.id/uploads/gtgkorea/images/data_17-09-2026_SURAT_KETERANGAN_PENGALAMAN_KERJA.pdf) | 1 | `1eb3c077995ee8f7097f35830fc2e78a1eb26d0c28592b09d54085ef6982e1cf` | Standard employer-issued work-experience proof |
| [Petunjuk Teknis Pengisian Formulir Uji Kompetensi](https://kp2mi.go.id/uploads/gtgkorea/images/data_17-09-2026_PETUNJUK_TEKNIS_PENGISIAN_FORMULIR_UJI_KOMPETENSI.pdf) | 2 | `afd1c586db3fc799ccda8bce4dc2bb012eb8fb7eabca75e826249bfb3ea46647` | Filled field hints; sector according to EPS exam card |
| [Contoh Scan Dokumen Kompetensi yang Benar](https://kp2mi.go.id/uploads/gtgkorea/images/data_17-09-2026_CONTOH_SCAN_DOKUMEN_KOMPTENSI_YANG_BENAR.pdf) | 8 | `d7b4b7af6e7f49457a71da1e6c7080f174191e32f3b558b3438bfcdc6705791c` | Scanning examples; many pages image-only and **not** text-certifiable |

All six public PDF URLs returned valid PDF files and could be opened. The 21 total pages were counted; selected pages and forms were rendered to images and inspected, with text extracted for the other pages. **The eight-page example scan is primarily visual**; no exhaustive visual signoff or OCR was performed. We do not ingest or publish personal details visible in document examples.

## Narrow official conclusions, independent of optional status

1. **Mandatory Skill Test vs optional Job Capacity Assessment.** A 2026 first-stage Manufacturing EPS-TOPIK passer must attend the Skill Test, but supporting competency evidence upload is optional for eligible applicants and was time-bound to September 21–23, 2026. Evidence categories: Manufacturing experience at least one year, manufacturing Diploma I or higher, manufacturing vocational training at least 120 hours, or valid national Manufacturing competency certification.
2. **Conditional form duty:** the **JUKNIS p3 item 6** states that **IF any one of the four optional evidence document types is uploaded**, a completed **Formulir Uji Kompetensi** must **also** be uploaded. The form is *not* a mandatory requirement for everybody taking the Skill Test.
3. **Experience-proof fallback:** where the employer cannot issue a work-experience certificate (e.g., shutdown/bankruptcy or microbusiness status), the official **Konfirmasi Dasar Faktual** form requires **two sureties who are not blood or marital relatives**, signed forms and identity copies/contact details, plus appropriate employment-contract or visa/immigration evidence. This fallback is **conditional**, not a blanket requirement for all Manufacturing applicants.
4. **Employer-issued proof:** the dedicated **Surat Keterangan Pengalaman Kerja** requires employer confirmation, authorized signature/seal and issuer contact, as applicable; the attached form says one certificate per employer. These details should not be generalized into a final job-application checklist.
5. **Shared form caveat:** the multilingual official competency form includes Manufacturing, Fisheries and other sector options; the filling guide instructs applicants to mark the **sector from their own EPS exam card**. An unrelated sector label elsewhere on the generic form should not be treated as a Manufacturing-rule change.
6. **Submission-date/URL caveat:** the example technical guide has historically formatted website screenshots and provides form-filling instructions. A prior **closed** date or screenshot is not proof that current submission has reopened; the application must point to a fresh KP2MI cycle notice before any new upload action.

## Product changes in PR #324

- `docs/data/id_e9_manufacturing_2026.json`: conditional documents and original official form/guide URLs recorded inside `skill_competency.competencyUploadNotice.conditionalSubmission`, with `optional=true`, `status=closed`, `notJobApplicationDocuments=true`.
- `docs/data/id_e9_manufacturing_2026_id.json`: applicant-visible Bahasa Indonesia explains the **if-chosen** form and company-cannot-issue fallback, while keeping "SUDAH BERAKHIR" and "OPSIONAL".
- `docs/data/exact_answer_rules_v1.json`: existing `skill_docs_wait_official_2026` answer extended, rather than converting held `job_docs` into an invented final Manufacturing checklist.
- `docs/sw.js`: `kep-v131` rotates offline copy.
- `tests/indonesia-extra-audit.spec.js`: 320px Chromium test for conditional requirement, closed window and held job application.

**Operational state:** beta interest intake OPEN / real beta access HOLD; no official hash acceptance, no automatic final job-application documents, no actual applicant data uploaded, no outside messages sent, no official applicant signoff or Pages release. Excluding user feedback from product-development completion never excuses basic safety gates.

Local isolated verification output: `C:\Users\USER\AppData\Local\Temp\kep_id_scope_verify_20261014\kp2mi_2026_09_17_attachment_preflight.json` and private unmodified public PDFs. Do not commit scanned example names, IDs or sample certificates into the GitHub repository.
