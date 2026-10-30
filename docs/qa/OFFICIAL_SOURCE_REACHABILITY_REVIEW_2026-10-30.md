# KEP official-source warning URL reachability review — 2026-10-30

**Scope:** Eight URLs marked for review in `docs/data/source_review_status.json`, last monitor message dated 2026-10-14. This is a *public web reachability and page identity spot-check*, NOT approval of source content, and does not change the source-review JSON or the launch gate.

| Recorded URL | Public check (2026-10-30) | Findings / next required step |
|---|---|---|
| https://law.go.kr/LSW/lsLinkCommonInfo.do?lsJoLnkSeq=1027161979 | Page opens | Korean Labor Standards Act Article 48(2), wage statements, showing effective date Oct 8, 2026. Compare legal text against prior evidence and in-app statement. |
| https://qcode.kdca.go.kr/qco/cd/codeInput2.do | Redirect opens | Redirects to https://travelhealth.kdca.go.kr/travel/cd/qcoInfo.do . Check whether in-app Q-CODE link and eligibility conditions need revision, and record the redirect explicitly. |
| https://1350.moel.go.kr/home/hp/ch/callchat.do | Page opens | MOEL 1350 phone counseling. Verify current contact information and relevant working-hours context; a separate chat page is narrower in scope. |
| https://epsnepal.gov.np/notices | Page opens | The notice listing currently loads, despite previously recorded HTTP 500. Run monitor again and verify the specific source content; do NOT clear a fetch warning on web-browser reachability alone. |
| https://colab.moha.gov.vn/tin-tucs/357/Chuong-trinh-EPS.aspx | Page opens | Vietnamese official EPS announcements listing; verify any new announcements separately for applicable cycle. |
| https://www.slbfe.lk/ | Page opens | Sri Lanka bureau portal with current Korean EPS announcements including Oct 29, 2026; compare changes and country-specific rules. |
| https://migrant.kg/ | Page opens | Kyrgyz migrant service portal redirects to /kg/; check language and official relevance. |
| https://www.mol.gov.mm/mol-department-of-labour/ | Page opens | Myanmar labor department listing with Oct 29, 2026 items; verify applicable specifics and domain provenance. |

## Required guardrails

- The source monitor's `state=review_required` is unchanged. The `checked=83/configured=84` figures are from the persisted historical monitor state and are NOT overwritten.
- Manually review the *content differences*, effective dates, jurisdiction, stage applicability and citations; then rerun source monitor and obtain authorized human approval.
- No Indonesia-Manufacturing official final-job-application documents were established by checking these URLs. Maintain exact HOLD.
- Beta access activation, main merge and production deployment remain blocked pending strict release gates.

## Additional code verification context

The newest `ux/indonesian-ui-copy-20261030` branch passed `python scripts/check_beta_launch_readiness.py --allow-source-review-pending` with explicit release HOLD. The Windows cross-platform UTF-8 fix in `scripts/test_release_copy_contract.py` passed 5 tests. Those are static checks and do NOT prove the strict official-source gate.

## Official pages

- Korean law Article 48: https://law.go.kr/LSW/lsLinkCommonInfo.do?lsJoLnkSeq=1027161979
- KDCA redirected Q-CODE: https://travelhealth.kdca.go.kr/travel/cd/qcoInfo.do
- MOEL 1350: https://1350.moel.go.kr/home/hp/ch/callchat.do
- Nepal: https://epsnepal.gov.np/notices
- Vietnam: https://colab.moha.gov.vn/tin-tucs/357/Chuong-trinh-EPS.aspx
- Sri Lanka: https://www.slbfe.lk/
- Kyrgyzstan: https://migrant.kg/
- Myanmar: https://www.mol.gov.mm/mol-department-of-labour/
