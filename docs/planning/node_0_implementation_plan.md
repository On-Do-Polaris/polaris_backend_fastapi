# Node 0: Data Preprocessing Implementation Plan

**작성일:** 2025-12-15
**버전:** v1.0
**관련 문서:** [report_plan_v3.md](report_plan_v3.md)

---

## 📌 Executive Summary

### 목표
Node 0 (Data Preprocessing)의 DB 직접 조회 로직 구현 - application DB와 datawarehouse DB에서 사업장 데이터 및 ModelOps 결과를 병렬로 로딩

### 핵심 특징
| 항목 | 내용 |
|------|------|
| **DB 접근** | 2개 DB (application, datawarehouse) |
| **병렬 처리** | 8개 사업장 동시 로딩 (~10초) |
| **조건부 실행** | AdditionalDataAgent (Excel 있을 때만) |
| **출력 형식** | sites_data (List[Dict]) |

---

## 🎯 Node 0 역할 정의

### 입력
```python
{
    "site_ids": List[int],           # 사업장 ID 리스트 (최대 8개)
    "excel_file": Optional[str],     # Excel 파일 경로 (Optional)
    "user_id": Optional[int],        # 사용자 ID
    "target_year": str               # 분석 목표 연도 (기본값: "2050")
}
```

### 출력
```python
{
    "sites_data": [
        {
            "site_id": int,
            "site_info": {
                "name": str,
                "latitude": float,
                "longitude": float,
                "address": str,
                "type": str  # 업종
            },
            "risk_results": [
                {
                    "risk_type": str,           # "extreme_heat", "typhoon", etc.
                    "final_aal": float,         # SSP245 기준 최종 AAL
                    "physical_risk_score": float # Hazard Score (0-100)
                }
            ],
            "modelops_raw": {...},              # 원본 ModelOps 데이터
            "building_characteristics": {}       # Placeholder (Node 1에서 채움)
        }
    ],
    "additional_data": Optional[Dict],          # Excel 데이터 (조건부)
    "agent_guidelines": Optional[Dict],         # LLM 가이드라인 (조건부)
    "loaded_at": str,                           # ISO 8601 timestamp
    "target_year": str
}
```

---

## 🗄️ 데이터베이스 스키마

### 1. application DB (SpringBoot)

#### sites 테이블
```sql
SELECT
    id,              -- UUID (PK)
    user_id,         -- UUID (FK → users)
    name,            -- VARCHAR(255)
    road_address,    -- VARCHAR(500)
    jibun_address,   -- VARCHAR(500)
    latitude,        -- DECIMAL(10,8)
    longitude,       -- DECIMAL(11,8)
    type             -- VARCHAR(100) (업종)
FROM sites
WHERE id = %s;
```

**쿼리 예시:**
```python
site_results = self.app_db.execute_query(
    "SELECT id, name, latitude, longitude, road_address, type FROM sites WHERE id = %s",
    (str(site_id),)
)
```

---

### 2. datawarehouse DB (ModelOps)

#### 필요한 테이블 (5개)
1. **hazard_results** - Hazard Score (H)
2. **exposure_results** - Exposure Score (E)
3. **vulnerability_results** - Vulnerability Score (V)
4. **probability_results** - P(H) 및 base AAL
5. **aal_scaled_results** - 최종 AAL (V 반영)

#### 통합 조회 메서드
```python
modelops_results = self.dw_db.fetch_all_modelops_results(
    site_id=str(site_id),
    latitude=latitude,
    longitude=longitude,
    target_year=target_year,
    risk_type=None  # 모든 리스크 타입 (9개)
)
```

**반환 구조:**
```python
{
    "hazard_results": [...],         # 9개 리스크별 Hazard Score
    "exposure_results": [...],       # 9개 리스크별 Exposure Score
    "vulnerability_results": [...],  # 9개 리스크별 Vulnerability Score
    "probability_results": [...],    # 9개 리스크별 P(H), base AAL
    "aal_scaled_results": [          # 9개 리스크별 최종 AAL
        {
            "site_id": "...",
            "risk_type": "extreme_heat",
            "target_year": "2050",
            "ssp126_final_aal": 0.012,
            "ssp245_final_aal": 0.025,
            "ssp370_final_aal": 0.038,
            "ssp585_final_aal": 0.051
        }
    ]
}
```

---

## 📊 구현 단계

### Phase 1: DB 연결 설정
- [x] DatabaseManager 확인 (이미 구현됨)
- [ ] application DB 연결 테스트
- [ ] datawarehouse DB 연결 테스트
- [ ] 환경 변수 설정 확인 (`APPLICATION_DATABASE_URL`, `DATABASE_URL`)

