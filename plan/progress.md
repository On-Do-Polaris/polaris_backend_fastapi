# SKAX Physical Risk Analysis System 개선 계획 및 진행 상황

## 1. 초기 요청 및 목표

*   `ai_agent/utils/building_data_fetcher.py`의 `get_admin_code` 함수 개선 (하드코딩 제거).
*   `bun`, `ji` 값 0-패딩 적용.
*   TCFD 문서에 명시된 모든 필수 항목을 API에서 가져와 저장.
*   건물 용도 처리 방식 파악 및 LLM 결과물 형태 최적화.
*   제공된 도로명 주소에 대한 실제 데이터 테스트 진행.

## 2. 완료된 작업

*   **`get_admin_code` 함수 개선:**
    *   V-World API의 `dong_code` (10자리)에서 `sigungu_cd` 및 `bjdong_cd`를 직접 파싱하도록 `get_admin_code` 함수를 수정했습니다.
    *   하드코딩된 시군구 코드 딕셔너리를 제거하여 로직을 간소화하고 정확도를 높였습니다.
*   **`bun`, `ji` 값 0-패딩 및 클린징 적용:**
    *   V-World Geocoder API에서 가져온 `bun` (번)과 `ji` (지) 값에서 숫자 이외의 문자를 모두 제거하여 순수하게 숫자 값만 남기도록 `get_building_code_from_coords` 함수를 수정했습니다. (예: "667유" -> "667")
    *   건축물대장 API 요구사항에 맞춰 이 값들을 4자리로 0-패딩하도록 적용되어 있었습니다.
*   **TCFD 필수 항목 전체 수집 및 저장:**
    *   TCFD 문서에 명시된 `getBrBasisOulnInfo`, `getBrRecapTitleInfo`, `getBrTitleInfo`, `getBrFlrOulnInfo` API의 모든 필수 항목(코드 및 이름)을 추출하여 `tcfd_data` 딕셔너리에 저장하도록 `fetch_full_tcfd_data` 및 `_parse_floor_details` 함수를 수정했습니다.
*   **`ai_agent/common/fallback_constants.py` 파일 생성:**
    *   `building_data_fetcher.py`의 필수 의존성이었으나 누락되었던 `fallback_constants.py` 파일을 사용자 제공 내용으로 `ai_agent/common/` 경로에 생성하여 `ModuleNotFoundError`를 해결했습니다.
*   **단위/목(Mock) 테스트 통과:**
    *   `ai_agent/utils/test_building_data_fetcher.py`에 작성된 `get_admin_code` 로직 테스트 및 `fetch_full_tcfd_data`의 데이터 추출/구조화 목 테스트가 모두 성공적으로 통과했습니다.
*   **`run_live_test.py` 스크립트 업데이트:**
    *   `juso.go.kr` API를 사용하여 주소에서 위/경도를 얻는 새로운 로직을 통합했습니다.

## 3. 현재 진행 중인 문제점 및 다음 단계

### 3.1. 문제점

1.  **주소 문자열 → 위/경도 변환 실패 (`juso.go.kr` API 사용 시):**
    *   초기에 V-World Geocoder API (`req/search`)를 사용하여 주소 문자열에서 위/경도를 얻으려 했으나, `NOT_FOUND` 오류가 발생했습니다.
    *   사용자 요청에 따라 `juso.go.kr` API로 전환하여 `get_address_components_from_juso` (주소 구성 요소 검색) 및 `get_coords_from_juso_components` (좌표 변환) 두 단계를 구현했습니다.
    *   그러나 `get_coords_from_juso_components`가 `COORDINATESEARCH_API_KEY`에 대해 `승인되지 않은 KEY (E0001)` 오류를 반환하여, `juso.go.kr`을 통한 주소 → 위/경도 변환 또한 현재 불가능한 상태입니다.
    *   결과적으로, `fetch_full_tcfd_data`가 필요로 하는 주소의 `lat`/`lon`을 안정적으로 얻을 수 있는 방법이 현재 없습니다.
