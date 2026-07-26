"""
전역 설정값
필요에 따라 숫자만 바꿔서 스크리닝 기준을 조정할 수 있습니다.
"""
import os

# ── 종목 스크리닝 기준 ──────────────────────────────────────
MARKET = "KOSPI"
MARKET_CAP_MIN = 300_000_000_000        # 시가총액 하한 (3천억원)
MARKET_CAP_MAX = 10_000_000_000_000     # 시가총액 상한 (10조원)
SHORT_BALANCE_MAX_PCT = 10.0            # 공매도 잔고 비중 상한 (%)
NEAR_52W_HIGH_PCT = 2.0                 # 52주 신고가 대비 허용 하락폭 (%)

# 정배열 판단에 사용할 이동평균선 (짧은 것 -> 긴 것 순서로 나열)
# 종가 > MA[0] > MA[1] > MA[2] > MA[3] 이면 정배열로 판단
MA_WINDOWS = [5, 20, 60, 120]

# ── 리포트 조회 기간 ─────────────────────────────────────────
RECENT_DAYS = 5              # 최근 평균 거래대금 / 수급 조회 기간 (영업일)
LOOKBACK_DAYS_OHLCV = 400    # 52주 고가 + 이동평균 계산용 넉넉한 조회 기간(달력일 기준)

# ── 테마 분석 (네이버 금융, 비공식) ───────────────────────────
NAVER_THEME_LIST_URL = "https://finance.naver.com/sise/theme.naver"
NAVER_THEME_DETAIL_URL = "https://finance.naver.com/sise/sise_group_detail.naver"
THEME_TOP_STOCK_COUNT = 2    # 주도 테마 내에서 거래대금 상위 몇 종목을 뽑을지

# ── 뉴스 검색 (네이버 검색 Open API) ───────────────────────────
# https://developers.naver.com 에서 애플리케이션 등록 후 발급받은 값을
# 로컬에서는 환경변수로, GitHub Actions에서는 Secrets로 주입합니다.
NAVER_CLIENT_ID = os.environ.get("NAVER_CLIENT_ID", "")
NAVER_CLIENT_SECRET = os.environ.get("NAVER_CLIENT_SECRET", "")
NAVER_NEWS_API_URL = "https://openapi.naver.com/v1/search/news.json"
NEWS_COUNT_PER_STOCK = 3

# ── 출력 경로 (GitHub Pages 배포 대상 폴더) ─────────────────────
OUTPUT_DIR = "docs"

# 요청 과다로 차단되지 않도록 호출 사이 최소 딜레이(초)
REQUEST_DELAY = 0.3
