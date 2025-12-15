"""
Node 2-A: Scenario Analysis (Physical Risk Report)
사업장별 SSP 시나리오 AAL 데이터 계산

설계 목적:
- 물리적 리스크 보고서 전용 (TCFD 전체 제외)
- 4가지 SSP 시나리오별 AAL 계산
- 시점별 데이터 추출 (2020, 2030, 2040, 2050년대)
- ❌ 하드코딩 제거: 텍스트 생성은 Node 3에서 처리
- ❌ 표 생성 제거: Node 3에서 통합 처리

작성일: 2025-12-15 (Physical Risk Report 전용)
버전: v2.0
"""

import asyncio
from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)


class ScenarioAnalysisNode:
    """
    Node 2-A: 시나리오 분석 노드 (물리적 리스크 전용)

    입력:
        - sites_data: List[dict] (사업장 목록)
        - risk_scores: Dict (ModelOps 리스크 점수)

    출력:
        - site_scenario_data: Dict[int, Dict] (사업장별 시나리오 데이터)
          {
              site_id: {
                  "SSP1-2.6": {
                      "temperature_change": {"2020": 1.5, "2030": 2.1, "2040": 2.8},
                      "urban_flood": {...},
                      ...
                  },
                  "SSP2-4.5": {...},
                  "SSP3-7.0": {...},
                  "SSP5-8.5": {...}
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
        risk_scores: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        메인 실행 함수

        :param sites_data: 사업장 정보 리스트
        :param risk_scores: ModelOps 물리적 리스크 점수
        :return: 사업장별 시나리오 데이터
        """
        self.logger.info(f"Node 2-A 시작: {len(sites_data)}개 사업장 시나리오 분석")

        # 1. 사업장별 시나리오 AAL 계산 (병렬)
        site_scenario_results = await self._calculate_scenarios_parallel(
            sites_data,
            risk_scores
        )

        self.logger.info(f"Node 2-A 완료: {len(site_scenario_results)}개 사업장 처리")

        return {
            "site_scenario_data": site_scenario_results,
            "status": "completed"
        }

    async def _calculate_scenarios_parallel(
        self,
        sites_data: List[Dict],
        risk_scores: Optional[Dict]
    ) -> Dict[int, Dict]:
        """
        사업장별 시나리오 AAL 병렬 계산

        :param sites_data: 사업장 정보 리스트
        :param risk_scores: ModelOps 리스크 점수
        :return: 사업장별 시나리오 데이터
        """
        tasks = []
        site_ids = []

        for site in sites_data:
            site_id = site["site_id"]
            site_ids.append(site_id)

            # 해당 사업장의 리스크 점수 추출
            site_risk_scores = risk_scores.get(str(site_id), {}) if risk_scores else {}

            task = self._calculate_site_scenario_aal(site, site_risk_scores)
            tasks.append(task)

        # 병렬 실행
        results_list = await asyncio.gather(*tasks, return_exceptions=True)

        # 결과를 dict로 변환
        site_scenario_results = {}
        for site_id, result in zip(site_ids, results_list):
            if isinstance(result, Exception):
                self.logger.error(f"사업장 {site_id} 시나리오 계산 실패: {result}")
                continue

            site_scenario_results[site_id] = result

        return site_scenario_results

    async def _calculate_site_scenario_aal(
        self,
        site: Dict,
        site_risk_scores: Dict
    ) -> Dict:
        """
        단일 사업장의 시나리오별 AAL 계산

        :param site: 사업장 정보
        :param site_risk_scores: 사업장 리스크 점수
        :return: 시나리오별 리스크 타입별 AAL
        """
        site_id = site["site_id"]

        # SSP 시나리오 목록
        ssp_scenarios = ["SSP1-2.6", "SSP2-4.5", "SSP3-7.0", "SSP5-8.5"]

        # 리스크 타입 목록
        risk_types = [
            "temperature_change",
            "sea_level_rise",
            "urban_flood",
            "river_flood",
            "coastal_flood",
            "drought",
            "wildfire",
            "typhoon",
            "water_stress"
        ]

        # 시점 목록 (물리적 리스크 보고서: 2100년 제외)
        time_points = ["2020", "2030", "2040"]

        # 결과 구조 생성
        scenario_data = {}

        for scenario in ssp_scenarios:
            scenario_data[scenario] = {}

            for risk_type in risk_types:
                scenario_data[scenario][risk_type] = {}

                for time_point in time_points:
                    # ModelOps 데이터에서 AAL 추출
                    # 형식: site_risk_scores[risk_type][scenario][time_point]
                    aal_value = self._extract_aal_from_risk_scores(
                        site_risk_scores,
                        risk_type,
                        scenario,
                        time_point
                    )

                    scenario_data[scenario][risk_type][time_point] = aal_value

        return scenario_data

    def _extract_aal_from_risk_scores(
        self,
        site_risk_scores: Dict,
        risk_type: str,
        scenario: str,
        time_point: str
    ) -> float:
        """
        ModelOps 리스크 점수에서 AAL 추출

        :param site_risk_scores: 사업장 리스크 점수
        :param risk_type: 리스크 타입
        :param scenario: SSP 시나리오
        :param time_point: 시점
        :return: AAL % (0~100)
        """
        try:
            # ModelOps 데이터 구조에 맞게 추출
            # 예시: site_risk_scores[risk_type][scenario][time_point]["aal_percent"]

            if risk_type in site_risk_scores:
                risk_data = site_risk_scores[risk_type]

                if isinstance(risk_data, dict) and scenario in risk_data:
                    scenario_data = risk_data[scenario]

                    if isinstance(scenario_data, dict) and time_point in scenario_data:
                        time_data = scenario_data[time_point]

                        if isinstance(time_data, dict):
                            return time_data.get("aal_percent", 0.0)
                        elif isinstance(time_data, (int, float)):
                            return float(time_data)

            return 0.0

        except Exception as e:
            self.logger.warning(
                f"AAL 추출 실패 ({risk_type}, {scenario}, {time_point}): {e}"
            )
            return 0.0


# 모듈 레벨 실행 함수 (워크플로우에서 호출)
async def run_scenario_analysis(
    sites_data: List[Dict],
    risk_scores: Optional[Dict] = None,
    llm=None
) -> Dict[str, Any]:
    """
    Node 2-A 실행 함수

    :param sites_data: 사업장 정보 리스트
    :param risk_scores: ModelOps 리스크 점수
    :param llm: LLM 클라이언트 (선택)
    :return: 시나리오 분석 결과
    """
    node = ScenarioAnalysisNode(llm=llm)
    return await node.execute(sites_data, risk_scores)
