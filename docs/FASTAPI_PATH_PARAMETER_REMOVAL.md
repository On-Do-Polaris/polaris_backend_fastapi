# FastAPI Path Parameter Removal - API 변경사항

## 변경 개요
모든 FastAPI 엔드포인트에서 경로 매개변수(Path Parameter)를 제거하고 요청 본문(Body) 또는 쿼리 매개변수(Query Parameter)로 변경했습니다.

**변경 날짜**: 2025-12-10
**변경 사유**: 엔드포인트 URL을 단순화하고 데이터를 요청 파라미터로 통일

---

## 1. Analysis API (`/api/analysis`)

### 변경 전 Prefix: `/api/sites`
### 변경 후 Prefix: `/api/analysis`

| 엔드포인트 (변경 전) | 엔드포인트 (변경 후) | 메서드 | 변경 내용 |
|---|---|---|---|
| `POST /api/sites/{site_id}/analysis/start` | `POST /api/analysis/start` | POST | `site_id`가 request body의 `site.id`로 이동 |
| `POST /api/sites/{site_id}/analysis/enhance` | `POST /api/analysis/enhance` | POST | `site_id`가 request body에 추가됨 (`siteId`) |
| `GET /api/sites/{site_id}/analysis/status/{job_id}` | `GET /api/analysis/status?siteId=xxx&jobId=xxx` | GET | 경로 변수 → 쿼리 파라미터 |
| `GET /api/sites/{site_id}/analysis/physical-risk-scores` | `GET /api/analysis/physical-risk-scores?siteId=xxx` | GET | 경로 변수 → 쿼리 파라미터 |
| `GET /api/sites/{site_id}/analysis/past-events` | `GET /api/analysis/past-events?siteId=xxx` | GET | 경로 변수 → 쿼리 파라미터 |
| `GET /api/sites/{site_id}/analysis/financial-impacts` | `GET /api/analysis/financial-impacts?siteId=xxx` | GET | 경로 변수 → 쿼리 파라미터 |
| `GET /api/sites/{site_id}/analysis/vulnerability` | `GET /api/analysis/vulnerability?siteId=xxx` | GET | 경로 변수 → 쿼리 파라미터 |
| `GET /api/sites/{site_id}/analysis/total` | `GET /api/analysis/total?siteId=xxx&hazardType=xxx` | GET | 경로 변수 → 쿼리 파라미터 |

#### 상세 변경 예시

**1) POST /api/analysis/start**
```json
// Request Body
{
  "site": {
    "id": "uuid",
    "name": "사업장명",
    "address": "주소",
    "latitude": 37.5665,
    "longitude": 126.9780,
    "industry": "제조업"
  },
  "hazardTypes": ["TYPHOON", "FLOOD"],
  "priority": "HIGH",
  "options": {...}
}
```

**2) POST /api/analysis/enhance**
```json
// Request Body (site_id 필드 추가됨)
{
  "siteId": "uuid",
  "jobId": "uuid",
  "additionalData": {...}
}
```

**3) GET /api/analysis/status**
```
GET /api/analysis/status?siteId={uuid}&jobId={uuid}
```

---

## 2. Additional Data API (`/api/additional-data`)

### 변경 전 Prefix: `/api/sites`
### 변경 후 Prefix: `/api/additional-data`

| 엔드포인트 (변경 전) | 엔드포인트 (변경 후) | 메서드 | 변경 내용 |
|---|---|---|---|
| `POST /api/sites/{site_id}/additional-data` | `POST /api/additional-data` | POST | `site_id`가 request body에 추가됨 (`siteId`) |
| `GET /api/sites/{site_id}/additional-data` | `GET /api/additional-data?siteId=xxx` | GET | 경로 변수 → 쿼리 파라미터 |
| `GET /api/sites/{site_id}/additional-data/all` | `GET /api/additional-data/all?siteId=xxx` | GET | 경로 변수 → 쿼리 파라미터 |
| `DELETE /api/sites/{site_id}/additional-data` | `DELETE /api/additional-data?siteId=xxx` | DELETE | 경로 변수 → 쿼리 파라미터 |
| `POST /api/sites/{site_id}/additional-data/file` | `POST /api/additional-data/file?siteId=xxx` | POST | 경로 변수 → 쿼리 파라미터 |

#### 상세 변경 예시

**1) POST /api/additional-data**
```json
// Request Body (siteId 필드 추가됨)
{
  "siteId": "uuid",
  "dataCategory": "BUILDING",
  "rawText": "...",
  "metadata": {...}
}
```

**2) GET /api/additional-data**
```
GET /api/additional-data?siteId={uuid}&dataCategory=BUILDING
```

**3) POST /api/additional-data/file**
```
POST /api/additional-data/file?siteId={uuid}&dataCategory=BUILDING
Form Data: file=...
```

---

## 3. Reports API (`/api/reports`)

| 엔드포인트 (변경 전) | 엔드포인트 (변경 후) | 메서드 | 변경 내용 |
|---|---|---|---|
| `GET /api/reports/web/{report_id}` | `GET /api/reports/web?reportId=xxx` | GET | 경로 변수 → 쿼리 파라미터 |
| `GET /api/reports/pdf/{report_id}` | `GET /api/reports/pdf?reportId=xxx` | GET | 경로 변수 → 쿼리 파라미터 |

#### 상세 변경 예시

**1) GET /api/reports/web**
```
GET /api/reports/web?reportId={report_id}
```

