# KEP M31 — 2025/2026 제조업 최종합격·구직등록 공고의 모집 주기 격리

**확인 기준:** 2026-10-17 WIB/KST. **역할:** 2026 인도네시아 E-9 일반 제조업 베타의 출처·서류 안전 검증. 사람의 공식자료 의미 승인 아님.

## 1. 공식 공고 현황 — 실제 검사

KP2MI 공식 [G-to-G Korea Pengumuman](https://kp2mi.go.id/gtog-korea/pengumuman) 목록을 2026-10-17에 직접 재조회했습니다. 총 320개 공고 제목을 검사했고, 2025년 구간까지 도달했습니다. 2026 일반 제조업 관련 제목 7건, 최종 구직신청을 명시한 일반 제조업 제목 0건, 타 모집 분야 온라인 구직신청 제목 3건이 확인됐습니다. 정규화 목록 SHA-256은 M24/M30 값 `4d67a65b8af983e6567fbc3b55374e30fa10c095954aafbbc8bb15100471a4e6`과 동일합니다. **제목 증거에 한정되며 전체 부속 PDF 확인/제출서류 확정이 아닙니다.**

## 2. 서로 다른 연도의 원문은 결코 같은 제출서류 규칙이 아니다

| 시점 / 공고 | 공식 원문 | 실제 문서가 말하는 범위 | 2026 최종 제출서류로 사용 |
|---|---|---|---|
| 2025-11-28 제조업 최종합격 | [2025 최종합격 원문](https://kp2mi.go.id/gtog-detail/korea/pengumuman-hasil-akhir-kelulusan-eps-topik-ubt-umum-sektor-manufaktur-program-g-to-g-ke-korea-selatan-tahun-2025) | 2025 최종 합격, 전자합격증과 온라인 신청 방법·서류는 추후 안내 | **금지** |
| 2025-12-05 전자합격증·온라인 신청 | [2025 구직등록 원문](https://kp2mi.go.id/gtog-detail/korea/pengumuman-pembagian-sertifikat-kelulusan-digital-e-sertifikat-ujian-eps-topik-ubt-umum-sektor-manufaktur-dan-pengajuan-lamaran-online-calon-pekerja-migran-indonesia-program-g-to-g-korea-tahun-2025) | 2025 전자합격증 다운로드 및 12월 10일 온라인 접수, 2025 MCU·학력증빙·연락처 및 스캔 방식 등 | **금지** |
| 2026-01-27 EPS-TOPIK 최초 시험등록 | [2026 최초 등록 공고](https://kp2mi.go.id/gtog-detail/korea/pengumuman-pendaftaran-ubt-umum-sektor-perikanan-dan-sektor-manufaktur-progam-g-to-g-ke-korea-selatan-dengan-sistem-poin-tahun-2026) | 2026 최초 EPS-TOPIK 응시 등록 및 MCU·HIMPSI의 온라인 구직신청 관련 예고 | **이 공고만으로 확정 금지** |
| 2026-09-10 EPS-TOPIK 1단계 결과 | [2026 제조업 1차 합격 원문](https://kp2mi.go.id/gtog-detail/korea/pengumuman-hasil-ujian-kemampuan-bahasa-korea-eps-topik-ubt-umum-sektor-manufaktur-tahun-2026) | EPS-TOPIK 2026 1단계 합격자 2,020명; Skill Test **필수**, 선택적 Job Capacity Assessment | **최종 합격 아님** |

2025년 12월 5일 원문에는 해당 연도의 필수 서류·의료검진과 12월 10일 접수 시작일이 실제로 쓰여 있습니다. 그러나 **이 정보의 모집 주기는 2025년**이며, 2026년 일반 제조업 제출자료나 2026년 접수 개시일로 사용할 수 없습니다. 2026년 1월 최초 시험 등록 자료에 나오는 KTP·여권·사진·학력서류도 전부 최종 구직등록 서류 목록으로 바꿔서는 안 됩니다.

## 3. 소프트웨어 실검증

- `scripts/test_m31_historical_job_docs_cohort_guard.js`: 제품 후보의 `docs/data/id_e9_manufacturing_2026.json`와 `docs/data/document_packs_2026.json`를 직접 검사. `job_application=held_official_notice`, 문서팩 `awaiting_sector_notice`, `items=[]` 유지. 2025년 구직등록 공식 링크가 2026 문서팩에 사용되지 않으며, 잘못된 승인·연도·필수서류·베타 전환의 **12개 위험 변조 사례 차단**.
- `scripts/audit_m31_official_2025_2026_lineage.py`: 2025년 최종합격·구직신청과 2026년 시험등록·1단계 결과를 별도 연도로 검증하는 **원문 수집 준비용** 스크립트. 검증된 공식 출처 외 리다이렉션 금지, 네 문서 모두 정책 자동 승인 금지. **13개 위험 변조 사례 SELF-TEST PASS**. 이번 턴에서 이 스크립트의 별도 HTTPS GET 실행은 연결 안전검사에서 차단돼, JSON 신규 4건의 원문 SHA 비교를 완료했다고 주장하지 않습니다.
- 기존 M29은 2026 제조업 공고 HTML 7/7 직접 재조회 및 M21 SHA 일치를 이미 확인했고, M30은 최신 공식 목록의 일반 제조업 최종 구직등록 공고 제목 0건을 다시 관측했습니다.

## 4. 담당자 수동 확인 전까지 반드시 차단

- 2026년 **최종 Skill Test 합격 발표**, **전자합격증 발급**, **해당 모집 분야 최종 온라인 구직등록**의 정확한 원문·첨부 문서·일시·적용 대상은 별도 확인 필요.
- 2025년 서류, 다른 2026 모집 분야(Root Industry/어업/특별시험)의 제출서류, 2026 EPS-TOPIK 최초 시험등록 서류를 임의로 가져오지 말 것.
- 공식 원문 검토 책임자의 실명 서명 및 12건 출처 변경 경고 판단 전에는 원천 데이터 해시 변경이나 규칙 승인 금지.
- 별도 승인된 후보 배포와 HEAD 일치(9/9 자산)·HTTPS(6/6 전환) 검증 이후에만 **별도의** 공개 베타 승인 절차를 진행.

**현재 상태:** 신청자 관심 등록 OPEN / 공개 베타 접근 HOLD / 제조업 최종 `job_docs` HOLD / 공식자료 수동 서명 PENDING / Draft PR 미병합·미배포.
