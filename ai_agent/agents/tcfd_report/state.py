"""
TCFD Report State 정의
LangGraph State TypedDict

작성일: 2025-12-15
버전: v02

State 구조:
    - site_data: 사이트 기본 정보 (Application DB)
    - 5개 결과 테이블: 분리 저장 (Datawarehouse DB)
    - building_data: BC Agent 결과 (별도 필드)
    - additional_data: AD Agent 결과 (별도 필드)
    - use_additional_data: Excel 데이터 사용 여부 플래그 (default=False)
"""

from typing import TypedDict, List, Dict, Any, Annotated


def default_false(current: bool | None, new: bool | None) -> bool:
    """use_additional_data의 기본값을 False로 설정하는 reducer"""
    if new is not None:
        return new
    if current is not None:
        return current
    return False


class TCFDReportState(TypedDict):
    """
    TCFD Report 생성을 위한 LangGraph State

    Fields:
        site_data: 사이트 기본 정보 리스트 (Application DB)
            [{
                "site_id": int,
                "site_info": {
                    "name": str,
                    "latitude": float,
                    "longitude": float,
                    "address": str,
                    "type": str
                }
            }]

        aal_scaled_results: AAL 최종 결과 (Vulnerability 반영)
            [{
                "site_id": str,
                "risk_type": str,
                "target_year": str,
                "ssp126_final_aal": float,
                "ssp245_final_aal": float,
                "ssp370_final_aal": float,
                "ssp585_final_aal": float
            }]

        hazard_results: Hazard Score 결과
            [{
                "latitude": float,
                "longitude": float,
                "risk_type": str,
                "target_year": str,
                "ssp126_score_100": float,
                "ssp245_score_100": float,
                "ssp370_score_100": float,
                "ssp585_score_100": float
            }]

        exposure_results: Exposure Score 결과
            [{
                "site_id": str,
                "risk_type": str,
                "target_year": str,
                "exposure_score": float
            }]

        vulnerability_results: Vulnerability Score 결과
            [{
                "site_id": str,
                "risk_type": str,
                "target_year": str,
                "vulnerability_score": float
            }]

        probability_results: Probability P(H) 결과
            [{
                "latitude": float,
                "longitude": float,
                "risk_type": str,
                "target_year": str,
                "ssp126_aal": float,
                "ssp245_aal": float,
                "ssp370_aal": float,
                "ssp585_aal": float,
                "damage_rates": list,
                "ssp126_bin_probs": list,
                "ssp245_bin_probs": list,
                "ssp370_bin_probs": list,
                "ssp585_bin_probs": list
            }]

        building_data: BC Agent 결과 (site_id를 키로 하는 Dict)
            {
                site_id: {
                    "meta": {...},
                    "building_data": {...},
                    "structural_grade": str,
                    "vulnerabilities": [...],
                    "resilience": [...],
                    "agent_guidelines": str
                },
                ...
            }

        additional_data: AD Agent 결과
            {
                "meta": {...},
                "site_specific_guidelines": {site_id: {...}, ...},
                "summary": str,
                "status": str
            }

        use_additional_data: Excel 추가 데이터 사용 여부 (default=False)
    """

    # 사이트 기본 정보 (Application DB)
    site_data: List[Dict[str, Any]]

    # Datawarehouse DB - 5개 결과 테이블 분리
    aal_scaled_results: List[Dict[str, Any]]
    hazard_results: List[Dict[str, Any]]
    exposure_results: List[Dict[str, Any]]
    vulnerability_results: List[Dict[str, Any]]
    probability_results: List[Dict[str, Any]]

    # Agent 결과 (별도 필드)
    building_data: Dict[int, Dict[str, Any]]  # BC Agent 결과
    additional_data: Dict[str, Any]            # AD Agent 결과

    # Excel 추가 데이터 사용 여부 플래그 (default=False)
    use_additional_data: Annotated[bool, default_false]
