# KEP UI/UX 개편 검토 기록 — 2026-10-30 KST

**판정: 검토용 후보. 상용 완성 승인 및 운영 배포는 보류.**

PR #326과 `KEP_UI_UX_REDESIGN_HANDOFF_2026-10-30.md` 전체를 기준으로, 실패 비교 → 모바일 홈 → 단계 안내 → 공식 출처 → 팝업 → 실제 화면에서 발견한 보정 순서로 진행했다. main과 기존 PR #326은 수정·병합하지 않았다. 모든 새 PR은 draft이며 앞 PR을 base로 하는 순차 검토 구조다.

## 브랜치·커밋·검증

| 작업 | 브랜치 | PR | 원격 커밋 | 해당 단계 전체 UI 결과 |
|---|---|---|---|---|
| 실패 비교·fixture·서버 | `fix/ui-regression-baseline-20261030` | #327 | `aa1c16e87c6265e90a0b3c1b8265cce4bc81c0b2` | 60/60 PASS |
| 모바일 홈 | `ux/mobile-action-home-20261030` | #328 | `5cb6f5d9566cd28bd1efe059fde93480cf20e518` | 67/67 PASS |
| 단계·서류 안내 | `ux/stage-task-guidance-20261030` | #329 | `f1e964eee32ed383dbe0f0e4d2ba545120f9c609` | 70/70 PASS |
| 공식 출처·불확실성 | `ux/official-source-context-20261030` | #330 | `ba810f00fff37f11e06391f08b9787022e47e3c7` | 74/74 PASS |
| 팝업·뒤로가기·초점 | `ux/mobile-dialog-navigation-20261030` | #331 | `f3125bd10a22ee50e0d0e0e4dd9fe02e647ba227` | 84/84 PASS |
| 실제 화면 보정·증거 | `fix/mobile-visual-polish-20261030` | 별도 후속 PR | PR head 참조 | 85/85 PASS |

GitHub API로 올린 각 원격 트리는 테스트한 로컬 Git 트리와 SHA가 일치함을 확인했다. API 생성 커밋의 작성 메타데이터 때문에 로컬 커밋 SHA와 원격 SHA는 다를 수 있으며, 위 표는 원격 SHA다. Actions는 실행하지 않았다.

## 첫 작업: 기존 실패 비교

- main `dc40ecbdaf29c33edeaf5165f4f26f84fcd062fa`와 PR #326 `2bfb5aff51e593c9bc3f6b4aa4d7182219542bb0`: 동일 환경에서 각각 **46 PASS / 10 FAIL**, 실패 이름이 모두 동일했다.
- 7건은 clean-source fixture가 실제 `latestReadOnlyObservation`을 남겨 두어 안전 로직과 모순된 상태를 만든 문제였다. 단계 이벤트와 선택은 정상이고 문서 도우미가 보호 조건에 의해 숨겨졌다. 실제 출처 데이터나 fail-closed 로직을 느슨하게 만들지 않았다.
- 나머지 3건은 공식 목록의 변경된 URL, 새 이메일 인증 코드 필드, 이미 제거된 전역 운영자 알림에 대한 오래된 assertion이었다.
- 추가 direct-intake 테스트의 fixture도 실제 승인·보안 위젯·OTP 흐름에 맞춰 고쳤다. 외부 접수·이메일 발송은 전부 mock이며 실제 신청을 만들지 않았다.
- 비교 실행에서는 ECONNREFUSED가 없었다. 브라우저 설치 중 실행한 초기 결과는 비교에서 제외했다. 별도 클라우드 명령의 서버 연결 문제를 관찰했으며, 테스트와 서버가 같은 프로세스 생명주기를 쓰도록 했다.
- 상세 오류 원문: `baseline-failures-2026-10-30.txt`. 실패 이름과 수치: `ui-baseline-2026-10-30.json`.

재현:

```sh
npm ci
npx playwright install chromium
PLAYWRIGHT_PORT=4173 npx playwright test --reporter=json
python scripts/check_webapp_contract.py
python scripts/check_beta_launch_readiness.py
node scripts/capture_ui_redesign.js
```

브라우저 설치가 끝난 뒤 테스트를 시작해야 한다. main/PR을 비교할 때는 별도 checkout과 포트를 사용한다. `reuseExistingServer=false`로 다른 checkout의 서버를 조용히 재사용하지 않는다.

## 실제 변경

- 큰 소개 hero와 진행률을 주 작업에서 제거하고, 진행 기록·백업을 선택 영역으로 옮겼다. 비정부 서비스 표시와 접수 마감은 첫 방문부터 보인다.
- 현재 단계는 사용자 선택임을 표시한다. 홈에 공식 원문 바로가기, 다음 행동, 안전 경고와 주 버튼을 함께 둔다. 데스크톱·태블릿의 도구 메뉴도 작업 위에서 찾을 수 있다.
- 27개 단계는 동일한 준비 안내를 쓴다. 공고 미선택·출처 검토 중에는 다른 회차의 서류 목록을 대신 노출하지 않는다. 비용 정보 부족을 무료로 표현하지 않는다.
- 원문 링크, 기관, 적용 범위, 데이터 확인 날짜와 검토 상태를 함께 표시한다. 과거 데이터 날짜를 오늘의 공식 검증처럼 표시하지 않는다. 출처가 불확실하면 비용이 기존 숫자와 같아도 확인됐다고 안내하지 않는다.
- 팝업의 닫기·하단 행동은 본문 스크롤과 분리된다. Back, Esc, 포커스 복귀, 배경 스크롤 잠금, 짧은 화면과 안전 영역을 처리한다.
- 실제 320px 캡처에서 발견한 CTA 가림과 파일 입력 18px 잘림을 고쳤다. 재방문 페이지를 다시 로드한 뒤 주 CTA를 검사하도록 테스트도 강화했다. 체크박스 터치 영역은 44px다.
- 주요 도구 제목을 인도네시아어로 정리하고, 회원 공간의 구현 용어를 이용자 안내로 바꿨다. 원어민 검토가 끝났다는 뜻은 아니다.

