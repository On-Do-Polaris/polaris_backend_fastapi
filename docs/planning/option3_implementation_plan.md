# Option 3 (Hybrid Approach) Implementation Plan
**버전**: v01
**작성일**: 2025-12-12
**목표**: TCFD 보고서 2페이지 → 5페이지 이상 확대 (RAG 확충 + Prompt 개선 + 구조 확장)

---

## 📋 전체 개요

### 핵심 전략
Option 3는 **새로운 Agent 추가 + 기존 Agent RAG/Prompt 개선**을 결합한 하이브리드 접근방식입니다.

**3대 축**:
1. **RAG 자료 확충**: 7개 Agent 중 1개만 RAG 사용 → 6개로 확대
2. **Prompt 고도화**: SK 스타일 반영 (계산식 설명 ❌, 결과/활용 중심 ✅)
3. **섹션 구조 확장**: 2개 새 Agent 추가 (StrategyAgent, MetricsAgent)

### 예상 성과
- **보고서 분량**: 2페이지 → **5~7페이지**
- **TCFD 4대 기둥 커버리지**: 현재 30% → **80%+**
- **물리적 리스크 깊이**: 현재 표면적 분석 → **세부 시나리오 기반 분석**

---

## 🎯 Phase별 실행 계획

### Phase 1: RAG 인프라 구축 (1주차)
**목표**: LlamaParse + Qdrant 기반 RAG 시스템 완성

#### 1.1 문서 Parsing 및 Ingestion
- [ ] **Task 1-1**: `ingest_rag_documents.py` 실행하여 기존 PDF 파싱
  - 대상 문서:
    - `FINAL-2017-TCFD-Report.pdf` (TCFD 공식 가이드라인)
    - `SnP_Climanomics_PangyoDC_Summary_Report_SK C&C_2024-02-08.pdf` (S&P 리포트)
    - Risk-specific RAG 파일들 (9개: Drought, Extreme_Heat, River_Flood 등)
  - 총 페이지 수: ~110페이지 (Free Tier 1,000페이지 중 11% 사용)
  - 예상 소요 시간: 10~15분

- [ ] **Task 1-2**: Parsing 결과 검증
  - 이미지 처리 확인 (LlamaParse는 이미지를 텍스트로 설명)
  - 표 추출 정확도 확인 (Markdown table 형식)
  - 그래프/차트 설명 품질 확인

- [ ] **Task 1-3**: Qdrant 업로드 확인
  - Collection `tcfd_documents`: 일반 텍스트 청크
  - Collection `tcfd_tables`: 표 데이터 (구조화)
  - 임베딩 모델: `all-MiniLM-L6-v2`

#### 1.2 RAG 검색 성능 테스트
- [ ] **Task 1-4**: 쿼리 테스트
  ```python
  # 예시 쿼리
  test_queries = [
      "TCFD 거버넌스 권고사항",
      "물리적 리스크 시나리오 분석 방법",
      "극한 고온 영향 사례",
      "기후 리스크 재무 영향 평가"
  ]
  ```
- [ ] **Task 1-5**: Top-K 최적화 (현재: 20개 → 실험 필요)

---

### Phase 2: Agent별 RAG 통합 (2~3주차)

#### 2.1 ReportAnalysisAgent (Agent 1) - 이미 완료 ✅
**현재 상태**: RAG 사용 중 (`RAGEngine(source="benchmark")`)
**개선 사항**: Prompt 고도화만 필요 (Phase 4에서 진행)

---

#### 2.2 ImpactAnalysisAgent (Agent 2) - RAG 신규 추가
**현재**: RiskContextBuilder만 사용 (knowledge folder)
**개선**: RAG 추가로 실제 사례 기반 영향 분석

**구현 계획**:
```python
# impact_analysis_agent_2.py
class ImpactAnalysisAgent:
    def __init__(self, llm_client):
        self.llm = llm_client
        self.risk_context = RiskContextBuilder()  # 기존 유지
        self.rag = RAGEngine(source="tcfd")  # 신규 추가

    def run(self, state: SuperAgentState) -> Dict[str, Any]:
        # 1) 기존: RiskContextBuilder에서 H/E/V/AAL 기반 컨텍스트
        context = self.risk_context.build_context(
            risk_scores=state["risk_scores"],
            aal_values=state["aal_values"]
        )

        # 2) 신규: RAG에서 유사 사례 검색
        rag_cases = self.rag.query(
            query=f"{state['target_location']} 지역 {risk_type} 영향 사례",
            top_k=10
        )

        # 3) Prompt에 두 가지 정보 모두 포함
        prompt = self._build_prompt(context, rag_cases, state)
        result = self.llm.invoke(prompt)
        return result
```

