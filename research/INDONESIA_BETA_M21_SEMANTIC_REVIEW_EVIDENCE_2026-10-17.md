# KEP M21 — 2026-10-17 인도네시아 제조업 공식 원문·첨부 링크 의미 검토 보조 증거

**대상:** Indonesia → E-9 → General Manufacturing (UBT Umum) 2026. **등급:** 공개 기관자료에 대한 기술적 재조회와 사람 검토 지원 근거만 포함. **책임자 정책·출시 승인 기록 아님.**

## 1. 당일 실제 재검사

- **2026-10-17 Asia/Jakarta**, M19에서 실제 조회한 2026 KP2MI Pengumuman 목록(185개 제목, 제조업 관련 7개)을 입력으로 사용.
- 한국 공통 출처 **5/5**에서 HTTPS 공식 본문 추출·내용 단서 확인 성공, **추출 텍스트 SHA가 M19 10월 17일 기술 관측값과 정확히 일치**.
- KP2MI 2026 제조업 관련 공고 **7/7 HTML 원문 HTTP 200** 재조회. 공식 `/uploads/gtgkorea/` PDF 첨부 링크 **24개** 수집; 7건의 공고별 첨부 링크 개수는 10월 14일 원문 조사 기록과 동일.
- 링크의 HTTP HEAD 메타데이터 검사: **10/24** 링크가 HTTP 200 `application/pdf`; **14/24** 링크는 Windows `WinError 10054` 연결 재설정으로 응답 확정 불가. **링크가 깨졌다, 파일이 삭제됐다, 파일 내용이 잘못됐다고 판정하지 않는다.** 서버 부하 방지를 위해 무리한 재시도 없음.
- HTML 본문에 `lamaran online`이라는 정확한 표현은 2026-01-27 공고에서 3회 포착, 다른 6개에서는 0회. 3회 출현도 **최종 2026 General Manufacturing post-Skill-Test `job_docs` 목록**임을 증명하지 않는다.

원본 추출 요약(파일 경로):
- `research/source_reviews/indonesia_m21_original_html_audit_2026-10-17.json` — 한국 공통 5개 텍스트 지문과 앵커, KP2MI 7개 HTML 텍스트 지문, 공식 첨부 PDF 링크 24개.
- `research/source_reviews/indonesia_m21_pdf_head_metadata_2026-10-17.json` — 링크별 HTTP HEAD 상태·Content-Type·바이트 길이(있을 경우)·실패 원인. **PDF 내용 다운로드나 페이지별 재검토 기록 아님.**

## 2. 한국 공통 공식자료 5건 — 좁은 범위 사실 확인

| 공식 출처 ID | 원문 링크 | 이번에 확인 가능한 사실 | 판단 경계 |
|---|---|---|---|
| `minimum_wage` | https://www.minimumwage.go.kr/index.jsp | 2026년 법정 최저임금 **시급 10,320원**, 월 환산 **2,156,880원**(주 40시간 + 유급주휴 8시간 기준). 앱 경고도 10,320원 언급. | 개인별 공제·초과근로·실제 최종 급여를 일률 계산하는 근거는 아님 |
| `labor_standards_wage_statement` | https://law.go.kr/LSW/lsLinkCommonInfo.do?lsJoLnkSeq=1027161979 | 근로기준법 제48조 ②: 사용자의 임금 지급 시 임금 구성·계산방법 및 공제 내역 등을 포함하는 임금명세서 서면(전자문서 포함) 교부 의무. | 법령의 모든 개정 의미·개별 사건의 위법성은 별도 심사 |
| `moel_wage_arrears_2026` | https://1350.moel.go.kr/rtmview.do?id=1000317748 | 공식 1350 상담 답변은 임금체불 시 관할 지방노동관서 진정 및 고용노동부 온라인 민원 경로를 안내. | 개별 체불액 확정·보상 가능 금액·지급 시기 보장 안 됨 |
| `kdca_qcode_input` | https://qcode.kdca.go.kr/qco/cd/codeInput2.do | 질병관리청 Q-CODE 공식 입력 서비스; 대상 국가/경유·증상 기준 등 조건 적용. 앱도 모든 E-9 입국자에게 무조건 필수라고 단정하지 않음. | 위험 국가 지정·실제 출국안내·최종 검역 기준은 출발 시점 별도 확인 |
| `moel_1350_contact` | https://1350.moel.go.kr/home/hp/ch/callchat.do | 국번없이 **1350(유료)**, 평일 **09:00–18:00 KST**. 외국인고용허가 관련 상담 범주 존재. 공식 페이지의 외국어 안내에는 **영어·중국어**가 기재됨. | 인도네시아어 상담 제공 또는 전화 연결·상담 처리 성공을 보장하지 않음 |

**공통 분류 5건 전부 2026-10-17 관측 지문에 일치.** 하지만 이것은 최종 승인된 정책/규칙과 비교한 *사람의 공식 의미 승인*을 대체하지 않는다. 기존 SHA 승인기준은 변경하지 않는다.

