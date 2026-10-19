# KEP M36 — 2026 제조업 공식 PDF 원문·단계 경계 검증

**기준:** 2026-10-17 (Asia/Jakarta). **범위:** KP2MI 2026년 9월 10일 제조업 1단계 합격 및 9월 17일 선택적 Job Capacity Assessment / Skill Test 증빙 공고의 첨부파일.

## 1. 공식 원문 확인 — 개인정보와 서류 목록 혼동 방지

| 공식 공고 | 연결 PDF | 기존 M23 원문 바이트 확인 | 이번 M36 원본 PDF 직접 GET | 절차 범위 |
|---|---:|---:|---:|---|
| [9월 10일 EPS-TOPIK UBT Umum 제조업 1차 합격](https://kp2mi.go.id/gtog-detail/korea/pengumuman-hasil-ujian-kemampuan-bahasa-korea-eps-topik-ubt-umum-sektor-manufaktur-tahun-2026) | 1 | 0 | **1/1 성공, 39페이지** | **최종 합격 아님**: 합격자 Skill Test 참가 필수. 합격자 명단을 최종 구직등록 파일로 전용 금지 |
| [9월 17일 제조업 선택적 역량증빙 제출 안내](https://kp2mi.go.id/gtog-detail/korea/pengumuman-persyaratan-unggah-dokumen-kompetensi-peserta-skill-test-ubt-umum-sektor-manufaktur-eps-topik-tahun-2026) | 6 | 4 | **1 성공(1페이지) / 1 시간초과 / 기존 4건 재다운로드 생략** | Job Capacity Assessment를 선택해 자격증·경력을 제출하는 경우의 첨부. 최종 구직등록 제출파일 목록이 아님 |

**신규 원본 GET 검증 성공 2/3, 미확인 1/3.** 성공한 파일은 `%PDF-` 헤더 확인, 전체 바이트 SHA-256 계산, PDF 페이지 열기, 첫 페이지 로컬 임시 이미지 렌더링을 실시했습니다. 실패한 PDF는 `inconclusive_timeout_or_network`로 저장했으며, 정상·누락·정책 변경 중 어느 것도 확정하지 않았습니다.

- 9월 10일 합격자 명단: `data_10-09-2026_Daftar_CPMI_yang_Lulus_Ujian_EPS_TOPIK_UBT_Umum_Sektor_Manufaktur_Tahun_2026.pdf`; 39페이지, **개인 이름·응시번호·페이지 본문·스크린샷을 GitHub에 저장하지 않음**.
- 9월 17일 경력 사실 확인 양식: `data_17-09-2026_FORMULIR_SURAT_KONFIRMASI_DASAR_FAKTUAL_PENGALAMAN_KERJA.pdf`; 1페이지.
- 9월 17일 올바른 역량증빙 스캔 예시: `data_17-09-2026_CONTOH_SCAN_DOKUMEN_KOMPTENSI_YANG_BENAR.pdf`; 이번 GET 35초 시간초과로 **미확인**.

이전 M23에서 원문을 이미 연 9월 17일 파일 4건은 다시 받지 않았고, 이전 SHA 출처를 그대로 참조했습니다. M23 원문 증거까지 합하면 7건 중 **6건의 PDF 원본 바이트 확인 기록**이 있고, 한 건은 아직 미확인입니다. 이 건수는 **전문가의 내용·적용 법령 의미 승인 건수와 다릅니다(0)**.

## 2. 기술 검증과 한계

- `scripts/audit_m36_2026_sept_official_pdf_originals.py`: M21 제조업 공고 2개·공식 첨부 URL 7개에 원본 바이트 증거 결속; M23 이미 확인한 4건의 불필요한 재다운로드 차단; 미확인 3건만 HTTP GET; 파일 헤더/용량/페이지/임시 렌더 검사; 15개 거짓 승인·개인정보·URL 변조 검증.
- `research/source_reviews/indonesia_m36_sept_2026_official_pdf_stage_audit_2026-10-17.json`: 7개 PDF의 게시 공고 날짜·절차 단계·이전 SHA 참조·신규 SHA·페이지 수·실패 여부 및 출시 HOLD만 기록. **합격자 이름·응시번호·PDF 본문은 기록하지 않음**.
- 사안별 사람 시각 검사, 모든 첨부 페이지의 전체 의미 검토, 원문 발행 기관의 최신성 판단은 이번 스크립트의 PASS가 아닙니다.
- M35의 구조적 서류 증거 형식 검사에 파일 정보를 넣어 **2026 제조업 최종 서류인 것처럼 처리하지 않음**. 단계가 서로 달라 `job_docs` 제출 승격이 금지됩니다.

## 3. 다음의 검토 우선순위

1. KP2MI 공식 공고 색인에서 **2026 제조업 최종 Skill Test 합격 이후의 실제 최종 온라인 구직등록 공고·첨부**가 발표되는지 확인. 9월 10일 1차 합격 명단이나 9월 17일 선택적 증빙 양식으로 대체 불가.
2. 실패한 9월 17일 스캔 예시 PDF는 별도 시간대 재수집·시각 검토 예정. 이 파일은 최종 제출서류를 확정하는 자료가 아닙니다.
3. 담당자가 실제 원문 링크·모집연도·문서종류·PDF 페이지·날짜를 확인하고, M34 사람 검토 20건과 M33 최종 서류 필수 게이트를 진짜 증거가 생겼을 때만 다시 판정.
4. 별도 배포 승인 후 후보 HEAD 무결성 9/9, HTTPS 6/6, 별도 베타 OPEN 승인.

**최종 상태:** 출처 의미 검토 미승인 / 2026 제조업 최종 구직등록 제출서류 HOLD / 베타 관심 신청 접수 OPEN / 실제 공개 베타 HOLD / Draft PR 미병합·미배포.
