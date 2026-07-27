"""
데모 리포트 파이프라인 실행 진입점.

실행:
    python main.py
    python main.py --date 20260724   # 특정 영업일 기준으로 실행(테스트용)
"""
import argparse
import sys
import traceback

from src import krx_client as krx
from src import screener
from src import stock_data
from src import theme as theme_module
from src import report


def run(date: str = None):
    date = date or krx.get_latest_business_date()
    print(f"=== {date} 기준 리포트 생성 시작 ===")

    # 1. 테마 리포트 (실패해도 종목 리포트는 계속 진행)
    try:
        theme_report = theme_module.get_theme_report(date)
        print(f"주도 테마: {theme_report['theme']['name']} ({theme_report['theme']['change_pct']}%)")
    except Exception:
        print("[경고] 테마 리포트 생성 실패 (네이버 페이지 구조 변경 가능성). 건너뜁니다.")
        traceback.print_exc()
        theme_report = None

    # 2. 종목 스크리닝
    screened = screener.run_screening(date)
    if not screened:
        print("조건을 만족하는 종목이 없습니다.")

    # 3. 종목별 상세 리포트 데이터 취합
    stock_items = []
    for ticker, info in screened.items():
        try:
            item = stock_data.build_stock_report_item(ticker, info, date)
            stock_items.append(item)
            print(f"  - {item['name']} 리포트 데이터 취합 완료")
        except Exception:
            print(f"  - {ticker} 리포트 데이터 취합 실패, 건너뜁니다.")
            traceback.print_exc()

    # 4. 차트 생성 + HTML 리포트 렌더링
    stock_items = report.enrich_with_charts(stock_items)
    output_path = report.render_report(date, theme_report, stock_items)

    print(f"=== 리포트 생성 완료: {output_path} ===")
    return output_path


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", default=None, help="YYYYMMDD 형식의 기준일 (미지정시 최근 영업일)")
    args = parser.parse_args()

    try:
        run(args.date)
    except Exception:
        traceback.print_exc()
        sys.exit(1)
