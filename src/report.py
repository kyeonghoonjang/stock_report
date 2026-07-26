"""
matplotlib으로 종목별 차트를 만들고, Jinja2 템플릿에 데이터를 채워
GitHub Pages로 배포할 정적 HTML 리포트를 생성한다.
"""
import base64
import io
import os
from datetime import datetime

import matplotlib
matplotlib.use("Agg")  # 서버(헤드리스) 환경에서 화면 없이 렌더링
import matplotlib.pyplot as plt
from jinja2 import Environment, FileSystemLoader

from . import config

# 한글 폰트가 없는 CI 환경에서도 깨지지 않도록 폰트 미지정 시 기본값 사용.
# 필요하면 워크플로우에서 나눔고딕 등을 설치하고 여기에 rcParams로 지정한다.
plt.rcParams["axes.unicode_minus"] = False


def _fig_to_base64(fig) -> str:
    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight", dpi=110)
    plt.close(fig)
    buf.seek(0)
    return base64.b64encode(buf.read()).decode("utf-8")


def make_trading_value_chart(stock_name: str, today_value: int, avg_5d_value: int) -> str:
    """금일 거래대금 vs 5일 평균 거래대금 막대 차트 (base64 PNG)."""
    fig, ax = plt.subplots(figsize=(4, 3))
    labels = ["today", "5d_avg"]
    values = [today_value / 1e8, avg_5d_value / 1e8]  # 억원 단위
    ax.bar(labels, values, color=["#2563eb", "#93c5fd"])
    ax.set_title(f"{stock_name} trading value (100M KRW)")
    ax.set_ylabel("100M KRW")
    return _fig_to_base64(fig)


def make_investor_flow_chart(stock_name: str, flow: dict) -> str:
    """최근 5일 외국인/기관/개인 순매수 합계 막대 차트 (base64 PNG)."""
    fig, ax = plt.subplots(figsize=(4, 3))
    labels = ["foreign", "institution", "individual"]
    values = [flow["foreign"] / 1e8, flow["institution"] / 1e8, flow["individual"] / 1e8]
    colors = ["#16a34a" if v >= 0 else "#dc2626" for v in values]
    ax.bar(labels, values, color=colors)
    ax.axhline(0, color="#333", linewidth=0.8)
    ax.set_title(f"{stock_name} 5d net buy (100M KRW)")
    ax.set_ylabel("100M KRW")
    return _fig_to_base64(fig)


def enrich_with_charts(report_items: list) -> list:
    """각 종목 리포트 항목에 base64 차트 이미지를 추가."""
    for item in report_items:
        item["trading_value_chart"] = make_trading_value_chart(
            item["name"], item["trading_value"]["today_value"], item["trading_value"]["avg_5d_value"]
        )
        item["investor_flow_chart"] = make_investor_flow_chart(item["name"], item["investor_flow"])
    return report_items


def render_report(date: str, theme_report: dict, stock_items: list, output_dir: str = None) -> str:
    """
    최종 HTML 리포트를 생성해서 output_dir/index.html 로 저장.
    반환: 저장된 파일 경로.
    """
    output_dir = output_dir or config.OUTPUT_DIR
    os.makedirs(output_dir, exist_ok=True)

    template_dir = os.path.join(os.path.dirname(__file__), "..", "templates")
    env = Environment(loader=FileSystemLoader(template_dir))
    template = env.get_template("report_template.html")

    html = template.render(
        date=date,
        generated_at=datetime.now().strftime("%Y-%m-%d %H:%M"),
        theme_report=theme_report,
        stocks=stock_items,
    )

    output_path = os.path.join(output_dir, "index.html")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)

    return output_path
