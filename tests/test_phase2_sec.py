import pytest
from unittest.mock import patch, MagicMock
from data_collectors.sec_edgar import get_recent_filings, fetch_filing_text, FilingRecord

USER_AGENT = "test@example.com"


def _mock_search_response(cik: str = "0001811518"):
    mock = MagicMock()
    mock.json.return_value = {
        "hits": {"hits": [{"_source": {"entity_id": cik}}]}
    }
    mock.raise_for_status.return_value = None
    return mock


def _mock_submissions_response():
    mock = MagicMock()
    mock.json.return_value = {
        "filings": {
            "recent": {
                "form": ["10-K", "10-K", "8-K", "8-K", "10-Q"],
                "filingDate": ["2024-02-26", "2023-02-27", "2024-11-05", "2024-08-07", "2024-11-07"],
                "accessionNumber": ["0001811518-24-000001", "0001811518-23-000001",
                                    "0001811518-24-000010", "0001811518-24-000008",
                                    "0001811518-24-000020"],
                "primaryDocument": ["pltr-20231231.htm", "pltr-20221231.htm",
                                    "ex991.htm", "ex992.htm", "pltr-20240930.htm"],
            }
        }
    }
    mock.raise_for_status.return_value = None
    return mock


def test_get_recent_filings_returns_list():
    with patch("data_collectors.sec_edgar.requests.get") as mock_get:
        mock_get.side_effect = [_mock_search_response(), _mock_submissions_response()]
        filings = get_recent_filings("PLTR", USER_AGENT, form_types=["10-K", "8-K"], max_per_type=2)

    assert isinstance(filings, list)
    assert len(filings) > 0


def test_get_recent_filings_correct_form_types():
    with patch("data_collectors.sec_edgar.requests.get") as mock_get:
        mock_get.side_effect = [_mock_search_response(), _mock_submissions_response()]
        filings = get_recent_filings("PLTR", USER_AGENT, form_types=["10-K", "8-K"], max_per_type=2)

    form_types_returned = {f.form_type for f in filings}
    assert form_types_returned.issubset({"10-K", "8-K"})


def test_get_recent_filings_max_per_type():
    with patch("data_collectors.sec_edgar.requests.get") as mock_get:
        mock_get.side_effect = [_mock_search_response(), _mock_submissions_response()]
        filings = get_recent_filings("PLTR", USER_AGENT, form_types=["10-K"], max_per_type=1)

    tenk_filings = [f for f in filings if f.form_type == "10-K"]
    assert len(tenk_filings) <= 1


def test_get_recent_filings_empty_on_no_hits():
    mock = MagicMock()
    mock.json.return_value = {"hits": {"hits": []}}
    mock.raise_for_status.return_value = None
    with patch("data_collectors.sec_edgar.requests.get", return_value=mock):
        filings = get_recent_filings("INVALID_TICKER", USER_AGENT)
    assert filings == []


def test_filing_record_has_url():
    with patch("data_collectors.sec_edgar.requests.get") as mock_get:
        mock_get.side_effect = [_mock_search_response(), _mock_submissions_response()]
        filings = get_recent_filings("PLTR", USER_AGENT, form_types=["10-K"], max_per_type=1)

    assert len(filings) >= 1
    assert filings[0].document_url.startswith("https://www.sec.gov/")


def test_fetch_filing_text_returns_truncated():
    mock = MagicMock()
    mock.text = "A" * 100000
    mock.raise_for_status.return_value = None
    with patch("data_collectors.sec_edgar.requests.get", return_value=mock):
        text = fetch_filing_text("https://fake.url/doc.htm", USER_AGENT, max_chars=50000)
    assert len(text) == 50000


def test_fetch_filing_text_returns_none_on_error():
    with patch("data_collectors.sec_edgar.requests.get", side_effect=Exception("timeout")):
        result = fetch_filing_text("https://fake.url/doc.htm", USER_AGENT)
    assert result is None
