# KEP — Korea-shared four-source check, 2026-10-15

This is a **read-only, limited semantic review** of four changed-source alerts from the 84/84 successful 2026-10-15 watch. Not hash acceptance, named human legal signoff, official complete-index review, beta OPEN, or permission to deploy.

| Source ID | 2026-10-15 current normalized SHA-256 | Verified narrow guidance |
| --- | --- | --- |
| `labor_standards_wage_statement` | `a8754d0fbd0d59f2164d056a6e40cdb7b7b8048cb95b8a87726481db40085786` | Labor Standards Act Article 48(2) still requires written/electronic wage statements on wage payment, including wage components and calculation; no employer-specific wage amount adjudicated |
| `kdca_qcode_input` | `c7ff92c67b21468dbc6f8be4547ea6c4032f150c065b2fd212e7e822fa8a8aee` | Official Q-CODE conditions remain risk-region/symptom-sensitive; no universal E-9 Q-CODE mandate |
| `moel_1350_contact` | `846f066be872e653a875fb9072badc2cd9d58dbb1546252fe040ef0e06b39d71` | 1350 official employment consultation; weekday 09:00–18:00 KST, without implying that a call files/completes a legal complaint |
| `moel_wage_arrears_2026` | `35fa3f7f3e67ec4a033abfe944bb9a498695f3cad8fefa15a245314bad6efe1c` | Official 2026-02-12 MOEL 1350 reply: unpaid wages can be reported to the relevant local labor authority; no guarantee of recovery date or outcome |

The first three normalized hashes **exactly match** independent snapshots documented on 2026-10-14 in `research/ID_KOREA_SHARED_3_OFFICIAL_SOURCE_RECHECK_20261014.md`. All four current pages returned equal hashes on two additional fetches in this review. The fourth changed alert was absent from yesterday's published `docs/data/source_review_status.json`; using the new diagnostic `--result` option correctly included it from the fresh 2026-10-15 read-only scan.

Source URLs: https://law.go.kr/LSW/lsLinkCommonInfo.do?lsJoLnkSeq=1027161979 ; https://qcode.kdca.go.kr/qco/cd/codeInput2.do ; https://1350.moel.go.kr/home/hp/ch/callchat.do ; https://1350.moel.go.kr/rtmview.do?id=1000317748 .

**Decision:** Present KEP wage-slip, conditional Q-CODE, 1350 advice and wage-arrears complaint guidance need no immediate rule change based on this bounded review. This does **not prove** no other rule changed on the sites. The earlier accepted baseline hashes were deliberately NOT replaced. The additional six non-Indonesia-country alerts remain pending. The same-day official scope/manual approval, KP2MI 2026 Manufacturing exact job document checklist, same-HEAD deployed Pages parity and manual beta access approval all remain blocked or pending. Public beta and direct D1 intake remain HOLD; email interest path may remain OPEN.
