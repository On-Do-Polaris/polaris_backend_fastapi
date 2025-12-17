# TCFD 보고서 에이전트 빠른 참조

**작성일**: 2025-12-16
**용도**: 다음 대화 시작 시 핵심만 빠르게 파악

---

## ⚡ 핵심 요약 (30초 만에 이해하기)

### 무엇을?
- 물리적 리스크 데이터 → **TCFD 보고서 자동 생성**
- 입력: H, E, V, AAL, 건물 정보
- 출력: JSON (프론트엔드 전달)

### 어떻게?
- **7개 노드** 순차 실행 (Node 0 → Node 6)
- **병렬 LLM 분석**: Top 5 리스크 동시 처리 (~30초)
- **RAG 통합**: 기존 SK 보고서 스타일 학습

### 어디서?
- 코드: `ai_agent/agents/tcfd_report/`
- 출력: `test_output/report_json_for_front.json`

---

## 🗺️ 노드 구조 (한눈에 보기)

```
Node 0 → 데이터 로드 + BC/AD Agent
  ↓
Node 1 → RAG 템플릿 생성
  ↓
Node 2-A → 시나리오 분석 (4개 SSP)
  ↓
Node 2-B → 영향 분석 (Top 5 리스크, 병렬)  ⭐ 핵심
  ↓
Node 2-C → 대응 전략 (Top 5 리스크, 병렬)  ⭐ 핵심
  ↓
Node 3 → Strategy 섹션 통합 (Executive Summary + Heatmap + P1~P5)
  ↓
Node 4 → 검증 (Validator)
  ↓
Node 5 → 조립 (Composer)
  ↓
Node 6 → 저장 + JSON 변환
```

**소요 시간**: 총 2~3분

---

## 📦 프론트엔드 JSON 구조

```json
{
  "report_id": "tcfd_report_20251216_163321",
  "meta": {"title": "TCFD 보고서"},
  "sections": [
    {
      "section_id": "governance" | "strategy" | "risk_management" | "metrics_targets",
      "title": "섹션 제목",
      "blocks": [
        {"type": "text", "subheading": "소제목", "content": "Markdown 본문"},
        {"type": "table", "headers": [...], "items": [...], "legend": [...]}
      ]
    }
  ]
}
```

**핵심**: 모든 콘텐츠는 `blocks[]` 배열로 통합

---

## 🔥 Node 2-B (가장 중요!)

**역할**: Top 5 리스크 영향 분석 (병렬 처리)

**3가지 차원 분석**:
1. **재무적 영향**: AAL → 금액 환산
2. **운영적 영향**: 다운타임, 위험 시스템
3. **자산 영향**: 취약 자산, 손상 가능성

**프롬프트 핵심**:
```markdown
<ROLE>
You are a top-tier Financial Analyst...
</ROLE>

<CONTEXT>
- QUANTITATIVE_ANALYSIS_RESULT: HEV 평균, Risk Scores, AAL
- RISK_KNOWLEDGE_BASE: 리스크별 정량 데이터 컨텍스트
</CONTEXT>

<OUTPUT_REQUIREMENTS>
1. 재무적 영향: 총 예상 손실, AAL%
2. 운영적 영향: 예상 다운타임
3. 자산 영향: 취약 자산
</OUTPUT_REQUIREMENTS>
```

**출력**:
```json
{
  "top_5_risks": [{"risk_type": "river_flood", "total_aal": 18.2}],
  "impact_analyses": [
    {
      "risk_type": "river_flood",
      "financial_impact": {"estimated_exposure": "연간 910억원"},
      "operational_impact": {"estimated_downtime": "최대 72시간"},
      "asset_impact": {"vulnerable_assets": ["지하 주차장"]}
    }
  ]
}
```

---

## 🔥 Node 2-C (두 번째로 중요!)

**역할**: Top 5 리스크 대응 전략 생성 (병렬 처리)

**필수 포함 사항**:
- ✅ **구체적 투자 시나리오** (최소 2개)
- ✅ **AAL 감소 예측** (예: 18.2% → 7.5%)
- ✅ **국제 표준 프로그램** (RE100, SBTi, CDP)
- ✅ **ROI 계산** (투자 회수 기간)

**출력**:
```json
{
  "mitigation_strategies": [
    {
      "risk_type": "river_flood",
      "strategy_summary": "배수 시스템 개선...",
      "cost_benefit_analysis": "투자 5억원, AAL 18.2%→7.5%, ROI 11개월",
      "improvement_scenarios": {
        "scenario_1": {
          "investment": "2.5억원",
          "expected_improvement": "AAL 18.2% → 10.4%",
          "timeline": "18개월"
        }
      },
      "specific_programs": {
        "international_standards": ["RE100", "SBTi", "CDP"]
      }
    }
  ]
}
```

