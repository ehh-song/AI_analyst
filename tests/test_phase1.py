import os
import pandas as pd
import pytest
from unittest.mock import patch


REQUIRED_ENV_VARS = [
    "ANTHROPIC_API_KEY",
    "FRED_API_KEY",
    "SEC_EDGAR_USER_AGENT",
]

PORTFOLIO_REQUIRED_COLUMNS = [
    "ticker", "market", "shares", "avg_price",
    "avg_price_currency", "account_type", "asset_class",
]


def test_env_file_example_exists():
    assert os.path.exists(".env.example"), ".env.example 파일이 없습니다"


def test_portfolio_csv_exists():
    assert os.path.exists("data/portfolio.csv"), "data/portfolio.csv 파일이 없습니다"


def test_portfolio_csv_columns():
    df = pd.read_csv("data/portfolio.csv")
    for col in PORTFOLIO_REQUIRED_COLUMNS:
        assert col in df.columns, f"portfolio.csv에 '{col}' 컬럼이 없습니다"


def test_portfolio_csv_no_empty_tickers():
    df = pd.read_csv("data/portfolio.csv")
    assert df["ticker"].notna().all(), "ticker에 빈 값이 있습니다"


def test_portfolio_csv_positive_shares():
    df = pd.read_csv("data/portfolio.csv")
    assert (df["shares"] > 0).all(), "shares는 0보다 커야 합니다"


def test_portfolio_csv_market_values():
    df = pd.read_csv("data/portfolio.csv")
    valid_markets = {"KR", "US"}
    assert set(df["market"].unique()).issubset(valid_markets), \
        f"market 값은 {valid_markets} 중 하나여야 합니다"


def test_config_loads_with_valid_env():
    mock_env = {
        "ANTHROPIC_API_KEY": "test-key",
        "FRED_API_KEY": "test-fred-key",
        "SEC_EDGAR_USER_AGENT": "test@example.com",
    }
    with patch.dict(os.environ, mock_env):
        from config.settings import load_config
        config = load_config()
        assert config.api.anthropic_key == "test-key"
        assert config.investor.age == 26
        assert config.investor.target_annual_return == 0.07
        assert config.investor.isa_nontaxable_limit_krw == 4_000_000


def test_config_raises_on_missing_env():
    with patch.dict(os.environ, {}, clear=True):
        from config.settings import load_config
        with pytest.raises(EnvironmentError):
            load_config()


def test_investor_profile_defaults():
    from config.settings import InvestorProfile
    profile = InvestorProfile()
    assert profile.max_single_stock_weight == 0.25
    assert "gambling" in profile.excluded_sectors
    assert "energy" in profile.preferred_sectors
    assert profile.has_isa is True
    assert profile.overseas_basic_deduction_krw == 2_500_000
