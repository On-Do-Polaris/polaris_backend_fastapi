# strategy_generation_agent_3.py
"""
파일명: strategy_generation_agent_3.py
최종 수정일: 2025-12-01
버전: v05

파일 개요:
    - LangGraph StrategyGeneration Node용 대응 전략 생성 Agent
    - 입력: report_profile, impact_analysis_result, vulnerability_analysis, AAL, physical_risk_scores
    - 출력: risk_specific_strategies, overall_strategy, recommendations, priority_actions, citations
    - RAG 기반 사례 검색 + LLM 기반 전략 생성

주요 기능:
    1. 상위 물리적 리스크 선정 (ImpactScore + AAL)
    2. RAG 기반 유사 사례 검색 (Graph RAG)
    3. LLM 기반 전략 생성
       - 종합 전략(overall_strategy)
       - 리스크별 전략(risk_specific_strategies)
       - 권고사항, 우선 조치
    4. citations 생성 및 정리 (기존 citations 무시, 항상 전체 재생성)
    5. Memory Node용 output 구성 (strategies[], citations[])

Refiner 루프 연계:
    - Strategy Issue 발생 시 route: strategy
    - LLM 재호출로 strategies[] + citations 재생성

변경 이력:
    - v01 (2025-11-14): 초안 작성, 물리적 리스크별 대응 전략 생성
    - v02 (2025-11-21): RAG + LLM 구조로 리팩토링, citations 포함
    - v03 (2025-11-24): 최신 LangGraph 아키텍처 반영, Memory Node/Refiner 루프 연계
    - v04 (2025-11-24): Impact Analysis Agent와 1:1 매핑, 전략별 citations 자동 재생성
    - v05 (2025-12-01): 프롬프트 구조 개선
"""

from typing import Dict, List, Any
import json