**예상 효과**:
- 현재: "AAL 3.2%는 높은 수준입니다" (건조한 설명)
- 개선: "유사한 환경의 SK 데이터센터 사례를 보면, 극한 고온으로 냉각 비용이 연 15% 증가했습니다. 귀사의 AAL 3.2%는..." (구체적 사례)

---

#### 2.3 StrategyGenerationAgent (Agent 3) - RAG 신규 추가
**현재**: RAG 미사용
**개선**: TCFD 전략 권고사항 + S&P 보고서 참고

**구현 계획**:
```python
class StrategyGenerationAgent:
    def __init__(self, llm_client):
        self.llm = llm_client
        self.rag = RAGEngine(source="tcfd")  # 신규 추가

    def run(self, state: SuperAgentState) -> Dict[str, Any]:
        # RAG: TCFD 전략 섹션 + S&P 대응 전략 사례
        rag_strategies = self.rag.query(
            query="기후 리스크 대응 전략 및 복원력 강화 방안",
            top_k=15
        )

        prompt = self._build_prompt(
            impact_analysis=state["impact_analysis"],
            rag_strategies=rag_strategies,
            report_profile=state.get("report_template", {})
        )
        result = self.llm.invoke(prompt)
        return result
```

**예상 효과**:
- 현재: 일반적인 대응 전략 제시
- 개선: TCFD 권고사항 + S&P 모범 사례 기반 구체적 전략

---

#### 2.4 ReportComposerAgent (Agent 4) - RAG 신규 추가
**현재**: report_profile만 사용
**개선**: RAG로 TCFD 문장 템플릿 참고

**구현 계획**:
```python
class ReportComposerAgent:
    def __init__(self, llm_client):
        self.llm = llm_client
        self.rag = RAGEngine(source="tcfd")  # 신규 추가

    def run(self, state: SuperAgentState) -> Dict[str, Any]:
        # RAG: TCFD 공식 문장 구조 + SK 보고서 스타일
        rag_templates = self.rag.query(
            query="TCFD 물리적 리스크 보고서 작성 예시 및 문장 구조",
            top_k=20
        )

        prompt = self._build_prompt(
            impact=state["impact_analysis"],
            strategy=state["response_strategy"],
            report_profile=state["report_template"],
            rag_templates=rag_templates
        )
        result = self.llm.invoke(prompt)
        return result
```

---

#### 2.5 ValidationAgent (Agent 5) - RAG 신규 추가
**현재**: 하드코딩된 검증 기준
**개선**: TCFD 권고사항 기반 동적 검증

**구현 계획**:
```python
class ValidationAgent:
    def __init__(self, llm_client):
        self.llm = llm_client
        self.rag = RAGEngine(source="tcfd")  # 신규 추가

    def run(self, state: SuperAgentState) -> Dict[str, Any]:
        # RAG: TCFD 공식 검증 체크리스트
        rag_criteria = self.rag.query(
            query="TCFD 물리적 리스크 공시 필수 요소 및 검증 기준",
            top_k=10
        )

        prompt = self._build_validation_prompt(
            report=state["generated_report"],
            rag_criteria=rag_criteria
        )
        result = self.llm.invoke(prompt)
        return result
```

---

#### 2.6 RefinerAgent (Agent 6) - RAG 신규 추가
**현재**: ValidationAgent 피드백만 사용
**개선**: RAG로 개선 사례 참고

**구현 계획**:
```python
class RefinerAgent:
    def __init__(self, llm_client):
        self.llm = llm_client
        self.rag = RAGEngine(source="tcfd")  # 신규 추가

    def run(self, state: SuperAgentState) -> Dict[str, Any]:
        # RAG: 유사한 문제 해결 사례
        issues = state["validation_feedback"]
        rag_fixes = self.rag.query(
            query=f"TCFD 보고서 품질 개선 방법: {issues}",
            top_k=10
        )

        prompt = self._build_refine_prompt(
            report=state["generated_report"],
            issues=issues,
            rag_fixes=rag_fixes
        )
        result = self.llm.invoke(prompt)
        return result
```