2.  **건축물대장 기본정보 없음:** (`fetch_full_tcfd_data` 내부에서 `getBrBasisOulnInfo` API 호출 결과)
    *   `juso.go.kr`을 통해 위/경도 변환이 성공적으로 이루어지더라도, `fetch_full_tcfd_data` 내부에서 `PUBLICDATA_API_KEY`를 사용하는 `getBrBasisOulnInfo` (건축물대장 기본개요 조회) API 호출이 "건축물대장 기본정보 없음" 메시지와 함께 데이터를 반환하지 않고 있습니다.
    *   이는 `PUBLICDATA_API_KEY`의 유효성/권한 문제, 또는 API 호출 파라미터(`sigunguCd`, `bjdongCd`, `bun`, `ji`)와 건축물대장 DB 간의 불일치 때문일 수 있습니다.

### 3.2. 현재 상태

*   `run_live_test.py` 스크립트는 `juso.go.kr` API를 통해 주소 구성 요소를 성공적으로 가져오지만, `COORDINATESEARCH_API_KEY` 문제로 인해 위/경도 변환 단계에서 멈춰 있습니다.
*   디버깅용 `print` 문을 통해 `VWORLD_API_KEY`, `PUBLICDATA_API_KEY`, `ROADSEARCH_API_KEY`, `COORDINATESEARCH_API_KEY`가 모두 코드에 의해 로드되었음이 확인되었습니다.

### 3.3. 다음 단계

1.  **`COORDINATESEARCH_API_KEY` 유효성 확인 요청:** 사용자께서는 `juso.go.kr` 좌표 변환 API용 `COORDINATESEARCH_API_KEY`가 올바르고 `addrCoordApi.do` 엔드포인트에 대해 승인된 키인지 **재확인해 주셔야 합니다.** (`E0001` 오류는 키 문제입니다.)
2.  **`PUBLICDATA_API_KEY` 유효성 확인 요청:** `건축물대장 기본정보 없음` 문제가 지속되므로, `PUBLICDATA_API_KEY` 또한 유효하고 건축물대장 API (`getBrBasisOulnInfo` 등)에 대한 권한이 있는지 확인이 필요합니다.
3.  **임시 위/경도 값 제공 요청 (선택 사항):** `juso.go.kr` 좌표 변환 API 키 문제가 즉시 해결되지 않을 경우, 테스트 진행을 위해 사용자가 직접 정확한 `lat`/`lon` 값을 제공해 주시면 `fetch_full_tcfd_data` 및 내부 V-World Geocoder/건축물대장 API 호출의 나머지 부분을 테스트할 수 있습니다.

---

**TCFD 데이터 구조 (Prompt 구성 요소): `tcfd_data` 딕셔너리의 각 섹션별 출처 및 포함 필드**

`ai_agent/agents/data_processing/vulnerability_analysis_agent.py`에서 `prompt`를 구성하는 `meta`, `physical_specs`, `floor_details`, `transition_specs`, `financial_info`, `geo_risks`는 `BuildingDataFetcher`의 `fetch_full_tcfd_data` 메서드가 반환하는 최종 `tcfd_data` 딕셔너리의 최상위 키들입니다. 각 섹션의 출처와 포함 필드는 다음과 같습니다.

### 1. `meta` (메타 정보)
*   **출처 API:**
    *   `get_building_code_from_coords` (V-World Geocoder API: 위/경도 → 지번/도로명 주소, 번/지)
    *   `get_admin_code` (법정동 코드 → 행정코드 변환)
    *   `getBrBasisOulnInfo` (건축물대장 기본개요 조회)
*   **주요 포함 필드:**
    *   `pk`: 관리건축물대장PK (`mgmBldrgstPk` - 건축물 유일 식별자)
    *   `name`: 건물명 (`bldNm`)
    *   `address`: 전체 지번 주소 (`full_address`)
    *   `road_address`: 전체 도로명 주소 (`road_address`)
    *   `coordinates`: 입력된 `lat`, `lon`
    *   `admin_codes`: `sigungu_cd` (시군구코드), `bjdong_cd` (법정동코드)
    *   `mgm_up_bldrgst_pk`: 관리상위건축물대장PK (집합건물 단지 식별자)
    *   `bldg_id`: 건물 아이디 (국가건축물 고유번호)
    *   `jiyuk_cd_nm`: 지역코드명 (용도지역별 규제 리스크)
    *   `jigu_cd_nm`: 지구코드명 (용도지구별 규제 리스크)
    *   `guyuk_cd_nm`: 구역코드명 (재해위험구역 등)

