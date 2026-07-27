"""
NAVER API HUB(네이버 클라우드 플랫폼)의 뉴스 검색 API로 종목 관련 주요 기사를 검색한다.
https://www.ncloud.com 콘솔 > NAVER API HUB > Application 등록 후
API Gateway 키(Key ID / Key)를 발급받을 수 있다.

당일 리포트 특성상 오래된 기사보다는 최근 기사가 더 유용하므로,
넉넉히 가져온 뒤 최근 N일 이내로 걸러서 최신순으로 상위 몇 개만 사용한다.
"""
import re
import time
from datetime import datetime, timedelta
from email.utils import parsedate_to_datetime

import requests

from . import config

# 관련도순으로 넉넉히 가져온 뒤, 그중 최근 기사만 추려낸다.
FETCH_MULTIPLIER = 4
RECENCY_WINDOW_DAYS = 3


def _strip_html(text: str) -> str:
    return re.sub(r"<[^>]+>", "", text)
    

def _parse_pub_date(pub_date_str: str):
    """네이버 API의 RFC 822 형식 pubDate 문자열을 datetime으로 변환. 실패 시 None."""
    try:
        return parsedate_to_datetime(pub_date_str)
    except (TypeError, ValueError):
        return None


def search_news_for_stock(stock_name: str, count: int = None) -> list:
    """
    종목명으로 뉴스를 검색해서 [{"title": str, "link": str, "pub_date": str, "pub_date_display": str}, ...] 반환.
    - 최근 RECENCY_WINDOW_DAYS일 이내 기사를 우선하고, 그 안에서 최신순으로 정렬.
    - 최근 기사가 하나도 없으면(비인기 종목 등) 관련도 상위 기사로 대체.
    - API 키가 설정되지 않은 경우 빈 리스트를 반환한다(리포트 생성은 계속 진행됨).
    """
    if not config.NAVER_API_KEY_ID or not config.NAVER_API_KEY:
        return []

    count = count or config.NEWS_COUNT_PER_STOCK
    headers = {
        "X-NCP-APIGW-API-KEY-ID": config.NAVER_API_KEY_ID,
        "X-NCP-APIGW-API-KEY": config.NAVER_API_KEY,
    }
    # 나중에 최근순으로 다시 정렬/필터링할 것이므로 여유 있게 더 많이 가져온다.
    params = {
        "query": stock_name,
        "display": min(count * FETCH_MULTIPLIER, 100),
        "sort": "sim",
        "format": "json",
    }

    resp = requests.get(config.NAVER_NEWS_API_URL, headers=headers, params=params, timeout=10)
    time.sleep(config.REQUEST_DELAY)

    if resp.status_code != 200:
        print(f"[뉴스 API 오류] status={resp.status_code}, body={resp.text[:300]}")
        return []

    raw_items = resp.json().get("items", [])
    articles = []
    for item in raw_items:
        pub_dt = _parse_pub_date(item.get("pubDate", ""))
        articles.append({
            "title": _strip_html(item["title"]),
            "link": item["originallink"] or item["link"],
            "pub_date": item.get("pubDate", ""),
            "pub_dt": pub_dt,
        })

    cutoff = datetime.now(tz=articles[0]["pub_dt"].tzinfo) - timedelta(days=RECENCY_WINDOW_DAYS) if articles and articles[0]["pub_dt"] else None
    recent = [a for a in articles if a["pub_dt"] and cutoff and a["pub_dt"] >= cutoff]
    recent.sort(key=lambda a: a["pub_dt"], reverse=True)

    selected = recent[:count] if recent else articles[:count]

    return [
        {
            "title": a["title"],
            "link": a["link"],
            "pub_date": a["pub_date"],
            "pub_date_display": a["pub_dt"].strftime("%m/%d %H:%M") if a["pub_dt"] else "",
        }
        for a in selected
    ]