---

### Phase 3: 새 Agent 개발 (3~4주차)

#### 3.1 StrategyAgent 신규 개발
**위치**: Impact 이후, Report Composer 이전
**목적**: TCFD "Strategy" 섹션 전담 (현재 누락)

**핵심 기능**:
1. 기후 시나리오별 영향 분석 (RCP 2.6 / 4.5 / 8.5)
2. 단기/중기/장기 리스크 식별 (2025 / 2030 / 2050)
3. 기후 복원력(Resilience) 평가
4. 비즈니스 전략 영향 분석

**입력**:
- `impact_analysis`: 물리적 리스크 영향
- `risk_scores`, `aal_values`: 정량 데이터
- RAG: TCFD Strategy 섹션 가이드라인

**출력**:
```json
{
  "scenarios": {
    "rcp_2.6": {
      "2025": "단기 영향 분석",
      "2030": "중기 영향 분석",
      "2050": "장기 영향 분석"
    },
    "rcp_4.5": { ... },
    "rcp_8.5": { ... }
  },
  "resilience_assessment": "복원력 평가 요약",
  "business_implications": "비즈니스 전략 영향"
}
```

**프롬프트 예시**:
```
You are a climate strategy analyst specializing in TCFD reporting.

TASK: Analyze climate risks across multiple scenarios and timeframes.

INPUT DATA:
- Physical Risk Scores: {risk_scores}
- AAL Values: {aal_values}
- Impact Analysis: {impact_analysis}

RAG CONTEXT (TCFD Strategy Examples):
{rag_strategies}

OUTPUT REQUIREMENTS:
1. Scenario Analysis: RCP 2.6, 4.5, 8.5
2. Time Horizons: 2025 (short-term), 2030 (medium-term), 2050 (long-term)
3. Resilience Assessment: How well is the organization prepared?
4. Strategic Implications: Business impact

STYLE (SK Report Style):
- Focus on RESULTS and APPLICATIONS, NOT formulas
- Use concrete examples from RAG context
- Avoid technical calculation details
- Emphasize actionable insights

OUTPUT FORMAT: JSON
```

---

#### 3.2 MetricsAgent 신규 개발
**위치**: Strategy 이후, Report Composer 이전
**목적**: TCFD "Metrics & Targets" 섹션 전담

**핵심 기능**:
1. 물리적 리스크 KPI 정의 (AAL, Risk Score 등)
2. 벤치마크 비교 (업계 평균 vs 현재 사업장)
3. 개선 목표 제시 (2030 / 2050 목표)
4. 모니터링 지표 추천

**입력**:
- `risk_scores`, `aal_values`: 정량 데이터
- `strategy_analysis`: StrategyAgent 출력
- RAG: TCFD Metrics 섹션 가이드라인

**출력**:
```json
{
  "key_metrics": {
    "aal_percentage": 3.2,
    "high_risk_count": 2,
    "risk_score_avg": 65.4
  },
  "benchmarks": {
    "industry_average_aal": 2.1,
    "gap_analysis": "귀사는 업계 평균 대비 1.1% 높음"
  },
  "targets": {
    "2030": "AAL 2.0% 이하로 감축",
    "2050": "AAL 1.0% 이하로 감축"
  },
  "monitoring_indicators": [
    "월별 극한 고온 일수",
    "냉각 시스템 가동 시간",
    "에너지 소비량 변화율"
  ]
}
```

---

### Phase 4: Prompt 고도화 (4~5주차)

#### 4.1 SK 스타일 반영 원칙
**핵심 인사이트**: "로직에 대한 직접적인 언급은 크게 없고 그로 인해 활용되는 내용을 기반으로 보고서를 작성"

**Before (❌ 현재 스타일)**:
```
The AAL is calculated as:
AAL = base_aal × F_vuln × (1 - IR)

Where:
- base_aal: Base average annual loss
- F_vuln: Vulnerability scaling factor
- IR: Insurance coverage rate

For this site:
- base_aal = 0.025
- F_vuln = 1.3
- IR = 0.05
- Final AAL = 0.025 × 1.3 × 0.95 = 3.09%
```

