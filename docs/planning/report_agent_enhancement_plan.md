# TCFD 보고서 에이전트 고도화 계획

**작성일**: 2025-12-12
**버전**: v1.0
**목적**: 보고서 출력을 2페이지에서 5+ 페이지로 확장하고, 내용 퀄리티 향상

---

## 1. 현황 분석

### 1.1 현재 시스템 구조
- **Backend 구성**: 3개 Backend 시스템
  - `polaris_backend_fastapi`: 보고서 생성 에이전트, 건물 분석 에이전트
  - `polaris_backend_modelops`: H, E, V, P(H), AAL 로직 계산
  - `polaris_backend_springboot`: (기타 서비스)

- **데이터 소스**:
  - PostgreSQL: H, E, V, AAL 계산 결과, 건물 분석 데이터
  - Qdrant Vector DB: 기존 보고서, 데이터 설명, TCFD 가이드라인

- **현재 Workflow**: LangGraph v07 (Phase 2)
  - 11개 노드로 구성
  - 7개 보고서 생성 에이전트
  - 3개 에이전트에서만 RAG 사용 (Template, Impact, Strategy)

### 1.2 현재 문제점
1. **출력 분량 부족**: 현재 2페이지 → 목표 5+ 페이지
2. **로직 설명 부재**: H×E×V, AAL 계산 방법론 설명 없음
3. **시각화 부족**: 표, 그래프, 히트맵 등 시각 자료 없음
4. **RAG 활용도 낮음**: 전체 7개 에이전트 중 3개만 RAG 사용

---

## 2. SK TCFD 보고서 벤치마킹 분석

### 2.1 보고서 구조 (26-48페이지, 총 23페이지)

**주요 특징**:
- **로직 직접 설명 없음**: 계산 공식을 상세히 설명하지 않음
- **활용 내용 중심**: 분석 결과를 어떻게 활용하는지 서술
- **시각화 풍부**: 20+ 테이블, 10+ 그래프/다이어그램

### 2.2 섹션별 내용

#### Governance (지배구조)
- 이사회 감독 체계
- 전략·ESG위원회 운영
- 기후변화 관련 KPI와 보상 연계

#### Strategy (전략)
- 기후 리스크/기회 식별 프로세스
- 시나리오 분석 (NGFS, RCP)
  - 전환 리스크: T1~T8 (8개)
  - 물리적 리스크: P1~P2 (2개)
  - 기회: O1~O4 (4개)
- 사업장 Level 영향 분석
- 포트폴리오 Level 영향 분석
- 대응 방안 (Net Zero 이행, 사업장 & 공급망 대응, 전환 기회)

#### Risk Management (리스크 관리)
- 환경 리스크 통합관리 체계
- 기후 리스크 관리 프로세스
- Value Chain 기후 리스크 관리

#### Metrics and Targets (지표 및 목표)
- Scope 1, 2, 3 배출량
- 온실가스 감축 목표
- RE100 목표 및 이행 성과
- 내부 탄소가격제 적용

### 2.3 시각화 요소

**테이블 예시**:
- SSP 시나리오별 물리적 리스크 히트맵
- 전환 리스크/기회 분류표
- Net Zero 로드맵 비용 시나리오
- 탄소리스크 보상비율 계산 프로세스

**그래프 예시**:
- NGFS 시나리오별 탄소가격 추이
- NGFS 시나리오별 배출량 추이
- SSP 경로별 연평균 자산손실률

**다이어그램**:
- 거버넌스 구조도
- 리스크 관리 프로세스
- 시나리오 분석 프로세스

---

## 3. 핵심 인사이트

### 3.1 "로직보다 활용"
SK 보고서는 **계산 로직을 상세히 설명하지 않고**, 대신:
- 어떤 데이터를 사용했는지
- 분석 결과가 무엇인지
- 그 결과를 바탕으로 어떤 대응 전략을 수립했는지

→ **우리도 H×E×V 계산 공식 설명보다, "CMIP6 기후 모델 사용", "RCP 8.5 시나리오에서 극한 고온 67.2점" 등 결과와 활용에 집중**

### 3.2 시나리오 분석의 중요성
- 전환 리스크: NGFS (Current Policies, Delayed Transition, Net Zero 2050)
- 물리적 리스크: SSP/RCP (1-2.6, 2-4.5, 3-7.0, 5-8.5)
- **각 시나리오별로 재무 영향을 정량화**

→ **우리 시스템의 ModelOps 계산 결과를 시나리오별로 분류하고, 재무 영향을 서술**

