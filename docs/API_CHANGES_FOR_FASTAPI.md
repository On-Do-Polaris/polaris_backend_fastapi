# Spring Boot API Changes Summary for FastAPI Team

## Document Information
- **Date**: 2025-12-09
- **Version**: v1.0
- **Author**: SKAX Backend Team
- **Purpose**: Communicate Spring Boot API changes to FastAPI team for coordination

---

## Summary of Changes

This document outlines the recent changes made to the Spring Boot backend APIs that may affect FastAPI integration.

### Changes Overview
1. ✅ **Completed**: Dashboard API - Added coordinates (latitude/longitude)
2. ✅ **Completed**: Sites List API - Added coordinates and full address fields
3. ✅ **Completed**: SSP Scenarios - Added SSP3-7.0 (now returns 4 scenarios)
4. 🔄 **In Progress**: Climate Simulation API - Removed manual parameters

---

## 1. Dashboard Summary API Enhancement

### Endpoint
`GET /api/dashboard/summary`

### What Changed
**Added two new fields to each site in the response:**
- `latitude` (BigDecimal): Site latitude coordinate
- `longitude` (BigDecimal): Site longitude coordinate

### Current Response Format
```json
{
  "mainClimateRisk": "극심한 고온",
  "sites": [
    {
      "siteId": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
      "siteName": "서울 본사",
      "siteType": "공장",
      "latitude": "37.36633726",       // NEW
      "longitude": "127.10661717",     // NEW
      "location": "서울특별시 강남구",
      "totalRiskScore": 75
    }
  ]
}
```

### Implementation Details
- **Source**: Coordinates are fetched from Spring Boot database (Site entity)
- **Method**: Response enrichment after receiving FastAPI response
- **Precision**: BigDecimal type with precision=10,scale=8 (latitude) and precision=11,scale=8 (longitude)

### Impact on FastAPI
**Option 1 (Recommended):** FastAPI can start including coordinates directly in the dashboard response
- Benefit: Eliminates extra database query in Spring Boot
- Requirement: FastAPI needs access to site coordinates

**Option 2 (Current):** Spring Boot enriches the response
- FastAPI returns original response format
- Spring Boot adds coordinates from its database

**No immediate action required from FastAPI team** - Current implementation works with existing FastAPI response format.

---

## 2. Sites List API Enhancement

### Endpoint
`GET /api/sites`

### What Changed
**Replaced single `location` field with 4 new fields:**
- ❌ Removed: `location` (single combined address field)
- ✅ Added: `latitude` (BigDecimal)
- ✅ Added: `longitude` (BigDecimal)
- ✅ Added: `jibunAddress` (String) - 지번 주소
- ✅ Added: `roadAddress` (String) - 도로명 주소

### Current Response Format
```json
{
  "sites": [
    {
      "siteId": "3bcf9839-01bb-4998-beb3-8728b7afe725",
      "siteName": "sk u 타워",
      "latitude": "37.36633726",
      "longitude": "127.10661717",
      "jibunAddress": "경기도 성남시 분당구 정자동 25-1 에스케이유타워",
      "roadAddress": "경기도 성남시 분당구 성남대로343번길 9",
      "siteType": "data_center"
    }
  ]
}
```

### Implementation Details
- **Source**: All data from Spring Boot database (no FastAPI involvement)
- **Change Type**: Response structure modification only
- **Breaking Change**: Yes - Frontend must update to use new field names

### Impact on FastAPI
**No impact** - This endpoint does not communicate with FastAPI. All data comes from Spring Boot database.

---

## 3. SSP Scenarios Update

### Endpoint
`GET /api/meta/ssp-scenarios`

### What Changed
**Added one new SSP scenario:**
- SSP3-7.0 (Regional Rivalry)

### Current Response
```json
["SSP1-2.6", "SSP2-4.5", "SSP3-7.0", "SSP5-8.5"]
```

**Previously returned:**
```json
["SSP1-2.6", "SSP2-4.5", "SSP5-8.5"]
```

### Implementation Details
- **Source**: Hardcoded list in Spring Boot controller
- **Count**: Now returns 4 scenarios (was 3)
- **Excluded**: SSP4-6.0 deliberately not included

