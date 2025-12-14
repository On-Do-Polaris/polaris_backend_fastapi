import json
import json
import pytest
from unittest.mock import patch, MagicMock
from ai_agent.utils.building_data_fetcher import BuildingDataFetcher

# For testing get_admin_code logic
def test_get_admin_code_parsing():
    fetcher = BuildingDataFetcher()
    
    # Test with a valid 10-digit dong_code
    dong_code_valid = "1168010800" # Example: 강남구 역삼동
    codes = fetcher.get_admin_code(dong_code_valid)
    assert codes['sigungu_cd'] == "11680"
    assert codes['bjdong_cd'] == "10800"

    # Test with a 5-digit sigungu_cd (should result in '00000' bjdong_cd)
    sigungu_code_only = "11110" # Example: 종로구
    codes = fetcher.get_admin_code(sigungu_code_only)
    assert codes['sigungu_cd'] == "11110"
    assert codes['bjdong_cd'] == "00000"

    # Test with None
    codes = fetcher.get_admin_code(None)
    assert codes['sigungu_cd'] == "00000"
    assert codes['bjdong_cd'] == "00000"

    # Test with empty string
    codes = fetcher.get_admin_code("")
    assert codes['sigungu_cd'] == "00000"
    assert codes['bjdong_cd'] == "00000"

# --- Helper functions for mocked API responses ---
def mock_vworld_geocoder_response():
    vworld_mock_response = """
    {
        "response": {
            "status": "OK",
            "result": [
                {"type": "parcel", "text": "서울특별시 강남구 역삼동 737", "structure": {
                    "level1": "서울특별시", "level2": "강남구", "level4L": "역삼동", "level4LC": "1168010800",
                    "number1": "737", "number2": "0"
                }, "zipcode": "06220"},
                {"type": "road", "text": "서울특별시 강남구 테헤란로 152", "structure": {}}
            ]
        }
    }
    """
    return MagicMock(json=lambda: json.loads(vworld_mock_response))

def mock_get_br_basis_ouln_info_response():
    return MagicMock(json=lambda: {
        "response": {"body": {"items": {"item": [{
            "mgmBldrgstPk": "11680-12345",
            "bldNm": "테헤란빌딩",
            "mgmUpBldrgstPk": "11680-UP-123",
            "bldgId": "BLDGID-789",
            "jiyukCdNm": "상업지역",
            "jiguCdNm": "중심업무지구",
            "guyukCdNm": "방재지구"
        }]}}}}
    )

def mock_get_br_title_info_response():
    return MagicMock(json=lambda: {
        "response": {"body": {"items": {"item": [{
            "strctCdNm": "철근콘크리트구조",
            "strctCd": "21000",
            "mainPurpsCdNm": "업무시설",
            "grndFlrCnt": 10,
            "ugrndFlrCnt": 3,
            "heit": 40.5,
            "rserthqkDsgnApplyYn": "Y",
            "rserthqkAblty": "내진특등급",
            "useAprDay": "20000101",
            "etcStrct": "일부 철골",
            "rideUseElvtCnt": 4
        }]}}}}
    )

def mock_get_br_recap_title_info_response():
    return MagicMock(json=lambda: {
        "response": {"body": {"items": {"item": [{
            "engrGrade": "1등급",
            "gnBldGrade": "최우수",
            "totPkngCnt": 100,
            "totArea": 10000.5,
            "archArea": 2000.0,
            "mainPurpsCd": "01000", # Example code for business
            "engrRat": "30%",
            "engrEpi": "80",
            "itgBldGrade": "우수",
            "hhldCnt": 0
        }]}}}}
    )

def mock_get_br_flr_ouln_info_response():
    return MagicMock(json=lambda: {
        "response": {"body": {"items": {"item": [
            {"flrNo": "-1", "flrNoNm": "지하1층", "flrGbCd": "10", "area": 1000.0, "mainPurpsCdNm": "기계실", "mainPurpsCd": "04000", "etcPurps": "펌프실", "strctCd": "21000", "strctCdNm": "철근콘크리트"},
            {"flrNo": "1", "flrNoNm": "1층", "flrGbCd": "20", "area": 900.0, "mainPurpsCdNm": "로비", "mainPurpsCd": "01000", "etcPurps": "", "strctCd": "21000", "strctCdNm": "철근콘크리트"},
            {"flrNo": "2", "flrNoNm": "2층", "flrGbCd": "20", "area": 800.0, "mainPurpsCdNm": "사무실", "mainPurpsCd": "01000", "etcPurps": "", "strctCd": "21000", "strctCdNm": "철근콘크리트"}
        ]}}}}
    )

