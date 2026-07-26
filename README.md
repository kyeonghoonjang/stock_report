# 주식 테마 리포트 (데모 v1)

장 마감 후 국내 주식(코스피) 데이터를 스크리닝해서, 매일 자동으로 HTML 리포트를 생성하고
GitHub Pages로 공개하는 데모 프로젝트입니다.

## 리포트 구성

1. **테마 리포트**: 당일 등락률 1위 테마 + 해당 테마 내 거래대금 상위 2종목
2. **선정 종목 리포트**: 아래 조건을 모두 만족하는 코스피 종목
   - 시가총액 3,000억 ~ 10조원
   - 일봉 기준 정배열 (종가 > 5일선 > 20일선 > 60일선 > 120일선)
   - 52주 신고가 돌파 또는 고가 대비 -2% 이내
   - ~~공매도 잔고 비중 10% 이하~~ → **현재 비활성화** (아래 "알려진 제약" 참고)

   각 종목에 대해 다음을 표시합니다.
   - 금일 거래대금 & 최근 5일 평균 거래대금 (차트)
   - 외국인/기관/개인 최근 5일 순매수 (차트)
   - 관련 주요 기사 (제목 하이퍼링크)

## ⚠️ KRX 로그인 관련 안내 (2025년 12월 정책 변경)

2025년 12월 27일부터 KRX 정보데이터시스템이 회원제 "KRX Data Marketplace"로 전환되어, 데이터 조회 시 로그인이 필수가 되었습니다 (조회 자체는 무료, 네이버/카카오 간편가입 가능).
이에 맞춰 `pykrx`도 업데이트되었고, **`KRX_ID` / `KRX_PW` 환경변수를 pykrx가 내부적으로 직접 읽어 로그인**합니다. (우리 코드가 아니라 pykrx 라이브러리 자체 동작입니다.)

- `pip install -U pykrx`로 최신 버전인지 꼭 확인하세요.
- `.env` / GitHub Secrets에 `KRX_ID`, `KRX_PW`를 반드시 추가해야 정상 동작합니다.
- **이 아이디/비밀번호를 캡처해서 공유하거나 코드에 하드코딩하지 마세요.** 다른 서비스와 같은 비밀번호를 재사용하지 않는 것을 권장합니다.

## 사용 데이터 소스 및 제약

| 항목 | 소스 | 비고 |
|---|---|---|
| 시세/시가총액/수급 | [pykrx](https://github.com/sharebook-kr/pykrx) | KRX 공식 데이터 기반, 무료 |
| 테마 정보 | 네이버 금융 페이지 스크래핑 | **비공식**. 페이지 구조 변경 시 `src/theme.py` 수정 필요 |
| 뉴스 | 네이버 검색 Open API | 무료지만 [developers.naver.com](https://developers.naver.com)에서 API 키 발급 필요 (일 25,000회 한도). 키가 없으면 뉴스 섹션은 비어있는 채로 리포트가 생성됩니다 |

## VSCode에서 디버그 실행

1. `.env.example`을 복사해서 `.env` 파일 생성 후 실제 발급받은 키 입력 (`.env`는 `.gitignore`에 포함되어 있어 커밋되지 않음)
2. `Ctrl+Shift+P` → **Python: Select Interpreter**로 가상환경 선택
3. VSCode 좌측 **Run and Debug** 탭 → **"리포트 실행 (main.py)"** 선택 → F5
   - `.vscode/launch.json`이 `.env` 값을 자동으로 읽어서 실행합니다.
   - 특정 날짜로 테스트하고 싶으면 "리포트 실행 (특정 날짜 지정)" 구성을 사용하거나 `args`의 날짜를 수정하세요.
4. `src/screener.py`, `src/theme.py` 등에 브레이크포인트를 걸어 값 확인 가능

## 로컬 실행 (터미널)

```bash
pip install -r requirements.txt
pip install -U pykrx   # KRX 로그인 대응 최신 버전 확인

# 네이버 뉴스 API를 쓰려면 (선택)
export NAVER_CLIENT_ID=xxx
export NAVER_CLIENT_SECRET=xxx

# KRX Data Marketplace 로그인 정보 (필수, 2025년 12월 정책 변경으로 인해)
export KRX_ID=xxx
export KRX_PW=xxx

python main.py
# 결과: docs/index.html
```

### 뉴스 API 키 발급 (네이버 검색 Open API)

1. [https://developers.naver.com](https://developers.naver.com) 로그인 → Application → 애플리케이션 등록
2. 사용 API 드롭다운에서 **검색** 선택
3. 비로그인 오픈 API 서비스 환경에서 WEB 설정 후 등록
4. 등록된 애플리케이션에서 Client ID / Client Secret 확인

## GitHub Actions + Pages 자동 배포 설정 방법

1. 이 저장소를 본인 GitHub 계정에 push
2. **Settings → Secrets and variables → Actions**에서
   `NAVER_CLIENT_ID`, `NAVER_CLIENT_SECRET`을 등록 (선택 사항, 없으면 뉴스만 비활성화됨)
   `KRX_ID`, `KRX_PW`도 반드시 등록 (필수, 없으면 시세 조회 자체가 실패함)
3. **Settings → Pages**에서 Source를 `Deploy from a branch` → `main` 브랜치 `/docs` 폴더로 설정
4. `.github/workflows/daily_report.yml`이 평일 KST 15:45에 자동 실행되어 `docs/index.html`을 갱신하고 push함
5. 몇 분 후 `https://<아이디>.github.io/<저장소명>/` 에서 리포트 확인 가능
6. Actions 탭에서 `workflow_dispatch`로 수동 실행도 가능 (테스트용)

## 알려진 제약 (데모 버전)

- **공매도 잔고 필터는 현재 비활성화되어 있습니다.** 2025년 12월 KRX Data Marketplace 전환 이후
  pykrx의 `get_shorting_balance_by_ticker`가 새 응답 형식(`ISU_CD`, `BAL_RTO` 등 영문 컬럼)을
  아직 제대로 매핑하지 못해 호출이 실패합니다 (2026년 2월 기준 pykrx 저장소에 관련 오픈 이슈 다수).
  `pip install -U pykrx`로 라이브러리가 업데이트되면, `src/screener.py`의 `run_screening()`에서
  `filter_by_short_balance()` 호출을 다시 추가해서 되살릴 수 있습니다 (함수 자체는 남겨둠).

- 스크리닝 대상은 코스피 전 종목이며, 종목 수가 많은 날은 개별 종목별 API 호출(OHLCV, 공매도, 수급)로
  인해 실행 시간이 다소 걸릴 수 있습니다. (GitHub Actions 무료 티어 한도 내에서는 충분히 가능한 수준)
- 테마 스크래핑은 비공식이므로 장기 운영 시 정기적인 점검이 필요합니다.
- 정배열/52주가 조건의 구체적 수치는 `src/config.py`에서 조정 가능합니다.
