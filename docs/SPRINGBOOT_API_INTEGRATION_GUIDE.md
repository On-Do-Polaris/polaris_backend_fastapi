# FastAPI ↔ Spring Boot API 연동 가이드

**작성일**: 2025-11-25
**버전**: v1.0
**FastAPI 버전**: 0.116.1
**Spring Boot 호환**: 필수 요구사항 포함

---

## 📋 목차

1. [시스템 개요](#시스템-개요)
2. [API 기본 정보](#api-기본-정보)
3. [인증 방식](#인증-방식)
4. [전체 API 목록](#전체-api-목록)
5. [API 상세 스펙](#api-상세-스펙)
6. [테스트 가이드](#테스트-가이드)
7. [Spring Boot 요구사항](#spring-boot-요구사항)
8. [에러 처리](#에러-처리)
9. [연동 예제 코드](#연동-예제-코드)

---

## 시스템 개요

### 아키텍처

```
┌─────────────────┐         HTTP/REST API        ┌──────────────────┐
│  Spring Boot    │ ───────────────────────────> │   FastAPI        │
│  (Frontend API) │                               │   (AI Backend)   │
│                 │ <─────────────────────────────│                  │
└─────────────────┘         JSON Response        └──────────────────┘
                                                           │
                                                           ▼
                                                  ┌──────────────────┐
                                                  │  AI Agent System │
                                                  │  - LangGraph     │
                                                  │  - OpenAI GPT-4  │
                                                  │  - LangSmith     │
                                                  └──────────────────┘
```

### 주요 기능

- **AI Agent 기반 물리적 리스크 분석**: 9가지 재해 유형에 대한 리스크 점수 계산
- **비동기 작업 처리**: 장시간 분석 작업을 비동기로 처리하고 상태 조회 제공
- **AAL (Average Annual Loss) 분석**: v11 아키텍처로 업그레이드된 재무 영향 분석
- **SSP 시나리오 분석**: 기후 변화 시나리오별 미래 전망
- **사업장 이전 시뮬레이션**: 후보지 비교 분석
- **LLM 기반 리포트 생성**: TCFD/ESG 보고서 자동 생성

---

## API 기본 정보

### Base URL

```
Development: http://localhost:8000
Production:  http://{your-fastapi-server-domain}:8000
```

### 공통 헤더

```
Content-Type: application/json
X-API-Key: {your-api-key}
```

### 응답 형식

모든 응답은 JSON 형식이며, 필드명은 **camelCase**를 사용합니다.

```json
{
  "jobId": "uuid",
  "siteId": "uuid",
  "status": "completed"
}
```

---

## 인증 방식

### API Key 인증

모든 API 요청 시 **HTTP 헤더**에 API Key를 포함해야 합니다.

```http
X-API-Key: your-secret-api-key-here
```

### API Key 설정

FastAPI 서버의 `.env` 파일에서 설정:

```bash
API_KEY=your-secret-api-key-here
```

### 인증 실패 응답

```json
{
  "detail": "Invalid API Key"
}
```
**Status Code**: `403 Forbidden`

---

## 전체 API 목록

### 1. 분석 (Analysis) API

| 메서드 | 엔드포인트 | 설명 |
|--------|-----------|------|
| POST | `/api/sites/{siteId}/analysis/start` | AI 리스크 분석 시작 |
| GET | `/api/sites/{siteId}/analysis/status/{jobId}` | 분석 작업 상태 조회 |
| GET | `/api/sites/{siteId}/analysis/physical-risk-scores` | 물리적 리스크 점수 조회 |
| GET | `/api/sites/{siteId}/analysis/past-events` | 과거 재난 이력 조회 |
| GET | `/api/sites/{siteId}/analysis/financial-impacts` | 재무 영향(AAL) 조회 |
| GET | `/api/sites/{siteId}/analysis/vulnerability` | 취약성 분석 결과 조회 |
| GET | `/api/sites/{siteId}/analysis/total` | 통합 분석 결과 조회 |

### 2. 시뮬레이션 (Simulation) API

| 메서드 | 엔드포인트 | 설명 |
|--------|-----------|------|
| POST | `/api/simulation/relocation/compare` | 사업장 이전 시뮬레이션 (비교) |
| POST | `/api/simulation/climate` | 기후 시뮬레이션 |

### 3. 리포트 (Reports) API

| 메서드 | 엔드포인트 | 설명 |
|--------|-----------|------|
| POST | `/api/reports` | 리포트 생성 |
| GET | `/api/reports/web` | 웹 리포트 뷰 조회 |
| GET | `/api/reports/pdf` | PDF 리포트 조회 |
| DELETE | `/api/reports` | 리포트 삭제 |

### 4. 메타 (Meta) API

| 메서드 | 엔드포인트 | 설명 |
|--------|-----------|------|
| GET | `/api/meta/hazard-types` | 지원하는 재해 유형 목록 |
| GET | `/api/meta/ssp-scenarios` | SSP 시나리오 목록 |

---

## API 상세 스펙

### 1. AI 리스크 분석 시작

#### `POST /api/sites/{siteId}/analysis/start`

AI Agent를 사용하여 사업장의 기후 물리적 리스크를 분석합니다.

**Request**

```http
POST /api/sites/550e8400-e29b-41d4-a716-446655440000/analysis/start HTTP/1.1
Host: localhost:8000
Content-Type: application/json
X-API-Key: your-api-key

{
  "site": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "서울 본사",
    "latitude": 37.5665,
    "longitude": 126.9780,
    "address": "서울특별시 중구 세종대로 110",
    "buildingAge": 15,
    "buildingType": "OFFICE",
    "floorArea": 15000.0,
    "assetValue": 50000000000
  },
  "hazardTypes": [
    "HIGH_TEMPERATURE",
    "COLD_WAVE",
    "TYPHOON",
    "INLAND_FLOOD",
    "URBAN_FLOOD",
    "COASTAL_FLOOD",
    "WILDFIRE",
    "DROUGHT",
    "WATER_SCARCITY"
  ],
  "priority": "HIGH",
  "options": {
    "includeFinancialImpact": true,
    "includeVulnerability": true,
    "includePastEvents": true,
    "sspScenarios": ["SSP2_45", "SSP5_85"]
  }
}
```

**Response (200 OK)**

```json
{
  "jobId": "123e4567-e89b-12d3-a456-426614174000",
  "siteId": "550e8400-e29b-41d4-a716-446655440000",
  "status": "running",
  "progress": 10,
  "currentNode": "data_collection",
  "currentHazard": null,
  "startedAt": "2025-11-25T07:30:00Z",
  "completedAt": null,
  "estimatedCompletionTime": "2025-11-25T07:35:00Z",
  "error": null
}
```

**Response Fields**

| 필드 | 타입 | 설명 |
|------|------|------|
| `jobId` | UUID | 작업 ID (상태 조회 시 사용) |
| `siteId` | UUID | 사업장 ID |
| `status` | string | `queued`, `running`, `completed`, `failed` |
| `progress` | integer | 진행률 (0-100) |
| `currentNode` | string | 현재 실행 중인 워크플로우 노드 |
| `startedAt` | datetime | 시작 시간 (ISO 8601) |
| `completedAt` | datetime | 완료 시간 (nullable) |
| `estimatedCompletionTime` | datetime | 예상 완료 시간 (nullable) |
| `error` | object | 에러 정보 (nullable) |

---

### 2. 분석 작업 상태 조회

#### `GET /api/sites/{siteId}/analysis/status/{jobId}`

진행 중인 분석 작업의 상태를 조회합니다.

**Request**

```http
GET /api/sites/550e8400-e29b-41d4-a716-446655440000/analysis/status/123e4567-e89b-12d3-a456-426614174000 HTTP/1.1
Host: localhost:8000
X-API-Key: your-api-key
```

**Response (200 OK) - 진행 중**

```json
{
  "jobId": "123e4567-e89b-12d3-a456-426614174000",
  "siteId": "550e8400-e29b-41d4-a716-446655440000",
  "status": "running",
  "progress": 45,
  "currentNode": "aal_analysis",
  "currentHazard": "HIGH_TEMPERATURE",
  "startedAt": "2025-11-25T07:30:00Z",
  "completedAt": null,
  "estimatedCompletionTime": "2025-11-25T07:35:00Z",
  "error": null
}
```

**Response (200 OK) - 완료**

```json
{
  "jobId": "123e4567-e89b-12d3-a456-426614174000",
  "siteId": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "progress": 100,
  "currentNode": "completed",
  "currentHazard": null,
  "startedAt": "2025-11-25T07:30:00Z",
  "completedAt": "2025-11-25T07:35:23Z",
  "estimatedCompletionTime": null,
  "error": null
}
```

**Response (404 Not Found)**

```json
{
  "detail": "Job not found"
}
```

---

### 3. 물리적 리스크 점수 조회

#### `GET /api/sites/{siteId}/analysis/physical-risk-scores?hazardType={type}`

SSP 시나리오별 물리적 리스크 점수를 조회합니다.

**Request**

```http
GET /api/sites/550e8400-e29b-41d4-a716-446655440000/analysis/physical-risk-scores?hazardType=HIGH_TEMPERATURE HTTP/1.1
Host: localhost:8000
X-API-Key: your-api-key
```

**Query Parameters**

| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| `hazardType` | string | Optional | 특정 재해 유형 필터 (없으면 전체) |

**Response (200 OK)**

```json
{
  "scenarios": [
    {
      "scenario": "SSP2_45",
      "riskType": "HIGH_TEMPERATURE",
      "shortTerm": {
        "q1": 65,
        "q2": 72,
        "q3": 78,
        "q4": 70
      },
      "midTerm": {
        "year2026": 68,
        "year2027": 70,
        "year2028": 73,
        "year2029": 75,
        "year2030": 77
      },
      "longTerm": {
        "year2020s": 72,
        "year2030s": 78,
        "year2040s": 84,
        "year2050s": 89
      }
    },
    {
      "scenario": "SSP5_85",
      "riskType": "HIGH_TEMPERATURE",
      "shortTerm": { "q1": 70, "q2": 78, "q3": 85, "q4": 76 },
      "midTerm": { "year2026": 74, "year2027": 77, "year2028": 81, "year2029": 84, "year2030": 87 },
      "longTerm": { "year2020s": 78, "year2030s": 88, "year2040s": 95, "year2050s": 98 }
    }
  ]
}
```

---

### 4. 재무 영향(AAL) 조회

#### `GET /api/sites/{siteId}/analysis/financial-impacts`

SSP 시나리오별 AAL (Average Annual Loss) 분석 결과를 조회합니다.

**✨ AAL v11 적용**: 최신 AAL Agent v11 아키텍처를 사용하여 계산됩니다.

**Request**

```http
GET /api/sites/550e8400-e29b-41d4-a716-446655440000/analysis/financial-impacts HTTP/1.1
Host: localhost:8000
X-API-Key: your-api-key
```

**Response (200 OK)**

```json
{
  "scenarios": [
    {
      "scenario": "SSP2_45",
      "riskType": "HIGH_TEMPERATURE",
      "shortTerm": {
        "q1": 0.015,
        "q2": 0.018,
        "q3": 0.021,
        "q4": 0.019
      },
      "midTerm": {
        "year2026": 0.023,
        "year2027": 0.025,
        "year2028": 0.027,
        "year2029": 0.029,
        "year2030": 0.031
      },
      "longTerm": {
        "year2020s": 0.028,
        "year2030s": 0.035,
        "year2040s": 0.042,
        "year2050s": 0.051
      }
    }
  ]
}
```

**AAL 값 해석**
- AAL 값은 0.0 ~ 1.0 범위의 비율입니다
- 예: `0.015` = 1.5% = 자산 가치의 1.5%가 연평균 손실
- 자산 가치가 500억원이면: `500억 × 0.015 = 7.5억원` 연평균 손실

---

### 5. 취약성 분석 결과 조회

#### `GET /api/sites/{siteId}/analysis/vulnerability`

건물의 취약성 분석 결과를 조회합니다.

**Request**

```http
GET /api/sites/550e8400-e29b-41d4-a716-446655440000/analysis/vulnerability HTTP/1.1
Host: localhost:8000
X-API-Key: your-api-key
```

**Response (200 OK)**

```json
{
  "siteId": "550e8400-e29b-41d4-a716-446655440000",
  "vulnerabilities": [
    {
      "riskType": "폭염",
      "vulnerabilityScore": 75
    },
    {
      "riskType": "태풍",
      "vulnerabilityScore": 70
    },
    {
      "riskType": "홍수",
      "vulnerabilityScore": 55
    },
    {
      "riskType": "가뭄",
      "vulnerabilityScore": 40
    }
  ]
}
```

---

### 6. 통합 분석 결과 조회

#### `GET /api/sites/{siteId}/analysis/total?hazardType={type}`

특정 재해 유형 기준 통합 분석 결과를 조회합니다.

**Request**

```http
GET /api/sites/550e8400-e29b-41d4-a716-446655440000/analysis/total?hazardType=HIGH_TEMPERATURE HTTP/1.1
Host: localhost:8000
X-API-Key: your-api-key
```

**Query Parameters**

| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| `hazardType` | string | **Required** | 재해 유형 (필수) |

**Response (200 OK)**

```json
{
  "siteId": "550e8400-e29b-41d4-a716-446655440000",
  "siteName": "서울 본사",
  "physicalRisks": [
    {
      "riskType": "HIGH_TEMPERATURE",
      "riskScore": 75,
      "financialLossRate": 0.023
    },
    {
      "riskType": "TYPHOON",
      "riskScore": 70,
      "financialLossRate": 0.018
    },
    {
      "riskType": "INLAND_FLOOD",
      "riskScore": 55,
      "financialLossRate": 0.012
    }
  ]
}
```

---

### 7. 사업장 이전 시뮬레이션

#### `POST /api/simulation/relocation/compare`

현재 위치와 후보 위치의 리스크를 비교합니다.

**Request**

```http
POST /api/simulation/relocation/compare HTTP/1.1
Host: localhost:8000
Content-Type: application/json
X-API-Key: your-api-key

{
  "currentSite": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "서울 본사",
    "latitude": 37.5665,
    "longitude": 126.9780,
    "address": "서울특별시 중구 세종대로 110",
    "buildingAge": 15,
    "buildingType": "OFFICE",
    "floorArea": 15000.0,
    "assetValue": 50000000000
  },
  "candidateSite": {
    "id": "550e8400-e29b-41d4-a716-446655440001",
    "name": "부산 후보지",
    "latitude": 35.1796,
    "longitude": 129.0756,
    "address": "부산광역시 해운대구",
    "buildingAge": 0,
    "buildingType": "OFFICE",
    "floorArea": 15000.0,
    "assetValue": 50000000000
  },
  "sspScenario": "SSP2_45"
}
```

**Response (200 OK)**

```json
{
  "currentLocation": {
    "risks": [
      {
        "riskType": "폭염",
        "riskScore": 75,
        "aal": 0.023
      },
      {
        "riskType": "태풍",
        "riskScore": 70,
        "aal": 0.018
      }
    ]
  },
  "newLocation": {
    "risks": [
      {
        "riskType": "폭염",
        "riskScore": 65,
        "aal": 0.018
      },
      {
        "riskType": "태풍",
        "riskScore": 85,
        "aal": 0.032
      }
    ]
  }
}
```

---

### 8. 리포트 생성

#### `POST /api/reports`

LLM 기반 리포트를 생성합니다.

**Request**

```http
POST /api/reports HTTP/1.1
Host: localhost:8000
Content-Type: application/json
X-API-Key: your-api-key

{
  "siteId": "550e8400-e29b-41d4-a716-446655440000",
  "reportType": "COMPREHENSIVE",
  "includeCharts": true,
  "language": "ko"
}
```

**Response (200 OK)**

```json
{
  "reportId": "report-123e4567",
  "status": "completed",
  "webUrl": "/api/reports/web",
  "pdfUrl": "/api/reports/pdf"
}
```

---

## 테스트 가이드

### 1. Swagger UI를 통한 테스트

FastAPI 서버 실행 후 브라우저에서 접속:

```
http://localhost:8000/docs
```

- 모든 API를 대화형으로 테스트 가능
- "Authorize" 버튼으로 API Key 설정
- "Try it out" 버튼으로 직접 요청 전송

### 2. cURL을 통한 테스트

#### 분석 시작

```bash
curl -X POST "http://localhost:8000/api/sites/550e8400-e29b-41d4-a716-446655440000/analysis/start" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{
    "site": {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "name": "서울 본사",
      "latitude": 37.5665,
      "longitude": 126.9780,
      "address": "서울특별시 중구",
      "buildingAge": 15,
      "buildingType": "OFFICE",
      "floorArea": 15000.0,
      "assetValue": 50000000000
    },
    "hazardTypes": ["HIGH_TEMPERATURE", "TYPHOON"],
    "priority": "HIGH"
  }'
```

#### 상태 조회

```bash
curl -X GET "http://localhost:8000/api/sites/550e8400-e29b-41d4-a716-446655440000/analysis/status/123e4567-e89b-12d3-a456-426614174000" \
  -H "X-API-Key: your-api-key"
```

### 3. Postman 컬렉션

Postman 컬렉션 파일을 제공합니다 (별도 요청 시).

---

## Spring Boot 요구사항

### 1. 필수 구현 사항

#### ✅ HTTP Client 설정

Spring Boot에서 FastAPI를 호출하기 위한 HTTP 클라이언트 설정:

```java
@Configuration
public class FastApiClientConfig {

    @Value("${fastapi.base-url}")
    private String fastApiBaseUrl;

    @Value("${fastapi.api-key}")
    private String apiKey;

    @Bean
    public RestTemplate fastApiRestTemplate() {
        RestTemplate restTemplate = new RestTemplate();

        // Timeout 설정 (AI 분석은 시간이 걸릴 수 있음)
        HttpComponentsClientHttpRequestFactory factory =
            new HttpComponentsClientHttpRequestFactory();
        factory.setConnectTimeout(10000);  // 10초
        factory.setReadTimeout(300000);     // 5분

        restTemplate.setRequestFactory(factory);

        // Interceptor로 API Key 자동 추가
        restTemplate.getInterceptors().add((request, body, execution) -> {
            request.getHeaders().set("X-API-Key", apiKey);
            return execution.execute(request, body);
        });

        return restTemplate;
    }
}
```

#### ✅ application.yml 설정

```yaml
fastapi:
  base-url: http://localhost:8000
  api-key: your-secret-api-key-here

  # Timeout 설정 (밀리초)
  connect-timeout: 10000
  read-timeout: 300000  # AI 분석은 최대 5분 소요 가능
```

### 2. DTO 클래스 예제

#### StartAnalysisRequest DTO

```java
@Data
@Builder
public class StartAnalysisRequest {
    private SiteInfo site;
    private List<String> hazardTypes;
    private String priority;  // HIGH, NORMAL, LOW
    private AnalysisOptions options;
}

@Data
@Builder
public class SiteInfo {
    private UUID id;
    private String name;
    private Double latitude;
    private Double longitude;
    private String address;
    private Integer buildingAge;
    private String buildingType;  // OFFICE, FACTORY, WAREHOUSE, etc.
    private Double floorArea;
    private Long assetValue;
}

@Data
@Builder
public class AnalysisOptions {
    private Boolean includeFinancialImpact;
    private Boolean includeVulnerability;
    private Boolean includePastEvents;
    private List<String> sspScenarios;  // SSP2_45, SSP5_85
}
```

#### AnalysisJobStatus Response DTO

```java
@Data
public class AnalysisJobStatus {
    private UUID jobId;
    private UUID siteId;
    private String status;  // queued, running, completed, failed
    private Integer progress;  // 0-100
    private String currentNode;
    private String currentHazard;
    private LocalDateTime startedAt;
    private LocalDateTime completedAt;
    private LocalDateTime estimatedCompletionTime;
    private ErrorInfo error;
}

@Data
public class ErrorInfo {
    private String code;
    private String message;
}
```

### 3. Service 클래스 예제

```java
@Service
@Slf4j
public class FastApiService {

    private final RestTemplate fastApiRestTemplate;
    private final String baseUrl;

    @Autowired
    public FastApiService(
        RestTemplate fastApiRestTemplate,
        @Value("${fastapi.base-url}") String baseUrl
    ) {
        this.fastApiRestTemplate = fastApiRestTemplate;
        this.baseUrl = baseUrl;
    }

    /**
     * AI 리스크 분석 시작
     */
    public AnalysisJobStatus startAnalysis(UUID siteId, StartAnalysisRequest request) {
        String url = baseUrl + "/api/sites/" + siteId + "/analysis/start";

        try {
            ResponseEntity<AnalysisJobStatus> response = fastApiRestTemplate.postForEntity(
                url,
                request,
                AnalysisJobStatus.class
            );

            return response.getBody();
        } catch (HttpClientErrorException e) {
            log.error("FastAPI 호출 실패: {}", e.getResponseBodyAsString());
            throw new RuntimeException("AI 분석 시작 실패", e);
        }
    }

    /**
     * 분석 작업 상태 조회
     */
    public AnalysisJobStatus getAnalysisStatus(UUID siteId, UUID jobId) {
        String url = baseUrl + "/api/sites/" + siteId + "/analysis/status/" + jobId;

        try {
            ResponseEntity<AnalysisJobStatus> response = fastApiRestTemplate.getForEntity(
                url,
                AnalysisJobStatus.class
            );

            return response.getBody();
        } catch (HttpStatusCodeException e) {
            if (e.getStatusCode() == HttpStatus.NOT_FOUND) {
                return null;
            }
            throw new RuntimeException("상태 조회 실패", e);
        }
    }

    /**
     * 폴링을 통한 완료 대기 (비동기 처리)
     */
    @Async
    public CompletableFuture<AnalysisJobStatus> waitForCompletion(
        UUID siteId,
        UUID jobId,
        int maxWaitSeconds
    ) {
        int waited = 0;
        int pollInterval = 5;  // 5초마다 폴링

        while (waited < maxWaitSeconds) {
            AnalysisJobStatus status = getAnalysisStatus(siteId, jobId);

            if (status == null) {
                throw new RuntimeException("Job not found");
            }

            if ("completed".equals(status.getStatus())) {
                return CompletableFuture.completedFuture(status);
            }

            if ("failed".equals(status.getStatus())) {
                throw new RuntimeException("Analysis failed: " + status.getError());
            }

            try {
                Thread.sleep(pollInterval * 1000);
                waited += pollInterval;
            } catch (InterruptedException e) {
                Thread.currentThread().interrupt();
                throw new RuntimeException("Polling interrupted", e);
            }
        }

        throw new RuntimeException("Analysis timeout");
    }
}
```

### 4. Controller 예제

```java
@RestController
@RequestMapping("/api/v1/climate-risk")
@Slf4j
public class ClimateRiskController {

    private final FastApiService fastApiService;

    @Autowired
    public ClimateRiskController(FastApiService fastApiService) {
        this.fastApiService = fastApiService;
    }

    /**
     * AI 리스크 분석 시작 및 완료 대기
     */
    @PostMapping("/sites/{siteId}/analyze")
    public ResponseEntity<AnalysisJobStatus> analyzeAndWait(
        @PathVariable UUID siteId,
        @RequestBody StartAnalysisRequest request
    ) {
        // 1. 분석 시작
        AnalysisJobStatus jobStatus = fastApiService.startAnalysis(siteId, request);
        log.info("분석 시작: jobId={}, progress={}%", jobStatus.getJobId(), jobStatus.getProgress());

        // 2. 완료 대기 (비동기)
        try {
            AnalysisJobStatus finalStatus = fastApiService.waitForCompletion(
                siteId,
                jobStatus.getJobId(),
                300  // 최대 5분 대기
            ).get();

            log.info("분석 완료: jobId={}", finalStatus.getJobId());
            return ResponseEntity.ok(finalStatus);

        } catch (Exception e) {
            log.error("분석 중 오류 발생", e);
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).build();
        }
    }

    /**
     * 물리적 리스크 점수 조회
     */
    @GetMapping("/sites/{siteId}/physical-risk-scores")
    public ResponseEntity<PhysicalRiskScoreResponse> getPhysicalRiskScores(
        @PathVariable UUID siteId,
        @RequestParam(required = false) String hazardType
    ) {
        String url = String.format(
            "%s/api/sites/%s/analysis/physical-risk-scores%s",
            baseUrl,
            siteId,
            hazardType != null ? "?hazardType=" + hazardType : ""
        );

        ResponseEntity<PhysicalRiskScoreResponse> response =
            fastApiRestTemplate.getForEntity(url, PhysicalRiskScoreResponse.class);

        return response;
    }
}
```

---

## 에러 처리

### HTTP 상태 코드

| 상태 코드 | 설명 | 대응 방법 |
|----------|------|----------|
| `200 OK` | 성공 | - |
| `400 Bad Request` | 잘못된 요청 | Request Body 검증 |
| `403 Forbidden` | API Key 인증 실패 | API Key 확인 |
| `404 Not Found` | 리소스 없음 | siteId, jobId 확인 |
| `422 Unprocessable Entity` | 유효성 검증 실패 | 필드 형식 확인 |
| `500 Internal Server Error` | 서버 오류 | 로그 확인, 재시도 |

### 에러 응답 형식

```json
{
  "detail": "Error message here"
}
```

또는

```json
{
  "detail": [
    {
      "loc": ["body", "site", "latitude"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

### 에러 처리 Best Practices

```java
try {
    // FastAPI 호출
} catch (HttpClientErrorException.BadRequest e) {
    // 400: 요청 데이터 검증
    log.error("잘못된 요청: {}", e.getResponseBodyAsString());
} catch (HttpClientErrorException.Forbidden e) {
    // 403: API Key 오류
    log.error("인증 실패: API Key 확인 필요");
} catch (HttpClientErrorException.NotFound e) {
    // 404: 리소스 없음
    log.error("리소스 없음: siteId 또는 jobId 확인 필요");
} catch (HttpServerErrorException e) {
    // 500: 서버 오류
    log.error("FastAPI 서버 오류: 재시도 필요");
} catch (ResourceAccessException e) {
    // Timeout 또는 연결 실패
    log.error("FastAPI 연결 실패: 네트워크 확인 필요");
}
```

---

## 연동 예제 코드

### 전체 플로우 예제

```java
@Service
@Slf4j
public class ClimateRiskAnalysisService {

    private final FastApiService fastApiService;

    /**
     * 전체 분석 플로우
     */
    public AnalysisResult performFullAnalysis(UUID siteId, SiteInfo siteInfo) {
        // 1. 분석 시작
        StartAnalysisRequest request = StartAnalysisRequest.builder()
            .site(siteInfo)
            .hazardTypes(Arrays.asList(
                "HIGH_TEMPERATURE", "TYPHOON", "INLAND_FLOOD"
            ))
            .priority("HIGH")
            .options(AnalysisOptions.builder()
                .includeFinancialImpact(true)
                .includeVulnerability(true)
                .includePastEvents(true)
                .sspScenarios(Arrays.asList("SSP2_45", "SSP5_85"))
                .build())
            .build();

        AnalysisJobStatus jobStatus = fastApiService.startAnalysis(siteId, request);
        log.info("분석 시작됨: jobId={}", jobStatus.getJobId());

        // 2. 완료 대기
        AnalysisJobStatus completedStatus = fastApiService.waitForCompletion(
            siteId,
            jobStatus.getJobId(),
            300  // 5분
        ).join();

        if (!"completed".equals(completedStatus.getStatus())) {
            throw new RuntimeException("분석 실패");
        }

        log.info("분석 완료: jobId={}", completedStatus.getJobId());

        // 3. 결과 조회
        PhysicalRiskScoreResponse riskScores =
            fastApiService.getPhysicalRiskScores(siteId, null);

        FinancialImpactResponse financialImpacts =
            fastApiService.getFinancialImpacts(siteId);

        VulnerabilityResponse vulnerability =
            fastApiService.getVulnerability(siteId);

        // 4. 결과 통합
        return AnalysisResult.builder()
            .jobId(completedStatus.getJobId())
            .siteId(siteId)
            .riskScores(riskScores)
            .financialImpacts(financialImpacts)
            .vulnerability(vulnerability)
            .analyzedAt(LocalDateTime.now())
            .build();
    }
}
```

---

## 연락처 및 지원

### 기술 지원

- **Email**: backend-team@example.com
- **Slack**: #fastapi-integration
- **Issue Tracker**: GitHub Issues

### 추가 요청사항

Spring Boot 팀에서 추가로 필요한 사항이 있으면 알려주세요:
- 추가 API 엔드포인트
- DTO 클래스 예제
- 특정 시나리오별 테스트 케이스
- WebSocket 연동 (실시간 진행률 업데이트)

---

**작성자**: Backend Team
**최종 업데이트**: 2025-11-25
**버전**: 1.0
**문서 상태**: ✅ 리뷰 완료
