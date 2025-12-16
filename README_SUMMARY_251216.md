# SKAX Physical Risk Analysis System - 요약

**AI Agent 기반 사업장 기후 물리적 리스크 분석 시스템 (빠른 시작 가이드)**

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.116.1-009688.svg)](https://fastapi.tiangolo.com/)
[![LangChain](https://img.shields.io/badge/LangChain-1.1.0-00A67E.svg)](https://langchain.com/)
[![LangGraph](https://img.shields.io/badge/LangGraph-1.0.3-FF6F00.svg)](https://langchain-ai.github.io/langgraph/)

> **전체 문서**: 상세한 내용은 [README.md](README.md)를 참조하세요.

---

## 개요

SKAX Physical Risk Analysis System은 기후 변화로 인한 물리적 리스크를 AI Agent 기반으로 분석하는 FastAPI 백엔드 시스템입니다. 9가지 재해 유형에 대한 리스크 점수, 재무 영향(AAL), TCFD 보고서를 자동 생성합니다.

### 핵심 특징

- **AI Agent 기반 분석**: LangGraph 11개 노드, 26개 특화 에이전트
- **9가지 재해 유형**: 극한 고온/저온, 산불, 가뭄, 물 부족, 홍수(3종), 태풍
- **자동 TCFD/ESG 보고서**: LLM 기반 준수 보고서 생성
- **ModelOps 연동**: 외부 서버에서 H×E×V, AAL 계산
- **Spring Boot 통합**: RESTful API 게이트웨이 연동

---

## 빠른 시작

### 사전 요구사항

- Python 3.11+
- OpenAI API Key
- PostgreSQL 15+ (PostGIS)

### 설치

```bash
# 1. 저장소 이동
cd C:\Users\SKAX\Documents\report_fastapi\79-report-agent\polaris_backend_fastapi

# 2. 가상 환경 생성 및 활성화
python -m venv .venv
.venv\Scripts\activate  # Windows

# 3. 의존성 설치
pip install -r requirements.txt

# 4. 환경 변수 설정
copy .env.example .env
# .env 파일 편집하여 OPENAI_API_KEY, DATABASE_URL 설정

# 5. 서버 실행
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### API 문서 확인

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

---

## 주요 기능

### 1. 물리적 리스크 분석

**H × E × V 공식** 기반 리스크 점수 (100점 만점)

- **Hazard**: 기후 재해 강도
- **Exposure**: 자산 노출 수준
- **Vulnerability**: 건물/사업장 취약성

**9가지 재해 유형**: 극한 고온, 극한 저온, 산불, 가뭄, 물 부족, 해안 홍수, 하천 홍수, 도시 홍수, 태풍

**SSP 시나리오**: SSP1-2.6, SSP2-4.5, SSP3-7.0, SSP5-8.5

### 2. 재무 영향 분석 (AAL)

**AAL (Average Annual Loss)**: 연평균 자산 손실률 (%)

```
AAL = base_aal × F_vuln × (1 - IR)
```

### 3. AI 보고서 생성

- **RAG 통합**: Qdrant 벡터 스토어를 통한 기존 보고서 참조
- **품질 검증**: 자동화된 검증 및 개선 루프
- **출력 포맷**: Markdown, JSON, PDF
- **다국어**: 한국어, 영어

### 4. 추가 기능

- 과거 재난 분석 (50km 반경)
- 후보지 추천 (배치 처리)
- 입지 이전 시뮬레이션

---

## API 엔드포인트

### 분석 시작

```http
POST /api/sites/{site_id}/analysis/start
X-API-Key: your-api-key

{
  "location": {
    "latitude": 37.5665,
    "longitude": 126.9780
  },
  "buildingInfo": {
    "buildingAge": 25,
    "hasSeismicDesign": true
  },
  "assetInfo": {
    "totalAssetValue": 50000000000
  }
}
```

### 보고서 생성

```http
POST /api/reports
X-API-Key: your-api-key

{
  "reportType": "PHYSICAL_RISK",
  "siteIds": ["uuid"],
  "language": "KO",
  "format": "PDF"
}
```

### 재난 이력 조회

```http
GET /api/disaster-history?latitude=37.5665&longitude=126.9780&radius=50
X-API-Key: your-api-key
```

**전체 API 명세**: http://localhost:8000/docs

---

## 시스템 아키텍처

```
Frontend → Spring Boot (8080) → FastAPI (8000) → ModelOps (8001)
                                      ↓
                                 PostgreSQL (5432)
                                      ↓
                                 Qdrant (6333)
```

### LangGraph 워크플로우 (11 노드)

```
Node 1: Data Collection
  ↓
Node 2 ∥ Node 3: Physical Risk Score ∥ AAL Analysis (ModelOps)
  ↓
Node 4: Risk Integration
  ↓
Node BC ∥ Nodes 5-8: Building Characteristics ∥ Report Chain
  ↓
Node 9: Validation
  ↓
Node 10: Finalization
```

---

## 환경 변수

### 필수

```bash
OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxxxxxxxxxx
API_KEY=your-secure-api-key
DATABASE_URL=postgresql://postgres:password@localhost:5432/skala_datawarehouse
```

### 선택 (개발용)

```bash
# LangSmith 추적
LANGSMITH_API_KEY=lsv2_pt_xxxxxxxxxxxxxxxxxxxxx
LANGSMITH_PROJECT=skax-physical-risk-dev

# ModelOps 연동
MODELOPS_URL=http://localhost:8001

# Qdrant 벡터 DB
QDRANT_URL=http://localhost:6333
RAG_MOCK_MODE=false

# 모의 데이터
USE_MOCK_DATA=false
```

---

## Docker 배포

### 빠른 실행

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

### Docker Compose (권장)

```bash
docker-compose up -d
```

**포함 서비스**: FastAPI, PostgreSQL (PostGIS), Qdrant

---

## 프로젝트 구조

```
polaris_backend_fastapi/
├── main.py                      # FastAPI 앱 진입점
├── requirements.txt             # 의존성
├── .env                         # 환경 변수
│
├── src/                         # API Layer
│   ├── routes/                  # API 라우트
│   ├── services/                # 비즈니스 로직
│   └── schemas/                 # Pydantic 모델
│
├── ai_agent/                    # AI Agent Layer
│   ├── workflow/                # LangGraph 워크플로우
│   ├── agents/                  # 26개 에이전트
│   ├── services/                # ModelOps, Spring Boot 클라이언트
│   └── utils/                   # LLM, RAG, Database 유틸
│
├── ETL/                         # 데이터 파이프라인
├── docs/                        # 문서
├── scratch/                     # 임시 파일 (TTL: 4시간)
└── report_outputs/              # 생성된 보고서
```

---

## 개발 가이드

### 테스트

```bash
# Mock 데이터로 전체 워크플로우 테스트
python test_main_mock.py

# 특정 Agent 테스트
pytest tests/test_workflow.py
```

### 코드 품질

```bash
# 포맷팅
black .

# 린팅
flake8 ai_agent/ src/

# 타입 체크
mypy ai_agent/ src/
```

---

## 문제 해결

### OpenAI API 에러

```bash
# .env 파일 확인
OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxxxxxxxxxx
```

### 데이터베이스 연결 실패

```bash
# 연결 문자열 확인
DATABASE_URL=postgresql://postgres:password@localhost:5432/skala_datawarehouse
```

### Qdrant 연결 실패

```bash
# Qdrant 서버 실행
docker run -p 6333:6333 qdrant/qdrant:v1.7.0

# 또는 모의 모드 사용
RAG_MOCK_MODE=true
```

### 메모리 부족

```bash
# Scratch 공간 TTL 감소
SCRATCH_TTL_HOURS=2

# Worker 수 감소
uvicorn main:app --workers 2
```

---

## 데이터베이스

### PostgreSQL 테이블 (45+)

#### 위치 & 기후

- `location_grid`: 기후 그리드 (PostGIS)
- `ta_data`, `rn_data`, `ws_data`: 기후 데이터 (SSP 시나리오별)

#### 리스크 & 재난

- `site_assessment_results`: ModelOps 계산 결과
- `disaster_yearbook`: 과거 재난 기록
- `typhoon_data`: 태풍 경로

#### 인프라

- `buildings_data`: 건물 데이터
- `dem_data`: 디지털 고도 모델

---

## 외부 서비스 연동

### ModelOps API

- **물리적 리스크 계산**: H×E×V
- **AAL 계산**: 확률×피해 모델링
- **배치 입지 평가**: ~1,000개 그리드

**엔드포인트**:

- `POST /api/v1/site-assessment/calculate`
- `POST /api/v1/site-assessment/batch/start`

### RAG (Qdrant)

기존 ESG/TCFD 보고서 참조

**보고서 업로드**:

```bash
python ai_agent/utils/scripts/upload_reports.py \
  --pdf report.pdf \
  --company "Samsung" \
  --year 2024
```

### Spring Boot 통합

FastAPI는 Spring Boot 게이트웨이의 AI 서비스로 작동

---

## 주요 변경 이력

### v1.2.0 (2025-12-05)

- **보고서 품질 개선**: 구체적 투자 시나리오 추가 (RE100, SBTi, CDP)
- **ThreadPool 안전 종료**: `ReportService.shutdown()` 구현
- **Scratch Space 자동 정리**: TTL 기반 백그라운드 정리

### v1.1.0 (2025-11-25)

- **Fork-Join 병렬 아키텍처**: Node 2∥3, Node BC∥5-8
- **ModelOps API 연동**: H, E, V, AAL 계산 외부화
- **추가 데이터 API**: Node 5 이후 재실행 메커니즘

---

## 기술 스택

- **Backend**: FastAPI 0.116.1, Python 3.11+, Uvicorn
- **AI**: LangChain 1.1.0, LangGraph 1.0.3, OpenAI GPT
- **Database**: PostgreSQL (PostGIS), Qdrant 1.7.0
- **Data**: pandas, numpy, netCDF4
- **Tools**: Pydantic, SQLAlchemy, httpx

---

## 추가 리소스

- **상세 문서**: [README.md](README.md)
- **API 문서**: http://localhost:8000/docs
- **개발 표준**: [docs/development_standards.md](docs/development_standards.md)
- **DB 가이드**: [docs/DB_operations.md](docs/DB_operations.md)
- **Spring Boot 연동**: [docs/springboot_integration.md](docs/springboot_integration.md)

---

## 라이선스

이 프로젝트는 SKAX의 비공개 프로젝트입니다.

---

**Built with FastAPI, LangChain, LangGraph, and OpenAI**
