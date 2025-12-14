좋습니다! DB 스키마 추가가 필요한 항목들을 정리한 문서를 작성하겠습니다.

````markdown
# 건축물 대장 집계 데이터 DB 스키마 제안서

> 작성일: 2025-12-11  
> 작성자: AI Agent Team  
> 관련 이슈: #68

---

## 📋 목차

1. [배경](#배경)
2. [현재 상황 분석](#현재-상황-분석)
3. [추가 필요 항목](#추가-필요-항목)
4. [제안 스키마](#제안-스키마)
5. [구현 계획](#구현-계획)

---

## 배경

### 문제 상황

- 건축물 취약성 분석 시 **건축물 대장 API**를 실시간 호출 중
- 하나의 번지(예: 원촌동 140-1)에 **80개 이상의 건물**이 존재
- API 호출 시간: 약 5~10초 (5개 엔드포인트 × 평균 1~2초)
- **중복 호출 방지 메커니즘 부재** → 같은 주소 재분석 시 매번 API 호출

### 해결 목표

1. **캐싱**: 번지 단위 건물 데이터를 DB에 저장하여 재사용
2. **성능 향상**: API 호출 시간 5~10초 → DB 조회 0.1초 이하
3. **비용 절감**: 공공데이터 API 트래픽 감소

---

## 현재 상황 분석

### ✅ 기존 Datawarehouse 테이블

#### 1. `api_buildings` (단일 건물 정보)

```sql
CREATE TABLE api_buildings (
  building_id UUID PRIMARY KEY,
  mgm_bldrgst_pk VARCHAR(50) UNIQUE,
  sigungu_cd VARCHAR(10),
  bjdong_cd VARCHAR(10),
  bun VARCHAR(10),
  ji VARCHAR(10),
  -- ... 단일 건물 상세 정보
  created_at TIMESTAMP DEFAULT NOW()
);
```
````

**한계점:**

- ❌ **단일 건물 기준** 설계 (1 row = 1 building)
- ❌ 번지 단위 집계 데이터 미지원
- ❌ 80개 건물 → 80개 row 생성 필요 (비효율)

#### 2. `site_additional_data` (사용자 추가 데이터)

```sql
CREATE TABLE site_additional_data (
  id UUID PRIMARY KEY,
  site_id UUID REFERENCES sites(site_id),
  data_category VARCHAR(50),
  structured_data JSONB,
  uploaded_at TIMESTAMP DEFAULT NOW()
);
```

**가능성:**

- ✅ JSONB로 유연한 구조 저장 가능
- ❌ **site_id 의존** → 번지 단위 캐싱 불가
- ❌ 인덱싱 어려움 (sigungu_cd, bjdong_cd 기반 조회 느림)

---

## 추가 필요 항목

### 📦 우리가 구현한 집계 데이터 구조

현재 `BuildingDataFetcher.fetch_full_tcfd_data()` 반환값:

```python
{
  "meta": {
    "building_count": 80,                    # ⭐ 필수
    "address": "대전광역시 유성구 원촌동 140-1",
    "road_address": "대전광역시 유성구 엑스포로 325",
    "sigungu_cd": "30200",                   # ⭐ 필수 (인덱싱)
    "bjdong_cd": "14200",                    # ⭐ 필수 (인덱싱)
    "bun": "0140",                           # ⭐ 필수 (고유키)
    "ji": "0001"                             # ⭐ 필수 (고유키)
  },
  "physical_specs": {
    "structure_types": [                     # ⭐ 필수
      "철근콘크리트구조",
      "철골구조",
      ...
    ],
    "purpose_types": ["교육연구시설", ...],  # ⭐ 필수
    "floors": {
      "max_ground": 7,                       # ⭐ 필수
      "max_underground": 1,                  # ⭐ 필수
      "min_underground": 1                   # ⭐ 필수
    },
    "seismic": {
      "buildings_with_design": 24,           # ⭐ 필수
      "buildings_without_design": 56         # ⭐ 필수
    },
    "age": {
      "oldest_approval_date": "19970902",    # ⭐ 필수
      "newest_approval_date": "20231026",
      "years": 28
    }
  },
  "transition_specs": {
    "total_area": 181238.45,                 # ⭐ 필수
    "total_building_area": 145000.00
  },
  "floor_details": [                         # ⭐ 필수 (샘플)
    {
      "floor_number": "지하1층",
      "floor_type": "지하",
      "area": 1234.5,
      "usage_main": "주차장",
      ...
    },
    // ... 최대 100개
  ]
}
```

### 🔴 DB에 없는 필수 항목

| 항목                         | 현재 상태 | 필요 이유                               |
| ---------------------------- | --------- | --------------------------------------- |
| **번지 단위 집계**           | ❌ 없음   | 80개 건물을 하나의 row로 저장           |
| **건물 수 (building_count)** | ❌ 없음   | 다중 건물 규모 파악                     |
| **구조 종류 배열**           | ❌ 없음   | 취약성 분석 핵심 (철근콘크리트 vs 목조) |
| **용도 종류 배열**           | ❌ 없음   | 중요시설 식별 (데이터센터, 제조시설 등) |
| **내진설계 집계**            | ❌ 없음   | 지진 리스크 평가 핵심                   |
| **층별 용도 종류**           | ❌ 없음   | 지하 중요설비 리스크 평가               |
| **API 호출 메타데이터**      | ❌ 없음   | 캐시 유효성 판단, 비용 추적             |

---

## 제안 스키마

### 🎯 Option 1: 전용 테이블 생성 (추천 ⭐⭐⭐)

```sql
-- ================================================================
-- 건축물 대장 집계 캐시 테이블
-- ================================================================
CREATE TABLE building_aggregate_cache (
  -- 기본키
  cache_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

  -- ================================================================
  -- 위치 식별자 (고유키)
  -- ================================================================
  sigungu_cd VARCHAR(10) NOT NULL,          -- 시군구코드
  bjdong_cd VARCHAR(10) NOT NULL,           -- 법정동코드
  bun VARCHAR(10) NOT NULL,                 -- 번 (4자리, 예: "0140")
  ji VARCHAR(10) NOT NULL,                  -- 지 (4자리, 예: "0001")

  -- ================================================================
  -- 주소 정보
  -- ================================================================
  jibun_address VARCHAR(500),               -- 지번 주소
  road_address VARCHAR(500),                -- 도로명 주소

  -- ================================================================
  -- 집계 데이터 (핵심)
  -- ================================================================
  building_count INTEGER NOT NULL,          -- 해당 번지의 총 건물 수

  -- 구조 및 용도 (배열 → JSONB)
  structure_types JSONB,                    -- ["철근콘크리트구조", "철골구조", ...]
  purpose_types JSONB,                      -- ["교육연구시설", "업무시설", ...]

  -- 층수 정보
  max_ground_floors INTEGER,                -- 최대 지상 층수
  max_underground_floors INTEGER,           -- 최대 지하 층수
  min_underground_floors INTEGER,           -- 최저 지하 층수 (절대값)

  -- 내진설계 집계
  buildings_with_seismic INTEGER,           -- 내진설계 적용 건물 수
  buildings_without_seismic INTEGER,        -- 내진설계 미적용 건물 수

  -- 연식 정보
  oldest_approval_date DATE,                -- 가장 오래된 건물 사용승인일
  newest_approval_date DATE,                -- 가장 최근 건물 사용승인일
  oldest_building_age_years INTEGER,        -- 가장 오래된 건물 연식

  -- 면적 정보
  total_floor_area_sqm NUMERIC(15,2),      -- 총 연면적 (m²)
  total_building_area_sqm NUMERIC(15,2),   -- 총 건축면적 (m²)

  -- ================================================================
  -- 층별 상세 정보 (샘플, 최대 100개)
  -- ================================================================
  floor_details JSONB,                      -- 층별 정보 배열
  floor_purpose_types JSONB,                -- 층별 용도 종류 (중복 제거)

  -- ================================================================
  -- 메타데이터
  -- ================================================================
  cached_at TIMESTAMP DEFAULT NOW(),        -- 캐시 생성 시간
  updated_at TIMESTAMP,                     -- 캐시 갱신 시간
  api_call_count INTEGER DEFAULT 0,         -- API 호출 횟수 (비용 추적)
  data_quality_score NUMERIC(3,2),          -- 데이터 품질 점수 (0~1)

  -- ================================================================
  -- 제약 조건
  -- ================================================================
  CONSTRAINT uk_building_aggregate
    UNIQUE(sigungu_cd, bjdong_cd, bun, ji),

  CONSTRAINT chk_building_count
    CHECK (building_count > 0),

  CONSTRAINT chk_data_quality
    CHECK (data_quality_score >= 0 AND data_quality_score <= 1)
);

-- ================================================================
-- 인덱스
-- ================================================================
-- 위치 기반 조회 (가장 빈번)
CREATE INDEX idx_building_agg_location
  ON building_aggregate_cache(sigungu_cd, bjdong_cd, bun, ji);

-- 캐시 유효성 판단 (24시간 이내)
CREATE INDEX idx_building_agg_cached_at
  ON building_aggregate_cache(cached_at DESC);

-- 지역별 통계 조회
CREATE INDEX idx_building_agg_region
  ON building_aggregate_cache(sigungu_cd, bjdong_cd);

-- ================================================================
-- 코멘트
-- ================================================================
COMMENT ON TABLE building_aggregate_cache IS
  '건축물 대장 API 집계 데이터 캐시 (번지 단위)';

COMMENT ON COLUMN building_aggregate_cache.building_count IS
  '해당 번지에 속한 총 건물 수';

COMMENT ON COLUMN building_aggregate_cache.structure_types IS
  '건물 구조 종류 배열 (JSON): ["철근콘크리트구조", "철골구조"]';

COMMENT ON COLUMN building_aggregate_cache.floor_details IS
  '층별 정보 샘플 (JSON): 최대 100개 층 데이터';

COMMENT ON COLUMN building_aggregate_cache.api_call_count IS
  'API 호출 횟수 (비용 추적 및 캐시 효율 분석용)';
```

### 📊 JSONB 컬럼 상세 구조

#### `structure_types` (구조 종류)

```json
["철근콘크리트구조", "철골구조", "철골철근콘크리트구조"]
```

#### `purpose_types` (용도 종류)

```json
["교육연구시설", "업무시설", "창고시설"]
```

#### `floor_details` (층별 정보, 최대 100개)

```json
[
  {
    "floor_number": "지하1층",
    "floor_type": "지하",
    "area_sqm": 1234.5,
    "usage_main": "주차장",
    "usage_etc": "기계실",
    "structure": "철근콘크리트구조"
  },
  {
    "floor_number": "1층",
    "floor_type": "지상",
    "area_sqm": 2500.0,
    "usage_main": "업무시설",
    "usage_etc": null,
    "structure": "철근콘크리트구조"
  }
  // ... 최대 100개
]
```

#### `floor_purpose_types` (층별 용도 종류, 중복 제거)

```json
["주차장", "업무시설", "교육연구시설", "기계실", "창고시설"]
```

---

### 🔄 Option 2: `site_additional_data` 활용 (임시 방안)

**변경 없이 기존 테이블 활용:**

```python
# 저장
{
  "site_id": "uuid",
  "data_category": "building_aggregate_cache",
  "structured_data": {
    "building_count": 80,
    "structure_types": [...],
    "seismic": {
      "buildings_with_design": 24,
      "buildings_without_design": 56
    },
    # ... 위 스키마와 동일
  },
  "uploaded_at": "2025-12-11T10:00:00Z"
}
```

**단점:**

- ❌ `site_id` 의존 → 번지 단위 캐싱 불가
- ❌ 인덱싱 어려움 (sigungu_cd로 빠른 조회 불가)
- ❌ 쿼리 복잡도 증가 (JSONB 내부 필드 검색)

---

## 구현 계획

### Phase 1: DB 스키마 생성 (DB 팀)

**담당:** DB 팀  
**기간:** 1일  
**작업:**

1. `datawarehouse` 데이터베이스에 `building_aggregate_cache` 테이블 생성
2. 인덱스 생성 (location, cached_at, region)
3. 제약 조건 설정 (UNIQUE, CHECK)

**SQL 스크립트:**

```bash
# Datawarehouse DB 접속
psql -h <GCP_SQL_HOST> -U <DB_USER> -d datawarehouse

# 스키마 생성 실행
\i building_aggregate_cache_schema.sql
```

---

### Phase 2: 캐싱 로직 구현 (AI Agent 팀)

**담당:** AI Agent 팀  
**기간:** 2일  
**작업:**

#### 2-1. Database 모듈 확장 ([`ai_agent/utils/database.py`](ai_agent/utils/database.py))

```python
class DatabaseClient:
    # ... 기존 코드 ...

    async def get_building_cache(
        self,
        sigungu_cd: str,
        bjdong_cd: str,
        bun: str,
        ji: str,
        max_age_hours: int = 24
    ) -> Optional[Dict]:
        """건축물 집계 캐시 조회 (24시간 이내)"""
        query = """
        SELECT * FROM building_aggregate_cache
        WHERE sigungu_cd = %s
          AND bjdong_cd = %s
          AND bun = %s
          AND ji = %s
          AND cached_at > NOW() - INTERVAL '%s hours'
        ORDER BY cached_at DESC
        LIMIT 1
        """
        result = await self.fetch_one(
            query,
            (sigungu_cd, bjdong_cd, bun, ji, max_age_hours)
        )
        return dict(result) if result else None

    async def save_building_cache(
        self,
        cache_data: Dict
    ) -> str:
        """건축물 집계 캐시 저장 (UPSERT)"""
        query = """
        INSERT INTO building_aggregate_cache (
          sigungu_cd, bjdong_cd, bun, ji,
          jibun_address, road_address,
          building_count, structure_types, purpose_types,
          max_ground_floors, max_underground_floors, min_underground_floors,
          buildings_with_seismic, buildings_without_seismic,
          oldest_approval_date, newest_approval_date, oldest_building_age_years,
          total_floor_area_sqm, total_building_area_sqm,
          floor_details, floor_purpose_types,
          api_call_count, data_quality_score
        ) VALUES (
          %(sigungu_cd)s, %(bjdong_cd)s, %(bun)s, %(ji)s,
          %(jibun_address)s, %(road_address)s,
          %(building_count)s, %(structure_types)s, %(purpose_types)s,
          %(max_ground_floors)s, %(max_underground_floors)s, %(min_underground_floors)s,
          %(buildings_with_seismic)s, %(buildings_without_seismic)s,
          %(oldest_approval_date)s, %(newest_approval_date)s, %(oldest_building_age_years)s,
          %(total_floor_area_sqm)s, %(total_building_area_sqm)s,
          %(floor_details)s, %(floor_purpose_types)s,
          %(api_call_count)s, %(data_quality_score)s
        )
        ON CONFLICT (sigungu_cd, bjdong_cd, bun, ji)
        DO UPDATE SET
          building_count = EXCLUDED.building_count,
          structure_types = EXCLUDED.structure_types,
          updated_at = NOW(),
          api_call_count = building_aggregate_cache.api_call_count + 1
        RETURNING cache_id
        """
        result = await self.fetch_one(query, cache_data)
        return str(result['cache_id'])
```

#### 2-2. BuildingDataFetcher 캐싱 로직 추가

```python
# ai_agent/utils/building_data_fetcher.py

from .database import DatabaseClient

class BuildingDataFetcher:
    def __init__(self):
        # ... 기존 코드 ...
        self.db_client = DatabaseClient()

    async def fetch_full_tcfd_data_with_cache(
        self,
        lat: float,
        lon: float,
        address: str = None,
        force_refresh: bool = False
    ) -> Dict[str, Any]:
        """
        건축물 집계 데이터 조회 (캐시 우선)

        Args:
            force_refresh: True면 캐시 무시하고 API 재호출
        """
        # 1. 주소 → 행정코드 변환
        if address:
            addr_result = self.search_address(address)
            if addr_result:
                codes = {
                    'sigungu_cd': addr_result['sigungu_cd'],
                    'bjdong_cd': addr_result['bjdong_cd']
                }
                bun = addr_result['bun'].zfill(4)
                ji = addr_result['ji'].zfill(4)
        else:
            # 좌표 → 주소 변환
            addr_info = self._get_address_from_vworld(lat, lon)
            codes = {
                'sigungu_cd': addr_info['sigungu_cd'],
                'bjdong_cd': addr_info['bjdong_cd']
            }
            bun = addr_info['bun']
            ji = addr_info['ji']

        # 2. 캐시 조회 (force_refresh가 False일 때만)
        if not force_refresh:
            cached = await self.db_client.get_building_cache(
                codes['sigungu_cd'],
                codes['bjdong_cd'],
                bun,
                ji,
                max_age_hours=24  # 24시간 유효
            )
            if cached:
                logger.info(f"✅ 캐시 적중: {codes['sigungu_cd']}-{codes['bjdong_cd']} {bun}-{ji}")
                return self._convert_cache_to_tcfd_format(cached)

        # 3. 캐시 미스 → API 호출
        logger.info(f"🔄 API 호출: {codes['sigungu_cd']}-{codes['bjdong_cd']} {bun}-{ji}")
        tcfd_data = self.fetch_full_tcfd_data(lat, lon, address)

        # 4. 캐시 저장
        cache_data = self._convert_tcfd_to_cache_format(tcfd_data, codes, bun, ji)
        await self.db_client.save_building_cache(cache_data)

        return tcfd_data

    def _convert_tcfd_to_cache_format(
        self,
        tcfd_data: Dict,
        codes: Dict,
        bun: str,
        ji: str
    ) -> Dict:
        """TCFD 데이터 → 캐시 DB 형식 변환"""
        meta = tcfd_data.get('meta', {})
        physical = tcfd_data.get('physical_specs', {})
        transition = tcfd_data.get('transition_specs', {})
        floors = tcfd_data.get('floor_details', [])

        return {
            'sigungu_cd': codes['sigungu_cd'],
            'bjdong_cd': codes['bjdong_cd'],
            'bun': bun,
            'ji': ji,
            'jibun_address': meta.get('address'),
            'road_address': meta.get('road_address'),
            'building_count': meta.get('building_count', 0),
            'structure_types': json.dumps(physical.get('structure_types', []), ensure_ascii=False),
            'purpose_types': json.dumps(physical.get('purpose_types', []), ensure_ascii=False),
            'max_ground_floors': physical.get('floors', {}).get('max_ground', 0),
            'max_underground_floors': physical.get('floors', {}).get('max_underground', 0),
            'min_underground_floors': physical.get('floors', {}).get('min_underground', 0),
            'buildings_with_seismic': physical.get('seismic', {}).get('buildings_with_design', 0),
            'buildings_without_seismic': physical.get('seismic', {}).get('buildings_without_design', 0),
            'oldest_approval_date': physical.get('age', {}).get('oldest_approval_date'),
            'newest_approval_date': physical.get('age', {}).get('newest_approval_date'),
            'oldest_building_age_years': physical.get('age', {}).get('years', 0),
            'total_floor_area_sqm': transition.get('total_area', 0),
            'total_building_area_sqm': transition.get('total_building_area', 0),
            'floor_details': json.dumps(floors[:100], ensure_ascii=False),  # 최대 100개
            'floor_purpose_types': json.dumps(
                list(set([f.get('usage_main') for f in floors if f.get('usage_main')])),
                ensure_ascii=False
            ),
            'api_call_count': 1,
            'data_quality_score': 1.0  # TODO: 품질 점수 계산 로직
        }
```

---

### Phase 3: 테스트 및 검증

**담당:** AI Agent 팀  
**기간:** 1일

#### 3-1. 단위 테스트

```python
# tests/test_building_cache.py

async def test_building_cache_hit():
    """캐시 적중 테스트"""
    fetcher = BuildingDataFetcher()

    # 1차 호출 (API)
    data1 = await fetcher.fetch_full_tcfd_data_with_cache(
        lat=36.3723,
        lon=127.3844
    )

    # 2차 호출 (캐시)
    data2 = await fetcher.fetch_full_tcfd_data_with_cache(
        lat=36.3723,
        lon=127.3844
    )

    assert data1 == data2  # 데이터 일치
    # TODO: API 호출 횟수 검증 (1회만)

async def test_cache_expiration():
    """캐시 만료 테스트 (24시간 후)"""
    # TODO: 시간 조작 라이브러리 (freezegun) 사용
```

#### 3-2. 통합 테스트

```bash
# 실제 주소로 테스트
python test_vulnerability_system.py
```

---

### Phase 4: 모니터링 및 최적화

**담당:** AI Agent 팀 + DevOps  
**기간:** 지속적

#### 4-1. 캐시 효율 모니터링 쿼리

```sql
-- 캐시 적중률
SELECT
  COUNT(*) as total_cached,
  AVG(api_call_count) as avg_api_calls_per_cache,
  SUM(api_call_count) as total_api_calls_saved
FROM building_aggregate_cache;

-- 지역별 캐시 현황
SELECT
  sigungu_cd,
  COUNT(*) as cache_count,
  AVG(building_count) as avg_buildings_per_lot,
  MAX(cached_at) as last_cached
FROM building_aggregate_cache
GROUP BY sigungu_cd
ORDER BY cache_count DESC
LIMIT 10;

-- 만료 임박 캐시 (재갱신 필요)
SELECT
  jibun_address,
  building_count,
  cached_at,
  NOW() - cached_at as age
FROM building_aggregate_cache
WHERE cached_at < NOW() - INTERVAL '20 hours'
ORDER BY cached_at ASC
LIMIT 20;
```

#### 4-2. 성능 지표

| 지표              | 목표    | 측정 방법                  |
| ----------------- | ------- | -------------------------- |
| **캐시 적중률**   | > 80%   | `api_call_count` 분석      |
| **조회 속도**     | < 100ms | DB 쿼리 실행 계획          |
| **API 호출 감소** | > 70%   | 로그 분석                  |
| **저장소 사용량** | < 1GB   | `pg_total_relation_size()` |

---

## 비교 분석

### Option 1 vs Option 2

| 항목            | Option 1 (전용 테이블)         | Option 2 (site_additional_data) |
| --------------- | ------------------------------ | ------------------------------- |
| **구현 복잡도** | 중간 (새 테이블 생성 필요)     | 낮음 (기존 테이블 활용)         |
| **쿼리 성능**   | ⭐⭐⭐ (인덱스 최적화)         | ⭐ (JSONB 검색 느림)            |
| **캐시 효율**   | ⭐⭐⭐ (번지 단위)             | ⭐⭐ (site 단위)                |
| **확장성**      | ⭐⭐⭐                         | ⭐⭐                            |
| **유지보수**    | ⭐⭐⭐ (명확한 스키마)         | ⭐⭐ (JSONB 구조 파악 어려움)   |
| **재사용성**    | ⭐⭐⭐ (다른 서비스 활용 가능) | ⭐ (site_id 의존)               |

---

## 마이그레이션 계획

### 기존 데이터 이전 (Optional)

`api_buildings` 테이블에 이미 데이터가 있다면:

```sql
-- 번지별로 집계하여 새 테이블에 삽입
INSERT INTO building_aggregate_cache (
  sigungu_cd, bjdong_cd, bun, ji,
  building_count,
  structure_types,
  purpose_types,
  max_ground_floors,
  max_underground_floors,
  -- ...
)
SELECT
  sigungu_cd,
  bjdong_cd,
  bun,
  ji,
  COUNT(*) as building_count,
  jsonb_agg(DISTINCT structure_cd) as structure_types,
  jsonb_agg(DISTINCT main_purps_cd) as purpose_types,
  MAX(grnd_flr_cnt) as max_ground_floors,
  MAX(ugrnd_flr_cnt) as max_underground_floors
  -- ...
FROM api_buildings
GROUP BY sigungu_cd, bjdong_cd, bun, ji;
```

---

## 보안 고려사항

### 1. 개인정보 미포함 확인

- ✅ 건축물 대장은 공공데이터 (개인정보 없음)
- ✅ 주소, 구조, 용도만 저장 (소유자, 거주자 정보 제외)

### 2. 접근 제어

```sql
-- 읽기 전용 계산 서비스 계정
GRANT SELECT ON building_aggregate_cache TO modelops_service;

-- 쓰기 권한은 AI Agent만
GRANT INSERT, UPDATE ON building_aggregate_cache TO ai_agent_service;
```

---

## 예상 효과

### 성능 개선

- ⏱️ **API 호출 시간 감소**: 5~10초 → 0.1초 (50~100배 향상)
- 💰 **API 비용 절감**: 중복 호출 70% 감소 (캐시 적중률 80% 가정)
- 📊 **동시 처리 능력 향상**: API 병목 제거로 TPS 증가

### 데이터 품질

- 🔄 **일관성**: 같은 주소는 항상 같은 데이터 반환
- 📈 **추적성**: `api_call_count`로 데이터 사용 빈도 파악
- 🛡️ **안정성**: API 장애 시에도 캐시로 서비스 가능

---

## 다음 단계

### 즉시 실행

1. [ ] DB 팀에 스키마 생성 요청 (Slack: `#db-team`)
2. [ ] 스키마 생성 SQL 스크립트 전달
3. [ ] 테스트 환경 (Dev DB)에서 먼저 검증

### 병행 작업

1. [ ] `database.py` 모듈 확장 (캐싱 메서드 추가)
2. [ ] `building_data_fetcher.py` 캐싱 로직 구현
3. [ ] 단위 테스트 작성

### 배포 후

1. [ ] 프로덕션 환경 배포
2. [ ] 캐시 적중률 모니터링 (1주일)
3. [ ] 성능 지표 리포트 작성

---

## 참고 자료

- 건축물 대장 API 문서
- 현재 ERD
- [이슈 #68](https://github.com/On-Do-Polaris/polaris_backend_fastapi/issues/68)

````

문서 생성 완료했습니다! 이제 이 문서를 저장하고 커밋하시겠습니까?

```bash
# 문서 커밋
git add docs/planning/building_aggregate_db_schema_proposal.md
git commit -m "[add] building_aggregate_db_schema_proposal_건축물집계데이터DB스키마제안서작성"
````