## 3. KP2MI 공식 2026 제조업 공고 7개

| 공고 날짜 | 원문 | 첨부 PDF 링크 | 의미 검토 포인트 |
|---|---|---:|---|
| 2026-09-17 | [Skill Test 역량증빙 첨부파일 업로드](https://kp2mi.go.id/gtog-detail/korea/pengumuman-persyaratan-unggah-dokumen-kompetensi-peserta-skill-test-ubt-umum-sektor-manufaktur-eps-topik-tahun-2026) | 6 | **Job Capacity Assessment의 선택적 역량증빙**, 접수기간 종료. 필수 Skill Test와 구별. 최종 구직등록 서류 아님 |
| 2026-09-10 | [EPS-TOPIK 1차 시험 결과](https://kp2mi.go.id/gtog-detail/korea/pengumuman-hasil-ujian-kemampuan-bahasa-korea-eps-topik-ubt-umum-sektor-manufaktur-tahun-2026) | 1 | 어학시험 결과는 최종 합격/최종 문서 목록이 아님 |
| 2026-05-05 | [시험 비용 환급 1단계](https://kp2mi.go.id/gtog-detail/korea/pengumuman-pengembalian-biaya-ujian-eps-topik-ubt-umum-sektor-perikanan-dan-sektor-manufaktur-tahun-2026-tahap-pertama) | 2 | 환급 대상/절차 자료로서 구직등록 제출서류와 무관 |
| 2026-03-27 | [EPS-TOPIK 시험 실시·장소](https://kp2mi.go.id/gtog-detail/korea/pengumuman-pelaksanaan-ujian-eps-topik-ubt-umum-sektor-perikanan-dan-sektor-manufaktur-tahun-2026) | 7 | 장소/시험 단계 자료; 일반제조업 최종 온라인 구직신청과 구별 |
| 2026-02-16 | [생체인식 및 시험등록 문서 검증](https://kp2mi.go.id/gtog-detail/korea/pengumuman-pemanggilan-perekaman-biometrik-dan-verifikasi-dokumen-online-peserta-pendaftar-program-g-to-g-korea-eps-topik-ubt-umum-sektor-perikanan-dan-sektor-manufaktur-tahun-2026) | 3 | **시험 등록** 문서 확인 절차; 이후 `job_docs`의 자동 근거로 사용 금지 |
| 2026-02-10 | [시험 등록 일정 변경](https://kp2mi.go.id/gtog-detail/korea/pengumuman-penyesuaian-waktu-pendaftaran-ubt-umum-sektor-perikanan-dan-sektor-manufaktur-program-g-to-g-ke-korea-selatan-tahun-2026) | 1 | 시험접수 일정이지 최종 구직등록 서류 목록 아님 |
| 2026-01-27 | [2026 일반 제조업·어업 EPS-TOPIK 최초 모집](https://kp2mi.go.id/gtog-detail/korea/pengumuman-pendaftaran-ubt-umum-sektor-perikanan-dan-sektor-manufaktur-progam-g-to-g-ke-korea-selatan-dengan-sistem-poin-tahun-2026) | 4 | `lamaran online` 3회 등장, 기존 조사상 MCU I/HIMPSI 및 이전 기수의 상태 구분 문맥. 2026년 이후 단계 최종 제출파일 확정 근거 아님 |

**총 PDF 링크 수 24개 = 6+1+2+7+3+1+4.** 10월 17일에는 PDF 파일 **내용 전체를 새로 읽은 것이 아니며**, HEAD 14건의 실패는 접속 재설정으로 인한 **미확인**이다. 2026년 어업 최종 구직등록, Root Industry, 2025년 일반 제조업의 양식을 2026년 일반 제조업에 복사하지 않는다.

## 4. 담당자 서명 전에 반드시 남은 질문

- [ ] 공식 한국 공통 5건의 실제 웹페이지와 제품 설명 간 의미 차이를 인간 검토자가 직접 확인하고 적용 범위 기록
- [ ] 기타 국가 5건 및 다국가 HRD EPS 2건의 차이 알림을 숨기지 않고 공통/비공통 범위 확인
- [ ] PDF HEAD 미확인 14건: 서버 과부하를 피하며 공식 웹페이지·원본 문서 접근성은 적절한 시점에 확인, **PDF 페이지별 내용 검증은 별도 표기**
- [ ] 2026 제조업 7개 공고의 본문/첨부 원문을 책임자가 검토하고, `job_docs` 최종 서류 확정 자료가 없는 경우 기존 HOLD 유지
- [ ] 책임자의 이름·승인 근거·승인 일시(Asia/Jakarta release day)를 원본 증거에 맞추어 **직접** 서명
- [ ] 최종 배포는 별도 승인된 후보 SHA/HTTPS 검증 후 진행, 베타 OPEN은 별도 명시적 승인

**불변:** `sourceHashAutomaticallyAccepted=false`, `manualSignoff=false`, `job_docs=HOLD`, `betaAccess=HOLD`, `authorizesRelease=false`, GitHub Draft PR #324 미병합. GitHub Actions 불필요.
