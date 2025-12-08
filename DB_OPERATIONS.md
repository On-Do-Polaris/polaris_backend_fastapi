# 데이터베이스 작업 정리 (ERD v03)

## 📊 개요

현재 API에서 데이터베이스 작업은 **PostgreSQL 데이터웨어하우스** (포트 **5432**)를 대상으로 하며, 주로 **기후 데이터 조회**에 사용됩니다.

- **ERD 버전**: v03 (2025-12-03)
- **데이터 형식**: Wide Format (ssp1, ssp2, ssp3, ssp5 컬럼)
- **총 테이블 수**: 45개
- **작업 범위**: 조회(SELECT) 전용 (저장은 ModelOps 담당)

---

## 🔌 데이터베이스 연결

### DatabaseManager 클래스
**위치**: `ai_agent/utils/database.py`

**초기화**:
```python
from ai_agent.utils.database import DatabaseManager

db = DatabaseManager()  # DATABASE_URL 환경변수 사용
# 또는
db = DatabaseManager(database_url="postgresql://user:pass@host:port/dbname")
```

**연결 정보**:
- 환경변수: `DATABASE_URL`
- 데이터베이스: `skala_datawarehouse`
- 포트: **5432** (PostgreSQL 기본 포트)
- 라이브러리: `psycopg2`
- 커서 타입: `RealDictCursor` (결과를 딕셔너리로 반환)

---

## 📖 데이터 조회 (SELECT)

### 1. 위치 정보 조회

#### 1.1 가장 가까운 기후 그리드 포인트 찾기
```python
grid_info = db.find_nearest_grid(
    latitude=37.5665,
    longitude=126.9780
)
# 반환: {'grid_id': 123, 'longitude': 126.975, 'latitude': 37.565, 'distance_meters': 150.5}
```

**쿼리 대상 테이블**: `location_grid`
**기능**: PostGIS를 사용한 공간 거리 계산

#### 1.2 행정구역 정보 조회 (코드 기반)
```python
admin_info = db.find_admin_by_code(admin_code="1101010100")
# 반환: {'admin_id', 'admin_code', 'admin_name', 'sido_code', 'sigungu_code', 'emd_code',
#        'level', 'population_2020', 'population_2050'}
```

**쿼리 대상 테이블**: `location_admin`

#### 1.3 행정구역 정보 조회 (좌표 기반)
```python
admin_info = db.find_admin_by_coords(
    latitude=37.5665,
    longitude=126.9780
)
```

**쿼리 대상 테이블**: `location_admin`
**기능**: PostGIS `ST_Contains`를 사용한 공간 포함 검사

---

### 2. 월별 기후 데이터 조회

#### 2.1 그리드 기반 월별 데이터 (Wide Format - ERD v03)
```python
monthly_data = db.fetch_monthly_grid_data(
    grid_id=123,
    start_date="2020-01-01",
    end_date="2023-12-31",
    scenario='ssp2',  # 'ssp1', 'ssp2', 'ssp3', 'ssp5' 또는 None (전체)
    variables=['ta', 'rn', 'ws', 'rhm', 'si', 'spei12']
)
# scenario='ssp2' 지정 시:
# {
#   'ta': [{'observation_date': '2020-01-01', 'ssp2': 15.5}, ...],
#   'rn': [{'observation_date': '2020-01-01', 'ssp2': 50.2}, ...],
# }
#
# scenario=None (전체 시나리오):
# {
#   'ta': [{'observation_date': '2020-01-01', 'ssp1': 14.5, 'ssp2': 15.5, 'ssp3': 16.0, 'ssp5': 16.5}, ...],
#   'rn': [{'observation_date': '2020-01-01', 'ssp1': 48.0, 'ssp2': 50.2, 'ssp3': 52.0, 'ssp5': 54.0}, ...],
# }
```

**쿼리 대상 테이블**:
- `ta_data` - 평균기온 (°C)
- `rn_data` - 강수량 (mm)
- `ws_data` - 풍속 (m/s)
- `rhm_data` - 상대습도 (%)
- `si_data` - 일사량 (MJ/m²)
- `spei12_data` - SPEI-12 가뭄지수