### Impact on FastAPI
**Action Required:**
- ✅ Verify FastAPI supports SSP3-7.0 scenario
- ✅ Update any scenario validation logic to accept SSP3-7.0
- ✅ Ensure all FastAPI endpoints that accept scenario parameter can handle SSP3-7.0

**Affected FastAPI Endpoints:**
- `/api/sites/{siteId}/analysis/start` - StartAnalysisRequest
- `/api/sites/{siteId}/analysis/ssp` - SSP projection endpoint
- `/api/simulation/climate` - Climate simulation
- Any other endpoints with SSP scenario parameters

---

## 4. Climate Simulation API Update (In Progress)

### Endpoint
`POST /api/simulation/climate`

### What Changed
**Removed two required fields from request:**
- ❌ Removed: `siteIds` (List<UUID>) - No longer accepts manual site selection
- ❌ Removed: `startYear` (Integer) - No longer accepts custom start year

**New behavior:**
- Automatically includes ALL sites belonging to the authenticated user
- Always simulates full year range: 2020-2100

### Request Format

**BEFORE:**
```json
{
  "scenario": "SSP2-4.5",
  "hazardType": "극심한 고온",
  "siteIds": ["3fa85f64-5717-4562-b3fc-2c963f66afa6", "..."],  // REMOVED
  "startYear": 2024  // REMOVED
}
```

**AFTER:**
```json
{
  "scenario": "SSP2-4.5",
  "hazardType": "극심한 고온"
}
```

### Response Format
**No changes** - Response format remains identical:
```json
{
  "scenario": "SSP2-4.5",
  "riskType": "극심한 고온",
  "yearlyData": [
    {
      "year": 2030,
      "nationalAverageTemperature": 14.5,
      "sites": [
        {
          "siteId": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
          "siteName": "서울 본사",
          "riskScore": 75,
          "localAverageTemperature": 15.2
        }
      ]
    }
    // ... years 2020 to 2100
  ]
}
```

### Spring Boot Implementation Changes

**Request Building:**
```java
// Spring Boot will now send to FastAPI:
{
  "scenario": "SSP2-4.5",
  "hazardType": "극심한 고온",
  "siteIds": ["uuid1", "uuid2", "..."],  // All user's sites from DB
  "startYear": 2020  // Fixed to 2020
}
```

**Flow:**
1. Spring Boot receives request with only `scenario` and `hazardType`
2. Spring Boot fetches ALL sites for authenticated user from database
3. Spring Boot builds FastAPI request with all site IDs and startYear=2020
4. Calls FastAPI endpoint
5. Returns complete response to client

### Impact on FastAPI

**Critical Questions for FastAPI Team:**

1. **Site Count Limit**: Does FastAPI have a limit on number of sites in `siteIds` array?
   - What's the maximum number of sites that can be processed in one request?
   - If limited, should we implement pagination or batching?

2. **Year Range Performance**: Can FastAPI efficiently handle 2020-2100 (81 years) for multiple sites?
   - Is there a performance concern with this range?
   - Should we consider chunking the year range?

3. **Response Size**: With all sites and all years, response size will be large
   - Is there a response size limit?
   - Should we implement pagination for the response?

4. **Existing Behavior**: Does FastAPI currently support:
   - Multiple site IDs in `siteIds` array? ✅ Assumed yes
   - `startYear` parameter? ✅ Assumed yes
   - Returning data up to year 2100? ✅ Assumed yes

**No immediate changes needed from FastAPI** - The endpoint signature remains the same. However, expect:
- Larger `siteIds` arrays (all user sites, not just selected)
- Always `startYear: 2020`
- More data to process per request

**Recommended FastAPI Actions:**
1. ✅ Test with multiple sites (5, 10, 20+ sites)
2. ✅ Verify performance with full year range 2020-2100
3. ✅ Monitor response times and memory usage
4. ✅ Consider implementing response caching if needed

---

## 5. Additional Data Management API (Previously Implemented)

