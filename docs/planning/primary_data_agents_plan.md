# Primary Data Agents 구현 계획

**작성일:** 2025-12-15
**버전:** v1.0
**관련 문서:** [report_plan_v3.md](report_plan_v3.md), [node_0_implementation_plan.md](node_0_implementation_plan.md)

---

## 📌 Executive Summary

### 목표
Primary Data 에이전트 3개 구현 - 데이터 수집, 건물 특성 분석, 추가 데이터 분석

### 핵심 특징
| 항목 | 내용 |
|------|------|
| **에이전트 수** | 3개 (DataCollection, BuildingCharacteristics, AdditionalData) |
| **실행 방식** | Node 0에서 직접 호출 |
| **LLM 사용** | BuildingCharacteristics, AdditionalData만 사용 |
| **배치 처리** | 8개 사업장 동시 처리 |

---

## 🎯 에이전트별 역할

### 1. DataCollectionAgent
**상태:** ❌ 미구현 (필요성 재검토)
**역할:** 기후 데이터 및 전력 사용량 수집

**재검토 사유:**
- Node 0에서 이미 DB 직접 조회로 모든 데이터 로딩
- 중복 기능
- **결론**: 삭제 또는 Deprecated 처리

---

### 2. BuildingCharacteristicsAgent
**상태:** ⚠️ 부분 구현 (v05)
**역할:** LLM 기반 건물 특성 해석 및 가이드라인 생성

#### 입력
```python
bc_input = [
    {
        "site_id": int,
        "site_info": {
            "latitude": float,
            "longitude": float,
            "address": str,
            "name": str,
            "type": str  # 업종
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

#### 출력
```python
{
    site_id: {
        "meta": {
            "analyzed_at": str,
            "location": {"lat": float, "lon": float}
        },
        "building_data": {
            "estimated_structure": str,    # "철근콘크리트", "철골조" 등
            "estimated_age": str,          # "10-20년", "20-30년" 등
            "estimated_floors": int,       # 추정 층수
            "construction_quality": str    # "양호", "보통", "취약"
        },
        "structural_grade": str,           # "A", "B", "C", "D"
        "vulnerabilities": [str],          # 취약점 리스트
        "resilience": [str],               # 회복력 요소 리스트
        "agent_guidelines": str            # LLM 가이드라인 (보고서 생성용)
    }
}
```

#### 구현 상태
- [x] `analyze_batch()` 메서드 (v05)
- [x] `_convert_risk_results_to_scores()` 헬퍼
- [ ] LLM 프롬프트 업데이트 (보고서 가이드라인 생성용)
- [ ] 실제 Google Building API 연동 (Optional)

---

### 3. AdditionalDataAgent
**상태:** ✅ 구현 완료 (v02)
**역할:** Excel 파일 분석 및 사업장별 가이드라인 생성

#### 입력
```python
excel_file: str          # Excel 파일 경로
site_ids: List[int]      # 사업장 ID 리스트
```

#### 출력
```python
{
    "status": "completed" | "failed",
    "meta": {
        "analyzed_at": str,
        "row_count": int,
        "site_count": int
    },
    "site_specific_guidelines": {
        site_id: {
            "relevance_score": float,    # 0.0 ~ 1.0
            "key_insights": [str],        # 핵심 인사이트
            "guideline": str              # LLM 가이드라인
        }
    },
    "summary": str                        # 전체 요약
}
```

#### 구현 상태
- [x] `analyze()` 메서드 (v02)
- [x] Excel 파싱 로직
- [x] LLM 기반 가이드라인 생성
- [x] 사업장별 관련도 계산

---

## 📊 구현 단계

### Phase 1: DataCollectionAgent 처리
- [ ] 기존 코드 확인
- [ ] 삭제 또는 Deprecated 처리
- [ ] `__init__.py` 업데이트

### Phase 2: BuildingCharacteristicsAgent 수정
- [ ] 기존 `analyze_batch()` 확인
- [ ] LLM 프롬프트 업데이트
  - [ ] 보고서 생성용 가이드라인 추가
  - [ ] 구조적 취약성 분석 강화
- [ ] 에러 핸들링 강화
- [ ] 로깅 추가

### Phase 3: AdditionalDataAgent 확인
- [ ] 기존 구현 검증
- [ ] Node 0 연동 테스트
- [ ] 반환 구조 검증

### Phase 4: __init__.py 업데이트
- [ ] DataCollectionAgent 제거 (또는 Deprecated)
- [ ] Export 업데이트

### Phase 5: 통합 테스트
- [ ] Node 0 → BC → AD 플로우 테스트
- [ ] 8개 사업장 배치 처리 테스트

---

## 📁 파일 구조

```
ai_agent/agents/primary_data/
├── __init__.py                          # Export 정의
├── data_collection_agent.py             # ❌ 삭제 대상
├── building_characteristics_agent.py    # ⚠️ 수정 필요
└── additional_data_agent.py             # ✅ 구현 완료
```

---

## 🔧 BuildingCharacteristicsAgent 프롬프트 구조

### 시스템 프롬프트
```
당신은 건물 기후 리스크 분석 전문가입니다.

