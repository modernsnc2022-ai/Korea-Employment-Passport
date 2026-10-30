# Indonesia E-9 beta — 3 Korea-common official sources: fresh independent recheck

**Retrieved:** 2026-10-14 **05:08:28 UTC** / 14:08 KST. Machine-only, read-only source retrieval through authorized Windows with normal TLS verification; no source hash baseline acceptance, no final government/legal review by a named human, no beta access approval.

**Scope:** Only the three **Indonesia/Korea-shared changed** official sources in `recruitment/ID_RELEASE_SOURCE_SCOPE_20261014.json`, **not** the five other-country pending/failing alerts. Existing `docs/data/source_review_status.json` `state=review_required` remains untouched.

## 1. Korean wage statement statute

- Monitored ID `labor_standards_wage_statement`.
- Official current source: [국가법령정보센터 근로기준법 제48조](https://law.go.kr/LSW/lsLinkCommonInfo.do?lsJoLnkSeq=1027161979).
- HTTP 200; final URL equals requested HTTPS URL. Page title: **국가법령정보센터 | 조문정보**.
- Parsed page explicitly names **근로기준법 [시행 2026. 10. 8.] [법률 제21533호, 2026. 4. 7., 일부개정] 제48조(임금대장 및 임금명세서)**.
- Statutory paragraph **제48조 ②** requires the employer to provide a wage statement when paying wages, including components, calculation method, and details of lawful wage deductions. The page provides the legal basis for applicant guidance to **keep payslips**, but not a conclusion on every employer-specific disputed calculation.
- Raw fetched response SHA-256: `b6d4f60f6268b020939047e3810d5c4fee5189ac5775cc296fd9138adba8477a`.
- Stripped body SHA-256: `a8754d0fbd0d59f2164d056a6e40cdb7b7b8048cb95b8a87726481db40085786`.

## 2. KDCA Q-CODE eligible traveller categories

- Monitored ID `kdca_qcode_input`.
- Original configured URL: [질병관리청 Q-CODE 기존 입력 페이지](https://qcode.kdca.go.kr/qco/cd/codeInput2.do).
- **301 HTTPS** redirect to actual official [KDCA Travel Health — Q-CODE 발급](https://travelhealth.kdca.go.kr/travel/cd/qcoInfo.do); final HTTP 200.
- Visible official **입력대상** section:
  - 입국자 who visited, stayed in, **or transited** through a **중점검역관리지역**.
  - 입국자 who visited, stayed in, or transited through a **검역관리지역**, **if fever, cough, or similar symptoms apply**.
- Therefore Q-CODE **must not be advertised as universally mandatory for all Indonesia E-9 arrivals**. Applicable regions and current conditions are subject to the official contemporaneous KDCA information and each actual departure notice.
- The page says details may be pre-entered from **seven days before Korea arrival to entry**, and describes on-arrival kiosk/tablet alternatives for travellers not pre-issued a QR code. This is not a waiver of legally applicable health-screening duties.
- Raw response SHA-256: `14841f0e5fac55b33b6d7c44acc95f631d7f4cc68a27e152b76cc8e21266f29f`.
- Parsed body SHA-256: `c7ff92c67b21468dbc6f8be4547ea6c4032f150c065b2fd212e7e822fa8a8aee`.

## 3. MOEL 1350 official contact

- Monitored ID `moel_1350_contact`.
- [고용노동부 고객상담센터 1350전화 상담](https://1350.moel.go.kr/home/hp/ch/callchat.do).
- HTTP 200 directly over HTTPS. Page title: **1350고용노동부 고객상담센터 홈페이지**.
- Official live page says **국번없이 1350**, **전화요금: 유료**, **이용시간: 평일 09:00 ~ 18:00** (Korea local time). It lists labour standards and foreign employment permits among consultation categories.
- This proves advertised telephone details, **not** guaranteed real-time call connectivity, case-resolution outcome, or Indonesian-language interpreting.
- Raw response SHA-256: `38f627b1f0a0b4d78ab331a9857e70d2f7f2534d425330dfd41ca6aa735945b3`.
- Parsed body SHA-256: `846f066be872e653a875fb9072badc2cd9d58dbb1546252fe040ef0e06b39d71`.

## Signoff and release boundary

All **three** pages were fetched with HTTP 200 and expected official TLS hosts, and actual body text matched the narrow claims above. This narrows the outstanding manual approval work but **does not convert** `ID_BETA_SOURCE_SIGNOFF.json.status=pending_manual_source_signoff` to approved. A named operator must confirm accurate product representations and the current-day source watch, record a genuine signoff timestamp, and acknowledge the five other-country alerts:

`np_eps_notice_index` (HTTP 500), `vn_colab_eps_notices`, `lk_slbfe_home`, `kg_migrant_home`, `mm_mol_dol_index`. **None** is auto-accepted or made part of the Indonesia Manufacturing rule pack.

The latest independent evidence is a *new* 2026-10-14 read-only capture. It is **not** the accepted official fingerprint baseline; the latter remains unchanged. Apart from source approval, beta OPEN still requires the KP2MI 2026 Manufacturing complete notice/attachments human review, the legacy GitHub Pages first-hop HTTPS issue resolution, the same-HEAD production deployment gate, and a separate explicit beta-access release decision.

**Operational safety:** No applicant/worker personal data, no account secrets, no external submissions, no auto-updating official decisions, no GitHub Actions, no production deploy.
