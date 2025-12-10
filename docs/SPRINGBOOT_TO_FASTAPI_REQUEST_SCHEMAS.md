# Spring Boot → FastAPI 요청 스키마 문서

**작성일**: 2025-12-09
**대상**: FastAPI 개발팀
**목적**: Spring Boot에서 FastAPI로 전송하는 모든 요청의 스키마 정의

---

## 목차

1. [인증 헤더](#인증-헤더)
2. [분석 시작 API](#1-분석-시작-api)
3. [시뮬레이션 API](#2-시뮬레이션-api)
4. [리포트 API](#3-리포트-api)
5. [추가 데이터 관리 API](#4-추가-데이터-관리-api)
6. [후보지 추천 배치 API](#5-후보지-추천-배치-api)
7. [조회 API (GET 요청)](#6-조회-api-get-요청)

---

## 인증 헤더

모든 요청에 다음 헤더가 포함됩니다:

```http
Content-Type: application/json
X-API-Key: {FASTAPI_API_KEY}
```

---

## 1. 분석 시작 API

### POST /api/sites/{siteId}/analysis/start

**Spring Boot 클라이언트**: `FastApiClient.startAnalysis()`

#### 요청 스키마

```json
{
  "site": {
    "id": "uuid",
    "name": "string",
    "address": "string",
    "latitude": "decimal (precision=10, scale=8)",
    "longitude": "decimal (precision=11, scale=8)",
    "industry": "string"
  },
  "hazardTypes": ["string"],
  "priority": "string",
  "options": {
    "includeFinancialImpact": "boolean",
    "includeVulnerability": "boolean",
    "includePastEvents": "boolean",
    "sspScenarios": ["string"]
  }
}
```

#### 필드 설명

| 필드 | 타입 | 필수 | 설명 | 예시값 |
|------|------|------|------|--------|
| `site.id` | UUID | ✅ | 사업장 고유 ID | `"550e8400-e29b-41d4-a716-446655440000"` |
| `site.name` | String | ✅ | 사업장 이름 | `"서울 본사"` |
| `site.address` | String | ✅ | 주소 (도로명 우선, 없으면 지번) | `"경기도 성남시 분당구 성남대로343번길 9"` |
| `site.latitude` | Decimal | ✅ | 위도 (최대 10자리, 소수점 8자리) | `37.36633726` |
| `site.longitude` | Decimal | ✅ | 경도 (최대 11자리, 소수점 8자리) | `127.10661717` |
| `site.industry` | String | ✅ | 산업 분류 | `"data_center"`, `"factory"`, `"office"` |
| `hazardTypes` | Array[String] | ✅ | 분석할 위험 유형 목록 | `["극심한 고온", "홍수", "태풍"]` |
| `priority` | String | ❌ | 작업 우선순위 | `"low"`, `"normal"`, `"high"` |
| `options.includeFinancialImpact` | Boolean | ❌ | 재무 영향 분석 포함 여부 | `true` |
| `options.includeVulnerability` | Boolean | ❌ | 취약성 분석 포함 여부 | `true` |
| `options.includePastEvents` | Boolean | ❌ | 과거 이벤트 포함 여부 | `true` |
| `options.sspScenarios` | Array[String] | ❌ | SSP 시나리오 목록 | `["SSP2-4.5", "SSP5-8.5"]` |

#### 예시 요청

```json
{
  "site": {
    "id": "0108c964-fd03-4dfd-82e3-caf5674f62bd",
    "name": "SK U 타워",
    "address": "경기도 성남시 분당구 성남대로343번길 9",
    "latitude": 37.36633726,
    "longitude": 127.10661717,
    "industry": "data_center"
  },
  "hazardTypes": [
    "극심한 고온",
    "홍수",
    "태풍",
    "가뭄",
    "산불",
    "해수면 상승"
  ],
  "priority": "high",
  "options": {
    "includeFinancialImpact": true,
    "includeVulnerability": true,
    "includePastEvents": true,
    "sspScenarios": ["SSP1-2.6", "SSP2-4.5", "SSP3-7.0", "SSP5-8.5"]
  }
}
```

---

## 2. 시뮬레이션 API

### 2.1. POST /api/simulation/relocation/compare

**Spring Boot 클라이언트**: `FastApiClient.compareRelocation()`
**서비스**: `SimulationService.compareRelocation()`

#### 요청 스키마

```json
{
  "currentSiteId": "uuid",
  "latitude": "decimal",
  "longitude": "decimal",
  "roadAddress": "string",
  "jibunAddress": "string"
}
```

#### 필드 설명

| 필드 | 타입 | 필수 | 설명 | 예시값 |
|------|------|------|------|--------|
| `currentSiteId` | UUID | ✅ | 현재 사업장 ID | `"550e8400-e29b-41d4-a716-446655440000"` |
| `latitude` | Decimal | ✅ | 이전 후보지 위도 | `37.5665` |
| `longitude` | Decimal | ✅ | 이전 후보지 경도 | `126.978` |
| `roadAddress` | String | ❌ | 도로명 주소 | `"서울특별시 중구 세종대로 110"` |
| `jibunAddress` | String | ❌ | 지번 주소 | `"서울특별시 중구 태평로1가 31"` |

#### 예시 요청

```json
{
  "currentSiteId": "0108c964-fd03-4dfd-82e3-caf5674f62bd",
  "latitude": 37.566535,
  "longitude": 126.9779692,
  "roadAddress": "서울특별시 종로구 세종대로 209",
  "jibunAddress": "서울특별시 종로구 세종로 1-68"
}
```

---

### 2.2. POST /api/simulation/climate

**Spring Boot 클라이언트**: `FastApiClient.runClimateSimulation()`
**서비스**: `SimulationService.runClimateSimulation()`

#### 요청 스키마

```json
{
  "scenario": "string",
  "hazardType": "string",
  "siteIds": ["uuid"],
  "startYear": "integer"
}
```

#### 필드 설명

| 필드 | 타입 | 필수 | 설명 | 예시값 |
|------|------|------|------|--------|
| `scenario` | String | ✅ | SSP 시나리오 | `"SSP1-2.6"`, `"SSP2-4.5"`, `"SSP3-7.0"`, `"SSP5-8.5"` |
| `hazardType` | String | ✅ | 위험 유형 (한글) | `"극심한 고온"` |
| `siteIds` | Array[UUID] | ✅ | 사업장 ID 목록 (사용자의 모든 사업장) | `["uuid1", "uuid2", ...]` |
| `startYear` | Integer | ✅ | 시작 연도 (항상 2020) | `2020` |

#### 예시 요청

```json
{
  "scenario": "SSP2-4.5",
  "hazardType": "극심한 고온",
  "siteIds": [
    "0108c964-fd03-4dfd-82e3-caf5674f62bd",
    "1234abcd-efgh-5678-ijkl-9012mnop3456"
  ],
  "startYear": 2020
}
```

#### 중요 사항

- **자동 사업장 선택**: Spring Boot는 현재 사용자의 **모든 사업장**을 자동으로 가져와 `siteIds`에 포함합니다
- **고정 연도 범위**: `startYear`는 항상 `2020`으로 고정되며, 종료 연도는 2100년입니다
- **SSP 시나리오**: 4가지만 지원 (SSP1-2.6, SSP2-4.5, SSP3-7.0, SSP5-8.5)

---

## 3. 리포트 API

### 3.1. POST /api/reports

**Spring Boot 클라이언트**: `FastApiClient.createReport()`
**서비스**: `ReportService.createReport()`

#### 요청 스키마

```json
{
  "userId": "uuid",
  "siteId": "uuid",
  "reportType": "string",
  "options": {
    "includeCharts": "boolean",
    "language": "string"
  }
}
```

#### 필드 설명

| 필드 | 타입 | 필수 | 설명 | 예시값 |
|------|------|------|------|--------|
| `userId` | UUID | ✅ | 사용자 ID | `"550e8400-e29b-41d4-a716-446655440000"` |
| `siteId` | UUID | ✅ | 사업장 ID | `"0108c964-fd03-4dfd-82e3-caf5674f62bd"` |
| `reportType` | String | ✅ | 리포트 타입 | `"comprehensive"`, `"summary"` |
| `options.includeCharts` | Boolean | ❌ | 차트 포함 여부 | `true` |
| `options.language` | String | ❌ | 언어 | `"ko"`, `"en"` |

---

## 4. 추가 데이터 관리 API

### 4.1. POST /api/sites/{siteId}/additional-data

**Spring Boot 클라이언트**: `FastApiClient.uploadAdditionalData()`
**서비스**: `AdditionalDataService.uploadAdditionalData()`

#### 요청 스키마

```json
{
  "dataCategory": "string",
  "buildingInfo": {
    "buildingStructure": "string",
    "buildYear": "integer",
    "floors": "integer",
    "basementFloors": "integer",
    "totalArea": "decimal"
  },
  "assetInfo": {
    "landValue": "decimal",
    "buildingValue": "decimal",
    "facilityValue": "decimal",
    "inventoryValue": "decimal"
  },
  "insuranceInfo": {
    "propertyInsurance": "decimal",
    "businessInterruptionInsurance": "decimal",
    "coverageStartDate": "string (ISO 8601)",
    "coverageEndDate": "string (ISO 8601)"
  },
  "powerInfo": {
    "backupGenerator": "boolean",
    "generatorCapacity": "decimal",
    "ups": "boolean",
    "upsCapacity": "decimal"
  }
}
```

#### 필드 설명

| 필드 | 타입 | 필수 | 설명 | 예시값 |
|------|------|------|------|--------|
| `dataCategory` | String | ✅ | 데이터 카테고리 | `"BUILDING"`, `"ASSET"`, `"INSURANCE"`, `"POWER"` |
| `buildingInfo.*` | Object | 조건부 | 건물 정보 (dataCategory=BUILDING) | - |
| `assetInfo.*` | Object | 조건부 | 자산 정보 (dataCategory=ASSET) | - |
| `insuranceInfo.*` | Object | 조건부 | 보험 정보 (dataCategory=INSURANCE) | - |
| `powerInfo.*` | Object | 조건부 | 전력 정보 (dataCategory=POWER) | - |

#### 예시 요청 (건물 정보)

```json
{
  "dataCategory": "BUILDING",
  "buildingInfo": {
    "buildingStructure": "철근 콘크리트",
    "buildYear": 2015,
    "floors": 20,
    "basementFloors": 3,
    "totalArea": 15000.50
  }
}
```

---

## 5. 후보지 추천 배치 API

### 5.1. POST /api/recommendation

**Spring Boot 클라이언트**: `FastApiClient.startRecommendationBatch()`
**서비스**: `RecommendationService.startBatch()`

#### 요청 스키마

```json
{
  "jobName": "string",
  "currentSiteId": "uuid",
  "searchArea": {
    "centerLat": "decimal",
    "centerLon": "decimal",
    "radiusKm": "decimal"
  },
  "criteria": {
    "maxRiskScore": "integer",
    "minRiskReduction": "decimal",
    "budget": "decimal"
  },
  "limit": "integer"
}
```

#### 필드 설명

| 필드 | 타입 | 필수 | 설명 | 예시값 |
|------|------|------|------|--------|
| `jobName` | String | ✅ | 배치 작업 이름 | `"서울 본사 이전 후보지 탐색"` |
| `currentSiteId` | UUID | ✅ | 현재 사업장 ID | `"0108c964-fd03-4dfd-82e3-caf5674f62bd"` |
| `searchArea.centerLat` | Decimal | ✅ | 검색 중심 위도 | `37.5665` |
| `searchArea.centerLon` | Decimal | ✅ | 검색 중심 경도 | `126.978` |
| `searchArea.radiusKm` | Decimal | ✅ | 검색 반경 (km) | `50.0` |
| `criteria.maxRiskScore` | Integer | ❌ | 최대 허용 리스크 점수 (0-100) | `70` |
| `criteria.minRiskReduction` | Decimal | ❌ | 최소 리스크 감소율 (0-1) | `0.3` |
| `criteria.budget` | Decimal | ❌ | 예산 | `10000000000.0` |
| `limit` | Integer | ❌ | 최대 후보지 개수 | `10` |

#### 예시 요청

```json
{
  "jobName": "SK U 타워 후보지 추천 (2025)",
  "currentSiteId": "0108c964-fd03-4dfd-82e3-caf5674f62bd",
  "searchArea": {
    "centerLat": 37.36633726,
    "centerLon": 127.10661717,
    "radiusKm": 30.0
  },
  "criteria": {
    "maxRiskScore": 60,
    "minRiskReduction": 0.25,
    "budget": 50000000000.0
  },
  "limit": 15
}
```

---

## 6. 조회 API (GET 요청)

다음 API들은 GET 요청이며, 쿼리 파라미터로 데이터를 전송합니다:

### 6.1. GET /api/v1/dashboard/summary

**쿼리 파라미터**:
```
userId={uuid}
```

**예시**:
```
GET /api/v1/dashboard/summary?userId=550e8400-e29b-41d4-a716-446655440000
```

---

### 6.2. GET /api/sites/{siteId}/analysis/status/{jobId}

**Path 파라미터**:
- `siteId`: 사업장 ID (UUID)
- `jobId`: 작업 ID (UUID)

**예시**:
```
GET /api/sites/0108c964-fd03-4dfd-82e3-caf5674f62bd/analysis/status/abc12345-def6-7890-ghij-klmnopqrstuv
```

---

### 6.3. GET /api/sites/{siteId}/analysis/physical-risk-scores

**Path 파라미터**:
- `siteId`: 사업장 ID (UUID)

**쿼리 파라미터** (옵션):
```
hazardType={string}
```

**예시**:
```
GET /api/sites/0108c964-fd03-4dfd-82e3-caf5674f62bd/analysis/physical-risk-scores?hazardType=극심한 고온
```

---

### 6.4. GET /api/sites/{siteId}/analysis/total

**Path 파라미터**:
- `siteId`: 사업장 ID (UUID)

**쿼리 파라미터** (필수):
```
hazardType={string}
```

**예시**:
```
GET /api/sites/0108c964-fd03-4dfd-82e3-caf5674f62bd/analysis/total?hazardType=홍수
```

---

### 6.5. GET /api/disaster-history

**쿼리 파라미터** (모두 옵션):
```
adminCode={string}
year={integer}
disasterType={string}
page={integer}
pageSize={integer}
```

**예시**:
```
GET /api/disaster-history?adminCode=11&year=2023&disasterType=홍수&page=1&pageSize=20
```

---

### 6.6. GET /api/sites/{siteId}/additional-data

**Path 파라미터**:
- `siteId`: 사업장 ID (UUID)

**쿼리 파라미터** (필수):
```
dataCategory={string}
```

**예시**:
```
GET /api/sites/0108c964-fd03-4dfd-82e3-caf5674f62bd/additional-data?dataCategory=BUILDING
```

---

### 6.7. GET /api/reports/web

**쿼리 파라미터** (필수):
```
userId={uuid}
```

**예시**:
```
GET /api/reports/web?userId=550e8400-e29b-41d4-a716-446655440000
```

---

### 6.8. GET /api/recommendation/{batchJobId}/progress

**Path 파라미터**:
- `batchJobId`: 배치 작업 ID (UUID)

**예시**:
```
GET /api/recommendation/abc12345-def6-7890-ghij-klmnopqrstuv/progress
```

---

## 데이터 타입 참고

### UUID 형식
```
"550e8400-e29b-41d4-a716-446655440000"
```

### Decimal (BigDecimal)
- **위도**: 최대 10자리, 소수점 이하 8자리 (`37.36633726`)
- **경도**: 최대 11자리, 소수점 이하 8자리 (`127.10661717`)
- **금액/면적**: 소수점 이하 2자리 권장

### ISO 8601 날짜 형식
```
"2024-01-15T09:30:00Z"
"2024-01-15"
```

---

## 위험 유형 (Hazard Types) 목록

Spring Boot에서 사용하는 위험 유형은 **한글**입니다:

| 영문 | 한글 | FastAPI 매핑 |
|------|------|--------------|
| `extreme_heat` | `극심한 고온` | ✅ |
| `typhoon` | `태풍` | ✅ |
| `flood` | `홍수` | ✅ |
| `drought` | `가뭄` | ✅ |
| `wildfire` | `산불` | ✅ |
| `sea_level_rise` | `해수면 상승` | ✅ |

**중요**: Spring Boot는 항상 **한글 이름**을 전송합니다. FastAPI 측에서 영문으로 변환이 필요한 경우 매핑 로직을 구현해야 합니다.

---

## SSP 시나리오 목록

Spring Boot에서 지원하는 SSP 시나리오:

1. `SSP1-2.6` (Sustainability)
2. `SSP2-4.5` (Middle of the Road)
3. `SSP3-7.0` (Regional Rivalry)
4. `SSP5-8.5` (Fossil-fueled Development)

**주의**: `SSP4-6.0`은 **지원하지 않습니다**.

---

## 산업 분류 (Industry Types)

현재 사용 중인 산업 분류 값:

- `data_center` (데이터센터)
- `factory` (공장)
- `office` (사무실)
- `warehouse` (창고)
- `retail` (소매점)

---

## 변경 이력

### 2025-12-09
- 초기 문서 작성
- 기후 시뮬레이션 API 업데이트 (siteIds 자동 선택, startYear 고정)
- SSP3-7.0 시나리오 추가

---

## 문의

FastAPI 팀에서 스키마 불일치나 422 에러가 발생하는 경우:

1. 이 문서의 스키마와 FastAPI 기대 스키마를 비교
2. 필드명 (camelCase vs snake_case) 확인
3. 필수 필드 누락 여부 확인
4. 데이터 타입 일치 여부 확인

Spring Boot 팀 연락처: [팀 연락처]