**스키마 (ERD v03)**:
```sql
-- 모든 월별 테이블 공통 구조
grid_id integer
observation_date date
ssp1 real  -- SSP1-2.6
ssp2 real  -- SSP2-4.5
ssp3 real  -- SSP3-7.0
ssp5 real  -- SSP5-8.5
```

---

### 3. 일별 기후 데이터 조회

#### 3.1 행정구역 기반 일별 데이터 (Wide Format)
```python
daily_data = db.fetch_daily_admin_data(
    admin_id=456,
    start_date="2020-01-01",
    end_date="2023-12-31",
    variables=['tamax', 'tamin']
)
# 반환: {
#   'tamax': [
#     {'time': '2020-01-01', 'ssp1': 10.5, 'ssp2': 11.0, 'ssp3': 11.5, 'ssp5': 12.0},
#     ...
#   ],
#   'tamin': [...]
# }
```

**쿼리 대상 테이블**:
- `tamax_data` - 일 최고기온 (4개 SSP 시나리오 동시 제공)
- `tamin_data` - 일 최저기온 (4개 SSP 시나리오 동시 제공)

---

### 4. 연별 기후 지수 조회

#### 4.1 그리드 기반 연별 극값 지수 (Wide Format - ERD v03)
```python
yearly_data = db.fetch_yearly_grid_data(
    grid_id=123,
    start_year=2021,
    end_year=2100,
    scenario='ssp2',  # 'ssp1', 'ssp2', 'ssp3', 'ssp5' 또는 None (전체)
    variables=['csdi', 'wsdi', 'rx1day', 'rx5day', 'cdd', 'rain80', 'sdii', 'ta_yearly']
)
# scenario='ssp2' 지정 시:
# {
#   'wsdi': [{'year': 2021, 'ssp2': 5.2}, ...],
#   'rx1day': [{'year': 2021, 'ssp2': 120.5}, ...],
# }
#
# scenario=None (전체 시나리오):
# {
#   'wsdi': [{'year': 2021, 'ssp1': 4.5, 'ssp2': 5.2, 'ssp3': 6.0, 'ssp5': 6.8}, ...],
#   'rx1day': [{'year': 2021, 'ssp1': 115.0, 'ssp2': 120.5, 'ssp3': 125.0, 'ssp5': 130.0}, ...],
# }
```

**쿼리 대상 테이블**:
- `csdi_data` - 한랭야 계속기간 지수 (일)
- `wsdi_data` - 온난야 계속기간 지수 (일)
- `rx1day_data` - 1일 최다강수량 (mm)
- `rx5day_data` - 5일 최다강수량 (mm)
- `cdd_data` - 연속 무강수일 (일)
- `rain80_data` - 80mm 이상 강수일수 (일)
- `sdii_data` - 강수강도 (mm/일)
- `ta_yearly_data` - 연평균 기온 (°C)

**스키마 (ERD v03)**:
```sql
-- 모든 연별 테이블 공통 구조 (2021-2100)
grid_id integer
year integer
ssp1 real  -- SSP1-2.6
ssp2 real  -- SSP2-4.5
ssp3 real  -- SSP3-7.0
ssp5 real  -- SSP5-8.5
```

---

### 5. 해수면 상승 데이터 조회

#### 5.1 해안 지역 해수면 상승 데이터 (Wide Format - ERD v03)
```python
sea_level_data = db.fetch_sea_level_data(
    latitude=35.1796,
    longitude=129.0756,
    start_year=2015,
    end_year=2100,
    scenario='ssp2'  # 'ssp1', 'ssp2', 'ssp3', 'ssp5' 또는 None (전체)
)
# scenario='ssp2' 지정 시:
# [
#   {'year': 2015, 'sea_level_rise_cm': 5.2},
#   {'year': 2016, 'sea_level_rise_cm': 5.8},
#   ...
# ]
#
# scenario=None (전체 시나리오):
# [
#   {'year': 2015, 'ssp1': 4.5, 'ssp2': 5.2, 'ssp3': 5.8, 'ssp5': 6.5},
#   {'year': 2016, 'ssp1': 4.8, 'ssp2': 5.8, 'ssp3': 6.2, 'ssp5': 7.0},
#   ...
# ]
```

