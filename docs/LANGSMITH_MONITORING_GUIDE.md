# LangSmith 모니터링 가이드

**작성일**: 2025-11-25
**버전**: v1.0
**프로젝트**: SKAX Physical Risk Analysis System

---

## 📋 목차

1. [개요](#개요)
2. [LangSmith란?](#langsmith란)
3. [시스템 아키텍처](#시스템-아키텍처)
4. [환경 설정](#환경-설정)
5. [트레이싱 구조](#트레이싱-구조)
6. [모니터링 대시보드 사용법](#모니터링-대시보드-사용법)
7. [성능 분석](#성능-분석)
8. [디버깅 가이드](#디버깅-가이드)
9. [비용 최적화](#비용-최적화)
10. [트러블슈팅](#트러블슈팅)

---

## 개요

본 문서는 SKAX Physical Risk Analysis System에서 LangSmith를 활용한 모니터링 및 성능 분석 가이드를 제공합니다.

### 시스템 구성

- **총 워크플로우 노드**: 12개
- **총 Agent 수**: 25개
  - Physical Risk Score Sub Agents: 9개
  - AAL Analysis Sub Agents: 9개
  - Report Generation Agents: 7개
- **LLM 사용**: GPT-4 (OpenAI)
- **트레이싱 범위**: 전체 워크플로우 + 모든 LLM 호출

---

## LangSmith란?

LangSmith는 LangChain이 제공하는 LLM 애플리케이션 관찰성(Observability) 플랫폼입니다.

### 주요 기능

1. **트레이싱 (Tracing)**
   - 모든 LLM 호출 및 Agent 실행을 추적
   - 실행 시간, 입력/출력, 에러 로깅

2. **모니터링 (Monitoring)**
   - 실시간 성능 메트릭
   - 비용 추적 (토큰 사용량)
   - 성공률/실패율 통계

3. **디버깅 (Debugging)**
   - 프롬프트 확인 및 개선
   - 체인/워크플로우 시각화
   - 에러 근본 원인 분석

4. **평가 (Evaluation)**
   - LLM 응답 품질 평가
   - A/B 테스트 지원
   - 회귀 테스트

---

## 시스템 아키텍처

### LangSmith 통합 구조

```
┌─────────────────────────────────────────────────────────────┐
│                    LangSmith Cloud                          │
│  https://smith.langchain.com                                │
│  - 프로젝트: skax-physical-risk-dev                         │
│  - API Key: lsv2_pt_a8f35bdf8a6a49fbbb162eb289e0af7c_...   │
└─────────────────────────────────────────────────────────────┘
                              ▲
                              │ HTTPS (Tracing Data)
                              │
┌─────────────────────────────────────────────────────────────┐
│               SKAX Physical Risk Analyzer                   │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Main Orchestrator (@traceable)                     │   │
│  │  - analyze()                                        │   │
│  └─────────────────────────────────────────────────────┘   │
│                         │                                   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  LangGraph Workflow (12 Nodes)                      │   │
│  │                                                      │   │
│  │  Node 1: data_collection (@traceable)               │   │
│  │  Node 2: vulnerability_analysis (@traceable)        │   │
│  │  Node 3: aal_analysis (@traceable)                  │   │
│  │  Node 3a: physical_risk_score (@traceable)          │   │
│  │  Node 4: risk_integration (@traceable)              │   │
│  │  Node 5: report_template (@traceable)               │   │
│  │  Node 6: impact_analysis (@traceable)               │   │
│  │  Node 7: strategy_generation (@traceable)           │   │
│  │  Node 8: report_generation (@traceable)             │   │
│  │  Node 9: validation (@traceable)                    │   │
│  │  Node 9a: refiner (@traceable)                      │   │
│  │  Node 10: finalization (@traceable)                 │   │
│  └─────────────────────────────────────────────────────┘   │
│                         │                                   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  LLM Client (@traceable)                            │   │
│  │  - LangChain ChatOpenAI                             │   │
│  │  - invoke() / ainvoke()                             │   │
│  │  - generate_response_strategy()                     │   │
│  └─────────────────────────────────────────────────────┘   │
│                         │                                   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Report Generation Agents                           │   │
│  │  - ReportAnalysisAgent (@traceable)                 │   │
│  │  - ImpactAnalysisAgent                              │   │
│  │  - StrategyGenerationAgent                          │   │
│  │  - ReportComposerAgent                              │   │
│  │  - ValidationAgent                                  │   │
│  │  - RefinerAgent                                     │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

---

## 환경 설정

### 1. 환경 변수 설정 (.env)

```bash
# ===== LangSmith 트레이싱 설정 =====
LANGSMITH_ENABLED=true
LANGSMITH_API_KEY=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
LANGSMITH_PROJECT=skax-physical-risk-dev
LANGSMITH_ENDPOINT=https://api.smith.langchain.com
LANGSMITH_SAMPLING_RATE=1.0

# ===== OpenAI API 설정 =====
OPENAI_API_KEY=your_openai_api_key_here
```

### 2. 필수 패키지 설치

```bash
pip install langsmith
pip install langchain-openai
pip install langchain-core
```

### 3. 설정 확인

```python
from ai_agent.config.settings import Config

config = Config()
print(f"LangSmith Enabled: {config.LANGSMITH_CONFIG['enabled']}")
print(f"Project: {config.LANGSMITH_CONFIG['project_name']}")
print(f"Sampling Rate: {config.LANGSMITH_CONFIG['sampling_rate']}")
```

### 4. 환경별 설정

#### Development 환경
```python
from ai_agent.config.settings import DevelopmentConfig

config = DevelopmentConfig()
# LangSmith Project: skax-physical-risk-dev
# Sampling Rate: 100% (전체 추적)
```

#### Production 환경
```python
from ai_agent.config.settings import ProductionConfig

config = ProductionConfig()
# LangSmith Project: skax-physical-risk-prod
# Tags: ['production', 'monitoring']
```

#### Test 환경
```python
from ai_agent.config.settings import TestConfig

config = TestConfig()
# LangSmith Disabled (CI 성능 최적화)
```

---

## 트레이싱 구조

### 트레이스 계층 구조

```
skax_physical_risk_analyze (Root Trace)
│
├─ data_collection_node
│  └─ DataCollectionAgent.collect()
│
├─ vulnerability_analysis_node
│  └─ VulnerabilityAnalysisAgent.analyze()
│
├─ aal_analysis_node (병렬)
│  ├─ ExtremeHeatAALAgent.analyze_aal()
│  ├─ ExtremeColdAALAgent.analyze_aal()
│  ├─ WildfireAALAgent.analyze_aal()
│  ├─ DroughtAALAgent.analyze_aal()
│  ├─ WaterStressAALAgent.analyze_aal()
│  ├─ SeaLevelRiseAALAgent.analyze_aal()
│  ├─ RiverFloodAALAgent.analyze_aal()
│  ├─ UrbanFloodAALAgent.analyze_aal()
│  └─ TyphoonAALAgent.analyze_aal()
│
├─ physical_risk_score_node (병렬)
│  ├─ ExtremeHeatScoreAgent.calculate()
│  ├─ ExtremeColdScoreAgent.calculate()
│  ├─ WildfireScoreAgent.calculate()
│  ├─ DroughtScoreAgent.calculate()
│  ├─ WaterStressScoreAgent.calculate()
│  ├─ SeaLevelRiseScoreAgent.calculate()
│  ├─ RiverFloodScoreAgent.calculate()
│  ├─ UrbanFloodScoreAgent.calculate()
│  └─ TyphoonScoreAgent.calculate()
│
├─ risk_integration_node
│
├─ report_template_node
│  └─ report_analysis_agent_run_sync
│     ├─ RAGEngine.query()
│     └─ llm_invoke (LLM Call #1)
│
├─ impact_analysis_node
│  └─ ImpactAnalysisAgent.analyze_impact()
│     └─ llm_invoke (LLM Call #2)
│
├─ strategy_generation_node
│  └─ StrategyGenerationAgent.generate_strategy()
│     ├─ RAGEngine.query()
│     └─ llm_invoke (LLM Call #3)
│
├─ report_generation_node
│  └─ ReportComposerAgent.compose_report()
│     └─ llm_invoke (LLM Call #4)
│
├─ validation_node
│  └─ ValidationAgent.validate_report()
│
├─ refiner_node (조건부)
│  └─ RefinerAgent.refine_sync()
│     └─ llm_invoke (LLM Call #5)
│
└─ finalization_node
   └─ FinalizerNode.run()
```

### 트레이스 태그 체계

| 태그 | 용도 | 예시 |
|------|------|------|
| `workflow` | 워크플로우 노드 | `workflow`, `node` |
| `agent` | Agent 실행 | `agent`, `report-analysis` |
| `llm` | LLM 호출 | `llm`, `invoke`, `async` |
| `rag` | RAG 검색 | `rag`, `search` |
| `parallel` | 병렬 실행 | `parallel`, `aal`, `physical-risk` |

---

## 모니터링 대시보드 사용법

### 1. LangSmith 대시보드 접속

1. https://smith.langchain.com 접속
2. 로그인 (API 키로 인증)
3. 프로젝트 선택: `skax-physical-risk-dev`

### 2. 트레이스 목록 확인

**경로**: Projects > skax-physical-risk-dev > Traces

#### 주요 컬럼
- **Name**: 트레이스 이름 (`skax_physical_risk_analyze`)
- **Status**: 성공/실패 (✅ / ❌)
- **Latency**: 실행 시간 (초)
- **Tokens**: 토큰 사용량
- **Cost**: 예상 비용 (USD)
- **Start Time**: 실행 시작 시간

#### 필터링
```
# 태그로 필터링
tags: workflow
tags: llm

# 상태로 필터링
status: error
status: success

# 시간 범위
Last 1 hour
Last 24 hours
Custom range
```

### 3. 개별 트레이스 상세 분석

**트레이스 클릭 시 표시 정보**:

#### Overview 탭
- 전체 실행 시간
- 총 토큰 사용량
- 총 비용
- 성공/실패 상태

#### Timeline 탭
- 각 노드별 실행 순서 시각화
- Waterfall 차트 (실행 시간 비교)
- 병렬 실행 구간 표시

#### Inputs/Outputs 탭
```json
// Input 예시
{
  "target_location": {
    "latitude": 37.5665,
    "longitude": 126.9780,
    "name": "Seoul, South Korea"
  },
  "building_info": {
    "building_age": 25,
    "has_seismic_design": true,
    "fire_access": true
  }
}

// Output 예시
{
  "workflow_status": "completed",
  "physical_risk_scores": {...},
  "aal_analysis": {...},
  "generated_report": {...}
}
```

#### Metadata 탭
- Agent 정보
- 실행 환경
- 에러 스택 트레이스 (실패 시)

### 4. LLM 호출 상세 분석

**LLM Call 클릭 시 표시 정보**:

- **Prompt**: 전송된 프롬프트 전체
- **Completion**: LLM 응답
- **Model**: 사용된 모델 (gpt-4)
- **Tokens**:
  - Prompt Tokens: 입력 토큰
  - Completion Tokens: 출력 토큰
  - Total Tokens: 총합
- **Cost**: 예상 비용
- **Latency**: 응답 시간

---

## 성능 분석

### 1. 노드별 실행 시간 분석

#### Metrics 대시보드에서 확인

```
# 평균 실행 시간
Average Latency by Tag

workflow, node, data-collection: 15.2s
workflow, node, aal, parallel: 45.8s
workflow, node, physical-risk, parallel: 42.3s
workflow, node, impact, llm: 8.5s
workflow, node, strategy, llm, rag: 12.3s
```

#### 병목 구간 식별

**기준**:
- 🟢 정상: < 10초
- 🟡 주의: 10-30초
- 🔴 병목: > 30초

**일반적인 병목**:
1. AAL Analysis Node (9개 Sub Agent 실행)
2. Physical Risk Score Node (9개 Sub Agent 실행)
3. Strategy Generation Node (RAG + LLM)

### 2. LLM 토큰 사용량 분석

#### 프롬프트별 토큰 통계

| Agent | Avg Prompt Tokens | Avg Completion Tokens | Total Tokens |
|-------|-------------------|----------------------|--------------|
| ReportAnalysisAgent | 3,200 | 1,500 | 4,700 |
| ImpactAnalysisAgent | 2,800 | 1,200 | 4,000 |
| StrategyGenerationAgent | 3,500 | 1,800 | 5,300 |
| ReportComposerAgent | 4,000 | 2,000 | 6,000 |
| RefinerAgent | 3,000 | 1,500 | 4,500 |

#### 비용 추정 (GPT-4 기준)

```
Input: $0.03 / 1K tokens
Output: $0.06 / 1K tokens

1회 실행 예상 비용:
- Prompt: 16,500 tokens × $0.03 / 1K = $0.495
- Completion: 8,000 tokens × $0.06 / 1K = $0.480
- Total: $0.975
```

### 3. 성공률/실패율 모니터링

#### Analytics 대시보드

```
# 최근 24시간
Total Runs: 120
Successful: 112 (93.3%)
Failed: 8 (6.7%)

# 실패 원인 분류
- LLM Timeout: 4
- Validation Failed: 2
- Data Collection Error: 2
```

---

## 디버깅 가이드

### 1. 에러 추적

#### 에러 발생 시 확인 절차

1. **트레이스 목록에서 실패한 실행 필터링**
   ```
   status: error
   ```

2. **에러 트레이스 클릭 → Timeline 확인**
   - 어느 노드에서 실패했는지 확인
   - 빨간색으로 표시된 노드 식별

3. **실패 노드 클릭 → Metadata 탭**
   ```python
   Error: JSONDecodeError: Expecting value: line 1 column 1 (char 0)

   Stack Trace:
     File "report_analysis_agent_1.py", line 128, in run_sync
       profile = self._sanitize_llm_response(llm_resp_raw)
     File "report_analysis_agent_1.py", line 294, in _sanitize_llm_response
       llm_resp = json.loads(llm_resp)
   ```

4. **Inputs/Outputs 탭에서 프롬프트 확인**
   - 입력 데이터가 올바른지 검증
   - 프롬프트 구조 확인

### 2. 프롬프트 최적화

#### Before (비효율적)

```python
prompt = f"Analyze the report: {report_text}"
# Tokens: 15,000 (너무 많은 컨텍스트)
```

#### After (최적화)

```python
# 요약본만 전달
summary = report_text[:2000]
prompt = f"Analyze the report summary: {summary}"
# Tokens: 3,000 (80% 감소)
```

#### 프롬프트 개선 체크리스트

- [ ] 불필요한 컨텍스트 제거
- [ ] JSON 출력 형식 명시
- [ ] Few-shot 예시 추가
- [ ] 시스템 메시지 최적화

### 3. Retry 로직 분석

#### Validation Retry Loop 추적

```
validation_node (Attempt 1) → Failed
  └─ Issues: text_quality, structure_incomplete

refiner_node (Loop 1) → Completed
  └─ Applied 3 fixes

validation_node (Attempt 2) → Failed
  └─ Issues: citation_missing

refiner_node (Loop 2) → Completed
  └─ Applied 1 fix

validation_node (Attempt 3) → Passed ✅
```

---

## 비용 최적화

### 1. 샘플링 비율 조정

#### Development 환경
```bash
# .env
LANGSMITH_SAMPLING_RATE=1.0  # 100% 추적 (디버깅)
```

#### Production 환경
```bash
# .env
LANGSMITH_SAMPLING_RATE=0.1  # 10% 샘플링 (비용 절감)
```

#### 동적 샘플링

```python
# config/settings.py
import random

class ProductionConfig(Config):
    def __init__(self):
        super().__init__()

        # 에러 발생 시 100% 추적, 정상 시 10% 샘플링
        self.LANGSMITH_CONFIG['sampling_function'] = lambda: (
            1.0 if has_error else 0.1
        )
```

### 2. 모델 선택 최적화

#### 태스크별 모델 전략

| Agent | 현재 모델 | 권장 모델 | 비용 절감 |
|-------|----------|----------|----------|
| ReportAnalysisAgent | GPT-4 | GPT-4 | - |
| ImpactAnalysisAgent | GPT-4 | GPT-3.5-Turbo | 90% |
| StrategyGenerationAgent | GPT-4 | GPT-4 | - |
| ReportComposerAgent | GPT-4 | GPT-4 | - |
| ValidationAgent | GPT-4 | GPT-3.5-Turbo | 90% |
| RefinerAgent | GPT-4 | GPT-3.5-Turbo | 90% |

#### 구현 예시

```python
# llm_client.py
class LLMClient:
    def __init__(self, model: str = 'gpt-4', task_type: str = 'general'):
        # 태스크별 모델 선택
        if task_type in ['validation', 'refine', 'impact']:
            model = 'gpt-3.5-turbo'

        self.llm = ChatOpenAI(model=model, ...)
```

### 3. 캐싱 전략

#### RAG 결과 캐싱

```python
# utils/rag_engine.py
from functools import lru_cache

class RAGEngine:
    @lru_cache(maxsize=128)
    def query(self, query: str, top_k: int = 20):
        # 동일 쿼리는 캐시에서 반환
        return self._search(query, top_k)
```

#### LLM 응답 캐싱

```python
# LangChain 내장 캐싱
from langchain.cache import InMemoryCache
from langchain.globals import set_llm_cache

set_llm_cache(InMemoryCache())
```

---

## 트러블슈팅

### 문제 1: 트레이스가 LangSmith에 표시되지 않음

**증상**:
- 워크플로우는 정상 실행되나 LangSmith에 트레이스 없음

**원인**:
1. 환경 변수 미설정
2. API 키 오류
3. 네트워크 연결 문제

**해결 방법**:

```bash
# 1. 환경 변수 확인
echo $LANGCHAIN_TRACING_V2  # "true" 출력 확인
echo $LANGCHAIN_API_KEY     # API 키 확인
echo $LANGCHAIN_PROJECT     # 프로젝트명 확인

# 2. Python에서 확인
python -c "
import os
print('Tracing:', os.getenv('LANGCHAIN_TRACING_V2'))
print('Project:', os.getenv('LANGCHAIN_PROJECT'))
print('API Key:', os.getenv('LANGCHAIN_API_KEY')[:10] + '...')
"

# 3. 수동 트레이스 테스트
python
>>> from langsmith import Client
>>> client = Client()
>>> client.list_projects()  # 프로젝트 목록 확인
```

### 문제 2: LLM 호출이 너무 느림

**증상**:
- 평균 응답 시간 > 30초
- LangSmith에서 긴 Latency 확인

**원인**:
1. 프롬프트 크기 과다 (> 8K tokens)
2. 모델 과부하
3. Rate Limit 도달

**해결 방법**:

```python
# 1. 프롬프트 크기 확인
from tiktoken import encoding_for_model

enc = encoding_for_model("gpt-4")
tokens = enc.encode(prompt)
print(f"Prompt tokens: {len(tokens)}")

# 2. 프롬프트 압축
def compress_prompt(text: str, max_tokens: int = 4000):
    enc = encoding_for_model("gpt-4")
    tokens = enc.encode(text)
    if len(tokens) > max_tokens:
        compressed = enc.decode(tokens[:max_tokens])
        return compressed + "\n\n[... 내용 압축됨 ...]"
    return text

# 3. Timeout 설정
llm = ChatOpenAI(
    model="gpt-4",
    timeout=30,  # 30초 타임아웃
    request_timeout=30
)
```

### 문제 3: 비용이 예상보다 높음

**증상**:
- 월 비용 > $1,000
- LangSmith에서 높은 토큰 사용량

**분석**:

```python
# LangSmith Analytics에서 확인
# Metrics > Cost by Tag

# 비용 상위 Agent 식별
Top Cost Contributors:
1. ReportComposerAgent: $350/month
2. StrategyGenerationAgent: $280/month
3. ReportAnalysisAgent: $220/month
```

**최적화**:

```python
# 1. 불필요한 LLM 호출 제거
# Before
for risk in risks:
    llm_analysis = llm.invoke(f"Analyze {risk}")  # 9번 호출

# After
batch_prompt = f"Analyze all risks: {risks}"
llm_analysis = llm.invoke(batch_prompt)  # 1번 호출

# 2. 캐싱 활성화
from langchain.cache import RedisCache
set_llm_cache(RedisCache())

# 3. 샘플링 비율 낮추기
LANGSMITH_SAMPLING_RATE=0.1  # 10%만 추적
```

### 문제 4: Refiner Loop가 무한 반복

**증상**:
- Validation 계속 실패
- Refiner Loop 3회 초과

**디버깅**:

```python
# LangSmith에서 Refiner 트레이스 확인
refiner_node (Loop 1)
  Input: validation_result = {
    "issues_found": ["text_quality", "citation_missing"]
  }
  Output: applied_fixes = ["fixed_grammar", "added_citations"]

refiner_node (Loop 2)
  Input: validation_result = {
    "issues_found": ["text_quality"]  # 여전히 실패
  }
  # Refiner가 동일 문제를 해결하지 못함
```

**해결**:

```python
# agents/report_generation/refiner_agent_6.py

# Refiner 프롬프트 개선
def refine_sync(self, draft_markdown, validation_results):
    issues = validation_results.get("issues_found", [])

    # 이슈별 구체적 지시
    fix_instructions = {
        "text_quality": "문법 오류 수정 및 문장 다듬기",
        "citation_missing": "누락된 인용 추가 (최소 3개)",
        "structure_incomplete": "누락된 섹션 추가"
    }

    prompt = f"""
    다음 이슈를 반드시 해결하세요:
    {[fix_instructions[issue] for issue in issues]}

    Draft: {draft_markdown}
    """
```

---

## 부록

### A. LangSmith API 사용 예시

#### 프로그래밍 방식 트레이스 조회

```python
from langsmith import Client

client = Client()

# 최근 10개 트레이스 조회
runs = client.list_runs(
    project_name="skax-physical-risk-dev",
    limit=10
)

for run in runs:
    print(f"Run ID: {run.id}")
    print(f"Name: {run.name}")
    print(f"Status: {run.status}")
    print(f"Latency: {run.total_time}s")
    print(f"Tokens: {run.total_tokens}")
    print("---")
```

#### 커스텀 메트릭 기록

```python
from langsmith import traceable

@traceable(
    name="custom_analysis",
    metadata={"version": "1.0", "env": "production"}
)
def analyze_custom(data):
    # 분석 로직
    result = process(data)

    # 커스텀 메트릭 추가
    return {
        "result": result,
        "metrics": {
            "accuracy": 0.95,
            "confidence": 0.88
        }
    }
```

### B. 참고 자료

- [LangSmith 공식 문서](https://docs.smith.langchain.com/)
- [LangChain 트레이싱 가이드](https://python.langchain.com/docs/langsmith/tracing)
- [OpenAI 가격 정책](https://openai.com/pricing)
- [SKAX 시스템 아키텍처 문서](./ARCHITECTURE.md)

### C. 연락처

**기술 지원**:
- Email: support@skax.com
- Slack: #skax-physical-risk

**LangSmith 관련 문의**:
- LangChain Community: https://discord.gg/langchain

---

**문서 끝**
