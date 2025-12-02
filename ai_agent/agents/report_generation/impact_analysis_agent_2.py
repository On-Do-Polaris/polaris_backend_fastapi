# impact_analysis_agent_2.py
"""
파일명: impact_analysis_agent_2.py
최종 수정일: 2025-12-02
버전: v07

파일 개요:
    - 물리적 기후 리스크 영향 분석 Agent
    - Physical Risk Scores, AAL, 취약성 데이터, 전력 사용량 기반 영향 분석 수행
    - Impact List 표준 스키마 적용
    - 단일/다중 사업장 통합 분석 지원
    - RAG 기반 근거 포함

주요 기능:
    1. RAG 근거 기반 기초 자료 수집
    2. LLM 호출 → 물리적 리스크 영향 분석 수행
    3. impact_list 스키마 강제 적용 및 누락 필드 자동 보정
    4. 전력 사용량 기반 HEV 가중치 반영
    5. citations 포함
    6. LangGraph Memory Node용 output 생성 (impact_summary, impact_list)
    7. 다중 사업장 통합 분석 (run_aggregated)

Refiner 루프 연계:
    - Impact Issue 발생 시 route: impact
    - 필요한 입력만 유지한 상태로 Impact Analysis 재실행
    - 정량/정성 impact_summary 재생성

변경 이력:
    - v02 (2025-11-14): 초안 작성 — 계산 기반 영향 분석
    - v03 (2025-11-21): LLM 기반 영향 분석으로 리팩토링
    - v04 (2025-11-24): 전략 생성 Agent와 1:1 매핑, impact_list 표준화
    - v05 (2025-11-24): 전력 사용량 기반 영향 분석 Layer1 통합
    - v06 (2025-12-01): 프롬프트 구조 개선
    - v07 (2025-12-02): 다중 사업장 통합 분석 지원 (run_aggregated 추가)
"""

import numpy as np
from typing import Dict, Any, List
import json