**After (✅ SK 스타일)**:
```
귀사의 연평균 재무 손실률(AAL)은 3.09%로 평가되었습니다.
이는 극한 고온과 홍수 리스크가 복합적으로 작용한 결과로,
냉각 시스템 가동 증가와 침수 피해 가능성이 주요 요인입니다.

유사한 환경의 SK 데이터센터 사례를 참고하면,
냉각 효율 개선과 방수 시설 강화를 통해 AAL을 1.5%p 감축한 바 있습니다.
```

#### 4.2 Agent별 Prompt 개선안

**ImpactAnalysisAgent (Agent 2)**:
```python
# Before
prompt = f"""
Analyze the physical risk impact based on H×E×V formula.

Risk Scores:
- Extreme Heat: H={H}, E={E}, V={V}, Score={H*E*V}
- River Flood: ...

Calculate the financial impact using AAL formula...
"""

# After
prompt = f"""
You are a climate risk analyst writing for executives.

CONTEXT:
{rag_cases}  # Real examples from RAG

YOUR TASK:
Analyze how climate risks will AFFECT this facility's operations and finances.

DATA:
- AAL: {aal_percentage}%
- High-risk hazards: {high_risks}

INSTRUCTIONS:
1. Explain WHAT the risks mean for business operations (NOT how they were calculated)
2. Reference similar cases from RAG context
3. Focus on operational impacts (downtime, costs, supply chain)
4. Avoid formulas, variables, or calculation steps

EXAMPLE (SK Style):
"귀사의 연평균 손실률 3.2%는 업계 평균 2.1% 대비 높은 수준입니다.
주요 원인은 극한 고온으로 인한 냉각 비용 증가(연 500만 달러 예상)와
홍수 리스크로 인한 데이터센터 가동 중단 가능성입니다.

유사 환경의 SK 판교 데이터센터 사례를 보면,
극한 고온 대응 냉각 시스템 업그레이드로 연간 15% 비용 절감에 성공했습니다."

OUTPUT FORMAT: Markdown
"""
```

**StrategyGenerationAgent (Agent 3)**:
```python
prompt = f"""
You are a sustainability strategist creating TCFD-compliant climate resilience strategies.

RAG CONTEXT (TCFD Best Practices):
{rag_strategies}

IMPACT ANALYSIS:
{impact_analysis}

YOUR TASK:
Develop actionable strategies to reduce climate risks.

INSTRUCTIONS:
1. Reference TCFD recommendations from RAG
2. Propose SPECIFIC actions (not generic "monitor climate")
3. Include cost-benefit considerations
4. Prioritize by impact and feasibility

SK STYLE:
- Results-oriented (NOT "we will calculate...", BUT "we will reduce AAL by...")
- Concrete examples from RAG context
- Avoid mentioning formulas or models

EXAMPLE:
"Based on TCFD recommendations and SK's proven approaches:

1. Short-term (2025):
   - Install advanced cooling systems (expected AAL reduction: 0.8%p)
   - Implement flood barriers around critical equipment
   - Estimated investment: $2M, ROI: 18 months

2. Medium-term (2030):
   - Diversify data center locations to low-risk regions
   - Expected AAL reduction: 1.5%p

Reference: SK Pangyo DC reduced extreme heat impact by 40% using similar measures."

OUTPUT FORMAT: JSON
"""
```

**ReportComposerAgent (Agent 4)**:
```python
prompt = f"""
You are composing a TCFD physical risk report in the style of SK's sustainability reports.

INPUTS:
- Report Profile: {report_profile}
- Impact Analysis: {impact_analysis}
- Strategy: {response_strategy}

RAG TEMPLATES:
{rag_templates}

CRITICAL STYLE REQUIREMENT (SK Standard):
❌ DO NOT explain calculation formulas (no H×E×V, no AAL formula)
✅ DO explain what the results MEAN and how to USE them

EXAMPLE:

❌ BAD (Formula-focused):
"The physical risk score is calculated as H×E×V. For extreme heat, H=75, E=80, V=65, resulting in a score of 390,000."

✅ GOOD (SK Style):
"극한 고온 리스크가 가장 높게 평가되었습니다. 이는 냉각 시스템 부담 증가와 장비 과열로 이어질 수 있으며, 유사 환경의 SK 데이터센터 사례를 참고하면 연간 운영비가 15% 증가한 바 있습니다."

OUTPUT SECTIONS:
1. Executive Summary
2. Physical Risk Overview (from impact_analysis)
3. Strategic Response (from response_strategy)
4. Metrics & Targets

Use report_profile for tone, structure, and formatting.
Incorporate RAG templates for TCFD-compliant phrasing.

OUTPUT FORMAT: Markdown
"""
```