**쿼리 대상 테이블**:
- `sea_level_grid` - 해수면 격자점 (80 rows = 10 x 8)
- `sea_level_data` - 해수면 상승 데이터 (cm)

**스키마 (ERD v03)**:
```sql
-- sea_level_data (2015-2100, ~1,720 rows)
grid_id integer
year integer
ssp1 real  -- SSP1-2.6 해수면 상승 (cm)
ssp2 real  -- SSP2-4.5 해수면 상승 (cm)
ssp3 real  -- SSP3-7.0 해수면 상승 (cm)
ssp5 real  -- SSP5-8.5 해수면 상승 (cm)
```

---

### 6. 공간 분석 캐시 조회

#### 6.1 토지피복 분석 결과 조회
```python
landcover = db.fetch_spatial_landcover(site_id="uuid-string")
# 반환: {
#   'urban_ratio': 0.45, 'forest_ratio': 0.30, 'agriculture_ratio': 0.15,
#   'water_ratio': 0.05, 'grassland_ratio': 0.03, 'wetland_ratio': 0.01,
#   'barren_ratio': 0.01, 'landcover_year': 2020, 'analyzed_at': '2024-01-01',
#   'is_valid': True
# }
```

**쿼리 대상 테이블**: `spatial_landcover`

#### 6.2 DEM(수치표고모델) 분석 결과 조회
```python
dem = db.fetch_spatial_dem(site_id="uuid-string")
# 반환: {
#   'elevation_point': 50.5, 'elevation_mean': 55.2, 'elevation_min': 45.0, 'elevation_max': 65.0,
#   'slope_point': 5.2, 'slope_mean': 6.1, 'slope_max': 15.5,
#   'aspect_point': 180.0, 'aspect_dominant': 'S',
#   'terrain_class': 'gentle_slope', 'flood_risk_terrain': 'low',
#   'analyzed_at': '2024-01-01', 'is_valid': True
# }
```

**쿼리 대상 테이블**: `spatial_dem`

---

### 7. 외부 API 캐시 조회

#### 7.1 주변 병원 조회
```python
hospitals = db.fetch_nearby_hospitals(
    latitude=37.5665,
    longitude=126.9780,
    radius_km=5.0
)
# 반환: [
#   {'name': '서울대병원', 'address': '...', 'type': '종합병원',
#    'phone': '02-1234-5678', 'x_pos': 126.975, 'y_pos': 37.565,
#    'distance_meters': 1250.5},
#   ...
# ]
```

**쿼리 대상 테이블**: `api_hospitals`
**기능**: PostGIS `ST_DWithin`을 사용한 반경 검색

#### 7.2 대피소 정보 조회
```python
shelters = db.fetch_nearby_shelters(admin_code="11010")
# 반환: {
#   'region': '서울특별시', 'target_population': 500000,
#   'acceptance_rate': 85.5, 'total_shelter_capacity': 425000,
#   'government_shelters': 50, 'public_shelters': 120
# }
```

**쿼리 대상 테이블**: `api_shelters`

#### 7.3 태풍 경로 이력 조회
```python
typhoon_history = db.fetch_typhoon_history(
    latitude=35.1796,
    longitude=129.0756,
    radius_km=100.0,
    start_year=2000,
    end_year=2023
)
# 반환: [
#   {
#     'typhoon_year': 2023, 'typhoon_number': 6,
#     'typhoon_name_kr': '카눈', 'typhoon_name_en': 'Khanun',
#     'observation_time': '2023-08-09 12:00:00',
#     'latitude': 35.2, 'longitude': 129.1,
#     'central_pressure': 960, 'max_wind_speed': 40,
#     'typhoon_grade': 'strong', 'distance_meters': 15000.0
#   },
#   ...
# ]
```