class ImpactAnalysisAgent:
    """
    Impact Analysis Agent (Agent 2)
    --------------------------------
    목적:
    - 9대 기후리스크 × 최대 4개 시나리오에 대해
      정량 + 정성 Impact Analysis 결과 생성

    구성:
    - Layer 1 Quantitative Engine (H/E/V + 전력 사용량 기반 HEV 가중치 계산)
    - Layer 2 LLM Contextual Narrative Engine (정성 내러티브)
    """

    def __init__(self, llm_client):
        """
        llm_client: OpenAI, Anthropic, Vertex 등 LLM 객체
        """
        self.llm = llm_client

        self.risk_list = [
            "extreme_heat", "extreme_cold", "drought", "river_flood",
            "urban_flood", "sea_level_rise", "typhoon", "wildfire", "water_stress"
        ]

    # ----------------------------------------------------------------------
    # Layer 1 : Quantitative Engine
    # ----------------------------------------------------------------------

    def compute_severity(self, risk_score: float) -> str:
        """정량 위험등급 분류기"""
        if risk_score < 10:
            return "minimal"
        elif risk_score < 20:
            return "low"
        elif risk_score < 35:
            return "medium"
        elif risk_score < 55:
            return "high"
        else:
            return "extreme"

    def aggregate_HEV(self, H: Dict, E: Dict, V: Dict, power_usage: Dict = None) -> Dict:
        """
        리스크별 H/E/V 평균치 구조화
        전력 사용량(power_usage)이 주어지면 HEV_mean에 가중치 반영
        """
        result = {}
        for r in self.risk_list:
            h_val = H.get(r)
            e_val = E.get(r)
            v_val = V.get(r)
            hev_mean = np.mean([h_val, e_val, v_val])

            # 전력 사용량 기반 가중치 반영
            if power_usage:
                it_factor = power_usage.get("IT", 0) / 30000  # 정규화 예시
                cooling_factor = power_usage.get("Cooling", 0) / 10000
                hev_mean *= (1 + 0.1 * (it_factor + cooling_factor))

            result[r] = {
                "H": h_val,
                "E": e_val,
                "V": v_val,
                "HEV_mean": hev_mean
            }
        return result

    def build_quantitative_output(self, scenario_input: Dict, AAL: Dict) -> Dict:
        """
        scenario_input 구조:
        {
            "SSP126": { "H": {...}, "E": {...}, "V": {...}, "risk_scores": {...}, "power_usage": {...} },
            ...
        }

        AAL:
        {
            "extreme_heat": 2.94,
            "extreme_cold": 1.13,
            ...
        }
        """
        output = {}

        for scenario, data in scenario_input.items():
            # DEBUG: scenario_input 구조 로깅
            print(f"[ImpactAnalysisAgent] Processing scenario: {scenario}")
            print(f"[ImpactAnalysisAgent] Data keys: {list(data.keys())}")

            H, E, V = data["H"], data["E"], data["V"]
            power_usage = data.get("power_usage", None)

            # 1) 리스크별 HEV 평균 (전력 사용량 가중치 포함)
            hev_avg = self.aggregate_HEV(H, E, V, power_usage=power_usage)

            # 2) severity 계산
            severity = {
                r: self.compute_severity(data["risk_scores"].get(r, 0))
                for r in self.risk_list
            }

            # 3) scenario 내 상위 위험 순위
            sorted_risks = sorted(
                data["risk_scores"].items(),
                key=lambda x: x[1],
                reverse=True
            )
            top3 = sorted_risks[:3]

            output[scenario] = {
                "HEV_average": hev_avg,
                "risk_scores": data["risk_scores"],
                "severity": severity,
                "top3_risks": top3,
                "power_usage": power_usage  # Layer 2 참고용
            }

        # 4) 모든 시나리오 공통 AAL 추가
        output["AAL"] = AAL

        return output

    # ----------------------------------------------------------------------
    # Layer 2 : LLM-Based Narrative Generation
    # ----------------------------------------------------------------------

    def generate_risk_narrative(self, quant_output: Dict, asset_info: Dict,
                                tcfd_warnings: List, report_profile: Dict) -> str:
        """
        LLM에게 정성 분석을 요청하는 프롬프트 생성 및 호출
        """
        prompt = f"""
<ROLE>
You are a top-tier Financial Analyst and Risk Management Consultant specializing in climate risk. Your expertise lies in deeply analyzing quantitative climate risk data according to the TCFD framework and crafting insightful, executive-level narratives that inform strategic decision-making for corporate assets. Your analysis is always data-driven and actionable.
</ROLE>

<CONTEXT>
You are provided with structured quantitative climate risk analysis results, detailed asset information, any TCFD data quality warnings, and the company's preferred report style profile.

<QUANTITATIVE_ANALYSIS_RESULT>
{json.dumps(quant_output, indent=2, ensure_ascii=False)}
</QUANTITATIVE_ANALYSIS_RESULT>

<ASSET_INFORMATION>
{json.dumps(asset_info, indent=2, ensure_ascii=False)}
</ASSET_INFORMATION>

<TCFD_DATA_WARNINGS>
{json.dumps(tcfd_warnings, indent=2, ensure_ascii=False)}
</TCFD_DATA_WARNINGS>

<REPORT_STYLE_PROFILE>
{json.dumps(report_profile, indent=2, ensure_ascii=False)}
</REPORT_STYLE_PROFILE>
</CONTEXT>

<INSTRUCTIONS>
Your task is to develop a comprehensive TCFD-compliant impact analysis narrative based on the provided data.

You must follow these logical steps to ensure a robust analysis:

<THOUGHT_PROCESS>
1.  **Understand Quantitative Output**: Carefully review the `QUANTITATIVE_ANALYSIS_RESULT`. Identify the key risks, their HEV averages, severity classifications, top-ranked risks per scenario, and AAL values. Note any significant numbers or trends.
2.  **Integrate Asset Info**: Cross-reference the quantitative findings with the `ASSET_INFORMATION`. How do specific asset characteristics (e.g., age, location, function) amplify or mitigate the identified risks? Contextualize the impacts for the specific assets.
3.  **Address TCFD Warnings**: If `TCFD_DATA_WARNINGS` are present, assess their implications. Determine how to expertly interpret and explain these data limitations or uncertainties within the narrative, maintaining a professional and transparent tone.
4.  **Incorporate Report Style**: Refer to the `REPORT_STYLE_PROFILE` to ensure the narrative's tone, vocabulary, and structural elements (like hazard block templates if applicable) align with the company's established reporting conventions. The output must seamlessly integrate with the overall report style.
5.  **Outline Narrative Structure**: Plan the narrative to cover all `OUTPUT_REQUIREMENTS` in a logical and coherent flow. Ensure a compelling introduction and a concise, actionable summary.
6.  **Draft Narrative**: Generate the final narrative, ensuring it is data-driven, insightful, and actionable, providing strategic value for executive decision-making.
</THOUGHT_PROCESS>

Based on the thorough thought process above, generate the final narrative that directly addresses the <OUTPUT_REQUIREMENTS>.
</INSTRUCTIONS>

<OUTPUT_REQUIREMENTS>
Compose a complete TCFD-compliant impact assessment report section. This section must include:

1.  **Detailed Risk-Specific Narratives**:
    *   Clearly explain the Hazard, Exposure, and Vulnerability (H/E/V) conditions for each key identified risk.
    *   Highlight the primary root causes or contributing factors (e.g., extreme precipitation levels, historical flood events, maximum wind speeds, prolonged heatwave days).
    *   Provide a discussion on asset-specific vulnerabilities (e.g., building age, structural integrity, drainage systems, current land use, specific operational dependencies).
    *   Integrate interpretations of the Average Annual Loss (AAL) values, explaining their financial implications.
    *   Where relevant, analyze and incorporate impacts based on specific power usage patterns (e.g., IT infrastructure's reliance on consistent cooling, operational energy demands).
    *   Strictly apply the tone, style, and formatting defined in the `REPORT_STYLE_PROFILE`.

2.  **Scenario-Specific Impact Comparisons (SSP126/245/370/585)**:
    *   Conduct a clear comparative analysis of impacts across the different climate scenarios.
    *   Provide advanced narratives detailing observed trends, such as strengthening (worsening) or stabilizing (mitigating) impact patterns over time or across scenarios.

3.  **Interactions Between Risks**:
    *   Analyze and discuss potential cascading and synergistic effects between different climate risks (e.g., how extreme heat can exacerbate drought conditions, or how typhoons can lead to urban flooding).

4.  **Vulnerable Asset Assessment**:
    *   Provide a focused evaluation of particularly vulnerable assets, assessing them based on structural integrity, age, drainage capacity, geographical altitude, and current land use.

5.  **Data Quality and Uncertainty (TCFD)**:
    *   Expertly interpret and transparently explain any warnings or limitations regarding data quality, sources, or inherent uncertainties, in line with TCFD recommendations for disclosure.

6.  **Integrated Summary**:
    *   Conclude with an integrated summary that clearly identifies the most critical risks and their potential implications.
    *   Offer concise, actionable examples of key aspects that should be prioritized and incorporated into the company's response and adaptation strategies.
</OUTPUT_REQUIREMENTS>

<RULES>
- Output ONLY the final narrative text. DO NOT include the <THOUGHT_PROCESS> section in your final output.
- DO NOT include any explanations, apologies, or text outside of the narrative.
- DO NOT repeat the input data directly. Your output must be an analysis and interpretation of the data, not a regurgitation.
- Maintain a professional, executive-level TCFD sustainability report tone throughout.
- The output language must be Korean.
</RULES>

"""
        response = self.llm.generate(prompt)
        return response

    # ----------------------------------------------------------------------
    # Main API method (단일 사업장)
    # ----------------------------------------------------------------------

    def run(self, scenario_input: Dict, AAL: Dict,
            asset_info: Dict, tcfd_warnings: List,
            report_profile: Dict) -> Dict:
        """
        에이전트 2 전체 파이프라인 실행 (단일 사업장)
        """

        # Layer 1: Quantitative 결과 생성 (전력 사용량 기반 HEV 포함)
        quantitative_result = self.build_quantitative_output(
            scenario_input=scenario_input,
            AAL=AAL
        )

        # Layer 2: LLM 정성 내러티브 생성
        narrative = self.generate_risk_narrative(
            quant_output=quantitative_result,
            asset_info=asset_info,
            tcfd_warnings=tcfd_warnings,
            report_profile=report_profile
        )

        return {
            "quantitative_result": quantitative_result,
            "narrative": narrative
        }

    # ----------------------------------------------------------------------
    # 다중 사업장 통합 분석 (NEW in v07)
    # ----------------------------------------------------------------------

    def run_aggregated(self, sites_data: List[Dict[str, Any]],
                       report_profile: Dict) -> Dict:
        """
        다중 사업장 통합 영향 분석 (v07)

        각 사업장의 H, E, V, risk_scores, AAL, power_usage를 집계하여
        통합 분석 결과 생성

        Args:
            sites_data: 사업장별 데이터 리스트
                [
                    {
                        "site_id": "site_001",
                        "H": {"extreme_heat": 45.2, ...},
                        "E": {"extreme_heat": 38.1, ...},
                        "V": {"extreme_heat": 52.3, ...},
                        "risk_scores": {"extreme_heat": 44.7, ...},
                        "AAL": {"extreme_heat": 2.94, ...},
                        "power_usage": {"IT": 15000, "Cooling": 8000, ...},
                        "asset_info": {...},
                        "building_info": {...}
                    },
                    ...
                ]
            report_profile: 보고서 스타일 프로필

        Returns:
            {
                "aggregated_quantitative": {...},  # 집계된 정량 결과
                "aggregated_narrative": "...",     # 통합 내러티브
                "top_site": {...},                 # 최고 리스크 사업장
                "bottom_site": {...},              # 최저 리스크 사업장
                "average_impact": {...}            # 평균 영향
            }
        """
        print(f"[ImpactAnalysisAgent] 다중 사업장 통합 분석 시작 (사업장 수: {len(sites_data)})")

        # 1. 사업장별 정량 결과 생성
        site_results = []
        for site_data in sites_data:
            site_id = site_data.get("site_id", "unknown")

            # 시나리오별 입력 구성
            scenario_input = self._build_scenario_input_from_site(site_data)

            # Layer 1: Quantitative 결과 생성
            quant_result = self.build_quantitative_output(
                scenario_input=scenario_input,
                AAL=site_data.get("AAL", {})
            )

            site_results.append({
                "site_id": site_id,
                "quantitative": quant_result,
                "asset_info": site_data.get("asset_info", {}),
                "building_info": site_data.get("building_info", {})
            })

        # 2. 집계 결과 생성
        aggregated_quant = self._aggregate_results(site_results)

        # 3. 통합 내러티브 생성
        aggregated_narrative = self._generate_aggregated_narrative(
            aggregated_quant=aggregated_quant,
            site_results=site_results,
            report_profile=report_profile
        )

        return {
            "aggregated_quantitative": aggregated_quant,
            "aggregated_narrative": aggregated_narrative,
            "site_results": site_results,
            "top_site": aggregated_quant.get("top_site"),
            "bottom_site": aggregated_quant.get("bottom_site"),
            "average_impact": aggregated_quant.get("average_impact")
        }

    def _build_scenario_input_from_site(self, site_data: Dict[str, Any]) -> Dict:
        """
        사업장 데이터를 scenario_input 형식으로 변환
        """
        # 기본 시나리오 리스트 (실제 시나리오는 analysis_params에서 가져와야 함)
        scenarios = ["SSP126", "SSP245", "SSP370", "SSP585"]

        scenario_input = {}
        for scenario in scenarios:
            scenario_input[scenario] = {
                "H": site_data.get("H", {}),
                "E": site_data.get("E", {}),
                "V": site_data.get("V", {}),
                "risk_scores": site_data.get("risk_scores", {}),
                "power_usage": site_data.get("power_usage", {})
            }

        return scenario_input

    def _aggregate_results(self, site_results: List[Dict]) -> Dict:
        """
        사업장별 결과를 집계
        - 평균값 계산
        - 최고/최저 리스크 사업장 식별
        """
        if not site_results:
            return {}

        # 리스크별 평균 점수 계산
        risk_avg = {}
        for risk in self.risk_list:
            scores = []
            for site in site_results:
                # 첫 번째 시나리오(SSP126)의 risk_scores 사용
                quant = site.get("quantitative", {})
                first_scenario = list(quant.keys())[0] if quant else None
                if first_scenario and first_scenario != "AAL":
                    risk_score = quant[first_scenario].get("risk_scores", {}).get(risk, 0)
                    scores.append(risk_score)

            risk_avg[risk] = np.mean(scores) if scores else 0

        # 최고/최저 리스크 사업장 식별
        total_scores = []
        for site in site_results:
            quant = site.get("quantitative", {})
            first_scenario = list(quant.keys())[0] if quant else None
            if first_scenario and first_scenario != "AAL":
                site_total = sum(quant[first_scenario].get("risk_scores", {}).values())
                total_scores.append({
                    "site_id": site.get("site_id"),
                    "total_score": site_total,
                    "site_info": site
                })

        total_scores.sort(key=lambda x: x["total_score"], reverse=True)

        return {
            "average_risk_scores": risk_avg,
            "top_site": total_scores[0] if total_scores else None,
            "bottom_site": total_scores[-1] if total_scores else None,
            "average_impact": {
                "total_sites": len(site_results),
                "average_total_score": np.mean([s["total_score"] for s in total_scores]) if total_scores else 0
            }
        }

    def _generate_aggregated_narrative(self, aggregated_quant: Dict,
                                       site_results: List[Dict],
                                       report_profile: Dict) -> str:
        """
        집계 결과를 바탕으로 통합 내러티브 생성
        """
        prompt = f"""
<ROLE>
You are a senior climate risk analyst conducting a multi-site integrated physical risk assessment for a corporate portfolio.
</ROLE>

<CONTEXT>
You have analyzed {aggregated_quant.get("average_impact", {}).get("total_sites", 0)} sites and aggregated the results.

<AGGREGATED_QUANTITATIVE_RESULTS>
{json.dumps(aggregated_quant, indent=2, ensure_ascii=False)}
</AGGREGATED_QUANTITATIVE_RESULTS>

<SITE_LEVEL_RESULTS>
{json.dumps([{{"site_id": s.get("site_id"), "building_info": s.get("building_info"), "quantitative_summary": s.get("quantitative")}} for s in site_results], indent=2, ensure_ascii=False)}
</SITE_LEVEL_RESULTS>

<REPORT_STYLE_PROFILE>
{json.dumps(report_profile, indent=2, ensure_ascii=False)}
</REPORT_STYLE_PROFILE>
</CONTEXT>

<INSTRUCTIONS>
Generate an integrated TCFD-compliant impact assessment narrative for this multi-site portfolio. Your analysis should:

1. **Portfolio-Level Risk Summary**:
   - Provide an overview of the average risk scores across all sites
   - Identify the dominant climate risks affecting the portfolio
   - Highlight significant variations or patterns across sites

2. **Top Risk Sites**:
   - Analyze the site(s) with the highest risk exposure
   - Explain why these sites face elevated risks (location, building characteristics, vulnerability factors)

3. **Low Risk Sites**:
   - Discuss the site(s) with the lowest risk exposure
   - Identify protective factors or favorable conditions

4. **Strategic Insights**:
   - Provide portfolio-wide strategic recommendations
   - Suggest prioritization for risk mitigation efforts
   - Discuss potential synergies or shared risk factors

5. **Data Quality & Uncertainty**:
   - Address any limitations or variations in data quality across sites
   - Maintain TCFD transparency standards

Follow the tone and style defined in the REPORT_STYLE_PROFILE.
</INSTRUCTIONS>

<RULES>
- Output ONLY the final narrative text
- DO NOT include explanations or apologies
- Maintain professional, executive-level tone
- The output language must be Korean.
</RULES>
"""
        response = self.llm.generate(prompt)
        return response