class StrategyGenerationAgent:
    """
    Strategy Generation Agent (Agent 3)
    ------------------------------------
    목적:
    - Agent 2 영향 분석 결과를 기반으로, 리스크별 대응 전략 자동 생성
    - 국제 기준 RAG 근거 포함
    - Composer/보고서용 구조화 output 생성

    구성:
    - Layer 1: Quantitative/Context Mapping (영향→전략 후보) - v05에서 run 함수로 변경
    - Layer 2: LLM Narrative Generation (전략 설명 + 비용/효과 분석)
    """

    def __init__(self, llm_client):
        """
        llm_client: OpenAI, Anthropic, Vertex 등 LLM 객체
        """
        self.llm = llm_client
        
    # ----------------------------------------------------------------------
    # Layer : LLM Narrative Generation
    # ----------------------------------------------------------------------
    def generate_strategy_narrative(self, candidate: Dict,
                                    facility_profile: Dict,
                                    report_profile: Dict) -> Dict:
        """
        LLM을 통해 단일 리스크에 대한 구조화된 대응 전략 JSON을 생성합니다.
        """
        risk = candidate.get("risk")
        impact = candidate.get("impact")
        prompt = f"""
    <ROLE>
    You are a premier strategy consultant specializing in TCFD and Climate Adaptation. Your expertise is in designing actionable, cost-effective, and data-driven response strategies for specific, analyzed climate risks. Your proposals are always concrete, measurable, and clearly justified, never vague.
    </ROLE>

    <CONTEXT>
    You will be provided with a specific climate risk's impact analysis, the profile of the facility at risk, and the company's preferred report style profile. 

        <IMPACT_ANALYSIS>
        This is the analysis for the specific risk: '{risk}'
        {json.dumps(impact, indent=2, ensure_ascii=False)}
        </IMPACT_ANALYSIS>

        <FACILITY_PROFILE>
        {json.dumps(facility_profile, indent=2, ensure_ascii=False)}
        </FACILITY_PROFILE>

        <REPORT_STYLE_PROFILE>
        {json.dumps(report_profile, indent=2, ensure_ascii=False)}
        </REPORT_STYLE_PROFILE>

    </CONTEXT>    

    <INSTRUCTIONS>
    Your task is to design a robust response strategy for the single climate risk specified in the context. You must generate a single, structured JSON object as the output. 
    Follow this thought process to structure your response:

    <THOUGHT_PROCESS>
    1.  **Analyze Impact**: Deeply understand the impact and vulnerabilities associated with the given risk from the `<IMPACT_ANALYSIS>` section.
    2.  **Brainstorm Strategies**: Consider a range of potential strategies: structural (e.g., building reinforcements), operational (e.g., emergency response plans), and financial (e.g., insurance).
    3.  **Evaluate Strategies**: Assess the brainstormed ideas based on estimated cost, effectiveness, feasibility, and timeline, considering the specific `<FACILITY_PROFILE>`.
    4.  **Select & Refine Best Strategy**: Choose the most viable strategy. Elaborate on it, breaking it down into specific recommendations for policy, operations, and technology as required by the output format.
    5.  **Find Citation**: Formulate a supporting citation from a reputable international standard or report (e.g., TCFD, IPCC, ISO) that justifies your proposed strategy.
    </THOUGHT_PROCESS>

    Based on this thought process, generate a single JSON object that strictly adheres to the format specified in <OUTPUT_FORMAT>.
    </INSTRUCTIONS>  

    <OUTPUT_FORMAT>
    - You must output a single, raw JSON object and nothing else.
    - The JSON object must have the following structure and keys:
        {{
        "risk": "The specific risk being addressed (e.g., 'extreme_heat')",
        "strategy_summary": "A concise, one-sentence summary of the proposed strategy.",
        "strategy_details": {{
            "policy_recommendation": "Recommendations related to company policy, governance, or procedures.",
            "operational_recommendation": "Recommendations for changes in operational processes or activities.",
            "technical_recommendation": "Recommendations for technical, structural, or engineering changes."
        }},
        "cost_benefit_analysis": "A brief analysis of the estimated costs and expected benefits of implementing the strategy.",
        "citation": "A supporting citation from an international standard, e.g., 'TCFD (2023) - Adaptation for Physical Risks'."
        }}

    </OUTPUT_FORMAT>

    <RULES>
    - Output ONLY a single raw JSON object. Do NOT include explanations, apologies, or any text outside the JSON object.
    - DO NOT provide vague or generic advice like "risk management should be strengthened." All recommendations must be specific and actionable.
    - The proposed strategy MUST be relevant and tailored to the facility described in `<FACILITY_PROFILE>`.
    - The output language must be Korean.
    </RULES>

    JSON_ONLY:
    """
        response_str = self.llm.generate(prompt)
        
        try:
            llm_output = json.loads(response_str)
        except (json.JSONDecodeError, TypeError):
            llm_output = {{
                "risk": risk,
                "strategy_summary": "Error: Failed to generate a valid strategy.",
                "strategy_details": {{
                    "policy_recommendation": "N/A",
                    "operational_recommendation": "N/A",
                    "technical_recommendation": "N/A"
                }},
                "cost_benefit_analysis": "N/A",
                "citation": "N/A"
            }}
        return llm_output

    # ----------------------------------------------------------------------
    # Main API method
    # ----------------------------------------------------------------------
    def run(self, impact_summary: List[Dict],
            facility_profile: Dict,
            report_profile: Dict) -> List[Dict]:
        """
        에이전트 3 전체 파이프라인 실행
        impact_summary의 각 리스크에 대해 개별적으로 전략을 생성합니다.
        """
        strategies_output = []  

        for impact_item in impact_summary:
            candidate = {
                "risk": impact_item.get("risk"),
                "impact": impact_item
            }
            
            # 각 리스크에 대해 LLM을 호출하여 구조화된 전략 JSON을 생성
            strategy_json = self.generate_strategy_narrative(
                candidate=candidate,
                facility_profile=facility_profile,
                report_profile=report_profile
            )

            strategies_output.append(strategy_json)
        return strategies_output
