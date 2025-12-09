# ERD 기반 API 수정 요약

## 개요
`docs/Datawarehouse.dbml` ERD 파일을 기준으로 FastAPI 코드와 스키마를 수정하였습니다.

**수정 일시**: 2025-12-09
**ERD 버전**: v04 (Last Modified: 2025-12-08)

---

## 주요 변경사항

### 1. Additional Data (추가 데이터) 스키마 수정

#### ERD 테이블: `site_additional_data`
```dbml
Table site_additional_data {
  id uuid [pk]
  site_id uuid [not null]
  data_category varchar(50) [not null]  // building/asset/power/insurance/custom
  raw_text text
  structured_data jsonb
  file_name varchar(255)
  file_s3_key varchar(500)
  file_size bigint
  file_mime_type varchar(100)
  metadata jsonb
  uploaded_by uuid
  uploaded_at timestamp
  expires_at timestamp

  indexes {
    site_id
    data_category
    (site_id, data_category) [unique]
  }
}
```

#### 변경 내용

**파일**: `src/schemas/additional_data.py`

- ✅ 추가: `DataCategory` Enum (building, asset, power, insurance, custom)
- ✅ 수정: `AdditionalDataUploadRequest`
  - `data_category` (필수): 데이터 카테고리
  - `structured_data` (선택): 정형화된 JSONB 데이터
  - `file_name`, `file_s3_key`, `file_size`, `file_mime_type` 필드 추가
  - `expires_at` 필드 추가
- ✅ 수정: `AdditionalDataUploadResponse`
  - `id`: 레코드 UUID 추가
  - `data_category` 추가
- ✅ 수정: `AdditionalDataGetResponse`
  - ERD의 모든 필드 포함

**파일**: `src/services/additional_data_service.py`

- ✅ 복합 키 사용: `(site_id, data_category)`를 unique key로 사용
- ✅ 메서드 추가:
  - `get_all_additional_data()`: 사업장의 모든 카테고리 데이터 조회
  - `upload_additional_data(uploaded_by)`: 업로드 사용자 ID 지원
- ✅ `get_additional_data_dict()`: 카테고리별 데이터를 통합하여 AI Agent에 전달

**파일**: `src/routes/additional_data.py`

- ✅ 새 엔드포인트: `GET /api/sites/{site_id}/additional-data/all`
  - 사업장의 모든 카테고리 데이터 조회
- ✅ 수정: `GET /api/sites/{site_id}/additional-data`
  - `dataCategory` 쿼리 파라미터 추가 (특정 카테고리만 조회)
- ✅ 수정: `DELETE /api/sites/{site_id}/additional-data`
  - `dataCategory` 쿼리 파라미터 추가 (특정 카테고리만 삭제)
- ✅ 수정: `POST /api/sites/{site_id}/additional-data/file`
  - `dataCategory` 쿼리 파라미터 추가 (필수)
  - 파일 메타데이터 자동 저장

---

### 2. Disaster History (재해 이력) 스키마 추가

#### ERD 테이블: `api_disaster_yearbook`
```dbml
Table api_disaster_yearbook {
  yearbook_id serial [pk]
  year integer [not null]
  admin_code varchar(10)  // NULL=전국 통계
  disaster_type varchar(50)
  typhoon_damage double  // 억원
  heavy_rain_damage double
  heavy_snow_damage double
  strong_wind_damage double
  wind_wave_damage double
  earthquake_damage double
  other_damage double
  total_damage double
  loss_amount_won bigint
  affected_buildings integer
  affected_population integer
  data_source varchar(100)
  major_disaster_type varchar(50)
  damage_level varchar(20)  // 경미/보통/심각/대재해
  cached_at timestamp
  api_response jsonb
}
```

#### 변경 내용

**파일**: `src/schemas/disaster_history.py`

- ✅ 추가: `DisasterYearbookRecord` 스키마
  - ERD `api_disaster_yearbook` 테이블의 모든 필드 포함
  - 재해별 피해액 (태풍, 호우, 대설, 강풍, 풍랑, 지진, 기타)
  - 총 피해액, 피해 건물 수, 피해 인구
- ✅ 추가: `DisasterType` Enum (태풍, 호우, 대설, 강풍, 풍랑, 지진, 기타)
- ✅ 수정: `DisasterSeverity` Enum
  - "재앙적" → "대재해" (ERD 기준)
- ✅ 기존: `DisasterHistoryRecord` (사용자 정의 이력) 유지

---

### 3. Batch Jobs (배치 작업) 스키마 추가

#### ERD 테이블: `batch_jobs`
```dbml
Table batch_jobs {
  batch_id uuid [pk]
  job_type varchar(50) [not null]  // site_recommendation/bulk_analysis/data_export
  status varchar(20) [not null]  // queued/running/completed/failed/cancelled
  progress integer [default: 0]  // 0-100
  total_items integer
  completed_items integer [default: 0]
  failed_items integer [default: 0]
  input_params jsonb
  results jsonb
  error_message text
  error_stack_trace text
  estimated_duration_minutes integer
  actual_duration_seconds integer
  created_at timestamp [default: `now()`]
  started_at timestamp
  completed_at timestamp
  expires_at timestamp
  created_by uuid
}
```

#### 변경 내용

**파일**: `src/schemas/recommendation.py`