### Endpoints
- `POST /api/sites/{siteId}/additional-data` - Upload additional data
- `GET /api/sites/{siteId}/additional-data?dataCategory={category}` - Get additional data
- `DELETE /api/sites/{siteId}/additional-data/{dataId}` - Delete additional data
- `GET /api/sites/{siteId}/additional-data/{dataId}/structured` - Get structured data

### Status
✅ **Already implemented** - These endpoints are now active and call FastAPI.

### FastAPI Endpoints Used
- `POST /api/sites/{siteId}/additional-data`
- `GET /api/sites/{siteId}/additional-data`
- `DELETE /api/sites/{siteId}/additional-data/{dataId}`
- `GET /api/sites/{siteId}/additional-data/{dataId}/structured`

### Data Categories Supported
- `building` - 건물 정보
- `asset` - 자산 정보
- `power` - 전력 사용량
- `insurance` - 보험 정보
- `custom` - 사용자 정의

**Verify these endpoints are implemented on FastAPI side.**

---

## 6. Disaster History API (Previously Implemented)

### Endpoint
`GET /api/disaster-history`

### Query Parameters
- `adminCode` (optional): 행정구역 코드
- `year` (optional): 연도
- `disasterType` (optional): 재해 유형
- `page` (optional, default=1): 페이지 번호
- `pageSize` (optional, default=20): 페이지당 개수

### Status
✅ **Already implemented** - This endpoint calls FastAPI.

### FastAPI Endpoint Used
`GET /api/disaster-history`

**Verify this endpoint returns paginated disaster yearbook data.**

---

## 7. Recommendation Batch API (Previously Implemented)

### Endpoints
- `POST /api/recommendation` - Start recommendation batch
- `GET /api/recommendation/{batchJobId}/progress` - Get batch progress
- `GET /api/recommendation/{batchJobId}/result` - Get recommendation results

### Status
✅ **Already implemented** - These endpoints call FastAPI.

### FastAPI Endpoints Used
- `POST /api/recommendation`
- `GET /api/recommendation/{batchJobId}/progress`
- `GET /api/recommendation/{batchJobId}/result`

**Verify batch job processing is implemented on FastAPI side.**

---

## Testing Recommendations

### For FastAPI Team

1. **SSP3-7.0 Support**
   - Test all analysis and simulation endpoints with `scenario: "SSP3-7.0"`
   - Verify data availability for this scenario

2. **Climate Simulation Stress Test**
   - Test with 10+ sites in `siteIds` array
   - Test with `startYear: 2020` and verify 2020-2100 range
   - Measure response time and size

3. **Dashboard Coordinates (Optional)**
   - Consider adding latitude/longitude to dashboard response
   - Would eliminate extra Spring Boot database query

4. **New Endpoints Verification**
   - Additional Data Management (4 endpoints)
   - Disaster History (1 endpoint)
   - Recommendation Batch (3 endpoints)

---

## Contact Information

For questions or coordination:
- **Spring Boot Team**: SKAX Backend Team
- **This Document**: `docs/API_CHANGES_FOR_FASTAPI.md`
- **Date**: 2025-12-09

---

## Appendix: Complete SSP Scenarios List

Current supported scenarios (4 total):
1. **SSP1-2.6** - Sustainability
2. **SSP2-4.5** - Middle of the Road
3. **SSP3-7.0** - Regional Rivalry (NEW)
4. **SSP5-8.5** - Fossil-fueled Development

Excluded:
- ~~SSP4-6.0~~ - Inequality (deliberately excluded)

---

## Appendix: Data Types Reference

### Coordinate Types
- **latitude**: BigDecimal (precision=10, scale=8)
  - Example: `37.36633726`
  - Range: -90.00000000 to 90.00000000
- **longitude**: BigDecimal (precision=11, scale=8)
  - Example: `127.10661717`
  - Range: -180.00000000 to 180.00000000

### UUID Format
- Standard UUID v4 format
- Example: `3fa85f64-5717-4562-b3fc-2c963f66afa6`

### Date/Time Format
- ISO 8601 format: `2025-12-09T12:00:00`
- Timezone: UTC (unless specified otherwise)
