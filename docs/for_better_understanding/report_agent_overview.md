# TCFD 보고서 생성 에이전트 완벽 가이드

**작성일**: 2025-12-16
**버전**: v2.0
**목적**: 다음 대화 시작 시 보고서 에이전트 전체 구조를 빠르게 이해하기 위한 종합 문서

---

## 📋 목차

1. [개요](#1-개요)
2. [전체 아키텍처](#2-전체-아키텍처)
3. [노드별 상세 설명](#3-노드별-상세-설명)
4. [데이터 흐름 및 State](#4-데이터-흐름-및-state)
5. [프론트엔드 JSON 구조](#5-프론트엔드-json-구조)
6. [RAG 시스템](#6-rag-시스템)
7. [Building Characteristics & Additional Data Agent](#7-building-characteristics--additional-data-agent)
8. [주요 개념 정리](#8-주요-개념-정리)
9. [실제 사용 예시](#9-실제-사용-예시)
10. [문제 해결 가이드](#10-문제-해결-가이드)

---

## 1. 개요

### 1.1 TCFD 보고서 생성 에이전트란?

**TCFD Report Generation Agent**는 기후 물리적 리스크 분석 데이터를 기반으로 **TCFD/ESG 준수 보고서를 자동 생성**하는 LangGraph 기반 멀티 에이전트 시스템입니다.

**핵심 특징**:
- ✅ **LangGraph 워크플로우**: 7개 노드 (Node 0 ~ Node 6) 순차 실행
- ✅ **LLM 기반 자동화**: GPT-4를 활용한 고품질 보고서 생성
- ✅ **RAG 통합**: 기존 ESG/TCFD 보고서 스타일 학습 및 참조
- ✅ **병렬 처리**: Top 5 리스크 동시 분석 (~30초)
- ✅ **자동 검증**: Validator 노드를 통한 품질 보증
- ✅ **프론트엔드 연동**: 표준 JSON 구조로 출력

**입력**: 사업장별 물리적 리스크 데이터 (H, E, V, AAL, 건물 정보 등)
**출력**: TCFD 4개 섹션 (Governance, Strategy, Risk Management, Metrics & Targets)

---

## 2. 전체 아키텍처

### 2.1 노드 구조 (Node 0 ~ Node 6)

```mermaid
graph TD
    A[Node 0: Data Preprocessing] --> B[Node 1: Template Loading]
    B --> C[Node 2-A: Scenario Analysis]
    C --> D[Node 2-B: Impact Analysis]
    D --> E[Node 2-C: Mitigation Strategies]
    E --> F[Node 3: Strategy Section]
    F --> G[Node 4: Validator]
    G --> H{Validation Pass?}
    H -->|Yes| I[Node 5: Composer]
    H -->|No| J[Refiner - 최대 3회 재실행]
    J --> D
    I --> K[Node 6: Finalizer]
    K --> L[프론트엔드 JSON 출력]
```

### 2.2 노드별 역할 요약

| 노드 | 이름 | 역할 | 소요 시간 | LLM 사용 |
|------|------|------|-----------|----------|
| **Node 0** | Data Preprocessing | DB에서 데이터 로드 + BC/AD Agent 실행 | ~30초 | ❌ |
| **Node 1** | Template Loading | RAG 기반 보고서 템플릿 생성 | ~10초 | ✅ |
| **Node 2-A** | Scenario Analysis | 4개 SSP 시나리오 비교 분석 | ~15초 | ✅ |
| **Node 2-B** | Impact Analysis | Top 5 리스크 영향 분석 (병렬) | ~30초 | ✅ (5개) |
| **Node 2-C** | Mitigation Strategies | Top 5 리스크 대응 전략 생성 (병렬) | ~30초 | ✅ (5개) |
| **Node 3** | Strategy Section | Executive Summary + Heatmap + P1~P5 통합 | ~20초 | ✅ |
| **Node 4** | Validator | 품질 검증 (TCFD 준수성, 데이터 일관성) | ~10초 | ✅ |
| **Node 5** | Composer | 최종 보고서 조립 (4개 섹션) | ~5초 | ❌ |
| **Node 6** | Finalizer | DB 저장 + 프론트엔드 JSON 변환 | ~2초 | ❌ |

**총 소요 시간**: 약 2~3분 (병렬 처리 최적화 적용)

---

## 3. 노드별 상세 설명

### Node 0: Data Preprocessing

**파일**: `ai_agent/agents/tcfd_report/node_0_data_preprocessing.py`

**역할**:
1. **Application DB**에서 사업장 기본 정보 조회 (site_id, name, location)
2. **Datawarehouse DB**에서 물리적 리스크 데이터 조회 (AAL, Hazard, Exposure, Vulnerability)
3. **BC Agent** (Building Characteristics Agent) 실행 → 건물 특성 분석
4. **AD Agent** (Additional Data Agent) 실행 → Excel 추가 데이터 처리 (optional)

**출력**:
```python
{
    "site_data": List[Dict],           # 사업장 기본 정보
    "aal_scaled_results": List[Dict],  # AAL 결과
    "hazard_results": List[Dict],      # Hazard 점수
    "exposure_results": List[Dict],    # Exposure 점수
    "vulnerability_results": List[Dict], # Vulnerability 점수
    "building_data": Dict[int, Dict],  # BC Agent 결과
    "additional_data": Dict[str, Any]  # AD Agent 결과 (optional)
}
```

**핵심 코드**:
```python
# BC Agent 실행 (Fork-Join 병렬)
bc_agent = BuildingCharacteristicsAgent(llm_client)
building_data = await bc_agent.analyze_all_sites(
    sites_data=sites_data,
    risk_scores=risk_scores
)
```

---

### Node 1: Template Loading

**파일**: `ai_agent/agents/tcfd_report/node_1_template_loading_v2.py`

**역할**:
- **RAG 기반 보고서 템플릿 생성**: 기존 ESG/TCFD 보고서 스타일 학습
- 회사별 보고서 톤, 구조, 문체 추출

**RAG 검색 대상**:
- `2025-SK-Inc.-Sustainability-Report-KOR-TCFD` (SK 2025 지속가능경영보고서)
- `FINAL-2017-TCFD-Report` (국제 TCFD 표준 보고서)

**출력 구조**:
```json
{
  "report_template_profile": {
    "tone": {
      "style": "formal",
      "tense": "present",
      "vocabulary_level": "professional"
    },
    "section_structure": {
      "main_sections": ["governance", "strategy", "risk_management", "metrics_targets"]
    },
    "formatting_rules": {
      "tables": "allowed",
      "charts": "allowed"
    },
    "scenario_templates": {
      "ssp1_2.6": "Low emissions scenario",
      "ssp2_4.5": "Moderate emissions scenario"
    },
    "hazard_template_blocks": {
      "extreme_heat": "극한 고온으로 인한 영향: {description}. 예상 피해: {impact}.",
      "river_flood": "하천 홍수 리스크: {description}. 예상 피해: {impact}."
    }
  }
}
```

---

### Node 2-A: Scenario Analysis

**파일**: `ai_agent/agents/tcfd_report/node_2a_scenario_analysis_v2.py`

**역할**:
- 4개 SSP 시나리오(SSP1-2.6, SSP2-4.5, SSP3-7.0, SSP5-8.5) 비교 분석
- 포트폴리오 전체 AAL 추이 분석 (단기/중기/장기)

**프롬프트 특징**:
- **EXHAUSTIVE 접근**: "처음부터 완벽하게 분석하면 재분석은 필요 없다"
- **5개 분석 요구사항**: 시나리오 차별화, 타임라인 분석, 리스크 해석, 전략적 시사점, 이해관계자 소통

**출력**:
```json
{
  "scenarios": {
    "ssp1_2.6": {
      "description": "저탄소 시나리오",
      "portfolio_aal": 45.2,
      "trend": "2030년까지 완만한 증가"
    }
  },
  "comparative_analysis": "시나리오별 AAL 차이 40.3%p",
  "narrative": "Markdown 형식 분석 텍스트"
}
```

---

### Node 2-B: Impact Analysis (⭐ 핵심 노드)

**파일**: `ai_agent/agents/tcfd_report/node_2b_impact_analysis_v2.py`

**역할**:
1. **Top 5 리스크 식별** (AAL 기준 내림차순)
2. **병렬 LLM 분석** (5개 리스크 동시 처리 → ~30초)
3. **3가지 차원 영향 분석**:
   - 재무적 영향 (Financial Impact): AAL → 금액 환산
   - 운영적 영향 (Operational Impact): 다운타임, 위험 시스템
   - 자산 영향 (Asset Impact): 취약 자산, 손상 가능성

**프롬프트 구조**:
```markdown
<ROLE>
You are a top-tier Financial Analyst and Risk Management Consultant...
</ROLE>

<CONTEXT>
- QUANTITATIVE_ANALYSIS_RESULT: HEV 평균, Risk Scores, AAL
- ASSET_INFORMATION: 사업장 정보
- RISK_KNOWLEDGE_BASE: 리스크별 정량 데이터 컨텍스트 (RiskContextBuilder 사용)
</CONTEXT>

<OUTPUT_REQUIREMENTS>
1. 재무적 영향: 총 예상 손실, AAL%, 주요 비용 요인
2. 운영적 영향: 예상 다운타임, 위험 시스템
3. 자산 영향: 취약 자산, 손상 가능성
</OUTPUT_REQUIREMENTS>
```

**출력 예시**:
```json
{
  "top_5_risks": [
    {"risk_type": "river_flood", "total_aal": 18.2},
    {"risk_type": "typhoon", "total_aal": 12.8}
  ],
  "impact_analyses": [
    {
      "risk_type": "river_flood",
      "financial_impact": {
        "estimated_exposure": "연간 910억원",
        "aal_percentage": 18.2,
        "key_cost_drivers": ["자산 손상", "운영 중단"]
      },
      "operational_impact": {
        "estimated_downtime": "최대 72시간",
        "critical_systems_at_risk": ["데이터센터", "전력 인프라"]
      },
      "asset_impact": {
        "vulnerable_assets": ["지하 주차장", "1층 설비"],
        "damage_potential": "높음"
      }
    }
  ],
  "impact_blocks": [
    {
      "type": "text",
      "subheading": "P1. 하천 홍수 (River Flood)",
      "content": "# 영향 분석\n\n하천 홍수는 포트폴리오 전체에서 가장 높은 AAL(18.2%)을 기록했습니다..."
    }
  ]
}
```

---

### Node 2-C: Mitigation Strategies

**파일**: `ai_agent/agents/tcfd_report/node_2c_mitigation_strategies_v2.py`

**역할**:
- Top 5 리스크별 **구체적 대응 전략** 생성 (병렬 처리)
- **국제 표준 프로그램** 포함: RE100, SBTi, CDP, ISO 14090

**프롬프트 핵심 요구사항**:
```markdown
<CRITICAL>
- 모든 권고사항은 Specific, Measurable, Time-bound 해야 함
- 투자 시나리오 최소 2개 제시 (AAL 감소 예측 포함)
- 국제 표준 프로그램 실제 사례 포함
</CRITICAL>
```

**출력 예시**:
```json
{
  "mitigation_strategies": [
    {
      "risk_type": "river_flood",
      "strategy_summary": "배수 시스템 개선 및 구조적 보강을 통한 홍수 리스크 저감",
      "strategy_details": {
        "policy_recommendation": "RE100 참여: 2030년까지 재생에너지 100% 전환, 연간 500억원 투자",
        "operational_recommendation": "2025년 Q2까지 실시간 홍수 모니터링 시스템 구축",
        "technical_recommendation": "배수 용량 50mm/hr → 120mm/hr로 증설 (총 5억원)"
      },
      "cost_benefit_analysis": "투자 5억원, AAL 18.2%→7.5% 감소, ROI 11개월",
      "improvement_scenarios": {
        "scenario_1": {
          "description": "배수 시스템 개선 (50% 예산)",
          "investment": "2.5억원",
          "expected_improvement": "AAL 18.2% → 10.4%",
          "timeline": "18개월"
        },
        "scenario_2": {
          "description": "종합 보강 (100% 예산)",
          "investment": "5억원",
          "expected_improvement": "AAL 18.2% → 7.5%",
          "timeline": "24개월"
        }
      },
      "specific_programs": {
        "international_standards": ["RE100", "SBTi", "CDP"],
        "adaptation_measures": ["Nature-based Solutions", "Green Infrastructure"]
      }
    }
  ],
  "mitigation_blocks": [
    {
      "type": "text",
      "subheading": "P1. 하천 홍수 대응 전략",
      "content": "# 대응 전략\n\n## 정책 권고사항\n- RE100 참여..."
    }
  ]
}
```

---

### Node 3: Strategy Section

**파일**: `ai_agent/agents/tcfd_report/node_3_strategy_section_v2.py`

**역할**:
1. **Executive Summary** 생성 (LLM 기반 종합 분석)
2. **Heatmap Table** 생성 (사업장별 AAL 분포 시각화)
3. **Priority Actions Table** 생성 (우선순위 조치 요약)
4. **P1~P5 블록 통합** (Node 2-B + Node 2-C 결과)

**Heatmap 색상 기준**:
- Gray: 0-3% (낮음)
- Yellow: 3-10% (중간)
- Orange: 10-30% (높음)
- Red: 30%+ (매우 높음)

**출력**:
```json
{
  "section_id": "strategy",
  "title": "2. Strategy",
  "blocks": [
    {
      "type": "text",
      "subheading": "Executive Summary",
      "content": "..."
    },
    {
      "type": "table",
      "title": "사업장별 물리적 리스크 AAL 분포",
      "headers": [
        {"text": "사업장", "value": "site"},
        {"text": "하천범람", "value": "river_flood"}
      ],
      "items": [
        {
          "site": "SK 판교캠퍼스",
          "river_flood": {"value": "7.2%", "bg_color": "yellow"}
        }
      ],
      "legend": [
        {"color": "gray", "label": "0-3% (낮음)"},
        {"color": "yellow", "label": "3-10% (중간)"}
      ]
    },
    // P1~P5 블록 (Node 2-B + 2-C 통합)
  ]
}
```

---

### Node 4: Validator

**파일**: `ai_agent/agents/tcfd_report/node_4_validator_v2.py`

**역할**:
- **품질 검증**: TCFD 준수성, 데이터 일관성, 완전성
- **자동 개선**: 검증 실패 시 Refiner 루프 실행 (최대 3회)

**검증 항목**:
```python
checks = {
    "completeness": "모든 필수 섹션 존재 여부",
    "consistency": "AAL 값, 리스크 이름 일관성",
    "tcfd_compliance": "TCFD 4개 권장사항 충족",
    "data_quality": "정량 데이터 정확성"
}
```

**출력**:
```json
{
  "validated": true,
  "quality_score": 92,
  "issues": []
}
```

---

### Node 5: Composer

**파일**: `ai_agent/agents/tcfd_report/node_5_composer_v2.py`

**역할**:
- 4개 섹션 조립 (Governance + Strategy + Risk Management + Metrics & Targets)
- Markdown + JSON 형식 최종 보고서 생성

**출력**:
```json
{
  "report": {
    "report_id": "tcfd_report_20251216_001",
    "meta": {"title": "TCFD 보고서"},
    "sections": [
      {
        "section_id": "governance",
        "title": "1. Governance",
        "blocks": [...]
      },
      {
        "section_id": "strategy",
        "title": "2. Strategy",
        "blocks": [...]
      }
    ]
  }
}
```

---

### Node 6: Finalizer

**파일**: `ai_agent/agents/tcfd_report/node_6_finalizer_v2.py`

**역할**:
- DB 저장 (Application DB - `tcfd_reports` 테이블)
- **프론트엔드 JSON 변환** (최종 출력)

---

## 4. 데이터 흐름 및 State

### 4.1 LangGraph State 구조

**파일**: `ai_agent/agents/tcfd_report/state.py`

```python
class TCFDReportState(TypedDict):
    # 사이트 기본 정보 (Application DB)
    site_data: List[Dict[str, Any]]

    # Datawarehouse DB - 5개 결과 테이블
    aal_scaled_results: List[Dict[str, Any]]
    hazard_results: List[Dict[str, Any]]
    exposure_results: List[Dict[str, Any]]
    vulnerability_results: List[Dict[str, Any]]
    probability_results: List[Dict[str, Any]]

    # Agent 결과
    building_data: Dict[int, Dict[str, Any]]  # BC Agent
    additional_data: Dict[str, Any]           # AD Agent

    # Excel 추가 데이터 사용 여부
    use_additional_data: Annotated[bool, default_false]

    # Physical Risk Report 전용 필드
    sites_risk_assessment: Optional[List[Dict[str, Any]]]
    risk_table_status: str
```

### 4.2 데이터 흐름 다이어그램

```
[Node 0] DB 데이터 → site_data, aal_results, hazard_results 등
         ↓
[Node 1] RAG 검색 → report_template
         ↓
[Node 2-A] 시나리오 분석 → scenario_analysis
         ↓
[Node 2-B] Top 5 리스크 + 영향 분석 → impact_analyses, impact_blocks
         ↓
[Node 2-C] 대응 전략 생성 → mitigation_strategies, mitigation_blocks
         ↓
[Node 3] 통합 → strategy_section (Executive Summary + Heatmap + P1~P5)
         ↓
[Node 4] 검증 → validation_result
         ↓ (Pass)
[Node 5] 조립 → report (4개 섹션)
         ↓
[Node 6] DB 저장 + JSON 변환 → 프론트엔드 전달
```

---

## 5. 프론트엔드 JSON 구조

### 5.1 최종 출력 형식

**파일**: `test_output/report_json_for_front.json`

```json
{
  "report_id": "tcfd_report_20251216_163321",
  "meta": {
    "title": "TCFD 보고서",
    "created_at": "2025-12-16T19:05:00Z",
    "company_name": "SK 테스트"
  },
  "sections": [
    {
      "section_id": "governance",
      "title": "1. Governance",
      "blocks": [
        {
          "type": "text",
          "subheading": "1.1 이사회의 감독",
          "content": "이사회는 기후 관련 리스크 및 기회에 대한..."
        }
      ]
    },
    {
      "section_id": "strategy",
      "title": "2. Strategy",
      "blocks": [
        {
          "type": "text",
          "subheading": "Executive Summary",
          "content": "기후 변화는 우리의 포트폴리오에..."
        },
        {
          "type": "table",
          "title": "사업장별 물리적 리스크 AAL 분포",
          "subheading": "사업장별 물리적 리스크 AAL 분포",
          "headers": [
            {"text": "사업장", "value": "site"},
            {"text": "HEAT_WAVE", "value": "heat_wave"},
            {"text": "RIVER_FLOOD", "value": "river_flood"}
          ],
          "items": [
            {
              "site": "SK 판교캠퍼스",
              "heat_wave": {"value": "15.2%", "bg_color": "orange"},
              "river_flood": {"value": "7.2%", "bg_color": "yellow"}
            },
            {
              "site": "SK u-타워",
              "heat_wave": {"value": "12.5%", "bg_color": "orange"},
              "river_flood": {"value": "12.5%", "bg_color": "orange"}
            }
          ],
          "legend": [
            {"color": "gray", "label": "0-3% (낮음)"},
            {"color": "yellow", "label": "3-10% (중간)"},
            {"color": "orange", "label": "10-30% (높음)"},
            {"color": "red", "label": "30%+ (매우 높음)"}
          ]
        },
        {
          "type": "text",
          "subheading": "2.2 사업 및 재무 영향",
          "content": "우리 포트폴리오는..."
        }
      ]
    }
  ]
}
```

### 5.2 Block 타입 설명

**TextBlock**:
```typescript
interface TextBlock {
  type: "text";
  subheading?: string;  // 소제목 (optional)
  content: string;      // Markdown 형식 본문
}
```

**TableBlock (히트맵 지원)**:
```typescript
interface TableBlock {
  type: "table";
  title: string;
  subheading?: string;
  headers: Array<{ text: string; value: string }>;
  items: Array<Record<string, string | { value: string; bg_color: string }>>;
  legend?: Array<{ color: string; label: string }>;
}
```

---

## 6. RAG 시스템

### 6.1 RAG 엔진 구조

**파일**: `ai_agent/utils/rag_helpers.py`, `ai_agent/utils/qdrant_vector_store.py`

**2가지 모드 지원**:

| 모드 | 임베딩 모델 | 벡터 차원 | 용도 |
|------|------------|----------|------|
| **qdrant** (기본) | all-MiniLM-L6-v2 | 384 | 새 컬렉션 생성용 |
| **existing** (최신) | multilingual-e5-large | 1024 | 기존 SK 보고서 검색용 |

### 6.2 기존 컬렉션 검색 (ExistingCollectionSearcher)

**사용 가능한 컬렉션**:
```python
AVAILABLE_COLLECTIONS = [
    "2025-SK-Inc.-Sustainability-Report-KOR-TCFD",  # SK 2025 지속가능경영보고서
    "FINAL-2017-TCFD-Report",                       # 국제 TCFD 표준 보고서
    "Physical-Risk-Logic-RAG",                      # 물리적 리스크 논리
    "aal-RAG",                                      # AAL 계산 논리
    "Extreme-Heat-RAG",                             # 극한 고온 리스크
    "Extreme-Cold-RAG",                             # 극한 저온 리스크
    "Drought-RAG",                                  # 가뭄 리스크
    "Water Stress-RAG",                             # 물 부족 리스크
    "Wildfire-RAG",                                 # 산불 리스크
    "River-Flood-RAG",                              # 하천 홍수 리스크
    "Urban Flood-RAG",                              # 도시 홍수 리스크
    "Sea-Level-Rise-RAG",                           # 해수면 상승 리스크
    "Typhon-RAG",                                   # 태풍 리스크
]
```

### 6.3 RAG 사용 예시

**Node 1에서 보고서 템플릿 검색**:
```python
from ai_agent.utils.rag_helpers import RAGEngine

# 기존 컬렉션 검색 모드
rag = RAGEngine(source="existing")

# SK 보고서에서 기후 거버넌스 관련 문단 검색
results = rag.query(
    query="기후 거버넌스 체계 및 이사회 역할",
    collection_names=["2025-SK-Inc.-Sustainability-Report-KOR-TCFD"],
    top_k=5
)

# Citations 생성
citations = rag.get_citations(results)
```

**Node 2-B에서 리스크 컨텍스트 검색**:
```python
from ai_agent.utils.knowledge import RiskContextBuilder

# RiskContextBuilder 사용 (리스크별 정량 데이터 컨텍스트)
risk_context_builder = RiskContextBuilder()
risk_context = risk_context_builder.get_impact_context(["river_flood", "typhoon"])
risk_context_json = risk_context_builder.format_for_prompt(risk_context, format_type="json")
```

---

## 7. Building Characteristics & Additional Data Agent

### 7.1 Building Characteristics Agent (BC Agent)

**파일**: `ai_agent/agents/primary_data/building_characteristics_agent.py`

**역할**:
- **LLM 기반 건물 특성 분석**: ModelOps 점수(H, E, V)를 자연어로 해석
- **리스크별 영향 가이드 생성**: 재무/운영/자산 영향 사전 분석

**실행 시점**: Node 0 (Fork-Join 병렬 실행)

**출력 구조**:
```python
{
    "site_id": {
        "meta": {...},
        "building_data": {...},
        "structural_grade": "A",
        "vulnerabilities": ["노후 배수", "지하 전력실"],
        "resilience": ["신축 건물", "내진 설계"],
        "agent_guidelines": {
            "river_flood": {
                "financial_impact": {
                    "estimated_exposure": "450억원",
                    "key_cost_drivers": ["자산 손상", "운영 중단"]
                },
                "operational_impact": {
                    "estimated_downtime": "48시간",
                    "critical_systems_at_risk": ["데이터센터"]
                },
                "asset_impact": {
                    "vulnerable_assets": ["지하 주차장"],
                    "damage_potential": "높음"
                }
            }
        }
    }
}
```

**Node 2-B에서 활용**:
```python
# BC Agent 가이드라인을 프롬프트에 주입
building_guide = building_data.get(site_id, {}).get("agent_guidelines", {})
prompt += f"<BUILDING_CHARACTERISTICS_GUIDE>\n{building_guide}\n</BUILDING_CHARACTERISTICS_GUIDE>"
```

### 7.2 Additional Data Agent (AD Agent)

**파일**: `ai_agent/agents/primary_data/additional_data_agent.py`

**역할**:
- **Excel 추가 데이터 처리**: 사용자 제공 추가 정보 분석
- **사업장별 가이드라인 생성**: 핵심 인사이트 추출

**실행 시점**: Node 0 (optional, Excel 파일 제공 시)

**출력 구조**:
```python
{
    "status": "active",
    "site_specific_guidelines": {
        "site_id": {
            "guideline": "판교캠퍼스는 IT 인프라가 집중되어 있어 전력 중단에 취약합니다...",
            "key_insights": ["IT 집약", "전력 의존도 높음", "백업 시스템 필요"]
        }
    },
    "summary": "8개 사업장 중 5개가 IT 집약형으로 전력 리스크 관리 필요"
}
```

**Node 2-B에서 활용**:
```python
# AD Agent 가이드라인을 프롬프트에 주입
additional_guide = additional_data.get("site_specific_guidelines", {}).get(site_id, {})
prompt += f"<ADDITIONAL_DATA>\n{additional_guide}\n</ADDITIONAL_DATA>"
```

---

## 8. 주요 개념 정리

### 8.1 AAL (Average Annual Loss)

**정의**: 연평균 자산 손실률 (%)

**계산 공식**:
```
AAL = base_aal × F_vuln × (1 - IR)

여기서:
- base_aal: ModelOps에서 계산한 기본 AAL (확률 × 손상률)
- F_vuln: 취약성 보정 계수 (Vulnerability Score 기반)
- IR: 복원력 계수 (Resilience Factor)
```

**해석**:
- AAL 5%: 자산 가치 100억원 → 연평균 5억원 손실 예상
- AAL 18.2%: 자산 가치 500억원 → 연평균 91억원 손실 예상

### 8.2 H × E × V 공식

**정의**: 물리적 리스크 점수 (100점 만점)

```
Risk Score = Hazard × Exposure × Vulnerability

여기서:
- Hazard (H): 기후 재해 강도 (0~100)
- Exposure (E): 자산 노출 수준 (0~100)
- Vulnerability (V): 건물/사업장 취약성 (0~100)
```

**예시**:
```
H = 80 (하천 홍수 위험 높음)
E = 70 (자산 집중도 높음)
V = 60 (건물 노후화)

Risk Score = (80 × 70 × 60) / 10000 = 33.6
```

### 8.3 SSP 시나리오

**정의**: IPCC AR6 기후 시나리오 (Shared Socioeconomic Pathways)

| 시나리오 | 설명 | 온도 상승 | 특징 |
|---------|------|-----------|------|
| **SSP1-2.6** | 저탄소 | +1.5°C | 적극적 탄소 감축, 재생에너지 확대 |
| **SSP2-4.5** | 중간 | +2.5°C | 현재 수준 정책 유지 (가장 현실적) |
| **SSP3-7.0** | 고탄소 | +3.5°C | 지역주의 강화, 기후 대응 미흡 |
| **SSP5-8.5** | 최악 | +4.5°C | 화석연료 의존 지속, 극심한 기후 변화 |

### 8.4 TCFD 4대 권장사항

**정의**: Task Force on Climate-related Financial Disclosures (기후 관련 재무정보 공개 태스크포스)

| 섹션 | 내용 | 공개 권장사항 |
|------|------|---------------|
| **Governance** | 지배구조 | 이사회 및 경영진의 기후 리스크 감독 체계 |
| **Strategy** | 전략 | 기후 리스크/기회가 사업/전략/재무에 미치는 영향 |
| **Risk Management** | 리스크 관리 | 기후 리스크 식별/평가/관리 프로세스 |
| **Metrics & Targets** | 지표 및 목표 | 기후 리스크/기회 평가에 사용되는 지표 및 목표 |

---

## 9. 실제 사용 예시

### 9.1 전체 플로우 실행

**파일**: `ai_agent/agents/tcfd_report/test_full_flow_real.py`

```python
import asyncio
from langchain_openai import ChatOpenAI
from ai_agent.agents.tcfd_report.node_0_data_preprocessing import DataPreprocessingNode

async def main():
    # 테스트 사이트 ID
    site_ids = [
        "22222222-2222-2222-2222-222222222222",  # SK 판교캠퍼스
        "44444444-4444-4444-4444-444444444444",  # SK u-타워
    ]

    # LLM 클라이언트
    llm_client = ChatOpenAI(model="gpt-4o-mini", temperature=0.3)

    # Node 0 실행
    node_0 = DataPreprocessingNode(
        app_db_url="postgresql://skala:skala1234@localhost:5555/application",
        dw_db_url="postgresql://skala:skala1234@localhost:5555/datawarehouse",
        llm_client=llm_client
    )

    state = await node_0.execute(
        site_ids=site_ids,
        target_years=["2025", "2030", "2050s"]
    )

    # Node 1~6 순차 실행...
    # (생략)

asyncio.run(main())
```

### 9.2 단일 노드 테스트

**Node 2-B만 테스트**:
```python
from ai_agent.agents.tcfd_report.node_2b_impact_analysis_v2 import ImpactAnalysisNode

node_2b = ImpactAnalysisNode(llm_client=llm_client)

result = await node_2b.execute(
    sites_data=sites_data,
    scenario_analysis=scenario_analysis,
    report_template=report_template,
    building_data=building_data,
    additional_data=additional_data
)

print(f"Top 5 risks: {result['top_5_risks']}")
print(f"Impact analyses: {len(result['impact_analyses'])}개")
```

### 9.3 RAG 검색 테스트

**기존 컬렉션 검색**:
```python
from ai_agent.utils.rag_helpers import RAGEngine

rag = RAGEngine(source="existing")

# SK 보고서 검색
results = rag.query(
    query="기후 거버넌스 체계",
    collection_names=["2025-SK-Inc.-Sustainability-Report-KOR-TCFD"],
    top_k=5
)

for result in results:
    print(f"Score: {result['score']}")
    print(f"Content: {result['content'][:200]}...")
```

---

## 10. 문제 해결 가이드

### 10.1 자주 발생하는 문제

#### 문제 1: RAG 검색 실패

**증상**:
```
[RAGEngine] Failed to search: Collection 'xxx' not found
```

**원인**: Qdrant 컬렉션이 생성되지 않음

**해결**:
```bash
# Qdrant 컨테이너 확인
docker ps | grep qdrant

# Qdrant 컬렉션 목록 확인
curl http://localhost:6333/collections

# 컬렉션 재생성
python ai_agent/utils/scripts/upload_reports.py
```

#### 문제 2: LLM 토큰 제한 초과

**증상**:
```
openai.error.InvalidRequestError: This model's maximum context length is 128000 tokens
```

**원인**: 프롬프트 + 입력 데이터가 너무 큼

**해결**:
```python
# Node 2-B에서 Top 5 리스크만 필터링 (이미 적용됨)
top_5_risks = sorted(risks, key=lambda x: x['aal'], reverse=True)[:5]

# 사업장 수 제한
sites_data = sites_data[:8]  # 최대 8개 사업장
```

#### 문제 3: 병렬 LLM 호출 실패

**증상**:
```
asyncio.TimeoutError: LLM response timeout
```

**원인**: 5개 리스크 동시 처리 시 일부 실패

**해결**:
```python
# Timeout 증가
async with asyncio.timeout(300):  # 5분
    results = await asyncio.gather(*tasks, return_exceptions=True)

# 실패한 태스크 재실행
for i, result in enumerate(results):
    if isinstance(result, Exception):
        results[i] = await retry_task(tasks[i])
```

### 10.2 디버깅 팁

**1. LangSmith 트레이싱 활성화**:
```bash
export LANGCHAIN_TRACING_V2=true
export LANGCHAIN_API_KEY=your-langsmith-key
export LANGCHAIN_PROJECT=tcfd-report-debug
```

**2. 로깅 레벨 조정**:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

**3. 중간 결과 저장**:
```python
# Node별 출력 저장
import json
with open("node_2b_output.json", "w") as f:
    json.dump(result, f, indent=2, ensure_ascii=False)
```

### 10.3 성능 최적화

**1. 병렬 처리 최대 활용**:
```python
# Node 2-B, 2-C에서 이미 적용됨
tasks = [analyze_risk(risk) for risk in top_5_risks]
results = await asyncio.gather(*tasks)
```

**2. RAG 캐싱**:
```python
# 동일 쿼리 반복 시 캐시 사용
@lru_cache(maxsize=100)
def cached_rag_query(query: str, top_k: int):
    return rag.query(query, top_k=top_k)
```

**3. LLM 모델 선택**:
```python
# 빠른 분석: gpt-4o-mini (저렴, 빠름)
llm_fast = ChatOpenAI(model="gpt-4o-mini", temperature=0.3)

# 고품질 분석: gpt-4 (비싸지만 정확)
llm_quality = ChatOpenAI(model="gpt-4", temperature=0.3)
```

---

## 11. 참고 자료

### 11.1 주요 파일 위치

```
polaris_backend_fastapi/
├── ai_agent/
│   ├── agents/
│   │   ├── tcfd_report/              # 보고서 생성 노드 (Node 0~6)
│   │   │   ├── node_0_data_preprocessing.py
│   │   │   ├── node_1_template_loading_v2.py
│   │   │   ├── node_2a_scenario_analysis_v2.py
│   │   │   ├── node_2b_impact_analysis_v2.py
│   │   │   ├── node_2c_mitigation_strategies_v2.py
│   │   │   ├── node_3_strategy_section_v2.py
│   │   │   ├── node_4_validator_v2.py
│   │   │   ├── node_5_composer_v2.py
│   │   │   ├── node_6_finalizer_v2.py
│   │   │   ├── state.py              # LangGraph State 정의
│   │   │   ├── schemas.py            # Pydantic 스키마 (TextBlock, TableBlock)
│   │   │   └── test_full_flow_real.py # 전체 플로우 테스트
│   │   └── primary_data/             # BC/AD Agent
│   │       ├── building_characteristics_agent.py
│   │       └── additional_data_agent.py
│   └── utils/
│       ├── rag_helpers.py            # RAG 엔진
│       ├── qdrant_vector_store.py    # Qdrant 클라이언트
│       └── knowledge.py              # RiskContextBuilder
├── test_output/
│   └── report_json_for_front.json    # 프론트엔드 전달용 JSON 샘플
└── docs/
    ├── for_better_understanding/     # 이해를 돕는 문서들
    │   └── report_agent_overview.md  # 이 문서
    └── progress/
        └── tcfd_prompt_analysis_2025-12-16.md # 프롬프트 품질 분석
```

### 11.2 관련 문서

- [README_251216.md](../../README_251216.md) - 전체 시스템 상세 문서
- [README_SUMMARY_251216.md](../../README_SUMMARY_251216.md) - 빠른 시작 가이드
- [tcfd_prompt_analysis_2025-12-16.md](../progress/tcfd_prompt_analysis_2025-12-16.md) - 프롬프트 품질 분석
- [ai_understanding.md](./ai_understanding.md) - AI 시스템 전체 이해
- [tcfd_guide.md](./tcfd_guide.md) - TCFD 프레임워크 가이드

---

## 12. 다음 단계

### 12.1 현재 진행 상황

- ✅ Node 0~6 구현 완료 (v2.0)
- ✅ RAG 시스템 고도화 (1024 차원 지원)
- ✅ 프론트엔드 JSON 구조 확정
- ✅ BC/AD Agent 통합
- ✅ 병렬 처리 최적화 (~30초)

### 12.2 개선 예정

- 🔄 Node 2-B 프롬프트 개선 (Few-shot 예제 추가)
- 🔄 Node 2-C ROI 계산 로직 강화
- 🔄 Node 4 검증 규칙 추가 (TCFD 세부 체크리스트)
- 🔄 다국어 지원 확대 (영어 보고서 생성)

### 12.3 추가 기능

- ⏳ PDF 출력 지원
- ⏳ 차트/그래프 자동 생성
- ⏳ 사용자 피드백 반영 (Refiner 루프 개선)

---

## 마치며

이 문서는 **TCFD 보고서 생성 에이전트**의 전체 구조를 빠르게 이해하기 위한 종합 가이드입니다. 다음 대화 시작 시 이 문서를 참조하면 컨텍스트를 빠르게 복원할 수 있습니다.

**문의 사항**:
- 코드 관련: `ai_agent/agents/tcfd_report/` 폴더 참조
- 프롬프트 개선: `docs/progress/tcfd_prompt_analysis_2025-12-16.md` 참조
- 전체 시스템: `README_251216.md` 참조

---

**작성자**: Claude Code
**최종 업데이트**: 2025-12-16
**버전**: v2.0