def mock_get_br_hsprc_info_response():
    return MagicMock(json=lambda: {
        "response": {"body": {"items": {"item": [{
            "hsprc": 1500000000.0,
            "stdDay": "20250101"
        }]}}}}
    )

def mock_vworld_wfs_response():
    return MagicMock(json=lambda: {
        "type": "FeatureCollection",
        "features": [{
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [126.9780, 37.5665]},
            "properties": {"name": "한강"}
        }]
    })


@patch('requests.get')
def test_fetch_full_tcfd_data_with_mocked_apis(mock_get):
    fetcher = BuildingDataFetcher()

    mock_get.side_effect = [
        mock_vworld_geocoder_response(),
        mock_get_br_basis_ouln_info_response(),
        mock_get_br_title_info_response(),
        mock_get_br_recap_title_info_response(),
        mock_get_br_flr_ouln_info_response(),
        mock_get_br_hsprc_info_response(),
        mock_vworld_wfs_response()
    ]

    lat, lon = 37.5665, 126.9780 # 서울시청
    tcfd_data = fetcher.fetch_full_tcfd_data(lat, lon)

    # Basic assertions for structure
    assert isinstance(tcfd_data, dict)
    assert "meta" in tcfd_data
    assert "physical_specs" in tcfd_data
    assert "transition_specs" in tcfd_data
    assert "floor_details" in tcfd_data
    assert "geo_risks" in tcfd_data

    # Verify get_admin_code parsing
    assert tcfd_data['meta']['admin_codes']['sigungu_cd'] == "11680"
    assert tcfd_data['meta']['admin_codes']['bjdong_cd'] == "10800"

    # Verify newly added fields from getBrBasisOulnInfo
    assert tcfd_data['meta']['mgm_up_bldrgst_pk'] == "11680-UP-123"
    assert tcfd_data['meta']['bldg_id'] == "BLDGID-789"
    assert tcfd_data['meta']['jiyuk_cd_nm'] == "상업지역"
    assert tcfd_data['meta']['jigu_cd_nm'] == "중심업무지구"
    assert tcfd_data['meta']['guyuk_cd_nm'] == "방재지구"

    # Verify newly added fields from getBrRecapTitleInfo
    assert tcfd_data['transition_specs']['arch_area'] == 2000.0
    assert tcfd_data['transition_specs']['main_purpose_cd'] == "01000"
    assert tcfd_data['transition_specs']['energy_rating'] == "30%"
    assert tcfd_data['transition_specs']['epi_score'] == "80"
    assert tcfd_data['transition_specs']['integrated_building_grade'] == "우수"
    assert tcfd_data['transition_specs']['household_count'] == 0

    # Verify newly added fields from getBrTitleInfo
    assert tcfd_data['physical_specs']['structure_cd'] == "21000"
    assert tcfd_data['physical_specs']['etc_structure'] == "일부 철골"
    assert tcfd_data['physical_specs']['ride_use_elevator_count'] == 4

    # Verify newly added fields from getBrFlrOulnInfo in floor_details
    assert len(tcfd_data['floor_details']) == 3
    floor1 = tcfd_data['floor_details'][0]
    assert floor1['flr_gb_cd'] == "10"
    assert floor1['usage_main_cd'] == "04000"
    assert floor1['structure_cd'] == "21000"
    assert floor1['structure_name'] == "철근콘크리트"
    assert floor1['is_potentially_critical'] == True

    floor2 = tcfd_data['floor_details'][1]
    assert floor2['flr_gb_cd'] == "20"
    assert floor2['usage_main_cd'] == "01000"
    assert floor2['is_potentially_critical'] == False

    floor3 = tcfd_data['floor_details'][2]
    assert floor3['flr_gb_cd'] == "20"
    assert floor3['usage_main_cd'] == "01000"


    # Verify bun/ji parsing (this is done in get_building_code_from_coords before fetch_full_tcfd_data)
    # The mock for V-World response already has 'number1': '737', 'number2': '0' which zfill(4) correctly.
