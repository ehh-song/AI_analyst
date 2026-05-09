import pytest
from unittest.mock import patch, MagicMock
from analyzers.fundamental import (
    fetch_fundamentals, score_fundamentals, from_dict, FundamentalMetrics
)


def _mock_info(**kwargs):
    defaults = {
        "regularMarketPrice": 198.5,
        "trailingPE": 29.5,
        "priceToBook": 45.2,
        "returnOnEquity": 0.171,
        "debtToEquity": 180.0,
        "currentRatio": 0.95,
        "freeCashflow": 108_000_000_000,
        "trailingEps": 6.43,
        "revenueGrowth": 0.041,
        "operatingMargins": 0.311,
        "dividendYield": 0.005,
    }
    defaults.update(kwargs)
    mock = MagicMock()
    mock.info = defaults
    return mock


def test_fetch_fundamentals_returns_metrics():
    with patch("analyzers.fundamental.yf.Ticker", return_value=_mock_info()):
        m = fetch_fundamentals("AAPL")
    assert m is not None
    assert m.ticker == "AAPL"
    assert m.per == pytest.approx(29.5)
    assert m.roe == pytest.approx(0.171)


def test_fetch_fundamentals_handles_none_values():
    with patch("analyzers.fundamental.yf.Ticker", return_value=_mock_info(trailingPE=None, priceToBook=None)):
        m = fetch_fundamentals("AAPL")
    assert m is not None
    assert m.per is None
    assert m.pbr is None


def test_fetch_fundamentals_returns_none_on_empty_info():
    mock = MagicMock()
    mock.info = {}
    with patch("analyzers.fundamental.yf.Ticker", return_value=mock):
        result = fetch_fundamentals("INVALID")
    assert result is None


def test_fetch_fundamentals_handles_exception():
    with patch("analyzers.fundamental.yf.Ticker", side_effect=Exception("network")):
        result = fetch_fundamentals("AAPL")
    assert result is None


def test_score_valuation_undervalued():
    m = FundamentalMetrics("X", per=12.0, pbr=None, roe=None, debt_to_equity=None,
                           current_ratio=None, free_cash_flow=None, eps_ttm=None,
                           revenue_growth_yoy=None, operating_margin=None, dividend_yield=None)
    scores = score_fundamentals(m)
    assert scores["valuation"] == "저평가"


def test_score_valuation_overvalued():
    m = FundamentalMetrics("X", per=35.0, pbr=None, roe=None, debt_to_equity=None,
                           current_ratio=None, free_cash_flow=None, eps_ttm=None,
                           revenue_growth_yoy=None, operating_margin=None, dividend_yield=None)
    scores = score_fundamentals(m)
    assert scores["valuation"] == "고평가"


def test_score_leverage_safe():
    m = FundamentalMetrics("X", per=None, pbr=None, roe=None, debt_to_equity=30.0,
                           current_ratio=None, free_cash_flow=None, eps_ttm=None,
                           revenue_growth_yoy=None, operating_margin=None, dividend_yield=None)
    scores = score_fundamentals(m)
    assert scores["leverage"] == "안전"


def test_from_dict_roundtrip():
    data = {
        "ticker": "MSFT", "per": 35.1, "pbr": 13.2, "roe": 0.38,
        "debt_to_equity": 42.0, "current_ratio": 1.7, "free_cash_flow": 70e9,
        "eps_ttm": 11.5, "revenue_growth_yoy": 0.16, "operating_margin": 0.43,
        "dividend_yield": 0.007,
    }
    m = from_dict(data)
    assert m.ticker == "MSFT"
    assert m.per == 35.1
