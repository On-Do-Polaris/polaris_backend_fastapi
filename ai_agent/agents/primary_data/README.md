# Primary Data Agents

**작성일:** 2025-12-15
**버전:** v03 (TCFD Report v2.1)
**위치:** `ai_agent/agents/primary_data/`

---

## 📌 개요

Primary Data Agents는 TCFD 보고서 생성 워크플로우의 **Node 0 (Data Preprocessing)**에서 사용되는 2개의 에이전트로 구성됩니다.

### 에이전트 구성

| 에이전트 | 버전 | 역할 | LLM 사용 |
|---------|------|------|----------|
| **BuildingCharacteristicsAgent** | v05 | 건물 특성 분석 및 가이드라인 생성 | ✅ |
| **AdditionalDataAgent** | v02 | Excel 추가 데이터 분석 및 가이드라인 생성 | ✅ |

### 삭제된 에이전트 (2025-12-15)

- **DataCollectionAgent**: Node 0에서 DB 직접 조회로 대체
- **VulnerabilityAnalysisAgent**: ModelOps로 H, E, V 계산 이관
- **SimpleVulnerabilityAnalyzer**: 미사용

---

## 🏗️ BuildingCharacteristicsAgent

### 역할
- **Google Building API** 또는 **건축물 대장 API**를 통해 건물 데이터 수집
- LLM 기반 건물 특성 해석 (구조, 노후도, 내진 설계 등)
- **보고서 생성 에이전트를 위한 가이드라인** 제공 (보고서 직접 생성 X)

### 입력

```python
sites_data = [
    {
        "site_id": int,
        "site_info": {
            "latitude": float,
            "longitude": float,
            "address": str,
            "name": str,
            "type": str  # 업종 (예: "data_center")
        },
        "risk_results": [
            {
                "risk_type": str,           # "extreme_heat", "typhoon", etc.
                "final_aal": float,         # SSP245 기준 최종 AAL
                "physical_risk_score": float # Hazard Score (0-100)
            }
        ]
    }
]
```

### 출력

```python
{
    site_id: {
        "meta": {
            "analyzed_at": str,            # ISO 8601 timestamp
            "location": {"lat": float, "lon": float},
            "data_source": str             # "Architectural HUB API (TCFD Enhanced)"
        },
        "building_data": {
            "estimated_structure": str,    # "철근콘크리트", "철골조"
            "estimated_age": str,          # "10-20년", "20-30년"
            "estimated_floors": int,       # 추정 층수
            "construction_quality": str    # "양호", "보통", "취약"
        },
        "structural_grade": str,           # "A", "B", "C", "D"
        "vulnerabilities": [
            {
                "category": str,           # "Structural", "Seismic", "Flood", etc.
                "factor": str,             # 취약성 요인
                "severity": str,           # "Very High", "High", "Medium", "Low"
                "description": str
            }
        ],
        "resilience": [
            {
                "category": str,
                "factor": str,
                "strength": str,           # "Very High", "High", "Medium"
                "description": str
            }
        ],
        "agent_guidelines": str            # LLM 가이드라인 (보고서 생성용)
    }
}
```

### 사용 예시

```python
from ai_agent.agents.primary_data import BuildingCharacteristicsAgent

# 초기화
bc_agent = BuildingCharacteristicsAgent(llm_client=llm_client)

# 배치 분석 (v05)
results = bc_agent.analyze_batch(sites_data)

# 결과 확인
for site_id, result in results.items():
    print(f"Site {site_id}: Grade {result['structural_grade']}")
    print(f"Vulnerabilities: {len(result['vulnerabilities'])}")
    print(f"Guidelines: {result['agent_guidelines'][:100]}...")
```

### LLM 프롬프트 구조

**시스템 역할:**
```
당신은 TCFD 보고서 생성 전문가이며,
보고서 생성 에이전트를 위한 가이드라인을 작성하는 역할을 맡고 있습니다.
```

**출력 목차:**
1. 건물 구조적 특징 요약
2. Strategy 섹션 작성 방향
3. P1~P5 영향 분석 강조 포인트
4. 대응 방안 작성 시 활용할 회복력 요인
5. 보고서 톤 & 스타일 권장사항

---

## 📊 AdditionalDataAgent

### 역할
- 사용자가 업로드한 **Excel 파일** 분석
- 사업장별 추가 정보 추출 및 관련도 계산
- **보고서 생성 에이전트를 위한 가이드라인** 제공

### 입력

```python
excel_file: str          # Excel 파일 경로
site_ids: List[int]      # 분석 대상 사업장 ID 리스트
```

**Excel 예상 구조:**
| site_id | site_name | column_1 | column_2 | ... |
|---------|-----------|----------|----------|-----|
| 1       | 본사       | 값1      | 값2      | ... |
| 2       | 공장       | 값3      | 값4      | ... |

### 출력

```python
{
    "meta": {
        "analyzed_at": str,
        "source_file": str,
        "site_count": int
    },
    "site_specific_guidelines": {
        site_id: {
            "site_id": int,
            "guideline": str,          # LLM 가이드라인
            "key_insights": List[str]  # 핵심 인사이트 리스트
        }
    },
    "summary": str,                    # 전체 요약
    "status": "completed" | "failed"
}
```

### 사용 예시

```python
from ai_agent.agents.primary_data import AdditionalDataAgent

# 초기화
ad_agent = AdditionalDataAgent(llm_client=llm_client)

# 분석
result = ad_agent.analyze("data.xlsx", site_ids=[1, 2, 3])

# 결과 확인
if result["status"] == "completed":
    for site_id, guideline in result["site_specific_guidelines"].items():
        print(f"Site {site_id}: {guideline['key_insights']}")
```

