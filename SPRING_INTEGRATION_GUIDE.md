# Spring Boot ↔ FastAPI 통합 가이드

## 📋 개요

본 문서는 Spring Boot Gateway와 FastAPI AI Agent 서버 간의 통합을 위한 가이드입니다.

**시스템 아키텍처**:
```
Frontend ← HTTP → Spring Boot (Gateway) ← HTTP → FastAPI (AI Agent) ← HTTP → ModelOps
                                                          ↓
                                                    PostgreSQL
```

---

## ✅ 이미 구현된 API (Spring Boot API 스펙 준수)

### 1. 분석 (Analysis) API

#### 1.1 분석 시작
```
POST /api/sites/{siteId}/analysis/start
```

**Request**:
```json
{
  "latitude": 37.5665,
  "longitude": 126.9780,
  "industryType": "제조업"
}
```

**Response**:
```json
{
  "jobId": "uuid",
  "siteId": "uuid",
  "status": "queued",
  "currentNode": null
}
```

**FastAPI 구현**: ✅ 완료
- 파일: `src/routes/analysis.py:30`
- 파라미터: camelCase alias 지원 (`siteId`, `jobId`)

#### 1.2 분석 상태 조회
```
GET /api/sites/{siteId}/analysis/status/{jobId}
```

**Response**:
```json
{
  "jobId": "uuid",
  "siteId": "uuid",
  "status": "completed",
  "currentNode": "report_generation",
  "error": null
}
```

**FastAPI 구현**: ✅ 완료

#### 1.3 물리적 리스크 점수 조회
```
GET /api/sites/{siteId}/analysis/physical-risk-scores?hazardType={hazardType}
```

**Response**:
```json
{
  "scenarios": [
    {
      "scenario": "SSP2-4.5",
      "riskType": "폭염",
      "shortTerm": { "score": 65, "level": "높음" },
      "midTerm": { "score": 75, "level": "높음" },
      "longTerm": { "score": 85, "level": "매우 높음" }
    }
  ]
}
```

**FastAPI 구현**: ✅ 완료

#### 1.4 과거 재난 이력 조회
```
GET /api/sites/{siteId}/analysis/past-events
```

**FastAPI 구현**: ✅ 완료

#### 1.5 재무 영향 (AAL) 조회
```
GET /api/sites/{siteId}/analysis/financial-impacts
```

**FastAPI 구현**: ✅ 완료

#### 1.6 취약성 분석 조회
```
GET /api/sites/{siteId}/analysis/vulnerability
```

**FastAPI 구현**: ✅ 완료

#### 1.7 통합 분석 결과 조회
```
GET /api/sites/{siteId}/analysis/total?hazardType={hazardType}
```

**FastAPI 구현**: ✅ 완료

---

### 2. 시뮬레이션 (Simulation) API

#### 2.1 사업장 이전 시뮬레이션
```
POST /api/simulation/relocation/compare
```

**Request**:
```json
{
  "currentSiteId": "uuid",
  "candidateSites": [
    { "latitude": 37.5, "longitude": 127.0, "name": "후보지 1" }
  ]
}
```

**FastAPI 구현**: ✅ 완료
- 파일: `src/routes/simulation.py:15`

#### 2.2 기후 시뮬레이션
```
POST /api/simulation/climate
```

**Request**:
```json
{
  "siteId": "uuid",
  "targetYear": 2050,
  "scenarios": ["SSP2-4.5", "SSP5-8.5"]
}
```

**FastAPI 구현**: ✅ 완료

---

### 3. 리포트 (Reports) API

#### 3.1 리포트 생성
```
POST /api/reports
```

**Request**:
```json
{
  "siteId": "uuid",
  "reportType": "comprehensive",
  "format": "pdf"
}
```

**FastAPI 구현**: ✅ 완료
- 파일: `src/routes/reports.py:19`

#### 3.2 웹 리포트 조회
```
GET /api/reports/web/{reportId}
```

**FastAPI 구현**: ✅ 완료

