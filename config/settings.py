import os
from dataclasses import dataclass, field
from typing import List
from dotenv import load_dotenv

load_dotenv()


def _require_env(key: str) -> str:
    value = os.getenv(key)
    if not value:
        raise EnvironmentError(f"Missing required environment variable: {key}")
    return value


def _get_env(key: str, default: str = "") -> str:
    return os.getenv(key, default)


@dataclass
class APIConfig:
    anthropic_key: str
    fred_key: str
    sec_user_agent: str
    fmp_key: str
    dart_key: str


@dataclass
class InvestorProfile:
    age: int = 26
    total_assets_krw: int = 14_000_000
    monthly_contribution_krw: int = 500_000
    target_annual_return: float = 0.07
    rebalancing_frequency: str = "quarterly"
    liquidity_need: str = "semi_annual"
    liquidity_amount_krw: int = 7_000_000
    risk_level: str = "moderate_growth"
    max_single_stock_weight: float = 0.25
    style: str = "long_term_hold"
    excluded_sectors: List[str] = field(default_factory=lambda: ["tobacco", "weapons", "gambling"])
    preferred_sectors: List[str] = field(default_factory=lambda: ["power", "energy", "tech"])
    has_isa: bool = True
    isa_nontaxable_limit_krw: int = 4_000_000
    isa_realized_gains_krw: int = 0
    overseas_unrealized_gains_krw: int = 0
    overseas_basic_deduction_krw: int = 2_500_000
    fx_risk_tolerance: bool = True


@dataclass
class AppConfig:
    api: APIConfig
    investor: InvestorProfile
    claude_model: str = "claude-sonnet-4-6"
    data_dir: str = "data"
    portfolio_file: str = "data/portfolio.csv"


def load_config() -> AppConfig:
    api = APIConfig(
        anthropic_key=_require_env("ANTHROPIC_API_KEY"),
        fred_key=_require_env("FRED_API_KEY"),
        sec_user_agent=_require_env("SEC_EDGAR_USER_AGENT"),
        fmp_key=_get_env("FMP_API_KEY"),
        dart_key=_get_env("DART_API_KEY"),
    )
    return AppConfig(api=api, investor=InvestorProfile())


if __name__ == "__main__":
    try:
        config = load_config()
        print("✓ API 설정 로드 성공")
        print(f"  - Claude 모델: {config.claude_model}")
        print(f"  - 포트폴리오 파일: {config.portfolio_file}")
        print("\n✓ 투자자 프로필:")
        p = config.investor
        print(f"  - 총 자산: {p.total_assets_krw:,}원")
        print(f"  - 목표 수익률: {p.target_annual_return:.0%}")
        print(f"  - 리밸런싱 주기: {p.rebalancing_frequency}")
        print(f"  - ISA 비과세 잔여: {p.isa_nontaxable_limit_krw - p.isa_realized_gains_krw:,}원")
    except EnvironmentError as e:
        print(f"✗ 설정 오류: {e}")
