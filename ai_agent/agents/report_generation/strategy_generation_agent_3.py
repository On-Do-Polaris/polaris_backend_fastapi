# strategy_generation_agent_3.py
"""
파일명: strategy_generation_agent_3.py
최종 수정일: 2025-12-02
버전: v06

파일 개요:
    - LangGraph StrategyGeneration Node용 대응 전략 생성 Agent
    - 입력: report_profile, impact_analysis_result, vulnerability_analysis, AAL, physical_risk_scores
    - 출력: risk_specific_strategies, overall_strategy, recommendations, priority_actions, citations
    - RAG 기반 사례 검색 + LLM 기반 전략 생성
    - 단일/다중 사업장 통합 전략 지원

주요 기능:
    1. 상위 물리적 리스크 선정 (ImpactScore + AAL)
    2. RAG 기반 유사 사례 검색 (Graph RAG)
    3. LLM 기반 전략 생성
       - 종합 전략(overall_strategy)
       - 리스크별 전략(risk_specific_strategies)
       - 권고사항, 우선 조치
    4. citations 생성 및 정리 (기존 citations 무시, 항상 전체 재생성)
    5. Memory Node용 output 구성 (strategies[], citations[])
    6. 다중 사업장 통합 전략 생성 (run_aggregated)

Refiner 루프 연계:
    - Strategy Issue 발생 시 route: strategy
    - LLM 재호출로 strategies[] + citations 재생성

변경 이력:
    - v01 (2025-11-14): 초안 작성, 물리적 리스크별 대응 전략 생성
    - v02 (2025-11-21): RAG + LLM 구조로 리팩토링, citations 포함
    - v03 (2025-11-24): 최신 LangGraph 아키텍처 반영, Memory Node/Refiner 루프 연계
    - v04 (2025-11-24): Impact Analysis Agent와 1:1 매핑, 전략별 citations 자동 재생성
    - v05 (2025-12-01): 프롬프트 구조 개선 (영어 프롬프트 적용)
    - v06 (2025-12-02): 다중 사업장 통합 전략 생성 지원 (run_aggregated 추가)
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
    # Layer 2: LLM Narrative Generation
    # ----------------------------------------------------------------------
    def generate_strategy_narrative(self, candidate: Dict,
                                    facility_profile: Dict,
                                    report_profile: Dict) -> Dict:
        """
        LLM을 통해 단일 리스크에 대한 구조화된 대응 전략 JSON을 생성합니다.
        """
        risk = candidate.get("risk")
        impact = candidate.get("impact")

        # feature/7-report-agent의 영어 프롬프트 사용
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
5.  **Quantify Expected Improvements**: **CRITICAL** - You must provide specific, quantitative improvement estimates:
   - Expected AAL reduction (e.g., "AAL 0.87% → 0.40% with 50% budget allocation to drainage improvement")
   - Risk score changes (e.g., "V score 77.5 → 45.0 with upgraded drainage system")
   - Investment ROI (e.g., "50% budget investment → 54% AAL reduction")
   - Concrete action plans with measurable outcomes
6.  **Include Specific Programs**: Reference concrete, actionable programs and standards:
   - International standards: RE100, SBTi (Science Based Targets initiative), CDP (Carbon Disclosure Project)
   - Specific adaptation programs: Nature-based Solutions, Green Infrastructure
   - Industry best practices with actual implementation examples
7.  **Find Citation**: Formulate a supporting citation from a reputable international standard or report (e.g., TCFD, IPCC, ISO) that justifies your proposed strategy.
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
        "policy_recommendation": "Recommendations related to company policy, governance, or procedures. **Include specific programs** like RE100, SBTi, CDP participation with concrete implementation steps.",
        "operational_recommendation": "Recommendations for changes in operational processes or activities. **Must include specific, measurable actions** (e.g., 'Install 500kW solar panels by Q2 2026', 'Implement real-time flood monitoring system').",
        "technical_recommendation": "Recommendations for technical, structural, or engineering changes. **Must include quantified improvements** (e.g., 'Upgrade drainage capacity from 50mm/hr to 120mm/hr', 'Install green roof covering 30% of building area')."
    }},
    "cost_benefit_analysis": "A detailed analysis with **specific numbers**: investment amount (e.g., 'Total investment: 500 million KRW'), expected AAL reduction (e.g., '0.87% → 0.40%'), payback period (e.g., '3.5 years'), annual savings (e.g., '435 million KRW → 200 million KRW annual expected loss').",
    "improvement_scenarios": {{
        "scenario_1": {{
            "description": "Specific scenario description (e.g., 'Allocate 50% budget to drainage improvement')",
            "investment": "Investment amount in KRW or % of total budget",
            "expected_improvement": "Quantified improvement (e.g., 'AAL 0.87% → 0.40%', 'Risk Score 88.5 → 42.3')",
            "timeline": "Implementation timeline (e.g., '18 months')"
        }},
        "scenario_2": {{
            "description": "Alternative scenario",
            "investment": "Investment amount",
            "expected_improvement": "Quantified improvement",
            "timeline": "Implementation timeline"
        }}
    }},
    "specific_programs": {{
        "international_standards": ["List of applicable standards like 'RE100: 100% renewable energy by 2030', 'SBTi: 50% emissions reduction by 2030'"],
        "adaptation_measures": ["Specific adaptation programs like 'Nature-based Solutions: Bioswales for 40% stormwater management', 'Green Infrastructure: Cool roofs reducing urban heat island effect by 2.5°C'"]
    }},
    "citation": "A supporting citation from an international standard, e.g., 'TCFD (2023) - Adaptation for Physical Risks'."
    }}

</OUTPUT_FORMAT>

<RULES>
- Output ONLY a single raw JSON object. Do NOT include explanations, apologies, or any text outside the JSON object.
- **CRITICAL**: DO NOT provide vague or generic advice like "지속 가능한 에너지 시스템 도입" or "이해관계자 협력 강화."
- **REQUIRED**: All recommendations must be:
  - Specific (e.g., "RE100 참여: 2030년까지 재생에너지 100% 전환, 연간 500억원 투자")
  - Measurable (e.g., "AAL 0.87% → 0.40% 감소, 배수 용량 50mm/hr → 120mm/hr 증설")
  - Time-bound (e.g., "2025년 Q2까지 태양광 패널 500kW 설치")
  - Financially quantified (e.g., "투자 5억원, 연간 절감액 2억원, 투자 회수 기간 2.5년")
- **improvement_scenarios**: You MUST provide at least 2 different investment scenarios with specific AAL reduction forecasts
- **specific_programs**: You MUST include real, internationally recognized programs (RE100, SBTi, CDP, ISO 14090, etc.) with concrete implementation steps
- The proposed strategy MUST be relevant and tailored to the facility described in `<FACILITY_PROFILE>`.
- The output language must be Korean.
- **Focus on "how to improve" rather than "what the result is"**: Frame recommendations as "현재 AAL 0.87%인데, X를 투자하면 0.40%로 감소" instead of just "AAL이 0.87%입니다."
</RULES>

JSON_ONLY:
"""
        response_str = self.llm.generate(prompt)

        try:
            llm_output = json.loads(response_str)
        except (json.JSONDecodeError, TypeError):
            llm_output = {
                "risk": risk,
                "strategy_summary": "Error: Failed to generate a valid strategy.",
                "strategy_details": {
                    "policy_recommendation": "N/A",
                    "operational_recommendation": "N/A",
                    "technical_recommendation": "N/A"
                },
                "cost_benefit_analysis": "N/A",
                "citation": "N/A"
            }
        return llm_output

    # ----------------------------------------------------------------------
    # Main API method (단일 사업장)
    # ----------------------------------------------------------------------
    def run(self, impact_summary: List[Dict],
            facility_profile: Dict,
            report_profile: Dict) -> List[Dict]:
        """
        에이전트 3 전체 파이프라인 실행 (단일 사업장)
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

    # ----------------------------------------------------------------------
    # 다중 사업장 통합 전략 생성 (NEW in v06)
    # ----------------------------------------------------------------------
    def run_aggregated(self, aggregated_impact: Dict,
                       sites_data: List[Dict[str, Any]],
                       report_profile: Dict) -> Dict:
        """
        다중 사업장 통합 대응 전략 생성 (v06)

        집계된 영향 분석 결과를 기반으로 포트폴리오 차원의 통합 전략 생성

        Args:
            aggregated_impact: Impact Analysis Agent의 run_aggregated() 결과
            sites_data: 사업장별 데이터 리스트
            report_profile: 보고서 스타일 프로필

        Returns:
            {
                "portfolio_strategy": {...},      # 포트폴리오 전체 전략
                "risk_specific_strategies": [...], # 리스크별 전략
                "priority_sites": [...],          # 우선 조치 사업장
                "cost_benefit_summary": {...}     # 비용/효과 요약
            }
        """
        print(f"[StrategyGenerationAgent] 다중 사업장 통합 전략 생성 시작 (사업장 수: {len(sites_data)})")

        # 1. 통합 facility_profile 생성
        aggregated_profile = self._aggregate_facility_profiles(sites_data)

        # 2. 상위 리스크 식별
        top_risks = aggregated_impact.get("aggregated_quantitative", {}).get("average_risk_scores", {})
        sorted_risks = sorted(top_risks.items(), key=lambda x: x[1], reverse=True)[:5]

        # 3. 리스크별 통합 전략 생성
        risk_specific_strategies = []
        for risk_name, risk_score in sorted_risks:
            # 리스크별 영향 정보 추출
            risk_impact = {
                "risk": risk_name,
                "average_score": risk_score,
                "top_site": aggregated_impact.get("top_site"),
                "bottom_site": aggregated_impact.get("bottom_site"),
                "severity": self._compute_severity(risk_score)
            }

            # LLM 호출로 리스크별 전략 생성
            strategy = self._generate_aggregated_risk_strategy(
                risk_name=risk_name,
                risk_impact=risk_impact,
                aggregated_profile=aggregated_profile,
                report_profile=report_profile
            )

            risk_specific_strategies.append(strategy)

        # 4. 포트폴리오 전체 전략 생성
        portfolio_strategy = self._generate_portfolio_strategy(
            risk_specific_strategies=risk_specific_strategies,
            aggregated_impact=aggregated_impact,
            aggregated_profile=aggregated_profile,
            report_profile=report_profile
        )

        # 5. 우선 조치 사업장 식별
        priority_sites = self._identify_priority_sites(
            aggregated_impact=aggregated_impact,
            sites_data=sites_data
        )

        return {
            "portfolio_strategy": portfolio_strategy,
            "risk_specific_strategies": risk_specific_strategies,
            "priority_sites": priority_sites,
            "aggregated_profile": aggregated_profile
        }

    def _aggregate_facility_profiles(self, sites_data: List[Dict[str, Any]]) -> Dict:
        """
        사업장별 프로필을 집계하여 포트폴리오 차원의 프로필 생성
        """
        total_sites = len(sites_data)
        total_asset_value = sum(site.get("asset_info", {}).get("total_value", 0) for site in sites_data)

        # 건물 연령 평균
        building_ages = [site.get("building_info", {}).get("age", 0) for site in sites_data]
        avg_age = sum(building_ages) / len(building_ages) if building_ages else 0

        return {
            "total_sites": total_sites,
            "total_asset_value": total_asset_value,
            "average_building_age": avg_age,
            "site_locations": [site.get("site_id", "unknown") for site in sites_data]
        }

    def _compute_severity(self, risk_score: float) -> str:
        """위험 등급 분류"""
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

    def _generate_aggregated_risk_strategy(self, risk_name: str,
                                           risk_impact: Dict,
                                           aggregated_profile: Dict,
                                           report_profile: Dict) -> Dict:
        """
        특정 리스크에 대한 포트폴리오 차원의 통합 전략 생성
        """
        prompt = f"""
