# Session Notes — AI Investment Analyst

> 이 파일은 세션이 초기화될 때 이어서 진행하기 위한 참조 문서다.
> 새 세션에서는 이 파일을 먼저 읽고 CLAUDE.md, investor_profile.md를 참조한 뒤 작업을 재개한다.

---

## 프로젝트 목표

주식 포트폴리오 리밸런싱을 돕는 AI 분석 도구 (Program 1: Portfolio Health Check).
보유 종목을 진단하고 SEC 공시 + 어닝콜 원문을 Claude API로 분석해 리밸런싱 제안을 제공한다.

---

## 개발 브랜치

`claude/investment-rebalancing-tool-f6rY2`

---

## 환경 제약

- **Claude Code 웹 환경**: 외부 네트워크 완전 차단 (Yahoo Finance, FRED, SEC EDGAR 모두 403)
- 실제 API 호출은 로컬 환경에서만 동작
- 모든 테스트는 mock 데이터 기반으로 작성

---

## 완료된 Phase

### Phase 1 — 기반 설정 ✅
- `requirements.txt`, `.env.example`, `.gitignore`
- `config/settings.py`: APIConfig, InvestorProfile, AppConfig 데이터클래스
- `data/portfolio.csv`: 삼성전자/PLTR/AAPL/MSFT/QQQ
- `tests/test_phase1.py`: 9개 테스트 통과

### Phase 2 — 데이터 수집 ✅
- `data_collectors/price_data.py`: yfinance 기반 주가 스냅샷, USD→KRW 환산
- `data_collectors/sec_edgar.py`: SEC EDGAR API로 10-K/10-Q/8-K 공시 수집
- `data_collectors/earnings_transcript.py`: FMP API 어닝콜 트랜스크립트 + 애널리스트 추정치
- `tests/fixtures/mock_price_data.json`: 오프라인 테스트용 mock 데이터
- 테스트: 22개 통과 (test_phase2_price: 8, test_phase2_sec: 7, test_phase2_transcript: 7)

---

## 완료된 Phase (추가)

### Phase 3 — 분석 엔진 ✅
- `analyzers/fundamental.py`: PER/PBR/ROE/부채비율/FCF, score_fundamentals() 평가 함수
- `analyzers/risk_metrics.py`: 샤프비율, 연간 변동성, 상관관계 행렬, 분산화 점수
- `analyzers/portfolio_weight.py`: 종목별/섹터별 비중, 목표 대비 이탈, 리밸런싱 액션 생성
- 테스트: 20개 통과

### Phase 4 — AI 분석 ✅
- `ai_advisor/company_analyst.py`: Claude API로 어닝콜 + 공시 분석, 5항목 JSON 반환
- 테스트: 7개 통과

### Phase 5 — 대시보드 ✅
- `dashboard/app.py`: Streamlit 3탭 (포트폴리오현황 / 종목진단 / 절세알림)
- mock 데이터 fallback 내장, import 정상 확인

---

## 투자자 프로필 핵심 요약

- 26세 대학원생, 총 자산 1,400만원, 주식 비중 80~90%
- 보유: 삼성전자(KR), PLTR, AAPL, MSFT, QQQ
- 목표 수익률: 연 7% (물가+5%), 분기 리밸런싱
- 반기 유동성 필요: 최대 700만원 (학비)
- 청년형 ISA 보유, 비과세 잔여 400만원
- 해외주식 미실현 이익 250만원 초과 가능 → 매도 시 절세 전략 필요
- 선호 섹터: 전력·에너지 (전공), 테크 / 배제: 담배·무기·카지노

---

## API 키 현황

| 키 | 상태 |
|----|------|
| ANTHROPIC_API_KEY | ✅ 설정됨 |
| FRED_API_KEY | ✅ 설정됨 |
| SEC_EDGAR_USER_AGENT | ✅ 설정됨 |
| FMP_API_KEY | ⬜ 미설정 (선택) |
| DART_API_KEY | ⬜ 미설정 (선택) |

---

## 전체 테스트 현황

```
tests/test_phase1.py            9 passed
tests/test_phase2_price.py      8 passed
tests/test_phase2_sec.py        7 passed
tests/test_phase2_transcript.py 7 passed
tests/test_phase3_fundamental.py 8 passed
tests/test_phase3_risk.py        6 passed
tests/test_phase3_weight.py      6 passed
tests/test_phase4_ai.py          7 passed
─────────────────────────────────────
합계: 58 passed  ← 전체 통과
```

---

## 새 세션 시작 시 체크리스트

1. `cat SESSION_NOTES.md` 로 현황 파악
2. `cat CLAUDE.md` 로 행동 원칙 확인
3. `cat investor_profile.md` 로 투자자 성향 확인
4. `python -m pytest tests/ -v` 로 기존 테스트 통과 확인
5. 미완료 Phase부터 이어서 진행
