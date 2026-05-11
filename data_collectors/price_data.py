from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Optional

import pandas as pd
import yfinance as yf


@dataclass
class PriceSnapshot:
    ticker: str
    market: str
    current_price: float
    current_price_krw: float
    prev_close: float
    day_change_pct: float
    week52_high: float
    week52_low: float
    week52_position_pct: float  # 현재가가 52주 범위에서 몇 % 위치인지
    market_cap: Optional[float]
    return_1m: Optional[float]
    return_3m: Optional[float]
    return_1y: Optional[float]
    currency: str


def get_usd_to_krw() -> float:
    ticker = yf.Ticker("USDKRW=X")
    info = ticker.fast_info
    rate = getattr(info, "last_price", None)
    if not rate:
        raise RuntimeError("환율 조회 실패 (USDKRW=X)")
    return rate


def _calc_period_return(history: pd.DataFrame, days: int) -> Optional[float]:
    if len(history) < days:
        return None
    past_price = history["Close"].iloc[-days]
    current_price = history["Close"].iloc[-1]
    if past_price <= 0:
        return None
    return (current_price - past_price) / past_price


def fetch_price_snapshot(ticker: str, market: str, usd_to_krw: float) -> Optional[PriceSnapshot]:
    try:
        stock = yf.Ticker(ticker)
        info = stock.fast_info
        history = stock.history(period="1y")

        if history.empty:
            return None

        current_price = float(history["Close"].iloc[-1])
        prev_close = float(history["Close"].iloc[-2]) if len(history) >= 2 else current_price
        day_change_pct = (current_price - prev_close) / prev_close if prev_close > 0 else 0.0

        week52_high = float(history["Close"].max())
        week52_low = float(history["Close"].min())
        price_range = week52_high - week52_low
        week52_position = (current_price - week52_low) / price_range if price_range > 0 else 0.5

        currency = "KRW" if market == "KR" else "USD"
        current_price_krw = current_price if market == "KR" else current_price * usd_to_krw

        market_cap = getattr(info, "market_cap", None)

        return PriceSnapshot(
            ticker=ticker,
            market=market,
            current_price=current_price,
            current_price_krw=current_price_krw,
            prev_close=prev_close,
            day_change_pct=day_change_pct,
            week52_high=week52_high,
            week52_low=week52_low,
            week52_position_pct=round(week52_position * 100, 1),
            market_cap=market_cap,
            return_1m=_calc_period_return(history, 21),
            return_3m=_calc_period_return(history, 63),
            return_1y=_calc_period_return(history, 252),
            currency=currency,
        )
    except Exception as e:
        print(f"  [경고] {ticker} 데이터 조회 실패: {e}")
        return None


def fetch_all_prices(portfolio_path: str = "data/portfolio.csv") -> dict[str, PriceSnapshot]:
    df = pd.read_csv(portfolio_path)
    usd_to_krw = get_usd_to_krw()

    results: dict[str, PriceSnapshot] = {}
    for _, row in df.iterrows():
        ticker, market = row["ticker"], row["market"]
        snapshot = fetch_price_snapshot(ticker, market, usd_to_krw)
        if snapshot:
            results[ticker] = snapshot
        time.sleep(0.3)

    return results


if __name__ == "__main__":
    print("주가 데이터 수집 중...\n")
    snapshots = fetch_all_prices()

    usd_krw = get_usd_to_krw()
    print(f"현재 환율: 1 USD = {usd_krw:,.0f} KRW\n")

    print(f"{'티커':<12} {'현재가':>10} {'통화':<4} {'원화환산':>14} {'당일등락':>8} {'52주위치':>8} {'1개월':>7} {'1년':>7}")
    print("-" * 80)
    for ticker, s in snapshots.items():
        r1m = f"{s.return_1m:+.1%}" if s.return_1m is not None else "  N/A"
        r1y = f"{s.return_1y:+.1%}" if s.return_1y is not None else "  N/A"
        print(
            f"{ticker:<12} {s.current_price:>10,.2f} {s.currency:<4} "
            f"{s.current_price_krw:>14,.0f} {s.day_change_pct:>+8.2%} "
            f"{s.week52_position_pct:>7.1f}% {r1m:>7} {r1y:>7}"
        )
