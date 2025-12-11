# Spring Boot → FastAPI 422 에러 해결 가이드

## 문서 정보
- **작성일**: 2025-12-10
- **대상**: Spring Boot 백엔드 팀
- **목적**: FastAPI 호출 시 422 Unprocessable Entity 에러 원인 분석 및 해결 방법

---

## 📋 목차
1. [422 에러란?](#422-에러란)
2. [주요 원인 분석](#주요-원인-분석)
3. [필수 수정 사항](#필수-수정-사항)
4. [Enum 값 매핑 테이블](#enum-값-매핑-테이블)
5. [코드 수정 예시](#코드-수정-예시)
6. [테스트 방법](#테스트-방법)
7. [문제 해결 체크리스트](#문제-해결-체크리스트)

---

## 422 에러란?

**HTTP 422 Unprocessable Entity**는 다음을 의미합니다:
- ✅ 요청 형식(JSON)은 올바름
- ✅ URL 경로는 정확함
- ✅ HTTP 메서드가 맞음
- ❌ **요청 데이터 내용이 검증 실패**

FastAPI는 Pydantic을 사용하여 요청 데이터를 엄격하게 검증합니다. 필드 타입, 값 범위, Enum 값 등이 정확히 일치해야 합니다.

---

## 주요 원인 분석

### ✅ 1. URL 경로 - 문제 없음!

**Spring Boot Client** (`FastApiClient.java`):
```java
// Line 60
POST /api/analysis/start  ✅ 올바름

// Line 83-86
GET /api/analysis/status?siteId={uuid}&jobId={uuid}  ✅ 올바름
```

**FastAPI Server** (`analysis.py`):
```python
@router.post("/start", ...)  # Prefix: /api/analysis
GET /api/analysis/status?siteId=...&jobId=...
```

**결론**: URL 경로는 모두 일치합니다. ✅

---

### ⚠️ 2. Industry 필드 - **HIGH 우선순위 수정 필요**

#### 문제 상황:

**Spring Boot** (`SiteInfoDto.java:50`):
```java
.industry(site.getType())  // DB에서 가져온 값 그대로 전달
```

**FastAPI 기대값** (`common.py:53`):
```python
industry: str = Field(..., description="산업 분류 (data_center, factory, office, warehouse, retail)")
```

#### 원인:
Spring의 `site.getType()`이 반환하는 값이 FastAPI가 기대하는 특정 문자열이 아닐 수 있습니다.

예시:
- Spring DB: `"제조업"`, `"데이터센터"`, `"MANUFACTURING"` 등
- FastAPI 기대: `"factory"`, `"data_center"`, `"office"`, `"warehouse"`, `"retail"`

#### 해결 방법:
`SiteInfoDto.java`에 매핑 로직 추가 필요:

```java
public static SiteInfoDto from(Site site) {
    String address = site.getRoadAddress() != null ? site.getRoadAddress() : site.getJibunAddress();

    // ✅ Industry 값 변환 로직 추가
    String industry = mapSiteTypeToIndustry(site.getType());

    return SiteInfoDto.builder()
        .id(site.getId())
        .name(site.getName())
        .address(address)
        .latitude(site.getLatitude())
        .longitude(site.getLongitude())
        .industry(industry)  // 변환된 값 사용
        .build();
}

/**
 * Site의 type을 FastAPI industry 형식으로 변환
 */
private static String mapSiteTypeToIndustry(String siteType) {
    if (siteType == null) {
        return "office";  // 기본값
    }

    // 대소문자 구분 없이 매핑
    String normalized = siteType.toLowerCase().trim();

    switch (normalized) {
        case "데이터센터":
        case "data_center":
        case "datacenter":
            return "data_center";

        case "제조업":
        case "공장":
        case "factory":
        case "manufacturing":
            return "factory";

        case "사무실":
        case "본사":
        case "office":
            return "office";

        case "창고":
        case "warehouse":
        case "물류센터":
            return "warehouse";

        case "매장":
        case "retail":
        case "소매":
            return "retail";

        default:
            log.warn("Unknown site type: {}. Using default 'office'", siteType);
            return "office";  // 알 수 없는 값은 기본값
    }
}
```

---

### ⚠️ 3. HazardType 값 - **HIGH 우선순위 수정 필요**

#### 문제 상황:

**FastAPI 기대값** (`common.py:8-17`):
```python
class HazardType(str, Enum):
    TYPHOON = "태풍"
    INLAND_FLOOD = "내륙침수"
    COASTAL_FLOOD = "해안침수"
    URBAN_FLOOD = "도시침수"
    DROUGHT = "가뭄"
    WILDFIRE = "산불"
    HIGH_TEMPERATURE = "폭염"
    COLD_WAVE = "한파"
    WATER_SCARCITY = "물부족"
```

FastAPI는 **한글 값**을 기대합니다!

#### Spring에서 보내는 값 확인 필요:

**현재 코드** (`StartAnalysisRequestDto.java:27`):
```java
private List<String> hazardTypes;  // 어떤 값이 들어가는가?
```

#### 예상 문제:
Spring이 다음과 같은 값을 보낼 가능성:
- ❌ `["TYPHOON", "FLOOD"]` (영문 대문자)
- ❌ `["typhoon", "inland_flood"]` (영문 소문자)
- ❌ `["Typhoon", "Inland Flood"]` (영문 타이틀케이스)

#### 해결 방법:
Spring Boot에서 **한글 값으로 변환** 필요:

```java
/**
 * Spring의 HazardType Enum을 FastAPI 한글 값으로 변환
 */
public class HazardTypeMapper {

    private static final Map<String, String> HAZARD_TYPE_MAP = Map.of(
        "TYPHOON", "태풍",
        "INLAND_FLOOD", "내륙침수",
        "COASTAL_FLOOD", "해안침수",
        "URBAN_FLOOD", "도시침수",
        "DROUGHT", "가뭄",
        "WILDFIRE", "산불",
        "HIGH_TEMPERATURE", "폭염",
        "COLD_WAVE", "한파",
        "WATER_SCARCITY", "물부족"
    );

    public static String toFastApiValue(String springHazardType) {
        String mapped = HAZARD_TYPE_MAP.get(springHazardType.toUpperCase());
        if (mapped == null) {
            throw new IllegalArgumentException("Unknown hazard type: " + springHazardType);
        }
        return mapped;
    }

    public static List<String> toFastApiValues(List<String> springHazardTypes) {
        return springHazardTypes.stream()
            .map(HazardTypeMapper::toFastApiValue)
            .collect(Collectors.toList());
    }
}
```

**FastApiClient.java 수정**:
```java
public Mono<Map<String, Object>> startAnalysis(StartAnalysisRequestDto request) {
    // ✅ HazardType 값 변환
    List<String> convertedHazardTypes = HazardTypeMapper.toFastApiValues(request.getHazardTypes());

    // DTO 복사 (변환된 값 사용)
    StartAnalysisRequestDto convertedRequest = StartAnalysisRequestDto.builder()
        .site(request.getSite())
        .hazardTypes(convertedHazardTypes)  // 변환된 값
        .priority(request.getPriority())
        .options(request.getOptions())
        .build();

    log.info("FastAPI 분석 시작 요청: siteId={}, hazardTypes={}, priority={}",
        convertedRequest.getSite().getId(), convertedRequest.getHazardTypes(), convertedRequest.getPriority());

    return webClient.post()
        .uri("/api/analysis/start")
        .header("X-API-Key", apiKey)
        .bodyValue(convertedRequest)  // 변환된 요청 사용
        .retrieve()
        .bodyToMono(MAP_TYPE_REF)
        .doOnSuccess(response -> log.info("분석 시작 성공: {}", response))
        .doOnError(error -> log.error("분석 시작 실패", error));
}
```

---

### ⚠️ 4. SSP Scenario 형식 - **MEDIUM 우선순위**

#### 문제 상황:

**FastAPI 기대값** (`common.py:26-30`):
```python
class SSPScenario(str, Enum):
    SSP1_26 = "SSP1-2.6"
    SSP2_45 = "SSP2-4.5"
    SSP3_70 = "SSP3-7.0"
    SSP5_85 = "SSP5-8.5"
```

#### Spring에서 확인 필요:

**현재 코드** (`StartAnalysisRequestDto.java:39`):
```java
private List<String> sspScenarios;  // ["SSP2-4.5", "SSP5-8.5"]
```

#### 올바른 형식:
- ✅ `"SSP1-2.6"` (하이픈 포함, 소수점 포함)
- ✅ `"SSP2-4.5"`
- ✅ `"SSP3-7.0"`
- ✅ `"SSP5-8.5"`

#### 잘못된 형식 예시:
- ❌ `"SSP245"` (하이픈 없음)
- ❌ `"SSP2_45"` (언더스코어)
- ❌ `"ssp2-4.5"` (소문자)

#### 검증 코드 추가 권장:
```java
public class SSPScenarioValidator {

    private static final Set<String> VALID_SCENARIOS = Set.of(
        "SSP1-2.6", "SSP2-4.5", "SSP3-7.0", "SSP5-8.5"
    );

    public static void validate(List<String> scenarios) {
        if (scenarios == null || scenarios.isEmpty()) {
            return;  // Optional이므로 null/empty 허용
        }

        for (String scenario : scenarios) {
            if (!VALID_SCENARIOS.contains(scenario)) {
                throw new IllegalArgumentException(
                    "Invalid SSP scenario: " + scenario +
                    ". Must be one of: " + VALID_SCENARIOS
                );
            }
        }
    }
}
```

---

### ✅ 5. Priority 값 - 문제 없음

**Spring Boot** (`StartAnalysisRequestDto.java:28`):
```java
private String priority;  // "low", "normal", "high"
```

**FastAPI** (`common.py:40-43`):
```python
class Priority(str, Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
```

**확인 사항**:
- ✅ 소문자 사용 (`"low"`, `"normal"`, `"high"`)
- ✅ 기본값: `"normal"`

---

### 🔍 6. 추가 검증 사항

#### A. UUID 형식
```java
// ✅ 올바른 형식
UUID siteId = UUID.fromString("0108c964-fd03-4dfd-82e3-caf5674f62bd");

// ❌ 잘못된 형식
String siteId = "some-random-string";  // UUID 아님
```

#### B. BigDecimal → Float 변환
Spring의 `BigDecimal`이 JSON 직렬화 시 문제를 일으킬 수 있습니다.

**확인 필요**:
```java
// SiteInfoDto.java:31-32
private BigDecimal latitude;   // JSON: 37.5665 (숫자로 직렬화되는지 확인)
private BigDecimal longitude;  // JSON: 126.9780
```

Jackson 설정 확인:
```java
// application.yml 또는 Jackson 설정
spring:
  jackson:
    serialization:
      WRITE_BIGDECIMAL_AS_PLAIN: true  # 과학적 표기법 방지
```

---

## Enum 값 매핑 테이블

### 1. HazardType (재난 유형)

| Spring Boot 값 (예상) | FastAPI 필수 값 | 설명 |
|---|---|---|
| `TYPHOON` | `태풍` | 태풍 |
| `INLAND_FLOOD` | `내륙침수` | 내륙 침수 |
| `COASTAL_FLOOD` | `해안침수` | 해안 침수 |
| `URBAN_FLOOD` | `도시침수` | 도시 침수 |
| `DROUGHT` | `가뭄` | 가뭄 |
| `WILDFIRE` | `산불` | 산불 |
| `HIGH_TEMPERATURE` | `폭염` | 폭염 |
| `COLD_WAVE` | `한파` | 한파 |
| `WATER_SCARCITY` | `물부족` | 물 부족 |

### 2. Industry (산업 분류)

| Spring DB 값 (예상) | FastAPI 필수 값 | 설명 |
|---|---|---|
| `데이터센터`, `data_center`, `datacenter` | `data_center` | 데이터 센터 |
| `제조업`, `공장`, `factory`, `manufacturing` | `factory` | 공장 |
| `사무실`, `본사`, `office` | `office` | 사무실 |
| `창고`, `warehouse`, `물류센터` | `warehouse` | 창고 |
| `매장`, `retail`, `소매` | `retail` | 소매점 |

### 3. SSP Scenarios (기후 시나리오)

| 올바른 값 | 설명 |
|---|---|
| `SSP1-2.6` | 지속가능 발전 경로 |
| `SSP2-4.5` | 중간 경로 (기본값) |
| `SSP3-7.0` | 지역 경쟁 경로 |
| `SSP5-8.5` | 화석연료 의존 경로 |

### 4. Priority (우선순위)

| 값 | 설명 |
|---|---|
| `low` | 낮음 |
| `normal` | 보통 (기본값) |
| `high` | 높음 |

---

## 코드 수정 예시

### 전체 수정 예시: FastApiClient.java

```java
public Mono<Map<String, Object>> startAnalysis(StartAnalysisRequestDto request) {
    // 1. Industry 값 검증 및 변환 (SiteInfoDto.from()에서 이미 처리됨)

    // 2. HazardType 값 변환
    List<String> convertedHazardTypes = HazardTypeMapper.toFastApiValues(request.getHazardTypes());

    // 3. SSP Scenario 검증 (options가 있는 경우)
    if (request.getOptions() != null && request.getOptions().getSspScenarios() != null) {
        SSPScenarioValidator.validate(request.getOptions().getSspScenarios());
    }

    // 4. 변환된 요청 생성
    StartAnalysisRequestDto convertedRequest = StartAnalysisRequestDto.builder()
        .site(request.getSite())
        .hazardTypes(convertedHazardTypes)
        .priority(request.getPriority() != null ? request.getPriority().toLowerCase() : "normal")
        .options(request.getOptions())
        .build();

    log.info("FastAPI 분석 시작 요청: siteId={}, hazardTypes={}, priority={}",
        convertedRequest.getSite().getId(),
        convertedRequest.getHazardTypes(),
        convertedRequest.getPriority());
    log.debug("전체 요청 본문: {}", convertedRequest);

    return webClient.post()
        .uri("/api/analysis/start")
        .header("X-API-Key", apiKey)
        .bodyValue(convertedRequest)
        .retrieve()
        .bodyToMono(MAP_TYPE_REF)
        .doOnSuccess(response -> log.info("분석 시작 성공: {}", response))
        .doOnError(error -> {
            log.error("분석 시작 실패", error);
            // 422 에러 발생 시 요청 본문 로깅
            if (error instanceof WebClientResponseException) {
                WebClientResponseException ex = (WebClientResponseException) error;
                if (ex.getStatusCode().value() == 422) {
                    log.error("422 Validation Error - 요청 본문: {}", convertedRequest);
                    log.error("422 Validation Error - 응답 본문: {}", ex.getResponseBodyAsString());
                }
            }
        });
}
```

---

## 테스트 방법

### 1. 단위 테스트 작성

```java
@Test
void testIndustryMapping() {
    // Given
    Site site = Site.builder()
        .id(UUID.randomUUID())
        .name("서울 본사")
        .type("제조업")  // DB 값
        .roadAddress("서울시 강남구...")
        .latitude(new BigDecimal("37.5665"))
        .longitude(new BigDecimal("126.9780"))
        .build();

    // When
    SiteInfoDto dto = SiteInfoDto.from(site);

    // Then
    assertEquals("factory", dto.getIndustry());  // FastAPI 기대값
}

@Test
void testHazardTypeMapping() {
    // Given
    List<String> springValues = List.of("TYPHOON", "INLAND_FLOOD");

    // When
    List<String> fastApiValues = HazardTypeMapper.toFastApiValues(springValues);

    // Then
    assertEquals(List.of("태풍", "내륙침수"), fastApiValues);
}

@Test
void testSSPScenarioValidation() {
    // Valid
    assertDoesNotThrow(() -> SSPScenarioValidator.validate(List.of("SSP2-4.5", "SSP5-8.5")));

    // Invalid
    assertThrows(IllegalArgumentException.class,
        () -> SSPScenarioValidator.validate(List.of("SSP245")));
}
```

### 2. 통합 테스트

```java
@SpringBootTest
@AutoConfigureWebTestClient
class FastApiClientIntegrationTest {

    @Autowired
    private FastApiClient fastApiClient;

    @Test
    void testStartAnalysis_Success() {
        // Given
        SiteInfoDto site = SiteInfoDto.builder()
            .id(UUID.fromString("0108c964-fd03-4dfd-82e3-caf5674f62bd"))
            .name("서울 본사")
            .address("서울시 강남구...")
            .latitude(new BigDecimal("37.5665"))
            .longitude(new BigDecimal("126.9780"))
            .industry("factory")  // FastAPI 형식
            .build();

        StartAnalysisRequestDto request = StartAnalysisRequestDto.builder()
            .site(site)
            .hazardTypes(List.of("태풍", "내륙침수"))  // FastAPI 형식
            .priority("normal")
            .options(StartAnalysisRequestDto.AnalysisOptions.builder()
                .includeFinancialImpact(true)
                .includeVulnerability(true)
                .includePastEvents(true)
                .sspScenarios(List.of("SSP2-4.5", "SSP5-8.5"))
                .build())
            .build();

        // When
        StepVerifier.create(fastApiClient.startAnalysis(request))
            // Then
            .assertNext(response -> {
                assertNotNull(response.get("jobId"));
                assertNotNull(response.get("siteId"));
                assertEquals("queued", response.get("status"));
            })
            .verifyComplete();
    }
}
```

### 3. 로컬 테스트 (cURL)

```bash
# 올바른 요청 예시
curl -X POST "http://localhost:8000/api/analysis/start" \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "site": {
      "id": "0108c964-fd03-4dfd-82e3-caf5674f62bd",
      "name": "서울 본사",
      "address": "서울시 강남구 테헤란로 123",
      "latitude": 37.5665,
      "longitude": 126.9780,
      "industry": "factory"
    },
    "hazardTypes": ["태풍", "내륙침수"],
    "priority": "normal",
    "options": {
      "includeFinancialImpact": true,
      "includeVulnerability": true,
      "includePastEvents": true,
      "sspScenarios": ["SSP2-4.5", "SSP5-8.5"]
    }
  }'
```

### 4. FastAPI 검증 에러 확인 방법

422 에러 발생 시 FastAPI는 다음과 같은 상세 정보를 반환합니다:

```json
{
  "detail": [
    {
      "type": "enum",
      "loc": ["body", "hazardTypes", 0],
      "msg": "Input should be '태풍', '내륙침수', '해안침수', '도시침수', '가뭄', '산불', '폭염', '한파' or '물부족'",
      "input": "TYPHOON",
      "ctx": {
        "expected": "'태풍', '내륙침수', '해안침수', '도시침수', '가뭄', '산불', '폭염', '한파' or '물부족'"
      }
    }
  ]
}
```

**에러 해석**:
- `loc`: `["body", "hazardTypes", 0]` → 요청 본문의 `hazardTypes` 배열의 첫 번째 요소
- `msg`: 기대하는 값 목록
- `input`: 실제로 받은 값 (`"TYPHOON"`)

---

## 문제 해결 체크리스트

### ✅ 수정 전 확인 사항

- [ ] Spring Boot의 `Site.type` 필드가 어떤 값을 저장하는지 확인
- [ ] HazardType이 어떤 형식으로 저장/전달되는지 확인
- [ ] SSP Scenario 값이 올바른 형식인지 확인
- [ ] Jackson 직렬화 설정 확인 (BigDecimal → Float)
- [ ] API Key가 올바르게 설정되어 있는지 확인

### ✅ 필수 수정 사항

- [ ] `SiteInfoDto.from()` 메서드에 `mapSiteTypeToIndustry()` 추가
- [ ] `HazardTypeMapper` 클래스 생성
- [ ] `FastApiClient.startAnalysis()` 메서드에 변환 로직 추가
- [ ] `SSPScenarioValidator` 클래스 생성 (선택)
- [ ] 단위 테스트 작성
- [ ] 422 에러 로깅 강화

### ✅ 테스트 체크리스트

- [ ] 단위 테스트 통과 확인
- [ ] Industry 매핑 테스트
- [ ] HazardType 매핑 테스트
- [ ] SSP Scenario 검증 테스트
- [ ] 통합 테스트 (실제 FastAPI 서버 호출)
- [ ] 로컬 환경에서 cURL 테스트
- [ ] 개발 환경 배포 후 E2E 테스트

### ✅ 배포 후 모니터링

- [ ] 422 에러 로그 모니터링
- [ ] 잘못된 값으로 인한 에러 패턴 파악
- [ ] 추가 매핑 규칙 필요 시 업데이트

---

## 빠른 참조: 주요 변경 파일

| 파일 | 변경 내용 |
|------|---------|
| `SiteInfoDto.java` | `mapSiteTypeToIndustry()` 메서드 추가 |
| `HazardTypeMapper.java` | **신규 생성** - Hazard Type 변환 |
| `SSPScenarioValidator.java` | **신규 생성** - SSP 검증 (선택) |
| `FastApiClient.java` | `startAnalysis()` 메서드에 변환 로직 추가 |
| `FastApiClientTest.java` | 단위 테스트 추가 |

---

## 추가 도움이 필요한 경우

1. **FastAPI 로그 확인**: FastAPI 서버 로그에서 정확한 검증 에러 확인
2. **Swagger UI 테스트**: `http://localhost:8000/docs`에서 직접 테스트
3. **Pydantic 검증 에러 문서**: https://docs.pydantic.dev/latest/errors/validation_errors/

---

## 요약

### 422 에러의 주요 원인
1. **Industry 필드**: Spring의 `site.type` 값이 FastAPI 기대값과 불일치
2. **HazardType**: 영문 값 대신 한글 값 필요
3. **SSP Scenario**: 정확한 형식 필요 (`"SSP2-4.5"`)

### 해결 방법
1. **Industry**: 매핑 함수로 변환
2. **HazardType**: Mapper 클래스로 한글 변환
3. **SSP**: Validator로 형식 검증

### 다음 단계
1. 매핑 로직 구현
2. 단위 테스트 작성
3. 통합 테스트 실행
4. 개발 환경 배포 및 모니터링
