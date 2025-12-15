"""
Node 3: Physical Risk Assessment Generator (Physical Risk Report)
사업장별 리스크 평가 및 표 생성

설계 목적:
- 물리적 리스크 보고서 전용 (TCFD 전체 제외)
- Node 2-A/B/C 결과 통합
- risk_table_generator 활용하여 sites_risk_assessment 생성
- 사업장별 color-coded 리스크 표 생성
- ✅ 최종 JSON 출력 (Excel 생성용)

작성일: 2025-12-15 (Physical Risk Report 전용)
버전: v2.0
"""

from typing import Dict, Any, List, Optional
import logging

# risk_table_generator import
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../utils'))
from risk_table_generator import generate_sites_risk_assessment, validate_risk_table

logger = logging.getLogger(__name__)


class PhysicalRiskAssessmentNode:
    """
    Node 3: 물리적 리스크 평가 생성 노드

    입력:
        - sites_data: List[dict] (사업장 목록)
        - scenario_analysis: Dict (Node 2-A 출력)
        - impact_analysis: Dict (Node 2-B 출력)
        - adaptation_recommendations: Dict (Node 2-C 출력)

    출력:
        - sites_risk_assessment: List[Dict] (사업장별 리스크 평가)
          [
              {
                  "site_id": 1,
                  "site_name": "대덕 데이터센터",
                  "site_type": "Data Center",
                  "address": "...",
                  "location": {"latitude": 36.37, "longitude": 127.36},
                  "risk_table": {
                      "SSP1-2.6": {
                          "chronic_risks": {...},
                          "acute_risks": {...}
                      },
                      ...
                  },
                  "vulnerability_summary": {
                      "high_risk_factors": [...],
                      "resilience_factors": [...]
                  }
              },
              ...
          ]
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
        impact_analysis: Dict,
        adaptation_recommendations: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        메인 실행 함수

        :param sites_data: 사업장 정보 리스트
        :param scenario_analysis: Node 2-A 시나리오 분석 결과
        :param impact_analysis: Node 2-B 영향 분석 결과
        :param adaptation_recommendations: Node 2-C 적응 권고사항 (선택)
        :return: 물리적 리스크 평가 결과
        """
        self.logger.info(f"Node 3 시작: {len(sites_data)}개 사업장 리스크 평가 생성")

        # 1. Node 2-A/B 결과 추출
        scenario_analysis_results = scenario_analysis.get("site_scenario_data", {})
        impact_analysis_results = impact_analysis.get("site_impact_data", {})

        # 2. sites_risk_assessment 생성 (risk_table_generator 활용)
        sites_risk_assessment = generate_sites_risk_assessment(
            sites_data=sites_data,
            scenario_analysis_results=scenario_analysis_results,
            impact_analysis_results=impact_analysis_results
        )

        # 3. 유효성 검증
        validation_results = self._validate_assessments(sites_risk_assessment)

        self.logger.info(
            f"Node 3 완료: {len(sites_risk_assessment)}개 사업장 평가 생성 "
            f"(검증: {validation_results['valid_count']}/{validation_results['total_count']})"
        )

        return {
            "sites_risk_assessment": sites_risk_assessment,
            "validation_results": validation_results,
            "status": "completed"
        }

    def _validate_assessments(self, sites_risk_assessment: List[Dict]) -> Dict[str, Any]:
        """
        생성된 리스크 평가 유효성 검증

        :param sites_risk_assessment: 사업장별 리스크 평가 리스트
        :return: 검증 결과
        """
        valid_count = 0
        invalid_sites = []

        for site_assessment in sites_risk_assessment:
            site_id = site_assessment.get("site_id")
            risk_table = site_assessment.get("risk_table", {})

            # risk_table 유효성 검증
            is_valid = validate_risk_table(risk_table)

            if is_valid:
                valid_count += 1
            else:
                invalid_sites.append(site_id)
                self.logger.warning(f"사업장 {site_id} 리스크 표 유효성 검증 실패")

        return {
            "total_count": len(sites_risk_assessment),
            "valid_count": valid_count,
            "invalid_count": len(invalid_sites),
            "invalid_sites": invalid_sites
        }


# 모듈 레벨 실행 함수 (워크플로우에서 호출)
async def run_physical_risk_assessment(
    sites_data: List[Dict],
    scenario_analysis: Dict,
    impact_analysis: Dict,
    adaptation_recommendations: Optional[Dict] = None,
    llm=None
) -> Dict[str, Any]:
    """
    Node 3 실행 함수

    :param sites_data: 사업장 정보 리스트
    :param scenario_analysis: Node 2-A 결과
    :param impact_analysis: Node 2-B 결과
    :param adaptation_recommendations: Node 2-C 결과 (선택)
    :param llm: LLM 클라이언트 (선택)
    :return: 물리적 리스크 평가 결과
    """
    node = PhysicalRiskAssessmentNode(llm=llm)
    return await node.execute(
        sites_data,
        scenario_analysis,
        impact_analysis,
        adaptation_recommendations
    )