---

### Phase 5: Governance 하드코딩 템플릿 (5주차)

#### 5.1 배경
사용자 요구사항: "우리 시스템을 보면 물리적 리스크 특화된 시스템이야. 그래서 이사회 Governance, 최고 경영진 같은 내용들은 하드코딩으로 할 예정"

#### 5.2 구현 방안
**파일**: `polaris_backend_fastapi/ai_agent/utils/governance_templates.py`

```python
"""
파일명: governance_templates.py
목적: TCFD Governance 섹션 하드코딩 템플릿
"""

GOVERNANCE_TEMPLATES = {
    "board_oversight": {
        "en": """
## Board Oversight

The Board of Directors maintains oversight of climate-related risks and opportunities through:

- **Quarterly Reviews**: Climate risk assessments are reviewed by the Board's Sustainability Committee on a quarterly basis
- **Risk Integration**: Physical climate risks are integrated into the enterprise risk management (ERM) framework
- **Strategic Planning**: Climate considerations are incorporated into annual strategic planning sessions
- **Executive Compensation**: Climate performance metrics are linked to executive compensation structures

The Board ensures that climate-related risks, including physical risks from extreme weather events, are adequately addressed in the organization's overall risk management approach.
        """,
        "ko": """
## 이사회의 감독

이사회는 다음을 통해 기후 관련 리스크 및 기회를 감독합니다:

- **분기별 검토**: 이사회 산하 지속가능경영위원회는 분기별로 기후 리스크 평가를 검토합니다
- **리스크 통합**: 물리적 기후 리스크는 전사 리스크 관리(ERM) 프레임워크에 통합되어 관리됩니다
- **전략 기획**: 기후 고려사항은 연간 전략 기획 세션에 반영됩니다
- **경영진 보상**: 기후 성과 지표는 경영진 보상 체계와 연계됩니다

이사회는 극한 기상 현상으로 인한 물리적 리스크를 포함한 기후 관련 리스크가 조직의 전반적인 리스크 관리 접근 방식에서 적절히 다뤄지도록 보장합니다.
        """
    },

    "management_role": {
        "en": """
## Management's Role

Climate risk management is led by the Chief Sustainability Officer (CSO) and supported by:

- **Climate Risk Committee**: Cross-functional team meeting monthly to assess physical and transition risks
- **Risk Assessment**: Annual comprehensive climate risk assessments covering all major facilities
- **Scenario Analysis**: Evaluation of climate scenarios (RCP 2.6, 4.5, 8.5) to inform strategic decisions
- **Reporting**: Quarterly updates to the Board on climate risk metrics and mitigation progress

The management team ensures that climate risk considerations are embedded in operational planning and capital allocation decisions.
        """,
        "ko": """
## 경영진의 역할

기후 리스크 관리는 최고지속가능경영책임자(CSO)가 주도하며, 다음 조직이 지원합니다:

- **기후리스크위원회**: 매월 회의를 통해 물리적 리스크 및 전환 리스크를 평가하는 부서 간 협의체
- **리스크 평가**: 주요 사업장을 대상으로 연간 종합 기후 리스크 평가 실시
- **시나리오 분석**: 전략적 의사결정을 지원하기 위한 기후 시나리오(RCP 2.6, 4.5, 8.5) 평가
- **보고**: 기후 리스크 지표 및 완화 진행 상황에 대한 분기별 이사회 보고

경영진은 기후 리스크 고려사항이 운영 계획 및 자본 배분 의사결정에 반영되도록 보장합니다.
        """
    }
}

def get_governance_section(language: str = "en") -> str:
    """
    Governance 섹션 전체를 반환

    Args:
        language: 'en' 또는 'ko'

    Returns:
        Markdown 형식의 Governance 섹션
    """
    sections = []
    sections.append(GOVERNANCE_TEMPLATES["board_oversight"][language])
    sections.append(GOVERNANCE_TEMPLATES["management_role"][language])
    return "\n\n".join(sections)
```

