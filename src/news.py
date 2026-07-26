"""
네이버 검색 Open API(뉴스)로 종목 관련 주요 기사를 검색한다.
https://developers.naver.com 에서 애플리케이션을 등록하면
Client ID / Client Secret을 무료로 발급받을 수 있다. (일 25,000회 호출 한도)
"""
import re
import time

import requests

from . import config


def _strip_html(text: str) -> str:
    return re.sub(r"<[^>]+>", "", text)


def search_news_for_stock(stock_name: str, count: int = None) -> list:
    """
    종목명으로 뉴스를 검색해서 [{"title": str, "link": str, "pub_date": str}, ...] 반환.
    API 키가 설정되지 않은 경우 빈 리스트를 반환한다(리포트 생성은 계속 진행됨).
    """
    if not config.NAVER_CLIENT_ID or not config.NAVER_CLIENT_SECRET:
        return []

    count = count or config.NEWS_COUNT_PER_STOCK
    headers = {
        "X-Naver-Client-Id": config.NAVER_CLIENT_ID,
        "X-Naver-Client-Secret": config.NAVER_CLIENT_SECRET,
    }
    params = {"query": stock_name, "display": count, "sort": "sim"}

    resp = requests.get(config.NAVER_NEWS_API_URL, headers=headers, params=params, timeout=10)
    time.sleep(config.REQUEST_DELAY)

    if resp.status_code != 200:
        return []

    items = resp.json().get("items", [])
    return [
        {
            "title": _strip_html(item["title"]),
            "link": item["originallink"] or item["link"],
            "pub_date": item.get("pubDate", ""),
        }
        for item in items
    ]
