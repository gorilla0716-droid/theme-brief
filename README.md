# 📰 테마 브리프

테마별 뉴스와 관련 주식을 매일 아침 체크하는 개인용 설치형 웹앱(PWA)입니다.

## 휴대폰에 설치
- **아이폰(Safari):** 앱 주소 열기 → 공유 버튼 → '홈 화면에 추가'
- **안드로이드(Chrome):** 앱 주소 열기 → ⋮ 메뉴 → '앱 설치' 또는 '홈 화면에 추가'

## 뉴스 자동 수집
- `.github/workflows/collect.yml`이 평일 아침 7시 48분(한국시간)에 `scripts/collect.py`를 실행합니다.
- Google 뉴스 RSS에서 `themes.json`의 검색어로 최근 4일 이내 기사를 테마당 최대 8건 모아 `data.json`을 갱신합니다.
- 비용 없음: API 키가 필요 없고, 공개 저장소의 GitHub Actions는 무료입니다. Claude 사용량도 들지 않습니다.

### 켜기 / 끄기 / 지금 실행
GitHub 저장소 → **Actions** → **Collect news**
- 끄기: 오른쪽 `···` → **Disable workflow**
- 켜기: **Enable workflow**
- 지금 실행: **Run workflow**

> GitHub는 저장소에 60일 동안 활동이 없으면 예약 실행을 자동으로 멈춥니다. 멈추면 위의 Enable workflow를 누르면 됩니다.

## 테마·검색어 바꾸기
`themes.json`을 GitHub에서 직접 수정하면 다음 수집부터 반영됩니다.
- `queries`: 테마별 검색어 (2~3개 권장)
- `watch`: '체크:' 줄에 보일 문구
- `stocks`: 관련 주식 (`name`, `code` 6자리, `reason`)

## 참고
- 체크포인트는 그날 주요 헤드라인 3개입니다. 호재·악재 표시는 제목 단어로 자동 분류한 것이라 틀릴 수 있습니다.
- 체크 표시, 직접 추가한 테마·뉴스·종목, 화면 설정은 각 기기의 브라우저에만 저장됩니다.
- 투자 판단의 근거가 아닌 참고용입니다.
