# KEP M27 — 한국 공통 공식 출처 5건과 인도네시아어 앱 안내 대조

**검사일:** 2026-10-17 (WIB/KST)

**대상:** 한국 공통 출처 5개 + 실서비스 후보 앱의 연결된 정확한 답변 6개 + MOEL 1350 지원 채널

**결론:** 공식 HTML 원문 재수집 5/5, M21 10월 17일 정규화 원문 SHA-256 일치 5/5, 앱 출처 연결 5/5 검토 대기 유지. **사람의 의미·적용 법령·출시 승인 없음.**

## 1. 독립 검증 결과

| 출처 | 공식 원문 및 기계 대조 결과 | 앱 안내와의 관계 | 필수 사람 검토 |
|---|---|---|---|
| 최저임금위원회 | [2026년 10,320원/시간, 주 40시간·유급주휴 포함 월 2,156,880원](https://www.minimumwage.go.kr/index.jsp); 오늘 재수집 SHA M21과 일치 | `minimum_wage_2026` 출처를 이번에 최저임금위원회 공식 주소로 일치시킴. 209시간 환산을 모든 개인의 고정 월급이라고 안내하지 않음 | 해당 연도의 지급 기준과 급여명세·소정근로시간 관련 설명 |
| 근로기준법 제48조 제2항 | [임금명세서의 구성항목, 계산방법, 공제내역](https://law.go.kr/LSW/lsLinkCommonInfo.do?lsJoLnkSeq=1027161979); 오늘 SHA 일치 | `payslip_required_items`, `pay_compare_slc_to_statement_components`에 출처 연결 | 법령 사이트의 개정·시행일과 현행 조문 범위. 브라우저/검색 인덱스의 법령 시행일 표기 차이는 사람 확인 필요 |
| 고용노동부 1350 임금체불 상담 답변 | [임금체불 시 관할 지방노동관서 진정·온라인 민원](https://1350.moel.go.kr/rtmview.do?id=1000317748); SHA 일치 | `labor_unpaid_wage_first_action_current`에 출처 연결 | 개별 상담 답변을 모든 사건에 동일하게 적용하지 말고 사안별 최신 절차 확인 |
| KDCA Q-CODE | [옛 입력 주소](https://qcode.kdca.go.kr/qco/cd/codeInput2.do) → [KDCA Travel Health 안내](https://travelhealth.kdca.go.kr/travel/cd/qcoInfo.do); 공식 HTML SHA 일치 | `departure_qcode_current_official`이 새 주소를 사용. 앱의 `sourceNeedsReview` URL 정규화가 옛 URL과 새 URL을 동일 변경 경고로 연결. Q-CODE는 모든 E-9 입국자에게 보편적으로 의무인 것으로 안내하지 않음 | 여행 시점의 검역관리 지역, 증상 및 KDCA 기준·입국자별 호출 안내 |
| MOEL 1350 상담 연락처 | [1350 유료, 평일 09:00~18:00 KST](https://1350.moel.go.kr/home/hp/ch/callchat.do); SHA 일치 | `labor_1350_scope_current` 출처 연결, `official_help_channels_v1.json`에 유료 통화·한국시간·모바일/채팅 상담시간과의 차이 명시 | 전화상담 언어지원·해외 연결 가능 여부를 보장하지 않음. 모바일상담은 전화와 시간이 다를 수 있음 |

## 2. M27 소프트웨어 변경

- `docs/app-runtime.js` — KDCA 옛 공식 Q-CODE 입력 URL과 새 Travel Health URL을 **동일한 미승인 출처 경고**로 비교. 검증되지 않은 URL 리다이렉션은 일반적으로 허용하지 않고, M21에 실제 수집된 정확한 공식 주소 한 쌍만 연결.
- `docs/data/exact_answer_rules_v1.json` — `minimum_wage_2026`의 원문 출처를 실제 2026년 시급·환산 월급을 고시하는 최저임금위원회 홈으로 변경. 기존 인도네시아어 209시간 조건은 유지하며 내용 자동 수정·승인은 하지 않음.
- `docs/data/official_help_channels_v1.json` — MOEL 1350을 **유료 전화·평일 09:00~18:00 한국시간**으로 명시하고 모바일/채팅의 별도 시간 가능성을 경고.
- `docs/sw.js` — 배포 전 캐시 버전 `kep-v140` 준비. 이는 실제 Pages/Cloudflare 배포가 아님.
- `scripts/test_m27_korea_official_claim_guard.js` — 실제 앱 URL 판정 함수와 데이터 로딩, 옛/새 Q-CODE 두 주소, 최저임금·근로기준법·임금체불·1350의 변경 경고, 부정확한 출처 관측 다섯 경우의 fail-closed 시험.
- `scripts/audit_m27_korea_official_claims.py` — 5개 한국 공식 HTTPS HTML 원문을 실제 GET으로 별도 확인하고 기존 M21 원문 지문과 대조. 매 실행의 검증 결과는 append-only JSON 증거로 저장.
- `research/source_reviews/indonesia_m27_korea_common_claim_audit_2026-10-17.json` — 실제 5건 GET 결과와 SHA-256 일치, 앱의 연결 대상, 사람의 판단 미완료 기록.

## 3. 승인·출시와 관계

HTML SHA 일치는 원문의 정규화 텍스트가 이전에 수집한 값과 같다는 **기계적 사실**입니다. 출처의 실제 법적 의미·시행일·개별 근로자 적용 가능성에 대한 **책임자의 최종 판단이 아닙니다**. M26 검토 대기표에서 한국 공통 항목 5건은 계속 PENDING입니다. HRD 다국가 2건, 기타 국가 5건도 미승인 상태입니다.

**2026년 일반 제조업 최종 온라인 구직등록 제출서류 목록 `job_docs=HOLD`; 공개 베타 `betaAccess=HOLD`; 승인 SHA 자동 승격 금지; Draft PR 미병합; 출시당일 최종 확인·실제 사람 서명 필요.**