### Phase 2: 사업장 정보 조회
- [ ] `_load_single_site()` 구현
  - [ ] application DB에서 sites 조회
  - [ ] 좌표 변환 (latitude, longitude)
  - [ ] 에러 핸들링 (사업장 없음)

### Phase 3: ModelOps 결과 조회
- [ ] `fetch_all_modelops_results()` 호출
- [ ] `_format_risk_results()` 구현
  - [ ] AAL 데이터 매핑 (SSP245 기준)
  - [ ] Hazard Score 매핑 (SSP245 기준)
  - [ ] 9개 리스크별 포맷팅

### Phase 4: 병렬 처리
- [ ] `_load_sites_data_parallel()` 구현
  - [ ] asyncio.gather() 사용
  - [ ] 8개 사업장 동시 로딩
  - [ ] None 필터링 (실패한 사업장 제거)

### Phase 5: Excel 처리 (조건부)
- [ ] `_process_excel()` 구현
  - [ ] AdditionalDataAgent 초기화
  - [ ] agent.analyze() 호출
  - [ ] 결과 포맷팅

### Phase 6: 에러 핸들링
- [ ] DB 연결 실패 처리
- [ ] 사업장 조회 실패 처리
- [ ] ModelOps 데이터 없음 처리
- [ ] Excel 파싱 실패 처리

### Phase 7: 테스트
- [ ] 단위 테스트 작성
  - [ ] `_load_single_site()` 테스트
  - [ ] `_format_risk_results()` 테스트
- [ ] 통합 테스트
  - [ ] 8개 사업장 병렬 로딩 테스트
  - [ ] Excel 조건부 실행 테스트

---

## 🔧 환경 변수

### .env 파일
```bash
# application DB (SpringBoot)
APPLICATION_DATABASE_URL=postgresql://user:password@host:5432/application

# datawarehouse DB (FastAPI + ModelOps)
DATABASE_URL=postgresql://skala_dw_user:password@localhost:5433/skala_datawarehouse
```

---

## 📝 코드 구조

### 파일 위치
```
ai_agent/
├── agents/
│   └── tcfd_report/
│       └── node_0_data_preprocessing.py  # 구현 대상
├── utils/
│   └── database.py                        # DatabaseManager (이미 구현됨)
└── agents/
    └── primary_data/
        └── additional_data_agent.py       # AdditionalDataAgent (이미 구현됨)
```

### 클래스 구조
```python
class DataPreprocessingNode:
    def __init__(self, app_db_url, dw_db_url)
    async def execute(site_ids, excel_file, user_id, target_year) -> Dict
    async def _load_sites_data_parallel(site_ids, target_year) -> List[Dict]
    async def _load_single_site(site_id, target_year) -> Optional[Dict]
    def _format_risk_results(aal_results, hazard_results) -> List[Dict]
    async def _process_excel(excel_file, site_ids) -> Dict
```

---

## 🧪 테스트 시나리오

### 시나리오 1: 정상 케이스 (8개 사업장)
```python
result = await node_0.execute(
    site_ids=[1, 2, 3, 4, 5, 6, 7, 8],
    excel_file=None,
    user_id=100,
    target_year="2050"
)

assert len(result["sites_data"]) == 8
assert result["additional_data"] is None
```

### 시나리오 2: Excel 포함
```python
result = await node_0.execute(
    site_ids=[1, 2, 3],
    excel_file="/path/to/data.xlsx",
    user_id=100,
    target_year="2050"
)

assert result["additional_data"] is not None
assert result["agent_guidelines"] is not None
```

### 시나리오 3: 사업장 조회 실패
```python
result = await node_0.execute(
    site_ids=[999],  # 존재하지 않는 ID
    excel_file=None,
    user_id=100,
    target_year="2050"
)

assert len(result["sites_data"]) == 0  # 빈 리스트
```

---

## 📚 참고 문서

- **ERD**: [erd.md](../for_better_understanding/erd.md)
- **DatabaseManager**: [database.py](../../ai_agent/utils/database.py)
- **AdditionalDataAgent**: [additional_data_agent.py](../../ai_agent/agents/primary_data/additional_data_agent.py)
- **TCFD Plan v3**: [report_plan_v3.md](report_plan_v3.md)

---

## 🎯 다음 단계

1. **Phase 1**: 환경 변수 설정 및 DB 연결 테스트
2. **Phase 2-3**: 사업장 정보 + ModelOps 결과 조회 구현
3. **Phase 4**: 병렬 처리 구현
4. **Phase 5**: Excel 처리 추가
5. **Phase 6**: 에러 핸들링
6. **Phase 7**: 테스트 작성

**예상 소요 시간:** 2-3시간 (테스트 포함)
