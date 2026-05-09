import pytest
from unittest.mock import patch, MagicMock
from data_collectors.earnings_transcript import get_transcripts, get_analyst_estimates, EarningsTranscript

FMP_KEY = "test_key"


def _mock_transcript_response():
    mock = MagicMock()
    mock.json.return_value = [
        {
            "symbol": "AAPL",
            "year": 2024,
            "quarter": 4,
            "date": "2024-10-31",
            "content": "Good afternoon. " + "A" * 2000,
        },
        {
            "symbol": "AAPL",
            "year": 2024,
            "quarter": 3,
            "date": "2024-08-01",
            "content": "Thank you for joining. " + "B" * 2000,
        },
    ]
    mock.raise_for_status.return_value = None
    return mock


def test_get_transcripts_returns_list():
    with patch("data_collectors.earnings_transcript.requests.get", return_value=_mock_transcript_response()):
        transcripts = get_transcripts("AAPL", FMP_KEY, limit=2)
    assert isinstance(transcripts, list)
    assert len(transcripts) == 2


def test_get_transcripts_content_minimum_length():
    with patch("data_collectors.earnings_transcript.requests.get", return_value=_mock_transcript_response()):
        transcripts = get_transcripts("AAPL", FMP_KEY, limit=2)
    assert all(len(t.content) >= 1000 for t in transcripts)


def test_get_transcripts_fields():
    with patch("data_collectors.earnings_transcript.requests.get", return_value=_mock_transcript_response()):
        transcripts = get_transcripts("AAPL", FMP_KEY)
    t = transcripts[0]
    assert t.ticker == "AAPL"
    assert t.year == 2024
    assert t.quarter == 4
    assert t.date == "2024-10-31"


def test_get_transcripts_returns_empty_without_key():
    transcripts = get_transcripts("AAPL", fmp_key="")
    assert transcripts == []


def test_get_transcripts_handles_api_error():
    with patch("data_collectors.earnings_transcript.requests.get", side_effect=Exception("timeout")):
        transcripts = get_transcripts("AAPL", FMP_KEY)
    assert transcripts == []


def test_get_analyst_estimates_returns_dict():
    mock = MagicMock()
    mock.json.return_value = [{
        "estimatedRevenueAvg": 95_000_000_000,
        "estimatedEpsAvg": 1.55,
        "numberAnalystEstimatedRevenue": 12,
        "numberAnalystsEstimatedEps": 18,
        "date": "2025-01-01",
    }]
    mock.raise_for_status.return_value = None
    with patch("data_collectors.earnings_transcript.requests.get", return_value=mock):
        result = get_analyst_estimates("AAPL", FMP_KEY)
    assert result is not None
    assert result["estimated_eps_avg"] == 1.55
    assert result["number_analysts_eps"] == 18


def test_get_analyst_estimates_returns_none_without_key():
    result = get_analyst_estimates("AAPL", fmp_key="")
    assert result is None