### 3.3 거버넌스와 KPI 연계
- CEO, CFO, 임원, 구성원까지 기후변화 KPI 연결
- 보상 체계와 연계
- 이사회 보고 체계

→ **우리 보고서에도 "기업은 이사회에 연 X회 기후변화 대응 현황 보고" 등 거버넌스 섹션 강화**

---

## 4. 고도화 전략

### 4.1 우선순위: 내용 퀄리티 향상

**Phase 1 (현재 집중)**: 내용 생성 퀄리티
1. RAG 자료 확충
2. Prompt 고도화
3. 섹션 구조 확장
4. 시나리오 분석 강화

**Phase 2 (추후 구현)**: 시각화 추가
- VisualizationAgent는 보류 (어떤 걸 표/그래프로 할지 불명확)
- 추가 Excel 데이터 처리 (DataProcessingAgent) 보류

### 4.2 RAG 자료 구성

**확정 자료**:
1. `각종 자료/For_RAG/FINAL-2017-TCFD-Report.pdf`
   - TCFD 권고안 원문
   - Governance, Strategy, Risk Management, Metrics 프레임워크

2. `각종 자료/For_RAG/SnP_Climanomics_PangyoDC_Summary_Report_SK C&C_2024-02-08.pptx`
   - 판교 데이터센터 S&P Global Climanomics 분석 보고서
   - 물리적 리스크 평가 방법론
   - **Note**: pptx 파싱이 문제되면 PDF로 변환 요청

3. `polaris_backend_fastapi/ai_agent/utils/knowledge/`
   - 데이터 설명 파일들 (이미 존재)

**추후 추가**:
- 다른 기업 ESG 보고서 (planning에 추후 구현으로 표기)

### 4.3 LlamaParse 통합 전략

**필요성**:
- TCFD PDF, S&P 보고서 등 복잡한 테이블/그림 포함
- 일반 PDF parser로는 구조 파악 어려움

**주의사항**:
- **Free 요금제 사용**: 과금 방지 필수
- LlamaCloud API 키 필요
- 처음에만 문서 많이 넣고, 서비스 시작 후에는 사용 최소화

**구현 계획**:
```python
# RAG 파이프라인에 LlamaParse 통합
from llama_parse import LlamaParse

parser = LlamaParse(
    api_key=os.getenv('LLAMA_CLOUD_API_KEY'),
    result_type="markdown"  # 또는 "text"
)

documents = parser.load_data("FINAL-2017-TCFD-Report.pdf")

# 테이블/그림 메타데이터 추출
for doc in documents:
    if doc.metadata.get('type') == 'table':
        # Qdrant에 별도 저장
        ...
```

### 4.4 보고서 생성 흐름 확인

**질문**: "생성물이 md로 만들어지고 pdf로 변환해서 최종 결과물이 나오는건가?"

→ **현재 시스템 확인 필요**. 아마도:
1. Report Composer Agent → Markdown 생성
2. Finalizer Node → Markdown → PDF 변환 (pandoc 또는 weasyprint 사용 예상)
3. DB에 저장 (`reports` 테이블의 `report_content` JSONB 컬럼)

---

## 5. 섹션별 확장 계획

### 5.1 Executive Summary (0.5 페이지)
**현재**: 간단한 요약
**목표**:
- 핵심 리스크 요약 (Top 3)
- 재무 영향 요약
- 주요 대응 전략 요약

### 5.2 Governance (지배구조) (0.5 페이지 → 1 페이지)
**추가 내용**:
- 이사회 감독 체계 설명
- 기후변화 관련 안건 보고 현황 (연 X회)
- 경영진 KPI 연계 (CEO, CFO)
- 보상 체계 연계

**RAG 활용**: TCFD 권고안에서 Governance 베스트 프랙티스 참조

### 5.3 Strategy (전략) (1 페이지 → 2.5 페이지)

#### 5.3.1 리스크/기회 식별 (0.5 페이지)
- 전환 리스크 (예: RE100 정책 변동성, ETS 강화)
- 물리적 리스크 (예: 극한 고온, 하천 홍수)
- 기회 (예: 저탄소 IT 솔루션 수요 증가)

#### 5.3.2 시나리오 분석 (1 페이지)
**전환 리스크**:
- NGFS Current Policies
- NGFS Delayed Transition
- NGFS Net Zero 2050

각 시나리오별:
- 탄소가격 추이
- 예상 재무 영향 (배출권 구매 비용)

**물리적 리스크**:
- SSP1-2.6, SSP2-4.5, SSP3-7.0, SSP5-8.5
- 사업장별 위험 요인 (폭염, 홍수, 태풍 등)
- 연평균 자산손실률 (Average Annual Loss %)

