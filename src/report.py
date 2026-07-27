"""
matplotlib으로 종목별 차트를 만들고, Jinja2 템플릿에 데이터를 채워
GitHub Pages로 배포할 정적 HTML 리포트를 생성한다.
"""
import base64
import glob
import io
import os
from datetime import datetime

import matplotlib
matplotlib.use("Agg")  # 서버(헤드리스) 환경에서 화면 없이 렌더링
import matplotlib.font_manager as fm
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from jinja2 import Environment, FileSystemLoader

from . import config


def _set_korean_font():
    """
    OS별로 흔히 쓰이는 한글 폰트 파일을 찾아서 matplotlib에 등록한다.
    (Windows: 맑은 고딕 / macOS: AppleGothic / Linux CI: 나눔고딕 - 워크플로우에서 설치)
    못 찾으면 경고만 출력하고 기본 폰트로 진행 (한글이 네모로 깨질 수 있음).
    """
    font_paths = [
        "C:/Windows/Fonts/malgun.ttf",  # Windows
        "/System/Library/Fonts/Supplemental/AppleGothic.ttf",  # macOS
        "/usr/share/fonts/truetype/nanum/NanumGothic.ttf",  # Ubuntu (GitHub Actions, apt install fonts-nanum)
        "/usr/share/fonts/truetype/nanum/NanumGothicBold.ttf",
    ]
    for path in font_paths:
        if os.path.exists(path):
            fm.fontManager.addfont(path)
            plt.rcParams["font.family"] = fm.FontProperties(fname=path).get_name()
            return
    print("[경고] 한글 폰트 파일을 찾지 못해 기본 폰트로 표시합니다 (차트의 한글이 깨질 수 있습니다).")


_set_korean_font()
plt.rcParams["axes.unicode_minus"] = False


def _fig_to_base64(fig) -> str:
    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight", dpi=110)
    plt.close(fig)
    buf.seek(0)
    return base64.b64encode(buf.read()).decode("utf-8")


def make_trading_value_chart(stock_name: str, today_value: int, avg_5d_value: int) -> str:
    """금일 거래대금 vs 5일 평균 거래대금 막대 차트 (억원 단위, base64 PNG)."""
    fig, ax = plt.subplots(figsize=(4, 3))
    labels = ["금일", "5일 평균"]
    values = [today_value / 1e8, avg_5d_value / 1e8]  # 억원 단위
    bars = ax.bar(labels, values, color=["#2563eb", "#93c5fd"])
    ax.bar_label(bars, fmt="%.0f", padding=3, fontsize=9)
    ax.set_title(f"{stock_name} 거래대금")
    ax.set_ylabel("억원")
    return _fig_to_base64(fig)


def make_investor_flow_chart(stock_name: str, flow: dict) -> str:
    """최근 5일 외국인/기관/개인 순매수 합계 막대 차트 (억원 단위, base64 PNG)."""
    fig, ax = plt.subplots(figsize=(4, 3))
    labels = ["외국인", "기관", "개인"]
    values = [flow["foreign"] / 1e8, flow["institution"] / 1e8, flow["individual"] / 1e8]
    colors = ["#dc2626" if v >= 0 else "#2563eb" for v in values]  # 국내 관행: 순매수(+) 빨강, 순매도(-) 파랑
    bars = ax.bar(labels, values, color=colors)
    ax.bar_label(bars, fmt="%.0f", padding=3, fontsize=9)
    ax.axhline(0, color="#333", linewidth=0.8)
    ax.set_title(f"{stock_name} 5일 순매수")
    ax.set_ylabel("억원")
    return _fig_to_base64(fig)


def make_candle_chart(stock_name: str, ohlc: dict) -> str:
    """금일 시가/고가/저가/종가를 하나의 캔들로 표현 (base64 PNG)."""
    o, h, l, c = ohlc["open"], ohlc["high"], ohlc["low"], ohlc["close"]
    is_up = c >= o
    color = "#dc2626" if is_up else "#2563eb"  # 국내 관행: 상승 빨강, 하락 파랑

    fig, ax = plt.subplots(figsize=(2.6, 3.4))
    ax.vlines(0, l, h, color=color, linewidth=1.5)  # 위꼬리/아래꼬리

    body_bottom = min(o, c)
    body_height = abs(c - o)
    if body_height == 0:
        body_height = max((h - l) * 0.01, 1)  # 시가=종가일 때도 몸통이 보이게 최소 높이 확보
    ax.add_patch(Rectangle((-0.18, body_bottom), 0.36, body_height, color=color))

    margin = (h - l) * 0.15 if h != l else max(h * 0.01, 1)
    ax.set_xlim(-1.3, 1.6)
    ax.set_ylim(l - margin, h + margin)
    ax.set_xticks([])
    ax.set_title(f"{stock_name} 금일 캔들", fontsize=10)
    ax.set_ylabel("가격(원)")

    labels = [("시가", o), ("고가", h), ("저가", l), ("종가", c)]
    for label, value in labels:
        ax.text(0.35, value, f"{label} {value:,.0f}", fontsize=7, va="center")

    return _fig_to_base64(fig)


def enrich_with_charts(report_items: list) -> list:
    """각 종목 리포트 항목에 base64 차트 이미지를 추가."""
    for item in report_items:
        item["trading_value_chart"] = make_trading_value_chart(
            item["name"], item["trading_value"]["today_value"], item["trading_value"]["avg_5d_value"]
        )
        item["investor_flow_chart"] = make_investor_flow_chart(item["name"], item["investor_flow"])
        item["candle_chart"] = make_candle_chart(item["name"], item["ohlc"])
    return report_items


def _update_archive_index(output_dir: str):
    """
    output_dir 안의 모든 '*_report.html'을 최신순으로 나열하는 index.html을 만든다.
    파일명이 index.html이 아니라 날짜별 파일로 바뀌면서, GitHub Pages 루트 접속 시
    보여줄 게 없어지는 문제를 방지하기 위한 간단한 아카이브 목록 페이지.
    """
    report_files = sorted(
        (os.path.basename(p) for p in glob.glob(os.path.join(output_dir, "*_report.html"))),
        reverse=True,
    )

    items_html = "\n".join(
        f'<li><a href="{fname}">{fname.replace("_report.html", "")}</a></li>' for fname in report_files
    )

    html = f"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<title>주식 테마 리포트 아카이브</title>
<style>
  body {{ font-family: -apple-system, "Malgun Gothic", sans-serif; max-width: 700px; margin: 40px auto; padding: 0 16px; color: #1f2937; }}
  h1 {{ font-size: 22px; }}
  ul {{ line-height: 2; }}
  a {{ color: #2563eb; text-decoration: none; }}
  a:hover {{ text-decoration: underline; }}
</style>
</head>
<body>
<h1>주식 테마 리포트 아카이브</h1>
<ul>
{items_html}
</ul>
</body>
</html>"""

    with open(os.path.join(output_dir, "index.html"), "w", encoding="utf-8") as f:
        f.write(html)


def render_report(date: str, theme_report: dict, stock_items: list, output_dir: str = None) -> str:
    """
    최종 HTML 리포트를 생성해서 output_dir/{date}_report.html 로 저장하고,
    전체 리포트 목록을 보여주는 output_dir/index.html도 함께 갱신한다.
    반환: 이번에 생성된 리포트 파일 경로.
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

    output_path = os.path.join(output_dir, f"{date}_report.html")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)

    _update_archive_index(output_dir)

    return output_path
