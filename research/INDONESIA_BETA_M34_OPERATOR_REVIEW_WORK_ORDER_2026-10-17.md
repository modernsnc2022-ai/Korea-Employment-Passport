# KEP M34 — 실제 담당자 공식자료 검토 인계 (서명 전 작업 지시서)

**일자:** 2026-10-17 (Jakarta). **성격:** 내부 운영자 검토 패킷이며 정부 기관의 제품 승인서가 아닙니다.

**결론:** 공식 공고 제목/URL 320건 재조회, 이전 M30 지문 일치. 정확한 일반 제조업 최종 구직등록 파일 목록 미확정, 실제 공개 베타 HOLD.

## 운영 책임 구분

기존 콘텐츠 리뷰어·베타 테스터는 공식 노동/검역/EPS 자료의 자동 승인권자가 아닙니다. 공식자료 내용을 읽고 확인하는 사람은 지정된 **내부 검토 책임자**이고, 국가기관이 KEP 서비스를 승인했다는 뜻이 아닙니다. 배포·베타 OPEN은 별도의 책임자 결정입니다.

## 필수 사람 검토 항목 — 총 20건

| 우선 | 항목 | 적용범위 | 실제 공식 원문 | 사람 검토 |
|---|---|---|---|---|
| P1 | SRC:kdca_qcode_input | korea_shared | [원문](https://qcode.kdca.go.kr/qco/cd/codeInput2.do) | PENDING |
| P1 | SRC:labor_standards_wage_statement | korea_shared | [원문](https://law.go.kr/LSW/lsLinkCommonInfo.do?lsJoLnkSeq=1027161979) | PENDING |
| P1 | SRC:minimum_wage | korea_shared | [원문](https://www.minimumwage.go.kr/index.jsp) | PENDING |
| P1 | SRC:moel_1350_contact | korea_shared | [원문](https://1350.moel.go.kr/home/hp/ch/callchat.do) | PENDING |
| P1 | SRC:moel_wage_arrears_2026 | korea_shared | [원문](https://1350.moel.go.kr/rtmview.do?id=1000317748) | PENDING |
| P1 | GATE:final_manufacturing_job_docs | 2026_ubt_umum_manufacturing_post_skill_test | [원문](https://kp2mi.go.id/gtog-korea/pengumuman) | PENDING |
| P2 | NOTICE:10-February-2026 | exam_registration_adjustment | [원문](https://kp2mi.go.id/gtog-detail/korea/pengumuman-penyesuaian-waktu-pendaftaran-ubt-umum-sektor-perikanan-dan-sektor-manufaktur-program-g-to-g-ke-korea-selatan-tahun-2026) | PENDING |
| P2 | NOTICE:10-September-2026 | eps_topik_stage_1_result | [원문](https://kp2mi.go.id/gtog-detail/korea/pengumuman-hasil-ujian-kemampuan-bahasa-korea-eps-topik-ubt-umum-sektor-manufaktur-tahun-2026) | PENDING |
| P2 | NOTICE:16-February-2026 | exam_enrollment_biometrics | [원문](https://kp2mi.go.id/gtog-detail/korea/pengumuman-pemanggilan-perekaman-biometrik-dan-verifikasi-dokumen-online-peserta-pendaftar-program-g-to-g-korea-eps-topik-ubt-umum-sektor-perikanan-dan-sektor-manufaktur-tahun-2026) | PENDING |
| P2 | NOTICE:17-September-2026 | optional_skill_test_evidence | [원문](https://kp2mi.go.id/gtog-detail/korea/pengumuman-persyaratan-unggah-dokumen-kompetensi-peserta-skill-test-ubt-umum-sektor-manufaktur-eps-topik-tahun-2026) | PENDING |
| P2 | NOTICE:27-January-2026 | initial_exam_registration | [원문](https://kp2mi.go.id/gtog-detail/korea/pengumuman-pendaftaran-ubt-umum-sektor-perikanan-dan-sektor-manufaktur-progam-g-to-g-ke-korea-selatan-dengan-sistem-poin-tahun-2026) | PENDING |
| P2 | NOTICE:27-March-2026 | exam_schedule | [원문](https://kp2mi.go.id/gtog-detail/korea/pengumuman-pelaksanaan-ujian-eps-topik-ubt-umum-sektor-perikanan-dan-sektor-manufaktur-tahun-2026) | PENDING |
| P2 | NOTICE:5-May-2026 | exam_fee_refund | [원문](https://kp2mi.go.id/gtog-detail/korea/pengumuman-pengembalian-biaya-ujian-eps-topik-ubt-umum-sektor-perikanan-dan-sektor-manufaktur-tahun-2026-tahap-pertama) | PENDING |
| P2 | SRC:mm_hrdk_schedule_index | multi_country_eps_schedule | [원문](https://epstopik.hrdkorea.or.kr/epstopik/abot/exam/selectSechduleDescList.do?lang=en) | PENDING |
| P2 | SRC:mm_hrdk_skills_candidates | multi_country_eps_schedule | [원문](https://epstopik.hrdkorea.or.kr/epstopik/pass/candidate/functionalLevelCandidateList.do?lang=en) | PENDING |
| P3 | SRC:kg_migrant_home | other_country | [원문](https://migrant.kg/) | PENDING |
| P3 | SRC:lk_slbfe_home | other_country | [원문](https://www.slbfe.lk/) | PENDING |
| P3 | SRC:mm_mol_dol_index | other_country | [원문](https://www.mol.gov.mm/mol-department-of-labour/) | PENDING |
| P3 | SRC:np_eps_notice_index | other_country | [원문](https://epsnepal.gov.np/notices) | PENDING |
| P3 | SRC:vn_colab_eps_notices | other_country | [원문](https://colab.moha.gov.vn/tin-tucs/357/Chuong-trinh-EPS.aspx) | PENDING |

## 기술 출시 게이트 — 담당자 서명 전

| 게이트 | 실제 검증 상태 | 담당자 직접 해야 할 확인 |
|---|---|---|
| route_safety | PASS | Retain official-only fallback for final Manufacturing documents. |
| country_source_classification | PASS | All current source alerts must remain visible; never accept changed hashes automatically. |
| official_monitor_today | PASS | Current read-only watch classified; separate named approval still required. |
| indonesia_source_manual_signoff | PENDING | Operator must review 5 Korea-common, acknowledge multi-country HRD Korea and foreign-country alerts, then sign the actual date. |
| kp2mi_manufacturing_release_day_signoff | PENDING | Human must review the current 2026 general Manufacturing notice contents/attachments and record a genuine same-day signoff. |
| exact_2026_manufacturing_final_job_documents | PENDING | Do not enable beta or final submission. Obtain exact KP2MI 2026 General Manufacturing job-doc original notice + attachments, review required files, and implement an explicit independently tested release-day signoff path. |
| optional_skill_annex_evidence | PASS | Do not promote the optional annexes into final job-application requirements. |
| published_main_source_integrity | PASS | Use authenticated read-only Pages source diagnostics; never change Pages branch to bypass review. |
| same_head_pages_deployment | PENDING | Run --live in a clean reviewed checkout after approved Pages deployment; independently review the actual deployment event. This check never authorizes OPEN. |
| explicit_manual_beta_open | PENDING | A responsible operator must explicitly authorize public beta OPEN after every technical/official gate passes. HOLD is the expected pre-approval state. |

## 증거 기록 원칙

- 담당자가 실제 URL, 본문 조항/부속 PDF 페이지, 적용 국가·직종·모집연도·발표일을 확인하고 실명·시간대 있는 확인 일시·판단 사유 기록
- 한국 공통 출처 5개는 우선 심사, HRD Korea 다국가 출처 2건은 인도네시아 적용 범위 확인, 다른 나라 5개는 해당 국가 담당 검토 항목으로 유지
- 시험등록 서류, 2025 제조업, 2026 어업/Root Industry/특별시험, 9월 선택적 Skill Test 첨부는 2026 일반 제조업 **최종** 구직등록 서류로 승격 금지
- 실제 공식 최종 목록과 서명된 서류별 판정을 확보하기 전에는 `job_docs` HOLD 해제 금지
- 서명 후에도 별도 승인된 후보 실서비스 배포, 동일 SHA 9/9, HTTPS 6/6, 운영자 베타 OPEN 승인 필요

**현재:** 전 항목 사람 검토 PENDING / 최종 2026 제조업 구직신청 서류 HOLD / Draft PR 미병합 / 공개 베타 HOLD.
