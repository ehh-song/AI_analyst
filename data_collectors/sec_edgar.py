from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Optional
import requests


BASE_URL = "https://data.sec.gov"
SUBMISSIONS_URL = f"{BASE_URL}/submissions"
COMPANY_SEARCH_URL = "https://efts.sec.gov/LATEST/search-index?q=%22{ticker}%22&dateRange=custom&startdt={start}&enddt={end}&forms={form}"


@dataclass
class FilingRecord:
    ticker: str
    form_type: str
    filed_date: str
    accession_number: str
    document_url: str
    description: str


def _get_headers(user_agent: str) -> dict:
    return {"User-Agent": user_agent, "Accept-Encoding": "gzip, deflate"}


def get_cik(ticker: str, user_agent: str) -> Optional[str]:
    url = f"https://efts.sec.gov/LATEST/search-index?q=%22{ticker}%22&forms=10-K"
    r = requests.get(url, headers=_get_headers(user_agent), timeout=15)
    r.raise_for_status()
    hits = r.json().get("hits", {}).get("hits", [])
    if not hits:
        return None
    return hits[0].get("_source", {}).get("entity_id")


def get_recent_filings(
    ticker: str,
    user_agent: str,
    form_types: list[str] = ["10-K", "10-Q", "8-K"],
    max_per_type: int = 3,
) -> list[FilingRecord]:
    cik_url = f"https://efts.sec.gov/LATEST/search-index?q=%22{ticker}%22&forms=10-K"
    r = requests.get(cik_url, headers=_get_headers(user_agent), timeout=15)
    r.raise_for_status()

    hits = r.json().get("hits", {}).get("hits", [])
    if not hits:
        return []

    cik_raw = hits[0].get("_source", {}).get("entity_id", "")
    cik = str(cik_raw).zfill(10)

    subs_url = f"{SUBMISSIONS_URL}/CIK{cik}.json"
    r2 = requests.get(subs_url, headers=_get_headers(user_agent), timeout=15)
    r2.raise_for_status()
    data = r2.json()

    filings_data = data.get("filings", {}).get("recent", {})
    forms = filings_data.get("form", [])
    dates = filings_data.get("filingDate", [])
    accessions = filings_data.get("accessionNumber", [])
    descriptions = filings_data.get("primaryDocument", [])

    results: list[FilingRecord] = []
    counts: dict[str, int] = {ft: 0 for ft in form_types}

    for form, date, acc, desc in zip(forms, dates, accessions, descriptions):
        if form not in form_types:
            continue
        if counts[form] >= max_per_type:
            continue

        acc_clean = acc.replace("-", "")
        doc_url = f"https://www.sec.gov/Archives/edgar/data/{int(cik_raw)}/{acc_clean}/{desc}"

        results.append(FilingRecord(
            ticker=ticker,
            form_type=form,
            filed_date=date,
            accession_number=acc,
            document_url=doc_url,
            description=desc,
        ))
        counts[form] += 1

        if all(v >= max_per_type for v in counts.values()):
            break

    return results


def fetch_filing_text(document_url: str, user_agent: str, max_chars: int = 50000) -> Optional[str]:
    try:
        r = requests.get(document_url, headers=_get_headers(user_agent), timeout=20)
        r.raise_for_status()
        return r.text[:max_chars]
    except Exception as e:
        print(f"  [경고] 공시 원문 수집 실패: {e}")
        return None


if __name__ == "__main__":
    import os
    from dotenv import load_dotenv
    load_dotenv()

    user_agent = os.getenv("SEC_EDGAR_USER_AGENT", "")
    tickers = ["PLTR", "AAPL", "MSFT"]

    for ticker in tickers:
        print(f"\n{ticker} 공시 수집 중...")
        filings = get_recent_filings(ticker, user_agent, form_types=["10-K", "8-K"], max_per_type=2)
        for f in filings:
            print(f"  [{f.form_type}] {f.filed_date} — {f.description}")
        time.sleep(0.5)