## 변경 파일

제품·실행 설정:

- `docs/app.html`
- `docs/app-shell.css`
- `docs/app-runtime.js`
- `playwright.config.js`

검증:

- `tests/ui.spec.js`
- `tests/beta-intake.spec.js`
- `tests/action-home.spec.js`
- `tests/stage-guidance.spec.js`
- `tests/source-context.spec.js`
- `tests/dialog-ux.spec.js`
- `tests/document-controls.spec.js`
- `scripts/capture_ui_redesign.js`

증거·인계: `docs/qa/`의 보고서, 결과 JSON/TXT/YAML, 현재 화면 49장과 변경 전 홈 1장.

`docs/data/`와 `app/assets/`의 diff는 0이다. 27개 단계, 13개 문서 팩, 308개 exact answer, 256개 질문, 8개 양식·113개 필드 등 기존 데이터 계약을 보존했다. 기존 저장 키, 베타 참가자 분리, 문서·상태 백업과 복원, 완료 순서, 공식 공고 범위 및 민감 값의 비저장 검증을 기존 회귀 테스트로 확인했다.

## 검증 결과와 한계

- 최종 전체 Playwright: **85/85 PASS**, FAIL 0. 결과 파일 참조. 재시도 0, 생략 0.
- 폭 320/360/375/390/430/768/1280px, Chromium 140.0.7339.16 / Playwright 1.55.0, 클라우드 Linux.
- 현재 화면 49장: 첫 방문·재방문 홈·단계 상단/하단, 390/1280px의 8개 도구, 320/390/1280px 서류 입력, 문서 화면의 루트 글자 크기 200% 모사. 실제 기기 촬영이나 브라우저 확대 검사 전체를 대신하지 않는다.
- 캡처 경로에서 페이지 가로 넘침 0, JavaScript pageerror 0. 닫기/주 버튼 유지, 공식 원문 클릭(mock 목적지), 실제 선택·문서 이동·재방문을 검사했다.
- 주 버튼의 실제 계산 색상은 흰색 / RGB(23,105,92), 대비 약 6.54:1. 이는 전체 화면의 모든 대비 조합을 감사한 결과가 아니다.
- 네이티브 dialog의 키보드 순환 및 접근성 트리를 확인했다. Chromium이 Tab 순환 경계에서 브라우저 chrome으로 이동할 수 있으며, 이후 Tab이 모달로 돌아오는지 검사했다. NVDA/VoiceOver 실사용은 미실시다.
- 정적 검사 명령 30개 중 **29 PASS / 1 FAIL**. 실패: `Check beta prelaunch readiness`. `--allow-source-review-pending`에서도 beta 페이지에 과거 특정 문구 3개를 요구하는 assertion이 실패한다. **main에서도 동일 실패를 재현했다.** 검사를 완화하거나 베타 안내를 허위로 바꾸지 않았다.
- strict 배포 준비 검사 **FAIL**: 출처 상태 `review_required`, 구성 출처 전부 검사 미완료, 남은 review/fetch 경고, 위 안내문 검사. 상세: `strict-release-gate-2026-10-30.txt`.
- Pages 후보 배포·HTTPS/자산 확인은 **미실시**다. 현재 운영 URL이 열리는 것은 이 후보의 배포 증거가 아니므로 대체 PASS로 기록하지 않았다.

## 화면 기준 평가

390px 변경 전 홈에서는 소개·마감·사용법·백업 뒤로 다음 행동이 밀렸다. 현재는 320px에서도 공식 원문 바로가기와 주 행동을 첫 화면에서 찾을 수 있다. 서류 입력은 정상 폭이고, 팝업 본문 맨 아래에서도 닫기와 주 행동이 남는다. 색만 바꾼 변경에서 벗어나 정보 순서·작업 흐름·상태 표현을 실제로 바꾼 후보라고 평가한다.

그러나 긴 공고 설명, 조건별 실제 용어, 후기 단계의 복잡한 상황, 현지 사용자의 이해도까지 검증한 것은 아니다. 49장 캡처와 자동 PASS만으로 상용 서비스 수준이라고 확정하지 않는다.

## 남은 일과 배포

1. 인도네시아 원어민 용어·문장 검수. 특히 기존 비용·기관 데이터의 영어 표현도 별도 검토가 필요하다.
2. 실제 Android/iOS에서 가상 키보드·브라우저 Back·안전 영역·확대 및 보조기술 실사용 확인.
3. EPS 초보자와 기존 참여자의 단계 선택 → 다음 행동 → 서류 → 공식 원문 작업 평가. 성공률·혼란 지점·이탈·탭 수는 아직 측정하지 않았다.
4. 출처 검토의 사람 승인과 최신성 확인. 상속된 베타 준비 검사 불일치의 별도 해결.
5. 사용자 디자인 승인 후에만 순차 병합·동일 후보 staging/자산/HTTPS 검증·운영 배포·롤백 검토.

**이번 작업에서 운영 배포, main 병합, 베타 공개, 출처 승인, GitHub Actions 실행, 사용자 Windows 장치 작업을 하지 않았다.**