#### 5.3 통합 방법
**ReportComposerAgent에서 사용**:
```python
from ..utils.governance_templates import get_governance_section

class ReportComposerAgent:
    def run(self, state: SuperAgentState) -> Dict[str, Any]:
        language = state.get("language", "en")

        # Governance 섹션은 하드코딩 템플릿 사용
        governance_section = get_governance_section(language)

        # 나머지 섹션은 LLM으로 생성
        strategy_section = self._generate_strategy(state)
        risk_mgmt_section = self._generate_risk_management(state)
        metrics_section = self._generate_metrics(state)

        # 최종 보고서 조합
        report = {
            "governance": governance_section,  # 하드코딩
            "strategy": strategy_section,      # LLM 생성
            "risk_management": risk_mgmt_section,  # LLM 생성
            "metrics_targets": metrics_section     # LLM 생성
        }

        return report
```

---

### Phase 6: Phase 2 Agent 배치 (6주차)

#### 6.1 VisualizationAgent
**위치**: FinalizerNode 이후 (워크플로우 종료 직전)
**목적**: 최종 보고서에 차트/그래프 추가

**보류 이유**: 현재 시각화 기준 불명확, Phase 2에서 재검토

**예상 기능** (Phase 2에서 구현 시):
- Risk Score 히트맵
- AAL 시계열 그래프 (2025 / 2030 / 2050)
- 시나리오별 비교 차트 (RCP 2.6 vs 4.5 vs 8.5)

**구현 위치**:
```python
# graph.py
workflow.add_node("visualization", visualization_node)
workflow.add_edge("finalization", "visualization")
workflow.add_edge("visualization", END)
```

---

#### 6.2 DataProcessingAgent
**위치**: AdditionalDataHelper 이전 (Pre-processing 단계)
**목적**: 사용자 제공 추가 데이터 전처리

**보류 이유**: 현재 AdditionalDataHelper로 충분, 추가 필요성 불명확

**예상 기능** (Phase 2에서 구현 시):
- 파일 형식 변환 (Excel → JSON, PDF → Text)
- 데이터 정규화 (단위 통일, 날짜 형식 통일)
- 이상치 탐지 및 제거

**구현 위치**:
```python
# Pre-processing 단계 (워크플로우 외부)
if user_provided_file:
    data_processor = DataProcessingAgent()
    processed_data = data_processor.process(user_file)
    additional_data_helper = AdditionalDataHelper()
    guidelines = additional_data_helper.generate_guidelines(processed_data)
```

---

## 📊 예상 결과물 비교

### Before (현재 - 2페이지)
```markdown
# Physical Risk Assessment Report

## Overview
- AAL: 3.2%
- High-risk hazards: Extreme Heat, River Flood

## Risk Scores
| Hazard | Score |
|--------|-------|
| Extreme Heat | 75 |
| River Flood | 68 |

## Recommendations
- Monitor climate trends
- Implement risk mitigation measures

(총 분량: 약 2페이지)
```