#### 3.3 PDF 리포트 다운로드
```
GET /api/reports/pdf/{reportId}
```

**FastAPI 구현**: ✅ 완료

#### 3.4 리포트 삭제
```
DELETE /api/reports
```

**FastAPI 구현**: ✅ 완료

---

---

## ✅ 새로 추가된 API (Spring Boot API 스펙 준수)

### Dashboard API

#### 대시보드 요약 정보
```
GET /api/dashboard/summary
```

**Response**:
```json
{
  "mainClimateRisk": "폭염",
  "sites": [
    {
      "siteId": "uuid",
      "siteName": "서울 본사",
      "siteType": "본사",
      "location": "서울특별시 강남구",
      "totalRiskScore": 75
    },
    {
      "siteId": "uuid",
      "siteName": "부산 공장",
      "siteType": "공장",
      "location": "부산광역시 해운대구",
      "totalRiskScore": 82
    }
  ]
}
```

**FastAPI 구현**: ✅ 완료
- 파일: `src/routes/dashboard.py`
- 현재: Mock 데이터 반환
- TODO: 실제 분석 결과 DB 연동

**용도**: 전체 사업장의 통합 리스크 현황 및 주요 기후 리스크 파악

---

## ℹ️ Spring Boot가 직접 처리하는 API (FastAPI 불필요)

다음 API는 Spring Boot에서 자체 DB 또는 로직으로 처리하므로 FastAPI 구현이 필요하지 않습니다.

### 1. 메타데이터 API

#### 1.1 SSP 시나리오 목록
```
GET /api/meta/ssp-scenarios
```

**Response**:
```json
["SSP1-2.6", "SSP2-4.5", "SSP3-7.0", "SSP5-8.5"]
```

**구현**: Spring Boot에서 직접 처리 (DB 또는 하드코딩)

#### 1.2 업종 목록
```
GET /api/meta/industries
```

**Response**:
```json
[
  {
    "id": 1,
    "code": "manufacturing",
    "name": "제조업",
    "description": "제조업 설명"
  }
]
```

**구현**: Spring Boot에서 직접 처리 (Application DB의 `industries` 테이블)

#### 1.3 리스크 유형 목록
```
GET /api/meta/hazards
```

**Response**:
```json
[
  {
    "id": 1,
    "code": "extreme_heat",
    "name": "폭염",
    "nameEn": "Extreme Heat",
    "category": "TEMPERATURE"
  }
]
```

**구현**: Spring Boot에서 직접 처리 (Application DB의 `hazard_types` 테이블)

### 2. 헬스체크 API

#### Spring Boot 자체 헬스체크
```
GET /api/health
```

**Response**:
```json
{
  "status": "UP",
  "components": {
    "db": { "status": "UP" },
    "fastapi": { "status": "UP" }
  }
}
```

**구현**: Spring Boot Actuator 또는 자체 구현

---

## ⚠️ Spring Boot에서 추가 구현이 필요한 API

다음 API는 FastAPI에만 구현되어 있으며, Spring Boot Gateway에서 프록시 설정이 필요합니다.

### 1. FastAPI AI Agent 헬스체크 (선택적)

#### AI Agent 상태 확인
```
GET /api/v1/health
```

**Response**:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "agentStatus": "ready",
  "activeJobs": 0,
  "timestamp": "2025-12-08T12:00:00Z"
}
```

**용도**: FastAPI/AI Agent의 헬스체크 (Spring Boot `/api/health`와는 별개)
**구현 위치**: `src/routes/meta.py:22`

**Spring Boot 구현 필요**:
```java
@RestController
@RequestMapping("/api/v1")
public class HealthController {

