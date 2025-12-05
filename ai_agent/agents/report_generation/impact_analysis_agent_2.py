# impact_analysis_agent_2.py
"""
파일명: impact_analysis_agent_2.py
최종 수정일: 2025-12-05
버전: v08

파일 개요:
    - 물리적 기후 리스크 영향 분석 Agent
    - Physical Risk Scores, AAL, 취약성 데이터, 전력 사용량 기반 영향 분석 수행
    - Impact List 표준 스키마 적용
    - 단일/다중 사업장 통합 분석 지원
    - RAG 기반 근거 포함
    - v08: 정량 데이터 기반 정성 분석 강화 (H×E×V 원인 분석, 사업장 비교, AAL 재무 영향)

주요 기능:
    1. RAG 근거 기반 기초 자료 수집
    2. LLM 호출 → 물리적 리스크 영향 분석 수행
    3. impact_list 스키마 강제 적용 및 누락 필드 자동 보정
    4. 전력 사용량 기반 HEV 가중치 반영
    5. citations 포함
    6. LangGraph Memory Node용 output 생성 (impact_summary, impact_list)
    7. 다중 사업장 통합 분석 (run_aggregated)
    8. v08: H×E×V 요소별 원인 분석 (규칙 기반 drivers 추출)
    9. v08: 사업장 비교 및 투자 우선순위 매트릭스
    10. v08: AAL 기반 재무 영향 분석
    11. v08: LLM 기반 정성 인사이트 추출

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
    - v08 (2025-12-05): 정량 데이터 기반 정성 분석 강화
        - H×E×V 원인 분석 (규칙 기반 + LLM 해석)
        - 사업장별 비교 분석 및 투자 우선순위
        - AAL 기반 재무 영향 계산
        - Top 5 리스크 필터링으로 LLM 컨텍스트 최적화
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
        다중 사업장 통합 영향 분석 (v08 - 정량 데이터 기반 정성 분석 강화)

        각 사업장의 H, E, V, risk_scores, AAL, power_usage를 집계하여
        통합 분석 결과 생성 + H×E×V 원인 분석 + 사업장 비교 + 재무 영향 분석

        Args:
            sites_data: 사업장별 데이터 리스트
                [
                    {
                        "site_id": "site_001",
                        "site_name": "서울 본사",
                        "location": {"latitude": 37.5, "longitude": 127.0, "is_coastal": False, "elevation": 30},
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
                "aggregated_quantitative": {...},  # 집계된 정량 결과 (기존)
                "quantitative_deep_dive": {...},   # NEW: Top 5 리스크 상세 분석
                "qualitative_insights": {...},     # NEW: LLM 기반 정성 해석
                "aggregated_narrative": "...",     # 통합 내러티브
                "site_results": [...],             # 사업장별 결과
                "top_site": {...},
                "bottom_site": {...},
                "average_impact": {...}
            }
        """
        print(f"[ImpactAnalysisAgent] 다중 사업장 통합 분석 시작 (v08 - Deep Dive)")
        print(f"[ImpactAnalysisAgent] 사업장 수: {len(sites_data)}")

        # 1. 사업장별 정량 결과 생성 (기존 로직)
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
                "site_name": site_data.get("site_name", site_id),
                "location": site_data.get("location", {}),
                "quantitative": quant_result,
                "asset_info": site_data.get("asset_info", {}),
                "building_info": site_data.get("building_info", {})
            })

        # 2. 집계 결과 생성 (기존)
        aggregated_quant = self._aggregate_results(site_results)

        # 3. NEW: 정량 상세 분석 (Top 5 리스크만)
        quantitative_deep_dive = self._build_quantitative_deep_dive(
            sites_data=sites_data,
            site_results=site_results
        )

        # 4. NEW: LLM 기반 정성 해석
        qualitative_insights = self._extract_qualitative_insights(
            quantitative_deep_dive=quantitative_deep_dive,
            sites_data=sites_data
        )

        # 5. 통합 내러티브 생성 (기존)
        aggregated_narrative = self._generate_aggregated_narrative(
            aggregated_quant=aggregated_quant,
            site_results=site_results,
            report_profile=report_profile
        )

        print(f"[ImpactAnalysisAgent] 다중 사업장 통합 분석 완료")
        print(f"[ImpactAnalysisAgent] - Top {quantitative_deep_dive.get('total_risks_analyzed', 0)} 리스크 분석 완료")
        print(f"[ImpactAnalysisAgent] - 정성 인사이트: {len(qualitative_insights.get('site_comparison_insights', []))}개")

        return {
            "aggregated_quantitative": aggregated_quant,
            "quantitative_deep_dive": quantitative_deep_dive,  # NEW
            "qualitative_insights": qualitative_insights,      # NEW
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

    # ----------------------------------------------------------------------
    # Quantitative Deep Dive Methods (v08 - 정량 데이터 기반 정성 분석)
    # ----------------------------------------------------------------------

    def _extract_hazard_drivers(self, risk_type: str, sites_data: List[Dict]) -> List[Dict]:
        """
        리스크 타입별 Hazard 점수가 높은 이유 추출 (규칙 기반)

        Args:
            risk_type: 리스크 타입 (e.g., "river_flood", "extreme_heat")
            sites_data: 사업장 데이터 리스트

        Returns:
            [
                {
                    "factor": "coastal_location",
                    "contribution": 0.45,
                    "description": "2개 사업장 해안 인접",
                    "affected_sites": ["site_002", "site_003"]
                },
                ...
            ]
        """
        drivers = []

        if risk_type == "river_flood":
            # 해안 근접도
            coastal_sites = [s for s in sites_data if s.get("location", {}).get("is_coastal", False)]
            if coastal_sites:
                drivers.append({
                    "factor": "coastal_location",
                    "contribution": 0.45,
                    "description": f"{len(coastal_sites)}개 사업장 해안 인접",
                    "affected_sites": [s.get("site_id") for s in coastal_sites]
                })

            # 저지대
            lowland_sites = [s for s in sites_data if s.get("location", {}).get("elevation", 999) < 50]
            if lowland_sites:
                drivers.append({
                    "factor": "low_elevation",
                    "contribution": 0.35,
                    "description": f"{len(lowland_sites)}개 사업장 저지대 (해발 50m 미만)",
                    "affected_sites": [s.get("site_id") for s in lowland_sites]
                })

        elif risk_type == "extreme_heat":
            # 아열대 기후권 (위도 35° 이하)
            subtropical_sites = [s for s in sites_data if s.get("location", {}).get("latitude", 40) < 35]
            if subtropical_sites:
                drivers.append({
                    "factor": "subtropical_climate",
                    "contribution": 0.50,
                    "description": f"{len(subtropical_sites)}개 사업장 아열대 기후권 (위도 35° 이하)",
                    "affected_sites": [s.get("site_id") for s in subtropical_sites]
                })

        elif risk_type == "typhoon":
            # 해안 노출도
            coastal_sites = [s for s in sites_data if s.get("location", {}).get("is_coastal", False)]
            if coastal_sites:
                drivers.append({
                    "factor": "coastal_exposure",
                    "contribution": 0.60,
                    "description": f"{len(coastal_sites)}개 사업장 태풍 경로 노출 (해안)",
                    "affected_sites": [s.get("site_id") for s in coastal_sites]
                })

        elif risk_type == "urban_flood":
            # 저지대
            lowland_sites = [s for s in sites_data if s.get("location", {}).get("elevation", 999) < 100]
            if lowland_sites:
                drivers.append({
                    "factor": "low_elevation",
                    "contribution": 0.40,
                    "description": f"{len(lowland_sites)}개 사업장 저지대 (해발 100m 미만)",
                    "affected_sites": [s.get("site_id") for s in lowland_sites]
                })

        elif risk_type == "sea_level_rise":
            # 해안 인접
            coastal_sites = [s for s in sites_data if s.get("location", {}).get("is_coastal", False)]
            if coastal_sites:
                drivers.append({
                    "factor": "coastal_proximity",
                    "contribution": 0.70,
                    "description": f"{len(coastal_sites)}개 사업장 해안선 인접",
                    "affected_sites": [s.get("site_id") for s in coastal_sites]
                })

        # 기타 리스크는 일반 기후 요인
        if not drivers:
            drivers.append({
                "factor": "climate_exposure",
                "contribution": 0.50,
                "description": f"지역별 {risk_type} 기후 노출도",
                "affected_sites": [s.get("site_id") for s in sites_data]
            })

        return drivers

    def _extract_vulnerability_drivers(self, risk_type: str, sites_data: List[Dict]) -> List[Dict]:
        """
        리스크 타입별 Vulnerability 점수가 높은 이유 추출 (규칙 기반)

        Args:
            risk_type: 리스크 타입
            sites_data: 사업장 데이터 리스트

        Returns:
            취약성 요인 리스트
        """
        drivers = []

        if risk_type in ["river_flood", "urban_flood"]:
            # 건물 노후화 (20년 이상)
            old_buildings = [s for s in sites_data if s.get("building_info", {}).get("building_age", 0) >= 20]
            if old_buildings:
                avg_age = np.mean([s.get("building_info", {}).get("building_age", 0) for s in old_buildings])
                drivers.append({
                    "factor": "building_age",
                    "contribution": 0.40,
                    "description": f"{len(old_buildings)}개 사업장 건물 노후화 (평균 {avg_age:.0f}년)",
                    "affected_sites": [s.get("site_id") for s in old_buildings]
                })

            # 배수 시스템 (drainage_system 필드가 있다면)
            poor_drainage = [s for s in sites_data if s.get("building_info", {}).get("drainage_system") == "poor"]
            if poor_drainage:
                drivers.append({
                    "factor": "drainage_system",
                    "contribution": 0.35,
                    "description": f"{len(poor_drainage)}개 사업장 배수 시스템 불량",
                    "affected_sites": [s.get("site_id") for s in poor_drainage]
                })

        elif risk_type == "extreme_heat":
            # 냉각 용량 부족
            insufficient_cooling = [s for s in sites_data if s.get("building_info", {}).get("cooling_capacity") == "insufficient"]
            if insufficient_cooling:
                drivers.append({
                    "factor": "cooling_capacity",
                    "contribution": 0.45,
                    "description": f"{len(insufficient_cooling)}개 사업장 냉각 시스템 용량 부족",
                    "affected_sites": [s.get("site_id") for s in insufficient_cooling]
                })

        elif risk_type == "typhoon":
            # 내진 설계 미비
            no_seismic = [s for s in sites_data if not s.get("building_info", {}).get("has_seismic_design", False)]
            if no_seismic:
                drivers.append({
                    "factor": "seismic_design",
                    "contribution": 0.30,
                    "description": f"{len(no_seismic)}개 사업장 내진 설계 미비",
                    "affected_sites": [s.get("site_id") for s in no_seismic]
                })

        # 공통: 건물 노후화 (일반)
        if not drivers:
            old_buildings = [s for s in sites_data if s.get("building_info", {}).get("building_age", 0) >= 15]
            if old_buildings:
                avg_age = np.mean([s.get("building_info", {}).get("building_age", 0) for s in old_buildings])
                drivers.append({
                    "factor": "general_aging",
                    "contribution": 0.35,
                    "description": f"{len(old_buildings)}개 사업장 건물 노후화 (평균 {avg_age:.0f}년)",
                    "affected_sites": [s.get("site_id") for s in old_buildings]
                })

        return drivers

    def _extract_exposure_drivers(self, risk_type: str, sites_data: List[Dict]) -> List[Dict]:
        """
        Exposure 점수가 높은 이유 추출 (자산 가치 기반)

        Args:
            risk_type: 리스크 타입
            sites_data: 사업장 데이터 리스트

        Returns:
            노출도 요인 리스트
        """
        drivers = []

        # 자산 가치 집중도
        total_assets = sum([s.get("asset_info", {}).get("total_asset_value", 0) for s in sites_data])
        if total_assets > 0:
            high_value_sites = [s for s in sites_data if s.get("asset_info", {}).get("total_asset_value", 0) / total_assets > 0.3]
            if high_value_sites:
                drivers.append({
                    "factor": "asset_concentration",
                    "contribution": 0.50,
                    "description": f"{len(high_value_sites)}개 사업장 자산 집중 (포트폴리오의 30% 이상)",
                    "affected_sites": [s.get("site_id") for s in high_value_sites]
                })

        # 평균 노출도
        if not drivers:
            drivers.append({
                "factor": "portfolio_exposure",
                "contribution": 0.40,
                "description": f"전체 {len(sites_data)}개 사업장 자산 노출",
                "affected_sites": [s.get("site_id") for s in sites_data]
            })

        return drivers

    def _analyze_hev_drivers(self, risk_type: str, site_results: List[Dict], sites_data: List[Dict] = None) -> Dict:
        """
        H×E×V 요소별 원인 분석 통합 메서드

        Args:
            risk_type: 리스크 타입
            site_results: 사업장별 정량 결과 리스트
            sites_data: 사업장 원본 데이터 리스트 (location, building_info 등)

        Returns:
            {
                "H": {
                    "average": 83.2,
                    "site_range": {"min": 78.5, "max": 88.1},
                    "drivers": [...]
                },
                "E": {...},
                "V": {...}
            }
        """
        # 사업장 데이터 추출 (sites_data가 없으면 site_results에서 추출)
        if sites_data is None:
            sites_data = site_results

        # H, E, V 평균 및 범위 계산
        h_scores = []
        e_scores = []
        v_scores = []

        for site in site_results:
            quant = site.get("quantitative", {})
            # 첫 번째 시나리오의 HEV_average 사용
            first_scenario = [k for k in quant.keys() if k != "AAL"][0] if quant else None
            if first_scenario:
                hev_avg = quant[first_scenario].get("HEV_average", {}).get(risk_type, {})
                h_scores.append(hev_avg.get("H", 0))
                e_scores.append(hev_avg.get("E", 0))
                v_scores.append(hev_avg.get("V", 0))

        # Drivers 추출
        h_drivers = self._extract_hazard_drivers(risk_type, sites_data)
        e_drivers = self._extract_exposure_drivers(risk_type, sites_data)
        v_drivers = self._extract_vulnerability_drivers(risk_type, sites_data)

        return {
            "H": {
                "average": round(np.mean(h_scores), 2) if h_scores else 0,
                "site_range": {
                    "min": round(min(h_scores), 2) if h_scores else 0,
                    "max": round(max(h_scores), 2) if h_scores else 0
                },
                "drivers": h_drivers
            },
            "E": {
                "average": round(np.mean(e_scores), 2) if e_scores else 0,
                "site_range": {
                    "min": round(min(e_scores), 2) if e_scores else 0,
                    "max": round(max(e_scores), 2) if e_scores else 0
                },
                "drivers": e_drivers
            },
            "V": {
                "average": round(np.mean(v_scores), 2) if v_scores else 0,
                "site_range": {
                    "min": round(min(v_scores), 2) if v_scores else 0,
                    "max": round(max(v_scores), 2) if v_scores else 0
                },
                "drivers": v_drivers
            }
        }

    def _build_site_comparison(self, risk_type: str, site_results: List[Dict],
                               sites_data: List[Dict], top_n: int = 3) -> List[Dict]:
        """
        사업장별 리스크 비교 (상위 N개만)

        Args:
            risk_type: 리스크 타입
            site_results: 사업장별 정량 결과
            sites_data: 사업장 원본 데이터
            top_n: 상위 N개 사업장

        Returns:
            [
                {
                    "site_id": "site_002",
                    "site_name": "부산 지사",
                    "aal_percentage": 0.87,
                    "aal_amount": 435000000,
                    "risk_score": 88.1,
                    "key_factors": ["해안 저지대", "건물 25년"],
                    "priority": "high"
                },
                ...
            ]
        """
        site_comparisons = []

        for i, site_result in enumerate(site_results):
            site_id = site_result.get("site_id")
            site_info = sites_data[i] if i < len(sites_data) else {}

            # AAL 추출
            quant = site_result.get("quantitative", {})
            aal_dict = quant.get("AAL", {})
            aal_pct = aal_dict.get(risk_type, 0)

            # Risk Score 추출
            first_scenario = [k for k in quant.keys() if k != "AAL"][0] if quant else None
            risk_score = 0
            if first_scenario:
                risk_score = quant[first_scenario].get("risk_scores", {}).get(risk_type, 0)

            # 자산 가치
            asset_value = site_info.get("asset_info", {}).get("total_asset_value", 0)
            aal_amount = asset_value * (aal_pct / 100) if asset_value > 0 else 0

            # Key factors 추출
            key_factors = self._extract_key_factors(risk_type, site_info)

            # Priority 분류
            priority = "high" if risk_score > 70 else ("medium" if risk_score > 40 else "low")

            site_comparisons.append({
                "site_id": site_id,
                "site_name": site_info.get("site_name", site_id),
                "aal_percentage": round(aal_pct, 4),
                "aal_amount": round(aal_amount, 0),
                "risk_score": round(risk_score, 2),
                "key_factors": key_factors,
                "priority": priority
            })

        # AAL 기준 정렬 후 상위 N개만
        site_comparisons.sort(key=lambda x: x["aal_percentage"], reverse=True)
        return site_comparisons[:top_n]

    def _extract_key_factors(self, risk_type: str, site_info: Dict) -> List[str]:
        """
        사업장별 핵심 위험 요인 추출

        Args:
            risk_type: 리스크 타입
            site_info: 사업장 정보

        Returns:
            핵심 요인 리스트 (예: ["해안 저지대", "건물 25년"])
        """
        factors = []

        location = site_info.get("location", {})
        building = site_info.get("building_info", {})

        # 위치 요인
        if location.get("is_coastal"):
            factors.append("해안 인접")
        if location.get("elevation", 999) < 50:
            factors.append("저지대")
        elif location.get("elevation", 0) < 100:
            factors.append("중저지대")

        # 건물 요인
        building_age = building.get("building_age", 0)
        if building_age >= 25:
            factors.append(f"건물 {building_age}년 노후")
        elif building_age >= 15:
            factors.append(f"건물 {building_age}년")

        if not building.get("has_seismic_design", True):
            factors.append("내진설계 미비")

        if building.get("drainage_system") == "poor":
            factors.append("배수 불량")

        if building.get("cooling_capacity") == "insufficient":
            factors.append("냉각 부족")

        # 최소 1개 요인
        if not factors:
            factors.append("일반 노출")

        return factors[:3]  # 최대 3개만

    def _calculate_financial_impact(self, risk_type: str, site_results: List[Dict],
                                    sites_data: List[Dict]) -> Dict:
        """
        재무 영향 계산 (AAL 기반)

        Args:
            risk_type: 리스크 타입
            site_results: 사업장별 정량 결과
            sites_data: 사업장 원본 데이터

        Returns:
            {
                "total_aal_percentage": 1.73,
                "total_aal_amount": 865000000,
                "site_breakdown": [...]
            }
        """
        total_aal_pct = 0
        total_aal_amount = 0
        site_breakdown = []

        for i, site_result in enumerate(site_results):
            site_info = sites_data[i] if i < len(sites_data) else {}

            quant = site_result.get("quantitative", {})
            aal_dict = quant.get("AAL", {})
            aal_pct = aal_dict.get(risk_type, 0)

            asset_value = site_info.get("asset_info", {}).get("total_asset_value", 0)
            aal_amount = asset_value * (aal_pct / 100) if asset_value > 0 else 0

            total_aal_pct += aal_pct
            total_aal_amount += aal_amount

            site_breakdown.append({
                "site_id": site_result.get("site_id"),
                "site_name": site_info.get("site_name", "Unknown"),
                "aal_percentage": round(aal_pct, 4),
                "aal_amount": round(aal_amount, 0)
            })

        return {
            "total_aal_percentage": round(total_aal_pct, 4),
            "total_aal_amount": round(total_aal_amount, 0),
            "average_aal_percentage": round(total_aal_pct / len(site_results), 4) if site_results else 0,
            "site_breakdown": site_breakdown
        }

    def _build_site_priority_matrix(self, site_comparisons: List[Dict]) -> Dict:
        """
        최우선 조치 사업장 식별

        Args:
            site_comparisons: 사업장 비교 데이터

        Returns:
            {
                "priority_site": {...},
                "investment_recommendation": "예산 50% 부산 투입"
            }
        """
        if not site_comparisons:
            return {}

        # 최고 AAL 사업장
        priority_site = site_comparisons[0]

        # 투자 배분 권고 (간단한 규칙)
        total_aal = sum([s["aal_percentage"] for s in site_comparisons])
        if total_aal > 0:
            priority_ratio = priority_site["aal_percentage"] / total_aal
            investment_pct = min(70, max(30, int(priority_ratio * 100)))
        else:
            investment_pct = 50

        recommendation = f"예산 {investment_pct}% {priority_site['site_name']} 투입"

        return {
            "priority_site": priority_site,
            "investment_recommendation": recommendation,
            "investment_percentage": investment_pct
        }

    def _build_quantitative_deep_dive(self, sites_data: List[Dict],
                                       site_results: List[Dict]) -> Dict:
        """
        정량 상세 분석 통합 (Top 5 리스크만)

        Args:
            sites_data: 사업장 원본 데이터
            site_results: 사업장별 정량 결과

        Returns:
            {
                "top_risks": [
                    {
                        "risk_type": "river_flood",
                        "average_risk_score": 75.3,
                        "hev_breakdown": {...},
                        "site_comparison": [...],
                        "financial_impact": {...},
                        "priority_matrix": {...}
                    },
                    ...
                ]
            }
        """
        print("[ImpactAnalysisAgent] Building quantitative deep dive...")

        # 1. Top 5 리스크 선정 (평균 점수 기준)
        risk_avg_scores = {}
        for risk in self.risk_list:
            scores = []
            for site_result in site_results:
                quant = site_result.get("quantitative", {})
                first_scenario = [k for k in quant.keys() if k != "AAL"][0] if quant else None
                if first_scenario:
                    score = quant[first_scenario].get("risk_scores", {}).get(risk, 0)
                    scores.append(score)
            risk_avg_scores[risk] = np.mean(scores) if scores else 0

        # 정렬 후 Top 5
        sorted_risks = sorted(risk_avg_scores.items(), key=lambda x: x[1], reverse=True)
        top_5_risks = [r[0] for r in sorted_risks[:5]]

        print(f"[ImpactAnalysisAgent] Top 5 risks: {top_5_risks}")

        # 2. Top 5 리스크별 상세 분석
        top_risks_analysis = []
        for risk_type in top_5_risks:
            # H×E×V 분해 분석
            hev_breakdown = self._analyze_hev_drivers(risk_type, site_results, sites_data)

            # 사업장 비교
            site_comparison = self._build_site_comparison(
                risk_type, site_results, sites_data, top_n=3
            )

            # 재무 영향
            financial_impact = self._calculate_financial_impact(
                risk_type, site_results, sites_data
            )

            # 우선순위 매트릭스
            priority_matrix = self._build_site_priority_matrix(site_comparison)

            top_risks_analysis.append({
                "risk_type": risk_type,
                "average_risk_score": round(risk_avg_scores[risk_type], 2),
                "hev_breakdown": hev_breakdown,
                "site_comparison": site_comparison,
                "financial_impact": financial_impact,
                "priority_matrix": priority_matrix
            })

        return {
            "top_risks": top_risks_analysis,
            "total_risks_analyzed": len(top_5_risks)
        }

    def _extract_qualitative_insights(self, quantitative_deep_dive: Dict,
                                       sites_data: List[Dict]) -> Dict:
        """
        LLM을 사용하여 정량 데이터를 정성적으로 해석

        Args:
            quantitative_deep_dive: _build_quantitative_deep_dive() 결과
            sites_data: 사업장 원본 데이터

        Returns:
            {
                "hev_interpretation": {
                    "river_flood": {
                        "H_high_reason": "부산, 대구가 하천 인접 (해안 45% + 저지대 35%)",
                        "V_high_reason": "건물 평균 25년 (40%) + 배수 불량 (35%)",
                        "mitigation_potential": "배수 개선 시 V 77.5→45.0, AAL 0.87%→0.40%"
                    },
                    ...
                },
                "site_comparison_insights": [
                    "부산(AAL 0.87%) >> 서울(0.42%) → 예산 50% 부산 투입",
                    ...
                ]
            }
        """
        print("[ImpactAnalysisAgent] Extracting qualitative insights via LLM...")

        prompt = f"""
<ROLE>
You are a senior climate risk analyst specializing in H×E×V (Hazard × Exposure × Vulnerability) framework analysis and financial impact assessment.
</ROLE>

<CONTEXT>
You have been provided with detailed quantitative analysis of physical climate risks across multiple sites, including:
- H×E×V component breakdown with rule-based drivers
- Site-by-site AAL (Annual Average Loss) comparisons
- Financial impact calculations
- Priority matrices for mitigation investments

<QUANTITATIVE_DATA>
{json.dumps(quantitative_deep_dive, indent=2, ensure_ascii=False)}
</QUANTITATIVE_DATA>

<SITES_DATA>
{json.dumps([{{"site_id": s.get("site_id"), "site_name": s.get("site_name"), "location": s.get("location"), "building_info": s.get("building_info")}} for s in sites_data], indent=2, ensure_ascii=False)}
</SITES_DATA>
</CONTEXT>

<INSTRUCTIONS>
For each top risk in the QUANTITATIVE_DATA, generate qualitative interpretations that explain:

1. **H_high_reason**: Why is the Hazard score high?
   - Reference the specific drivers and their contribution percentages
   - Explain in concrete terms (e.g., "2개 사업장이 해안 인접(기여도 45%) + 1개 사업장 저지대(기여도 35%)")

2. **E_high_reason**: Why is the Exposure score at this level?
   - Explain asset concentration or portfolio exposure
   - Use specific numbers from the data

3. **V_high_reason**: Why is the Vulnerability score high?
   - Reference building characteristics (age, drainage, cooling, etc.)
   - Cite contribution percentages from drivers
   - Example: "건물 평균 25년 노후화(기여도 40%) + 배수 시스템 불량(기여도 35%)"

4. **mitigation_potential**: What would happen if we mitigate V?
   - Calculate potential AAL reduction
   - Format: "배수 시스템 개선 시 V 77.5→45.0 예상, AAL 0.87%→0.40% (54% 감소)"

5. **site_comparison_insight**: Compare top sites quantitatively
   - Format: "부산(AAL 0.87%, Risk 88.1) >> 서울(AAL 0.42%, Risk 65.3) → 예산 50% 부산 우선 투입"
   - Use actual AAL percentages and site names from the data

Your interpretations must:
- Use ONLY the numbers provided in QUANTITATIVE_DATA
- Reference driver contribution percentages explicitly
- Provide concrete, actionable insights
- Maintain professional TCFD reporting tone
</INSTRUCTIONS>

<OUTPUT_FORMAT>
Return a JSON object with this structure:
{{
    "hev_interpretation": {{
        "river_flood": {{
            "H_high_reason": "...",
            "E_high_reason": "...",
            "V_high_reason": "...",
            "mitigation_potential": "..."
        }},
        "extreme_heat": {{...}},
        ...
    }},
    "site_comparison_insights": [
        "부산(AAL 0.87%) >> 서울(0.42%) → 예산 50% 부산 투입",
        ...
    ]
}}
</OUTPUT_FORMAT>

<RULES>
- Output ONLY valid JSON
- DO NOT invent numbers - use only data from QUANTITATIVE_DATA
- MUST include contribution percentages when citing drivers
- Language: Korean for descriptions
- Be specific and concrete, not abstract
</RULES>
"""

        response = self.llm.generate(prompt)

        # Parse JSON response
        try:
            # LLM이 ```json ... ``` 형식으로 반환할 수 있으므로 정리
            if "```json" in response:
                response = response.split("```json")[1].split("```")[0].strip()
            elif "```" in response:
                response = response.split("```")[1].split("```")[0].strip()

            insights = json.loads(response)
            return insights
        except json.JSONDecodeError as e:
            print(f"[ImpactAnalysisAgent] Warning: Failed to parse LLM JSON response: {e}")
            print(f"[ImpactAnalysisAgent] Raw response: {response[:500]}")
            # Fallback: 기본 구조 반환
            return {
                "hev_interpretation": {},
                "site_comparison_insights": []
            }
