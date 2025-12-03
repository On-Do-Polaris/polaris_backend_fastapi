# DB팀 요청 문서

**요청 일자**: 2025-12-03
**요청자**: AI Agent 개발팀
**우선순위**: 🔴 High

---

## 요약

ERD와 API 정합성 분석 결과, **2개의 신규 테이블** 생성이 필요합니다.

---

## 1. site_additional_data 테이블 생성 요청

### 목적
사용자가 제공하는 추가 데이터를 범용적으로 저장
- 전력 사용량 (IT전력, 냉방전력 등)
- 보험 가입률
- 건물 상세 정보 (연령, 구조, 내진설계 등)
- 자산 정보
- 사용자 자유 입력 텍스트
- 파일 업로드

### 특징
- **정해진 양식 없음**: 데이터 형태가 사용자마다 다름
- **다양한 형식 지원**: 텍스트, JSON, 파일
- **카테고리별 관리**: building, asset, power, insurance, custom 등으로 구분

### DDL

```sql
CREATE TABLE site_additional_data (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  site_id UUID NOT NULL REFERENCES sites(id) ON DELETE CASCADE,

  -- 데이터 분류
  data_category VARCHAR(50) NOT NULL,  -- 'building', 'asset', 'power', 'insurance', 'custom'

  -- 자유 형식 데이터
  raw_text TEXT,                       -- 사용자 입력 텍스트
  structured_data JSONB,               -- 구조화된 JSON 데이터

  -- 파일 업로드 지원
  file_name VARCHAR(255),
  file_s3_key VARCHAR(500),
  file_size BIGINT,
  file_mime_type VARCHAR(100),

  -- 메타데이터
  metadata JSONB,

  -- 추적 정보
  uploaded_by UUID REFERENCES users(id),
  uploaded_at TIMESTAMP DEFAULT now(),
  expires_at TIMESTAMP,                -- 임시 데이터 만료 (NULL = 영구)

  CONSTRAINT unique_site_category UNIQUE (site_id, data_category)
);

-- 인덱스
CREATE INDEX idx_site_additional_data_site_id ON site_additional_data(site_id);
CREATE INDEX idx_site_additional_data_category ON site_additional_data(data_category);
CREATE INDEX idx_site_additional_data_uploaded_at ON site_additional_data(uploaded_at);
```

### 사용 예시

#### 전력 사용량 저장
```json
{
  "site_id": "550e8400-e29b-41d4-a716-446655440000",
  "data_category": "power",
  "structured_data": {
    "it_power_kwh": 25000,
    "cooling_power_kwh": 8000,
    "total_power_kwh": 40000,
    "measurement_year": 2024,
    "measurement_month": 11
  }
}
```

#### 보험 정보 저장
```json
{
  "site_id": "550e8400-e29b-41d4-a716-446655440000",
  "data_category": "insurance",
  "structured_data": {
    "coverage_rate": 0.7,
    "insurer": "삼성화재",
    "policy_number": "POL-2024-12345"
  }
}
```

#### 건물 상세 정보 저장
```json
{
  "site_id": "550e8400-e29b-41d4-a716-446655440000",
  "data_category": "building",
  "structured_data": {
    "building_age": 25,
    "structure": "철근콘크리트",
    "seismic_design": true,
    "gross_floor_area": 5000.5,
    "floors_above": 10,
    "floors_below": 2
  }
}
```

#### 사용자 자유 입력
```json
{
  "site_id": "550e8400-e29b-41d4-a716-446655440000",
  "data_category": "custom",
  "raw_text": "건물 리모델링 2023년 완료, 태양광 패널 200kW 설치 예정",
  "metadata": {
    "source": "user_input",
    "timestamp": "2025-12-01"
  }
}
```

### API 연동
- `POST /api/sites/{site_id}/additional-data` → INSERT
- `GET /api/sites/{site_id}/additional-data` → SELECT by site_id
- `DELETE /api/sites/{site_id}/additional-data` → DELETE
- `POST /api/sites/{site_id}/additional-data/file` → S3 업로드 + INSERT

---

## 2. batch_jobs 테이블 생성 요청

### 목적
후보지 추천 배치 작업의 상태 추적 및 결과 저장
- 대량 격자점 분석 (10,000+ grids) 비동기 처리
- 진행률 실시간 추적
- 완료 후 결과 조회

### 특징
- **비동기 작업 관리**: 장시간 소요 작업의 상태 추적
- **진행률 추적**: 0-100% 진행률 표시
- **결과 캐싱**: 완료된 결과를 일정 기간 보관 (expires_at)

### DDL

