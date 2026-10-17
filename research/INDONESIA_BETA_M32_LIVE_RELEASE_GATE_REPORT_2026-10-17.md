# KEP M32 — 출시 차단 8개 게이트: 실제 Pages/HTTPS 확인 결과

**실측일:** 2026-10-17 KST / Asia-Jakarta. **프로젝트:** Korea Employment Passport (KEP), Indonesia E-9 General Manufacturing 2026.

**유형:** 원본 GitHub 및 공개 HTTPS URL 읽기 전용 확인. **최종 사람의 승인이나 실제 배포 명령은 아님.**

## 1. 동일 코드 버전 출시에 대한 실측

GitHub Pages 실제 설정은 **`main/docs`**이고, GitHub 저장소 `origin/main`을 직접 확인한 뒤 외부 도메인 `https://www.gdglobal.kr/Korea-Employment-Passport/`에서 제공되는 핵심 파일 9개를 GET하여 실제 Git blob과 비교했습니다.

| 점검 | 관측 결과 | 의미 |
|---|---:|---|
| 배포 소스 계정·브랜치·경로 | GitHub Pages `main/docs` | 출처 확인 |
| 외부 공개 핵심 파일 vs 배포 `main` | **9/9** | 기존 공개 배포본 무결성 PASS |
| 외부 공개 핵심 파일 vs 당시 Draft PR HEAD | **0/9** | 새 M31 후보는 아직 서비스 중이 아님 |
| 6개 예전 진입 URL의 첫 리다이렉션 | **6/6 HTTPS** | 다운그레이드나 캠페인 코드 소실 관측되지 않음 |
| 공개 베타 접근 | **HOLD** | 관심등록 OPEN과 실제 로그인·사용 허용은 구분 |

해당 실측에서는 현재 후보의 커밋 `726cb119ad69a2ef9e7f303ae0c9c63ca73dfb63`을 기준으로 검사했습니다. M32의 검증기/보고서는 이후 Draft PR에만 추가되므로, 새 M32 HEAD 배포 무결성이 검증됐다는 의미는 아닙니다.

**주의:** 정상 배포된 기존 9개 자산과 HTTPS 6개 경로는 **이전 안정판의 상태**입니다. 새 후보의 실제 사용 가능성을 승인하는 증거가 아닙니다. 검증 스크립트는 Pages 설정을 수정하거나 파일을 배포하지 않았습니다.

## 2. 현재 출시 차단 원인

| 게이트 | 상태 | 구체적인 다음 조치 |
|---|---|---|
| 2026 일반 제조업 앱 경로·제출서류 안전 | PASS | 27단계 경로와 현재 `job_docs=held_official_notice` 유지 |
| 84개 공식자료 읽기 전용 수집 | PASS | 동일 날짜 관측 84/84, 지문 변동 12건 승인 없이 유지 |
| **공식자료 담당자 의미 검토** | **PENDING** | 검토 대기표 20개 항목, 특히 한국 공통 5건과 HRD 2건·타국 5건 검토. 실제 이름·확인 시각·원문 근거 필요 |
| **2026 제조업 최종 구직등록 서류** | **PENDING** | 해당 2026년 후속 공고·정확한 첨부 PDF·필수/선택 제출서류·기한을 원문으로 검증. 다른 모집 주기 금지 |
| 공개 `main/docs` 소스 무결성 | PASS | 구 공개본 9/9 정상. 배포까지 완료했다는 뜻은 아님 |
| **승인된 후보와 같은 HEAD의 실제 배포** | **PENDING** | 별도 승인 받은 뒤에만 배포. 그 후 동일 SHA 자산 9/9·HTTPS 경로 6/6 재검증 |
| 기존 URL HTTPS 첫 리다이렉션 | PASS | 읽기 전용 6/6 안전 |
| **별도 운영자 공개 베타 OPEN 승인** | **PENDING** | 사람의 정책 검토, 정확한 2026 서류, 승인된 배포 증거를 모두 갖춘 다음 별도 결정 |

**결과: 4 PASS / 4 PENDING.** 특히 **책임자 원문 심사(서명 없음)**, **최종 제조업 서류**, **같은 HEAD 배포 증거**, **수동 공개 베타 승인**이 직접적인 미완료 항목입니다.

## 3. 검증 가능 코드 및 증거

- `scripts/audit_m32_live_release_blockers.py`: GitHub Pages API 설정, 공개 `main/docs` 소스 9개, 현재 Draft HEAD 9개, 실제 HTTPS 리다이렉션 6개를 원본 코드와 함께 읽기 전용 검사. 스스로 승인·배포하는 기능 없음.
- `research/source_reviews/indonesia_m32_pages_release_blockers_2026-10-17.json`: 날짜·커밋·실측 카운트·8개 게이트의 증거·각 미해결 항목을 고정한 기록.
- 잘못된 베타 승인, 2026 최종 서류 임의 검증, 다른 SHA 자동 승인, 배포 소스 분기 변경 등 **16개 공격적인 상태 변조를 모두 차단**.
- 원래의 출시 사전검사 `report_indonesia_beta_release_preflight.py --as-of 2026-10-17 --live`도 실제 실행해 공개 원본 `published_main_source_integrity=PASS`, `same_head_pages_deployment=PENDING`, `releaseAuthorized=FALSE`를 확인했습니다.

## 4. 유지해야 할 원칙

- 오래된 2025년 최종 온라인 구직등록 자료, 2026년 최초 시험접수 자료, Skill Test 선택적 서류, 다른 분야의 공고는 2026년 일반 제조업 최종 구직등록 제출서류로 유용하지 않습니다.
- 정규화된 웹페이지 SHA-256 일치는 기술적 내용 유지의 증거일 뿐, 한국의 법령·검역 또는 각국 EPS 정책에 대한 책임자 승인이 아닙니다.
- 신규 원문이 없으면 구직등록 단계는 `HOLD`이고, 수동 승인 없이 해시값을 갱신하지 않습니다.
- 기존 Draft PR #324는 OPEN/DRAFT 상태로 보존하며 강제 배포·병합·GitHub Actions 사용은 하지 않습니다.

**베타 관심 신청서 접수: OPEN / 실제 공개 베타 접근: HOLD / 공식자료 의미 검토: PENDING / 2026 제조업 최종 서류: HOLD.**
