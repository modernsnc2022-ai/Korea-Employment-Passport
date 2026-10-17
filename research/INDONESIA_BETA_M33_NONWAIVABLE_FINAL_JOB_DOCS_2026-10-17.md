# KEP M33 — 최종 제조업 구직서류 미확정 시 출시 준비 차단

**검사 날짜:** 2026-10-17 / **상태:** 안전 검증 완료, 출시 미승인.

## 실제 발견한 문제

기존 `report_indonesia_beta_release_preflight.py`는 KP2MI 2026 제조업 공고의 사람 검토 결과가 "최종 구직등록 공고 없음"으로 서명돼도 해당 게이트를 PASS로 인정할 수 있었습니다. 다른 소스 서명·배포 검증이 모두 PASS인 가상 상황에서는 `readyForManualLaunchDecision=True`가 될 수 있었으며, 이것은 "2026 최종 구직등록 필수서류 실제 공식 근거 확보"라는 제품 출시 원칙에 어긋납니다.

## M33 안전 조치

1. 새 필수 게이트 `exact_2026_manufacturing_final_job_documents`를 추가했습니다. 출처 목록을 사람이 검토했더라도 2026 일반 제조업 최종 온라인 제출서류 원문과 첨부 자료를 확보하지 않았으면 **PENDING**입니다.
2. 기존 `required_ids`에 이 게이트를 포함했으며, 필수 게이트의 누락·중복·비PASS 상태가 있으면 준비 판정을 거부하는 `required_gates_all_pass`를 구현했습니다.
3. 시험용 가상 원문 승인·동일 HEAD 배포(9/9 핵심 파일·6/6 HTTPS)가 모두 통과하더라도 최종 서류가 HOLD이면 `readyForManualLaunchDecision=False`인 것을 테스트했습니다.
4. 이 게이트를 해제하는 절차는 자동 승인되지 않으며, 추후 해당 모집 주기 공식 원문·PDF를 사람이 실제 검토하고 별도 명시적 안전 코드 변경·시험·배포 승인 과정을 거쳐야 합니다.

## 실서비스에서 읽기 전용 재검증

`python scripts/report_indonesia_beta_release_preflight.py --as-of 2026-10-17 --live --json`을 실제 실행했습니다.

- 10개 명시적 검사 게이트: **5 PASS / 5 PENDING**.
- 공개 서비스 기존 `main/docs` 핵심 자산 검증 PASS, 신규 Draft HEAD의 동일 SHA 배포는 PENDING.
- 현재 관측된 공식 출처 84/84 기술 수집 PASS, SHA 변경 경고 12건은 실명 서명 미완료.
- **2026 제조업 최종 구직등록 서류 PENDING** / 실제 공개 베타 HOLD.
- `readyForManualLaunchDecision=False`, `authorizesRelease=False`.
- 현재 출처의 기술 점검 결과는 정책·의료·노동법의 책임자 승인으로 해석하면 안 됩니다.

증거 파일: `research/source_reviews/indonesia_m33_exact_final_job_docs_preflight_2026-10-17.json`. 원본 자료나 GitHub 설정, 베타 OPEN 상태는 수정하지 않았습니다.

## 운영자 다음 단계

실제 2026 제조업 최종 Skill Test 합격 공고와 구직등록 제출서류 원문·정확한 부속 PDF를 확인하고, 분야·연도·필수 파일·제출기한 및 관할 기관을 사람 검토자가 서명해야 합니다. 동시에 12개 변경 출처의 뜻을 점검하고, 추후 별도 승인으로 새 후보를 배포한 뒤 동일 SHA 9/9 및 HTTPS 6/6 재검증해야 합니다. 그 다음 실제 공개 베타 OPEN을 별도로 결정해야 합니다.

**기존 관심 신청자 접수 OPEN / 공개 서비스 베타 접근 HOLD / 최종 제출서류 HOLD / Draft PR 미병합·미배포.**
