"""
전역 설정값
필요에 따라 숫자만 바꿔서 스크리닝 기준을 조정할 수 있습니다.
"""
import os

from dotenv import load_dotenv

# 프로젝트 루트의 .env 파일을 자동으로 읽어서 환경변수로 등록한다.
# (VSCode F5 실행뿐 아니라 터미널에서 python main.py로 직접 실행할 때도 동작하게 하기 위함)
load_dotenv()

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

# ── 뉴스 검색 (NAVER API HUB - 네이버 클라우드 플랫폼) ───────────
# https://www.ncloud.com 콘솔의 NAVER API HUB에서 Application 등록 후 발급받은
# API Gateway 키(X-NCP-APIGW-API-KEY-ID / X-NCP-APIGW-API-KEY)를
# 로컬에서는 환경변수로, GitHub Actions에서는 Secrets로 주입합니다.
NAVER_API_KEY_ID = os.environ.get("NAVER_API_KEY_ID", "")
NAVER_API_KEY = os.environ.get("NAVER_API_KEY", "")
NAVER_NEWS_API_URL = "https://naverapihub.apigw.ntruss.com/search/v1/news"
NEWS_COUNT_PER_STOCK = 3

# ── 출력 경로 (GitHub Pages 배포 대상 폴더) ─────────────────────
OUTPUT_DIR = "docs"

# 요청 과다로 차단되지 않도록 호출 사이 최소 딜레이(초)
REQUEST_DELAY = 0.3
