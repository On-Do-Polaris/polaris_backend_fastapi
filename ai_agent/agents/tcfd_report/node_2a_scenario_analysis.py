"""
Node 2-A: Scenario Analysis
전체 사업장의 시나리오별 AAL 추이 분석

설계 이유:
- 항목별 순차 처리: v1의 사이트별 병렬에서 변경
- 포트폴리오 관점: 8개 사업장 전체를 통합 분석
- 4가지 SSP 시나리오: 다양한 기후 시나리오 추이 분석
- TableBlock 생성: 시나리오별 AAL 비교표를 JSON으로 생성

작성일: 2025-12-14 (v2 Refactoring)
"""

import asyncio
from typing import Dict, Any, List, Optional
from .schemas import TableBlock, TableData, TableRow


class ScenarioAnalysisNode:
    """
    Node 2-A: 시나리오 분석 노드

    입력:
        - sites_data: List[dict] (8개 사업장)
        - agent_guideline: Optional[dict] (Excel 있을 경우만)

    출력:
        - scenarios: Dict (SSP1-2.6, SSP2-4.5, SSP3-7.0, SSP5-8.5)
        - comparison: str (시나리오 간 비교 분석)
    """

    def __init__(self, llm):
        self.llm = llm

    async def execute(
        self,
        sites_data: List[Dict],
        agent_guideline: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        메인 실행 함수
        """
        # 1. 사업장별 시나리오 AAL 계산 (병렬)
        site_scenario_results = await self._calculate_scenarios_parallel(sites_data)

        # 2. 포트폴리오 통합 분석
        scenarios = self._aggregate_scenarios(site_scenario_results)

        # 3. LLM 기반 시나리오 비교 분석
        comparison = await self._analyze_scenarios_with_llm(scenarios, agent_guideline)

        # 4. TableBlock 생성 (시나리오별 AAL 비교표)
        scenario_table = self._create_scenario_table(scenarios)

        return {
            "scenarios": scenarios,
            "comparison": comparison,
            "scenario_table": scenario_table  # JSON TableBlock
        }

    async def _calculate_scenarios_parallel(self, sites_data: List[Dict]) -> List[Dict]:
        """
        8개 사업장 시나리오 AAL 병렬 계산 (~15초)
        """
        tasks = [self._calculate_site_scenario_aal(site) for site in sites_data]
        results = await asyncio.gather(*tasks)
        return results

    async def _calculate_site_scenario_aal(self, site: Dict) -> Dict:
        """
        단일 사업장의 시나리오별 AAL 계산
        """
        # TODO: AAL 데이터에서 시나리오별 추출
        return {
            "site_id": site["site_id"],
            "ssp1_2.6": {"timeline": [2024, 2030, 2050, 2100], "aal_values": []},
            "ssp2_4.5": {"timeline": [2024, 2030, 2050, 2100], "aal_values": []},
            "ssp3_7.0": {"timeline": [2024, 2030, 2050, 2100], "aal_values": []},
            "ssp5_8.5": {"timeline": [2024, 2030, 2050, 2100], "aal_values": []}
        }

    def _aggregate_scenarios(self, site_results: List[Dict]) -> Dict:
        """
        포트폴리오 시나리오 집계
        """
        # TODO: 사업장별 AAL 합산 → 포트폴리오 AAL
        return {
            "ssp1_2.6": {
                "summary": "",
                "timeline": [2024, 2030, 2040, 2050, 2100],
                "aal_values": [],  # TODO
                "key_points": ""
            },
            "ssp2_4.5": {},
            "ssp3_7.0": {},
            "ssp5_8.5": {}
        }

    async def _analyze_scenarios_with_llm(
        self,
        scenarios: Dict,
        agent_guideline: Optional[Dict]
    ) -> str:
        """
        LLM 기반 시나리오 비교 분석
        """
        # 시나리오 요약 정보 추출
        scenario_summaries = []
        for scenario_key in ["ssp1_2.6", "ssp2_4.5", "ssp3_7.0", "ssp5_8.5"]:
            scenario_data = scenarios.get(scenario_key, {})
            timeline = scenario_data.get("timeline", [])
            aal_values = scenario_data.get("aal_values", [])

            if timeline and aal_values:
                scenario_summaries.append(
                    f"**{scenario_key.upper()}**: {timeline[0]}년 {aal_values[0]:.2f}% → "
                    f"{timeline[-1]}년 {aal_values[-1]:.2f}% "
                    f"(증가율: {((aal_values[-1] - aal_values[0]) / aal_values[0] * 100):.1f}%)"
                )

        scenario_summary_text = "\n".join(scenario_summaries)

        # 추가 가이드라인 (Excel 데이터가 있을 경우)
        additional_context = ""
        if agent_guideline:
            summary = agent_guideline.get("summary", "")
            if summary:
                additional_context = f"\n\n**추가 고려 사항:**\n{summary}"

        # LLM 프롬프트
        prompt = f"""당신은 TCFD 보고서 작성 전문가이며, 기후 시나리오 분석을 담당하고 있습니다.

**임무:**
4가지 SSP 시나리오(SSP1-2.6, SSP2-4.5, SSP3-7.0, SSP5-8.5)별로 포트폴리오 AAL(Annual Average Loss) 추이를 비교 분석하고,
TCFD Strategy 섹션에 포함될 **시나리오 분석 서술문**을 작성하세요.

**시나리오별 AAL 추이:**
{scenario_summary_text}{additional_context}

**출력 요구사항:**
1. **각 시나리오별 주요 특징** (3-4문장)
   - SSP1-2.6 (지속가능 발전): 파리협정 목표 달성 시나리오
   - SSP2-4.5 (중간 경로): 현재 정책 유지 시나리오
   - SSP3-7.0 (지역 경쟁): 기후 정책 미흡 시나리오
   - SSP5-8.5 (화석연료 의존): 최악의 시나리오

2. **시나리오 간 비교 분석** (5-7문장)
   - 가장 낙관적 시나리오(SSP1-2.6)와 가장 비관적 시나리오(SSP5-8.5) 간 AAL 차이
   - 중간 시나리오(SSP2-4.5)가 현실적으로 예상되는 경로임을 강조
   - 시나리오별 AAL 증가율 비교

3. **전략적 시사점** (3-5문장)
   - 기후변화 대응의 시급성
   - 시나리오 불확실성에 대비한 적응 전략 필요성
   - SSP2-4.5를 기준 시나리오로 채택하는 이유

**출력 형식:**
일반 텍스트 (마크다운 불필요, 문단 구분은 줄바꿈 2개)

**톤 & 스타일:**
- 객관적이고 전문적인 어조
- 정량적 데이터 기반 서술
- TCFD 보고서에 적합한 형식적 문체
"""

        # LLM 호출
        response = await self.llm.ainvoke(prompt)

        # 응답 텍스트 추출
        if hasattr(response, 'content'):
            return response.content
        elif isinstance(response, str):
            return response
        else:
            return str(response)

    def _create_scenario_table(self, scenarios: Dict) -> Dict:
        """
        시나리오별 AAL 비교 TableBlock 생성

        Returns:
            TableBlock JSON (schemas.py의 TableBlock 형식)
        """
        # 테이블 헤더
        headers = ["시나리오", "2024", "2030", "2040", "2050", "2100", "증가율"]

        # 시나리오 이름 매핑
        scenario_names = {
            "ssp1_2.6": "SSP1-2.6 (지속가능)",
            "ssp2_4.5": "SSP2-4.5 (중간)",
            "ssp3_7.0": "SSP3-7.0 (지역경쟁)",
            "ssp5_8.5": "SSP5-8.5 (화석연료)"
        }

        # 테이블 행 생성
        rows = []
        for scenario_key, scenario_name in scenario_names.items():
            scenario_data = scenarios.get(scenario_key, {})
            timeline = scenario_data.get("timeline", [2024, 2030, 2040, 2050, 2100])
            aal_values = scenario_data.get("aal_values", [0, 0, 0, 0, 0])

            # 증가율 계산 (2024 대비 2100)
            if len(aal_values) >= 2 and aal_values[0] > 0:
                growth_rate = ((aal_values[-1] - aal_values[0]) / aal_values[0]) * 100
                growth_str = f"+{growth_rate:.1f}%" if growth_rate > 0 else f"{growth_rate:.1f}%"
            else:
                growth_str = "N/A"

            # 행 데이터 생성
            row_cells = [scenario_name]
            for aal in aal_values:
                row_cells.append(f"{aal:.1f}%")
            row_cells.append(growth_str)

            rows.append({"cells": row_cells})

        # TableBlock 생성
        table_block = {
            "type": "table",
            "title": "시나리오별 포트폴리오 AAL 추이 비교",
            "data": {
                "headers": headers,
                "rows": rows
            }
        }

        return table_block
