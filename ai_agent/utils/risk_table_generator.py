"""
파일명: risk_table_generator.py
작성일: 2025-12-15
버전: v1.0
파일 개요: 물리적 리스크 표 생성 유틸리티

역할:
    - AAL % 기반 risk_level 및 color 계산
    - 사업장별 리스크 표 JSON 생성
    - SSP 시나리오별 매트릭스 구조화
"""

from typing import Dict, Any, List, Tuple
import logging

logger = logging.getLogger(__name__)


# 리스크 레벨 정의 (S&P Global Climanomics Hazard 기반)
RISK_LEVELS = {
    "none": {"label": "-", "color": "#D3D3D3", "aal_range": (0, 0)},
    "very_low": {"label": "0~3%", "color": "#FFF4CC", "aal_range": (0, 3)},
    "low": {"label": "~6%", "color": "#D4E8C1", "aal_range": (3, 6)},
    "medium": {"label": "~10%", "color": "#A8D57E", "aal_range": (6, 10)},
    "high": {"label": "~16%", "color": "#FDB885", "aal_range": (10, 16)},
    "very_high": {"label": "~30%", "color": "#F59547", "aal_range": (16, 30)},
    "extreme": {"label": "30%~", "color": "#C84D4D", "aal_range": (30, 100)}
}


def calculate_risk_level(aal_percent: float) -> Tuple[str, str]:
    """
    AAL % 기반으로 risk_level 및 color 계산

    :param aal_percent: 연평균 자산 손실률 (%)
    :return: (risk_level, color) 튜플

    예시:
        >>> calculate_risk_level(1.5)
        ('very_low', '#FFF4CC')

        >>> calculate_risk_level(12.3)
        ('high', '#FDB885')
    """
    if aal_percent == 0:
        return "none", RISK_LEVELS["none"]["color"]
    elif aal_percent <= 3:
        return "very_low", RISK_LEVELS["very_low"]["color"]
    elif aal_percent <= 6:
        return "low", RISK_LEVELS["low"]["color"]
    elif aal_percent <= 10:
        return "medium", RISK_LEVELS["medium"]["color"]
    elif aal_percent <= 16:
        return "high", RISK_LEVELS["high"]["color"]
    elif aal_percent <= 30:
        return "very_high", RISK_LEVELS["very_high"]["color"]
    else:
        return "extreme", RISK_LEVELS["extreme"]["color"]


def generate_risk_table_for_site(
    site_id: int,
    site_name: str,
    scenario_data: Dict[str, Dict[str, Dict[str, float]]]
) -> Dict[str, Any]:
    """
    단일 사업장에 대한 리스크 표 생성

    :param site_id: 사업장 ID
    :param site_name: 사업장 이름
    :param scenario_data: 시나리오별 리스크 데이터
        구조 예시:
        {
            "SSP1-2.6": {
                "temperature_change": {
                    "2020": 1.5,
                    "2030": 2.1,
                    "2040": 2.8
                },
                ...
            },
            ...
        }
    :return: risk_table JSON
    """
    logger.info(f"사업장 {site_id} ({site_name}) 리스크 표 생성 시작")

    # 만성/급성 리스크 분류
    chronic_risks = ["temperature_change", "sea_level_rise"]
    acute_risks = [
        "urban_flood", "river_flood", "coastal_flood",
        "drought", "wildfire", "typhoon", "water_stress"
    ]

    risk_table = {}

    # 각 시나리오별 처리
    for scenario_id, risks_data in scenario_data.items():
        risk_table[scenario_id] = {
            "chronic_risks": {},
            "acute_risks": {}
        }

        # 만성 리스크 처리
        for risk_type in chronic_risks:
            if risk_type in risks_data:
                risk_table[scenario_id]["chronic_risks"][risk_type] = {}

                for year, aal_percent in risks_data[risk_type].items():
                    risk_level, color = calculate_risk_level(aal_percent)

                    risk_table[scenario_id]["chronic_risks"][risk_type][year] = {
                        "aal_percent": round(aal_percent, 1),
                        "risk_level": risk_level,
                        "color": color
                    }

        # 급성 리스크 처리
        for risk_type in acute_risks:
            if risk_type in risks_data:
                risk_table[scenario_id]["acute_risks"][risk_type] = {}

                for year, aal_percent in risks_data[risk_type].items():
                    risk_level, color = calculate_risk_level(aal_percent)

                    risk_table[scenario_id]["acute_risks"][risk_type][year] = {
                        "aal_percent": round(aal_percent, 1),
                        "risk_level": risk_level,
                        "color": color
                    }

    logger.info(f"사업장 {site_id} 리스크 표 생성 완료")
    return risk_table