### After (Option 3 - 5~7페이지)
```markdown
# TCFD Physical Climate Risk Disclosure

## 1. Governance (하드코딩 템플릿)
### 1.1 Board Oversight
이사회는 분기별로 기후 리스크를 검토하며...
(1페이지)

### 1.2 Management's Role
최고지속가능경영책임자(CSO)가 주도하며...
(0.5페이지)

## 2. Strategy (StrategyAgent - 신규)
### 2.1 Climate Scenario Analysis
- RCP 2.6 (2°C): 2030년까지 극한 고온 일수 20% 증가 예상...
- RCP 4.5 (3°C): 2050년까지 홍수 리스크 35% 증가...
- RCP 8.5 (4°C): 2050년까지 AAL 5.8%로 상승...
(1.5페이지)

### 2.2 Resilience Assessment
현재 복원력 수준: 중간. SK 판교 DC 사례를 참고하면...
(0.5페이지)

## 3. Risk Management
### 3.1 Physical Risk Impact Analysis (ImpactAnalysisAgent - RAG 추가)
귀사의 연평균 손실률 3.2%는 업계 평균 2.1% 대비 높은 수준입니다.
주요 원인은 극한 고온으로 인한 냉각 비용 증가(연 500만 달러)와...

유사 환경의 SK 데이터센터 사례:
- 극한 고온 대응: 냉각 시스템 업그레이드로 15% 비용 절감
- 홍수 대응: 방수벽 설치로 침수 위험 80% 감소
(1.5페이지)

### 3.2 Response Strategies (StrategyGenerationAgent - RAG 추가)
#### Short-term (2025)
- 냉각 시스템 효율 개선: 예상 AAL 감소 0.8%p
- 투자: $2M, ROI: 18개월

#### Medium-term (2030)
- 사업장 다각화: 저위험 지역 확대
- 예상 AAL 감소: 1.5%p
(1페이지)

## 4. Metrics and Targets (MetricsAgent - 신규)
### 4.1 Key Performance Indicators
| Metric | Current | Industry Avg | Gap |
|--------|---------|--------------|-----|
| AAL | 3.2% | 2.1% | +1.1% |
| High-risk count | 2 | 1.5 | +0.5 |

### 4.2 Targets
- 2030: AAL 2.0% 이하 감축
- 2050: AAL 1.0% 이하 감축

### 4.3 Monitoring Indicators
- 월별 극한 고온 일수
- 냉각 시스템 가동 시간
(1페이지)

(총 분량: 약 7페이지)
```

---

## 🎯 성공 지표 (KPI)

| 지표 | 현재 (Before) | 목표 (After) | 측정 방법 |
|-----|--------------|-------------|----------|
| 보고서 분량 | 2페이지 | 5~7페이지 | 최종 PDF 페이지 수 |
| TCFD 커버리지 | Metrics 30% | 4대 기둥 80%+ | 섹션별 체크리스트 |
| RAG 사용 Agent | 1/7 (14%) | 6/7 (86%) | Agent별 RAG 통합 여부 |
| Prompt SK 스타일 | 0% | 100% | 계산식 언급 횟수 (0회 목표) |
| 실행 사례 인용 | 0건 | 5건 이상 | RAG에서 가져온 사례 수 |
| LLM 호출 횟수 | ~7회 | ~9회 (+2 Agent) | 워크플로우 트레이스 |
| 평균 실행 시간 | ~45초 | ~60초 (+15초) | LangSmith 측정 |

---

## 🚀 실행 타임라인

| 주차 | Phase | 주요 작업 | 예상 소요 시간 |
|-----|-------|---------|--------------|
| 1주차 | Phase 1 | RAG 인프라 (Parsing + Qdrant) | 8시간 |
| 2주차 | Phase 2.1-2.3 | Agent 2, 3 RAG 통합 | 12시간 |
| 3주차 | Phase 2.4-2.6 | Agent 4, 5, 6 RAG 통합 | 12시간 |
| 4주차 | Phase 3 | StrategyAgent + MetricsAgent 개발 | 16시간 |
| 5주차 | Phase 4 | Prompt 고도화 (전체 Agent) | 12시간 |
| 6주차 | Phase 5-6 | Governance 템플릿 + 통합 테스트 | 10시간 |
| **총계** | | | **70시간** |

---

## ⚠️ 리스크 및 대응 방안

### 리스크 1: LlamaParse 쿼터 초과
- **확률**: 낮음 (110페이지 / 1,000페이지 = 11%)
- **대응**: 로컬 캐싱으로 재파싱 방지 (`DocumentParser.parse_pdf` 캐시 우선)

### 리스크 2: RAG 검색 품질 저하
- **확률**: 중간 (임베딩 모델 성능 의존)
- **대응**: Top-K 파라미터 실험 (10 / 15 / 20), 필요시 reranking 도입

### 리스크 3: Prompt 개선 효과 불명확
- **확률**: 중간 (LLM 응답 변동성)
- **대응**: A/B 테스트 (Before/After 프롬프트 비교), LangSmith로 품질 추적

### 리스크 4: 실행 시간 증가 (45초 → 60초)
- **확률**: 높음 (RAG 검색 + 2개 Agent 추가)
- **대응**: 병렬 실행 검토 (Impact + Building Characteristics), 캐싱 강화

