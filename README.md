# Polaris Physical Risk Analysis Backend

**AI Agent 기반 사업장 기후 물리적 리스크 분석 시스템**

[![Python](https://img.shields.io/badge/Python-3.11.9-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.116.1-009688.svg)](https://fastapi.tiangolo.com/)
[![LangChain](https://img.shields.io/badge/LangChain-1.1.0-00A67E.svg)](https://langchain.com/)
[![LangGraph](https://img.shields.io/badge/LangGraph-1.0.3-FF6F00.svg)](https://langchain-ai.github.io/langgraph/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16+-336791.svg)](https://www.postgresql.org/)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg)](https://www.docker.com/)

## 📋 목차

- [개요](#개요)
- [주요 기능](#주요-기능)
- [시스템 아키텍처](#시스템-아키텍처)
- [설치 및 실행](#설치-및-실행)
- [API 문서](#api-문서)
- [AI Agent 구조](#ai-agent-구조)
- [프로젝트 구조](#프로젝트-구조)
- [환경 변수](#환경-변수)
- [개발 가이드](#개발-가이드)

---

## 개요

Polaris Physical Risk Analysis Backend는 **기후 변화로 인한 물리적 리스크를 AI Agent 기반으로 분석**하는 FastAPI 백엔드 시스템입니다. LangGraph를 활용한 워크플로우 오케스트레이션으로 9가지 재해 유형에 대한 리스크 점수, 재무 영향(AAL), TCFD 대응 전략을 자동 생성합니다.

### 핵심 특징

- **AI Agent 기반 분석**: LangGraph로 구현된 11개 노드, 26개 Sub-Agent 협업
- **Fork-Join 병렬 처리**: Physical Risk Score, AAL 분석, Building Characteristics 동시 실행
- **자동 보고서 생성**: LLM 기반 TCFD/ESG 보고서 자동 작성 (정량/정성 통합)
- **ModelOps API 연동**: 외부 ML 모델 서버에서 H, E, V, AAL 계산 수행
- **PostgreSQL Datawarehouse**: ERD v03 기반 45개 테이블 (Wide Format, 약 4.5억 행)
- **추가 데이터 반영**: 사용자 제공 데이터로 Node 5 이후 재실행 (캐시 활용)
- **Spring Boot Gateway 연동**: RESTful API 프록시 패턴
- **GCP Cloud Run 배포**: Docker 컨테이너 기반 자동 배포 파이프라인

---

## 주요 기능

### 1. 물리적 리스크 분석 (Physical Risk Score)
- **H × E × V 방식**: Hazard × Exposure × Vulnerability 기반 점수 (100점 만점)
- **9가지 재해 유형**:
  - 극한 고온 (Extreme Heat)
  - 극한 저온 (Extreme Cold)
  - 산불 (Wildfire)
  - 가뭄 (Drought)
  - 물 부족 (Water Stress)
  - 해안 침수 (Coastal Flood)
  - 하천 홍수 (River Flood)
  - 도시 침수 (Urban Flood)
  - 태풍 (Typhoon)
- **ModelOps API 연동**: H, E, V 값은 외부 서버에서 계산

### 2. 재무 영향 분석 (AAL - Average Annual Loss)
- **확률 × 손상률 기반**: 연평균 손실률(%) 계산
- **SSP 시나리오별 분석**: SSP1-2.6, SSP2-4.5, SSP3-7.0, SSP5-8.5
- **시계열 분석**: 단기(2020s), 중기(2030s), 장기(2040s, 2050s)
- **ModelOps API 연동**: base_aal은 외부 서버에서 계산

### 3. 건물 특성 분석 (Building Characteristics)
- **LLM 기반 정성 분석**: ModelOps 점수(H, E, V)를 자연어로 해석
- **리스크 요인 설명**: 건물 노후화, 배수 불량, 해안 인접 등 세부 요인 분석
- **Fork-Join 병렬 실행**: Report Chain과 동시 실행 (Node BC)

### 4. AI 기반 보고서 생성
- **Report Template**: 기존 ESG/TCFD 보고서 스타일 학습
- **Impact Analysis**: 정량 데이터(AAL, 점수) 기반 구체적 영향 분석
- **Strategy Generation**: 구체적 투자 시나리오 + 국제 표준 프로그램(RE100, SBTi, CDP) 포함
- **Report Composer**: Markdown + JSON 형식 최종 보고서
- **Validation & Refiner**: 자동 검증 및 품질 보완

### 5. 추가 데이터 반영 (Enhanced Analysis)
- **Node 5 이후 재실행**: 사용자 제공 추가 데이터로 보고서 품질 향상
- **캐시 활용**: Node 1~4 (ModelOps 데이터) 재사용으로 효율적 실행
- **Additional Data API**: `/api/additional-data` 엔드포인트로 관리

### 6. 재난 이력 분석
- **과거 재난 이벤트 조회**: 사업장 반경 50km 이내 재난 이력
- **재난 유형별 통계**: 빈도, 강도, 피해 규모 분석

### 7. 후보지 추천 (Batch Processing)
- **ModelOps 배치 작업**: 대한민국 전역 그리드 분석
- **비동기 처리**: Polling 방식으로 진행 상태 추적
- **Top-N 추천**: 리스크 최소 위치 추천

---

## 시스템 아키텍처

```
┌─────────────────────────────────────────────────────────────┐
│                   Spring Boot Server                         │
│                  (프론트엔드 연동)                            │
└────────────────────┬────────────────────────────────────────┘
                     │ REST API
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                  FastAPI Backend (main.py)                   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              Routes (src/routes/)                    │   │
│  │  - analysis.py (분석 API)                            │   │
│  │  - reports.py (보고서 API)                           │   │
│  │  - simulation.py (시뮬레이션 API)                    │   │
│  │  - recommendation.py (후보지 추천 API)               │   │
│  │  - additional_data.py (추가 데이터 API)              │   │
│  │  - disaster_history.py (재난 이력 API)               │   │
│  └────────────┬─────────────────────────────────────────┘   │
│               ▼                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │       Services (src/services/)                       │   │
│  │  - AnalysisService (Singleton)                       │   │
│  │  - ReportService (Singleton, ThreadPool)             │   │
│  │  - SimulationService                                 │   │
│  │  - RecommendationService (ModelOps 연동)             │   │
│  └────────────┬─────────────────────────────────────────┘   │
└───────────────┼──────────────────────────────────────────────┘
                │
                ▼
┌─────────────────────────────────────────────────────────────┐
│           AI Agent Layer (ai_agent/)                         │
│                                                              │
│  ┌────────────────────────────────────────────────────┐     │
│  │      SKAXPhysicalRiskAnalyzer (main.py)            │     │
│  │       (Main Orchestrator)                          │     │
│  └────────────┬───────────────────────────────────────┘     │
│               │                                              │
│               ▼                                              │
│  ┌────────────────────────────────────────────────────┐     │
│  │       LangGraph Workflow (11 Nodes)                │     │
│  │                                                     │     │
│  │  1. Data Collection (Scratch Space)                │     │
│  │  ┌────────────────┬────────────────┐               │     │
│  │  │ 2. Physical    │ 3. AAL         │ (병렬)        │     │
│  │  │    Risk Score  │    Analysis    │               │     │
│  │  │  (9 Agents)    │  (9 Agents)    │               │     │
│  │  │  [ModelOps]    │  [ModelOps]    │               │     │
│  │  └────────────────┴────────────────┘               │     │
│  │  4. Risk Integration (통합)                        │     │
│  │  ┌──────────────────────┬──────────────────┐       │     │
│  │  │ 5. Report Chain      │ BC. Building     │ (병렬)│     │
│  │  │  - Template (Node 5) │     Characteristics│      │     │
│  │  │  - Impact (Node 6)   │     (LLM 분석)    │      │     │
│  │  │  - Strategy (Node 7) │                   │      │     │
│  │  │  - Composer (Node 8) │                   │      │     │
│  │  └──────────────────────┴──────────────────┘       │     │
│  │  9. Validation (품질 검증)                         │     │
│  │  10. Finalization (MD/JSON/PDF 생성)               │     │
│  └────────────────────────────────────────────────────┘     │
│                                                              │
│  ┌────────────────────────────────────────────────────┐     │
│  │              Utils                                 │     │
│  │  - LLMClient (OpenAI)                              │     │
│  │  - ScratchSpaceManager (TTL 4시간)                 │     │
│  │  - AdditionalDataHelper (추가 데이터 가이드라인)   │     │
│  │  - LangSmithTracer (모니터링)                      │     │
│  └────────────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                   ModelOps API Server                        │
│  - Physical Risk Score 계산 (H, E, V)                        │
│  - AAL 계산 (base_aal)                                       │
│  - 배치 후보지 추천                                          │
└─────────────────────────────────────────────────────────────┘
```

---

## 설치 및 실행

### 사전 요구사항

- Python 3.11 이상
- OpenAI API Key
- (선택) LangSmith API Key (추적용)
- (선택) ModelOps API 서버 (실제 데이터용)

### 1. 저장소 클론

```bash
git clone <repository-url>
cd backend_team
```

### 2. 가상 환경 생성 및 의존성 설치

#### 방법 A: uv 사용 (권장)
```bash
pip install uv
uv pip install -e .
```

#### 방법 B: pip 사용
```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e .
```

### 3. 환경 변수 설정

`.env` 파일을 프로젝트 루트에 생성:

```env
# OpenAI API
OPENAI_API_KEY=your-openai-api-key

# LangSmith (선택)
LANGSMITH_API_KEY=your-langsmith-api-key
LANGSMITH_PROJECT=skax-physical-risk-dev

# API Server
HOST=0.0.0.0
PORT=8000
DEBUG=False

# API Key Authentication
API_KEY=your-secret-api-key

# ModelOps API (실제 데이터용)
MODELOPS_API_URL=http://modelops-server:5000
MODELOPS_API_KEY=your-modelops-api-key

# Mock Data (개발용)
USE_MOCK_DATA=False

# CORS
CORS_ORIGINS=*

# Scratch Space TTL
SCRATCH_TTL_HOURS=4
SCRATCH_CLEANUP_INTERVAL_HOURS=1
SCRATCH_AUTO_CLEANUP=True
```

### 4. 서버 실행

```bash
# 개발 모드 (자동 재시작)
python main.py

# 또는 uvicorn 직접 실행
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

서버가 시작되면 다음 URL에서 확인 가능:
- API 문서: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- Health Check: http://localhost:8000/

---

## API 문서

### 인증

모든 API 요청에는 `X-API-Key` 헤더가 필요함:

```bash
curl -H "X-API-Key: your-secret-api-key" http://localhost:8000/api/sites/{site_id}/analysis/start
```

### 주요 엔드포인트

#### 1. 분석 시작
```http
POST /api/sites/{site_id}/analysis/start
Content-Type: application/json
X-API-Key: your-secret-api-key

{
  "location": {
    "latitude": 37.5665,
    "longitude": 126.9780,
    "name": "서울 본사",
    "roadAddress": "서울특별시 중구 세종대로 110",
    "jibunAddress": "서울특별시 중구 태평로1가 31"
  },
  "buildingInfo": {
    "buildingAge": 25,
    "hasSeismicDesign": true,
    "fireAccess": true
  },
  "assetInfo": {
    "totalAssetValue": 50000000000,
    "insuranceCoverageRate": 0.7
  }
}
```

#### 2. 추가 데이터 반영 (Enhanced Analysis)
```http
POST /api/sites/{site_id}/analysis/enhance
X-API-Key: your-secret-api-key

{
  "jobId": "uuid",
  "additionalData": {
    "rawText": "건물 지하 1층 배수 시스템이 노후화되어 침수 위험 있음",
    "metadata": {
      "source": "시설관리팀",
      "date": "2025-12-01"
    },
    "buildingInfo": {
      "drainageCapacity": "50mm/hr",
      "basementFloors": 2
    },
    "powerUsage": {
      "itPowerKwh": 5000,
      "coolingPowerKwh": 3000,
      "totalPowerKwh": 10000
    }
  }
}
```

#### 3. 물리적 리스크 점수 조회
```http
GET /api/sites/{site_id}/analysis/physical-risk-scores?hazardType=HIGH_TEMPERATURE
X-API-Key: your-secret-api-key
```

#### 4. 재무 영향 (AAL) 조회
```http
GET /api/sites/{site_id}/analysis/financial-impacts
X-API-Key: your-secret-api-key
```

#### 5. 보고서 생성
```http
POST /api/reports
X-API-Key: your-secret-api-key

{
  "reportType": "PHYSICAL_RISK",
  "siteIds": ["uuid1", "uuid2"],
  "language": "KO",
  "format": "PDF"
}
```

#### 6. 재난 이력 조회
```http
GET /api/disaster-history?latitude=37.5665&longitude=126.9780&radius=50
X-API-Key: your-secret-api-key
```

#### 7. 후보지 추천 (배치 작업 시작)
```http
POST /api/recommendation/batch/start
X-API-Key: your-secret-api-key

{
  "scenarioId": 4,
  "topN": 10,
  "buildingInfo": {...},
  "assetInfo": {...}
}
```

전체 API 명세는 `/docs`에서 확인.

---

## AI Agent 구조

### LangGraph 워크플로우 (11개 노드)

| 노드 | Agent | 역할 | 출력 |
|------|-------|------|------|
| **1. Data Collection** | DataCollectionAgent | Scratch Space 데이터 수집 | climate_data, scratch_session_id |
| **2. Physical Risk Score** | 9개 Score Agents | H×E×V 기반 리스크 점수 (ModelOps) | physical_risk_scores (9개) |
| **3. AAL Analysis** | 9개 AAL Agents | P×D 기반 재무 손실률 (ModelOps) | aal_analysis (9개) |
| **4. Risk Integration** | - | 리스크 통합 및 우선순위화 | integrated_risks |
| **BC. Building Characteristics** | BuildingCharacteristicsAgent | LLM 기반 정성 분석 | building_characteristics |
| **5. Report Template** | ReportTemplateAgent | 기존 보고서 스타일 추출 | report_template |
| **6. Impact Analysis** | ImpactAnalysisAgent | 정량 데이터 기반 영향 분석 | impact_analysis |
| **7. Strategy Generation** | StrategyGenerationAgent | 구체적 투자 시나리오 생성 | response_strategy |
| **8. Report Generation** | ReportComposerAgent | 최종 보고서 작성 | generated_report |
| **9. Validation** | ValidationAgent | Report + BC 통합 검증 | validation_result |
| **10. Finalization** | FinalizerNode | MD/JSON/PDF 파일 저장 | final_report, output_paths |

### Sub-Agent 목록 (26개)

#### Physical Risk Score Agents (9개) - ModelOps 연동
1. ExtremeHeatScoreAgent
2. ExtremeColdScoreAgent
3. WildfireScoreAgent
4. DroughtScoreAgent
5. WaterStressScoreAgent
6. CoastalFloodScoreAgent
7. RiverFloodScoreAgent
8. UrbanFloodScoreAgent
9. TyphoonScoreAgent

#### AAL Analysis Agents (9개) - ModelOps 연동
1. ExtremeHeatAALAgent
2. ExtremeColdAALAgent
3. WildfireAALAgent
4. DroughtAALAgent
5. WaterStressAALAgent
6. CoastalFloodAALAgent
7. RiverFloodAALAgent
8. UrbanFloodAALAgent
9. TyphoonAALAgent

#### Report Generation Agents (8개)
1. DataCollectionAgent - Scratch Space 관리
2. BuildingCharacteristicsAgent - LLM 기반 정성 분석
3. ReportTemplateAgent - 보고서 템플릿 분석
4. ImpactAnalysisAgent - 정량 영향 분석
5. StrategyGenerationAgent - 전략 생성 (구체적 투자 시나리오)
6. ReportComposerAgent - 보고서 작성
7. ValidationAgent - 통합 검증
8. FinalizerNode - 최종화

### Fork-Join 병렬 처리

```
Node 1 (Data Collection)
  ↓
Node 2 ∥ Node 3 (Physical Risk Score ∥ AAL Analysis)
  ↓
Node 4 (Risk Integration)
  ↓
Node BC ∥ Nodes 5-8 (Building Characteristics ∥ Report Chain)
  ↓
Node 9 (Validation - 통합 검증)
  ↓
Node 10 (Finalization)
```

### 추가 데이터 반영 메커니즘

```
1차 분석 (Node 1~4)
  ↓ State 캐싱
사용자 추가 데이터 입력
  ↓
Additional Data Helper (LLM 1회 호출)
  ↓ Agent별 가이드라인 생성
Node 5 이후 재실행 (캐시 재사용)
  ↓
향상된 보고서 생성
```

---

## 프로젝트 구조

```
backend_team/
├── main.py                      # FastAPI 앱 진입점
├── pyproject.toml               # 프로젝트 설정
├── requirements.txt             # pip freeze 결과
├── .env                         # 환경 변수
├── .gitignore
│
├── src/                         # API Layer
│   ├── core/
│   │   ├── config.py           # 설정 관리
│   │   ├── auth.py             # API Key 인증
│   │   ├── logging_config.py   # 로깅 설정
│   │   └── middleware.py       # RequestID 미들웨어
│   ├── routes/
│   │   ├── analysis.py         # 분석 API
│   │   ├── reports.py          # 보고서 API
│   │   ├── simulation.py       # 시뮬레이션 API
│   │   ├── recommendation.py   # 후보지 추천 API
│   │   ├── additional_data.py  # 추가 데이터 API
│   │   └── disaster_history.py # 재난 이력 API
│   ├── services/
│   │   ├── analysis_service.py (Singleton)
│   │   ├── report_service.py (Singleton, ThreadPool)
│   │   ├── simulation_service.py
│   │   └── recommendation_service.py (ModelOps 연동)
│   └── schemas/
│       ├── analysis.py
│       ├── reports.py
│       ├── recommendation.py
│       └── common.py
│
├── ai_agent/                    # AI Agent Layer
│   ├── main.py                 # SKAXPhysicalRiskAnalyzer
│   ├── config/
│   │   └── settings.py         # Agent 설정
│   ├── workflow/
│   │   ├── graph.py            # LangGraph 워크플로우
│   │   ├── nodes.py            # 11개 노드 구현
│   │   └── state.py            # SuperAgentState
│   ├── agents/
│   │   ├── data_processing/
│   │   │   └── data_collection_agent.py
│   │   ├── sub_agents/
│   │   │   ├── physical_risk_score/    # 9개
│   │   │   └── aal_analysis/           # 9개
│   │   └── report_generation/
│   │       ├── building_characteristics_agent.py
│   │       ├── report_template_agent_1.py
│   │       ├── impact_analysis_agent_2.py
│   │       ├── strategy_generation_agent_3.py
│   │       ├── report_composer_agent_4.py
│   │       ├── validation_agent_5.py
│   │       └── finalizer_node_7.py
│   ├── services/
│   │   └── modelops_client.py   # ModelOps API 클라이언트
│   └── utils/
│       ├── llm_client.py        # OpenAI
│       ├── scratch_manager.py   # Scratch Space (TTL)
│       ├── ttl_cleaner.py       # 자동 정리 스케줄러
│       ├── additional_data_helper.py  # 추가 데이터 가이드라인
│       ├── mock_db_loader.py    # Mock 데이터
│       └── langsmith_tracer.py  # LangSmith 추적
│
├── docs/                        # 문서
│   ├── ERD_Diagram.md
│   ├── fastapi_threadpool_shutdown.md  # 쓰레드 풀 관리
│   └── ...
│
├── scratch/                     # Scratch Space (TTL 4시간, 자동 정리)
├── report_outputs/              # 생성된 보고서
├── Dockerfile
└── docker-deploy.sh
```

---

## 환경 변수

### 필수

| 변수명 | 설명 | 기본값 |
|--------|------|--------|
| `OPENAI_API_KEY` | OpenAI API 키 | - |
| `API_KEY` | API 인증 키 | `your-secret-api-key` |

### 선택

| 변수명 | 설명 | 기본값 |
|--------|------|--------|
| `LANGSMITH_API_KEY` | LangSmith 추적 키 | - |
| `LANGSMITH_PROJECT` | LangSmith 프로젝트 | `skax-physical-risk-dev` |
| `MODELOPS_API_URL` | ModelOps API URL | - |
| `MODELOPS_API_KEY` | ModelOps API 키 | - |
| `HOST` | 서버 호스트 | `0.0.0.0` |
| `PORT` | 서버 포트 | `8000` |
| `DEBUG` | 디버그 모드 | `False` |
| `USE_MOCK_DATA` | Mock 데이터 사용 | `False` |
| `CORS_ORIGINS` | CORS 허용 도메인 | `*` |
| `SCRATCH_TTL_HOURS` | Scratch Space TTL | `4` |
| `SCRATCH_CLEANUP_INTERVAL_HOURS` | 자동 정리 간격 | `1` |
| `SCRATCH_AUTO_CLEANUP` | 자동 정리 활성화 | `True` |

---

## 개발 가이드

### 테스트 실행

```bash
# Mock 데이터로 전체 워크플로우 테스트
python test_main_mock.py

# 특정 Agent 테스트
pytest tests/test_workflow.py
```

### 코드 품질

```bash
# Black (포맷팅)
black .

# Flake8 (린팅)
flake8 ai_agent/ src/

# MyPy (타입 체크)
mypy ai_agent/ src/
```

### Docker

```bash
# 빌드
docker build -t skax-backend:latest .

# 실행
docker run -d \
  -p 8000:8000 \
  --env-file .env \
  --name skax-backend \
  skax-backend:latest
```

### 쓰레드 풀 안전한 종료

FastAPI 앱 종료 시 `ReportService`의 ThreadPoolExecutor가 자동으로 정리됨:

```python
# main.py
@app.on_event("shutdown")
async def shutdown_event():
    if report_service_instance:
        report_service_instance.shutdown()  # 실행 중인 작업 완료 대기
```

자세한 내용: [docs/fastapi_threadpool_shutdown.md](docs/fastapi_threadpool_shutdown.md)

---

## 📝 변경 이력

### v1.2.0 (2025-12-05)

#### ✨ 보고서 품질 개선 - 구체적 투자 시나리오 추가
- **StrategyGenerationAgent 강화**:
  - `improvement_scenarios` 필드 추가 (투자 시나리오별 AAL 감소 예측)
  - `specific_programs` 필드 추가 (RE100, SBTi, CDP, ISO 14090 등)
  - SMART 기준 강제: Specific, Measurable, Time-bound, Financially quantified
  - ❌ "지속 가능한 에너지 시스템 도입" 같은 추상적 표현 금지
  - ✅ "RE100 참여: 2030년까지 재생에너지 100% 전환, 연간 500억원 투자" 강제
- **ReportComposerAgent 강화**:
  - Strategy, Risk Management, Metrics & Targets 섹션 가이드라인 강화
  - "결과 나열" → "개선 방안과 효과" 중심으로 전환
  - 예: "AAL 0.87%인데, 예산 50%를 배수 개선에 투입하면 0.40%로 감소"
- **ValidationAgent 버그 수정**:
  - strategies 데이터 구조 불일치 해결 (List/Dict 모두 처리)

#### 🔧 인프라 개선
- **ThreadPoolExecutor 안전한 종료**: `ReportService.shutdown()` 구현
- **Scratch Space TTL 자동 정리**: 데몬 스레드 기반 백그라운드 정리
- **Singleton Service 패턴**: `main.py`에서 앱 수준 서비스 관리

#### 📚 문서 추가
- [docs/fastapi_threadpool_shutdown.md](docs/fastapi_threadpool_shutdown.md)

### v1.1.0 (2025-11-25)

#### 🏗️ Fork-Join 병렬 아키텍처 적용
- **Node 2 ∥ Node 3**: Physical Risk Score와 AAL 병렬 실행
- **Node BC ∥ Nodes 5-8**: Building Characteristics와 Report Chain 병렬 실행
- **BuildingCharacteristicsAgent 추가**: LLM 기반 정성 분석 (ModelOps 점수 해석)

#### 🔗 ModelOps API 연동
- Physical Risk Score H, E, V 계산 외부화
- AAL base_aal 계산 외부화
- 후보지 추천 배치 작업 연동

#### 📦 추가 데이터 API
- `/api/additional-data` 엔드포인트 추가
- Node 5 이후 재실행 메커니즘 구현
- AdditionalDataHelper (LLM 1회 호출로 가이드라인 생성)

#### ⚡ Scratch Space 관리
- TTL 4시간 자동 삭제
- 백그라운드 정리 스케줄러 (1시간마다)
- ScratchSpaceManager 구현

#### 📚 문서 업데이트
- 전체 아키텍처 다이어그램 업데이트
- API 엔드포인트 7개로 확장

---

## 라이선스

이 프로젝트는 비공개 프로젝트다.

---

## 문의

기술 지원 및 문의사항은 개발팀에 문의.

---

**Built with using FastAPI, LangChain, LangGraph, and OpenAI**
