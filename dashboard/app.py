import json
import os
from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st

from analyzers.portfolio_weight import calc_weights, PortfolioWeightReport
from analyzers.risk_metrics import calc_portfolio_risk

MOCK_PATH = Path("tests/fixtures/mock_price_data.json")
PORTFOLIO_CSV = "data/portfolio.csv"
ISA_LIMIT_KRW = 4_000_000
OVERSEAS_BASIC_DEDUCTION_KRW = 2_500_000


def _load_prices() -> tuple[dict[str, float], float]:
    data = json.loads(MOCK_PATH.read_text())
    usd_krw = data["usd_to_krw"]
    prices = {t: s["current_price_krw"] for t, s in data["snapshots"].items()}
    return prices, usd_krw


def _load_mock_snapshots() -> dict:
    return json.loads(MOCK_PATH.read_text())["snapshots"]


def _make_returns_df(snapshots: dict) -> tuple[pd.DataFrame, np.ndarray]:
    np.random.seed(42)
    n = 252
    tickers = list(snapshots.keys())
    vol_map = {t: s.get("return_1y", 0.10) or 0.10 for t, s in snapshots.items()}
    data = {t: np.random.normal(0.0004, abs(vol_map[t]) / 16, n) for t in tickers}
    df = pd.DataFrame(data)
    return df, np.ones(len(tickers)) / len(tickers)


def render_tab1(report: PortfolioWeightReport, snapshots: dict):
    st.subheader("포트폴리오 현황")

    col1, col2, col3 = st.columns(3)
    col1.metric("총 평가금액", f"{report.total_value_krw:,.0f}원")
    col2.metric("보유 종목 수", len(report.holdings))
    col3.metric(
        "리밸런싱 필요",
        "⚠️ 필요" if report.rebalance_needed else "✅ 양호",
    )

    st.divider()

    col_left, col_right = st.columns(2)

    with col_left:
        st.markdown("**종목별 비중**")
        weight_data = pd.DataFrame([
            {"종목": h.ticker, "비중(%)": round(h.current_weight * 100, 1), "플래그": h.flag}
            for h in report.holdings
        ])
        st.dataframe(weight_data, use_container_width=True, hide_index=True)

    with col_right:
        st.markdown("**섹터별 비중**")
        sector_df = pd.DataFrame([
            {"섹터": k, "비중(%)": round(v * 100, 1)}
            for k, v in report.sector_weights.items()
        ]).sort_values("비중(%)", ascending=False)
        st.bar_chart(sector_df.set_index("섹터"))

    st.divider()
    st.markdown("**수익률 현황**")
    rows = []
    for h in report.holdings:
        s = snapshots.get(h.ticker, {})
        rows.append({
            "종목": h.ticker,
            "현재가(원)": f"{s.get('current_price_krw', 0):,.0f}",
            "당일등락": f"{s.get('day_change_pct', 0):+.2%}",
            "1개월": f"{s.get('return_1m', 0) or 0:+.1%}",
            "3개월": f"{s.get('return_3m', 0) or 0:+.1%}",
            "1년": f"{s.get('return_1y', 0) or 0:+.1%}",
            "52주위치": f"{s.get('week52_position_pct', 0):.0f}%",
        })
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)