<ROLE>
You are a senior climate strategy consultant developing portfolio-wide adaptation strategies for multiple facilities facing climate risks.
</ROLE>

<CONTEXT>
You are designing a strategy for the climate risk '{risk_name}' across a portfolio of {aggregated_profile.get("total_sites", 0)} facilities.

<RISK_IMPACT_SUMMARY>
{json.dumps(risk_impact, indent=2, ensure_ascii=False)}
</RISK_IMPACT_SUMMARY>

<PORTFOLIO_PROFILE>
{json.dumps(aggregated_profile, indent=2, ensure_ascii=False)}
</PORTFOLIO_PROFILE>

<REPORT_STYLE_PROFILE>
{json.dumps(report_profile, indent=2, ensure_ascii=False)}
</REPORT_STYLE_PROFILE>
</CONTEXT>

<INSTRUCTIONS>
Design a comprehensive portfolio-wide response strategy for this specific climate risk. Your strategy should:

1. **Strategic Overview**: Provide a high-level strategy summary that addresses the risk across all facilities
2. **Differentiated Approach**: Distinguish between high-risk and low-risk facilities in your recommendations
3. **Scalable Solutions**: Propose solutions that can be efficiently deployed across multiple sites
4. **Investment Prioritization**: Suggest how to prioritize investments across the portfolio
5. **Synergies**: Identify opportunities for shared infrastructure or coordinated responses