    @GetMapping("/health")
    public ResponseEntity<HealthResponse> health() {
        // FastAPI /api/v1/health 프록시 (선택적)
        return restTemplate.getForEntity(
            fastApiUrl + "/api/v1/health",
            HealthResponse.class
        );
    }
}
```

**참고**: 이 엔드포인트는 선택적이며, Spring Boot의 `/api/health`와 별개로 FastAPI Agent의 상태를 확인하고 싶을 때만 사용합니다.

---

### 2. 추가 데이터 관리 API (필수)

사용자가 제공하는 추가 컨텍스트 데이터를 관리합니다.

#### 2.1 추가 데이터 업로드
```
POST /api/sites/{siteId}/additional-data
```

**Request**:
```json
{
  "rawText": "본 사업장은 2020년 건설되었으며...",
  "buildingInfo": {
    "buildingAge": 5,
    "buildingType": "철근콘크리트",
    "seismicDesign": true,
    "grossFloorArea": 5000
  },
  "assetInfo": {
    "totalAssetValue": 50000000000,
    "employeeCount": 200
  },
  "insurance": {
    "coverageRate": 0.8
  }
}
```

**Response**:
```json
{
  "siteId": "uuid",
  "dataId": "uuid",
  "status": "uploaded",
  "uploadedAt": "2025-12-08T12:00:00Z"
}
```

**구현 위치**: `src/routes/additional_data.py:16`

**Spring Boot 구현 필요**:
```java
@RestController
@RequestMapping("/api/sites")
public class AdditionalDataController {

    @PostMapping("/{siteId}/additional-data")
    public ResponseEntity<AdditionalDataUploadResponse> uploadAdditionalData(
        @PathVariable UUID siteId,
        @RequestBody AdditionalDataInput request
    ) {
        // FastAPI 프록시
        return restTemplate.postForEntity(
            fastApiUrl + "/api/sites/" + siteId + "/additional-data",
            request,
            AdditionalDataUploadResponse.class
        );
    }

    @GetMapping("/{siteId}/additional-data")
    public ResponseEntity<AdditionalDataGetResponse> getAdditionalData(
        @PathVariable UUID siteId
    ) {
        // FastAPI 프록시
        return restTemplate.getForEntity(
            fastApiUrl + "/api/sites/" + siteId + "/additional-data",
            AdditionalDataGetResponse.class
        );
    }

    @DeleteMapping("/{siteId}/additional-data")
    public ResponseEntity<Void> deleteAdditionalData(
        @PathVariable UUID siteId
    ) {
        // FastAPI 프록시
        restTemplate.delete(
            fastApiUrl + "/api/sites/" + siteId + "/additional-data"
        );
        return ResponseEntity.noContent().build();
    }
}
```

---

### 3. 재해 이력 API (Mock)

현재 FastAPI는 Mock 데이터를 반환합니다. 실제 DB 연동은 추후 구현 예정입니다.

#### 3.1 재해 이력 목록 조회
```
GET /api/disaster-history?siteId={siteId}&disasterType={type}&startDate={date}&endDate={date}
```

**Response**:
```json
{
  "items": [
    {
      "id": "uuid",
      "siteId": "uuid",
      "disasterType": "FLOOD",
      "occurredAt": "2023-07-15T00:00:00Z",
      "severity": "SEVERE",
      "damageAmount": 500000000,
      "casualties": 0,
      "description": "집중호우로 인한 침수"
    }
  ],
  "total": 10,
  "page": 1,
  "pageSize": 20
}
```

**구현 위치**: `src/routes/disaster_history.py:20`

**Spring Boot 구현 필요**:
```java
@RestController
@RequestMapping("/api/disaster-history")
public class DisasterHistoryController {