### 2. `physical_specs` (물리적 특성)
*   **출처 API:** `getBrTitleInfo` (건축물대장 표제부 조회)
*   **주요 포함 필드:**
    *   `structure`: 구조명 (`strctCdNm` 예: "철근콘크리트구조")
    *   `structure_cd`: 구조코드 (`strctCd`)
    *   `main_purpose`: 주용도명 (`mainPurpsCdNm` 예: "업무시설")
    *   `etc_structure`: 기타구조 (`etcStrct`)
    *   `floors`:
        *   `ground`: 지상층수 (`grndFlrCnt`)
        *   `underground`: 지하층수 (`ugrndFlrCnt`)
        *   `height`: 높이 (m) (`heit`)
    *   `seismic`:
        *   `applied`: 내진설계적용여부 (`rserthqkDsgnApplyYn` 예: "Y")
        *   `ability`: 내진능력 (`rserthqkAblty` 예: "내진특등급")
    *   `age`:
        *   `approval_date`: 사용승인일 (`useAprDay`)
        *   `years`: 건물 연식 (현재 연도 - 사용승인일 연도)
    *   `ride_use_elevator_count`: 승용승강기수 (`rideUseElvtCnt`)

### 3. `floor_details` (층별 상세 정보) - ⭐ 핵심
*   **출처 API:** `getBrFlrOulnInfo` (건축물대장 층별개요 조회)
*   **주요 포함 필드 (각 층별):**
    *   `floor_no`: 층번호 (`flrNo` 예: -1, 1, 2)
    *   `name`: 층명칭 (`flrNoNm` 예: "지하1층", "1층")
    *   `type`: 층 구분 ("Underground" 또는 "Ground")
    *   `flr_gb_cd`: 층 구분 코드 (`flrGbCd` 예: "10" for 지하)
    *   `area`: 면적 (m²) (`area`)
    *   `usage_main`: 주용도명 (`mainPurpsCdNm`)
    *   `usage_main_cd`: 주용도코드 (`mainPurpsCd`)
    *   `usage_etc`: 기타용도 (`etcPurps`)
    *   `structure_cd`: 구조코드 (`strctCd`)
    *   `structure_name`: 구조명 (`strctCdNm`)
    *   `is_potentially_critical`: 중요설비(기계실, 전기실 등) 포함 여부 (LLM 힌트용 플래그)

### 4. `transition_specs` (전환 특성)
*   **출처 API:** `getBrRecapTitleInfo` (건축물대장 총괄표제부 조회)
*   **주요 포함 필드:**
    *   `energy_grade`: 에너지효율등급 (`engrGrade`)
    *   `green_grade`: 친환경건축물등급 (`gnBldGrade`)
    *   `total_parking`: 총주차수 (`totPkngCnt`)
    *   `total_area`: 연면적 (m²) (`totArea`)
    *   `arch_area`: 건축면적 (m²) (`archArea`)
    *   `main_purpose_cd`: 주용도코드 (`mainPurpsCd`)
    *   `energy_rating`: 에너지절감율 (`engrRat`)
    *   `epi_score`: EPI점수 (`engrEpi`)
    *   `integrated_building_grade`: 지능형건축물등급 (`itgBldGrade`)
    *   `household_count`: 세대수 (`hhldCnt`)

### 5. `financial_info` (재무 정보)
*   **출처 API:** `getBrHsprcInfo` (건축물대장 주택가격 조회)
*   **주요 포함 필드:**
    *   `housing_price`: 주택가격 (`hsprc`)
    *   `base_date`: 기준일자 (`stdDay`)

### 6. `geo_risks` (지리적 리스크)
*   **출처 API:**
    *   `get_river_info` (V-World WFS API)
    *   `get_distance_to_coast` (고정된 해안점 기준 계산)
*   **주요 포함 필드:**
    *   `river`:
        *   `distance_m`: 하천까지의 거리 (m)
        *   `river_name`: 하천명
    *   `coast_distance_m`: 해안선까지의 거리 (m)

---