---

## 🔍 RAG 시스템

**2가지 모드**:

| 모드 | 모델 | 차원 | 용도 |
|------|------|------|------|
| `existing` | multilingual-e5-large | 1024 | 기존 SK 보고서 검색 ⭐ |
| `qdrant` | all-MiniLM-L6-v2 | 384 | 새 컬렉션 생성 |

**사용 예시**:
```python
from ai_agent.utils.rag_helpers import RAGEngine

rag = RAGEngine(source="existing")
results = rag.query(
    query="기후 거버넌스 체계",
    collection_names=["2025-SK-Inc.-Sustainability-Report-KOR-TCFD"],
    top_k=5
)
```

**사용 가능한 컬렉션**:
- `2025-SK-Inc.-Sustainability-Report-KOR-TCFD` (SK 보고서)
- `FINAL-2017-TCFD-Report` (TCFD 표준)
- `River-Flood-RAG`, `Typhon-RAG` 등 (리스크별 9개)

---

## 🏗️ BC/AD Agent

### Building Characteristics Agent (BC Agent)
- **역할**: ModelOps 점수(H, E, V)를 자연어로 해석
- **실행 시점**: Node 0 (병렬)
- **출력**: `agent_guidelines` (리스크별 영향 가이드)

### Additional Data Agent (AD Agent)
- **역할**: Excel 추가 데이터 처리
- **실행 시점**: Node 0 (optional)
- **출력**: `site_specific_guidelines` (사업장별 인사이트)

**Node 2-B에서 활용**:
```python
# BC/AD Agent 가이드라인을 프롬프트에 주입
prompt += f"<BUILDING_GUIDE>{building_data}</BUILDING_GUIDE>"
prompt += f"<ADDITIONAL_DATA>{additional_data}</ADDITIONAL_DATA>"
```

---

## 📊 주요 개념

### AAL (Average Annual Loss)
- **정의**: 연평균 자산 손실률 (%)
- **예시**: AAL 18.2% = 자산 500억원 → 연 91억원 손실

### H × E × V
- **Hazard**: 기후 재해 강도 (0~100)
- **Exposure**: 자산 노출 수준 (0~100)
- **Vulnerability**: 건물 취약성 (0~100)

### SSP 시나리오
- **SSP1-2.6**: 저탄소 (+1.5°C)
- **SSP2-4.5**: 중간 (+2.5°C) ⭐ 가장 현실적
- **SSP5-8.5**: 최악 (+4.5°C)

---

## 🚀 실행 방법

### 전체 플로우 실행
```bash
cd polaris_backend_fastapi
python -m ai_agent.agents.tcfd_report.test_full_flow_real
```

### 단일 노드 테스트
```python
from ai_agent.agents.tcfd_report.node_2b_impact_analysis_v2 import ImpactAnalysisNode

node = ImpactAnalysisNode(llm_client=llm_client)
result = await node.execute(sites_data=..., scenario_analysis=...)
```

---

## 🐛 문제 해결

### RAG 검색 실패
```bash
# Qdrant 컨테이너 확인
docker ps | grep qdrant

# 컬렉션 목록 확인
curl http://localhost:6333/collections
```

### LLM 토큰 제한 초과
- Node 2-B에서 Top 5 리스크만 필터링 (이미 적용됨)
- 사업장 수 제한 (최대 8개)

### 병렬 LLM 호출 실패
- Timeout 증가: `asyncio.timeout(300)`
- 실패한 태스크 재실행

---

## 📂 주요 파일 위치

```
ai_agent/agents/tcfd_report/
├── node_0_data_preprocessing.py      # DB 데이터 로드 + BC/AD Agent
├── node_1_template_loading_v2.py     # RAG 템플릿
├── node_2a_scenario_analysis_v2.py   # 시나리오 분석
├── node_2b_impact_analysis_v2.py     # 영향 분석 ⭐
├── node_2c_mitigation_strategies_v2.py # 대응 전략 ⭐
├── node_3_strategy_section_v2.py     # Strategy 섹션
├── node_4_validator_v2.py            # 검증
├── node_5_composer_v2.py             # 조립
├── node_6_finalizer_v2.py            # 저장 + JSON
├── state.py                          # LangGraph State
├── schemas.py                        # Pydantic 스키마
└── test_full_flow_real.py            # 전체 테스트
```

---

## 📚 더 자세한 내용

- **종합 가이드**: [report_agent_overview.md](./report_agent_overview.md)
- **시스템 전체**: [README_251216.md](../../README_251216.md)
- **프롬프트 분석**: [tcfd_prompt_analysis_2025-12-16.md](../progress/tcfd_prompt_analysis_2025-12-16.md)

---

**작성자**: Claude Code
**최종 업데이트**: 2025-12-16
**버전**: v2.0