    @GetMapping
    public ResponseEntity<DisasterHistoryListResponse> getDisasterHistory(
        @RequestParam(required = false) UUID siteId,
        @RequestParam(required = false) String disasterType,
        @RequestParam(required = false) @DateTimeFormat(iso = ISO.DATE) LocalDate startDate,
        @RequestParam(required = false) @DateTimeFormat(iso = ISO.DATE) LocalDate endDate,
        @RequestParam(defaultValue = "1") int page,
        @RequestParam(defaultValue = "20") int pageSize
    ) {
        // FastAPI 프록시
        UriComponentsBuilder builder = UriComponentsBuilder
            .fromHttpUrl(fastApiUrl + "/api/disaster-history")
            .queryParamIfPresent("siteId", Optional.ofNullable(siteId))
            .queryParamIfPresent("disasterType", Optional.ofNullable(disasterType))
            .queryParamIfPresent("startDate", Optional.ofNullable(startDate))
            .queryParamIfPresent("endDate", Optional.ofNullable(endDate))
            .queryParam("page", page)
            .queryParam("pageSize", pageSize);

        return restTemplate.getForEntity(
            builder.toUriString(),
            DisasterHistoryListResponse.class
        );
    }
}
```

---

### 4. 후보지 추천 API (배치 작업)

대량의 후보지를 분석하여 최적 입지를 추천합니다.

#### 4.1 배치 작업 시작
```
POST /api/recommendation/batch/start
```

**Request**:
```json
{
  "candidateSites": [
    { "latitude": 37.5, "longitude": 127.0, "name": "후보지 1" },
    { "latitude": 35.1, "longitude": 129.0, "name": "후보지 2" }
  ],
  "criteria": {
    "hazardTypes": ["FLOOD", "TYPHOON"],
    "maxAcceptableRisk": 70
  }
}
```

**Response**:
```json
{
  "batchId": "uuid",
  "status": "queued",
  "totalSites": 2
}
```

**구현 위치**: `src/routes/recommendation.py:16`

#### 4.2 배치 진행 상황 조회
```
GET /api/recommendation/batch/{batchId}/progress
```

**Response**:
```json
{
  "batchId": "uuid",
  "status": "running",
  "progress": 50,
  "totalSites": 2,
  "completedSites": 1,
  "failedSites": 0
}
```

#### 4.3 배치 결과 조회
```
GET /api/recommendation/batch/{batchId}/result
```

**Response**:
```json
{
  "batchId": "uuid",
  "status": "completed",
  "recommendations": [
    {
      "siteId": "uuid",
      "name": "후보지 1",
      "totalRiskScore": 65,
      "rank": 1,
      "recommendation": "추천"
    }
  ]
}
```

**Spring Boot 구현 필요**:
```java
@RestController
@RequestMapping("/api/recommendation")
public class RecommendationController {

    @PostMapping("/batch/start")
    public ResponseEntity<SiteRecommendationBatchResponse> startBatch(
        @RequestBody SiteRecommendationBatchRequest request
    ) {
        return restTemplate.postForEntity(
            fastApiUrl + "/api/recommendation/batch/start",
            request,
            SiteRecommendationBatchResponse.class
        );
    }

    @GetMapping("/batch/{batchId}/progress")
    public ResponseEntity<BatchProgressResponse> getBatchProgress(
        @PathVariable UUID batchId
    ) {
        return restTemplate.getForEntity(
            fastApiUrl + "/api/recommendation/batch/" + batchId + "/progress",
            BatchProgressResponse.class
        );
    }

    @GetMapping("/batch/{batchId}/result")
    public ResponseEntity<SiteRecommendationResultResponse> getBatchResult(
        @PathVariable UUID batchId
    ) {
        return restTemplate.getForEntity(
            fastApiUrl + "/api/recommendation/batch/" + batchId + "/result",
            SiteRecommendationResultResponse.class
        );
    }
}
```

---

## 🔧 환경 설정

### FastAPI 환경 변수 (.env)

```bash
# ===== 필수 설정 =====
# API 키 (Spring Boot ↔ FastAPI 통신용)
API_KEY=your-secret-api-key

# ModelOps 연결
MODELOPS_BASE_URL=http://modelops-server:8001
MODELOPS_API_KEY=your-modelops-api-key

# 데이터베이스 (Datawarehouse)
DATABASE_URL=postgresql://user:pass@host:5432/skala_datawarehouse

# ===== 선택 설정 =====
# CORS 설정 (Spring Boot 도메인 허용)
CORS_ORIGINS=https://your-spring-domain.com,http://localhost:8080