**쿼리 대상 테이블**: `typhoon_besttrack`

---

## 💾 데이터 저장 (INSERT/UPDATE/DELETE)

### 현재 상태: **미구현**

현재 API에서는 **데이터 저장 작업이 구현되지 않았습니다**. 모든 DB 작업은 **조회(SELECT) 전용**입니다.

### 예외: Scratch Space 저장
실제 DB 저장 대신, **Scratch Space**에 임시 파일로 저장됩니다:

```python
from ai_agent.utils.scratch_manager import ScratchSpaceManager

scratch = ScratchSpaceManager(base_path="./scratch", default_ttl_hours=4)

# 세션 생성
session_id = scratch.create_session(ttl_hours=4, metadata={...})

# JSON 데이터 저장
scratch.save_data(session_id, 'climate_data.json', data, format='json')

# CSV 데이터 저장
scratch.save_data(session_id, 'results.csv', df, format='csv')
```

**TTL (Time-To-Live)**:
- 기본값: 4시간
- 자동 정리: 백그라운드 스케줄러가 주기적으로 만료된 세션 삭제
- 설정: `ai_agent/config/settings.yaml`의 `SCRATCH_SPACE.auto_cleanup_enabled`

---

## 🔄 실제 사용 흐름

### 1. AI Agent의 데이터 수집 과정

**DataCollectionAgent** (`ai_agent/agents/data_processing/data_collection_agent.py`):

```python
class DataCollectionAgent:
    def __init__(self):
        self.db_manager = DatabaseManager()  # DB 연결
        self.scratch_manager = ScratchSpaceManager()  # 임시 저장소

    def collect(self, target_location, analysis_params, session_id):
        # 1. 기후 데이터 조회 (DB)
        climate_data = self._collect_climate_data(target_location, analysis_params)

        # 2. Scratch에 저장 (파일 시스템)
        self.scratch_manager.save_data(session_id, 'climate_data.json', climate_data, format='json')

        # 3. 지리 데이터 조회 (DB)
        geographic_data = self._collect_geographic_data(target_location)
        self.scratch_manager.save_data(session_id, 'geographic_data.json', geographic_data, format='json')

        # 4. 역사적 재해 데이터 조회 (DB)
        historical_events = self._collect_historical_events(target_location, analysis_params)
        self.scratch_manager.save_data(session_id, 'historical_events.json', historical_events, format='json')

        # 5. SSP 시나리오 데이터 조회 (DB)
        ssp_data = self._collect_ssp_scenario_data(target_location, analysis_params)
        self.scratch_manager.save_data(session_id, 'ssp_scenarios.json', ssp_data, format='json')

        return {'status': 'success', 'session_id': session_id}
```

**특징**:
- ✅ DB에서 조회
- ✅ Scratch에 임시 저장 (TTL 4시간)
- ❌ DB에 저장하지 않음

---

### 2. 재해 이력 서비스 (Mock 데이터 사용 중)

**DisasterHistoryService** (`src/services/disaster_history_service.py`):

```python
class DisasterHistoryService:
    async def get_disaster_history(self, filters):
        if settings.USE_MOCK_DATA:
            return self._get_mock_disaster_history(filters)

        # TODO: 실제 DB 쿼리 구현 예정
        raise NotImplementedError("DB connection not implemented yet")
```

**현재 상태**:
- ❌ DB 연결 미구현
- ✅ Mock 데이터로 대체
- 📝 TODO 주석으로 향후 구현 계획 명시

**쿼리 예정 테이블**: `disaster_history` (아직 생성되지 않음)

---

## 📊 데이터베이스 스키마 요약 (ERD v03)

### 조회 가능한 테이블

