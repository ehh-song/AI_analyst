import pytest
from unittest.mock import patch, MagicMock
import pandas as pd
import numpy as np

from data_collectors.price_data import (
    fetch_price_snapshot,
    fetch_all_prices,
    _calc_period_return,
    PriceSnapshot,
)

USD_TO_KRW = 1380.0


def _make_history(days: int = 300, start_price: float = 100.0) -> pd.DataFrame:
    prices = [start_price * (1 + 0.001 * i) for i in range(days)]
    return pd.DataFrame({"Close": prices, "Volume": [1_000_000] * days})


def _mock_ticker(history: pd.DataFrame, market_cap: float = 1e12):
    mock = MagicMock()
    mock.history.return_value = history
    mock.fast_info.market_cap = market_cap
    return mock


def test_calc_period_return_normal():
    history = _make_history(300, 100.0)
    result = _calc_period_return(history, 21)
    assert result is not None
    assert -1.0 < result < 10.0


def test_calc_period_return_insufficient_data():
    history = _make_history(10, 100.0)
    assert _calc_period_return(history, 21) is None


def test_fetch_price_snapshot_us_stock():
    history = _make_history(300, 200.0)
    with patch("data_collectors.price_data.yf.Ticker", return_value=_mock_ticker(history)):
        snapshot = fetch_price_snapshot("AAPL", "US", USD_TO_KRW)

    assert snapshot is not None
    assert snapshot.ticker == "AAPL"
    assert snapshot.currency == "USD"
    assert snapshot.current_price_krw == pytest.approx(snapshot.current_price * USD_TO_KRW)
    assert 0 <= snapshot.week52_position_pct <= 100


def test_fetch_price_snapshot_kr_stock():
    history = _make_history(300, 70000.0)
    with patch("data_collectors.price_data.yf.Ticker", return_value=_mock_ticker(history)):
        snapshot = fetch_price_snapshot("005930.KS", "KR", USD_TO_KRW)

    assert snapshot is not None
    assert snapshot.currency == "KRW"
    assert snapshot.current_price_krw == pytest.approx(snapshot.current_price)


def test_fetch_price_snapshot_returns_none_on_empty_history():
    mock = MagicMock()
    mock.history.return_value = pd.DataFrame()
    mock.fast_info.market_cap = None
    with patch("data_collectors.price_data.yf.Ticker", return_value=mock):
        result = fetch_price_snapshot("INVALID", "US", USD_TO_KRW)
    assert result is None


def test_fetch_price_snapshot_handles_exception_gracefully():
    with patch("data_collectors.price_data.yf.Ticker", side_effect=Exception("network error")):
        result = fetch_price_snapshot("AAPL", "US", USD_TO_KRW)
    assert result is None


def test_fetch_all_prices_returns_dict(tmp_path):
    csv = tmp_path / "portfolio.csv"
    csv.write_text("ticker,market,shares,avg_price,avg_price_currency,account_type,asset_class\n"
                   "AAPL,US,10,145.0,USD,일반,stock\n")

    history = _make_history(300, 180.0)
    with patch("data_collectors.price_data.yf.Ticker", return_value=_mock_ticker(history)), \
         patch("data_collectors.price_data.get_usd_to_krw", return_value=USD_TO_KRW):
        results = fetch_all_prices(str(csv))

    assert "AAPL" in results
    assert isinstance(results["AAPL"], PriceSnapshot)


def test_week52_position_at_max():
    days = 252
    prices = list(range(1, days + 1))
    history = pd.DataFrame({"Close": prices, "Volume": [1_000_000] * days})
    mock = _mock_ticker(history)
    with patch("data_collectors.price_data.yf.Ticker", return_value=mock):
        snapshot = fetch_price_snapshot("TEST", "US", USD_TO_KRW)
    assert snapshot.week52_position_pct == 100.0