Generate a single JSON object with the following structure:
{{
    "risk": "The specific risk being addressed",
    "strategy_summary": "Portfolio-wide strategy summary",
    "strategy_details": {{
        "high_risk_facilities": "Specific recommendations for high-risk sites",
        "moderate_risk_facilities": "Recommendations for moderate-risk sites",
        "low_risk_facilities": "Recommendations for low-risk sites"
    }},
    "investment_guidance": "Guidance on prioritizing investments across facilities",
    "implementation_timeline": "Suggested timeline for portfolio-wide implementation",
    "citation": "Supporting citation from international standards"
}}
</INSTRUCTIONS>

<RULES>
- Output ONLY a single raw JSON object
- Be specific and actionable
- Consider economies of scale in multi-facility implementation
- The output language must be Korean.
</RULES>

JSON_ONLY:
"""
        response_str = self.llm.generate(prompt)

        try:
            strategy_json = json.loads(response_str)
        except (json.JSONDecodeError, TypeError):
            strategy_json = {
                "risk": risk_name,
                "strategy_summary": "Error: Failed to generate valid strategy",
                "strategy_details": {},
                "investment_guidance": "N/A",
                "implementation_timeline": "N/A",
                "citation": "N/A"
            }

        return strategy_json

    def _generate_portfolio_strategy(self, risk_specific_strategies: List[Dict],
                                     aggregated_impact: Dict,
                                     aggregated_profile: Dict,
                                     report_profile: Dict) -> Dict:
        """
        포트폴리오 전체의 종합 전략 생성
        """
        prompt = f"""
