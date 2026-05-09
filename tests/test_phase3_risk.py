import pytest
import numpy as np
import pandas as pd
from analyzers.risk_metrics import calc_portfolio_risk, RISK_FREE_RATE, TRADING_DAYS


def _make_returns(n: int = 252, seed: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    data = {
        "005930.KS": rng.normal(0.0003, 0.018, n),
        "PLTR":      rng.normal(0.0008, 0.045, n),
        "AAPL":      rng.normal(0.0005, 0.022, n),
        "MSFT":      rng.normal(0.0005, 0.020, n),
        "QQQ":       rng.normal(0.0004, 0.019, n),
    }
    return pd.DataFrame(data)


def test_portfolio_risk_returns_summary():
    df = _make_returns()
    weights = np.array([0.20, 0.20, 0.20, 0.20, 0.20])
    result = calc_portfolio_risk(df, weights)
    assert result.annual_volatility > 0
    assert result.max_drawdown <= 0
    assert 0 <= result.diversification_score <= 1


def test_portfolio_volatility_decreases_with_diversification():
    df = _make_returns()
    equal_w = np.array([0.20, 0.20, 0.20, 0.20, 0.20])
    concentrated_w = np.array([0.80, 0.05, 0.05, 0.05, 0.05])
    r_equal = calc_portfolio_risk(df, equal_w)
    r_concentrated = calc_portfolio_risk(df, concentrated_w)
    assert r_concentrated.annual_volatility >= r_equal.annual_volatility


def test_correlation_matrix_shape():
    df = _make_returns()
    weights = np.ones(5) / 5
    result = calc_portfolio_risk(df, weights)
    assert result.correlation_matrix.shape == (5, 5)


def test_correlation_matrix_diagonal_is_one():
    df = _make_returns()
    weights = np.ones(5) / 5
    result = calc_portfolio_risk(df, weights)
    diag = np.diag(result.correlation_matrix.values)
    np.testing.assert_allclose(diag, np.ones(5), atol=1e-10)


def test_sharpe_ratio_computed():
    df = _make_returns()
    weights = np.ones(5) / 5
    result = calc_portfolio_risk(df, weights)
    assert result.sharpe_ratio is not None
    assert isinstance(result.sharpe_ratio, float)


def test_diversification_score_range():
    df = _make_returns()
    weights = np.ones(5) / 5
    result = calc_portfolio_risk(df, weights)
    assert 0.0 <= result.diversification_score <= 1.0
