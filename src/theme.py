"""
네이버 금융 '테마별 시세' 페이지를 스크래핑해서
1) 당일 등락률 1위 테마를 '주도 테마'로 선정
2) 해당 테마 내 거래대금 상위 N종목을 추출한다.

주의: 테마 목록/구성 종목은 공식 API가 없어 네이버 페이지를 스크래핑한다 (비공식).
다만 거래대금 수치 자체는 스크래핑이 아니라 이미 신뢰성이 검증된 pykrx로 직접 조회해서 정확도를 높였다
(예전 버전은 네이버 상세 페이지의 특정 컬럼을 자릿수로 추측해서 읽었는데, 페이지 레이아웃에 따라
 거래대금이 아예 안 잡히는 문제가 있었다).
"""
import re
import time

import requests
from bs4 import BeautifulSoup

from . import config
from . import krx_client as krx

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}


def get_leading_theme() -> dict:
    """
    등락률 기준 1위 테마 정보를 반환.
    반환: {"name": str, "no": str, "change_pct": float}
    """
    resp = requests.get(config.NAVER_THEME_LIST_URL, headers=HEADERS, timeout=10)
    resp.encoding = "euc-kr"
    soup = BeautifulSoup(resp.text, "html.parser")

    table = soup.select_one("table.type_1")
    if table is None:
        raise RuntimeError("테마 목록 테이블을 찾을 수 없습니다. 페이지 구조가 변경되었을 수 있습니다.")

    best = None
    for row in table.select("tr"):
        link = row.select_one("td.col_type1 a")
        rate_cell = row.select_one("td.col_type2")
        if link is None or rate_cell is None:
            continue

        name = link.get_text(strip=True)
        href = link.get("href", "")
        match = re.search(r"no=(\d+)", href)
        if not match:
            continue
        theme_no = match.group(1)

        rate_text = rate_cell.get_text(strip=True).replace("%", "").replace("+", "")
        try:
            change_pct = float(rate_text)
        except ValueError:
            continue

        if best is None or change_pct > best["change_pct"]:
            best = {"name": name, "no": theme_no, "change_pct": change_pct}

    if best is None:
        raise RuntimeError("주도 테마를 찾지 못했습니다.")
    return best


def get_stocks_in_theme(theme_no: str) -> list:
    """
    테마 상세 페이지에서 구성 종목의 티커/이름만 추출한다 (거래대금은 여기서 안 다룸).
    특정 CSS 클래스에 의존하지 않고, "종목 상세로 연결되는 링크(code=파라미터 포함)"를
    모두 찾는 방식이라 페이지의 표 레이아웃이 바뀌어도 비교적 잘 견딘다.
    반환: [{"ticker": str, "name": str}, ...]
    """
    params = {"type": "theme", "no": theme_no}
    resp = requests.get(config.NAVER_THEME_DETAIL_URL, headers=HEADERS, params=params, timeout=10)
    resp.encoding = "euc-kr"
    soup = BeautifulSoup(resp.text, "html.parser")

    stocks = []
    seen = set()
    for link in soup.select("a[href*='code=']"):
        href = link.get("href", "")
        match = re.search(r"code=(\d{6})", href)
        if not match:
            continue
        ticker = match.group(1)
        name = link.get_text(strip=True)
        if not name or ticker in seen:
            continue
        seen.add(ticker)
        stocks.append({"ticker": ticker, "name": name})

    return stocks


def get_theme_report(date: str) -> dict:
    """
    테마 리포트 섹션 전체(주도 테마 + 거래대금 상위 종목) 생성.
    date: 거래대금을 조회할 기준일(YYYYMMDD)
    """
    theme = get_leading_theme()
    stocks = get_stocks_in_theme(theme["no"])

    for s in stocks:
        try:
            s["trading_value"] = krx.get_ticker_trading_value(s["ticker"], date)
        except Exception:
            s["trading_value"] = 0
        time.sleep(config.REQUEST_DELAY)

    stocks.sort(key=lambda x: x["trading_value"], reverse=True)
    top_stocks = stocks[: config.THEME_TOP_STOCK_COUNT]

    return {"theme": theme, "top_stocks": top_stocks}