### 리스크 5: 새 Agent 통합 버그
- **확률**: 중간 (LangGraph 상태 관리 복잡성)
- **대응**: 단위 테스트 작성, 단계별 통합 (한 번에 1개 Agent씩)

---

## 📁 파일 구조 (예상)

```
polaris_backend_fastapi/
├── ai_agent/
│   ├── agents/
│   │   ├── report_generation/
│   │   │   ├── report_analysis_agent_1.py (기존 - Prompt 개선)
│   │   │   ├── impact_analysis_agent_2.py (RAG 추가 + Prompt 개선)
│   │   │   ├── strategy_generation_agent_3.py (RAG 추가 + Prompt 개선)
│   │   │   ├── report_composer_agent_4.py (RAG 추가 + Prompt 개선)
│   │   │   ├── validation_agent_5.py (RAG 추가)
│   │   │   ├── refiner_agent_6.py (RAG 추가)
│   │   │   ├── strategy_agent_7.py (신규 개발)
│   │   │   └── metrics_agent_8.py (신규 개발)
│   │   └── building_characteristics/
│   │       └── building_characteristics_agent.py (기존 유지)
│   ├── services/
│   │   ├── document_parser.py (완료 ✅)
│   │   └── rag_ingestion_service.py (완료 ✅)
│   ├── utils/
│   │   ├── rag_helpers.py (기존 - RAGEngine)
│   │   ├── governance_templates.py (신규 - Phase 5)
│   │   └── knowledge/
│   │       └── risk_insight.py (기존 유지)
│   └── workflow/
│       ├── graph.py (2개 Agent 추가로 수정)
│       └── state.py (신규 필드 추가: strategy_analysis, metrics_analysis)
├── scripts/
│   └── ingest_rag_documents.py (완료 ✅)
└── docs/
    └── planning/
        ├── option3_implementation_plan.md (본 문서)
        └── rag_parsing_strategy.md (완료 ✅)
```

---

## ✅ 체크리스트

### Phase 1: RAG 인프라
- [ ] `ingest_rag_documents.py` 실행 완료
- [ ] Qdrant 업로드 확인 (tcfd_documents + tcfd_tables)
- [ ] RAG 검색 품질 테스트 완료
- [ ] Top-K 파라미터 최적화

### Phase 2: Agent RAG 통합
- [ ] ImpactAnalysisAgent RAG 추가
- [ ] StrategyGenerationAgent RAG 추가
- [ ] ReportComposerAgent RAG 추가
- [ ] ValidationAgent RAG 추가
- [ ] RefinerAgent RAG 추가

### Phase 3: 새 Agent 개발
- [ ] StrategyAgent 구현
- [ ] MetricsAgent 구현
- [ ] graph.py 통합 (노드 추가)
- [ ] state.py 필드 추가 (strategy_analysis, metrics_analysis)

### Phase 4: Prompt 고도화
- [ ] ImpactAnalysisAgent Prompt SK 스타일 적용
- [ ] StrategyGenerationAgent Prompt SK 스타일 적용
- [ ] ReportComposerAgent Prompt SK 스타일 적용
- [ ] Before/After A/B 테스트

### Phase 5: Governance 템플릿
- [ ] governance_templates.py 작성
- [ ] ReportComposerAgent 통합
- [ ] 영어/한국어 템플릿 검증

### Phase 6: 통합 테스트
- [ ] 전체 워크플로우 실행 테스트
- [ ] 보고서 분량 확인 (5페이지 이상)
- [ ] TCFD 4대 기둥 커버리지 확인
- [ ] 성능 측정 (실행 시간 60초 이내)

---

## 🔗 관련 문서

- [RAG Parsing Strategy](./rag_parsing_strategy.md)
- [Progress Tracking (2025-12-12)](../progress/2025-12-12_report_enhancement.md)
- [Development Standards](../standards_core.md)
- [Additional Data Flow](../../ai_agent/additional_data_flow.mmd)

---

**작성자**: Claude Code
**검토 필요 사항**:
1. Phase별 우선순위 조정 여부
2. 새 Agent (Strategy, Metrics) 출력 스키마 승인
3. Governance 하드코딩 템플릿 내용 검토
4. LlamaParse 실행 승인 (쿼터 사용)
