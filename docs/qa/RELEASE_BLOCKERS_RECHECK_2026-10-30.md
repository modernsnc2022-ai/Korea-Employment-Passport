# KEP 잔여 출시 차단 항목 — 2026-10-30 재검증

## 실제 실행
- 검사 대상: `ux/indonesian-ui-copy-20261030`
- `python scripts/check_beta_launch_readiness.py --allow-source-review-pending`: PASS, 27 stages / 256 questions / 8 forms / 113 fields, official sources 83/84 checked.
- `python scripts/test_release_copy_contract.py`: 5 tests PASS (Windows UTF-8 명시 수정 후).
- 해당 성공은 출처 최신성 승인 또는 beta OPEN을 뜻하지 않는다.
- STRICT 검사를 우회해 베타를 열지 말 것.

## 최우선 공식 출처 검토 필요 — 8개
1. https://law.go.kr/LSW/lsLinkCommonInfo.do?lsJoLnkSeq=1027161979
2. https://qcode.kdca.go.kr/qco/cd/codeInput2.do
3. https://1350.moel.go.kr/home/hp/ch/callchat.do
4. https://epsnepal.gov.np/notices — 지난 모니터 기록 HTTP 500 / fetch failure.
5. https://colab.moha.gov.vn/tin-tucs/357/Chuong-trinh-EPS.aspx
6. https://www.slbfe.lk/
7. https://migrant.kg/
8. https://www.mol.gov.mm/mol-department-of-labour/

위 목록은 소스 모니터의 **2026-10-14 기록**에 기초한다. 오늘 URL 접근 성공/실패를 재검증한 결과가 아니다. 84개 중 83개 확인 수치도 현재 리포지토리에 저장된 자동 점검 상태이며, 실시간 상태가 아니다.

## release gate
- 공식 기관 최신 원문 재조회, 변경 전후 비교, 해당 국가·회차 적용 범위 검증 및 사람 승인.
- Indonesia Manufacturing E-9 2026 Skill Test 이후 최종 제출서류 공고 확인 전 exact HOLD 유지. 타 회차나 산업 공고로 대체 금지.
- 공식 출처 검토와 fetch failure를 해결하기 전 strict release PASS 불가.
- 최신 PR head에서 전체 Playwright, static, 사전 검증, 모바일 실기기·스크린리더 확인.
- 동일 후보 staging·HTTPS·자산 확인, 디자인 승인, 단계별 PR 병합 및 롤백 계획.
- beta interest 신청 접수와 서비스 beta OPEN은 별도.

## 재현
```sh
python scripts/test_release_copy_contract.py
python scripts/check_beta_launch_readiness.py --allow-source-review-pending
python scripts/check_beta_launch_readiness.py
```
마지막 strict 명령은 공식 검토를 완료하기 전 FAIL이 정상이다.

## 이번 수정
- Windows 기본 locale이 cp949일 때 출시 안내문 테스트가 UnicodeDecodeError로 실패하던 부분을 명시적 UTF-8로 수정.
- 안전성 검사를 우회하거나 출처를 'clean'으로 위조하지 않음.