# Mock 데이터 사용 여부 (개발 시에만 true)
USE_MOCK_DATA=false

# LangSmith 트레이싱 (선택)
LANGSMITH_ENABLED=true
LANGSMITH_API_KEY=your-langsmith-key
LANGSMITH_PROJECT=skax-physical-risk-prod
```

### Spring Boot 설정 (application.yml)

```yaml
external:
  fastapi:
    url: http://fastapi-server:8000
    api-key: ${FASTAPI_API_KEY}
    timeout:
      connect: 5000
      read: 300000  # 5분 (분석 작업은 오래 걸릴 수 있음)

spring:
  cloud:
    gateway:
      routes:
        # Analysis API
        - id: fastapi-analysis
          uri: ${external.fastapi.url}
          predicates:
            - Path=/api/sites/{siteId}/analysis/**
          filters:
            - AddRequestHeader=X-API-Key, ${external.fastapi.api-key}
            - StripPrefix=0

        # Simulation API
        - id: fastapi-simulation
          uri: ${external.fastapi.url}
          predicates:
            - Path=/api/simulation/**
          filters:
            - AddRequestHeader=X-API-Key, ${external.fastapi.api-key}

        # Reports API
        - id: fastapi-reports
          uri: ${external.fastapi.url}
          predicates:
            - Path=/api/reports/**
          filters:
            - AddRequestHeader=X-API-Key, ${external.fastapi.api-key}

        # Meta API (추가 필요)
        - id: fastapi-meta
          uri: ${external.fastapi.url}
          predicates:
            - Path=/api/v1/meta/**, /api/v1/health
          filters:
            - AddRequestHeader=X-API-Key, ${external.fastapi.api-key}

        # Additional Data API (추가 필요)
        - id: fastapi-additional-data
          uri: ${external.fastapi.url}
          predicates:
            - Path=/api/sites/{siteId}/additional-data/**
          filters:
            - AddRequestHeader=X-API-Key, ${external.fastapi.api-key}

        # Disaster History API (추가 필요)
        - id: fastapi-disaster-history
          uri: ${external.fastapi.url}
          predicates:
            - Path=/api/disaster-history/**
          filters:
            - AddRequestHeader=X-API-Key, ${external.fastapi.api-key}

        # Recommendation API (추가 필요)
        - id: fastapi-recommendation
          uri: ${external.fastapi.url}
          predicates:
            - Path=/api/recommendation/**
          filters:
            - AddRequestHeader=X-API-Key, ${external.fastapi.api-key}
```

---

## 🔐 인증

FastAPI는 **API Key 기반 인증**을 사용합니다.

### Spring Boot → FastAPI 요청 시

모든 요청에 다음 헤더 추가:
```
X-API-Key: {API_KEY}
```

### FastAPI 인증 미들웨어

```python
# src/core/auth.py
from fastapi import Security, HTTPException
from fastapi.security import APIKeyHeader

API_KEY_HEADER = APIKeyHeader(name="X-API-Key")

async def verify_api_key(api_key: str = Security(API_KEY_HEADER)):
    if api_key != settings.API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API Key")
    return api_key
```

---

## 📊 데이터 흐름

### 1. 분석 요청 흐름

```
1. Frontend → Spring Boot
   POST /api/sites/{siteId}/analysis/start

2. Spring Boot → FastAPI
   POST /api/sites/{siteId}/analysis/start
   Header: X-API-Key: {API_KEY}

3. FastAPI → ModelOps
   POST /api/v1/calculate/aal
   (E, V, AAL 계산 트리거)

4. ModelOps → DB
   결과 저장 (exposure_results, vulnerability_results, aal_scaled_results)

5. FastAPI → DB
   결과 조회

6. FastAPI → Spring Boot → Frontend
   분석 결과 반환
```

### 2. 폴링 방식 상태 확인

```
1. Frontend → Spring Boot (주기적 폴링)
   GET /api/sites/{siteId}/analysis/status/{jobId}

2. Spring Boot → FastAPI
   GET /api/sites/{siteId}/analysis/status/{jobId}

3. FastAPI 응답
   {
     "status": "running",  // queued → running → completed
     "progress": 50,
     "currentNode": "aal_analysis"
   }
```

---

## 🐛 에러 처리

### FastAPI 에러 응답 형식

```json
{
  "detail": "Error message",
  "code": "ERROR_CODE",
  "timestamp": "2025-12-08T12:00:00Z"
}
```

### 주요 에러 코드

| 코드 | HTTP Status | 설명 |
|------|-------------|------|
| `INVALID_API_KEY` | 403 | API 키 인증 실패 |
| `SITE_NOT_FOUND` | 404 | 사업장 정보 없음 |
| `JOB_NOT_FOUND` | 404 | 작업 ID 없음 |
| `ANALYSIS_FAILED` | 500 | 분석 처리 실패 |
| `MODELOPS_ERROR` | 502 | ModelOps 연동 오류 |
| `DATABASE_ERROR` | 500 | DB 조회 오류 |

---

## 📝 체크리스트

### Spring Boot 구현 필요 항목

- [ ] **Gateway 라우팅 설정**
  - [ ] Meta API (`/api/v1/meta/**`, `/api/v1/health`)
  - [ ] Additional Data API (`/api/sites/{siteId}/additional-data/**`)
  - [ ] Disaster History API (`/api/disaster-history/**`)
  - [ ] Recommendation API (`/api/recommendation/**`)

- [ ] **Controller 구현** (선택: 프록시 대신 직접 구현하는 경우)
  - [ ] `HealthController`
  - [ ] `AdditionalDataController`
  - [ ] `DisasterHistoryController`
  - [ ] `RecommendationController`

- [ ] **DTO 클래스 생성**
  - [ ] `HazardTypeInfo`
  - [ ] `HealthResponse`
  - [ ] `AdditionalDataInput`
  - [ ] `AdditionalDataUploadResponse`
  - [ ] `DisasterHistoryListResponse`
  - [ ] `SiteRecommendationBatchRequest`
  - [ ] `SiteRecommendationBatchResponse`
  - [ ] `BatchProgressResponse`
  - [ ] `SiteRecommendationResultResponse`

- [ ] **환경 변수 설정**
  - [ ] `FASTAPI_URL`
  - [ ] `FASTAPI_API_KEY`

- [ ] **API 문서 업데이트**
  - [ ] `api-docs.yaml`에 새로운 엔드포인트 추가

---

## 🚀 배포 시 주의사항

1. **Mock 데이터 비활성화**
   ```bash
   # FastAPI .env
   USE_MOCK_DATA=false
   ```

2. **CORS 설정**
   - Spring Boot 프로덕션 도메인을 `CORS_ORIGINS`에 추가

3. **타임아웃 설정**
   - 분석 작업은 최대 5분 소요 가능
   - Spring Boot Gateway 타임아웃: 300초 이상

4. **헬스체크**
   - Docker: `GET /api/v1/health`
   - K8s Liveness: `GET /api/v1/health`
   - K8s Readiness: `GET /api/v1/health`

---

## 📚 추가 참고 자료

- **DB 작업 가이드**: `DB_OPERATIONS.md`
- **ModelOps 연동**: `docs/modelops_handover/`
- **개발 표준**: `development_standard.md`
- **ERD**: `docs/Datawarehouse.dbml`
- **API 스키마**: FastAPI Swagger UI - `http://localhost:8000/docs`

---

## 🆘 문의

구현 중 문제가 발생하면 다음을 확인하세요:

1. **FastAPI 로그**: `docker logs fastapi-container`
2. **API 테스트**: `http://localhost:8000/docs` (Swagger UI)
3. **DB 연결**: `DATABASE_URL` 환경 변수 확인
4. **ModelOps 연결**: `MODELOPS_BASE_URL` 환경 변수 확인