| 카테고리 | 테이블 이름 | 설명 | 데이터 형식 (ERD v03) | 행 수 |
|---------|-----------|------|---------------------|------|
| **위치** | `location_grid` | 기후 그리드 포인트 | PostGIS POINT | 451,351 |
| | `location_admin` | 행정구역 경계 (인구 포함) | PostGIS MULTIPOLYGON | 5,259 |
| | `sea_level_grid` | 해수면 격자점 | PostGIS POINT | 80 |
| **월별 데이터** | `ta_data` | 월평균 기온 | **Wide** (observation_date, ssp1~5) | ~108M |
| | `rn_data` | 월 강수량 | **Wide** | ~108M |
| | `ws_data` | 월평균 풍속 | **Wide** | ~108M |
| | `rhm_data` | 월평균 상대습도 | **Wide** | ~108M |
| | `si_data` | 월 일사량 | **Wide** | ~108M |
| | `spei12_data` | SPEI-12 가뭄지수 | **Wide** | ~108M |
| **일별 데이터** | `tamax_data` | 일 최고기온 | **Wide** (time, ssp1~5) | ~7.63M |
| | `tamin_data` | 일 최저기온 | **Wide** | ~7.63M |
| **연별 지수** | `wsdi_data` | 온난야 계속기간 지수 | **Wide** (year, ssp1~5) | ~9M |
| | `csdi_data` | 한랭야 계속기간 지수 | **Wide** | ~9M |
| | `rx1day_data` | 1일 최다강수량 | **Wide** | ~9M |
| | `rx5day_data` | 5일 최다강수량 | **Wide** | ~9M |
| | `cdd_data` | 연속 무강수일 | **Wide** | ~9M |
| | `rain80_data` | 80mm+ 강수일수 | **Wide** | ~9M |
| | `sdii_data` | 강수강도 | **Wide** | ~9M |
| | `ta_yearly_data` | 연평균 기온 | **Wide** | ~9M |
| **해수면** | `sea_level_data` | 해수면 상승 | **Wide** (year, ssp1~5) | ~1,720 |
| **공간 분석** | `spatial_landcover` | 토지피복 분석 캐시 | 비율 (%) | - |
| | `spatial_dem` | DEM 분석 캐시 | 표고/경사/향 | - |
| **API 캐시** | `api_hospitals` | 병원 정보 | PostGIS POINT | - |
| | `api_shelters` | 대피소 정보 | 지역별 통계 | - |
| | `api_typhoon_besttrack` | 태풍 베스트트랙 | PostGIS POINT | 2015~2022 |
| | `api_disaster_yearbook` | 재해연보 | 재해 통계 | - |
| **ModelOps** | `probability_results` | P(H) 확률 | bin_probabilities (jsonb) | ~4.06M |
| | `hazard_results` | Hazard Score (H) | hazard_score_100 | ~4.06M |
| | `exposure_results` | Exposure (E) | exposure_score | ~4.06M |
| | `vulnerability_results` | Vulnerability (V) | vulnerability_score | ~4.06M |
| | `aal_scaled_results` | 최종 AAL | final_aal | ~4.06M |

---

## 🔧 유틸리티 함수

### 저수준 쿼리 메서드

```python
# SELECT 쿼리 실행
results = db.execute_query(
    "SELECT * FROM location_grid WHERE grid_id = %s",
    params=(123,)
)
# 반환: List[Dict[str, Any]]

# INSERT/UPDATE/DELETE 실행
affected_rows = db.execute_update(
    "UPDATE location_grid SET value = %s WHERE grid_id = %s",
    params=(99.5, 123)
)
# 반환: int (영향받은 행 수)
```

### 컨텍스트 매니저 (수동 트랜잭션 제어)

```python
with db.get_connection() as conn:
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM location_grid LIMIT 10")
    results = cursor.fetchall()
    # commit은 자동 (정상 종료 시)
    # rollback은 자동 (예외 발생 시)
```

---

## 🌐 API 엔드포인트별 DB 사용

