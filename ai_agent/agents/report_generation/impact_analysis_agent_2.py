# impact_analysis_agent_2.py
"""
파일명: impact_analysis_agent_2.py
최종 수정일: 2025-12-01
버전: v06

파일 개요:
    - 물리적 기후 리스크 영향 분석 Agent
    - Physical Risk Scores, AAL, 취약성 데이터, 전력 사용량 기반 영향 분석 수행
    - Impact List 표준 스키마 적용
    - 향후 Strategy Generation Agent와 1:1 매핑을 위한 구조 확정
    - RAG 기반 근거 포함

주요 기능:
    1. RAG 근거 기반 기초 자료 수집
    2. LLM 호출 → 물리적 리스크 영향 분석 수행
    3. impact_list 스키마 강제 적용 및 누락 필드 자동 보정
    4. 전력 사용량 기반 HEV 가중치 반영
    5. citations 포함
    6. LangGraph Memory Node용 output 생성 (impact_summary, impact_list)

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
            "extreme_heat", "extreme_cold", "drought", "inland_flood",
            "urban_flood", "coastal_flood", "typhoon", "wildfire", "water_stress"
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
    # Main API method
    # ----------------------------------------------------------------------

    def run(self, scenario_input: Dict, AAL: Dict,
            asset_info: Dict, tcfd_warnings: List,
            report_profile: Dict) -> Dict:
        """
        에이전트 2 전체 파이프라인 실행
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
