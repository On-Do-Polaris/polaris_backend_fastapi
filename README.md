# SKAX Physical Risk Analyzer

SKAX 물리적 리스크 분석 에이전트 시스템

## 개요

이 시스템은 기후 변화에 따른 물리적 리스크를 분석하기 위한 에이전트 기반 프레임워크입니다.

## 주요 기능

### 1. 데이터 수집 에이전트 (Data Collection Agent)
- 기상 데이터 수집
- 지리 정보 수집
- SSP 시나리오 데이터 수집

### 2. SSP 시나리오 확률 계산 (SSP Probability Calculator)
4개의 SSP 시나리오에 대한 발생 확률 계산:
- SSP1-2.6: 지속 가능 발전 시나리오
- SSP2-4.5: 중간 시나리오
- SSP3-7.0: 지역 경쟁 시나리오
- SSP5-8.5: 화석 연료 기반 발전 시나리오

### 3. 8대 기후 리스크 분석 에이전트
각 리스크에 대해 H(Hazard) × E(Exposure) × V(Vulnerability) 계산:

1. **이상기온(고온)** - High Temperature Risk Agent
2. **이상기온(한파)** - Cold Wave Risk Agent (폭설 가중치 포함)
3. **해수면 상승** - Sea Level Rise Risk Agent (FROZEN)
4. **가뭄** - Drought Risk Agent
5. **산불** - Wildfire Risk Agent
6. **태풍** - Typhoon Risk Agent
7. **물부족** - Water Scarcity Risk Agent (FROZEN)
8. **하천 범람(홍수)** - Flood Risk Agent

### 4. 리스크 통합 계산 (Risk Integration Agent)
- 개별 리스크 통합
- 복합 리스크 분석
- 종합 리스크 스코어 산출

### 5. 리포트 생성 (Report Generation Agent)
- 분석 결과 요약
- 시각화
- PDF/HTML 리포트 출력

## 프로젝트 구조

```
backend_team/
├── main.py                          # 메인 오케스트레이터 (LangGraph 기반)
├── visualize_workflow.py            # 워크플로우 시각화 스크립트
├── agents/
│   ├── __init__.py
│   ├── data_collection_agent.py     # 데이터 수집
│   ├── ssp_probability_calculator.py # SSP 확률 계산
│   ├── base_climate_risk_agent.py   # 기후 리스크 베이스 클래스
│   ├── climate_risk_agents/
│   │   ├── __init__.py
│   │   ├── high_temperature_risk_agent.py
│   │   ├── cold_wave_risk_agent.py
│   │   ├── sea_level_rise_risk_agent.py
│   │   ├── drought_risk_agent.py
│   │   ├── wildfire_risk_agent.py
│   │   ├── typhoon_risk_agent.py
│   │   ├── water_scarcity_risk_agent.py
│   │   └── flood_risk_agent.py
│   ├── risk_integration_agent.py    # 리스크 통합
│   └── report_generation_agent.py   # 리포트 생성
├── workflow/                        # LangGraph 워크플로우
│   ├── __init__.py
│   ├── state.py                     # 상태 정의
│   ├── nodes.py                     # 노드 정의
│   └── graph.py                     # 그래프 정의 및 시각화
├── config/
│   ├── __init__.py
│   └── settings.py                  # 설정 파일
├── requirements.txt                 # Python 의존성
├── .env.example                     # 환경 변수 템플릿
├── workflow_diagram.mmd             # Mermaid 워크플로우 다이어그램
├── README.md                        # 프로젝트 문서
├── LANGGRAPH_GUIDE.md              # LangGraph 가이드
└── PROJECT_SUMMARY.md              # 프로젝트 요약
```

## 설치

```bash
pip install -r requirements.txt
```

## 사용 방법

```python
from main import SKAXPhysicalRiskAnalyzer
from config import Config

# 설정 로드
config = Config()

# 분석기 초기화 (LangGraph 워크플로우 자동 생성)
analyzer = SKAXPhysicalRiskAnalyzer(config)

# 워크플로우 구조 출력
analyzer.print_structure()

# 분석 대상 위치 설정
target_location = {
    'latitude': 37.5665,
    'longitude': 126.9780,
    'name': 'Seoul, South Korea'
}

# 분석 파라미터 설정
analysis_params = {
    'time_horizon': '2050',
    'analysis_period': '2025-2050'
}

# 분석 실행 (LangGraph로 병렬 처리)
results = analyzer.analyze(target_location, analysis_params)

# 워크플로우 시각화
analyzer.visualize("workflow_graph.png")
```

### 워크플로우 시각화만 하기

```bash
python visualize_workflow.py
```

이 명령어는 다음을 생성합니다:
- `workflow_diagram.mmd` - Mermaid 다이어그램 파일 (텍스트)
- `workflow_diagram.png` - PNG 이미지 파일 (시각화)
- 콘솔에 텍스트 기반 워크플로우 구조 출력

**시각화 보기:**
- PNG 이미지: `workflow_diagram.png` 파일을 직접 열기
- 온라인 편집: https://mermaid.live 에서 `workflow_diagram.mmd` 내용 붙여넣기

## 분석 흐름 (LangGraph 기반)

```
START
  ↓
[1. 데이터 수집]
  ↓
[2. SSP 확률 계산]
  ↓
[3. 8대 기후 리스크 분석] ← 병렬 처리
  ├─ 3.1 고온
  ├─ 3.2 한파 (폭설 포함)
  ├─ 3.3 해수면 상승 (FROZEN)
  ├─ 3.4 가뭄
  ├─ 3.5 산불
  ├─ 3.6 태풍
  ├─ 3.7 물부족 (FROZEN)
  └─ 3.8 홍수
  ↓
[4. 리스크 통합]
  ↓
[5. 리포트 생성]
  ↓
END
```

**주요 특징:**
- Step 3의 8개 리스크 분석은 LangGraph를 통해 병렬로 실행
- 각 노드는 독립적으로 실행되며 결과를 상태에 누적
- 모든 리스크 분석이 완료되면 자동으로 통합 단계로 진행

## 리스크 계산 방식

각 기후 리스크는 다음과 같이 계산됩니다:

```
Risk Score = Hazard × Exposure × Vulnerability

- Hazard: 기후 현상의 강도와 빈도 (SSP 시나리오 가중 평균)
- Exposure: 자산, 인구, 인프라의 노출 정도
- Vulnerability: 적응 능력과 민감도
```

## 환경 설정

환경 변수를 `.env` 파일에 설정:

```env
ENVIRONMENT=development
CLIMATE_API_URL=https://api.climate.example.com
CLIMATE_API_KEY=your_api_key
GEOGRAPHIC_API_URL=https://api.geo.example.com
GEOGRAPHIC_API_KEY=your_api_key
DEBUG=True
```

## 개발 상태

- ✅ 구조 설계 완료
- ✅ LangGraph 워크플로우 통합 완료
- ✅ 워크플로우 시각화 도구 완료
- ⚠️ 데이터 수집 로직 구현 필요
- ⚠️ 리스크 계산 알고리즘 구현 필요
- ⚠️ 시각화 모듈 구현 필요
- ❄️ 해수면 상승 리스크 (FROZEN)
- ❄️ 물부족 리스크 (FROZEN)

## TODO

- [ ] 데이터 소스 API 연동
- [ ] 리스크 계산 알고리즘 구현
- [ ] 시각화 모듈 개발
- [ ] 테스트 코드 작성
- [ ] 문서화 보완

## 라이선스

(라이선스 정보 추가)

## 기여

(기여 가이드 추가)
