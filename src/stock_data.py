"""
스크리닝을 통과한 개별 종목에 대해 리포트에 필요한 세부 정보를 취합한다.
  1. 금일 거래대금 & 최근 5일 평균 거래대금
  2. 외국인/기관/개인 5일 수급
  3. 관련 주요 기사

(공매도 잔고는 현재 스크리닝/리포트에서 비활성화 상태 - screener.py 상단 설명 참고)
"""
from . import config
from . import krx_client as krx
from . import news as news_module


def build_trading_value_stats(ticker: str, date: str) -> dict:
    """금일 거래대금 및 최근 N영업일 평균 거래대금."""
    from_date = krx.n_business_days_ago(date, config.RECENT_DAYS)
    cap_history = krx.get_ohlcv(ticker, from_date, date)  # 거래량만 있으므로 시가총액 스냅샷과 별도 처리 필요시 조정

    # 거래대금은 get_market_cap_by_ticker에 일자별로 있지만, 여기서는 종목별 시계열이 필요하므로
    # OHLCV의 거래량 * 종가로 근사하지 않고, 별도 시가총액 시계열 조회 함수가 필요하면 pykrx의
    # get_market_cap(fromdate, todate, ticker)를 사용한다.
    from pykrx import stock as pykrx_stock
    cap_series = pykrx_stock.get_market_cap(from_date, date, ticker)

    if cap_series.empty:
        return {"today_value": 0, "avg_5d_value": 0}

    today_value = int(cap_series["거래대금"].iloc[-1])
    avg_5d_value = int(cap_series["거래대금"].tail(config.RECENT_DAYS).mean())
    return {"today_value": today_value, "avg_5d_value": avg_5d_value}


def build_investor_flow(ticker: str, date: str) -> dict:
    """최근 N영업일 외국인/기관/개인 순매수 거래대금 합계."""
    from_date = krx.n_business_days_ago(date, config.RECENT_DAYS)
    df = krx.get_investor_trading_value(ticker, from_date, date)

    if df.empty:
        return {"foreign": 0, "institution": 0, "individual": 0}

    recent = df.tail(config.RECENT_DAYS)
    return {
        "foreign": int(recent["외국인합계"].sum()) if "외국인합계" in recent else 0,
        "institution": int(recent["기관합계"].sum()) if "기관합계" in recent else 0,
        "individual": int(recent["개인"].sum()) if "개인" in recent else 0,
    }


def build_today_ohlc(screening_info: dict) -> dict:
    """스크리닝 단계에서 이미 가져온 OHLCV 데이터에서 당일(가장 최근 영업일) 시가/고가/저가/종가를 추출."""
    ohlcv = screening_info.get("ohlcv")
    if ohlcv is None or ohlcv.empty:
        return {"open": 0, "high": 0, "low": 0, "close": 0}

    last = ohlcv.iloc[-1]
    return {
        "open": float(last["시가"]),
        "high": float(last["고가"]),
        "low": float(last["저가"]),
        "close": float(last["종가"]),
    }


def build_stock_report_item(ticker: str, screening_info: dict, date: str) -> dict:
    """종목 하나에 대한 리포트 항목 전체를 조립."""
    name = krx.get_ticker_name(ticker)

    return {
        "ticker": ticker,
        "name": name,
        "pct_from_52w_high": screening_info["pct_from_52w_high"],
        "ohlc": build_today_ohlc(screening_info),
        "trading_value": build_trading_value_stats(ticker, date),
        "investor_flow": build_investor_flow(ticker, date),
        "news": news_module.search_news_for_stock(name),
    }