<ROLE>
You are a chief climate strategy officer synthesizing climate adaptation strategies for a multi-facility corporate portfolio.
</ROLE>

<CONTEXT>
You have developed individual risk-specific strategies. Now synthesize these into a coherent portfolio-wide strategic framework.

<RISK_SPECIFIC_STRATEGIES>
{json.dumps(risk_specific_strategies, indent=2, ensure_ascii=False)}
</RISK_SPECIFIC_STRATEGIES>

<AGGREGATED_IMPACT>
{json.dumps(aggregated_impact, indent=2, ensure_ascii=False)}
</AGGREGATED_IMPACT>

<PORTFOLIO_PROFILE>
{json.dumps(aggregated_profile, indent=2, ensure_ascii=False)}
</PORTFOLIO_PROFILE>
</CONTEXT>

<INSTRUCTIONS>
Develop an integrated portfolio-level climate strategy that:

1. **Strategic Vision**: Articulate an overarching strategic approach to climate adaptation
2. **Resource Allocation**: Provide clear guidance on how to allocate resources across risks and facilities
3. **Governance**: Recommend governance structures for portfolio-wide climate risk management
4. **Monitoring & Review**: Suggest KPIs and review mechanisms
5. **Phasing**: Propose a phased implementation approach

Generate a JSON object with:
{{
    "strategic_vision": "Overarching strategic approach",
    "priority_actions": ["Action 1", "Action 2", ...],
    "resource_allocation_guidance": "How to allocate budget and resources",
    "governance_recommendations": "Recommended governance structures",
    "monitoring_framework": "KPIs and review mechanisms",
    "implementation_phases": {{
        "short_term": "Actions for 0-2 years",
        "medium_term": "Actions for 2-5 years",
        "long_term": "Actions for 5+ years"
    }}
}}
</INSTRUCTIONS>

<RULES>
- Output ONLY a single raw JSON object
- Be strategic and executive-focused
- The output language must be Korean.
</RULES>

JSON_ONLY:
"""
        response_str = self.llm.generate(prompt)

        try:
            portfolio_strategy = json.loads(response_str)
        except (json.JSONDecodeError, TypeError):
            portfolio_strategy = {
                "strategic_vision": "Error: Failed to generate portfolio strategy",
                "priority_actions": [],
                "resource_allocation_guidance": "N/A",
                "governance_recommendations": "N/A",
                "monitoring_framework": "N/A",
                "implementation_phases": {}
            }

        return portfolio_strategy

    def _identify_priority_sites(self, aggregated_impact: Dict,
                                 sites_data: List[Dict[str, Any]]) -> List[Dict]:
        """
        우선 조치가 필요한 사업장 식별
        """
        top_site = aggregated_impact.get("top_site")
        if not top_site:
            return []

        return [
            {
                "site_id": top_site.get("site_id"),
                "total_score": top_site.get("total_score"),
                "priority_level": "High",
                "rationale": "Highest aggregate climate risk score across all assessed risks"
            }
        ]