### LLM 프롬프트 구조

**시스템 역할:**
```
당신은 TCFD 보고서 생성 전문가이며,
사용자가 제공한 추가 데이터를 분석하여
보고서 생성 에이전트를 위한 가이드라인을 작성하는 역할을 맡고 있습니다.
```

**출력 목차:**
1. **데이터 요약** (3-5문장)
2. **보고서 활용 방안**
   - Node 2-A (Scenario Analysis): 시나리오 분석 활용법
   - Node 2-B (Impact Analysis): 영향 분석 강조 포인트
   - Node 2-C (Mitigation Strategies): 대응 전략 참고 정보
3. **주의사항**

---

## 🔄 Node 0 통합 플로우

```
Node 0: Data Preprocessing
│
├─ 1. DB 직접 조회 (application + datawarehouse)
│   └─ sites_data 로딩 (8개 사업장, 병렬)
│
├─ 2. BuildingCharacteristicsAgent 실행 ⭐
│   ├─ 입력: sites_data
│   └─ 출력: building_characteristics (사업장별)
│
└─ 3. AdditionalDataAgent 실행 (조건부) ⭐
    ├─ 입력: excel_file, site_ids
    └─ 출력: additional_data_guidelines
```

### Node 0 출력 예시

```python
{
    "sites_data": [
        {
            "site_id": 1,
            "site_info": {...},
            "risk_results": [...],
            "building_characteristics": {  # ← BC Agent 출력
                "structural_grade": "B",
                "vulnerabilities": [...],
                "agent_guidelines": "..."
            }
        }
    ],
    "additional_data_guidelines": {        # ← AD Agent 출력 (Optional)
        "site_specific_guidelines": {...},
        "summary": "..."
    },
    "loaded_at": "2025-12-15T14:30:00",
    "target_year": "2050"
}
```

---

## 📁 파일 구조

```
primary_data/
├── __init__.py                          # Export 정의 (v03)
├── building_characteristics_agent.py    # BC Agent (v05, 597줄)
├── additional_data_agent.py             # AD Agent (v02, 270줄)
└── README.md                            # 이 문서
```

---

## ⚙️ 설정

### 환경 변수

```bash
# LLM 클라이언트
OPENAI_API_KEY=your-openai-api-key

# Building Data Fetcher (BC Agent)
PUBLICDATA_API_KEY=your-publicdata-api-key  # 건축물 대장 API
VWORLD_API_KEY=your-vworld-api-key          # 역지오코딩 API
```

### LLM 클라이언트 초기화

```python
from ai_agent.utils.llm_client import LLMClient

llm_client = LLMClient(
    model="gpt-4o",
    temperature=0.3,
    max_tokens=2000
)
```

---

## 🧪 테스트

### BC Agent 단독 테스트

```python
from ai_agent.agents.primary_data import BuildingCharacteristicsAgent

bc_agent = BuildingCharacteristicsAgent(llm_client=llm)

test_data = [{
    "site_id": 1,
    "site_info": {
        "latitude": 37.5665,
        "longitude": 126.9780,
        "address": "서울특별시 중구 세종대로 110",
        "name": "서울시청",
        "type": "government"
    },
    "risk_results": [
        {"risk_type": "extreme_heat", "final_aal": 0.025, "physical_risk_score": 75.0},
        {"risk_type": "urban_flood", "final_aal": 0.018, "physical_risk_score": 60.0}
    ]
}]

result = bc_agent.analyze_batch(test_data)
assert 1 in result
assert result[1]["structural_grade"] in ["A", "B", "C", "D"]
```

### AD Agent 단독 테스트

```python
from ai_agent.agents.primary_data import AdditionalDataAgent

ad_agent = AdditionalDataAgent(llm_client=llm)

# 테스트용 Excel 파일 필요
result = ad_agent.analyze("test_data.xlsx", site_ids=[1, 2])
assert result["status"] == "completed"
assert len(result["site_specific_guidelines"]) == 2
```

---

## 📚 참고 문서

- **Node 0 구현**: [node_0_data_preprocessing.py](../tcfd_report/node_0_data_preprocessing.py)
- **ERD**: [erd.md](../../../docs/for_better_understanding/erd.md)
- **TCFD Plan v3**: [report_plan_v3.md](../../../docs/planning/report_plan_v3.md)
- **BuildingDataFetcher**: [building_data_fetcher.py](../../utils/building_data_fetcher.py)

---

## 🔧 개발 가이드

### 새로운 취약성 요인 추가 (BC Agent)

`building_characteristics_agent.py`의 `_identify_vulnerabilities()` 메서드에 로직 추가:

```python
# 예: 옥상 태양광 설비 취약성 추가
solar_panels = building_data.get('solar_panels', {})
if solar_panels.get('installed'):
    factors.append({
        "category": "Wind",
        "factor": "옥상 태양광 설비 보유",
        "severity": "Medium",
        "description": "강풍 시 태양광 패널 파손 위험"
    })
```

### Excel 구조 커스터마이징 (AD Agent)

`additional_data_agent.py`의 `_extract_site_data()` 메서드 수정:

```python
# 실제 Excel 컬럼명에 맞게 수정
if '사업장ID' in df.columns:
    site_df = df[df['사업장ID'] == site_id]
```

---

**마지막 업데이트:** 2025-12-15