**2) GET /api/reports/pdf**
```
GET /api/reports/pdf?reportId={report_id}
```

---

## 4. Recommendation API (`/api/recommendation`)

| 엔드포인트 (변경 전) | 엔드포인트 (변경 후) | 메서드 | 변경 내용 |
|---|---|---|---|
| `GET /api/recommendation/batch/{batch_id}/progress` | `GET /api/recommendation/batch/progress?batchId=xxx` | GET | 경로 변수 → 쿼리 파라미터 |
| `GET /api/recommendation/batch/{batch_id}/result` | `GET /api/recommendation/batch/result?batchId=xxx` | GET | 경로 변수 → 쿼리 파라미터 |
| `DELETE /api/recommendation/batch/{batch_id}` | `DELETE /api/recommendation/batch?batchId=xxx` | DELETE | 경로 변수 → 쿼리 파라미터 |

#### 상세 변경 예시

**1) GET /api/recommendation/batch/progress**
```
GET /api/recommendation/batch/progress?batchId={uuid}
```

**2) GET /api/recommendation/batch/result**
```
GET /api/recommendation/batch/result?batchId={uuid}
```

**3) DELETE /api/recommendation/batch**
```
DELETE /api/recommendation/batch?batchId={uuid}
```

---

## 5. Disaster History API (`/api/disaster-history`)

| 엔드포인트 (변경 전) | 엔드포인트 (변경 후) | 메서드 | 변경 내용 |
|---|---|---|---|
| `GET /api/disaster-history/{disaster_id}` | `GET /api/disaster-history/detail?disasterId=xxx` | GET | 경로 변수 → 쿼리 파라미터 |

#### 상세 변경 예시

**1) GET /api/disaster-history/detail**
```
GET /api/disaster-history/detail?disasterId={uuid}
```

---

## 마이그레이션 체크리스트 (Spring Boot 측)

### ✅ 필수 수정 사항

1. **Analysis API 호출 변경**
   - [ ] `POST /api/sites/{siteId}/analysis/start` → `POST /api/analysis/start` (body에 site 정보 포함)
   - [ ] `POST /api/sites/{siteId}/analysis/enhance` → `POST /api/analysis/enhance` (body에 siteId 추가)
   - [ ] 모든 GET 엔드포인트의 경로 변수를 쿼리 파라미터로 변경

2. **Additional Data API 호출 변경**
   - [ ] Prefix `/api/sites` → `/api/additional-data`로 변경
   - [ ] POST 요청 body에 `siteId` 필드 추가
   - [ ] 모든 GET/DELETE 엔드포인트의 경로 변수를 쿼리 파라미터로 변경

3. **Reports API 호출 변경**
   - [ ] `/api/reports/web/{reportId}` → `/api/reports/web?reportId={reportId}`
   - [ ] `/api/reports/pdf/{reportId}` → `/api/reports/pdf?reportId={reportId}`

4. **Recommendation API 호출 변경**
   - [ ] 모든 `{batch_id}` 경로 변수를 `?batchId={batchId}` 쿼리 파라미터로 변경

5. **Disaster History API 호출 변경**
   - [ ] `/api/disaster-history/{disasterId}` → `/api/disaster-history/detail?disasterId={disasterId}`

### 📝 요청/응답 스키마 변경 없음
- 쿼리 파라미터와 요청 본문의 필드명은 기존과 동일 (camelCase 유지)
- 응답 스키마는 변경 없음

### ⚠️ 주의사항
- 모든 쿼리 파라미터는 camelCase로 전달해야 함 (예: `siteId`, `jobId`, `batchId`, `reportId`)
- API Key 인증은 변경 없음 (`X-API-Key` 헤더 사용)

---

## 테스트 방법

### 1. Health Check (변경 없음)
```bash
curl -X GET "http://localhost:8000/api/v1/health"
```

### 2. Analysis Start (변경됨)
```bash
# 변경 전
curl -X POST "http://localhost:8000/api/sites/{site_id}/analysis/start" \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{...}'

# 변경 후
curl -X POST "http://localhost:8000/api/analysis/start" \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "site": {
      "id": "uuid",
      "name": "사업장명",
      "address": "주소",
      "latitude": 37.5665,
      "longitude": 126.9780,
      "industry": "제조업"
    },
    "hazardTypes": ["TYPHOON"],
    "priority": "NORMAL"
  }'
```

### 3. Analysis Status (변경됨)
```bash
# 변경 전
curl -X GET "http://localhost:8000/api/sites/{site_id}/analysis/status/{job_id}" \
  -H "X-API-Key: your-api-key"

# 변경 후
curl -X GET "http://localhost:8000/api/analysis/status?siteId={site_id}&jobId={job_id}" \
  -H "X-API-Key: your-api-key"
```

---

## 롤백 계획
만약 문제가 발생할 경우:
1. Git에서 이전 커밋으로 롤백
2. 기존 경로 변수 방식으로 복원 가능
3. 변경사항은 모두 `src/routes/` 디렉토리 내에 국한됨

---

## 변경 파일 목록
- `src/routes/analysis.py`
- `src/routes/additional_data.py`
- `src/routes/reports.py`
- `src/routes/recommendation.py`
- `src/routes/disaster_history.py`
- `src/schemas/analysis.py` (EnhanceAnalysisRequest에 site_id 추가)
- `src/schemas/additional_data.py` (AdditionalDataUploadRequest에 site_id 추가)
