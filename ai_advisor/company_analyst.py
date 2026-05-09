import json
from dataclasses import dataclass
from typing import Optional
import anthropic


SYSTEM_PROMPT = """당신은 기관급 주식 분석가입니다. SEC 공시(10-K, 10-Q, 8-K)와 어닝콜 트랜스크립트 원문을 바탕으로 기업을 분석합니다.

분석 원칙:
- 경영진 발언의 톤 변화(낙관→보수적 등)를 민감하게 감지한다
- 수치보다 질적 변화(리스크 신규 언급, 가이던스 철회 등)를 우선 포착한다
- 투자자 관점에서 실질적으로 중요한 정보만 간결하게 전달한다
- 한국어로 답변한다"""


@dataclass
class CompanyAnalysis:
    ticker: str
    guidance_summary: str        # 경영진 가이던스 요약
    key_risks: str               # 핵심 리스크 발언
    tone_change: str             # 전 분기 대비 톤 변화
    capital_allocation: str      # 자본 배분 방향
    overall_opinion: str         # 종합 투자 의견
    raw_response: str


def analyze_company(
    ticker: str,
    transcript_text: str,
    filing_text: str,
    client: anthropic.Anthropic,
    model: str = "claude-sonnet-4-6",
) -> Optional[CompanyAnalysis]:
    if not transcript_text and not filing_text:
        return None

    sources = []
    if transcript_text:
        sources.append(f"<earnings_call>\n{transcript_text[:8000]}\n</earnings_call>")
    if filing_text:
        sources.append(f"<sec_filing>\n{filing_text[:6000]}\n</sec_filing>")

    user_message = f"""다음 {ticker} 관련 공식 자료를 분석해주세요.

{chr(10).join(sources)}

아래 5가지 항목을 JSON 형식으로 반환하세요:
{{
  "guidance_summary": "경영진 다음 분기/연도 가이던스 요약 (2~3문장)",
  "key_risks": "원문에서 언급된 핵심 리스크 발언 (2~3개 bullet)",
  "tone_change": "전 분기 대비 경영진 발언 톤 변화 (한 문장)",
  "capital_allocation": "배당/자사주매입/CAPEX 방향 요약 (1~2문장)",
  "overall_opinion": "비중확대 / 비중유지 / 비중축소 중 하나와 근거 (2문장)"
}}"""

    try:
        response = client.messages.create(
            model=model,
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_message}],
        )
        raw = response.content[0].text.strip()

        json_start = raw.find("{")
        json_end = raw.rfind("}") + 1
        parsed = json.loads(raw[json_start:json_end])

        return CompanyAnalysis(
            ticker=ticker,
            guidance_summary=parsed.get("guidance_summary", ""),
            key_risks=parsed.get("key_risks", ""),
            tone_change=parsed.get("tone_change", ""),
            capital_allocation=parsed.get("capital_allocation", ""),
            overall_opinion=parsed.get("overall_opinion", ""),
            raw_response=raw,
        )
    except Exception as e:
        print(f"  [경고] {ticker} AI 분석 실패: {e}")
        return None


def analyze_portfolio(
    holdings: list[dict],
    client: anthropic.Anthropic,
    model: str = "claude-sonnet-4-6",
) -> str:
    summary = json.dumps(holdings, ensure_ascii=False, indent=2)

    response = client.messages.create(
        model=model,
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        messages=[{
            "role": "user",
            "content": (
                f"다음 포트폴리오를 분석하고 리밸런싱 우선순위를 제안해주세요.\n\n"
                f"```json\n{summary}\n```\n\n"
                "1. 전체 포트폴리오 진단 (2~3문장)\n"
                "2. 즉시 조정이 필요한 종목과 이유\n"
                "3. 중장기 관점에서 추가 검토할 섹터"
            ),
        }],
    )
    return response.content[0].text
