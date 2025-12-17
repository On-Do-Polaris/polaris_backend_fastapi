# SKAX AI Agent 아키텍처 설계서 및 기능 명세서

**작성일**: 2025-12-17  
**버전**: v2.0  
**프로젝트**: SKAX 기후 리스크 분석 및 TCFD 보고서 생성 시스템

---

## 목차

1. [아키텍처 설계서](#1-아키텍처-설계서)

   - 1.1 시스템 개요
   - 1.2 전체 아키텍처
   - 1.3 Agent 계층 구조
   - 1.4 데이터 흐름도
   - 1.5 기술 스택

2. [기능 명세서](#2-기능-명세서)
   - 2.1 Primary Data Agents
   - 2.2 TCFD Report Generation Agents
   - 2.3 상태 관리 (State Management)
   - 2.4 외부 연동

---

## 1. 아키텍처 설계서

### 1.1 시스템 개요

#### 목적

SKAX AI Agent는 다중 사업장에 대한 기후 물리적 리스크를 분석하고, TCFD(Task Force on Climate-related Financial Disclosures) 표준에 맞춰 자동으로 보고서를 생성하는 Multi-Agent 시스템입니다.

#### 핵심 기능

- ✅ **물리적 리스크 분석**: 9가지 리스크(하천범람, 태풍, 도시침수, 해안침수, 산불, 극심한고온, 극심한저온, 가뭄, 해수면상승)
- ✅ **AAL(Annual Average Loss) 계산**: 시나리오별(SSP1-2.6, SSP2-4.5, SSP3-7.0, SSP5-8.5) 연평균 손실률
- ✅ **TCFD 보고서 자동 생성**: Governance, Strategy, Risk Management, Metrics 4대 섹션
- ✅ **건물 특성 분석**: 건축물 대장 API 기반 취약성 평가
- ✅ **추가 데이터 처리**: 사용자 업로드 Excel 데이터 분석 및 통합

---

### 1.2 전체 아키텍처

```
┌─────────────────────────────────────────────────────────────────┐
│                     SKAX AI Agent System                        │
│                    (LangGraph Orchestration)                    │
└─────────────────────────────────────────────────────────────────┘
                               │
                ┌──────────────┴──────────────┐
                │                             │
    ┌───────────▼──────────┐      ┌──────────▼──────────┐
    │  Primary Data Layer  │      │  Report Gen Layer   │
    │   (BC + AD Agents)   │      │  (TCFD Workflow)    │
    └───────────┬──────────┘      └──────────┬──────────┘
                │                             │
    ┌───────────▼──────────┐      ┌──────────▼──────────┐
    │  Building Char. API  │      │  Node 0-6 Pipeline  │
    │  Additional Data     │      │  (Template → Final) │
    └───────────┬──────────┘      └──────────┬──────────┘
                │                             │
    ┌───────────▼─────────────────────────────▼──────────┐
    │              ModelOps Backend (FastAPI)            │
    │  - AAL Calculation (9 Risks × 4 Scenarios)        │
    │  - Physical Risk Score (H × E × V)                │
    │  - PostgreSQL DB (Sites, Results, Reports)        │
    └────────────────────────────────────────────────────┘
```

#### 주요 컴포넌트

| Layer             | Component                      | 역할                        |
| ----------------- | ------------------------------ | --------------------------- |
| **Orchestration** | `SKAXPhysicalRiskAnalyzer`     | 전체 워크플로우 조율        |
| **Primary Data**  | `BuildingCharacteristicsAgent` | 건축물 대장 API 데이터 분석 |
| **Primary Data**  | `AdditionalDataAgent`          | 사용자 Excel 데이터 처리    |
| **TCFD Workflow** | `Node 0-6 Pipeline`            | TCFD 보고서 생성 파이프라인 |
| **Backend**       | `ModelOps FastAPI`             | AAL 계산, DB 연동           |

---

### 1.3 Agent 계층 구조

#### 전체 Agent Map (14개 Agent)

```
SKAX AI Agent System
├── 1. Primary Data Agents (2개)
│   ├── BC Agent (Building Characteristics)
│   └── AD Agent (Additional Data)
│
└── 2. TCFD Report Generation Agents (12개)
    ├── Node 0: Data Preprocessing Agent
    ├── Node 1: Template Loading Agent
    ├── Node 2-A: Scenario Analysis Agent
    ├── Node 2-B: Impact Analysis Agent
    ├── Node 2-C: Mitigation Strategies Agent
    ├── Node 3: Strategy Section Agent
    ├── Node 4: Validator Agent
    ├── Node 5: Composer Agent
    └── Node 6: Finalizer Agent
```

#### Agent별 입출력

| Agent        | 입력                   | 출력                                | LLM 사용        |
| ------------ | ---------------------- | ----------------------------------- | --------------- |
| **BC Agent** | 건물 PK (mgm_bld_pk)   | building_data (구조, 연식, 용도 등) | ❌ API Only     |
| **AD Agent** | Excel 파일 경로        | additional_data (파싱된 JSON)       | ✅ GPT-4o       |
| **Node 0**   | site_data (n개 사업장) | 통합 데이터셋                       | ❌ Transform    |
| **Node 1**   | -                      | report_template_profile             | ✅ GPT-4o + RAG |
| **Node 2-A** | aal_scaled_results     | scenario_analysis_blocks            | ✅ GPT-4o       |
| **Node 2-B** | Top 5 리스크           | impact_analysis_blocks              | ✅ GPT-4o       |
| **Node 2-C** | Top 5 리스크           | mitigation_strategies_blocks        | ✅ GPT-4o       |
| **Node 3**   | 2-A, 2-B, 2-C 결과     | strategy_section                    | ✅ GPT-4o       |
| **Node 4**   | 생성된 섹션            | validation_results                  | ✅ GPT-4o       |
| **Node 5**   | 전체 섹션              | composed_report                     | ❌ Assembly     |
| **Node 6**   | composed_report        | report_id, JSON, MD, PDF            | ❌ DB 저장      |

---

### 1.4 데이터 흐름도

#### 1.4.1 Primary Data Flow

```
┌─────────────────┐
│  사용자 요청    │
│  (site_ids)     │
└────────┬────────┘
         │
    ┌────▼────┐
    │ BC API  │ ← 건축물 대장 API
    └────┬────┘
         │ building_data (구조, 연식, 용도)
         │
    ┌────▼────────┐
    │  BC Agent   │ → 취약성 점수 계산
    └────┬────────┘
         │
    ┌────▼────────┐
    │   Node 0    │ ← site_data (DB)
    └────┬────────┘
         │
    ┌────▼────────┐
    │  State 통합 │
    └─────────────┘
```

#### 1.4.2 TCFD Report Generation Flow

```
Node 0 (Preprocessing)
  │
  ├─→ Node 1 (Template Loading) ← RAG Engine
  │
  ├─→ Node 2-A (Scenario Analysis)
  │   ├─→ Node 4 (Validator) ──┐
  │   └─→ (재생성 루프) ←──────┘
  │
  ├─→ Node 2-B (Impact Analysis)
  │   ├─→ Node 4 (Validator) ──┐
  │   └─→ (재생성 루프) ←──────┘
  │
  ├─→ Node 2-C (Mitigation Strategies)
  │   ├─→ Node 4 (Validator) ──┐
  │   └─→ (재생성 루프) ←──────┘
  │
  ├─→ Node 3 (Strategy Section)
  │   ├─→ Node 4 (Validator) ──┐
  │   └─→ (재생성 루프) ←──────┘
  │
  └─→ Node 5 (Composer)
       │
       └─→ Node 6 (Finalizer) → DB 저장
```

---

### 1.5 기술 스택

#### Backend Framework

- **Language**: Python 3.11+
- **Framework**: FastAPI 0.115.x
- **Orchestration**: LangGraph 0.2.x
- **LLM**: OpenAI GPT-4o (gpt-4o-2024-11-20)

#### AI/ML Stack

- **LLM Framework**: LangChain 0.3.x
- **Vector DB**: Qdrant (RAG용)
- **Embeddings**: OpenAI text-embedding-3-large
- **Monitoring**: LangSmith

#### Data Processing

- **Database**: PostgreSQL 15+ (TimescaleDB)
- **ORM**: SQLAlchemy 2.0
- **Excel Parsing**: pandas, openpyxl
- **JSON Schema**: Pydantic v2

#### External APIs

- **건축물 대장 API**: 국토교통부 공공데이터
- **기후 시나리오 API**: 기상청 SSP 데이터

#### DevOps

- **Container**: Docker
- **CI/CD**: GitHub Actions
- **Logging**: Python logging + LangSmith
- **Environment**: python-dotenv

---

## 2. 기능 명세서

### 2.1 Primary Data Agents

#### 2.1.1 Building Characteristics Agent

**목적**: 건축물 대장 API로부터 건물 특성 데이터를 수집하고 취약성을 평가

**주요 기능**:

1. ✅ **API 데이터 수집**

   - 입력: `mgm_bld_pk` (건물 관리번호)
   - 출력: 구조, 연식, 용도, 면적, 층수 등

2. ✅ **취약성 평가**

   - 구조별 취약성 (목조 > 조적 > 철근콘크리트 > 철골)
   - 연식별 취약성 (50년+ > 30-50년 > 10-30년 > 10년 미만)
   - 용도별 취약성 (산업시설 > 상업시설 > 주거시설 > 공공시설)

3. ✅ **회복력 평가**
   - 내진 설계 여부
   - 방수 시설 유무
   - 비상 전력 시스템

**데이터 스키마**:

```python
{
  "mgm_bld_pk": "string",
  "structure": "string",  # 구조
  "building_age": int,    # 연식
  "main_purpose": "string",  # 용도
  "total_area": float,    # 연면적
  "floor_count": int,     # 층수
  "vulnerability_score": float,  # 취약성 점수 (0-1)
  "resilience_score": float      # 회복력 점수 (0-1)
}
```

**제약사항**:

- ⚠️ API 호출 제한: 1초당 10회
- ⚠️ 데이터 갱신 주기: 실시간 (API 의존)
- ⚠️ 에러 처리: API 실패 시 기본값 사용

---

#### 2.1.2 Additional Data Agent

**목적**: 사용자가 업로드한 Excel 파일을 분석하고 LLM 가이드라인 생성

**주요 기능**:

1. ✅ **Excel 파싱**

   - 다중 시트 자동 병합
   - " | " 구분자 파싱 (key:value)
   - 빈 행 자동 제거

2. ✅ **데이터 정제**

   - NaN/None 제거
   - numpy 타입 → Python native 변환
   - 소수점 6자리 제한

3. ✅ **JSON 압축**

   - separators=(',', ':')
   - indent=1
   - 30-40% 용량 절감

4. ✅ **LLM 가이드라인 생성**
   - 데이터 구조 분석
   - 주요 필드 설명
   - 활용 방안 제시

**입력 형식**:

```json
{
  "file_path": "/path/to/excel.xlsx",
  "site_id": "uuid"
}
```

**출력 스키마**:

```python
{
  "parsed_data": {
    "sheet1": [...],
    "sheet2": [...]
  },
  "llm_guideline": "string",  # LLM 생성 가이드라인
  "metadata": {
    "total_rows": int,
    "total_sheets": int,
    "parsed_at": "datetime"
  }
}
```

**제약사항**:

- ⚠️ 파일 크기 제한: 50MB
- ⚠️ 시트 수 제한: 최대 10개
- ⚠️ 행 수 제한: 시트당 10,000행

---

### 2.2 TCFD Report Generation Agents

#### 2.2.1 Node 0: Data Preprocessing

**목적**: n개 사업장 데이터를 DB에서 조회하고 통합

**입력**:

```python
{
  "site_ids": ["uuid1", "uuid2", ...],
  "building_data": {...},
  "additional_data": {...}
}
```

**처리 과정**:

1. DB 쿼리 (sites 테이블)
2. AAL 결과 조회 (aal_scaled_results)
3. 물리적 리스크 점수 조회 (hazard/exposure/vulnerability_results)
4. 데이터 통합 및 정규화

**출력**:

```python
{
  "site_data": [...],  # n개 사업장 통합 데이터
  "aal_scaled_results": {...},  # AAL 결과
  "hazard_results": {...},
  "exposure_results": {...},
  "vulnerability_results": {...}
}
```

---

#### 2.2.2 Node 1: Template Loading

**목적**: RAG 엔진으로 기존 ESG/TCFD 보고서 분석 및 템플릿 메타데이터 생성

**주요 기능**:

1. ✅ **RAG 검색**

   - Qdrant에서 유사 보고서 검색
   - Top-k=5 관련 문서 추출

2. ✅ **템플릿 메타데이터 생성**
   - 섹션 구조 (Governance, Strategy, Risk Management, Metrics)
   - 각 섹션별 권장 소제목
   - 차트/표 형식 가이드

**LLM 프롬프트**:

```
당신은 TCFD 보고서 구조 전문가입니다.
다음 기존 보고서를 분석하여 템플릿 메타데이터를 생성하세요:

[RAG 검색 결과]
...

출력 형식 (JSON):
{
  "sections": [
    {
      "section_id": "governance",
      "title": "1. Governance",
      "subheadings": ["1.1 ...", "1.2 ..."]
    },
    ...
  ]
}
```

**출력**:

```python
{
  "report_template_profile": {
    "sections": [...],
    "chart_guidelines": {...},
    "table_guidelines": {...}
  }
}
```

---

#### 2.2.3 Node 2-A: Scenario Analysis

**목적**: 4개 SSP 시나리오별 AAL 추이 분석 및 텍스트 생성

**입력**:

- `aal_scaled_results`: 시나리오별 AAL (2024, 2030, 2050, 2100)

**처리**:

1. AAL 추이 계산 (증가/감소율)
2. 시나리오별 비교 분석
3. 주요 인사이트 추출

**LLM 프롬프트**:

```
다음 AAL 데이터를 분석하여 시나리오 분석 텍스트를 작성하세요:

SSP1-2.6: [52.9% → 45.0%] (-15%)
SSP5-8.5: [52.9% → 92.5%] (+75%)

출력: TCFD Strategy 섹션의 "시나리오 분석 결과" 텍스트
```

**출력**:

```python
{
  "scenario_analysis_blocks": [
    {
      "type": "text",
      "subheading": "2.1 시나리오 분석 결과",
      "content": "..."
    },
    {
      "type": "table",
      "title": "시나리오별 AAL 추이",
      "headers": [...],
      "items": [...]
    }
  ]
}
```

---

#### 2.2.4 Node 2-B: Impact Analysis

**목적**: Top 5 리스크의 재무 영향 분석

**입력**:

- `aal_scaled_results`: 리스크별 AAL
- `site_data`: 자산 가치, 면적

**처리**:

1. Top 5 리스크 추출 (AAL 기준)
2. 재무 영향 계산 (AAL × 자산 가치)
3. 사업장별 영향도 분석

**출력**:

```python
{
  "impact_analysis_blocks": [
    {
      "type": "text",
      "subheading": "2.2 재무 영향 분석",
      "content": "..."
    },
    {
      "type": "table",
      "title": "Top 5 리스크 재무 영향",
      "headers": [...],
      "items": [...]
    }
  ]
}
```

---

#### 2.2.5 Node 2-C: Mitigation Strategies

**목적**: Top 5 리스크별 대응 전략 수립

**입력**:

- Top 5 리스크 목록
- `building_data`: 건물 특성
- `additional_data`: 추가 데이터

**처리**:

1. 리스크별 완화 전략 생성
2. 단기/중장기 대응 방안 분류
3. 비용-편익 분석

**LLM 프롬프트**:

```
다음 리스크에 대한 대응 전략을 수립하세요:

Risk: 하천범람 (AAL 18.2%)
Building: 철근콘크리트, 15년, 업무시설

출력:
- 단기 대응 (1-2년)
- 중장기 대응 (3-5년)
- 예상 투자 비용
- 기대 효과 (AAL 감축률)
```

**출력**:

```python
{
  "mitigation_strategies_blocks": [
    {
      "type": "text",
      "subheading": "3.1 리스크별 대응 전략",
      "content": "..."
    },
    {
      "type": "table",
      "title": "Top 5 리스크 대응 전략",
      "headers": [...],
      "items": [...]
    }
  ]
}
```

---

#### 2.2.6 Node 3: Strategy Section

**목적**: Executive Summary 생성 및 Strategy 섹션 조립

**입력**:

- Node 2-A, 2-B, 2-C 결과
- `report_template_profile`

**처리**:

1. Executive Summary 작성
2. 히트맵 표 생성 (사업장별 AAL)
3. 섹션 순서 정렬

**출력**:

```python
{
  "strategy_section": {
    "section_id": "strategy",
    "title": "2. Strategy",
    "blocks": [
      {"type": "text", "subheading": "Executive Summary", "content": "..."},
      {"type": "table", "title": "사업장별 AAL 히트맵", ...},
      ...
    ]
  }
}
```

---

#### 2.2.7 Node 4: Validator

**목적**: TCFD 7대 원칙 기준 품질 검증

**검증 항목**:

1. ✅ **Relevance**: 리스크가 사업과 관련성이 있는가?
2. ✅ **Specific**: 구체적인 수치와 사례가 포함되었는가?
3. ✅ **Complete**: 모든 필수 정보가 포함되었는가?
4. ✅ **Clear**: 이해하기 쉬운 언어로 작성되었는가?
5. ✅ **Balanced**: 긍정/부정 측면이 균형있게 기술되었는가?
6. ✅ **Comparable**: 시계열/벤치마크 비교가 가능한가?
7. ✅ **Consistent**: 다른 섹션과 일관성이 있는가?

**출력**:

```python
{
  "is_valid": bool,
  "validation_results": {
    "node_2a": {"is_valid": True, "issues": []},
    "node_2b": {"is_valid": False, "issues": ["Specific 원칙 위반"]},
    ...
  },
  "failed_nodes": ["node_2b"]
}
```

**재생성 로직**:

- 실패한 노드만 재실행
- 최대 3회 재시도
- 3회 실패 시 경고와 함께 진행

---

#### 2.2.8 Node 5: Composer

**목적**: 전체 보고서 섹션 조립

**처리**:

1. Governance 섹션 (하드코딩)
2. Strategy 섹션 (Node 3 결과)
3. Risk Management 섹션 (Node 2-C 기반)
4. Metrics 섹션 (AAL 목표 설정)
5. Appendix 섹션 (방법론, 데이터 출처)

**출력**:

```python
{
  "composed_report": {
    "report_id": "tcfd_report_20251217_...",
    "meta": {"title": "TCFD 기후 리스크 보고서"},
    "sections": [...]
  }
}
```

---

#### 2.2.9 Node 6: Finalizer

**목적**: JSONB DB 저장 및 파일 생성

**처리**:

1. PostgreSQL JSONB 컬럼에 저장
2. Markdown 파일 생성 (.md)
3. JSON 파일 생성 (.json)
4. PDF 변환 (향후)

**출력**:

```python
{
  "report_id": "tcfd_report_20251217_123456",
  "json_path": "/path/to/report.json",
  "md_path": "/path/to/report.md",
  "pdf_path": None,  # 향후 구현
  "status": "completed"
}
```

---

### 2.3 상태 관리 (State Management)

#### TCFDReportState

**State 스키마** (`state.py`):

```python
class TCFDReportState(TypedDict):
    # 입력 데이터
    site_data: List[Dict]  # n개 사업장 통합 데이터
    building_data: Dict  # BC Agent 결과
    additional_data: Optional[Dict]  # AD Agent 결과
    use_additional_data: bool

    # AAL 결과
    aal_scaled_results: Dict

    # 물리적 리스크 점수
    hazard_results: Dict
    exposure_results: Dict
    vulnerability_results: Dict
    probability_results: Dict

    # 종합 평가
    sites_risk_assessment: List[Dict]

    # TCFD 보고서 생성
    report_template_profile: Optional[Dict]
    scenario_analysis_blocks: List[Dict]
    impact_analysis_blocks: List[Dict]
    mitigation_strategies_blocks: List[Dict]
    strategy_section: Optional[Dict]
    composed_report: Optional[Dict]

    # 검증
    validation_results: Optional[Dict]
    retry_count: int

    # 최종 출력
    report_id: Optional[str]
    report_json_path: Optional[str]
    report_md_path: Optional[str]
```

**State 전달 흐름**:

```
Node 0 → Node 1 → Node 2-A → Node 4
                ↓               ↓
              Node 2-B → Node 4
                ↓               ↓
              Node 2-C → Node 4
                           ↓
                        Node 3 → Node 4
                                  ↓
                                Node 5 → Node 6
```

---

### 2.4 외부 연동

#### 2.4.1 ModelOps Backend API

**엔드포인트**:

- `POST /api/v1/physical-risk/aal`: AAL 계산
- `POST /api/v1/physical-risk/score`: 물리적 리스크 점수 계산
- `GET /api/v1/sites/{site_id}`: 사업장 정보 조회

**응답 예시**:

```json
{
  "aal_results": {
    "riverine_flood": {
      "SSP1-2.6": {"2024": 7.2, "2050": 6.1},
      ...
    }
  }
}
```

#### 2.4.2 건축물 대장 API

**엔드포인트**:

- `GET /api/building/{mgm_bld_pk}`

**응답 예시**:

```json
{
  "mgm_bld_pk": "...",
  "structure": "철근콘크리트",
  "building_age": 15,
  "main_purpose": "업무시설",
  "total_area": 5000.0
}
```

#### 2.4.3 Qdrant Vector DB

**컬렉션**: `tcfd_reports`  
**임베딩**: OpenAI text-embedding-3-large (3072차원)

**검색 쿼리**:

```python
query = "TCFD 보고서 구조 템플릿"
results = qdrant_client.search(
    collection_name="tcfd_reports",
    query_vector=embedding,
    limit=5
)
```

---

## 부록

### A. 용어 정의

| 용어          | 설명                                                         |
| ------------- | ------------------------------------------------------------ |
| **AAL**       | Annual Average Loss, 연평균 손실률 (%)                       |
| **TCFD**      | Task Force on Climate-related Financial Disclosures          |
| **SSP**       | Shared Socioeconomic Pathways (기후 시나리오)                |
| **H×E×V**     | Hazard × Exposure × Vulnerability (위험도 × 노출도 × 취약성) |
| **RAG**       | Retrieval-Augmented Generation                               |
| **LangGraph** | LangChain의 상태 기반 Agent 오케스트레이션 프레임워크        |

### B. 환경 변수

```bash
# LLM
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-2024-11-20

# LangSmith
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=lsv2_pt_...
LANGCHAIN_PROJECT=skax-physical-risk

# Database
DATABASE_URL=postgresql://user:pass@host:5432/db

# Qdrant
QDRANT_URL=http://localhost:6333
QDRANT_API_KEY=...

# Building API
BUILDING_API_URL=https://api.data.go.kr/...
BUILDING_API_KEY=...
```

### C. 성능 지표

| 지표                   | 목표       | 현재    |
| ---------------------- | ---------- | ------- |
| **전체 파이프라인**    | < 5분      | 3-4분   |
| **Node 1 (RAG)**       | < 30초     | 20초    |
| **Node 2-A/B/C (LLM)** | < 1분/노드 | 40-50초 |
| **Node 4 (검증)**      | < 30초     | 25초    |
| **Node 6 (DB 저장)**   | < 10초     | 5초     |

### D. 에러 처리

| 에러 타입         | 대응 방안                          |
| ----------------- | ---------------------------------- |
| **API 타임아웃**  | 3회 재시도 (exponential backoff)   |
| **LLM 파싱 실패** | JSON 블록 추출 → 재요청            |
| **DB 연결 실패**  | 커넥션 풀 재시작                   |
| **검증 실패**     | 최대 3회 재생성 → 경고와 함께 진행 |

---

**문서 버전**: v2.0  
**최종 수정**: 2025-12-17  
**작성자**: SKAX AI Team
