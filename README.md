# Backend Team - AI Agent Project

## 프로젝트 구조

```
backend_team/
├── ai_agent/                      # AI Agent 메인 패키지
│   ├── agents/                    # 에이전트 모듈
│   │   ├── data_processing/      # 데이터 처리 (2개)
│   │   │   ├── data_collection_agent.py
│   │   │   └── vulnerability_analysis_agent.py
│   │   ├── risk_analysis/        # 리스크 분석 (18개)
│   │   │   ├── aal_analysis/                # AAL 분석 (9개)
│   │   │   └── physical_risk_score/         # 물리적 리스크 점수 (9개)
│   │   └── report_generation/    # 보고서 생성 (5개)
│   │       ├── report_template_agent.py
│   │       ├── impact_analysis_agent.py
│   │       ├── strategy_generation_agent.py
│   │       ├── report_generation_agent.py
│   │       └── validation_agent.py
│   ├── config/                    # 설정 모듈
│   │   └── settings.py
│   ├── workflow/                  # LangGraph 워크플로우
│   │   ├── graph.py
│   │   ├── nodes.py
│   │   └── state.py
│   ├── utils/                     # 유틸리티
│   │   ├── llm_client.py
│   │   └── rag_engine.py
│   ├── main.py                    # 메인 분석기
│   ├── visualize_workflow.py
│   ├── requirements.txt
│   ├── README.md
│   └── development_standard.md
└── README.md                      # 이 파일
```

## 설치 및 실행

### 1. 가상 환경 설정 (선택사항)

```bash
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# 또는
.venv\Scripts\activate     # Windows
```

### 2. 의존성 설치

```bash
pip install -r ai_agent/requirements.txt
```

### 3. 환경 변수 설정

`.env` 파일을 생성하고 필요한 API 키를 설정합니다:

```bash
cp ai_agent/.env.example .env
```

`.env` 파일 예시:
```
OPENAI_API_KEY=your_api_key_here
CLIMATE_API_KEY=your_climate_api_key
DEBUG=False
ENVIRONMENT=production
```

### 4. 실행

#### 메인 분석 실행
```bash
python -m ai_agent.main
```

#### 워크플로우 시각화
```bash
python -m ai_agent.visualize_workflow
```

## 주요 기능

### SKAX 물리적 리스크 분석

이 시스템은 **Super Agent 계층 구조**를 사용하여 기후 변화에 따른 물리적 리스크를 분석합니다.

#### 워크플로우 (10개 노드)

1. **데이터 수집**: 기후 데이터, 위치 정보, 과거~현재 전력 사용량 수집
2. **취약성 분석**: 건물 연식, 내진 설계, 소방차 진입성 분석
3. **AAL 분석**: 9개 리스크별 연평균 재무 손실률 계산 (병렬 실행)
4. **물리적 리스크 점수**: H×E×V 기반 100점 스케일 점수 산출 (병렬 실행)
5. **리포트 템플릿**: RAG 기반 보고서 구조 생성
6. **영향 분석**: 전력 사용량 기반 리스크별 구체적 영향 분석
7. **대응 전략**: LLM + RAG 기반 맞춤형 전략 수립 (영향 분석 반영)
8. **리포트 생성**: 종합 보고서 작성
9. **검증**: 품질 검증 및 자동 재시도 (최대 3회)
10. **최종화**: 최종 보고서 확정

#### 에이전트 구조 (총 25개)

**1. 데이터 처리 (Data Processing - 2개):**
- 데이터 수집 (Data Collection)
- 취약성 분석 (Vulnerability Analysis)

**2. 리스크 분석 (Risk Analysis - 18개):**
- AAL 분석 Sub Agents (9개): 극심한 고온, 극심한 한파, 산불, 가뭄, 물 부족, 해안 홍수, 내륙 홍수, 도심 홍수, 열대성 태풍
- 물리적 리스크 점수 Sub Agents (9개): 위 9개 리스크 각각에 대한 100점 스케일 점수 산출

**3. 보고서 생성 (Report Generation - 5개):**
- 리포트 템플릿 생성 (Report Template)
- 영향 분석 (Impact Analysis) - 전력 사용량 기반
- 대응 전략 수립 (Strategy Generation)
- 보고서 작성 (Report Generation)
- 검증 (Validation)

## 개발 표준

자세한 개발 표준은 [ai_agent/development_standard.md](ai_agent/development_standard.md)를 참조하세요.

## 문서

- [AI Agent README](ai_agent/README.md): AI Agent 시스템 상세 설명
- [개발 표준](ai_agent/development_standard.md): 코딩 컨벤션 및 개발 가이드


## 라이선스

Copyright (C) 2025 SKALA On-Do Team. All rights reserved.
