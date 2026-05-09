from dataclasses import dataclass
from typing import Optional
import numpy as np
import pandas as pd
import yfinance as yf


TRADING_DAYS = 252
RISK_FREE_RATE = 0.035  # 한국 3년 국채 기준


@dataclass
class RiskMetrics:
    ticker: str
    annual_volatility: float
    sharpe_ratio: Optional[float]
    max_drawdown: float
    beta: Optional[float]
    var_95: float           # 95% 신뢰구간 일간 VaR


@dataclass
class PortfolioRiskSummary:
    annual_volatility: float
    sharpe_ratio: Optional[float]
    max_drawdown: float
    correlation_matrix: pd.DataFrame
    diversification_score: float    # 0~1, 높을수록 분산 잘 됨


def _returns(prices: pd.Series) -> pd.Series:
    return prices.pct_change().dropna()


def calc_ticker_risk(ticker: str, period: str = "1y") -> Optional[RiskMetrics]:
    try:
        hist = yf.Ticker(ticker).history(period=period)
        if hist.empty or len(hist) < 20:
            return None

        rets = _returns(hist["Close"])
        annual_vol = float(rets.std() * np.sqrt(TRADING_DAYS))
        mean_return = float(rets.mean() * TRADING_DAYS)
        sharpe = (mean_return - RISK_FREE_RATE) / annual_vol if annual_vol > 0 else None

        cum = (1 + rets).cumprod()
        rolling_max = cum.cummax()
        drawdown = (cum - rolling_max) / rolling_max
        max_dd = float(drawdown.min())

        var_95 = float(np.percentile(rets, 5))

        spy = yf.Ticker("SPY").history(period=period)
        beta = None
        if not spy.empty:
            spy_rets = _returns(spy["Close"])
            aligned = pd.concat([rets, spy_rets], axis=1).dropna()
            if len(aligned) > 10:
                cov = np.cov(aligned.iloc[:, 0], aligned.iloc[:, 1])
                beta = float(cov[0, 1] / cov[1, 1]) if cov[1, 1] != 0 else None

        return RiskMetrics(
            ticker=ticker,
            annual_volatility=annual_vol,
            sharpe_ratio=sharpe,
            max_drawdown=max_dd,
            beta=beta,
            var_95=var_95,
        )
    except Exception as e:
        print(f"  [경고] {ticker} 리스크 계산 실패: {e}")
        return None


def calc_portfolio_risk(
    returns_df: pd.DataFrame,
    weights: np.ndarray,
) -> PortfolioRiskSummary:
    corr = returns_df.corr()
    cov = returns_df.cov() * TRADING_DAYS

    port_var = float(weights @ cov.values @ weights)
    port_vol = float(np.sqrt(port_var))
    port_mean = float((returns_df.mean() * TRADING_DAYS) @ weights)
    sharpe = (port_mean - RISK_FREE_RATE) / port_vol if port_vol > 0 else None

    cum = (1 + returns_df @ weights).cumprod()
    rolling_max = cum.cummax()
    max_dd = float(((cum - rolling_max) / rolling_max).min())

    upper = corr.values[np.triu_indices_from(corr.values, k=1)]
    avg_corr = float(np.mean(upper)) if len(upper) > 0 else 0.0
    diversification = round(1 - avg_corr, 3)

    return PortfolioRiskSummary(
        annual_volatility=port_vol,
        sharpe_ratio=sharpe,
        max_drawdown=max_dd,
        correlation_matrix=corr,
        diversification_score=diversification,
    )


def build_returns_df(tickers: list[str], period: str = "1y") -> pd.DataFrame:
    frames = {}
    for ticker in tickers:
        try:
            hist = yf.Ticker(ticker).history(period=period)
            if not hist.empty:
                frames[ticker] = _returns(hist["Close"])
        except Exception:
            pass
    if not frames:
        return pd.DataFrame()
    return pd.DataFrame(frames).dropna()
