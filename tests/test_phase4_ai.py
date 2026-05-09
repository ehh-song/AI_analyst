import json
import pytest
from unittest.mock import MagicMock, patch
from ai_advisor.company_analyst import analyze_company, analyze_portfolio, CompanyAnalysis


SAMPLE_TRANSCRIPT = "Good afternoon. Revenue grew 14% year-over-year. " * 100
SAMPLE_FILING = "Item 1A. Risk Factors. The Company faces regulatory risk in AI. " * 50

MOCK_JSON = {
    "guidance_summary": "다음 분기 매출 성장 지속 예상. 서비스 부문 두 자릿수 성장 유지.",
    "key_risks": "- 중국 시장 규제 리스크\n- AI 관련 규제 불확실성\n- 환율 변동 영향",
    "tone_change": "전 분기 대비 중국 시장 우려 톤이 강화되었으나 전반적 낙관 기조 유지.",
    "capital_allocation": "자사주 매입 $90B 지속. 배당 4% 인상 발표.",
    "overall_opinion": "비중유지. 현재 밸류에이션은 고평가 구간이나 AI 사이클 수혜 기대.",
}


def _mock_client(response_text: str):
    client = MagicMock()
    msg = MagicMock()
    msg.content = [MagicMock(text=response_text)]
    client.messages.create.return_value = msg
    return client


def test_analyze_company_returns_analysis():
    client = _mock_client(json.dumps(MOCK_JSON))
    result = analyze_company("AAPL", SAMPLE_TRANSCRIPT, SAMPLE_FILING, client)
    assert result is not None
    assert isinstance(result, CompanyAnalysis)
    assert result.ticker == "AAPL"


def test_analyze_company_all_fields_populated():
    client = _mock_client(json.dumps(MOCK_JSON))
    result = analyze_company("AAPL", SAMPLE_TRANSCRIPT, SAMPLE_FILING, client)
    assert result.guidance_summary != ""
    assert result.key_risks != ""
    assert result.tone_change != ""
    assert result.capital_allocation != ""
    assert result.overall_opinion != ""


def test_analyze_company_returns_none_on_empty_input():
    client = _mock_client("{}")
    result = analyze_company("AAPL", "", "", client)
    assert result is None


def test_analyze_company_handles_json_with_preamble():
    preamble = "분석 결과입니다:\n\n" + json.dumps(MOCK_JSON)
    client = _mock_client(preamble)
    result = analyze_company("MSFT", SAMPLE_TRANSCRIPT, "", client)
    assert result is not None
    assert result.guidance_summary != ""


def test_analyze_company_returns_none_on_api_error():
    client = MagicMock()
    client.messages.create.side_effect = Exception("API error")
    result = analyze_company("AAPL", SAMPLE_TRANSCRIPT, SAMPLE_FILING, client)
    assert result is None


def test_analyze_portfolio_returns_string():
    client = _mock_client("포트폴리오 진단: 테크 집중도가 높습니다. 에너지 섹터 추가를 권장합니다.")
    holdings = [
        {"ticker": "AAPL", "weight": 0.25, "flag": "과대"},
        {"ticker": "MSFT", "weight": 0.20, "flag": "정상"},
    ]
    result = analyze_portfolio(holdings, client)
    assert isinstance(result, str)
    assert len(result) > 0


def test_claude_api_called_with_correct_model():
    client = _mock_client(json.dumps(MOCK_JSON))
    analyze_company("PLTR", SAMPLE_TRANSCRIPT, "", client, model="claude-sonnet-4-6")
    call_kwargs = client.messages.create.call_args[1]
    assert call_kwargs["model"] == "claude-sonnet-4-6"
