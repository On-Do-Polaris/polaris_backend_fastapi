# SKAX Physical Risk Analysis System

**AI Agent 기반 사업장 기후 물리적 리스크 분석 시스템**

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.116.1-009688.svg)](https://fastapi.tiangolo.com/)
[![LangGraph](https://img.shields.io/badge/LangGraph-1.0.1-FF6F00.svg)](https://langchain-ai.github.io/langgraph/)

## 📋 목차

- [개요](#개요)
- [주요 기능](#주요-기능)
- [시스템 아키텍처](#시스템-아키텍처)
- [설치 및 실행](#설치-및-실행)
- [API 문서](#api-문서)
- [AI Agent 구조](#ai-agent-구조)
- [프로젝트 구조](#프로젝트-구조)
- [환경 변수 설정](#환경-변수-설정)

---

## 개요

SKAX Physical Risk Analysis System은 **기후 변화로 인한 물리적 리스크를 AI Agent 기반으로 분석**하는 FastAPI 백엔드 시스템입니다. LangGraph를 활용한 워크플로우 오케스트레이션으로 9가지 재해 유형에 대한 리스크 점수, 재무 영향, 대응 전략을 자동으로 생성합니다.

### 핵심 특징

- **AI Agent 기반 분석**: LangGraph로 구현된 13개 노드, 25개 Sub-Agent
- **병렬 처리**: Physical Risk Score와 AAL 분석 동시 실행
- **자동 보고서 생성**: LLM 기반 TCFD/ESG 보고서 자동 작성
- **재시도 메커니즘**: 검증 실패 시 자동 보완 (Refiner Loop)
- **Spring Boot 연동**: RESTful API로 Spring Boot 서버와 통신

---

## 주요 기능

### 1. 물리적 리스크 분석 (Physical Risk Score)
- **H × E × V 방식**: Hazard × Exposure × Vulnerability 기반 점수 계산
- **9가지 재해 유형**:
  - 극한 고온 (Extreme Heat)
  - 극한 저온 (Extreme Cold)
  - 산불 (Wildfire)
  - 가뭄 (Drought)
  - 물 부족 (Water Stress)
  - 해수면 상승 (Sea Level Rise)
  - 하천 홍수 (River Flood)
  - 도시 침수 (Urban Flood)
  - 태풍 (Typhoon)

### 2. 재무 영향 분석 (AAL - Average Annual Loss)
- **확률 × 손상률 기반**: 연평균 손실률 계산
- **SSP 시나리오별 분석**: SSP1-2.6, SSP2-4.5, SSP3-7.0, SSP5-8.5
- **시계열 분석**: 단기(Q1-Q4), 중기(2026-2030), 장기(2020s-2050s)

### 3. AI 기반 보고서 생성
- **Report Analysis**: 기존 ESG/TCFD 보고서 스타일 학습
- **Impact Analysis**: 전력 소비 기반 구체적 영향 분석
- **Strategy Generation**: LLM + RAG 기반 대응 전략 생성
- **Validation & Refiner**: 자동 검증 및 품질 보완

### 4. 취약성 평가 (Vulnerability Analysis)
- 건물 연식, 내진 설계, 소방 접근성 기반 취약성 점수
- 9개 재해 유형별 취약성 평가

### 5. 사업장 이전 시뮬레이션
- 대안 위치 비교 분석
- 리스크 감소율 계산

---

## 시스템 아키텍처

```
┌─────────────────────────────────────────────────────────────┐
│                      Spring Boot Server                      │
│                    (프론트엔드 연동)                          │
└────────────────────┬────────────────────────────────────────┘
                     │ REST API
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                     FastAPI Backend                          │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              API Layer (src/)                        │   │
│  │  - analysis.py (리스크 분석 API)                     │   │
│  │  - reports.py (보고서 생성 API)                      │   │
│  │  - simulation.py (시뮬레이션 API)                    │   │
│  │  - meta.py (메타데이터 API)                          │   │
│  └────────────┬─────────────────────────────────────────┘   │
│               ▼                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │           Service Layer (src/services/)              │   │
│  │  - AnalysisService                                   │   │
│  │  - ReportService                                     │   │
│  │  - SimulationService                                 │   │
│  └────────────┬─────────────────────────────────────────┘   │
└───────────────┼──────────────────────────────────────────────┘
                │
                ▼
┌─────────────────────────────────────────────────────────────┐
│              AI Agent Layer (ai_agent/)                      │
│                                                              │
│  ┌────────────────────────────────────────────────────┐     │
│  │        SKAXPhysicalRiskAnalyzer                    │     │
│  │         (Main Orchestrator)                        │     │
│  └────────────┬───────────────────────────────────────┘     │
│               │                                              │
│               ▼                                              │
│  ┌────────────────────────────────────────────────────┐     │
│  │         LangGraph Workflow (13 Nodes)              │     │
│  │                                                     │     │
│  │  1. Data Collection (PostgreSQL)                   │     │
│  │  2. Vulnerability Analysis                         │     │
│  │  ┌────────────────┬────────────────┐               │     │
│  │  │ 3a. Physical   │ 3b. AAL        │ (병렬 실행)   │     │
│  │  │     Risk Score │     Analysis   │               │     │
│  │  │  (9 Sub-Agent) │  (9 Sub-Agent) │               │     │
│  │  └────────────────┴────────────────┘               │     │
│  │  4. Risk Integration                               │     │
│  │  5. Report Template (ReportAnalysisAgent)          │     │
│  │  6. Impact Analysis (ImpactAnalysisAgent)          │     │
│  │  7. Strategy Generation (StrategyGenerationAgent)  │     │
│  │  8. Report Generation (ReportComposerAgent)        │     │
│  │  9. Validation (ValidationAgent)                   │     │
│  │  9a. Refiner (RefinerAgent) ← 자동 보완 루프       │     │
│  │  10. Finalization (FinalizerNode)                  │     │
│  └────────────────────────────────────────────────────┘     │
│                                                              │
│  ┌────────────────────────────────────────────────────┐     │
│  │              Utilities                             │     │
│  │  - LLMClient (OpenAI)                              │     │
│  │  - RAGEngine (Vector Search)                       │     │
│  │  - DatabaseManager (PostgreSQL)                    │     │
│  │  - ScratchSpaceManager (임시 데이터)               │     │
│  │  - LangSmithTracer (관찰성)                        │     │
│  └────────────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────────────┘
```

---

## 설치 및 실행

### 사전 요구사항

- Python 3.11 이상
- PostgreSQL 데이터베이스
- OpenAI API Key
- (선택) LangSmith API Key (추적용)

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

# Database
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/polaris

# API Server
HOST=0.0.0.0
PORT=8000
DEBUG=False

# API Key Authentication
API_KEY=your-secret-api-key

# Mock Data (개발용)
USE_MOCK_DATA=False
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

모든 API 요청에는 `X-API-Key` 헤더가 필요합니다:

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
  "site": {
    "id": "uuid",
    "name": "서울 본사",
    "latitude": 37.5665,
    "longitude": 126.9780,
    "address": "서울특별시 중구",
    "assetValue": 50000000000
  }
}
```

**응답**:
```json
{
  "jobId": "uuid",
  "siteId": "uuid",
  "status": "completed",
  "progress": 100,
  "currentNode": "completed",
  "startedAt": "2025-11-25T10:00:00",
  "completedAt": "2025-11-25T10:05:00"
}
```

#### 2. 물리적 리스크 점수 조회
```http
GET /api/sites/{site_id}/analysis/physical-risk-scores?hazardType=HIGH_TEMPERATURE
X-API-Key: your-secret-api-key
```

#### 3. 재무 영향 (AAL) 조회
```http
GET /api/sites/{site_id}/analysis/financial-impacts
X-API-Key: your-secret-api-key
```

#### 4. 보고서 생성
```http
POST /api/sites/{site_id}/reports/generate
X-API-Key: your-secret-api-key

{
  "reportType": "TCFD",
  "format": "PDF",
  "language": "KO"
}
```

#### 5. 시뮬레이션
```http
POST /api/sites/{site_id}/simulation/relocate
X-API-Key: your-secret-api-key

{
  "alternativeLocations": [
    {
      "name": "대전 지사",
      "latitude": 36.3504,
      "longitude": 127.3845
    }
  ]
}
```

전체 API 명세는 `/docs`에서 확인하세요.

---

## AI Agent 구조

### LangGraph 워크플로우 (13개 노드)

| 노드 | Agent | 역할 | 출력 |
|------|-------|------|------|
| **1. Data Collection** | DataCollectionAgent | PostgreSQL에서 기후 데이터 수집 | climate_data, scratch_session_id |
| **2. Vulnerability Analysis** | VulnerabilityAnalysisAgent | 건물/자산 취약성 평가 | vulnerability_scores (9개) |
| **3a. Physical Risk Score** | 9개 Score Agents | H×E×V 기반 리스크 점수 | physical_risk_scores (9개) |
| **3b. AAL Analysis** | 9개 AAL Agents | P×D 기반 재무 손실률 | aal_analysis (9개) |
| **4. Risk Integration** | - | 리스크 통합 및 우선순위화 | integrated_risks |
| **5. Report Template** | ReportAnalysisAgent | 기존 보고서 스타일 추출 | report_profile |
| **6. Impact Analysis** | ImpactAnalysisAgent | 전력 소비 기반 영향 분석 | impact_analysis |
| **7. Strategy Generation** | StrategyGenerationAgent | LLM+RAG 대응 전략 생성 | response_strategy |
| **8. Report Generation** | ReportComposerAgent | 최종 보고서 작성 | generated_report |
| **9. Validation** | ValidationAgent | 품질 검증 | validation_result |
| **9a. Refiner** | RefinerAgent | 자동 보완 (최대 3회) | refined_report |
| **10. Finalization** | FinalizerNode | MD/JSON/PDF 파일 저장 | final_report, output_paths |

### Sub-Agent 목록 (25개)

#### Physical Risk Score Agents (9개)
1. ExtremeHeatScoreAgent
2. ExtremeColdScoreAgent
3. WildfireScoreAgent
4. DroughtScoreAgent
5. WaterStressScoreAgent
6. SeaLevelRiseScoreAgent
7. RiverFloodScoreAgent
8. UrbanFloodScoreAgent
9. TyphoonScoreAgent

#### AAL Analysis Agents (9개)
1. ExtremeHeatAALAgent
2. ExtremeColdAALAgent
3. WildfireAALAgent
4. DroughtAALAgent
5. WaterStressAALAgent
6. SeaLevelRiseAALAgent
7. RiverFloodAALAgent
8. UrbanFloodAALAgent
9. TyphoonAALAgent

#### Report Generation Agents (7개)
1. ReportAnalysisAgent - 보고서 스타일 분석
2. ImpactAnalysisAgent - 영향 분석
3. StrategyGenerationAgent - 전략 생성
4. ReportComposerAgent - 보고서 작성
5. ValidationAgent - 검증
6. RefinerAgent - 자동 보완
7. FinalizerNode - 최종화

### Refiner Loop (자동 보완 메커니즘)

```
[Validation] → 검증 실패 감지
     ↓
[이슈 분류]
     ├─ 텍스트/구조 이슈 → [Refiner] (최대 3회)
     ├─ 영향 분석 이슈 → [Impact Analysis] 재실행
     ├─ 전략 이슈 → [Strategy Generation] 재실행
     └─ 재시도 초과 → [Finalization]
```

---

## 프로젝트 구조

```
backend_team/
├── main.py                      # FastAPI 앱 진입점
├── pyproject.toml               # 프로젝트 설정 및 의존성
├── requirements.txt             # pip freeze 결과
├── .env                         # 환경 변수 (Git 제외)
├── .gitignore
│
├── src/                         # API Layer
│   ├── core/
│   │   ├── config.py           # 설정 관리
│   │   └── auth.py             # API Key 인증
│   ├── routes/
│   │   ├── analysis.py         # 분석 API
│   │   ├── reports.py          # 보고서 API
│   │   ├── simulation.py       # 시뮬레이션 API
│   │   └── meta.py             # 메타데이터 API
│   ├── services/
│   │   ├── analysis_service.py
│   │   ├── report_service.py
│   │   └── simulation_service.py
│   └── schemas/
│       ├── analysis.py         # Pydantic 모델
│       ├── reports.py
│       └── common.py
│
├── ai_agent/                    # AI Agent Layer
│   ├── main.py                 # SKAXPhysicalRiskAnalyzer
│   ├── config/
│   │   └── settings.py         # Agent 설정
│   ├── workflow/
│   │   ├── graph.py            # LangGraph 워크플로우 정의
│   │   ├── nodes.py            # 13개 노드 구현
│   │   └── state.py            # SuperAgentState 정의
│   ├── agents/
│   │   ├── data_processing/
│   │   │   ├── data_collection_agent.py
│   │   │   └── vulnerability_analysis_agent.py
│   │   ├── risk_analysis/
│   │   │   ├── physical_risk_score/    # 9개 Score Agents
│   │   │   └── aal_analysis/           # 9개 AAL Agents
│   │   └── report_generation/
│   │       ├── report_analysis_agent_1.py
│   │       ├── impact_analysis_agent_2.py
│   │       ├── strategy_generation_agent_3.py
│   │       ├── report_composer_agent_4.py
│   │       ├── validation_agent_5.py
│   │       ├── refiner_agent_6.py
│   │       └── finalizer_node_7.py
│   └── utils/
│       ├── llm_client.py       # OpenAI 클라이언트
│       ├── rag_engine.py       # Vector Search
│       ├── database.py         # PostgreSQL 연결
│       ├── scratch_manager.py  # 임시 데이터 관리
│       └── langsmith_tracer.py # LangSmith 추적
│
├── docs/                        # 문서
│   ├── ERD_Diagram.md
│   ├── GITHUB_SECRETS_GUIDE.md
│   ├── LOCAL_DOCKER_TEST_GUIDE.md
│   └── ORACLE_SERVER_DEPLOY_GUIDE.md
│
├── scratch/                     # 임시 데이터 저장소 (TTL 4시간)
├── Dockerfile                   # Docker 이미지 빌드
└── docker-deploy.sh             # 배포 스크립트
```

---

## 환경 변수 설정

### 필수 환경 변수

| 변수명 | 설명 | 기본값 |
|--------|------|--------|
| `OPENAI_API_KEY` | OpenAI API 키 (필수) | - |
| `DATABASE_URL` | PostgreSQL 연결 URL | `postgresql+asyncpg://user:password@localhost:5432/polaris` |
| `API_KEY` | API 인증 키 | `your-secret-api-key` |

### 선택 환경 변수

| 변수명 | 설명 | 기본값 |
|--------|------|--------|
| `LANGSMITH_API_KEY` | LangSmith 추적 API 키 | - |
| `LANGSMITH_PROJECT` | LangSmith 프로젝트 이름 | `skax-physical-risk-dev` |
| `HOST` | 서버 호스트 | `0.0.0.0` |
| `PORT` | 서버 포트 | `8000` |
| `DEBUG` | 디버그 모드 | `False` |
| `USE_MOCK_DATA` | Mock 데이터 사용 (개발용) | `False` |
| `CORS_ORIGINS` | CORS 허용 도메인 | `*` |

---

## 개발 가이드

### 테스트 실행

```bash
# 전체 테스트
pytest

# 커버리지 포함
pytest --cov=ai_agent --cov=src

# 특정 테스트
pytest tests/test_workflow.py
```

### 코드 품질 검사

```bash
# Black (코드 포맷팅)
black .

# Flake8 (린팅)
flake8 ai_agent/ src/

# MyPy (타입 체크)
mypy ai_agent/ src/
```

### Docker 빌드 및 실행

```bash
# 이미지 빌드
docker build -t skax-backend:latest .

# 컨테이너 실행
docker run -d \
  -p 8000:8000 \
  --env-file .env \
  --name skax-backend \
  skax-backend:latest
```

---

## 라이선스

이 프로젝트는 비공개 프로젝트입니다.

---

## 문의

기술 지원 및 문의사항은 개발팀에 문의하세요.

---

**Built with ❤️ using FastAPI, LangGraph, and OpenAI**