사업장의 위치 정보와 물리적 리스크 점수를 기반으로:
1. 건물 구조 특성 추정
2. 취약성 및 회복력 평가
3. TCFD 보고서 생성을 위한 가이드라인 제공

**출력 형식:**
- 건물 구조 추정 (구조, 연식, 층수, 품질)
- 구조적 등급 (A/B/C/D)
- 취약점 리스트
- 회복력 요소 리스트
- 보고서 생성 가이드라인 (3-5문장)
```

### 사용자 프롬프트 템플릿
```
사업장 정보:
- 이름: {name}
- 주소: {address}
- 좌표: ({lat}, {lon})
- 업종: {type}

물리적 리스크 점수 (상위 5개):
1. {risk_type_1}: AAL={aal_1}, Score={score_1}
2. {risk_type_2}: AAL={aal_2}, Score={score_2}
...

위 정보를 바탕으로 건물 특성을 분석하고 TCFD 보고서 작성 가이드라인을 제공해주세요.
```

---

## 🧪 테스트 시나리오

### 시나리오 1: BuildingCharacteristics 단독 테스트
```python
bc_agent = BuildingCharacteristicsAgent(llm_client=llm)
result = bc_agent.analyze_batch([
    {
        "site_id": 1,
        "site_info": {"name": "본사", "latitude": 37.5, "longitude": 127.0, "address": "서울시", "type": "data_center"},
        "risk_results": [
            {"risk_type": "extreme_heat", "final_aal": 0.025, "physical_risk_score": 75.0},
            {"risk_type": "typhoon", "final_aal": 0.018, "physical_risk_score": 60.0}
        ]
    }
])

assert 1 in result
assert "structural_grade" in result[1]
assert "agent_guidelines" in result[1]
```

### 시나리오 2: AdditionalData 단독 테스트
```python
ad_agent = AdditionalDataAgent(llm_client=llm)
result = ad_agent.analyze("data.xlsx", [1, 2, 3])

assert result["status"] == "completed"
assert "site_specific_guidelines" in result
```

### 시나리오 3: Node 0 통합 테스트
```python
node_0 = DataPreprocessingNode(llm_client=llm)
result = await node_0.execute(
    site_ids=[1, 2, 3],
    excel_file="data.xlsx",
    target_year="2050"
)

assert len(result["sites_data"]) == 3
assert result["sites_data"][0]["building_characteristics"] is not None
assert result["additional_data_guidelines"] is not None
```

---

## 📚 참고 문서

- **Node 0 구현**: [node_0_data_preprocessing.py](../../ai_agent/agents/tcfd_report/node_0_data_preprocessing.py)
- **ERD**: [erd.md](../for_better_understanding/erd.md)
- **TCFD Plan v3**: [report_plan_v3.md](report_plan_v3.md)

---

## 🎯 다음 단계

1. **Phase 1**: DataCollectionAgent 처리 (삭제)
2. **Phase 2**: BuildingCharacteristicsAgent LLM 프롬프트 업데이트
3. **Phase 3**: AdditionalDataAgent 검증
4. **Phase 4**: `__init__.py` 업데이트
5. **Phase 5**: 통합 테스트

**예상 소요 시간:** 1-2시간