```sql
CREATE TABLE batch_jobs (
  -- 기본 정보
  batch_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  job_type VARCHAR(50) NOT NULL,       -- 'site_recommendation', 'bulk_analysis', 'climate_simulation'

  -- 상태 관리
  status VARCHAR(20) NOT NULL,         -- 'queued', 'running', 'completed', 'failed', 'cancelled'
  progress INTEGER DEFAULT 0,          -- 진행률 (0-100)

  -- 작업 세부사항
  total_items INTEGER,                 -- 총 처리 항목 수
  completed_items INTEGER DEFAULT 0,   -- 완료 항목 수
  failed_items INTEGER DEFAULT 0,      -- 실패 항목 수

  -- 입력/출력
  input_params JSONB,                  -- 요청 파라미터 (재실행용)
  results JSONB,                       -- 배치 결과

  -- 에러 추적
  error_message TEXT,
  error_stack_trace TEXT,

  -- 성능 메트릭
  estimated_duration_minutes INTEGER,
  actual_duration_seconds INTEGER,

  -- 시간 정보
  created_at TIMESTAMP DEFAULT now(),
  started_at TIMESTAMP,
  completed_at TIMESTAMP,
  expires_at TIMESTAMP,                -- 결과 만료 (예: 7일 후 삭제)

  -- 소유자
  created_by UUID REFERENCES users(id),

  CONSTRAINT check_progress CHECK (progress >= 0 AND progress <= 100)
);

-- 인덱스
CREATE INDEX idx_batch_jobs_status ON batch_jobs(status);
CREATE INDEX idx_batch_jobs_created_at ON batch_jobs(created_at);
CREATE INDEX idx_batch_jobs_created_by ON batch_jobs(created_by);
CREATE INDEX idx_batch_jobs_job_type ON batch_jobs(job_type);
```

### 사용 예시

#### 배치 작업 시작
```json
{
  "batch_id": "550e8400-e29b-41d4-a716-446655440000",
  "job_type": "site_recommendation",
  "status": "queued",
  "progress": 0,
  "total_items": 10000,
  "input_params": {
    "scenario_id": 2,
    "start_year": 2025,
    "end_year": 2050,
    "top_n": 3
  },
  "estimated_duration_minutes": 30,
  "created_at": "2025-12-03T10:00:00Z"
}
```

#### 진행 중 상태
```json
{
  "batch_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "running",
  "progress": 65,
  "completed_items": 6500,
  "total_items": 10000,
  "started_at": "2025-12-03T10:30:00Z"
}
```

#### 완료 후 결과
```json
{
  "batch_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "progress": 100,
  "completed_items": 10000,
  "results": {
    "scenario_id": 2,
    "scenario_name": "SSP2-4.5",
    "total_grids_analyzed": 10000,
    "recommended_sites": [
      {
        "rank": 1,
        "grid_id": 12345,
        "latitude": 37.5665,
        "longitude": 126.978,
        "total_risk_score": 35.2,
        "aal_total": 1.25,
        "expected_loss": 625000000
      },
      {
        "rank": 2,
        "grid_id": 12346,
        "latitude": 37.57,
        "longitude": 126.98,
        "total_risk_score": 36.8,
        "aal_total": 1.35,
        "expected_loss": 675000000
      },
      {
        "rank": 3,
        "grid_id": 12347,
        "latitude": 37.573,
        "longitude": 126.985,
        "total_risk_score": 38.1,
        "aal_total": 1.42,
        "expected_loss": 710000000
      }
    ]
  },
  "completed_at": "2025-12-03T11:00:00Z",
  "actual_duration_seconds": 1800,
  "expires_at": "2025-12-10T11:00:00Z"
}
```

### API 연동
- `POST /api/recommendation/batch/start` → INSERT
- `GET /api/recommendation/batch/{batch_id}/progress` → SELECT (status, progress)
- `GET /api/recommendation/batch/{batch_id}/result` → SELECT (results)
- `DELETE /api/recommendation/batch/{batch_id}` → UPDATE status='cancelled' or DELETE

---

## 3. 보류/제외 사항

### 보류
- **재난 이력 테이블**: 처리 방안 미확정, 추후 논의 후 결정
- **워크플로우 결과 구조화**: 현재 JSONB로 충분, 결과 포맷 계속 변경 중

### 제외
- **인용 출처 테이블**: 리포트 내 임베딩으로 처리, 별도 테이블 불필요

---

## 4. 예상 일정

| 작업 | 담당 | 예상 소요 |
|------|------|----------|
| DB 테이블 생성 (2개) | DB팀 | **1일** |
| API 스키마 수정 | AI Agent팀 | 2일 |
| Workflow 수정 | AI Agent팀 | 3일 |
| 통합 테스트 | AI Agent팀 | 2일 |
| **총 예상 기간** | | **8일 (약 2주)** |

---

## 5. 참고 문서

- 상세 분석 계획: `C:\Users\Administrator\.claude\plans\dreamy-wondering-sunbeam.md`
- ERD 문서: `docs/erd.md`
- OpenAPI 스펙: `openapi.json`

---

## 문의

추가 질문이나 요구사항이 있으시면 AI Agent 개발팀으로 연락 부탁드립니다.

감사합니다.