def generate_sites_risk_assessment(
    sites_data: List[Dict[str, Any]],
    scenario_analysis_results: Dict[str, Any],
    impact_analysis_results: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """
    전체 사업장 리스크 평가 생성

    :param sites_data: 사업장 기본 정보 리스트
    :param scenario_analysis_results: Node 2-A 시나리오 분석 결과
    :param impact_analysis_results: Node 2-B 영향 분석 결과
    :return: sites_risk_assessment 배열
    """
    logger.info(f"전체 사업장 리스크 평가 생성 시작: {len(sites_data)}개 사업장")

    sites_risk_assessment = []

    for site in sites_data:
        site_id = site["site_id"]
        site_name = site["site_name"]

        # 해당 사업장의 시나리오 데이터 추출
        site_scenario_data = scenario_analysis_results.get(str(site_id), {})

        # 해당 사업장의 영향 분석 데이터 추출
        site_impact_data = impact_analysis_results.get(str(site_id), {})

        # 리스크 표 생성
        risk_table = generate_risk_table_for_site(
            site_id=site_id,
            site_name=site_name,
            scenario_data=site_scenario_data
        )

        # 최종 구조 생성
        site_assessment = {
            "site_id": site_id,
            "site_name": site_name,
            "site_type": site.get("site_type", "Unknown"),
            "address": site.get("address", ""),
            "location": {
                "latitude": site.get("latitude", 0.0),
                "longitude": site.get("longitude", 0.0)
            },
            "risk_table": risk_table,
            "vulnerability_summary": {
                "high_risk_factors": site_impact_data.get("high_risk_factors", []),
                "resilience_factors": site_impact_data.get("resilience_factors", [])
            }
        }

        sites_risk_assessment.append(site_assessment)
        logger.info(f"사업장 {site_id} ({site_name}) 평가 완료")

    logger.info(f"전체 사업장 리스크 평가 생성 완료: {len(sites_risk_assessment)}개")
    return sites_risk_assessment


def validate_risk_table(risk_table: Dict[str, Any]) -> bool:
    """
    리스크 표 유효성 검증

    :param risk_table: 생성된 리스크 표
    :return: 유효성 여부
    """
    required_scenarios = ["SSP1-2.6", "SSP2-4.5", "SSP3-7.0", "SSP5-8.5"]
    required_years = ["2020", "2030", "2040"]

    for scenario in required_scenarios:
        if scenario not in risk_table:
            logger.error(f"필수 시나리오 누락: {scenario}")
            return False

        # 만성 리스크 검증
        if "chronic_risks" not in risk_table[scenario]:
            logger.error(f"{scenario}: chronic_risks 누락")
            return False

        # 급성 리스크 검증
        if "acute_risks" not in risk_table[scenario]:
            logger.error(f"{scenario}: acute_risks 누락")
            return False

    logger.info("리스크 표 유효성 검증 완료")
    return True


# 예시 사용법
if __name__ == "__main__":
    # 테스트 데이터
    test_scenario_data = {
        "SSP1-2.6": {
            "temperature_change": {
                "2020": 1.5,
                "2030": 2.1,
                "2040": 2.8
            },
            "sea_level_rise": {
                "2020": 0,
                "2030": 0,
                "2040": 0
            },
            "urban_flood": {
                "2020": 0.8,
                "2030": 1.2,
                "2040": 1.8
            }
        }
    }

    # 리스크 표 생성
    table = generate_risk_table_for_site(
        site_id=1,
        site_name="대덕 데이터센터",
        scenario_data=test_scenario_data
    )

    # 검증
    is_valid = validate_risk_table(table)
    print(f"유효성: {is_valid}")

    # 출력
    import json
    print(json.dumps(table, indent=2, ensure_ascii=False))
