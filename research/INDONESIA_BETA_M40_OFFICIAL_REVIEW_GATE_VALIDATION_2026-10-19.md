# KEP M40 — 공식 공고·담당자 심사 연결 회귀검사

**기준 자료:** 2026-10-18에 수집한 KP2MI / HRD Korea, M21 공식 HTML 원문, M34의 미서명 검토 업무, M39 출시 판정. **실제 테스트 실행:** 2026-10-19.

- KP2MI 공식 제목 320건 중 2026 일반 제조업 관련 7건. 각 원문의 URL·게시일을 M34의 사람 검토 지시서 7건에 일대일 연결.
- HRD Korea의 인도네시아 제조업 시험 일정 Jakarta / Semarang 2건을 별도 일정 증거로 연결.
- `verify_m40_oct18_human_notice_handoff.py --check --self-test`를 PC에서 실행하여 원문 결속 PASS, 허위 승인 등 13개 변조 차단 PASS.
- M40 독립 출시 게이트 `kp2mi_current_notice_index_observed` 추가. `report_indonesia_beta_release_preflight.py --self-test` PASS.
- `--as-of 2026-10-18` 비실시간 회귀검사에서 신규 공고 관측 게이트 PASS. **11개 게이트 5 PASS/6 PENDING(비실시간 기본 검사 기준)**; `readyForManualLaunchDecision=False` 및 `authorizesRelease=False`.
- **2026-10-19 새로운 출시일**에는 10/18 M40 자료를 재사용할 수 없으므로 공고 관측 게이트는 PENDING이고 공식 84건 감시 역시 별도 오늘 유효 관측 전까지 BLOCKED. 출시 판단 미완료.
- 2026-10-19 KP2MI 공고 인덱스 별도 live GET: 320건, 일반 제조업 관련 기존 7건, 해당 최종 구직등록 제목 후보 0건; 제목 URL 지문 `4d67a65b8af983e6567fbc3b55374e30fa10c095954aafbbc8bb15100471a4e6` 동일. 이는 320건 제목 확인 범위에 한하며 부속 PDF의 존재/부재를 증명하지 않음.

**결론:** 정부 공식자료 자체의 의미 검토는 사람의 실명·원문·첨부 페이지 판단 필요. 기존 20개 검토 업무는 미서명, 현재 2026 제조업 최종 온라인 제출서류 확정 없음, Draft PR 병합·배포 없음. 관심 등록 OPEN / 공개 베타 접근 HOLD.

**운영자 다음 작업:** 10월 19일 공식 자료 84개 당일 관측과 별도 M40 사전검사 게이트의 당일 증거 연결, 실제 제조업 최종 구직등록 공고 출현 여부 확인, 담당자 승인·서류 확정·배포·베타 OPEN 개별 진행.
