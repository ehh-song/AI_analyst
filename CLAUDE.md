# AI Investment Analyst - Project Guidelines

## 프로젝트 개요

주식 포트폴리오 리밸런싱을 돕는 AI 기반 투자 분석 도구.
사용자가 보유 자산을 진단하고, 시장 데이터를 수집하며, AI를 통해 리밸런싱 의사결정을 보조받는 시스템.

---

## Claude 행동 원칙

### 셀프 리뷰 규칙 (3-Pass Review)

어떤 계획, 설계, 코드 제안이든 사용자에게 제시하기 전에 반드시 스스로 3회 검토한다.

1. **1차 검토**: 초안 작성 후 논리적 오류, 누락된 요소 확인
2. **2차 검토**: 1차 검토 결과를 바탕으로 개선점 적용, 엣지 케이스 및 리스크 점검
3. **3차 검토**: 최종안이 사용자 요구사항에 부합하는지, 불필요하게 복잡하지 않은지 확인

각 제안 시 검토 과정에서 발견한 주요 개선사항을 간략히 함께 제시한다.

---

## 코딩 규칙

### 일반
- 불필요한 주석 작성 금지. 코드 자체로 의도가 명확해야 함
- 현재 요구사항을 넘는 추상화, 기능 추가 금지
- 에러 핸들링은 실제로 발생 가능한 경우에만 작성
- 보안 취약점(인젝션, 키 노출 등) 없는 코드 작성

### Python
- 타입 힌트 사용 (함수 파라미터, 반환값)
- 환경변수는 `.env` + `python-dotenv`로 관리, 코드에 하드코딩 금지
- 외부 API 호출 시 타임아웃, 재시도 로직 포함

### 구조
- 기능별 모듈 분리 (수집 / 분석 / AI 어드바이저 / 대시보드)
- 각 모듈은 독립적으로 실행 및 테스트 가능하게 작성

---

## 프로젝트 아키텍처

```
AI_analyst/
├── data_collectors/
│   ├── market_data.py        # Yahoo Finance, FRED API
│   ├── news_sentiment.py     # NewsAPI + Claude 요약
│   └── portfolio_tracker.py  # 현재 보유 종목 현황
│
├── analyzers/
│   ├── valuation.py          # PER, PBR, DCF 계산
│   ├── risk_metrics.py       # 샤프비율, 변동성, 상관관계
│   └── rebalance_engine.py   # 목표 비중 vs 현재 비중 비교
│
├── ai_advisor/
│   ├── portfolio_qa.py       # Claude API: 포트폴리오 질의응답
│   ├── scenario_analysis.py  # 시나리오 분석 ("금리 1% 상승 시")
│   └── report_generator.py   # 주간 리밸런싱 리포트 자동 생성
│
├── dashboard/
│   └── app.py                # Streamlit 대시보드
│
├── CLAUDE.md
├── .env.example
└── requirements.txt
```

---

## 주요 데이터 소스

| 분류 | 소스 | 용도 |
|------|------|------|
| 주가/ETF | Yahoo Finance API (`yfinance`) | 현재가, 이력 데이터 |
| 거시지표 | FRED API | 금리, CPI, GDP |
| 뉴스 | NewsAPI | 센티먼트 분석용 원문 |
| 국내주 | 네이버 금융 (크롤링) | 국내 종목 보완 |
| 재무제표 | FinancialModelingPrep API | PER, PBR, EPS 등 |

---

## AI 활용 방식

- Claude API를 통해 수집된 데이터를 해석하고 리밸런싱 제안 생성
- AI는 **의사결정 보조** 역할. 최종 결정은 항상 사용자
- 포트폴리오 질의응답, 시나리오 분석, 자동 리포트 생성에 활용
- 프롬프트 캐싱 적용으로 API 비용 최적화

---

## Git 브랜치 전략

- 개발 브랜치: `claude/investment-rebalancing-tool-f6rY2`
- 커밋 메시지는 영어, 변경 의도 중심으로 작성
- 기능 단위로 커밋 분리
