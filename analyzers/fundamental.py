from dataclasses import dataclass
from typing import Optional
import yfinance as yf


@dataclass
class FundamentalMetrics:
    ticker: str
    per: Optional[float]        # Price-to-Earnings
    pbr: Optional[float]        # Price-to-Book
    roe: Optional[float]        # Return on Equity
    debt_to_equity: Optional[float]
    current_ratio: Optional[float]
    free_cash_flow: Optional[float]
    eps_ttm: Optional[float]
    revenue_growth_yoy: Optional[float]
    operating_margin: Optional[float]
    dividend_yield: Optional[float]


def _safe(info: dict, key: str) -> Optional[float]:
    val = info.get(key)
    if val is None or val != val:  # NaN check
        return None
    try:
        return float(val)
    except (TypeError, ValueError):
        return None


def fetch_fundamentals(ticker: str) -> Optional[FundamentalMetrics]:
    try:
        stock = yf.Ticker(ticker)
        info = stock.info

        if not info or info.get("regularMarketPrice") is None and info.get("currentPrice") is None:
            return None

        return FundamentalMetrics(
            ticker=ticker,
            per=_safe(info, "trailingPE"),
            pbr=_safe(info, "priceToBook"),
            roe=_safe(info, "returnOnEquity"),
            debt_to_equity=_safe(info, "debtToEquity"),
            current_ratio=_safe(info, "currentRatio"),
            free_cash_flow=_safe(info, "freeCashflow"),
            eps_ttm=_safe(info, "trailingEps"),
            revenue_growth_yoy=_safe(info, "revenueGrowth"),
            operating_margin=_safe(info, "operatingMargins"),
            dividend_yield=_safe(info, "dividendYield"),
        )
    except Exception as e:
        print(f"  [경고] {ticker} 재무지표 수집 실패: {e}")
        return None


def score_fundamentals(m: FundamentalMetrics) -> dict:
    scores = {}

    if m.per is not None:
        if m.per < 15:
            scores["valuation"] = "저평가"
        elif m.per < 25:
            scores["valuation"] = "적정"
        else:
            scores["valuation"] = "고평가"

    if m.roe is not None:
        scores["profitability"] = "우수" if m.roe > 0.15 else ("보통" if m.roe > 0.08 else "미흡")

    if m.debt_to_equity is not None:
        scores["leverage"] = "안전" if m.debt_to_equity < 50 else ("보통" if m.debt_to_equity < 150 else "위험")

    if m.current_ratio is not None:
        scores["liquidity"] = "안전" if m.current_ratio > 1.5 else ("보통" if m.current_ratio > 1.0 else "주의")

    return scores


def from_dict(data: dict) -> FundamentalMetrics:
    return FundamentalMetrics(**data)
