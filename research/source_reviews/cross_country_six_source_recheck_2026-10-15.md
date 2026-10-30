# KEP cross-country source watch — six drift candidates (2026-10-15)

**Scope:** Six of the ten 84-source watch changes, each fetched twice independently after the full 84/84 read-only scan. All six reproduced the same current normalized SHA-256 across both fetches. Repeated-hash stability does NOT prove that the official instructions are semantically unchanged or that a specific future country's workflow is ready.

| Monitored ID | Correct geographic relevance | Current normalized SHA-256 | Narrow finding and decision |
| --- | --- | --- | --- |
| `mm_hrdk_schedule_index` | **Multi-country HRD Korea EPS-TOPIK schedule**, NOT Myanmar-specific despite the `mm_` source ID | `d8d9b5d35f0d0fbd5afab7de5cd62c9dde888d74daa52105971780226ee25855` | Official index covers multiple national schedules, including Philippines, Laos and Sri Lanka; separate HRD record for **2026 Indonesia specialized Root Industry/Mold CBT** exists. None alone proves a fresh general Manufacturing 2026 Indonesian application date. **Cross-country relevance review pending** |
| `np_eps_notice_index` | Nepal EPS | `06241589a60fc5372b6cc3c7f39b0739c08d98e63140f66b5223713b12a79f05` | Nepal official notices include October 2026 departure-group announcements and 2026 EPS-TOPIK testing announcements. Distinguish 2025 Manufacturing, 2026 exam cohorts and actual worker departure groups. **Nepal rule promotion pending** |
| `vn_colab_eps_notices` | Vietnam COLAB EPS | `1f0e5daceaceb08c1fe53bf5a3aa924060b7806f4f43d0a4c0bb1c6cc2efb6f4` | Recent EPS departure and 2026 agriculture/fisheries exams; other 2026 Vietnamese Manufacturing exam/result notices also exist in COLAB's official listings. Match each to cycle and sector before country pack editing. **Vietnam rule promotion pending** |
| `lk_slbfe_home` | Sri Lanka SLBFE homepage | `5dd07edf37428fa9067aa0ababb7b5203b3131d99a4785448225a0a915055e58` | Generic official site change alone is not a validated Korea E-9 Manufacturing 2026 notice or fee. **Sri Lanka country-specific notice check pending** |
| `kg_migrant_home` | Kyrgyzstan official migrant portal | `c711d785855357eddef851208b32335f58112452c0ae9ee2cccc5b9203f5dfee` | Official portal redirects from `https://migrant.kg/` to `/kg/`; a homepage change cannot confirm a Korea E-9 Manufacturing step. **Kyrgyzstan-specific review pending** |
| `mm_mol_dol_index` | Myanmar Ministry of Labour, Department of Labour | `dad0fa868f0c40be73699e1ed57f916a74ec00c3f68c6fad9edb632734f1dbb9` | Generic department page change cannot verify a 2026 Korea EPS Manufacturing cohort or fee. **Myanmar-specific review pending** |

## Official URLs inspected / cross-checked

- Multi-country HRD Korea: https://epstopik.hrdkorea.or.kr/epstopik/abot/exam/selectSechduleDescList.do?lang=en ; specific Indonesia **specialized** Root Industry/Mold record: https://epstopik.hrdkorea.or.kr/epstopik/abot/exam/sechduleDetail.do?examNation=012&examNot=54&examYear=2026&lang=ko&lcnsId=001
- Nepal: https://epsnepal.gov.np/notices
- Vietnam: https://colab.moha.gov.vn/tin-tucs/357/Chuong-trinh-EPS.aspx
- Sri Lanka: https://www.slbfe.lk/
- Kyrgyzstan: https://migrant.kg/
- Myanmar: https://www.mol.gov.mm/mol-department-of-labour/

## Decision and retained release protection

**Correct earlier classification:** four Korea-common sources, **one multi-country HRD Korea schedule**, and five country-specific foreign official sources. The `mm_hrdk_schedule_index` ID is misleading; never treat it as solely Myanmar-related or suppress its possible Indonesia-relevant future changes.

There is no basis from these six index/homepage observations to authorize a route, application deadline, exam date, fee, or Indonesian general Manufacturing requirement. Preserve **every changed SHA as unaccepted**, all six source alerts for separate semantic review, all non-Indonesian country packs on their existing holds, `job_docs` HOLD, applicant HTTPS intake OFF and beta HOLD. Do not rewrite the historical 2026-10-14 scope/signed state. Final human country-review and live deployment evidence remain outstanding.
