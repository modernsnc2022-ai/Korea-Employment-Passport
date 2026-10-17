# KEP M28 — 다국가 HRD Korea 및 타국 출처 7건 공식 원문 재검사

**기준:** 2026-10-17 WIB/KST. **형식:** 공식 HTTPS HTML을 직접 재수집한 기술적 관측 및 인도네시아 규칙 격리 검증. **공식자료 책임자의 의미 승인, SHA 수동 승인, 공개 베타 승인이 아닙니다.**

## 1. 공식 원문 7건 재검사 결과

| 출처 ID | 범위 | 공식 URL | M19 같은 날 초기 SHA 대조 | M28 접속 |
|---|---|---|---|---|
| `mm_hrdk_schedule_index` | HRD Korea 다국가 시험 일정 | https://epstopik.hrdkorea.or.kr/epstopik/abot/exam/selectSechduleDescList.do?lang=en | 일치 | CA 검증 HTTPS 원문 성공 |
| `mm_hrdk_skills_candidates` | HRD Korea 다국가 기능·기술 평가 대상 | https://epstopik.hrdkorea.or.kr/epstopik/pass/candidate/functionalLevelCandidateList.do?lang=en | 일치 | 원문 성공 |
| `kg_migrant_home` | 키르기스스탄 | https://migrant.kg/ | 일치 | 원문 성공 |
| `lk_slbfe_home` | 스리랑카 | https://www.slbfe.lk/ | **불일치** | 원문 성공 |
| `mm_mol_dol_index` | 미얀마 | https://www.mol.gov.mm/mol-department-of-labour/ | 일치 | 원문 성공 |
| `np_eps_notice_index` | 네팔 | https://epsnepal.gov.np/notices | 일치 | 원문 성공 |
| `vn_colab_eps_notices` | 베트남 | https://colab.moha.gov.vn/tin-tucs/357/Chuong-trinh-EPS.aspx | 일치 | 원문 성공 |

**기계 관측:** 7개 HTTPS 원문 수집 성공, 이전 2026-10-17 관측 정규화 SHA 동일 **6건**, 변경 **1건**, 원문 접근 불능 **0건**. 비교 기준은 **같은 날 M19 초기 관측 지문**이지 인간이 수동으로 승인한 규칙값이 아닙니다.

**스리랑카 재검사 변화:**

- 이전 동일일 관측 SHA-256: `71183b66eb53f41266a4d25dbb551716b6ec85b2ba66446d089a1856eba41733`
- 이번 M28 관측 SHA-256: `2c6dbfffacebfdb42973a0579494b033db7fc917700cec984b3ac5ceed62cc47`
- 둘 다 원문 HTML 텍스트 정규화 지문입니다. 지문 차이는 **사이트 내용/위젯 변경**을 나타낼 수 있지만 **EPS 정책 개정 여부 및 효력일은 확인되지 않았습니다**. 원본과 실제 업무 안내를 책임자가 검토해야 합니다.

## 2. 적용범위 격리 — 핵심 결론

- HRD Korea 두 페이지는 EPS 프로그램에 여러 참가국이 있을 수 있는 **다국가 자료**입니다. 원래 source ID의 `mm_` 접두사 때문에 *미얀마만의 공고로 판단해 제외하는 행위*는 금지합니다.
- 키르기스스탄, 스리랑카, 미얀마, 네팔, 베트남의 공고는 인도네시아 2026 UBT Umum 일반 제조업의 최신 모집서류·절차를 증명하지 않습니다. 인도네시아 `Country Pack`에 요구 서류·시험 일정·자격·최종 구직등록 요건으로 자동 반영해서는 안 됩니다.
- 앱의 실제 `sourceNeedsReview` 함수는 해당 **7개 URL 모두 변경 경고를 유지**합니다. 잘못된 모니터 집계/승인 값을 가정한 5개 상태도 fail-closed입니다.
- 한국 공통 출처 5건(M27)도 이미 사람의 의미 승인이 없으므로 **총 12건 변경 경고는 여전히 검토 대기**입니다.

## 3. 프로그램 및 검증 산출물

- `scripts/audit_m28_hrd_foreign_official_sources.py`: 공식 모니터 ID·정확한 HTTPS 호스트·다국가/타국 분류 확인 후 독립 원문 GET, 원문 SHA 대조, 불명확한 원문은 미확인 처리. **16개 악의적 입력/승인 상태 검증 모두 차단**.
- `scripts/test_m28_foreign_source_guard.js`: 실제 앱 출처 경고 함수로 HRD 두 건/외국 5건의 **7개 pending 상태**와 잘못된 모니터 5개 상태 검사.
- `research/source_reviews/indonesia_m28_hrd_foreign_source_recheck_2026-10-17.json`: 수집 결과, 구분, 기존/새 SHA-256, TLS 방식, 인적 승인 미완료를 적은 append-only 원본 증거. 추후 원문이 달라져도 이 기록에 덮어쓰지 않음.

## 4. 다음의 실제 책임자 판단

- [ ] 스리랑카 SLBFE 사이트의 실제 공고/정책 변경 여부, 적용 부문·효력일을 원문 비교로 확인한 후 담당자가 서명.
- [ ] HRD Korea 다국가 공고의 인도네시아 적용 가능성을 개별 공고·일정·국가별로 확인하며 **URL 변경 경고를 삭제하지 않음**.
- [ ] 다른 외국 4건도 국가 담당자가 추후 실제 의미 검토. 동일 SHA는 자동 의미 승인 조건이 아님.
- [ ] 2026년 인도네시아 일반 제조업 **최종 온라인 구직등록 서류 원문** 확보 전까지 `job_docs` 계속 HOLD.
- [ ] 위 원문을 토대로 책임자가 실제 출시일 기준 검토·서명한 후, 승인된 후보 배포 9/9 자산 및 6/6 HTTPS 검사, 별도 베타 공개 승인.

**유지 상태:** `humanSemanticReviewApproved=false`, `sourceHashAutoAccepted=false`, `job_docs=hold`, `betaAccess=hold`, **Draft PR 미병합·미배포**.