#### 5.3.3 대응 전략 (1 페이지)
- Net Zero 2040 로드맵
- RE100 이행 계획
- 에너지 효율화 투자
- 공급망 리스크 관리

**RAG 활용**:
- TCFD 권고안에서 시나리오 분석 방법론
- S&P Climanomics 보고서에서 물리적 리스크 평가 기준

### 5.4 Risk Management (리스크 관리) (0.5 페이지 → 1 페이지)

#### 5.4.1 리스크 관리 프로세스
- 식별 → 평가 → 대응 → 모니터링
- 환경경영시스템 (ISO 14001) 연계
- 전사 리스크 관리 체계 통합

#### 5.4.2 Value Chain 관리
- Upstream: 공급업체 ESG 평가
- Operation: 사업장 온실가스 관리
- Downstream: 고객 Scope 3 지원

### 5.5 Metrics and Targets (지표 및 목표) (0.5 페이지 → 1 페이지)

#### 5.5.1 온실가스 배출량
- Scope 1, 2, 3 배출량 (연도별 추이)
- 배출 원단위

#### 5.5.2 감축 목표
- Net Zero 2040 (Scope 1+2)
- 2030년 60% 감축 (Base year 2023)
- Scope 3: 2050년 90% 감축

#### 5.5.3 RE100 이행
- 2024년 24.7% 달성
- 2030년 60% 목표
- 2040년 100% 목표

#### 5.5.4 내부 탄소가격제
- ICP 적용 사례
- 투자 의사결정 반영

---

## 6. Agent별 개선 사항

### 6.1 Report Analysis Agent (Template)
**현재**: 기본 템플릿 생성
**개선**:
- TCFD 4대 축 (Governance, Strategy, Risk, Metrics) 구조화
- 각 섹션별 하위 항목 상세화
- SK 보고서 구조 참조

**Prompt 개선**:
```
You are creating a TCFD climate risk assessment report template.

Reference the following structure from leading TCFD reports:
1. Governance
   - Board oversight
   - Management's role
   - KPI linkage to compensation

2. Strategy
   - Climate-related risks and opportunities
   - Scenario analysis (NGFS, RCP/SSP)
   - Business impact assessment
   - Response strategies

...

Use RAG to retrieve:
- TCFD official recommendations
- Best practice examples from similar companies
```

### 6.2 Impact Analysis Agent
**현재**: Layer 1 (정량 엔진) + Layer 2 (LLM 서술)
**개선**:
- 시나리오별 재무 영향 분리 서술
- "RCP 8.5 시나리오에서 2050년까지 냉방 비용 X% 증가 예상" 등 구체화
- S&P Climanomics 보고서 참조하여 물리적 리스크 서술

**RAG 활용 강화**:
- S&P 보고서에서 "Average Annual Loss" 개념 참조
- TCFD 권고안에서 재무 영향 보고 방식 참조

### 6.3 Strategy Generation Agent
**현재**: 대응 전략 생성
**개선**:
- Net Zero 로드맵 상세화
- RE100 이행 단계별 계획
- 투자 포트폴리오 전환 계획 (탄소집약 → 저탄소)

**RAG 활용 강화**:
- 유사 기업의 대응 전략 사례
- TCFD 권고안의 전략 섹션 가이드

### 6.4 Report Composer Agent
**현재**: Markdown + JSON 생성
**개선**:
- 섹션 번호 체계화 (1., 1.1, 1.1.1)
- 데이터 출처 명시 ("Source: ModelOps calculation based on CMIP6")
- 시나리오 분석 결과 표 삽입 (Markdown table 형식)

