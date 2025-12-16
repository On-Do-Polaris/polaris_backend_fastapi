"""
Node 2-B: Impact Analysis (Physical Risk Report)
사업장별 취약성 및 회복력 분석

설계 목적:
- 물리적 리스크 보고서 전용 (TCFD 전체 제외)
- BuildingCharacteristicsAgent 결과 통합
- 취약성 요인 (vulnerabilities) 추출
- 회복력 요인 (resilience) 추출
- ❌ 하드코딩 제거: 텍스트 생성은 Node 3에서 처리
- ❌ TextBlock 제거: Node 3에서 통합 처리

작성일: 2025-12-15 (Physical Risk Report 전용)
버전: v2.0
"""

import asyncio
from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)


class ImpactAnalysisNode:
    """
    Node 2-B: 영향 분석 노드 (물리적 리스크 전용)

    입력:
        - sites_data: List[dict] (사업장 목록)
        - scenario_analysis: Dict (Node 2-A 출력)
        - building_characteristics: Dict (BuildingCharacteristicsAgent 결과)

    출력:
        - site_impact_data: Dict[int, Dict] (사업장별 영향 분석 데이터)
          {
              site_id: {
                  "high_risk_factors": [...],  # 취약성 요인
                  "resilience_factors": [...],  # 회복력 요인
                  "structural_grade": "A1",
                  "building_age": 15,
                  "impact_summary": {
                      "chronic_vulnerability": "high/medium/low",
                      "acute_vulnerability": "high/medium/low"
                  }
              }
          }
    """

    def __init__(self, llm=None):
        """
        초기화

        :param llm: LLM 클라이언트 (현재는 사용하지 않음, 추후 확장용)
        """
        self.llm = llm
        self.logger = logger

    async def execute(
        self,
        sites_data: List[Dict],
        scenario_analysis: Dict,
        building_characteristics: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        메인 실행 함수

        :param sites_data: 사업장 정보 리스트
        :param scenario_analysis: Node 2-A 시나리오 분석 결과
        :param building_characteristics: BuildingCharacteristicsAgent 결과
        :return: 사업장별 영향 분석 데이터
        """
        self.logger.info(f"Node 2-B 시작: {len(sites_data)}개 사업장 영향 분석")

        # 1. 사업장별 영향 분석 (병렬)
        site_impact_results = await self._analyze_impacts_parallel(
            sites_data,
            scenario_analysis,
            building_characteristics
        )

        self.logger.info(f"Node 2-B 완료: {len(site_impact_results)}개 사업장 처리")

        return {
            "site_impact_data": site_impact_results,
            "status": "completed"
        }

    async def _analyze_impacts_parallel(
        self,
        sites_data: List[Dict],
        scenario_analysis: Dict,
        building_characteristics: Optional[Dict]
    ) -> Dict[int, Dict]:
        """
        사업장별 영향 분석 병렬 처리

        :param sites_data: 사업장 정보 리스트
        :param scenario_analysis: Node 2-A 결과
        :param building_characteristics: BuildingCharacteristicsAgent 결과
        :return: 사업장별 영향 분석 데이터
        """
        tasks = []
        site_ids = []

        for site in sites_data:
            site_id = site["site_id"]
            site_ids.append(site_id)

            # 해당 사업장의 시나리오 데이터 추출
            site_scenario_data = scenario_analysis.get("site_scenario_data", {}).get(site_id, {})

            # 해당 사업장의 건물 특성 데이터 추출
            site_bc_data = building_characteristics.get(str(site_id), {}) if building_characteristics else {}

            task = self._analyze_site_impact(
                site,
                site_scenario_data,
                site_bc_data
            )
            tasks.append(task)

        # 병렬 실행
        results_list = await asyncio.gather(*tasks, return_exceptions=True)

        # 결과를 dict로 변환
        site_impact_results = {}
        for site_id, result in zip(site_ids, results_list):
            if isinstance(result, Exception):
                self.logger.error(f"사업장 {site_id} 영향 분석 실패: {result}")
                continue

            site_impact_results[site_id] = result

        return site_impact_results

    async def _analyze_site_impact(
        self,
        site: Dict,
        site_scenario_data: Dict,
        site_bc_data: Dict
    ) -> Dict:
        """
        단일 사업장의 영향 분석

        :param site: 사업장 정보
        :param site_scenario_data: 사업장 시나리오 데이터 (Node 2-A)
        :param site_bc_data: 사업장 건물 특성 데이터 (BC Agent)
        :return: 영향 분석 데이터
        """
        site_id = site["site_id"]

        # 1. BuildingCharacteristicsAgent 결과에서 취약성/회복력 추출
        vulnerabilities = site_bc_data.get("vulnerabilities", [])
        resilience = site_bc_data.get("resilience", [])
        structural_grade = site_bc_data.get("structural_grade", "Unknown")

        # 건물 연식 추출
        building_data = site_bc_data.get("building_data", {})
        physical_specs = building_data.get("physical_specs", {})
        age_info = physical_specs.get("age", {})
        building_age = age_info.get("years", 0)

        # 2. 취약성 요인 정리 (high/very_high severity만)
        high_risk_factors = [
            {
                "factor": v["factor"],
                "severity": v["severity"],
                "description": v["description"]
            }
            for v in vulnerabilities
            if v.get("severity") in ["high", "very_high"]
        ]

        # 3. 회복력 요인 정리 (high/very_high strength만)
        resilience_factors = [
            {
                "factor": r["factor"],
                "strength": r["strength"],
                "description": r["description"]
            }
            for r in resilience
            if r.get("strength") in ["high", "very_high"]
        ]

        # 4. 시나리오 데이터 기반 취약성 평가 (SSP5-8.5 worst case 기준)
        impact_summary = self._calculate_impact_summary(site_scenario_data)

        return {
            "high_risk_factors": high_risk_factors,
            "resilience_factors": resilience_factors,
            "structural_grade": structural_grade,
            "building_age": building_age,
            "impact_summary": impact_summary
        }

    def _calculate_impact_summary(self, site_scenario_data: Dict) -> Dict:
        """
        시나리오 데이터 기반 영향 요약 계산

        :param site_scenario_data: 사업장 시나리오 데이터
        :return: 영향 요약
        """
        # SSP5-8.5 worst-case 시나리오 사용
        worst_case = site_scenario_data.get("SSP5-8.5", {})

        # 만성 리스크 (temperature_change, sea_level_rise)
        chronic_risks = ["temperature_change", "sea_level_rise"]
        chronic_aal_2040 = []

        for risk_type in chronic_risks:
            if risk_type in worst_case:
                aal_2040 = worst_case[risk_type].get("2040", 0.0)
                chronic_aal_2040.append(aal_2040)

        avg_chronic_aal = sum(chronic_aal_2040) / len(chronic_aal_2040) if chronic_aal_2040 else 0.0

        # 급성 리스크 (나머지 7개)
        acute_risks = [
            "urban_flood", "river_flood", "coastal_flood",
            "drought", "wildfire", "typhoon", "water_stress"
        ]
        acute_aal_2040 = []

        for risk_type in acute_risks:
            if risk_type in worst_case:
                aal_2040 = worst_case[risk_type].get("2040", 0.0)
                acute_aal_2040.append(aal_2040)

        avg_acute_aal = sum(acute_aal_2040) / len(acute_aal_2040) if acute_aal_2040 else 0.0

        # 취약성 레벨 계산 (AAL % 기준)
        def get_vulnerability_level(aal: float) -> str:
            if aal >= 10:
                return "high"
            elif aal >= 3:
                return "medium"
            else:
                return "low"

        return {
            "chronic_vulnerability": get_vulnerability_level(avg_chronic_aal),
            "acute_vulnerability": get_vulnerability_level(avg_acute_aal),
            "chronic_aal_2040": round(avg_chronic_aal, 2),
            "acute_aal_2040": round(avg_acute_aal, 2)
        }


# 모듈 레벨 실행 함수 (워크플로우에서 호출)
async def run_impact_analysis(
    sites_data: List[Dict],
    scenario_analysis: Dict,
    building_characteristics: Optional[Dict] = None,
    llm=None
) -> Dict[str, Any]:
    """
    Node 2-B 실행 함수

    :param sites_data: 사업장 정보 리스트
    :param scenario_analysis: Node 2-A 결과
    :param building_characteristics: BuildingCharacteristicsAgent 결과
    :param llm: LLM 클라이언트 (선택)
    :return: 영향 분석 결과
    """
    node = ImpactAnalysisNode(llm=llm)
    return await node.execute(sites_data, scenario_analysis, building_characteristics)