| 엔드포인트 | DB 사용 여부 | 테이블 | 비고 |
|-----------|------------|-------|-----|
| `POST /api/v1/analysis` | ✅ 사용 | 기후 데이터 테이블 전체 | DataCollectionAgent 통해 조회 |
| `GET /api/v1/reports/{job_id}` | ❌ 미사용 | - | Scratch Space에서 읽기 |
| `GET /api/v1/disaster-history` | ❌ Mock | `disaster_history` (예정) | 현재 Mock 데이터 사용 |
| `POST /api/v1/additional-data` | ❌ 미사용 | - | Scratch Space에 저장 |
| `GET /api/v1/meta/hazards` | ❌ 미사용 | - | 하드코딩된 Enum |
| `POST /api/v1/simulation` | ✅ 사용 | 기후 데이터 테이블 | 시뮬레이션 시 조회 |
| `POST /api/v1/recommendations` | ❌ 미사용 | - | LLM 기반 추천 |

---

## 🔐 환경 변수 설정

### GitHub Secrets (CD 파이프라인용)

```yaml
DATABASE_URL: postgresql://username:password@host:5432/skala_datawarehouse
```

**주의사항**:
- ✅ 포트: **5432** (PostgreSQL 기본 포트)
- ✅ 특수문자 그대로 입력 (URL 인코딩 불필요)
- ✅ 작은따옴표로 감싸져 Docker 컨테이너에 전달됨
- ❌ 패스워드에 `'` (작은따옴표) 포함 시 이스케이프 필요

### 로컬 개발 환경

```bash
# .env 파일
DATABASE_URL=postgresql://user:pass@localhost:5432/skala_datawarehouse
```

---

## 📝 향후 개선 사항

### 1. 재해 이력 DB 저장 구현
**현재**: Mock 데이터
**목표**: `disaster_history` 테이블 생성 및 CRUD 구현

```sql
CREATE TABLE disaster_history (
    id UUID PRIMARY KEY,
    site_id UUID NOT NULL,
    disaster_type VARCHAR(50),
    occurred_at TIMESTAMP,
    severity VARCHAR(20),
    damage_amount BIGINT,
    casualties INT,
    description TEXT,
    recovery_duration INT,
    location VARCHAR(255),
    weather_condition TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

### 2. 분석 결과 저장
**현재**: Scratch Space (임시 파일)
**목표**: 영구 저장용 `analysis_results` 테이블 생성

```sql
CREATE TABLE analysis_results (
    job_id UUID PRIMARY KEY,
    site_id UUID NOT NULL,
    analysis_type VARCHAR(50),
    results JSONB,
    status VARCHAR(20),
    created_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP
);
```

### 3. 사용자 제공 데이터 저장
**현재**: Scratch Space
**목표**: `user_provided_data` 테이블 생성

```sql
CREATE TABLE user_provided_data (
    id UUID PRIMARY KEY,
    site_id UUID NOT NULL,
    data_type VARCHAR(50),
    data JSONB,
    uploaded_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP
);
```

---

## 📚 참고 자료

### 관련 파일
- **DB 유틸리티**: `ai_agent/utils/database.py`
- **Scratch 관리**: `ai_agent/utils/scratch_manager.py`
- **데이터 수집**: `ai_agent/agents/data_processing/data_collection_agent.py`
- **재해 이력 서비스**: `src/services/disaster_history_service.py`
- **ERD 문서**: `docs/Datawarehouse.dbml`

### ERD 버전
- **현재 버전**: **v03** (2025-12-03)
- **주요 변경사항**: Long Format → **Wide Format** (ssp1, ssp2, ssp3, ssp5 컬럼)
- **총 테이블 수**: 45개
- **포트**: 5432 (기존 5434에서 변경)

### 📈 ERD v03 변경 요약

**기존 (v02)**:
```sql
-- Long Format (scenario_id 파라미터 필요)
SELECT year, value
FROM wsdi_data
WHERE grid_id = 123 AND scenario_id = 2;
```

**신규 (v03)**:
```sql
-- Wide Format (4개 시나리오가 컬럼)
SELECT year, ssp1, ssp2, ssp3, ssp5
FROM wsdi_data
WHERE grid_id = 123;
```

**장점**:
- ✅ 한 번의 쿼리로 모든 시나리오 조회 가능
- ✅ 시나리오 간 비교 분석 용이
- ✅ 쿼리 횟수 감소 (성능 향상)
