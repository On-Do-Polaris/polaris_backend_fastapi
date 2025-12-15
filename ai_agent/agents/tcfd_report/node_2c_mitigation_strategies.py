"""
Node 2-C: Adaptation Recommendations (Physical Risk Report)
사업장별 적응 권고사항 분류

설계 목적:
- 물리적 리스크 보고서 전용 (TCFD 전체 제외)
- 리스크 레벨 기반 적응 권고사항 분류
- 단기/중기/장기 우선순위 카테고리 제공
- ❌ 하드코딩 제거: 텍스트 생성은 Node 3에서 처리
- ❌ TextBlock 제거: Node 3에서 통합 처리

작성일: 2025-12-15 (Physical Risk Report 전용)
버전: v2.0
"""

import asyncio
from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)


class AdaptationRecommendationsNode:
    """
    Node 2-C: 적응 권고사항 노드 (물리적 리스크 전용)

    입력:
        - sites_data: List[dict] (사업장 목록)
        - scenario_analysis: Dict (Node 2-A 출력)
        - impact_analysis: Dict (Node 2-B 출력)

    출력:
        - site_adaptation_data: Dict[int, Dict] (사업장별 적응 권고사항)
          {
              site_id: {
                  "priority_level": "high/medium/low",
                  "recommended_actions": {
                      "immediate": [...],  # 즉시 조치 필요
                      "short_term": [...],  # 1-3년
                      "long_term": [...]   # 3년 이상
                  },
                  "focus_areas": [...]  # 집중 대응 필요 리스크 타입
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
        impact_analysis: Dict
    ) -> Dict[str, Any]:
        """
        메인 실행 함수

        :param sites_data: 사업장 정보 리스트
        :param scenario_analysis: Node 2-A 시나리오 분석 결과
        :param impact_analysis: Node 2-B 영향 분석 결과
        :return: 사업장별 적응 권고사항
        """
        self.logger.info(f"Node 2-C 시작: {len(sites_data)}개 사업장 적응 권고사항 분류")

        # 1. 사업장별 적응 권고사항 (병렬)
        site_adaptation_results = await self._classify_adaptations_parallel(
            sites_data,
            scenario_analysis,
            impact_analysis
        )

        self.logger.info(f"Node 2-C 완료: {len(site_adaptation_results)}개 사업장 처리")

        return {
            "site_adaptation_data": site_adaptation_results,
            "status": "completed"
        }

    async def _classify_adaptations_parallel(
        self,
        sites_data: List[Dict],
        scenario_analysis: Dict,
        impact_analysis: Dict
    ) -> Dict[int, Dict]:
        """
        사업장별 적응 권고사항 병렬 분류

        :param sites_data: 사업장 정보 리스트
        :param scenario_analysis: Node 2-A 결과
        :param impact_analysis: Node 2-B 결과
        :return: 사업장별 적응 권고사항
        """
        tasks = []
        site_ids = []

        for site in sites_data:
            site_id = site["site_id"]
            site_ids.append(site_id)

            # 해당 사업장의 시나리오 데이터 추출
            site_scenario_data = scenario_analysis.get("site_scenario_data", {}).get(site_id, {})

            # 해당 사업장의 영향 분석 데이터 추출
            site_impact_data = impact_analysis.get("site_impact_data", {}).get(site_id, {})

            task = self._classify_site_adaptation(
                site,
                site_scenario_data,
                site_impact_data
            )
            tasks.append(task)

        # 병렬 실행
        results_list = await asyncio.gather(*tasks, return_exceptions=True)

        # 결과를 dict로 변환
        site_adaptation_results = {}
        for site_id, result in zip(site_ids, results_list):
            if isinstance(result, Exception):
                self.logger.error(f"사업장 {site_id} 적응 권고사항 분류 실패: {result}")
                continue

            site_adaptation_results[site_id] = result

        return site_adaptation_results

    async def _classify_site_adaptation(
        self,
        site: Dict,
        site_scenario_data: Dict,
        site_impact_data: Dict
    ) -> Dict:
        """
        단일 사업장의 적응 권고사항 분류

        :param site: 사업장 정보
        :param site_scenario_data: 사업장 시나리오 데이터 (Node 2-A)
        :param site_impact_data: 사업장 영향 분석 데이터 (Node 2-B)
        :return: 적응 권고사항 데이터
        """
        site_id = site["site_id"]

        # 1. 우선순위 레벨 결정 (impact_summary 기반)
        impact_summary = site_impact_data.get("impact_summary", {})
        chronic_vuln = impact_summary.get("chronic_vulnerability", "low")
        acute_vuln = impact_summary.get("acute_vulnerability", "low")

        priority_level = self._determine_priority_level(chronic_vuln, acute_vuln)

        # 2. 집중 대응 필요 리스크 타입 식별 (AAL > 6% 기준)
        focus_areas = self._identify_focus_areas(site_scenario_data)

        # 3. 권고 조치 카테고리 분류
        recommended_actions = self._categorize_actions(
            priority_level,
            focus_areas,
            site_impact_data
        )

        return {
            "priority_level": priority_level,
            "recommended_actions": recommended_actions,
            "focus_areas": focus_areas
        }

    def _determine_priority_level(self, chronic_vuln: str, acute_vuln: str) -> str:
        """
        우선순위 레벨 결정

        :param chronic_vuln: 만성 리스크 취약성 (high/medium/low)
        :param acute_vuln: 급성 리스크 취약성 (high/medium/low)
        :return: 우선순위 레벨 (high/medium/low)
        """
        vuln_score = 0

        if chronic_vuln == "high":
            vuln_score += 2
        elif chronic_vuln == "medium":
            vuln_score += 1

        if acute_vuln == "high":
            vuln_score += 2
        elif acute_vuln == "medium":
            vuln_score += 1

        if vuln_score >= 3:
            return "high"
        elif vuln_score >= 1:
            return "medium"
        else:
            return "low"

    def _identify_focus_areas(self, site_scenario_data: Dict) -> List[str]:
        """
        집중 대응 필요 리스크 타입 식별

        :param site_scenario_data: 사업장 시나리오 데이터
        :return: 리스크 타입 리스트
        """
        focus_areas = []

        # SSP5-8.5 worst-case 시나리오 기준
        worst_case = site_scenario_data.get("SSP5-8.5", {})

        for risk_type, time_data in worst_case.items():
            # 2040년 AAL 기준
            aal_2040 = time_data.get("2040", 0.0)

            # AAL > 6% (medium 이상) 리스크만 포함
            if aal_2040 > 6.0:
                focus_areas.append(risk_type)

        return sorted(focus_areas)

    def _categorize_actions(
        self,
        priority_level: str,
        focus_areas: List[str],
        site_impact_data: Dict
    ) -> Dict[str, List[str]]:
        """
        권고 조치 카테고리 분류

        :param priority_level: 우선순위 레벨
        :param focus_areas: 집중 대응 필요 리스크 타입
        :param site_impact_data: 사업장 영향 분석 데이터
        :return: 카테고리별 권고 조치
        """
        recommended_actions = {
            "immediate": [],
            "short_term": [],
            "long_term": []
        }

        # 우선순위에 따른 기본 권고사항
        if priority_level == "high":
            recommended_actions["immediate"] = [
                "emergency_response_plan",
                "risk_monitoring_system",
                "insurance_review"
            ]
            recommended_actions["short_term"] = [
                "infrastructure_hardening",
                "backup_systems",
                "staff_training"
            ]
            recommended_actions["long_term"] = [
                "facility_relocation_study",
                "climate_resilient_design",
                "comprehensive_adaptation_strategy"
            ]

        elif priority_level == "medium":
            recommended_actions["immediate"] = [
                "risk_assessment_update",
                "insurance_coverage_check"
            ]
            recommended_actions["short_term"] = [
                "selective_infrastructure_upgrade",
                "monitoring_enhancement"
            ]
            recommended_actions["long_term"] = [
                "strategic_planning",
                "technology_adoption"
            ]

        else:  # low
            recommended_actions["immediate"] = [
                "routine_monitoring"
            ]
            recommended_actions["short_term"] = [
                "preventive_maintenance"
            ]
            recommended_actions["long_term"] = [
                "periodic_reassessment"
            ]

        # 집중 대응 영역에 따른 추가 권고사항
        if "coastal_flood" in focus_areas or "river_flood" in focus_areas or "urban_flood" in focus_areas:
            if "flood_barriers" not in recommended_actions["short_term"]:
                recommended_actions["short_term"].append("flood_barriers")

        if "temperature_change" in focus_areas:
            if "cooling_system_upgrade" not in recommended_actions["short_term"]:
                recommended_actions["short_term"].append("cooling_system_upgrade")

        if "typhoon" in focus_areas or "wildfire" in focus_areas:
            if "structural_reinforcement" not in recommended_actions["short_term"]:
                recommended_actions["short_term"].append("structural_reinforcement")

        return recommended_actions


# 모듈 레벨 실행 함수 (워크플로우에서 호출)
async def run_adaptation_recommendations(
    sites_data: List[Dict],
    scenario_analysis: Dict,
    impact_analysis: Dict,
    llm=None
) -> Dict[str, Any]:
    """
    Node 2-C 실행 함수

    :param sites_data: 사업장 정보 리스트
    :param scenario_analysis: Node 2-A 결과
    :param impact_analysis: Node 2-B 결과
    :param llm: LLM 클라이언트 (선택)
    :return: 적응 권고사항 결과
    """
    node = AdaptationRecommendationsNode(llm=llm)
    return await node.execute(sites_data, scenario_analysis, impact_analysis)