**출력 예시**:
```markdown
## 2. Strategy

### 2.1 Climate-related Risks and Opportunities

#### 2.1.1 Transition Risks

| Risk ID | Type | Description | Time Frame | Impact |
|---------|------|-------------|------------|--------|
| T1 | Policy | RE100 policy volatility in South Korea | Short/Mid/Long | High |
| T3 | Policy | ETS (Emissions Trading Scheme) tightening | Short/Mid | High |

#### 2.1.2 Physical Risks

| Risk ID | Type | Description | Time Frame | Impact |
|---------|------|-------------|------------|--------|
| P1 | Acute | Increased frequency of extreme heat events | Long | High |
| P2 | Chronic | Rising temperatures affecting data center cooling costs | Long | High |

### 2.2 Scenario Analysis

#### 2.2.1 Transition Risk Scenarios

**NGFS Net Zero 2050 Scenario**

Based on IEA Net Zero 2050 projections, carbon prices in South Korea are expected to reach:
- 2030: USD 90/tCO₂eq
- 2040: USD 160/tCO₂eq

**Financial Impact**:
Under the NZE 2050 scenario, estimated cumulative carbon costs (~2040):
- BAU (Business As Usual): KRW 153.1 billion
- With Net Zero implementation: KRW 196.2 billion

The Net Zero pathway requires upfront investments in renewable energy and energy efficiency,
resulting in higher initial costs but lower long-term carbon price exposure.

#### 2.2.2 Physical Risk Scenarios

**SSP5-8.5 (Worst Case)**

S&P Global Climanomics analysis indicates:
- **Daedeok Data Center**: Low to moderate risk across all hazard categories by 2040
- **Pangyo Data Center**: Low risk, with slightly elevated water stress in SSP5-8.5 pathway

**Modeled Average Annual Loss (AAL)**:
All facilities show AAL < 3% of asset value under all SSP scenarios, indicating manageable
physical risk exposure.

Key risk factors:
- Extreme heat: Potential increase in cooling energy consumption
- River flooding: Infrastructure resilience measures in place
- Water stress: Not significant for data center operations in assessed locations

...
```

### 6.5 Validation Agent
**현재**: 정확성, 일관성, 완전성 검증
**개선**:
- TCFD 권고안 준수 여부 체크리스트 추가
  - Governance 섹션 포함 여부
  - 시나리오 분석 포함 여부
  - 정량적 지표 포함 여부 (Scope 1,2,3, 감축 목표)
- 데이터 출처 명시 여부 확인

**RAG 활용**:
- TCFD 권고안의 체크리스트 참조

---

## 7. 구현 순서

### Phase 1: RAG 인프라 구축 (1-2일)
1. LlamaParse 설정 및 테스트
2. TCFD PDF, S&P pptx 파싱 및 Qdrant 저장
3. 기존 knowledge 파일 Qdrant 업데이트

### Phase 2: Prompt 고도화 (2-3일)
1. Report Analysis Agent: 템플릿 구조화
2. Impact Analysis Agent: 시나리오별 서술 강화
3. Strategy Generation Agent: 대응 전략 상세화
4. Report Composer Agent: 섹션 구조 개선

### Phase 3: Validation 강화 (1일)
1. TCFD 체크리스트 구현
2. 데이터 출처 검증 로직 추가

### Phase 4: 통합 테스트 (1-2일)
1. 전체 워크플로우 실행
2. 출력 보고서 페이지 수 확인 (목표: 5+ 페이지)
3. 내용 퀄리티 검토

---

## 8. 성공 지표

### 정량적 지표
- [ ] 보고서 페이지 수: 5 페이지 이상 (Markdown 기준)
- [ ] TCFD 4대 축 모두 포함
- [ ] 섹션 수: 최소 15개 (3단계 depth)
- [ ] 시나리오 분석: 전환 리스크 2+ 시나리오, 물리적 리스크 2+ 시나리오

### 정성적 지표
- [ ] 계산 로직 설명이 아닌 "활용 내용" 중심
- [ ] 시나리오별 재무 영향 정량화
- [ ] 대응 전략 구체화 (Net Zero 로드맵, RE100 계획)
- [ ] 데이터 출처 명시

---

## 9. 리스크 및 제약사항

### 제약사항
1. **DB/Qdrant 연결 불가 (현재)**: 구조적 부분만 수정 중
2. **VisualizationAgent 보류**: 표/그래프 생성 기준 불명확
3. **추가 데이터 보류**: Excel 데이터 처리 추후 구현
4. **LlamaParse Free 요금제**: 과금 주의

### 리스크
1. **LLM 출력 품질**: Prompt만으로 5페이지 생성 가능성 불확실
   - 완화: RAG 자료 충분히 제공, Few-shot examples 추가

2. **PPTX 파싱 문제**: LlamaParse가 pptx 잘 처리 못할 수 있음
   - 완화: 사용자에게 PDF 변환 요청

3. **토큰 제한**: GPT-4 등 모델의 출력 토큰 제한
   - 완화: 섹션별로 생성 후 조합

---

## 10. 다음 단계

1. **LlamaParse 테스트**
   - TCFD PDF 파싱 결과 확인
   - S&P pptx → PDF 변환 필요 여부 확인

2. **Progress 문서 작성 시작**
   - `polaris_backend_fastapi/docs/progress/` 에 진행 상황 기록

3. **Agent Prompt 개선 착수**
   - Report Analysis Agent 부터 시작
