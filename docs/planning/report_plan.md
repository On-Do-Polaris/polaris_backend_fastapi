# TCFD 보고서 생성 Agent 설계 문서

**작성일:** 2025-12-14
**버전:** v1.0
**선택안:** 후보 1 (사업장별 병렬 분석 + 통합 구조)

---

## 목차

1. [개요](#개요)
2. [시스템 아키텍처](#시스템-아키텍처)
3. [워크플로우 설계](#워크플로우-설계)
4. [Node별 상세 구현](#node별-상세-구현)
5. [출력 구조](#출력-구조)
6. [구현 로드맵](#구현-로드맵)
7. [참고 자료](#참고-자료)

---

## 개요

### 프로젝트 목표

**기업 ESG 보고서의 TCFD(기후변화 관련 재무정보 공개) 섹션을 생성하는 AI Agent 시스템 구축**

### 핵심 요구사항

- **물리적 리스크 중심**: 9가지 물리적 리스크 분석 (전환 리스크 제외)
- **다중 사업장 지원**: N개 사업장 개별 + 통합 분석
- **TCFD 권고안 준수**: 4개 핵심 영역 (Governance, Strategy, Risk Management, Metrics & Targets) + Appendix
- **하이브리드 생성**: 데이터 있는 섹션은 AI 생성 + 템플릿 기반 보완
- **Excel 데이터 통합**: 사용자 제공 추가 데이터 반영

### 기술 스택

- **LLM**: GPT-4.1
- **목표 분량**: 12-20페이지 (TCFD 권장)
- **생성 시간**: 4-6분 (3개 사업장 기준)
- **출력 형식**: JSON (JSONB로 DB 저장) + PDF (Optional)

---

## 시스템 아키텍처

### 활용 가능한 데이터 소스

#### 1. 물리적 리스크 분석 결과 (ModelOps)

- **H×E×V 점수**: 9가지 리스크별, 4가지 SSP 시나리오별
- **AAL (연평균 손실액)**: 연도별 타임라인 (2024-2100), 시나리오별
- **위험 분포**: bin별 확률 분포 (bin_probs)

#### 2. 리스크 인사이트 지식베이스 (Knowledge)

- **risk_insight.py** (1,395줄): 9가지 리스크 메타데이터
  - 정의, 과학적 근거, 산출 방법, 영향 분야, 완화 키워드
- **RiskContextBuilder**: Agent별 맞춤 컨텍스트 추출

#### 3. 건물 취약성 분석 (AI)

- **vulnerability_analysis_agent**: 건물 대장 데이터 기반 LLM 분석
  - 취약성 요인 (vulnerabilities)
  - 회복력 요인 (resilience)
  - 구조 등급 평가 (A~E)
  - LLM 생성 분석 보고서
- **building_characteristics_agent**: 건물 특성 요약 생성

#### 4. 사업장 정보

- **sites 테이블**: 기본 정보 (이름, 주소, 좌표)
- **건물HUB API**: 건물 메타 정보 (구조, 용도, 면적, 준공 연도)

#### 5. 사용자 제공 추가 데이터

- **Excel 업로드**: 건물, 자산, 보험, 재무, 커스텀 데이터
- **site_additional_data 테이블**: JSONB로 저장

#### 6. RAG 데이터

- **Qdrant Vector DB**: 기존 ESG/TCFD 보고서, TCFD 권고안
- **컬렉션**: `esg_tcfd_reports`

### 제한된 또는 없는 데이터 소스 (템플릿으로 보완)

- **Governance**: 이사회 구성, ESG위원회 정보
- **전환 리스크**: 탄소세, 규제 변화, 기술 전환
- **GHG 배출량**: Scope 1/2/3
- **RE100, Net Zero**: 재생에너지 전환율, 감축 목표
- **공급망**: 탄소 집약도, Scope 3 세부
- **3자 검증**: 검증 의견서

---

## 워크플로우 설계

### 전체 노드 구조도

```
┌─────────────────────────────────────────────────────────────┐
│ Node 0: Multi-Site Data Preprocessing                       │
│ - Excel 파싱 (pandas)                                       │
│ - AdditionalDataHelper: Agent별 가이드라인 생성             │
│ - DB에서 사업장별 데이터 로딩                               │
└────────────────────────┬────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────┐
│ Node 1: Report Profile & Template Loading                   │
│ - RAG: 기존 보고서 스타일 참조                              │
│ - TCFD 구조 템플릿 로딩                                     │
│ - 4가지 섹션별 필수 요소 체크리스트                         │
└────────────────────────┬────────────────────────────────────┘
                         ↓
         ┌───────────────┼───────────────┐
         ↓               ↓               ↓
┌─────────────┐ ┌─────────────┐ ┌─────────────┐
│ Node 2-A:   │ │ Node 2-B:   │ │ Node 2-C:   │
│ Site        │ │ Site        │ │ Site        │
│ Analyzer #1 │ │ Analyzer #2 │ │ Analyzer #3 │
│             │ │             │ │             │
│ - 9가지     │ │ (동일)      │ │ (동일)      │
│   리스크별  │ │             │ │             │
│   영향분석  │ │             │ │             │
│ - P1~P9     │ │             │ │             │
│   섹션 생성 │ │             │ │             │
│ - 6 pages   │ │ - 6 pages   │ │ - 6 pages   │
└──────┬──────┘ └──────┬──────┘ └──────┬──────┘
       └───────────────┼───────────────┘
                       ↓
┌─────────────────────────────────────────────────────────────┐
│ Node 3: Portfolio Aggregator & Comparator                   │
│ - 전체 AAL 합산                                             │
│ - Top 5 리스크 식별 (전체 포트폴리오 기준)                 │
│ - 사업장 간 비교 분석 (AAL, 취약성)                        │
│ - Heatmap 테이블 생성 (색상 코딩)                          │
│ - 2-3 pages                                                 │
└────────────────────────┬────────────────────────────────────┘
                         ↓
         ┌───────────────┼───────────────┐
         ↓                               ↓
┌─────────────────────────┐    ┌─────────────────────────┐
│ Node 4:                 │    │ Node 5:                 │
│ Risk Management         │    │ Metrics & Targets       │
│ Section Generator       │    │ Section Generator       │
│                         │    │                         │
│ - 리스크 관리 프로세스  │    │ - AAL 추이 그래프       │
│ - 통합 리스크 관리      │    │ - 시나리오별 비교       │
│ - 완화 조치 체계        │    │ - KPI 지표              │
│ - 3 pages               │    │ - 4 pages               │
└────────┬────────────────┘    └────────┬────────────────┘
         └───────────────┬──────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────┐
│ Node 6: Strategy Section Generator                          │
│ - 사업장별 분석 결과 통합                                   │
│ - 포트폴리오 분석 결과 통합                                 │
│ - P1~P5 영향 분석 및 대응 방안 (Top 5 리스크만)            │
│ - Heatmap 테이블 삽입                                       │
│ - 7 pages                                                   │
└────────────────────────┬────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────┐
│ Node 7: Governance & Appendix Template Generator            │
│ - Governance 섹션 (템플릿 기반, 변수 치환)                  │
│ - Appendix 섹션 생성:                                       │
│   * 상세 데이터 테이블 (9가지 리스크 전체)                 │
│   * 방법론 (AAL 산출, H×E×V 프레임워크)                    │
│   * 데이터 출처 (기상청, 환경부, IPCC 등)                  │
│   * 용어 정의 (AAL, SSP, RCP 등)                           │
│ - 3-4 pages                                                 │
└────────────────────────┬────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────┐
│ Node 8: Report Composer                                     │
│ - 전체 섹션 순서 조립:                                      │
│   1. Executive Summary (Node 6에서 자동 생성)              │
│   2. Governance (Node 7)                                    │
│   3. Strategy (Node 6)                                      │
│   4. Risk Management (Node 4)                               │
│   5. Metrics & Targets (Node 5)                             │
│   6. Appendix (Node 7)                                      │
│ - 페이지 번호 부여                                          │
│ - 목차 생성                                                 │
│ - JSON 구조화                                               │
└────────────────────────┬────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────┐
│ Node 9: Quality Validator                                   │
│ - TCFD 7대 원칙 검증:                                       │
│   * Relevant, Specific, Clear, Consistent,                 │
│     Comparable, Reliable, Timely                            │
│ - 필수 요소 누락 체크                                       │
│ - 데이터 일관성 검증 (AAL 합계, 리스크 개수 등)            │
│ - 개선 필요 사항 리스트 반환                                │
└────────────────────────┬────────────────────────────────────┘
                         ↓
                  ┌──────┴──────┐
                  ↓             ↓
            [Pass]          [Needs Fix]
              ↓                 ↓
              │    ┌────────────┘
              │    │
              ↓    ↓
┌─────────────────────────────────────────────────────────────┐
│ Node 10: Refiner (조건부)                                   │
│ - Validator의 피드백 기반 수정                              │
│ - 최대 2회 재시도                                           │
└────────────────────────┬────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────┐
│ Node 11: Finalizer                                          │
│ - JSON을 JSONB로 DB 저장 (reports 테이블)                  │
│ - (Optional) PDF 생성 (weasyprint/reportlab)               │
│ - 메타데이터 업데이트 (생성 시간, 페이지 수 등)            │
│ - 완료 응답 반환                                            │
└─────────────────────────────────────────────────────────────┘
```

### 병렬 처리 전략

**병렬 Node (동시 실행):**

- **Node 2-A, 2-B, 2-C**: 사업장별 독립 분석 (데이터 의존성 없음)
- **Node 4, 5**: Risk Management와 Metrics & Targets는 Node 3 결과만 사용하므로 병렬 가능

**순차 Node (직렬 실행):**

- **Node 0 → 1 → 2 → 3 → 6 → 7 → 8 → 9 → (10) → 11**

---

## Node별 상세 구현

### Node 0: Multi-Site Data Preprocessing

**목적:** 사용자 입력 데이터(Excel + 사업장 ID 리스트)를 파싱하고 Agent별 가이드라인 생성

**입력:**

```python
{
    "site_ids": [123, 124, 125],
    "excel_file": "additional_data.xlsx",  # Optional
    "user_id": 456
}
```

**처리 로직:**

#### 1. Excel 파싱

```python
import pandas as pd

def parse_excel(file_path: str) -> dict:
    """
    Excel 파일에서 5가지 카테고리 데이터 추출
    """
    df = pd.read_excel(file_path, sheet_name=None)  # 모든 시트 읽기

    additional_data = {
        "building": {},
        "asset": {},
        "power": {},
        "insurance": {},
        "custom": {}
    }

    # 각 시트별 데이터 파싱
    for sheet_name, sheet_df in df.items():
        category = determine_category(sheet_name)  # "건물", "자산" 등 → category 매핑
        additional_data[category][sheet_name] = sheet_df.to_dict(orient='records')

    return additional_data
```

#### 2. AdditionalDataHelper 호출

```python
from ai_agent.utils.additional_data_helper import AdditionalDataHelper

helper = AdditionalDataHelper()

agent_configs = [
    {"agent_name": "Site Analyzer", "role": "사업장별 물리적 리스크 분석"},
    {"agent_name": "Strategy Generator", "role": "TCFD Strategy 섹션 작성"},
    {"agent_name": "Risk Management Generator", "role": "TCFD Risk Management 섹션 작성"}
]

guidelines = helper.generate_guidelines(
    additional_data=additional_data,
    agent_configs=agent_configs
)
```

**출력 예시:**

```python
{
    "Site Analyzer": {
        "relevant_data": {
            "building": {"비상전력": "자가발전기 2대, UPS 30분"},
            "insurance": {"보험금액": "100억원", "담보범위": "화재/풍수해"}
        },
        "guideline": "건물에 자가발전기가 있으므로 정전 시 회복력이 높습니다. 보험으로 홍수 피해가 일부 완화됩니다."
    }
}
```

#### 3. 사업장별 데이터 로딩

```python
async def load_site_data(site_ids: list[int]) -> list[dict]:
    """
    DB에서 사업장별 데이터 조회 및 구조화
    """
    sites_data = []

    for site_id in site_ids:
        # 1. 사업장 기본 정보
        site_info = await db.query(Site).filter(Site.id == site_id).first()

        # 2. 물리적 리스크 분석 결과
        risk_results = await db.query(PhysicalRiskResult).filter(
            PhysicalRiskResult.site_id == site_id
        ).all()

        # 3. AAL 데이터
        aal_data = await db.query(AAL).filter(AAL.site_id == site_id).all()

        # 4. 건물 취약성 분석 (LLM 생성)
        vulnerability = await db.query(BuildingVulnerability).filter(
            BuildingVulnerability.site_id == site_id
        ).first()

        # 5. 추가 데이터
        additional_data = await db.query(SiteAdditionalData).filter(
            SiteAdditionalData.site_id == site_id
        ).first()

        sites_data.append({
            "site_id": site_id,
            "site_info": site_info.to_dict(),
            "risk_results": [r.to_dict() for r in risk_results],
            "aal_data": [a.to_dict() for a in aal_data],
            "vulnerability": vulnerability.to_dict() if vulnerability else None,
            "additional_data": additional_data.data if additional_data else {}
        })

    return sites_data
```

**출력:**

```python
{
    "sites_data": [
        {
            "site_id": 123,
            "site_info": {"name": "서울 본사", "address": "..."},
            "risk_results": [...],
            "aal_data": [...],
            "vulnerability": {...},
            "additional_data": {...}
        },
        # ... site 124, 125
    ],
    "agent_guidelines": {
        "Site Analyzer": {...},
        "Strategy Generator": {...},
        "Risk Management Generator": {...}
    }
}
```

---

### Node 1: Report Profile & Template Loading

**목적:** TCFD 보고서 구조 템플릿 및 기존 보고서 스타일 참조 정보 로딩

**처리 로직:**

#### 1. RAG 쿼리 (기존 보고서 스타일 참조)

```python
from ai_agent.utils.rag_helpers import RAGEngine

rag = RAGEngine()

# 쿼리 1: TCFD Strategy 섹션 스타일
strategy_examples = rag.query(
    query_text="TCFD Strategy section physical risk analysis examples",
    top_k=3
)

# 쿼리 2: 히트맵 테이블 예시
heatmap_examples = rag.query(
    query_text="climate risk heatmap table color-coded by scenario",
    top_k=2
)

citations = rag.get_citations(strategy_examples + heatmap_examples)
```

#### 2. TCFD 구조 템플릿 로딩

```python
tcfd_structure = {
    "sections": [
        {
            "id": "executive_summary",
            "title": "Executive Summary",
            "required": True,
            "max_pages": 2,
            "key_elements": ["핵심 리스크 요약", "재무 영향", "대응 전략"]
        },
        {
            "id": "governance",
            "title": "Governance",
            "required": True,
            "max_pages": 2,
            "key_elements": [
                "이사회 감독 체계",
                "경영진 역할 및 책임",
                "ESG위원회 구성 및 활동"
            ],
            "data_available": False,  # 템플릿 사용
            "template_path": "templates/governance.md"
        },
        {
            "id": "strategy",
            "title": "Strategy",
            "required": True,
            "max_pages": 8,
            "key_elements": [
                "리스크 및 기회 식별 (단기/중기/장기)",
                "사업 및 재무 영향 분석",
                "시나리오 기반 회복력 평가"
            ],
            "data_available": True  # AI 생성
        },
        {
            "id": "risk_management",
            "title": "Risk Management",
            "required": True,
            "max_pages": 3,
            "key_elements": [
                "리스크 식별 프로세스",
                "리스크 관리 프로세스",
                "전사 리스크 관리 통합"
            ],
            "data_available": True  # AI 생성
        },
        {
            "id": "metrics_targets",
            "title": "Metrics and Targets",
            "required": True,
            "max_pages": 4,
            "key_elements": [
                "기후 관련 지표 (AAL 등)",
                "온실가스 배출량 (Scope 1/2/3)",
                "감축 목표 및 달성 현황"
            ],
            "data_available": "partial"  # 일부 AI 생성, 일부 템플릿
        },
        {
            "id": "appendix",
            "title": "Appendix",
            "required": True,
            "max_pages": 5,
            "key_elements": [
                "상세 데이터 테이블",
                "방법론 설명",
                "데이터 출처",
                "용어 정의"
            ],
            "data_available": True  # AI 생성
        }
    ],
    "quality_principles": [
        "Relevant", "Specific and Complete", "Clear and Balanced",
        "Consistent over time", "Comparable", "Reliable and Verifiable", "Timely"
    ]
}
```

**출력:**

```python
{
    "tcfd_structure": tcfd_structure,
    "style_references": {
        "strategy_examples": strategy_examples,
        "heatmap_examples": heatmap_examples,
        "citations": citations
    }
}
```

---

### Node 2-A/B/C: Site Analyzer (Parallel)

**목적:** 각 사업장별로 9가지 물리적 리스크에 대한 영향 분석 및 대응 방안 생성

**입력 (Node 2-A 예시):**

```python
{
    "site_data": sites_data[0],  # site_id=123
    "agent_guideline": "건물에 자가발전기가 있으므로...",
    "risk_insight": RiskContextBuilder.get_impact_context()  # 선택적 지식 주입
}
```

**처리 로직:**

#### 1. 리스크별 영향 분석 (P1~P9 섹션 생성)

```python
from ai_agent.utils.knowledge.risk_context_builder import RiskContextBuilder
from langchain.chat_models import ChatOpenAI

llm = ChatOpenAI(model="gpt-4-1106-preview", temperature=0.3)
context_builder = RiskContextBuilder()

risk_analyses = []

for risk_result in site_data["risk_results"]:
    risk_type = risk_result["risk_type"]  # "river_flood"

    # 선택적 지식 추출
    risk_context = context_builder.get_impact_context(risk_type)

    # AAL 데이터 필터링
    aal_for_risk = [
        a for a in site_data["aal_data"]
        if a["risk_type"] == risk_type
    ]

    # 프롬프트 생성
    prompt = f"""
당신은 물리적 기후 리스크 분석 전문가입니다.
{site_data["site_info"]["name"]}의 {risk_type} 리스크를 분석하세요.

### 제공된 데이터
**리스크 점수 (H×E×V):**
- Hazard: {risk_result["hazard_score"]}
- Exposure: {risk_result["exposure_score"]}
- Vulnerability: {risk_result["vulnerability_score"]}
- Total: {risk_result["total_score"]}

**AAL (연평균 손실액):**
- SSP1-2.6: {aal_for_risk[0]["aal_ssp1"]}%
- SSP2-4.5: {aal_for_risk[0]["aal_ssp2"]}%
- SSP5-8.5: {aal_for_risk[0]["aal_ssp5"]}%

**건물 취약성:**
{site_data["vulnerability"]["analysis_report"]}

**추가 제공 정보:**
{agent_guideline}

### 리스크 인사이트 (과학적 근거)
{risk_context}

### 요청 사항
아래 형식으로 분석 보고서를 작성하세요:

### P{i}. {risk_type_korean}

**영향 분석**
- 재무적 영향: AAL 기반 손실액 추정, 최악 시나리오 고려
- 운영적 영향: 사업 중단, 생산성 저하, 공급망 차질 등
- 자산 영향: 건물/설비 손상 가능성, 내구연한 단축

**대응 방안**
- 단기 조치 (1-2년): [구체적 조치 2-3개]
- 중기 조치 (3-5년): [구체적 조치 2-3개]
- 장기 조치 (5년+): [구체적 조치 2-3개]

**우선순위**: [높음/중간/낮음]
"""

    analysis = llm.invoke(prompt)
    risk_analyses.append({
        "risk_type": risk_type,
        "analysis": analysis
    })
```

#### 2. 사업장 종합 요약 생성

```python
summary_prompt = f"""
{site_data["site_info"]["name"]}의 9가지 물리적 리스크 분석을 종합하세요.

## Top 3 리스크
- {top_3_risks}

## 총 AAL
- {total_aal}%

## 핵심 권고 사항
- [3-5 bullet points]
"""

site_summary = llm.invoke(summary_prompt)
```

**출력 (Node 2-A):**

```python
{
    "site_id": 123,
    "site_name": "서울 본사",
    "risk_analyses": [
        {
            "risk_type": "extreme_heat",
            "risk_name": "극심한 고온",
            "impact_analysis": {
                "financial": "AAL 2.5%로 연간 약 5억원 손실 예상",
                "operational": "냉방 부하 증가로 전력 소비량 5-10% 증가 예상",
                "asset": "냉각탑 노후화, HVAC 시스템 교체 필요"
            },
            "mitigation_strategies": {
                "short_term": ["고온 대비 냉각탑 점검", "피크 전력 사용 관리"],
                "mid_term": ["고효율 냉방 시스템 교체", "단열 성능 개선"],
                "long_term": ["건물 외피 재설계", "재생에너지 도입"]
            },
            "priority": "높음",
            "markdown_content": "### P1. 극심한 고온\n\n**영향 분석**\n..."
        },
        // ... 나머지 8개 리스크
    ],
    "site_summary": {
        "top_3_risks": ["river_flood", "urban_flood", "extreme_heat"],
        "total_aal": 18.3,
        "key_strategies": [
            "홍수 방어 시설 우선 구축",
            "냉방 시스템 효율화",
            "재생에너지 전환 검토"
        ]
    },
    "total_pages": 6
}
```

---

### Node 3: Portfolio Aggregator & Comparator

**목적:** 사업장별 결과를 통합하고 포트폴리오 수준 분석 수행

**입력:**

```python
{
    "site_123_analysis": Node_2A_output,
    "site_124_analysis": Node_2B_output,
    "site_125_analysis": Node_2C_output
}
```

**처리 로직:**

#### 1. 포트폴리오 AAL 집계

```python
def aggregate_portfolio_aal(site_analyses: list[dict]) -> dict:
    """
    전체 포트폴리오의 AAL 합산 및 Top 리스크 식별
    """
    total_aal = 0
    risk_aal_map = {}  # {risk_type: total_aal}

    for site_analysis in site_analyses:
        for risk_analysis in site_analysis["risk_analyses"]:
            risk_type = risk_analysis["risk_type"]
            aal = risk_analysis["impact_analysis"].get("aal_value", 0)

            total_aal += aal
            risk_aal_map[risk_type] = risk_aal_map.get(risk_type, 0) + aal

    # Top 5 리스크 추출
    top_5_risks = sorted(risk_aal_map.items(), key=lambda x: x[1], reverse=True)[:5]

    return {
        "total_aal": total_aal,
        "top_5_risks": [
            {"risk_type": r[0], "aal": r[1], "percentage": r[1]/total_aal*100}
            for r in top_5_risks
        ],
        "risk_aal_map": risk_aal_map
    }
```

#### 2. 히트맵 테이블 생성 (색상 코딩)

```python
def generate_heatmap_table(site_analyses: list[dict], portfolio_data: dict) -> dict:
    """
    사업장 × 리스크 × 시나리오 히트맵 테이블 생성

    색상 기준 (SK ESG 2025 스타일):
    - Gray: 0-3% (낮음)
    - Yellow: 3-10% (중간)
    - Orange: 10-30% (높음)
    - Red: 30%+ (매우 높음)
    """

    def get_color(aal_value: float) -> str:
        if aal_value < 3:
            return "gray"
        elif aal_value < 10:
            return "yellow"
        elif aal_value < 30:
            return "orange"
        else:
            return "red"

    # 테이블 헤더
    headers = [
        {"text": "사업장", "rowspan": 2},
        {"text": "리스크 유형", "colspan": len(portfolio_data["top_5_risks"])},
        {"text": "Total AAL", "rowspan": 2}
    ]

    sub_headers = [r["risk_type"] for r in portfolio_data["top_5_risks"]]

    # 테이블 행 생성
    rows = []
    for site_analysis in site_analyses:
        row = {
            "site_name": site_analysis["site_name"],
            "cells": []
        }

        for top_risk in portfolio_data["top_5_risks"]:
            risk_type = top_risk["risk_type"]

            # 해당 사업장의 해당 리스크 AAL 찾기
            risk_data = next(
                (r for r in site_analysis["risk_analyses"] if r["risk_type"] == risk_type),
                None
            )

            if risk_data:
                aal = risk_data["impact_analysis"].get("aal_value", 0)
                row["cells"].append({
                    "value": f"{aal:.1f}%",
                    "color": get_color(aal),
                    "bg_color": get_color(aal)
                })
            else:
                row["cells"].append({
                    "value": "-",
                    "color": "gray",
                    "bg_color": "gray"
                })

        # Total AAL
        total_site_aal = site_analysis["site_summary"]["total_aal"]
        row["cells"].append({
            "value": f"{total_site_aal:.1f}%",
            "color": get_color(total_site_aal),
            "bg_color": get_color(total_site_aal)
        })

        rows.append(row)

    return {
        "type": "heatmap_table",
        "title": "사업장별 물리적 리스크 AAL 분포 (SSP2-4.5 시나리오)",
        "headers": headers,
        "sub_headers": sub_headers,
        "rows": rows,
        "legend": [
            {"color": "gray", "label": "0-3% (낮음)"},
            {"color": "yellow", "label": "3-10% (중간)"},
            {"color": "orange", "label": "10-30% (높음)"},
            {"color": "red", "label": "30%+ (매우 높음)"}
        ]
    }
```

#### 3. 사업장 비교 분석

```python
comparison_prompt = f"""
다음 3개 사업장의 기후 리스크 분석 결과를 비교하고 인사이트를 도출하세요:

**서울 본사:**
- Total AAL: 18.3%
- Top 3: 하천 범람 (7.2%), 도시 침수 (5.1%), 극심한 고온 (2.5%)

**대전 데이터센터:**
- Total AAL: 12.5%
- Top 3: 극심한 고온 (4.8%), 가뭄 (3.2%), 태풍 (2.1%)

**부산 물류센터:**
- Total AAL: 22.1%
- Top 3: 태풍 (9.3%), 해수면 상승 (6.2%), 하천 범람 (3.8%)

### 요청 사항:
1. 포트폴리오 전체의 가장 큰 리스크는 무엇인가?
2. 사업장 간 차이가 발생하는 이유는? (지리적 요인, 자산 특성 등)
3. 우선 투자가 필요한 사업장은?
"""

comparison_analysis = llm.invoke(comparison_prompt)
```

**출력:**

```python
{
    "portfolio_summary": {
        "total_sites": 3,
        "total_aal": 52.9,
        "average_aal": 17.6,
        "top_5_risks": [
            {"risk_type": "river_flood", "aal": 18.2, "percentage": 34.4},
            {"risk_type": "typhoon", "aal": 11.4, "percentage": 21.5},
            {"risk_type": "urban_flood", "aal": 8.7, "percentage": 16.4},
            {"risk_type": "extreme_heat", "aal": 7.3, "percentage": 13.8},
            {"risk_type": "sea_level_rise", "aal": 6.2, "percentage": 11.7}
        ]
    },
    "heatmap_table": {
        "type": "heatmap_table",
        "title": "사업장별 물리적 리스크 AAL 분포",
        "rows": [
            {
                "site_name": "서울 본사",
                "cells": [
                    {"value": "7.2%", "bg_color": "yellow"},
                    {"value": "2.1%", "bg_color": "gray"},
                    {"value": "5.1%", "bg_color": "yellow"},
                    {"value": "2.5%", "bg_color": "gray"},
                    {"value": "0.0%", "bg_color": "gray"},
                    {"value": "18.3%", "bg_color": "orange"}
                ]
            },
            // ... 나머지 사업장
        ]
    },
    "comparison_analysis": "포트폴리오 전체적으로 하천 범람이 가장 큰 리스크로...",
    "total_pages": 2
}
```

---

### Node 4: Risk Management Section Generator

**목적:** TCFD Risk Management 섹션 생성

**입력:**

```python
{
    "portfolio_summary": Node_3_output["portfolio_summary"],
    "top_5_risks": Node_3_output["portfolio_summary"]["top_5_risks"]
}
```

**처리 로직:**

```python
risk_mgmt_prompt = f"""
당신은 TCFD 보고서의 Risk Management 섹션을 작성하는 전문가입니다.

### 제공된 정보
**포트폴리오 Top 5 리스크:**
{json.dumps(portfolio_summary["top_5_risks"], ensure_ascii=False, indent=2)}

### 요청 사항
아래 구조에 따라 Risk Management 섹션을 작성하세요:

## 3. Risk Management

### 3.1 기후 리스크 식별 및 평가 프로세스

우리는 다음과 같은 체계적인 프로세스를 통해 물리적 기후 리스크를 식별하고 평가합니다:

1. **리스크 식별 (Identification)**
   - [H×E×V 프레임워크 설명]
   - [9가지 물리적 리스크 식별 방법]
   - [시나리오 분석 (SSP 1-2.6, 2-4.5, 5-8.5)]

2. **리스크 평가 (Assessment)**
   - [AAL (연평균 손실액) 산출 방법]
   - [재무적 영향도 평가 기준]
   - [우선순위 결정 매트릭스]

3. **리스크 모니터링 (Monitoring)**
   - [연간 재평가 주기]
   - [조기 경보 시스템]

### 3.2 리스크 관리 프로세스

식별된 리스크에 대해 다음과 같은 관리 활동을 수행합니다:

1. **완화 (Mitigation)**
   - Top 5 리스크에 대한 구체적 완화 조치 [각 리스크별 2-3개]

2. **적응 (Adaptation)**
   - [장기적 회복력 강화 방안]

3. **이전 (Transfer)**
   - [보험 활용 전략]

### 3.3 전사 리스크 관리 통합

기후 리스크는 다음과 같이 전사 리스크 관리 체계에 통합됩니다:

- [ERM (Enterprise Risk Management) 연계]
- [환경경영시스템 (ISO 14001) 통합]
- [재무 리스크 관리와의 연계]

**작성 원칙:**
- 구체적이고 실행 가능한 조치 중심
- TCFD 권고안의 3가지 하위 권고 (a, b, c) 모두 포함
- 2-3 페이지 분량
"""

risk_mgmt_section = llm.invoke(risk_mgmt_prompt)
```

**출력:**

```python
{
    "section_id": "risk_management",
    "title": "Risk Management",
    "content": risk_mgmt_section,
    "blocks": [
        {
            "type": "text",
            "subheading": "3.1 기후 리스크 식별 및 평가 프로세스",
            "content": "..."
        },
        {
            "type": "diagram",
            "title": "기후 리스크 관리 프로세스 흐름도",
            "data": {
                "nodes": ["식별", "평가", "완화", "모니터링"],
                "edges": [...]
            }
        },
        {
            "type": "text",
            "subheading": "3.2 리스크 관리 프로세스",
            "content": "..."
        }
    ],
    "total_pages": 3
}
```

---

### Node 5: Metrics & Targets Section Generator

**목적:** TCFD Metrics and Targets 섹션 생성

**입력:**

```python
{
    "portfolio_summary": Node_3_output["portfolio_summary"],
    "site_analyses": [Node_2A_output, Node_2B_output, Node_2C_output]
}
```

**처리 로직:**

```python
metrics_prompt = f"""
당신은 TCFD 보고서의 Metrics and Targets 섹션을 작성하는 전문가입니다.

### 제공된 정보
**포트폴리오 전체 AAL:** {portfolio_summary["total_aal"]}%
**Top 5 리스크:** {portfolio_summary["top_5_risks"]}

### 요청 사항
아래 구조에 따라 Metrics and Targets 섹션을 작성하세요:

## 4. Metrics and Targets

### 4.1 기후 관련 지표

우리는 다음과 같은 지표를 통해 물리적 기후 리스크를 측정하고 관리합니다:

**1. AAL (Annual Average Loss, 연평균 손실액)**
- 정의: 기후 리스크로 인한 연간 예상 손실액의 평균
- 2024년 기준: 포트폴리오 전체 {total_aal}%
- 시나리오별 차이:
  - SSP1-2.6 (저탄소): [값]
  - SSP2-4.5 (중간): [값]
  - SSP5-8.5 (고탄소): [값]

**2. 리스크 점수 (H×E×V)**
- [각 사업장별 평균 점수]

**3. 회복력 지표**
- [건물 구조 등급 분포]
- [보험 커버리지 비율]

### 4.2 온실가스 배출량 (템플릿)

*주: 현재 Scope 1/2/3 배출량 데이터가 제한적이므로, 향후 보완 예정*

- Scope 1: [추정치 또는 "N/A"]
- Scope 2: [추정치 또는 "N/A"]
- Scope 3: [추정치 또는 "N/A"]

### 4.3 목표 및 성과

**물리적 리스크 감축 목표:**
- 2030년까지 포트폴리오 AAL을 [기준년도] 대비 20% 감축
- 고위험(AAL 30% 이상) 사업장 제로화

**진행 현황:**
- [현재 달성률]
- [주요 이정표]

**차트 삽입:**
- [AAL 추이 그래프 (2024-2040)]
- [시나리오별 비교 차트]
"""

metrics_section = llm.invoke(metrics_prompt)
```

**차트 데이터 생성:**

```python
def generate_aal_trend_chart(site_analyses: list[dict]) -> dict:
    """
    AAL 추이 차트 데이터 생성 (연도별 예측)
    """
    years = list(range(2024, 2041, 2))  # 2024, 2026, ..., 2040

    series = []
    for scenario in ["SSP1-2.6", "SSP2-4.5", "SSP5-8.5"]:
        data = []
        for year in years:
            # AAL 데이터에서 해당 연도 추출 (단순화)
            aal_value = calculate_aal_for_year(year, scenario, site_analyses)
            data.append(aal_value)

        series.append({
            "name": scenario,
            "data": data,
            "color": get_scenario_color(scenario)
        })

    return {
        "type": "line_chart",
        "title": "포트폴리오 AAL 추이 (2024-2040)",
        "data": {
            "categories": years,
            "y_unit": "%",
            "series": series
        }
    }
```

**출력:**

```python
{
    "section_id": "metrics_targets",
    "title": "Metrics and Targets",
    "content": metrics_section,
    "blocks": [
        {
            "type": "text",
            "subheading": "4.1 기후 관련 지표",
            "content": "..."
        },
        {
            "type": "line_chart",
            "title": "포트폴리오 AAL 추이 (2024-2040)",
            "data": {
                "categories": [2024, 2026, 2028, 2030, 2032, 2034, 2036, 2038, 2040],
                "y_unit": "%",
                "series": [
                    {
                        "name": "SSP1-2.6",
                        "data": [52.9, 51.2, 49.8, 48.1, 46.5, 45.0, 43.2, 41.8, 40.5],
                        "color": "#36A2EB"
                    },
                    {
                        "name": "SSP2-4.5",
                        "data": [52.9, 53.5, 54.8, 56.2, 57.9, 59.3, 60.8, 62.1, 63.5],
                        "color": "#FFCE56"
                    },
                    {
                        "name": "SSP5-8.5",
                        "data": [52.9, 55.1, 58.3, 62.5, 67.2, 72.1, 77.8, 83.2, 89.5],
                        "color": "#FF6384"
                    }
                ]
            }
        },
        {
            "type": "text",
            "subheading": "4.3 목표 및 성과",
            "content": "..."
        }
    ],
    "total_pages": 4
}
```

---

### Node 6: Strategy Section Generator

**목적:** TCFD Strategy 섹션 생성 (가장 중요하고 분량이 많은 섹션)

**입력:**

```python
{
    "site_analyses": [Node_2A_output, Node_2B_output, Node_2C_output],
    "portfolio_data": Node_3_output,
    "heatmap_table": Node_3_output["heatmap_table"],
    "style_references": Node_1_output["style_references"]
}
```

**처리 로직:**

#### 1. Executive Summary 자동 생성

```python
exec_summary_prompt = f"""
당신은 TCFD 보고서의 Executive Summary를 작성하는 전문가입니다.

### 제공된 정보
**포트폴리오 개요:**
- 총 사업장 수: {len(site_analyses)}
- 총 AAL: {portfolio_data["total_aal"]}%
- Top 3 리스크: {portfolio_data["top_5_risks"][:3]}

**주요 발견사항:**
{comparison_analysis}

### 요청 사항
다음 내용을 포함하여 1-2 페이지 분량의 Executive Summary를 작성하세요:

1. **기후 리스크 개요**
   - 우리 조직이 직면한 주요 물리적 리스크 3가지
   - 예상 재무 영향 (AAL 기반)

2. **주요 발견사항**
   - 사업장 간 리스크 차이
   - 가장 취약한 자산/사업장

3. **대응 전략**
   - 단기 우선순위 (1-2년)
   - 중장기 투자 계획 (5년+)

4. **TCFD 준수 현황**
   - 4개 핵심 영역 (Governance, Strategy, Risk Management, Metrics) 간략 요약
"""

executive_summary = llm.invoke(exec_summary_prompt)
```

#### 2. Strategy 본문 생성 (Top 5 리스크 중심)

```python
strategy_prompt = f"""
당신은 TCFD 보고서의 Strategy 섹션을 작성하는 전문가입니다.

### 제공된 정보
{json.dumps(portfolio_data, ensure_ascii=False, indent=2)}

### 기존 보고서 스타일 참조
{style_references["strategy_examples"]}

### 요청 사항
아래 구조에 따라 Strategy 섹션을 작성하세요:

## 2. Strategy

### 2.1 리스크 및 기회 식별

우리는 단기(~2025), 중기(~2030), 장기(~2040)에 걸쳐 다음과 같은 물리적 기후 리스크를 식별했습니다:

**[히트맵 테이블 삽입 위치]**

위 히트맵은 포트폴리오 전체 사업장에 대한 물리적 리스크 분포를 보여줍니다.
특히 주목할 점은 [인사이트 2-3문장].

### 2.2 사업 및 재무 영향

포트폴리오 전체의 연평균 손실액(AAL)은 {total_aal}%로 추정되며,
이는 연간 약 [금액]의 재무적 영향을 의미합니다.

**시나리오별 분석:**
- SSP1-2.6 (2°C 미만): [영향]
- SSP2-4.5 (중간 경로): [영향]
- SSP5-8.5 (고배출): [영향]

### 2.3 주요 리스크별 영향 분석 및 대응 방안

다음은 포트폴리오에서 가장 큰 영향을 미치는 5가지 리스크에 대한 상세 분석입니다:

**[P1~P5 섹션을 사업장별 분석 결과에서 추출하여 삽입]**

### 2.4 전략적 회복력 (Resilience)

다양한 기후 시나리오에서도 사업 연속성을 유지하기 위한 우리의 전략은:

1. **물리적 방어 강화**: [구체적 투자 계획]
2. **자산 다변화**: [지리적 분산 전략]
3. **보험 및 재무 완충**: [리스크 이전 전략]
"""

strategy_content = llm.invoke(strategy_prompt)
```

#### 3. P1~P5 섹션 통합

```python
def extract_top_5_impact_sections(site_analyses: list[dict], top_5_risks: list[dict]) -> list[str]:
    """
    사업장별 분석 결과에서 Top 5 리스크의 P 섹션을 추출하여 통합
    """
    p_sections = []

    for i, top_risk in enumerate(top_5_risks, start=1):
        risk_type = top_risk["risk_type"]

        # 모든 사업장에서 해당 리스크 분석 수집
        all_site_analyses_for_risk = []
        for site_analysis in site_analyses:
            risk_data = next(
                (r for r in site_analysis["risk_analyses"] if r["risk_type"] == risk_type),
                None
            )
            if risk_data:
                all_site_analyses_for_risk.append({
                    "site_name": site_analysis["site_name"],
                    "analysis": risk_data["markdown_content"]
                })

        # 통합 프롬프트
        integration_prompt = f"""
다음은 {len(all_site_analyses_for_risk)}개 사업장의 {risk_type} 리스크 분석입니다:

{json.dumps(all_site_analyses_for_risk, ensure_ascii=False, indent=2)}

이를 통합하여 하나의 일관된 "P{i}. {risk_type_korean}" 섹션을 작성하세요.
사업장별 차이를 언급하되, 포트폴리오 전체 관점에서 서술하세요.
"""

        integrated_section = llm.invoke(integration_prompt)
        p_sections.append(integrated_section)

    return p_sections
```

**출력:**

```python
{
    "section_id": "strategy",
    "title": "Strategy",
    "blocks": [
        {
            "type": "text",
            "subheading": "Executive Summary",
            "content": executive_summary
        },
        {
            "type": "text",
            "subheading": "2.1 리스크 및 기회 식별",
            "content": "..."
        },
        {
            "type": "heatmap_table",
            "data": heatmap_table  # Node 3에서 생성된 것
        },
        {
            "type": "text",
            "subheading": "2.2 사업 및 재무 영향",
            "content": "..."
        },
        {
            "type": "text",
            "subheading": "2.3 주요 리스크별 영향 분석 및 대응 방안",
            "content": ""
        },
        {
            "type": "text",
            "subheading": "P1. 하천 범람 (River Flood)",
            "content": p_sections[0]
        },
        {
            "type": "text",
            "subheading": "P2. 태풍 (Typhoon)",
            "content": p_sections[1]
        },
        {
            "type": "text",
            "subheading": "P3. 도시 침수 (Urban Flood)",
            "content": p_sections[2]
        },
        {
            "type": "text",
            "subheading": "P4. 극심한 고온 (Extreme Heat)",
            "content": p_sections[3]
        },
        {
            "type": "text",
            "subheading": "P5. 해수면 상승 (Sea Level Rise)",
            "content": p_sections[4]
        },
        {
            "type": "text",
            "subheading": "2.4 전략적 회복력",
            "content": "..."
        }
    ],
    "total_pages": 7
}
```

---

### Node 7: Governance & Appendix Template Generator

**목적:** 데이터가 없는 섹션을 템플릿 기반으로 생성

**처리 로직:**

#### 1. Governance 섹션 (템플릿)

```python
governance_template = """
## 1. Governance

### 1.1 이사회의 감독

{company_name}의 이사회는 기후 관련 리스크 및 기회에 대한 최종 감독 책임을 지니고 있습니다.

**전략·ESG위원회**
- 구성: 사외이사 {num_independent}명, 사내이사 {num_internal}명
- 역할: 기후변화 전략 방향 설정, 주요 리스크 검토, 투자 의사결정 승인
- 활동: 분기 1회 정기 회의, 필요 시 수시 개최

**2024년 주요 안건:**
- 물리적 기후 리스크 분석 결과 보고 ({report_date})
- TCFD 공시 체계 수립 ({tcfd_date})
- 기후 리스크 완화 투자 계획 승인 ({investment_date})

### 1.2 경영진의 역할

**CEO (Chief Executive Officer)**
- 기후 리스크 관리 총괄 책임
- 주요 투자 의사결정 최종 승인

**CSO (Chief Sustainability Officer)** *(또는 해당 직책)*
- 기후 리스크 분석 및 대응 전략 수립
- TCFD 보고서 작성 감독
- 이사회 보고 (분기별)

**CFO (Chief Financial Officer)**
- 기후 리스크의 재무적 영향 평가
- 예산 편성 시 기후 리스크 반영

### 1.3 성과 보상 연계

경영진 성과평가(KPI)에 다음과 같은 기후 관련 지표를 반영하고 있습니다:

- 물리적 리스크 완화 조치 이행률: {kpi_weight_1}%
- AAL 감축 목표 달성도: {kpi_weight_2}%
- TCFD 공시 품질 평가: {kpi_weight_3}%
"""

def generate_governance_section(company_name: str, variables: dict) -> str:
    """
    변수 치환하여 Governance 섹션 생성
    """
    return governance_template.format(
        company_name=company_name,
        num_independent=variables.get("num_independent", "5"),
        num_internal=variables.get("num_internal", "1"),
        report_date=variables.get("report_date", "2024년 3월"),
        tcfd_date=variables.get("tcfd_date", "2024년 6월"),
        investment_date=variables.get("investment_date", "2024년 9월"),
        kpi_weight_1=variables.get("kpi_weight_1", "30"),
        kpi_weight_2=variables.get("kpi_weight_2", "40"),
        kpi_weight_3=variables.get("kpi_weight_3", "30")
    )
```

#### 2. Appendix 섹션 생성

```python
appendix_prompt = f"""
당신은 TCFD 보고서의 Appendix 섹션을 작성하는 전문가입니다.

### 요청 사항
아래 구조에 따라 Appendix를 작성하세요:

## Appendix

### A1. 상세 데이터 테이블

**표 A1-1: 사업장별 물리적 리스크 점수 (9가지 전체)**

| 사업장 | 극심한 고온 | 극심한 저온 | 가뭄 | 하천 범람 | 도시 침수 | 해수면 상승 | 태풍 | 산불 | 물 스트레스 |
|--------|------------|------------|------|----------|----------|------------|------|------|-----------|
| 서울 본사 | {data} | {data} | ... |
| ... |

**표 A1-2: AAL 연도별 추이 (2024-2100, 10년 단위)**

**표 A1-3: 시나리오별 AAL 비교**

### A2. 방법론

**H×E×V 프레임워크**
- Hazard (위험요인): 기후 변수의 강도 및 빈도
- Exposure (노출도): 자산의 지리적 위치 및 규모
- Vulnerability (취약성): 건물 구조, 노후도, 대응 능력

**AAL (연평균 손실액) 산출 방법**
```

AAL = Σ (P_i × L_i)
여기서:

- P_i: i번째 위험 시나리오의 발생 확률
- L_i: i번째 시나리오에서의 손실액

```

**기후 시나리오**
- SSP1-2.6: 지속가능 발전 경로 (온도 상승 1.5-2°C)
- SSP2-4.5: 중간 경로 (온도 상승 2-3°C)
- SSP5-8.5: 고배출 경로 (온도 상승 4-5°C)

### A3. 데이터 출처

- 기후 데이터: 기상청 기후정보포털, IPCC AR6
- 건물 데이터: 건축물대장 (국토교통부)
- 재해 이력: 재해연보 (행정안전부)
- 시나리오: CMIP6 (Coupled Model Intercomparison Project Phase 6)

### A4. 용어 정의

- **AAL (Annual Average Loss)**: 연평균 손실액
- **SSP (Shared Socioeconomic Pathways)**: 공유사회경제경로
- **TCFD**: Task Force on Climate-related Financial Disclosures
- **H×E×V**: Hazard × Exposure × Vulnerability
- **bin**: 리스크 강도 구간 (예: 0-10%, 10-20% 등)

### A5. 제3자 검증

*(현재 미적용, 향후 검증 계획)*

우리는 향후 다음 항목에 대한 제3자 검증을 계획하고 있습니다:
- AAL 산출 방법론
- 기후 시나리오 적용 타당성
- 재무 영향 추정 신뢰성
"""

appendix_section = llm.invoke(appendix_prompt)
```

**출력:**

```python
{
    "governance_section": {
        "section_id": "governance",
        "title": "Governance",
        "content": governance_content,
        "total_pages": 2,
        "is_template": True
    },
    "appendix_section": {
        "section_id": "appendix",
        "title": "Appendix",
        "blocks": [
            {
                "type": "text",
                "subheading": "A1. 상세 데이터 테이블",
                "content": "..."
            },
            {
                "type": "table",
                "title": "표 A1-1: 사업장별 물리적 리스크 점수",
                "data": {...}
            },
            {
                "type": "text",
                "subheading": "A2. 방법론",
                "content": "..."
            },
            {
                "type": "text",
                "subheading": "A3. 데이터 출처",
                "content": "..."
            },
            {
                "type": "text",
                "subheading": "A4. 용어 정의",
                "content": "..."
            }
        ],
        "total_pages": 4
    }
}
```

---

### Node 8: Report Composer

**목적:** 전체 섹션을 TCFD 순서에 맞게 조립하고 JSON 구조화

**입력:**

```python
{
    "governance": Node_7["governance_section"],
    "strategy": Node_6,
    "risk_management": Node_4,
    "metrics_targets": Node_5,
    "appendix": Node_7["appendix_section"]
}
```

**처리 로직:**

```python
def compose_report(sections: dict, metadata: dict) -> dict:
    """
    전체 보고서 JSON 구조 생성
    """
    report = {
        "report_id": f"tcfd_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        "meta": {
            "title": f"{metadata['company_name']} TCFD 보고서",
            "generated_at": datetime.now().isoformat(),
            "llm_model": "gpt-4-1106-preview",
            "site_count": len(metadata["site_ids"]),
            "total_pages": 0,
            "total_aal": metadata["total_aal"],
            "version": "1.0"
        },
        "sections": []
    }

    # 섹션 순서 정의 (TCFD 표준)
    section_order = [
        ("executive_summary", sections["strategy"]["blocks"][0]),  # Strategy 내 첫 블록
        ("governance", sections["governance"]),
        ("strategy", sections["strategy"]),
        ("risk_management", sections["risk_management"]),
        ("metrics_targets", sections["metrics_targets"]),
        ("appendix", sections["appendix"])
    ]

    page_counter = 1
    for section_id, section_data in section_order:
        section_pages = section_data.get("total_pages", 0)

        report["sections"].append({
            "section_id": section_id,
            "title": section_data["title"],
            "page_start": page_counter,
            "page_end": page_counter + section_pages - 1,
            "blocks": section_data.get("blocks", [])
        })

        page_counter += section_pages

    report["meta"]["total_pages"] = page_counter - 1

    # 목차 생성
    report["table_of_contents"] = generate_toc(report["sections"])

    return report

def generate_toc(sections: list[dict]) -> list[dict]:
    """
    목차 생성
    """
    toc = []
    for section in sections:
        toc.append({
            "title": section["title"],
            "page": section["page_start"]
        })

        # 하위 제목 추가
        for block in section["blocks"]:
            if block.get("subheading"):
                toc.append({
                    "title": f"  - {block['subheading']}",
                    "page": section["page_start"]  # 실제로는 더 정확한 페이지 계산 필요
                })

    return toc
```

**출력 예시 (최종 JSON):**

```json
{
  "report_id": "tcfd_report_20251214_153045",
  "meta": {
    "title": "SK주식회사 TCFD 보고서",
    "generated_at": "2025-12-14T15:30:45",
    "llm_model": "gpt-4-1106-preview",
    "site_count": 3,
    "total_pages": 18,
    "total_aal": 52.9,
    "version": "1.0"
  },
  "table_of_contents": [
    {"title": "Executive Summary", "page": 1},
    {"title": "1. Governance", "page": 3},
    {"title": "  - 1.1 이사회의 감독", "page": 3},
    {"title": "2. Strategy", "page": 5},
    {"title": "  - 2.1 리스크 및 기회 식별", "page": 5},
    {"title": "  - P1. 하천 범람", "page": 7},
    {"title": "3. Risk Management", "page": 12},
    {"title": "4. Metrics and Targets", "page": 15},
    {"title": "Appendix", "page": 19}
  ],
  "sections": [
    {
      "section_id": "executive_summary",
      "title": "Executive Summary",
      "page_start": 1,
      "page_end": 2,
      "blocks": [
        {
          "type": "text",
          "content": "## Executive Summary\n\n우리 조직은 3개 사업장에 대한 물리적 기후 리스크 분석을 수행하였으며, 포트폴리오 전체의 연평균 손실액(AAL)은 52.9%로 추정되었습니다..."
        }
      ]
    },
    {
      "section_id": "governance",
      "title": "Governance",
      "page_start": 3,
      "page_end": 4,
      "blocks": [
        {
          "type": "text",
          "subheading": "1.1 이사회의 감독",
          "content": "SK주식회사의 이사회는 기후 관련 리스크 및 기회에 대한..."
        }
      ]
    },
    {
      "section_id": "strategy",
      "title": "Strategy",
      "page_start": 5,
      "page_end": 11,
      "blocks": [
        {
          "type": "text",
          "subheading": "2.1 리스크 및 기회 식별",
          "content": "우리는 단기(~2025), 중기(~2030), 장기(~2040)에 걸쳐..."
        },
        {
          "type": "heatmap_table",
          "title": "사업장별 물리적 리스크 AAL 분포",
          "data": {
            "headers": [
              {"text": "사업장", "rowspan": 2},
              {"text": "리스크 유형", "colspan": 5},
              {"text": "Total AAL", "rowspan": 2}
            ],
            "sub_headers": ["하천 범람", "태풍", "도시 침수", "극심한 고온", "해수면 상승"],
            "rows": [
              {
                "site_name": "서울 본사",
                "cells": [
                  {"value": "7.2%", "bg_color": "yellow"},
                  {"value": "2.1%", "bg_color": "gray"},
                  {"value": "5.1%", "bg_color": "yellow"},
                  {"value": "2.5%", "bg_color": "gray"},
                  {"value": "0.0%", "bg_color": "gray"},
                  {"value": "18.3%", "bg_color": "orange"}
                ]
              },
              {
                "site_name": "대전 데이터센터",
                "cells": [
                  {"value": "3.8%", "bg_color": "yellow"},
                  {"value": "2.1%", "bg_color": "gray"},
                  {"value": "1.2%", "bg_color": "gray"},
                  {"value": "4.8%", "bg_color": "yellow"},
                  {"value": "0.0%", "bg_color": "gray"},
                  {"value": "12.5%", "bg_color": "orange"}
                ]
              },
              {
                "site_name": "부산 물류센터",
                "cells": [
                  {"value": "3.8%", "bg_color": "yellow"},
                  {"value": "9.3%", "bg_color": "yellow"},
                  {"value": "2.4%", "bg_color": "gray"},
                  {"value": "1.2%", "bg_color": "gray"},
                  {"value": "6.2%", "bg_color": "yellow"},
                  {"value": "22.1%", "bg_color": "orange"}
                ]
              }
            ],
            "legend": [
              {"color": "gray", "label": "0-3% (낮음)"},
              {"color": "yellow", "label": "3-10% (중간)"},
              {"color": "orange", "label": "10-30% (높음)"},
              {"color": "red", "label": "30%+ (매우 높음)"}
            ]
          }
        },
        {
          "type": "text",
          "subheading": "P1. 하천 범람 (River Flood)",
          "content": "### 영향 분석\n\n**재무적 영향**\n포트폴리오 전체에서 하천 범람으로 인한 AAL은 18.2%로..."
        }
      ]
    },
    {
      "section_id": "risk_management",
      "title": "Risk Management",
      "page_start": 12,
      "page_end": 14,
      "blocks": [...]
    },
    {
      "section_id": "metrics_targets",
      "title": "Metrics and Targets",
      "page_start": 15,
      "page_end": 18,
      "blocks": [
        {
          "type": "text",
          "subheading": "4.1 기후 관련 지표",
          "content": "..."
        },
        {
          "type": "line_chart",
          "title": "포트폴리오 AAL 추이 (2024-2040)",
          "data": {
            "categories": [2024, 2026, 2028, 2030, 2032, 2034, 2036, 2038, 2040],
            "y_unit": "%",
            "series": [
              {
                "name": "SSP1-2.6",
                "data": [52.9, 51.2, 49.8, 48.1, 46.5, 45.0, 43.2, 41.8, 40.5],
                "color": "#36A2EB"
              },
              {
                "name": "SSP2-4.5",
                "data": [52.9, 53.5, 54.8, 56.2, 57.9, 59.3, 60.8, 62.1, 63.5],
                "color": "#FFCE56"
              },
              {
                "name": "SSP5-8.5",
                "data": [52.9, 55.1, 58.3, 62.5, 67.2, 72.1, 77.8, 83.2, 89.5],
                "color": "#FF6384"
              }
            ]
          }
        }
      ]
    },
    {
      "section_id": "appendix",
      "title": "Appendix",
      "page_start": 19,
      "page_end": 23,
      "blocks": [...]
    }
  ]
}
```

---

### Node 9: Quality Validator

**목적:** TCFD 7대 원칙 및 필수 요소 검증

**검증 항목:**

```python
validation_checks = {
    "tcfd_completeness": {
        "name": "TCFD 필수 요소 완전성",
        "checks": [
            "Governance: 이사회 감독 체계 포함 여부",
            "Governance: 경영진 역할 포함 여부",
            "Strategy: 단기/중기/장기 리스크 식별 여부",
            "Strategy: 재무 영향 분석 포함 여부",
            "Strategy: 시나리오 분석 포함 여부",
            "Risk Management: 리스크 식별 프로세스 포함 여부",
            "Risk Management: 전사 리스크 관리 통합 설명 여부",
            "Metrics: AAL 지표 포함 여부",
            "Metrics: 목표 및 성과 포함 여부"
        ]
    },
    "data_consistency": {
        "name": "데이터 일관성",
        "checks": [
            "사업장 개수 일치 (meta vs sections)",
            "AAL 합계 일치 (개별 vs 전체)",
            "히트맵 테이블 데이터 정합성",
            "차트 데이터 정합성"
        ]
    },
    "quality_principles": {
        "name": "TCFD 7대 품질 원칙",
        "checks": [
            "Relevant: 의사결정에 유용한 정보 포함",
            "Specific: 구체적 수치 및 사례 포함",
            "Clear: 명확하고 이해하기 쉬운 서술",
            "Consistent: 용어 및 형식 일관성",
            "Comparable: 시나리오/연도 간 비교 가능",
            "Reliable: 출처 및 방법론 명시",
            "Timely: 최신 데이터 사용"
        ]
    }
}

def validate_report(report: dict) -> dict:
    """
    보고서 품질 검증
    """
    issues = []

    # 1. 필수 요소 체크
    required_sections = ["governance", "strategy", "risk_management", "metrics_targets"]
    for section_id in required_sections:
        if not any(s["section_id"] == section_id for s in report["sections"]):
            issues.append({
                "severity": "critical",
                "type": "completeness",
                "message": f"필수 섹션 누락: {section_id}"
            })

    # 2. 데이터 일관성 체크
    total_aal_from_sites = sum([...])  # 사업장별 AAL 합산
    total_aal_from_meta = report["meta"]["total_aal"]
    if abs(total_aal_from_sites - total_aal_from_meta) > 0.1:
        issues.append({
            "severity": "high",
            "type": "consistency",
            "message": f"AAL 불일치: sites={total_aal_from_sites}, meta={total_aal_from_meta}"
        })

    # 3. 히트맵 테이블 검증
    heatmap = find_block_by_type(report, "heatmap_table")
    if heatmap:
        if len(heatmap["rows"]) != report["meta"]["site_count"]:
            issues.append({
                "severity": "medium",
                "type": "consistency",
                "message": "히트맵 행 개수가 사업장 개수와 불일치"
            })

    # 4. 페이지 수 검증
    if report["meta"]["total_pages"] < 5:
        issues.append({
            "severity": "medium",
            "type": "completeness",
            "message": f"분량 부족: {report['meta']['total_pages']}페이지 (최소 5페이지 권장)"
        })

    return {
        "is_valid": len([i for i in issues if i["severity"] == "critical"]) == 0,
        "issues": issues,
        "quality_score": calculate_quality_score(report, issues)
    }

def calculate_quality_score(report: dict, issues: list[dict]) -> float:
    """
    품질 점수 계산 (0-100)
    """
    base_score = 100

    for issue in issues:
        if issue["severity"] == "critical":
            base_score -= 30
        elif issue["severity"] == "high":
            base_score -= 15
        elif issue["severity"] == "medium":
            base_score -= 5

    return max(0, base_score)
```

**출력:**

```python
{
    "is_valid": True,
    "issues": [
        {
            "severity": "medium",
            "type": "completeness",
            "message": "Appendix에 제3자 검증 의견서 누락 (현재 데이터 없으므로 허용)"
        }
    ],
    "quality_score": 95.0,
    "recommendations": [
        "Strategy 섹션에 더 구체적인 투자 금액 명시 권장",
        "Governance 섹션에 실제 이사회 구성 정보 반영 시 신뢰도 향상"
    ]
}
```

---

### Node 10: Refiner (조건부)

**조건:** `validation["is_valid"] == False` 또는 `quality_score < 70`

**처리 로직:**

```python
def refine_report(report: dict, validation_result: dict, max_retries: int = 2) -> dict:
    """
    검증 피드백 기반 보고서 수정
    """
    retry_count = 0

    while retry_count < max_retries and not validation_result["is_valid"]:
        # Critical 이슈만 수정
        critical_issues = [i for i in validation_result["issues"] if i["severity"] == "critical"]

        for issue in critical_issues:
            if issue["type"] == "completeness":
                # 누락된 섹션 추가
                missing_section_id = extract_section_id_from_message(issue["message"])
                report = add_missing_section(report, missing_section_id)

            elif issue["type"] == "consistency":
                # 데이터 불일치 수정
                report = fix_data_inconsistency(report, issue)

        # 재검증
        validation_result = validate_report(report)
        retry_count += 1

    return report

def add_missing_section(report: dict, section_id: str) -> dict:
    """
    누락된 섹션을 템플릿으로 긴급 추가
    """
    emergency_templates = {
        "governance": "## 1. Governance\n\n이사회는 기후 리스크를 감독합니다...",
        "metrics_targets": "## 4. Metrics and Targets\n\n주요 지표는..."
    }

    report["sections"].append({
        "section_id": section_id,
        "title": section_id.replace("_", " ").title(),
        "blocks": [
            {"type": "text", "content": emergency_templates.get(section_id, "내용 준비 중")}
        ],
        "is_emergency_template": True
    })

    return report
```

---

### Node 11: Finalizer

**목적:** DB 저장 및 PDF 생성 (Optional)

**처리 로직:**

```python
async def finalize_report(report: dict, user_id: int, site_ids: list[int]) -> dict:
    """
    최종 보고서 저장 및 메타데이터 업데이트
    """
    # 1. JSONB로 DB 저장
    db_report = Report(
        user_id=user_id,
        title=report["meta"]["title"],
        report_type="TCFD",
        content=report,  # JSONB 컬럼
        total_pages=report["meta"]["total_pages"],
        total_aal=report["meta"]["total_aal"],
        site_count=report["meta"]["site_count"],
        generated_at=datetime.now(),
        llm_model=report["meta"]["llm_model"],
        status="completed"
    )

    await db.add(db_report)
    await db.commit()

    # 2. 사업장-보고서 관계 저장
    for site_id in site_ids:
        await db.add(ReportSite(
            report_id=db_report.id,
            site_id=site_id
        ))
    await db.commit()

    # 3. (Optional) PDF 생성
    pdf_path = None
    if request.get("generate_pdf", False):
        pdf_path = await generate_pdf_from_json(report, db_report.id)

    return {
        "success": True,
        "report_id": db_report.id,
        "download_url": f"/api/reports/{db_report.id}/download",
        "pdf_url": pdf_path if pdf_path else None,
        "meta": report["meta"]
    }

async def generate_pdf_from_json(report: dict, report_id: int) -> str:
    """
    JSON 보고서를 PDF로 변환 (weasyprint 사용)
    """
    from weasyprint import HTML, CSS

    # 1. JSON → HTML 변환
    html_content = render_report_to_html(report)

    # 2. CSS 스타일 적용
    css = CSS(string="""
        body { font-family: 'Noto Sans KR', sans-serif; }
        h1 { color: #2C3E50; }
        table.heatmap td.yellow { background-color: #FFF3CD; }
        table.heatmap td.orange { background-color: #FFE5B4; }
        table.heatmap td.red { background-color: #FFCCCB; }
        table.heatmap td.gray { background-color: #F0F0F0; }
    """)

    # 3. PDF 생성
    pdf_path = f"/tmp/reports/tcfd_report_{report_id}.pdf"
    HTML(string=html_content).write_pdf(pdf_path, stylesheets=[css])

    # 4. S3 업로드 (Optional)
    s3_url = upload_to_s3(pdf_path, f"reports/{report_id}.pdf")

    return s3_url

def render_report_to_html(report: dict) -> str:
    """
    JSON 블록을 HTML로 렌더링
    """
    html_parts = [
        f"<h1>{report['meta']['title']}</h1>",
        "<div class='toc'><h2>목차</h2><ul>"
    ]

    # 목차
    for item in report["table_of_contents"]:
        html_parts.append(f"<li>{item['title']} ... {item['page']}</li>")
    html_parts.append("</ul></div>")

    # 섹션 렌더링
    for section in report["sections"]:
        html_parts.append(f"<section id='{section['section_id']}'>")
        html_parts.append(f"<h2>{section['title']}</h2>")

        for block in section["blocks"]:
            if block["type"] == "text":
                html_parts.append(f"<div>{block['content']}</div>")

            elif block["type"] == "heatmap_table":
                html_parts.append(render_heatmap_to_html(block))

            elif block["type"] == "line_chart":
                # Chart.js는 PDF에서 렌더링 불가 → 이미지로 변환 필요
                chart_image = generate_chart_image(block)
                html_parts.append(f"<img src='{chart_image}' />")

        html_parts.append("</section>")

    return "\n".join(html_parts)

def render_heatmap_to_html(block: dict) -> str:
    """
    히트맵 테이블을 HTML <table>로 변환
    """
    html = f"<table class='heatmap'><caption>{block['title']}</caption>"

    # 헤더
    html += "<thead><tr>"
    for header in block["data"]["headers"]:
        html += f"<th rowspan='{header.get('rowspan', 1)}' colspan='{header.get('colspan', 1)}'>{header['text']}</th>"
    html += "</tr><tr>"
    for sub_header in block["data"]["sub_headers"]:
        html += f"<th>{sub_header}</th>"
    html += "</tr></thead>"

    # 행
    html += "<tbody>"
    for row in block["data"]["rows"]:
        html += f"<tr><td>{row['site_name']}</td>"
        for cell in row["cells"]:
            html += f"<td class='{cell['bg_color']}'>{cell['value']}</td>"
        html += "</tr>"
    html += "</tbody></table>"

    return html
```

---

## 출력 구조

### JSON Schema (최종 출력)

```typescript
interface TCFDReport {
  report_id: string;
  meta: {
    title: string;
    generated_at: string; // ISO 8601
    llm_model: string;
    site_count: number;
    total_pages: number;
    total_aal: number;
    version: string;
  };
  table_of_contents: Array<{
    title: string;
    page: number;
  }>;
  sections: Array<{
    section_id:
      | "executive_summary"
      | "governance"
      | "strategy"
      | "risk_management"
      | "metrics_targets"
      | "appendix";
    title: string;
    page_start: number;
    page_end: number;
    blocks: Array<Block>;
  }>;
}

type Block =
  | TextBlock
  | HeatmapTableBlock
  | LineChartBlock
  | BarChartBlock
  | DiagramBlock
  | TableBlock;

interface TextBlock {
  type: "text";
  subheading?: string;
  content: string; // Markdown 형식
}

interface HeatmapTableBlock {
  type: "heatmap_table";
  title: string;
  data: {
    headers: Array<{ text: string; rowspan?: number; colspan?: number }>;
    sub_headers: string[];
    rows: Array<{
      site_name: string;
      cells: Array<{
        value: string;
        color: "gray" | "yellow" | "orange" | "red";
        bg_color: "gray" | "yellow" | "orange" | "red";
      }>;
    }>;
    legend: Array<{ color: string; label: string }>;
  };
}

interface LineChartBlock {
  type: "line_chart";
  title: string;
  data: {
    categories: (string | number)[]; // X축
    y_unit: string;
    series: Array<{
      name: string;
      data: number[];
      color: string;
    }>;
  };
}

interface TableBlock {
  type: "table";
  title: string;
  data: {
    headers: string[];
    rows: Array<string[]>;
  };
}

interface DiagramBlock {
  type: "diagram";
  title: string;
  data: {
    nodes: string[];
    edges: Array<{ from: string; to: string; label?: string }>;
  };
}
```

---

## 구현 로드맵

### Phase 1: MVP (최소 기능 제품) - 2주

**목표:** 단일 사업장 TCFD 보고서 생성 (핵심 3개 섹션만)

**구현 범위:**

- Node 0: Excel 파싱 + DB 데이터 로딩
- Node 1: 템플릿 로딩
- Node 2-A: 단일 사업장 분석 (9가지 리스크)
- Node 6: Strategy 섹션 생성 (히트맵 제외)
- Node 8: Composer (간소화)
- Node 11: DB 저장

**제외 사항:**

- 병렬 처리 (Node 2-B/C)
- Node 3 (포트폴리오 통합)
- Node 4, 5 (Risk Management, Metrics)
- Node 7 (Governance, Appendix)
- Node 9, 10 (검증, 수정)
- PDF 생성

**검증 기준:**

- 단일 사업장 보고서 생성 성공
- Strategy 섹션에 P1~P9 전체 포함
- 5페이지 이상 분량
- JSON 구조 정합성

---

### Phase 2: Full Feature - 2주

**목표:** 전체 11-Node 워크플로우 구현

**추가 구현:**

- Node 2-B/C: 병렬 사업장 분석
- Node 3: 포트폴리오 통합 + 히트맵 생성
- Node 4, 5: Risk Management, Metrics 섹션
- Node 7: Governance & Appendix
- Node 9: Quality Validator
- Node 10: Refiner

**검증 기준:**

- 3개 사업장 동시 처리 성공
- 히트맵 테이블 색상 코딩 정확
- TCFD 4대 영역 + Appendix 완성
- 12-20페이지 분량
- Quality Score 85점 이상

---

### Phase 3: Optimization & Enhancement - 1주

**목표:** 성능 최적화 및 부가 기능

**구현:**

- PDF 생성 (weasyprint)
- 차트 이미지 자동 생성 (matplotlib/plotly)
- LLM 비용 최적화 (캐싱, 프롬프트 압축)
- 병렬 처리 성능 개선 (asyncio)
- 사용자 피드백 반영 기능
- 보고서 버전 관리

**검증 기준:**

- 3개 사업장 처리 시간 6분 → 4분 단축
- LLM API 비용 30% 절감
- PDF 품질 검증 (300 DPI 이상)

---

## 참고 자료

### 내부 문서

1. `polaris_backend_fastapi/docs/for_better_understanding/tcfd_guide.md`: TCFD 권고안 상세
2. `polaris_backend_fastapi/docs/for_better_understanding/sk_esg_2025.md`: SK ESG 보고서 스타일 참조
3. `polaris_backend_fastapi/docs/for_better_understanding/visual_front.md`: 프론트엔드 차트 구조
4. `polaris_backend_fastapi/ai_agent/utils/knowledge/risk_insight.py`: 리스크 지식베이스

### 외부 표준

1. TCFD Recommendations (2017): https://www.fsb-tcfd.org/
2. GRI Standards 2021
3. SASB Standards
4. IPCC AR6 Climate Scenarios

### 기술 문서

1. LangGraph Documentation: https://langchain-ai.github.io/langgraph/
2. GPT-4 Turbo API: https://platform.openai.com/docs/models/gpt-4-turbo
3. Qdrant Vector DB: https://qdrant.tech/documentation/
4. WeasyPrint PDF Generation: https://doc.courtbouillon.org/weasyprint/

---

**문서 작성 완료일:** 2025-12-14
**작성자:** AI Agent Design Team
**승인자:** [User Approval Required]
**다음 단계:** Phase 1 구현 착수 (승인 후)
