# KP2MI — 2026 General Manufacturing EPS-TOPIK registration: January/February official PDF annexes

**Captured:** 2026-10-14 UTC (~14:20 KST), direct TLS-verified read-only PDF downloads from public `kp2mi.go.id`; four documents **HTTP 200 / PDF magic valid / 27 pages total**. All pages' embedded text was extracted using PyMuPDF. Key pages were rendered and selected pages visually inspected; this is **not** an assertion that all 27 pages' graphics/screenshot examples were manually reviewed. Do not include identifying example data or scanned official sample images in the repo.

## Files and immutable download evidence

| Document | Pages | Bytes | SHA-256 | Official PDF |
|---|---:|---:|---|---|
| January 27 Sisko P2MI applicant guide (`JUKNIS`) | 14 | 1,797,803 | `31eb8ccdd139fb36c04b1865c84c5083c38dafff9a1a97698bd595915cfd3b72` | [Official guide](https://kp2mi.go.id/uploads/gtgkorea/images/data_27-01-2026_JUKNIS_PENDAFTARAN_CPMI_G2G_KOREA_UBT_UMUM_MANUFAKTUR_DAN_PERIKANAN_TAHUN_2026.pdf) |
| January 27 right/wrong document-scan examples | 10 | 7,989,045 | `4d7b0f3d387ca5e3d7b1522ea0929f55858e693336116e09601cce830c45b654` | [Official scan examples](https://kp2mi.go.id/uploads/gtgkorea/images/data_27-01-2026_Contoh_Scan_Persyaratan_Dokumen_Pendaftaran_yang_Benar.pdf) |
| February 9 personal-data-protection declaration template | 1 | 299,951 | `bde416746990e5d51a1019c3c827449bc3f88fe04934ebab9fe8043c20ed7167` | [Official declaration](https://kp2mi.go.id/uploads/gtgkorea/images/data_09-02-2026_Surat_Pernyataan_Pelindungan_Data_Pribadi.pdf) |
| January 27 BNI virtual-account examination-fee instructions | 2 | 282,862 | `5dcd470f7b50d44ea5ca658f220d87e4e99f1bc27e3131ac1f4d01698a6718e5` | [Official BNI payment guide](https://kp2mi.go.id/uploads/gtgkorea/images/data_27-01-2026_Petunjuk_Pembayaran_EPS_TOPIK_Kode_Bayar_BNI_2026.pdf) |

## Exact findings with page references

**JUKNIS pp.1–5 (initial account and cohort registration):** register at Sisko P2MI, activate the applicant's email, enter biodata, parents and domicile; choose **one** of General Manufacturing and Fisheries. **The chosen sector cannot subsequently be switched** (p.5, repeated p.8). This instruction is for the **2026 UBT General EPS-TOPIK registration cycle** and cannot be repurposed as a definitive later-stage post-Skill Test Manufacturing job-application checklist.

**JUKNIS pp.6–12 (online registration/payment):** the official registration flow requires a bank account in the applicant's own name (p.6), generates an exam-fee billing code on the official platform (p.8), and requires applicant name to match the payee before payment (p.10). Applicant then checks biodata/parent records and uploads the registration requirements with each file **no larger than 2 MB**; one photo example is JPG (pp.11–12). Do **not** copy example bank virtual-account numbers or payment amounts from diagrams into a live applicant payment instruction; verify the real official invoice for the actual cycle.

**JUKNIS p.13 (irreversible choices):** before final save, review the fingerprint capture location, planned stay period and detailed field of work. **After clicking Save, the fingerprint capture location and detailed field of work cannot be changed.** The guide does not say the stay-period field is equally immutable. Page 14 distinguishes an applicant who has already completed biometric capture from one who must wait for an official BP3MI/P4MI call.

**Official right/wrong scan examples, pp.2–8:** trim borders/rotate legible scans, avoid blur/incorrect size, do not upload a scanned printed studio photograph; **upload the original digital photograph**, **3.5 × 4.5 cm with a white background** (p.5). The bankbook example (p.7) says the account number must be legible and **if a physical bankbook is absent, a mobile/internet banking screenshot may be used as the registration example**. This does **not** waive the applicant-ownership requirement or imply any later MCU/visa procedure accepts the same alternative. The **Manufacturing-specific** education example (p.8) requires at least **SLTP or equivalent**; **`Surat Keterangan Lulus (SKL)` is not permitted**; if the diploma is lost, use an official replacement diploma statement from the school/local education authority. The Fisheries education example (p.9) and Fisheries Basic Safety Training item (p.10) **must not** be applied to Manufacturing.

**February 9 personal-data declaration (p.1):** provides a personal-data-protection statement for G-to-G Korea placement, including name, NIK, address and telephone fields and several consents. It is an official **blank-form** source; don't store completed personal details or imply KEP is the government recipient. The application's existing `reg_privacy` document pack requirement is based on the related announcement's rules, not simply the existence of this form.

**BNI virtual-account payment guide, pp.1–2:** describes BNI ATM/mobile/SMS/teller channels for paying the EPS-TOPIK exam invoice using the generated VA/billing code. It does not certify a present-day open application period or justify sharing an illustrative VA account.

## Engineering and release scope

This evidence supports **early 2026 Manufacturing EPS-TOPIK registration stage** only. In October the registration window is already closed; the applicant must follow future official notices for other cycles. It does **not** prove the exact *post-Skill Test final online job-application* 2026 Manufacturing document list (`job_docs`), and it does **not** turn the separate September **optional** Job Capacity Assessment competency documents into mandatory recruitment-stage attachments. Keep `job_docs=held_official_notice`, preserve optional competency upload `status=closed`, and keep all manual signoffs PENDING.

Safe narrowly verified registration improvements: distinguish immutable sector selection from immutable capture location and occupation details; explain a *registration-only* account screenshot fallback from the official samples; distinguish `SKL` from the officially issued diploma-replacement statement; do not invent any ability to edit values after confirmation. Preserve login privacy and don't request, store, or upload applicants' raw scans to KEP or its repository.

**Limits:** all four public PDFs fetched and all 27 page texts processed; only selected image pages were visually inspected, and example visual layouts are not a field-by-field complete official human certification. Real same-day operator review and release signoff remain separate. This is supporting documentation, not a source-hash acceptance or a beta OPEN decision.
