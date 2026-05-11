from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Optional
import requests


FMP_BASE = "https://financialmodelingprep.com/api/v3"


@dataclass
class EarningsTranscript:
    ticker: str
    year: int
    quarter: int
    date: str
    content: str


def get_transcripts(
    ticker: str,
    fmp_key: str,
    limit: int = 2,
) -> list[EarningsTranscript]:
    if not fmp_key:
        return []

    url = f"{FMP_BASE}/earning_call_transcript/{ticker}?limit={limit}&apikey={fmp_key}"
    try:
        r = requests.get(url, timeout=15)
        r.raise_for_status()
        data = r.json()
    except Exception as e:
        print(f"  [경고] {ticker} 트랜스크립트 수집 실패: {e}")
        return []

    if not isinstance(data, list):
        return []

    results = []
    for item in data:
        content = item.get("content", "")
        if not content:
            continue
        results.append(EarningsTranscript(
            ticker=ticker,
            year=item.get("year", 0),
            quarter=item.get("quarter", 0),
            date=item.get("date", ""),
            content=content,
        ))

    return results


def get_analyst_estimates(ticker: str, fmp_key: str) -> Optional[dict]:
    if not fmp_key:
        return None

    url = f"{FMP_BASE}/analyst-estimates/{ticker}?limit=4&apikey={fmp_key}"
    try:
        r = requests.get(url, timeout=15)
        r.raise_for_status()
        data = r.json()
        if not isinstance(data, list) or not data:
            return None
        latest = data[0]
        return {
            "estimated_revenue_avg": latest.get("estimatedRevenueAvg"),
            "estimated_eps_avg": latest.get("estimatedEpsAvg"),
            "number_analysts_revenue": latest.get("numberAnalystEstimatedRevenue"),
            "number_analysts_eps": latest.get("numberAnalystsEstimatedEps"),
            "date": latest.get("date"),
        }
    except Exception as e:
        print(f"  [경고] {ticker} 애널리스트 추정치 수집 실패: {e}")
        return None


if __name__ == "__main__":
    import os
    from dotenv import load_dotenv
    load_dotenv()

    fmp_key = os.getenv("FMP_API_KEY", "")
    tickers = ["AAPL", "MSFT", "PLTR"]

    for ticker in tickers:
        print(f"\n{ticker} 어닝콜 트랜스크립트 수집 중...")
        transcripts = get_transcripts(ticker, fmp_key, limit=2)
        for t in transcripts:
            print(f"  {t.year}Q{t.quarter} ({t.date}) — {len(t.content):,}자")
            print(f"  미리보기: {t.content[:200]}...")
        time.sleep(0.3)
