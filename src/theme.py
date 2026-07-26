"""
네이버 금융 '테마별 시세' 페이지를 스크래핑해서
1) 당일 등락률 1위 테마를 '주도 테마'로 선정
2) 해당 테마 내 거래대금 상위 N종목을 추출한다.

주의: 공식 API가 아니라 HTML 구조에 의존하는 비공식 스크래핑입니다.
네이버 페이지 구조가 바뀌면 파싱 로직을 수정해야 할 수 있습니다.
"""
import re
import time

import requests
from bs4 import BeautifulSoup

from . import config

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


def get_top_stocks_in_theme(theme_no: str, top_n: int = None) -> list:
    """
    특정 테마 상세 페이지에서 거래대금 상위 N종목을 반환.
    반환: [{"ticker": str, "name": str, "trading_value": int}, ...]
    """
    top_n = top_n or config.THEME_TOP_STOCK_COUNT
    params = {"type": "theme", "no": theme_no}
    resp = requests.get(config.NAVER_THEME_DETAIL_URL, headers=HEADERS, params=params, timeout=10)
    resp.encoding = "euc-kr"
    soup = BeautifulSoup(resp.text, "html.parser")

    table = soup.select_one("table.type_5")
    if table is None:
        raise RuntimeError("테마 상세 테이블을 찾을 수 없습니다. 페이지 구조가 변경되었을 수 있습니다.")

    stocks = []
    for row in table.select("tr"):
        link = row.select_one("a.tltle")
        if link is None:
            continue

        name = link.get_text(strip=True)
        href = link.get("href", "")
        match = re.search(r"code=(\w+)", href)
        if not match:
            continue
        ticker = match.group(1)

        cells = [c.get_text(strip=True).replace(",", "") for c in row.select("td")]
        # 거래대금 컬럼 위치는 페이지 레이아웃에 의존 (없으면 0으로 처리 후 이후 pykrx 데이터로 보정 권장)
        trading_value = 0
        for c in cells:
            if c.isdigit() and len(c) >= 6:
                trading_value = int(c)
                break

        stocks.append({"ticker": ticker, "name": name, "trading_value": trading_value})
        time.sleep(config.REQUEST_DELAY)

    stocks.sort(key=lambda x: x["trading_value"], reverse=True)
    return stocks[:top_n]


def get_theme_report() -> dict:
    """테마 리포트 섹션 전체(주도 테마 + 상위 종목) 생성."""
    theme = get_leading_theme()
    top_stocks = get_top_stocks_in_theme(theme["no"])
    return {"theme": theme, "top_stocks": top_stocks}
