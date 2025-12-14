# TCFD 데이터 페처 개선 계획

## 1. `get_admin_code` 함수 개선
- `get_building_code_from_coords`에서 반환하는 V-World API의 `dong_code` (10자리)를 직접 활용하여 `sigungu_cd` (앞 5자리)와 `bjdong_cd` (뒤 5자리)를 파싱하도록 수정한다.
- 현재 `get_admin_code` 내의 하드코딩된 `sigungu_codes` 딕셔너리를 제거한다.

## 2. `bun`, `ji` 값 0-패딩 적용
- `fetch_full_tcfd_data` 함수 내에서 `getBrBasisOulnInfo` 호출 시 `bun`과 `ji` 파라미터가 4자리 숫자로 0-패딩 (`zfill(4)`) 되도록 수정한다.

## 3. TCFD 필수 항목 전체 수집 및 저장
`건축HUB API - TCFD 보고서 작성용 최종 필수 항목.md` 문서에 명시된 모든 필수 항목을 API 응답에서 추출하여 `tcfd_data` 딕셔너리에 저장한다. 특히 코드(`Cd`)가 있는 경우 코드 값을 우선적으로 저장하도록 한다.

### 3.1. `getBrBasisOulnInfo` (건축물대장 기본개요 조회) 항목 추가
- `mgmUpBldrgstPk`
- `bldgId`
- `jiyukCdNm`
- `jiguCdNm`
- `guyukCdNm`

### 3.2. `getBrRecapTitleInfo` (건축물대장 총괄표제부 조회) 항목 추가
- `archArea`
- `mainPurpsCd` (코드)
- `engrRat`
- `engrEpi`
- `itgBldGrade`
- `hhldCnt`

### 3.3. `getBrTitleInfo` (건축물대장 표제부 조회) 항목 추가
- `strctCd` (코드)
- `etcStrct`
- `rideUseElvtCnt`

### 3.4. `getBrFlrOulnInfo` (건축물대장 층별개요 조회) 항목 추가 및 `_parse_floor_details` 함수 수정
- `flrGbCd` (코드)
- `mainPurpsCd` (코드)
- `strctCd` (코드)

## 4. 코드 가독성 및 유지보수성 향상
- 변경 사항 적용 후 코드의 일관성과 가독성을 유지한다.
- 불필요한 주석이나 로직을 정리한다.
