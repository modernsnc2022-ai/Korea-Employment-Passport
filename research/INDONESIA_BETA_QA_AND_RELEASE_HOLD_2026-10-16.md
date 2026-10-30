# Korea Employment Passport — Indonesia Beta Product QA / Release HOLD

**검증일:** 2026-10-16 (KST)
**검증 Git HEAD:** `4e2c09a06345c1fe1ab844036a38fe0f4f8471fb`
**범위:** Indonesia → E-9 → General Manufacturing 2026
**보고서 성격:** 읽기 전용 QA 증거. 승인·규칙 갱신·서비스 배포·베타 OPEN 권한 없음.

## 1. 기술 검증 결과

| 항목 | 실행 명령 / 조건 | 결과 |
|---|---|---|
| 제품 정적 출시 점검 (공식자료 승인 분리) | `python scripts/check_beta_launch_readiness.py --allow-source-review-pending` | **PASS** — 27단계, BQC 256, exact job hold 1 |
| 신청 D1 로직 | `python scripts/check_beta_intake_backend.py` | **PASS** — atomic dedup, retention, default disabled |
| 이메일 OTP 검증기 | `python scripts/check_beta_email_verifier.py` | **PASS** — local SQLite, use-once, rate limit |
| 웹앱 계약 검증 | `python scripts/check_webapp_contract.py` | **PASS** — 9 views, 27 stages, 113 fields |
| 16개 Country Pack 계약 | `python scripts/check_country_pack_contract.py` | **PASS** — Indonesia 외 15개국 research HOLD |
| Edge 베타 신청 UI | Playwright 1.55.0, `KEP_TEST_PORT=42873`, `playwright test beta-intake` | **17/17 PASS** |
| Edge 전체 UI | Playwright 1.55.0, `CI=1`, `KEP_TEST_PORT=42874`, `playwright test` | **96/96 PASS** (3.4분, 1 worker) |
| 출시 판정기 자체 회귀 검증 | `python scripts/report_indonesia_beta_release_preflight.py --self-test` | **PASS** |

Edge UI는 PC의 로컬 HTTP 서버와 모의 신청·이메일 인증 API를 사용했다. 실제 지원자 신청·이메일 전송·실제 Cloudflare 등록은 수행하지 않았다. 17개의 신청 UI 테스트는 96개 전체 스위트에도 포함되므로 합산해 113개 독립 사례라고 보고하면 안 된다.

## 2. 실제 출시 판정 — 2026-10-16

실행: `python scripts/report_indonesia_beta_release_preflight.py --as-of 2026-10-16`

| 출시 게이트 ID | 판정 | 근거 및 다음 확인 |
|---|---|---|
| route_safety | PASS | 27단계·Skill Test·최종 `job_docs` 정확한 HOLD 유지 |
| country_source_classification | PASS (과거 자료 분류만) | 기록된 과거 값 83/84, 3 Korea-common + 5 other-country, `np_eps_notice_index` fetch failure. **당일 유효 자료 아님.** |
| official_monitor_today | **BLOCKED** | 기존 snapshot / Indonesia sourceScope = 2026-10-14. 2026-10-15 별도 관측도 2026-10-16의 당일 승인으로 재사용 불가 |
| indonesia_source_manual_signoff | **PENDING** | 이름·시각·실제 검토 내용을 갖춘 인도네시아 범위 담당자 승인 필요 |
| kp2mi_manufacturing_release_day_signoff | **PENDING** | KP2MI Pengumuman 2026 제조업 일반 분야 공고 및 첨부물의 담당자 전체 목록 검토 필요. 이전 2026-10-14 기록만 존재 |
| optional_skill_annex_evidence | PASS | PDF annex 6개 / 선택 제출 범위만 확인. 최종 제조업 `job_docs` 근거로 자동 승격 금지 |
| same_head_pages_deployment | **PENDING** | 동일 승인 Git HEAD의 실제 Cloudflare Pages HTTPS 9/9 assets + 6/6 redirects 검증 필요 |
| explicit_manual_beta_open | **PENDING** | `betaAccess=hold`, `publicBeta=pending_manual_approval`; 웹 메일 기반 사전 관심 등록 경로의 `intake=open`은 베타 OPEN 승인과 구분 |

**READY_FOR_MANUAL_DECISION = False; LIVE_DEPLOYMENT_VERIFIED = False; authorizesRelease = False.**

## 3. 우선순위 작업

1. 사용자·담당자의 실제 공식자료 검토: KP2MI Pengumuman 인도네시아 **General Manufacturing**의 대상 공고와 첨부 PDF 확인. 직접 식별 불가한 최종 `job_docs`는 HOLD 유지.
2. 같은 날 실제 공식 84-source 관측과 인도네시아 국가 범위 변경 검토. 2026-10-15 4 Korea-common + 1 multi-country HRD + 5 other-country 기록은 과거 관측일 뿐 자동 승인 아님. 기타 국가의 pending alert는 보존.
3. 본문·원문 SHA·공식 출처·담당자·현지 시간대를 갖춘 실제 담당자 서명. 합성 QA 서명이나 자동 SHA 승격 금지.
4. 승인된 코드 HEAD의 Pages 배포가 이루어진 뒤 독립적 실시간 read-only asset parity 검사 및 테스트. 배포 자체는 이번 QA에서 하지 않음.
5. 모든 기술·공식자료 게이트가 충족됐을 때만 별도 명시적 수동 beta OPEN 결정. 현재는 반드시 HOLD.

## 4. 범위 및 해석 제한

- 이번 테스트는 **기술·브라우저 결함을 발견하지 못한 현 시점의 검증**이다. 실제 외부 사용자 30명 + 한국 근무자 20명의 검증, 27단계 broker replacement, 실서비스 이메일 전달성, Cloudflare 실제 CPU/D1/Cron 비용 또는 원문 공고 승인까지 완료됐다는 뜻은 아니다.
- 기존 Draft PR #324는 미병합 상태로 유지한다. 고객·신청자 데이터, KEP Beta 공개 설정, official source hash 승인 기록은 수정하지 않는다.
- 실제 서비스 사용 가능 여부의 최종 판단에는 원문 사실 검증·담당자 승인·배포 증거가 모두 필요하다.