def render_tab2(report: PortfolioWeightReport, snapshots: dict):
    st.subheader("종목별 진단")

    if report.rebalance_needed:
        st.warning("리밸런싱 권고 종목이 있습니다.")
        for action in report.rebalance_actions:
            st.markdown(f"- {action}")
        st.divider()

    returns_df, weights = _make_returns_df(snapshots)
    risk = calc_portfolio_risk(returns_df, weights)

    col1, col2, col3 = st.columns(3)
    col1.metric("포트폴리오 연간 변동성", f"{risk.annual_volatility:.1%}")
    col2.metric("샤프비율", f"{risk.sharpe_ratio:.2f}" if risk.sharpe_ratio else "N/A")
    col3.metric("분산화 점수", f"{risk.diversification_score:.2f} / 1.00")

    st.divider()
    st.markdown("**종목 간 상관관계**")
    corr = risk.correlation_matrix.round(2)
    st.dataframe(corr.style.background_gradient(cmap="RdYlGn_r", vmin=-1, vmax=1),
                 use_container_width=True)

    st.divider()
    for h in report.holdings:
        flag_color = "🔴" if h.flag == "과대" else ("🔵" if h.flag == "과소" else "🟢")
        with st.expander(f"{flag_color} {h.ticker} — {h.sector} | 현재 {h.current_weight:.1%} / 목표 {h.target_weight:.1%}"):
            s = snapshots.get(h.ticker, {})
            c1, c2 = st.columns(2)
            c1.metric("현재가(원)", f"{s.get('current_price_krw', 0):,.0f}")
            c1.metric("52주 위치", f"{s.get('week52_position_pct', 0):.0f}%")
            c2.metric("비중 이탈", f"{h.deviation:+.1%}")
            c2.metric("평가금액", f"{h.current_value_krw:,.0f}원")

            if h.flag != "정상":
                st.info(f"**조치**: {'일부 매도' if h.flag == '과대' else '추가 매수'} 권고")

            st.caption("AI 분석 결과를 보려면 로컬 환경에서 Claude API 키를 설정하세요.")


def render_tab3(report: PortfolioWeightReport, snapshots: dict):
    st.subheader("절세 알림")

    st.markdown("### ISA 계좌 현황")
    isa_used = 0
    isa_remaining = ISA_LIMIT_KRW - isa_used
    st.progress(isa_used / ISA_LIMIT_KRW, text=f"비과세 사용: {isa_used:,}원 / {ISA_LIMIT_KRW:,}원")
    st.metric("ISA 비과세 잔여 한도", f"{isa_remaining:,}원")
    st.caption("청년형 ISA 기준 400만원 비과세 한도 적용")

    st.divider()
    st.markdown("### 해외주식 양도소득세")

    overseas = [h for h in report.holdings if h.ticker in ("PLTR", "AAPL", "MSFT", "QQQ")]
    rows = []
    for h in overseas:
        s = snapshots.get(h.ticker, {})
        current_price = s.get("current_price", 0)
        usd_krw = 1380.0
        rows.append({
            "종목": h.ticker,
            "현재 비중": f"{h.current_weight:.1%}",
            "평가금액(원)": f"{h.current_value_krw:,.0f}",
            "비고": "매도 시 양도세 확인 필요",
        })
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    st.warning(
        f"**주의**: 해외주식 연간 실현 이익이 {OVERSEAS_BASIC_DEDUCTION_KRW:,}원 초과 시 22% 양도소득세 부과.\n\n"
        "PLTR/AAPL/MSFT 미실현 이익이 기본공제(250만원)를 초과할 가능성이 있습니다. "
        "매도 전 반드시 연간 실현 이익 합계를 확인하세요."
    )

    st.divider()
    st.markdown("### 반기 유동성 체크")
    total = report.total_value_krw
    liquid_target = 7_000_000
    cash_now = report.cash_weight * total
    st.metric("현재 현금성 자산", f"{cash_now:,.0f}원", delta=f"반기 목표 {liquid_target:,}원 대비 {cash_now - liquid_target:+,.0f}원")
    if cash_now < liquid_target:
        st.warning("반기 학비(700만원) 충당을 위해 현금 비중 확보가 필요합니다.")
    else:
        st.success("반기 유동성 목표 충족 중입니다.")


def main():
    st.set_page_config(page_title="AI 포트폴리오 진단", layout="wide")
    st.title("AI 포트폴리오 진단")
    st.caption("데이터 출처: 오프라인 mock 데이터 (로컬 실행 시 실시간 데이터 사용)")

    prices, _ = _load_prices()
    snapshots = _load_mock_snapshots()
    report = calc_weights(PORTFOLIO_CSV, prices, cash_krw=500_000)

    tab1, tab2, tab3 = st.tabs(["📊 포트폴리오 현황", "🔍 종목별 진단", "💰 절세 알림"])
    with tab1:
        render_tab1(report, snapshots)
    with tab2:
        render_tab2(report, snapshots)
    with tab3:
        render_tab3(report, snapshots)


if __name__ == "__main__":
    main()
