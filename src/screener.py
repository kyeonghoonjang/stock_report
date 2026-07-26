"""
선정 종목 스크리닝 파이프라인.

  1) 시가총액 필터 (스냅샷 1회 호출로 전 종목 처리)
  2) 정배열 + 52주 신고가 필터 (후보군만 종목별 OHLCV 조회)

※ 공매도 잔고 필터는 현재 비활성화되어 있습니다.
  2025년 12월 KRX Data Marketplace 전환 이후 pykrx의 관련 함수가 아직 불안정해서
  (get_shorting_balance_by_ticker 호출 시 컬럼 매핑 오류 발생) 임시로 뺐습니다.
  나중에 pykrx가 업데이트되면 filter_by_short_balance()를 run_screening()에서
  다시 호출하도록 되돌리면 됩니다. 함수 자체는 아래에 그대로 남겨뒀습니다.
"""
import pandas as pd

from . import config
from . import krx_client as krx


def filter_by_market_cap(date: str) -> pd.DataFrame:
    """시가총액 3천억~10조 필터. 반환: 티커를 index로 하는 DataFrame."""
    cap_df = krx.get_market_cap_snapshot(date)
    mask = cap_df["시가총액"].between(config.MARKET_CAP_MIN, config.MARKET_CAP_MAX)
    return cap_df[mask].copy()


def _is_bullish_alignment(ohlcv: pd.DataFrame) -> bool:
    """종가 > MA5 > MA20 > MA60 > MA120 여부 (최근 영업일 기준)."""
    if len(ohlcv) < max(config.MA_WINDOWS) + 5:
        return False

    close = ohlcv["종가"]
    mas = [close.rolling(w).mean().iloc[-1] for w in config.MA_WINDOWS]
    last_close = close.iloc[-1]

    values = [last_close] + mas
    return all(values[i] > values[i + 1] for i in range(len(values) - 1))


def _near_or_breaking_52w_high(ohlcv: pd.DataFrame) -> tuple[bool, float]:
    """
    52주(약 252영업일) 신고가 대비 위치를 계산.
    반환: (조건 충족 여부, 52주 고가 대비 등락률 %)
    조건: 등락률이 -NEAR_52W_HIGH_PCT% 이상 (즉 -2% 이내이거나 신고가 돌파)
    """
    window = ohlcv.tail(252)
    if window.empty:
        return False, 0.0

    high_52w = window["고가"].max()
    last_close = ohlcv["종가"].iloc[-1]
    pct_from_high = (last_close - high_52w) / high_52w * 100
    return pct_from_high >= -config.NEAR_52W_HIGH_PCT, pct_from_high


def filter_by_chart_pattern(tickers: list, date: str) -> dict:
    """
    정배열 + 52주 신고가 조건을 만족하는 티커만 남긴다.
    반환: {티커: {"ohlcv": df, "pct_from_52w_high": float}}
    """
    from_date = krx.n_business_days_ago(date, config.LOOKBACK_DAYS_OHLCV)
    passed = {}

    for ticker in tickers:
        ohlcv = krx.get_ohlcv(ticker, from_date, date)
        if ohlcv.empty:
            continue

        if not _is_bullish_alignment(ohlcv):
            continue

        ok, pct = _near_or_breaking_52w_high(ohlcv)
        if not ok:
            continue

        passed[ticker] = {"ohlcv": ohlcv, "pct_from_52w_high": pct}

    return passed


def filter_by_short_balance(tickers: list, date: str) -> dict:
    """
    공매도 잔고 비중 10% 이하만 남긴다.
    날짜 하루치 전종목 스냅샷을 한 번만 조회해서 후보 티커들과 대조한다.
    반환: {티커: 공매도잔고비중(float, %) 또는 None(조회 실패/데이터 없음)}

    주의: 2025년 12월 KRX Data Marketplace 전환 이후 pykrx의 공매도 관련 함수가
    아직 불안정하다(2026년 2월 기준 관련 오픈 이슈 다수). 조회 자체가 실패하면
    전체 파이프라인을 죽이지 않고, 해당 조건은 '확인 불가'로 처리해 통과시킨다.
    """
    try:
        snapshot = krx.get_shorting_balance_snapshot(date)
    except Exception as e:
        print(f"[경고] 공매도 잔고 스냅샷 조회 실패 (pykrx 라이브러리 이슈 가능성): {e}")
        print("       -> 이 조건은 '확인 불가'로 표시하고 나머지 후보는 그대로 통과시킵니다.")
        return {ticker: None for ticker in tickers}

    passed = {}
    for ticker in tickers:
        if ticker not in snapshot.index:
            # 공매도 데이터가 없는 종목(=거래 자체가 없거나 조회 불가)은 조건 충족으로 간주하지 않고 제외
            continue

        try:
            short_pct = float(snapshot.loc[ticker, "비중"])
        except (TypeError, ValueError):
            passed[ticker] = None
            continue

        if short_pct <= config.SHORT_BALANCE_MAX_PCT:
            passed[ticker] = short_pct

    return passed


def run_screening(date: str) -> dict:
    """
    전체 스크리닝 파이프라인 실행.
    반환: {티커: {"ohlcv": df, "pct_from_52w_high": float}}
    (공매도 필터는 현재 비활성화 상태 - 모듈 상단 설명 참고)
    """
    cap_df = filter_by_market_cap(date)
    cap_candidates = list(cap_df.index)
    print(f"[1/2] 시가총액 필터 통과: {len(cap_candidates)}종목")

    chart_candidates = filter_by_chart_pattern(cap_candidates, date)
    print(f"[2/2] 정배열+52주가 필터 통과: {len(chart_candidates)}종목")

    return chart_candidates
