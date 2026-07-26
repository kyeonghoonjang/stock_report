"""
pykrx 호출을 감싸는 래퍼 모듈.
- 원본 pykrx 함수 이름/시그니처가 바뀌더라도 이 파일만 고치면 되도록 격리.
"""
import time
from datetime import datetime, timedelta

import pandas as pd
from pykrx import stock

from . import config


def get_latest_business_date() -> str:
    """가장 최근 영업일(YYYYMMDD)을 반환. 장중이면 전일 기준일 수 있음."""
    today = datetime.now().strftime("%Y%m%d")
    return stock.get_nearest_business_day_in_a_week(today)


def get_kospi_tickers(date: str) -> list:
    """코스피 전 종목 티커 리스트."""
    return stock.get_market_ticker_list(date, market=config.MARKET)


def get_ticker_name(ticker: str) -> str:
    return stock.get_market_ticker_name(ticker)


def get_market_cap_snapshot(date: str) -> pd.DataFrame:
    """
    해당 일자 코스피 전 종목의 시가총액/거래량/거래대금/상장주식수 스냅샷.
    index: 티커, columns: 종가, 시가총액, 거래량, 거래대금, 상장주식수
    """
    df = stock.get_market_cap_by_ticker(date, market=config.MARKET)
    time.sleep(config.REQUEST_DELAY)
    return df


def get_ohlcv(ticker: str, from_date: str, to_date: str) -> pd.DataFrame:
    """개별 종목 일봉 OHLCV."""
    df = stock.get_market_ohlcv_by_date(from_date, to_date, ticker)
    time.sleep(config.REQUEST_DELAY)
    return df


def get_shorting_balance_snapshot(date: str) -> pd.DataFrame:
    """
    해당 일자 코스피 전 종목의 공매도 잔고 스냅샷 (티커를 index로 하는 DataFrame).
    columns: 공매도잔고, 상장주식수, 공매도금액, 시가총액, 비중
    (2026년 초 pykrx 업데이트로 get_shorting_balance_by_ticker의 시그니처가
     '종목별 기간 조회'에서 '날짜별 전종목 스냅샷'으로 변경되었다.)
    """
    df = stock.get_shorting_balance_by_ticker(date, market=config.MARKET)
    time.sleep(config.REQUEST_DELAY)
    return df


def get_investor_trading_value(ticker: str, from_date: str, to_date: str) -> pd.DataFrame:
    """
    개별 종목의 투자자별(외국인/기관/개인 등) 순매수 거래대금 시계열.
    columns: 금융투자, 보험, 투신, ... 기관합계, 기타법인, 개인, 외국인합계, 전체
    """
    df = stock.get_market_trading_value_by_date(from_date, to_date, ticker)
    time.sleep(config.REQUEST_DELAY)
    return df


def n_business_days_ago(date: str, n: int) -> str:
    """대략적인 조회 시작일 계산용 (여유를 두고 달력일 기준으로 역산)."""
    d = datetime.strptime(date, "%Y%m%d") - timedelta(days=int(n * 1.6) + 5)
    return d.strftime("%Y%m%d")
