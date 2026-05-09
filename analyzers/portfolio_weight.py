from dataclasses import dataclass, field
from typing import Optional
import pandas as pd


SECTOR_MAP = {
    "005930.KS": "반도체",
    "PLTR":      "AI·소프트웨어",
    "AAPL":      "빅테크",
    "MSFT":      "빅테크",
    "QQQ":       "ETF·나스닥",
}

TARGET_WEIGHTS = {
    "005930.KS": 0.15,
    "PLTR":      0.15,
    "AAPL":      0.15,
    "MSFT":      0.15,
    "QQQ":       0.20,
    "_CASH":     0.20,
}

REBALANCE_THRESHOLD = 0.05  # 목표 대비 ±5% 초과 시 리밸런싱 권고


@dataclass
class HoldingWeight:
    ticker: str
    sector: str
    current_value_krw: float
    current_weight: float
    target_weight: float
    deviation: float            # current - target
    flag: str                   # "과대" / "과소" / "정상"


@dataclass
class PortfolioWeightReport:
    total_value_krw: float
    holdings: list[HoldingWeight]
    sector_weights: dict[str, float]
    cash_weight: float
    rebalance_needed: bool
    rebalance_actions: list[str]  # 자연어 액션 리스트


def calc_weights(
    portfolio_csv: str,
    price_krw: dict[str, float],
    cash_krw: float = 0,
) -> PortfolioWeightReport:
    df = pd.read_csv(portfolio_csv)

    values: dict[str, float] = {}
    for _, row in df.iterrows():
        ticker = row["ticker"]
        price = price_krw.get(ticker)
        if price is None:
            continue
        values[ticker] = float(row["shares"]) * price

    total = sum(values.values()) + cash_krw
    if total <= 0:
        raise ValueError("포트폴리오 총액이 0입니다")

    holdings = []
    for ticker, value in values.items():
        current_w = value / total
        target_w = TARGET_WEIGHTS.get(ticker, 0.0)
        deviation = current_w - target_w

        if deviation > REBALANCE_THRESHOLD:
            flag = "과대"
        elif deviation < -REBALANCE_THRESHOLD:
            flag = "과소"
        else:
            flag = "정상"

        holdings.append(HoldingWeight(
            ticker=ticker,
            sector=SECTOR_MAP.get(ticker, "기타"),
            current_value_krw=value,
            current_weight=current_w,
            target_weight=target_w,
            deviation=deviation,
            flag=flag,
        ))

    holdings.sort(key=lambda h: h.current_weight, reverse=True)

    sector_weights: dict[str, float] = {}
    for h in holdings:
        sector_weights[h.sector] = sector_weights.get(h.sector, 0.0) + h.current_weight

    cash_weight = cash_krw / total

    actions = _generate_actions(holdings, total, cash_weight)
    rebalance_needed = any(h.flag != "정상" for h in holdings)

    return PortfolioWeightReport(
        total_value_krw=total,
        holdings=holdings,
        sector_weights=sector_weights,
        cash_weight=cash_weight,
        rebalance_needed=rebalance_needed,
        rebalance_actions=actions,
    )


def _generate_actions(
    holdings: list[HoldingWeight],
    total: float,
    cash_weight: float,
) -> list[str]:
    actions = []
    for h in holdings:
        if h.flag == "정상":
            continue
        diff_krw = abs(h.deviation) * total
        direction = "일부 매도" if h.flag == "과대" else "추가 매수"
        actions.append(
            f"{h.ticker} ({h.sector}): {direction} — "
            f"현재 {h.current_weight:.1%} → 목표 {h.target_weight:.1%} "
            f"(약 {diff_krw:,.0f}원)"
        )

    target_cash = TARGET_WEIGHTS.get("_CASH", 0.20)
    cash_dev = cash_weight - target_cash
    if cash_dev < -REBALANCE_THRESHOLD:
        actions.append(
            f"현금 비중 부족: 현재 {cash_weight:.1%} → 목표 {target_cash:.1%} "
            f"(약 {abs(cash_dev) * total:,.0f}원 확보 권장)"
        )

    return actions