- ✅ 추가: `JobType` Enum
  - `site_recommendation`: 후보지 추천
  - `bulk_analysis`: 대량 분석
  - `data_export`: 데이터 내보내기
- ✅ 수정: `BatchStatus` Enum
  - `PROCESSING` → `RUNNING` (ERD 기준)
  - `CANCELLED` 추가
- ✅ 추가: `BatchJob` 스키마
  - ERD `batch_jobs` 테이블의 모든 필드 포함
  - `progress`, `total_items`, `completed_items`, `failed_items`
  - `input_params`, `results` (JSONB)
  - `error_message`, `error_stack_trace`
  - `estimated_duration_minutes`, `actual_duration_seconds`
- ✅ 수정: `BatchProgressResponse`
  - ERD 필드에 맞춰 수정
  - `processed_grids` → `completed_items`
  - `total_grids` → `total_items`
  - `job_type`, `failed_items`, `actual_duration_seconds` 추가
- ✅ 수정: `SiteRecommendationResultResponse`
  - ERD 필드에 맞춰 수정
  - `total_grids_analyzed` → `total_items`
  - `completed_items`, `failed_items`, `actual_duration_seconds` 추가

---

## API 엔드포인트 변경사항

### Additional Data API

#### 기존 엔드포인트 (수정됨)

1. **POST** `/api/sites/{site_id}/additional-data`
   - **변경**: `dataCategory` 필드 필수 추가
   - **예시**:
     ```json
     {
       "dataCategory": "building",
       "rawText": "건물 특성 설명...",
       "structuredData": {
         "building_age": 25,
         "structure": "철근콘크리트"
       }
     }
     ```

2. **GET** `/api/sites/{site_id}/additional-data?dataCategory={category}`
   - **변경**: `dataCategory` 쿼리 파라미터 추가 (선택)
   - **미지정 시**: 전체 카테고리 중 첫 번째 반환

3. **DELETE** `/api/sites/{site_id}/additional-data?dataCategory={category}`
   - **변경**: `dataCategory` 쿼리 파라미터 추가 (선택)
   - **미지정 시**: 사업장의 모든 카테고리 데이터 삭제

4. **POST** `/api/sites/{site_id}/additional-data/file?dataCategory={category}`
   - **변경**: `dataCategory` 쿼리 파라미터 필수 추가

#### 신규 엔드포인트

5. **GET** `/api/sites/{site_id}/additional-data/all`
   - **설명**: 사업장의 모든 카테고리 데이터 조회
   - **응답**: `List[AdditionalDataGetResponse]`

---

## 데이터 카테고리 설명

| 카테고리 | 설명 | 예시 데이터 |
|---------|------|------------|
| `building` | 건물 정보 | 구조, 연식, 층수, 내진설계 여부 등 |
| `asset` | 자산 정보 | 자산 가치, 면적, 직원 수 등 |
| `power` | 전력 사용량 | IT 전력, 냉각 전력, 총 전력 등 |
| `insurance` | 보험 정보 | 보험 보전율, 보험 상품 등 |
| `custom` | 기타 사용자 정의 | 자유 형식 데이터 |

---

## 호환성 및 마이그레이션

### Backwards Compatibility

- ✅ 기존 API 호출은 대부분 호환됨
- ⚠️ `POST /api/sites/{site_id}/additional-data`는 `dataCategory` 필드 필수
- ✅ `GET`, `DELETE`는 `dataCategory` 미지정 시 기존 동작 유지

### 마이그레이션 가이드

기존 코드에서 새 API로 마이그레이션:

```python
# 기존 (deprecated)
await service.upload_additional_data(
    site_id,
    AdditionalDataUploadRequest(
        rawText="건물 정보...",
        metadata={}
    )
)

# 새 API (권장)
await service.upload_additional_data(
    site_id,
    AdditionalDataUploadRequest(
        dataCategory=DataCategory.BUILDING,
        rawText="건물 정보...",
        structuredData={
            "building_age": 25,
            "structure": "철근콘크리트"
        }
    )
)
```

---

## 테스트 필요 항목

### 1. Additional Data API
- [ ] 카테고리별 데이터 업로드
- [ ] 동일 카테고리 중복 업로드 시 덮어쓰기
- [ ] 특정 카테고리 조회
- [ ] 모든 카테고리 조회
- [ ] 특정 카테고리 삭제
- [ ] 파일 업로드 (카테고리 지정)

### 2. Disaster History API
- [ ] 재해연보 데이터 조회 (연도별, 지역별)
- [ ] 재해 유형별 필터링

### 3. Batch Jobs API
- [ ] 배치 작업 생성
- [ ] 진행 상태 조회
- [ ] 결과 조회
- [ ] 에러 처리

---

## 다음 단계

1. **데이터베이스 마이그레이션**
   - ERD 기반 실제 PostgreSQL 테이블 생성
   - SQLAlchemy ORM 모델 작성

2. **서비스 레이어 구현**
   - 메모리 캐시 → PostgreSQL 연동
   - JSONB 필드 활용 로직

3. **통합 테스트**
   - API 엔드포인트 테스트
   - ERD 제약조건 검증

4. **문서화**
   - Swagger/OpenAPI 문서 업데이트
   - 사용자 가이드 작성

---

## 참고 자료

- ERD 파일: [docs/Datawarehouse.dbml](../Datawarehouse.dbml)
- Database: `skala_datawarehouse` (Port: 5434)
- Total Tables: 44
