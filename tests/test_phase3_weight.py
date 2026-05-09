import pytest
import os
from analyzers.portfolio_weight import calc_weights, HoldingWeight


PRICE_KRW = {
    "005930.KS": 58400,
    "PLTR":      167670,
    "AAPL":      273971,
    "MSFT":      597222,
    "QQQ":       650284,
}


def test_calc_weights_sum_to_one(tmp_path):
    csv = tmp_path / "p.csv"
    csv.write_text(
        "ticker,market,shares,avg_price,avg_price_currency,account_type,asset_class\n"
        "005930.KS,KR,100,70000,KRW,ISA,stock\n"
        "PLTR,US,50,10.5,USD,일반,stock\n"
        "AAPL,US,10,145.0,USD,일반,stock\n"
        "MSFT,US,8,280.0,USD,일반,stock\n"
        "QQQ,US,5,320.0,USD,일반,etf\n"
    )
    report = calc_weights(str(csv), PRICE_KRW, cash_krw=0)
    total_w = sum(h.current_weight for h in report.holdings)
    assert total_w == pytest.approx(1.0, abs=1e-6)


def test_calc_weights_total_value(tmp_path):
    csv = tmp_path / "p.csv"
    csv.write_text(
        "ticker,market,shares,avg_price,avg_price_currency,account_type,asset_class\n"
        "AAPL,US,10,145.0,USD,일반,stock\n"
    )
    report = calc_weights(str(csv), {"AAPL": 200000}, cash_krw=500000)
    assert report.total_value_krw == pytest.approx(2_500_000)


def test_deviation_flag_overweight(tmp_path):
    csv = tmp_path / "p.csv"
    csv.write_text(
        "ticker,market,shares,avg_price,avg_price_currency,account_type,asset_class\n"
        "005930.KS,KR,1000,70000,KRW,ISA,stock\n"
        "AAPL,US,1,145.0,USD,일반,stock\n"
    )
    prices = {"005930.KS": 58400, "AAPL": 200000}
    report = calc_weights(str(csv), prices)
    samsung = next(h for h in report.holdings if h.ticker == "005930.KS")
    assert samsung.flag == "과대"


def test_rebalance_actions_not_empty_when_needed(tmp_path):
    csv = tmp_path / "p.csv"
    csv.write_text(
        "ticker,market,shares,avg_price,avg_price_currency,account_type,asset_class\n"
        "005930.KS,KR,1000,70000,KRW,ISA,stock\n"
    )
    report = calc_weights(str(csv), {"005930.KS": 58400})
    assert report.rebalance_needed is True
    assert len(report.rebalance_actions) > 0


def test_sector_weights_present(tmp_path):
    csv = tmp_path / "p.csv"
    csv.write_text(
        "ticker,market,shares,avg_price,avg_price_currency,account_type,asset_class\n"
        "AAPL,US,10,145.0,USD,일반,stock\n"
        "MSFT,US,8,280.0,USD,일반,stock\n"
    )
    prices = {"AAPL": 200000, "MSFT": 600000}
    report = calc_weights(str(csv), prices)
    assert "빅테크" in report.sector_weights


def test_raises_on_zero_total(tmp_path):
    csv = tmp_path / "p.csv"
    csv.write_text(
        "ticker,market,shares,avg_price,avg_price_currency,account_type,asset_class\n"
        "AAPL,US,10,145.0,USD,일반,stock\n"
    )
    with pytest.raises(ValueError):
        calc_weights(str(csv), {}, cash_krw=0)
