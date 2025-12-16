"""
파일명: node_2b_impact_analysis_v2.py
최종 수정일: 2025-12-15
버전: v2.0

개요:
    Node 2-B: Impact Analysis (영향 분석)

    Node 2-A의 시나리오 분석 결과를 기반으로
    Top 5 물리적 리스크의 영향을 3가지 차원에서 분석합니다:
    1. 재무적 영향 (Financial Impact)
    2. 운영적 영향 (Operational Impact)
    3. 자산 영향 (Asset Impact)

주요 기능:
    1. Top 5 리스크 식별 (AAL 기준 내림차순)
    2. Node 1 템플릿 참조하여 보고서 스타일 유지
    3. Node 2-A 시나리오 분석 결과 활용
    4. 병렬 LLM 분석 (5개 리스크 동시 처리, ~30초)
    5. TextBlock x5 생성 (P1~P5 영향 분석 텍스트)

입력:
    - sites_data: List[dict] (8개 사업장 리스크 데이터)
    - scenario_analysis: Dict (Node 2-A 출력)
    - report_template: Dict (Node 1 출력)
    - sites_metadata: Optional[List[dict]] (사업장 메타데이터)

출력:
    - top_5_risks: List[dict] (Top 5 리스크 정보)
    - impact_analyses: List[dict] (5개 리스크별 영향 분석)
    - impact_blocks: List[TextBlock] (P1~P5 텍스트 블록)

설계 철학 (Node 1과 동일):
    "처음부터 완벽하게 분석하면 재분석은 필요 없다"
    - EXHAUSTIVE 프롬프트로 영향 분석 수행
    - Node 1 템플릿의 hazard_template_blocks 패턴 활용
    - 정량적 데이터(AAL) + 정성적 해석 결합

작성일: 2025-12-15 (v2 Refactoring)
"""

import asyncio
import json
from typing import Dict, Any, List, Optional
from .schemas import TextBlock


class ImpactAnalysisNode:
    """
    Node 2-B: 영향 분석 노드 v2

    역할:
        - Top 5 물리적 리스크 식별 (AAL 기준)
        - 각 리스크의 재무/운영/자산 영향 분석
        - Node 1 템플릿과 Node 2-A 시나리오 분석 결과 참조

    의존성:
        - Node 2-A 완료 필수 (시나리오 분석 결과 사용)
        - Node 1 완료 필수 (템플릿 참조)
    """

    def __init__(self, llm_client):
        """
        Node 초기화

        Args:
            llm_client: ainvoke 메서드를 지원하는 LLM 클라이언트
        """
        self.llm = llm_client

        # 리스크 한글 이름 매핑
        self.risk_name_mapping = { 
            "extreme_heat": "극심한 고온",
            "extreme_cold": "극심한 한파",
            "wildfire": "산불",
            "drought": "가뭄",
            "water_stress": "물부족",
            "sea_level_rise": "해수면 상승",
            "river_flood": "하천 홍수",            
            "urban_flood": "도시 홍수",
            "typhoon": "태풍"
        }

    async def execute(
        self,
        sites_data: List[Dict],
        scenario_analysis: Dict,
        report_template: Dict[str, Any],
        building_data: Optional[Dict[int, Dict]] = None,
        additional_data: Optional[Dict[str, Any]] = None,
        sites_metadata: Optional[List[Dict]] = None
    ) -> Dict[str, Any]:
        """
        메인 실행 함수

        Args:
            sites_data: 8개 사업장 리스크 데이터
            scenario_analysis: Node 2-A 시나리오 분석 결과
            report_template: Node 1 보고서 템플릿
            building_data: BC Agent 결과 (site_id -> building analysis)
                          agent_guidelines 내 impact_analysis_guide 활용
            additional_data: AD Agent 결과 (Excel 추가 데이터)
                            site_specific_guidelines 활용
            sites_metadata: 사업장 메타데이터 (optional)

        Returns:
            Dict containing:
                - top_5_risks: Top 5 리스크 정보
                - impact_analyses: 영향 분석 결과
                - impact_blocks: TextBlock x5
        """
        print("\n" + "="*80)
        print("🔄 Node 2-B: Impact Analysis v2 실행 시작")
        print("="*80)

        # building_data 정보 출력
        if building_data:
            print(f"📊 Building Data 활용: {len(building_data)}개 사업장")
        else:
            print("⚠️  Building Data 없음 - 기본 분석 진행")

        # additional_data 정보 출력
        if additional_data and additional_data.get("site_specific_guidelines"):
            print(f"📋 Additional Data 활용: {len(additional_data.get('site_specific_guidelines', {}))}개 사업장")
        else:
            print("⚠️  Additional Data 없음")

        # Step 1: Top 5 리스크 식별
        print("\n[1/4] Top 5 리스크 식별 중...")
        top_5_risks = self._identify_top_risks(sites_data)
        print(f"✅ Top 5 리스크 식별 완료:")
        for i, risk in enumerate(top_5_risks, 1):
            risk_name = self.risk_name_mapping.get(risk["risk_type"], risk["risk_type"])
            print(f"   P{i}. {risk_name}: AAL {risk['total_aal']:.2f}%")

        # Step 2: 사업장별 리스크 상세 데이터 추출
        print("\n[2/4] 사업장별 리스크 데이터 추출 중...")
        top_5_detailed = self._extract_risk_details(
            top_5_risks, sites_data, sites_metadata, building_data
        )
        print(f"✅ 상세 데이터 추출 완료")

        # Step 3: LLM 기반 영향 분석 (병렬)
        print("\n[3/4] LLM 기반 영향 분석 중 (병렬 처리)...")
        impact_analyses = await self._analyze_impacts_parallel(
            top_5_detailed,
            scenario_analysis,
            report_template,
            building_data,
            additional_data
        )
        print(f"✅ 영향 분석 완료")

        # Step 4: TextBlock x5 생성
        print("\n[4/4] TextBlock x5 생성 중...")
        impact_blocks = self._create_impact_text_blocks(impact_analyses, report_template)
        print(f"✅ TextBlock 생성 완료")

        print("\n" + "="*80)
        print("✅ Node 2-B 실행 완료!")
        print("="*80)

        return {
            "top_5_risks": top_5_risks,
            "impact_analyses": impact_analyses,
            "impact_blocks": impact_blocks
        }

    def _identify_top_risks(self, sites_data: List[Dict]) -> List[Dict]:
        """
        Top 5 리스크 식별 (AAL 기준 내림차순)

        Args:
            sites_data: 사업장 데이터

        Returns:
            List[Dict]: [
                {"risk_type": "river_flood", "total_aal": 18.2},
                ...
            ]
        """
        risk_aal_map = {}

        # 모든 사업장의 리스크 AAL 합산
        for site in sites_data:
            for risk_result in site.get("risk_results", []):
                risk_type = risk_result.get("risk_type")
                aal = risk_result.get("final_aal", 0)

                if risk_type:
                    risk_aal_map[risk_type] = risk_aal_map.get(risk_type, 0) + aal

        # AAL 기준 내림차순 정렬 → Top 5
        sorted_risks = sorted(risk_aal_map.items(), key=lambda x: x[1], reverse=True)[:5]

        return [
            {
                "risk_type": risk_type,
                "total_aal": round(aal, 2),
                "rank": i + 1
            }
            for i, (risk_type, aal) in enumerate(sorted_risks)
        ]

    def _extract_risk_details(
        self,
        top_5_risks: List[Dict],
        sites_data: List[Dict],
        sites_metadata: Optional[List[Dict]],
        building_data: Optional[Dict[int, Dict]] = None
    ) -> List[Dict]:
        """
        Top 5 리스크의 사업장별 상세 데이터 추출

        Args:
            top_5_risks: Top 5 리스크 정보
            sites_data: 사업장 데이터
            sites_metadata: 사업장 메타데이터
            building_data: BC Agent 결과 (site_id -> building analysis)

        Returns:
            List[Dict]: Top 5 리스크별 상세 정보 (building_data 포함)
        """
        detailed_risks = []

        for risk_info in top_5_risks:
            risk_type = risk_info["risk_type"]

            # 해당 리스크에 영향받는 사업장 추출
            affected_sites = []

            for site in sites_data:
                site_id = site.get("site_id")
                site_name = site.get("site_name", "Unknown Site")

                # 해당 리스크 찾기
                for risk_result in site.get("risk_results", []):
                    if risk_result.get("risk_type") == risk_type:
                        aal = risk_result.get("final_aal", 0)

                        if aal > 0:
                            site_info = {
                                "site_id": site_id,
                                "site_name": site_name,
                                "aal": round(aal, 2),
                                "risk_details": risk_result
                            }

                            # building_data에서 해당 사업장 건물 특성 추가
                            if building_data and site_id in building_data:
                                bd = building_data[site_id]
                                site_info["building_characteristics"] = {
                                    "structural_grade": bd.get("structural_grade", "N/A"),
                                    "vulnerabilities": bd.get("vulnerabilities", []),
                                    "resilience": bd.get("resilience", []),
                                    "agent_guidelines": bd.get("agent_guidelines", {})
                                }

                            affected_sites.append(site_info)

            # 상세 정보 구성
            detailed_risks.append({
                "risk_type": risk_type,
                "rank": risk_info["rank"],
                "total_aal": risk_info["total_aal"],
                "affected_sites": affected_sites,
                "num_affected_sites": len(affected_sites)
            })

        return detailed_risks

    async def _analyze_impacts_parallel(
        self,
        top_5_detailed: List[Dict],
        scenario_analysis: Dict,
        report_template: Dict,
        building_data: Optional[Dict[int, Dict]] = None,
        additional_data: Optional[Dict[str, Any]] = None
    ) -> List[Dict]:
        """
        Top 5 리스크 병렬 영향 분석 (~30초)

        Args:
            top_5_detailed: Top 5 리스크 상세 정보 (building_characteristics 포함)
            scenario_analysis: Node 2-A 시나리오 분석 결과
            report_template: Node 1 템플릿
            building_data: BC Agent 결과 (site_id -> building analysis)
            additional_data: AD Agent 결과 (Excel 추가 데이터)

        Returns:
            List[Dict]: 5개 리스크별 영향 분석 결과
        """
        tasks = [
            self._analyze_single_risk_impact(risk, scenario_analysis, report_template, building_data, additional_data)
            for risk in top_5_detailed
        ]
        impact_analyses = await asyncio.gather(*tasks)
        return impact_analyses

    async def _analyze_single_risk_impact(
        self,
        risk: Dict,
        scenario_analysis: Dict,
        report_template: Dict,
        building_data: Optional[Dict[int, Dict]] = None,
        additional_data: Optional[Dict[str, Any]] = None
    ) -> Dict:
        """
        단일 리스크 영향 분석 (EXHAUSTIVE 프롬프트 + Building Data + Additional Data)

        Args:
            risk: 리스크 상세 정보 (building_characteristics 포함)
            scenario_analysis: 시나리오 분석 결과
            report_template: Node 1 템플릿
            building_data: BC Agent 결과 (site_id -> building analysis)
            additional_data: AD Agent 결과 (Excel 추가 데이터)

        Returns:
            Dict: {
                "risk_type": str,
                "rank": int,
                "financial_impact": str,
                "operational_impact": str,
                "asset_impact": str,
                "summary": str
            }
        """
        risk_type = risk["risk_type"]
        risk_name_kr = self.risk_name_mapping.get(risk_type, risk_type)
        total_aal = risk["total_aal"]
        affected_sites = risk["affected_sites"]

        # Node 1 템플릿에서 참조할 정보 추출
        hazard_templates = report_template.get("hazard_template_blocks", {})
        tone = report_template.get("tone", {})
        reusable_paragraphs = report_template.get("reusable_paragraphs", [])

        # 시나리오 분석 결과 요약
        scenarios = scenario_analysis.get("scenarios", {})
        scenario_summary = self._format_scenarios_brief(scenarios)

        # 사업장 정보 포맷팅 (건물 특성 포함)
        sites_info = self._format_affected_sites_with_building(affected_sites)

        # 건물 특성 기반 영향 분석 가이드 추출
        building_impact_guide = self._extract_building_impact_guide(affected_sites, risk_type)

        # 추가 데이터(Excel) 기반 컨텍스트 추출
        additional_context = self._extract_additional_data_context(additional_data, affected_sites)

        # EXHAUSTIVE 프롬프트 작성
        prompt = f"""
<ROLE>
You are an ELITE climate risk impact analyst specializing in TCFD disclosures.
Your task is to analyze the impact of {risk_name_kr} ({risk_type}) risk
on the company's operations, assets, and financial performance.
</ROLE>

<CRITICAL_ANALYSIS_REQUIREMENTS>

1. FINANCIAL IMPACT (재무적 영향)
   - Translate AAL ({total_aal}%) into monetary terms
   - Estimate potential losses in KRW (billion won)
   - Consider insurance coverage and deductibles
   - Project impact on earnings (EBITDA, net income)
   - Assess impact on asset valuation
   - **Use building structural grades to refine damage estimates**

2. OPERATIONAL IMPACT (운영적 영향)
   - Identify critical operations at risk
   - Estimate potential downtime (hours/days)
   - Assess supply chain disruptions
   - Evaluate impact on service delivery
   - Consider cascading effects on other sites
   - **Account for building vulnerabilities in downtime estimates**

3. ASSET IMPACT (자산 영향)
   - Assess physical damage to buildings and equipment
   - Identify vulnerable infrastructure (power, cooling, IT)
   - Evaluate long-term asset degradation
   - Consider replacement vs. retrofit costs
   - Assess impact on asset lifespan
   - **Use building-specific vulnerability data for precise assessment**

4. SCENARIO-SPECIFIC ANALYSIS
   - How does this risk evolve across SSP scenarios?
   - Which scenario poses the greatest threat?
   - What are the inflection points?

5. STAKEHOLDER COMMUNICATION
   - Use clear, data-driven language
   - Support claims with specific numbers (AAL, sites affected, etc.)
   - Frame impacts in business terms
   - Provide context: is this acceptable risk or urgent action needed?

</CRITICAL_ANALYSIS_REQUIREMENTS>

<INPUT_DATA>

Risk Information:
- Risk Type: {risk_name_kr} ({risk_type})
- Rank: P{risk["rank"]} (Top {risk["rank"]} out of 9 risks)
- Total AAL: {total_aal}%
- Number of Affected Sites: {risk["num_affected_sites"]}

Affected Sites (with Building Characteristics):
{sites_info}

Building-Specific Impact Analysis Guide:
{building_impact_guide}

Additional Site-Specific Context (from Excel data):
{additional_context}

Scenario Analysis Context:
{scenario_summary}

Reference Template (from previous reports):

Tone: {json.dumps(tone, ensure_ascii=False, indent=2)}

Hazard Template for {risk_type}:
{json.dumps(hazard_templates.get(risk_type, {}), ensure_ascii=False, indent=2)}

Sample Paragraphs:
{self._format_sample_paragraphs(reusable_paragraphs[:3])}

</INPUT_DATA>

<OUTPUT_REQUIREMENTS>

Generate a comprehensive impact analysis in Korean with 3 sections:

1. 재무적 영향 (Financial Impact)
- Estimated financial exposure in KRW (billion won)
- Impact on key financial metrics (revenue, EBITDA, etc.)
- Insurance considerations
- Reference building structural grades where relevant
- 2-3 paragraphs

2. 운영적 영향 (Operational Impact)
- Critical operations at risk
- Estimated downtime or service disruption
- Supply chain and interdependency effects
- Consider building vulnerabilities in operational risk
- 2-3 paragraphs

3. 자산 영향 (Asset Impact)
- Physical damage assessment based on building characteristics
- Infrastructure vulnerabilities (cite specific building vulnerabilities)
- Long-term asset degradation
- Building resilience factors that may mitigate impacts
- 2-3 paragraphs

Summary (1 paragraph)
- Overall assessment of risk severity
- Key numbers: AAL, estimated loss, affected sites
- Building-specific factors affecting overall risk
- Urgency level: immediate action needed or manageable?

Formatting:
- Use Markdown for structure
- Bold key metrics (AAL, costs, downtime)
- Use bullet points for lists
- Cite specific numbers from input data
- Reference building grades (e.g., "B등급 건물의 경우...")

Length: 600-900 words total (comprehensive but concise)

</OUTPUT_REQUIREMENTS>

<QUALITY_CHECKLIST>
Before submitting, verify:
- [ ] All 3 impact dimensions are analyzed with equal depth
- [ ] Financial impact includes specific KRW estimates
- [ ] Operational impact cites affected sites and operations
- [ ] Asset impact describes physical vulnerabilities from building data
- [ ] Building structural grades are referenced where relevant
- [ ] Summary synthesizes key findings including building factors
- [ ] Tone matches the reference template style
- [ ] Output is ready for direct inclusion in TCFD Strategy section
</QUALITY_CHECKLIST>

Now, generate the impact analysis as a JSON object with keys:
"financial_impact", "operational_impact", "asset_impact", "summary"
"""

        # LLM 호출
        try:
            response = await self.llm.ainvoke(prompt)

            # JSON 파싱 시도 (마크다운 코드 블록 처리)
            json_str = self._extract_json_from_response(response)
            if json_str:
                parsed = json.loads(json_str)
                return {
                    "risk_type": risk_type,
                    "rank": risk["rank"],
                    "total_aal": total_aal,
                    "financial_impact": parsed.get("financial_impact", "분석 중"),
                    "operational_impact": parsed.get("operational_impact", "분석 중"),
                    "asset_impact": parsed.get("asset_impact", "분석 중"),
                    "summary": parsed.get("summary", "")
                }
            else:
                # 텍스트 응답인 경우 섹션 분리 시도
                return self._parse_text_response(response, risk_type, risk["rank"], total_aal)

        except Exception as e:
            print(f"⚠️  리스크 {risk_type} 분석 실패: {e}")
            # Fallback
            return self._generate_fallback_impact(risk)

    def _format_scenarios_brief(self, scenarios: Dict) -> str:
        """시나리오 분석 결과 요약 (간략)"""
        lines = []
        for scenario_key, data in scenarios.items():
            aal_start = data.get("aal_values", [0])[0]
            aal_end = data.get("aal_values", [0])[-1]
            lines.append(f"- {scenario_key.upper()}: {aal_start}% (2024) → {aal_end}% (2100)")
        return "\n".join(lines)

    def _format_affected_sites(self, affected_sites: List[Dict]) -> str:
        """영향받는 사업장 포맷팅"""
        if not affected_sites:
            return "No sites affected"

        lines = []
        for site in affected_sites[:5]:  # 최대 5개만 표시
            site_name = site.get("site_name", "Unknown")
            aal = site.get("aal", 0)
            lines.append(f"- {site_name}: AAL {aal}%")

        if len(affected_sites) > 5:
            lines.append(f"- ... (총 {len(affected_sites)}개 사업장)")

        return "\n".join(lines)

    def _format_affected_sites_with_building(self, affected_sites: List[Dict]) -> str:
        """건물 특성을 포함한 사업장 정보 포맷팅"""
        if not affected_sites:
            return "No sites affected"

        lines = []
        for site in affected_sites[:5]:  # 최대 5개만 표시
            site_name = site.get("site_name", "Unknown")
            aal = site.get("aal", 0)

            # 기본 정보
            site_line = f"- **{site_name}**: AAL {aal}%"

            # 건물 특성 정보 추가
            bc = site.get("building_characteristics", {})
            if bc:
                grade = bc.get("structural_grade", "N/A")
                vulnerabilities = bc.get("vulnerabilities", [])
                resilience = bc.get("resilience", [])

                site_line += f"\n  - 구조등급: {grade}"

                if vulnerabilities:
                    vuln_str = ", ".join(v.get("category", str(v)) if isinstance(v, dict) else str(v)
                                        for v in vulnerabilities[:3])
                    site_line += f"\n  - 취약점: {vuln_str}"

                if resilience:
                    res_str = ", ".join(r.get("factor", str(r)) if isinstance(r, dict) else str(r)
                                       for r in resilience[:3])
                    site_line += f"\n  - 복원력: {res_str}"

            lines.append(site_line)

        if len(affected_sites) > 5:
            lines.append(f"- ... (총 {len(affected_sites)}개 사업장)")

        return "\n".join(lines)

    def _extract_building_impact_guide(self, affected_sites: List[Dict], risk_type: str) -> str:
        """건물 특성 기반 영향 분석 가이드 추출 (BC Agent agent_guidelines 활용)"""
        guides = []

        for site in affected_sites[:5]:  # 최대 5개 사업장
            bc = site.get("building_characteristics", {})
            agent_guidelines = bc.get("agent_guidelines", {})

            if not agent_guidelines:
                continue

            site_name = site.get("site_name", "Unknown")

            # impact_analysis_guide 섹션 추출 (BC Agent v08 형식)
            impact_guide = agent_guidelines.get("impact_analysis_guide", {})
            if impact_guide:
                guide_parts = [f"**{site_name}**:"]

                # 재무적 영향 가이드 (financial_impact)
                financial = impact_guide.get("financial_impact", {})
                if financial:
                    exposure = financial.get("estimated_exposure", "N/A")
                    cost_drivers = financial.get("key_cost_drivers", [])
                    narrative = financial.get("narrative", "")
                    guide_parts.append(f"  - 재무 노출: {exposure}")
                    if cost_drivers:
                        guide_parts.append(f"    비용 요인: {', '.join(cost_drivers[:3])}")
                    if narrative:
                        guide_parts.append(f"    분석: {narrative[:100]}...")

                # 운영적 영향 가이드 (operational_impact)
                operational = impact_guide.get("operational_impact", {})
                if operational:
                    downtime = operational.get("estimated_downtime", "N/A")
                    critical_systems = operational.get("critical_systems_at_risk", [])
                    narrative = operational.get("narrative", "")
                    guide_parts.append(f"  - 운영: 예상 다운타임 {downtime}")
                    if critical_systems:
                        guide_parts.append(f"    위험 시스템: {', '.join(critical_systems[:3])}")
                    if narrative:
                        guide_parts.append(f"    분석: {narrative[:100]}...")

                # 자산 영향 가이드 (asset_impact)
                asset = impact_guide.get("asset_impact", {})
                if asset:
                    vulnerable = asset.get("vulnerable_assets", [])
                    damage_potential = asset.get("damage_potential", "N/A")
                    narrative = asset.get("narrative", "")
                    if vulnerable:
                        guide_parts.append(f"  - 자산: 취약 자산 - {', '.join(vulnerable[:3])}")
                    guide_parts.append(f"    손상 가능성: {damage_potential}")
                    if narrative:
                        guide_parts.append(f"    분석: {narrative[:100]}...")

                guides.append("\n".join(guide_parts))

        if not guides:
            return "건물 특성 기반 가이드 없음 (기본 분석 수행)"

        return "\n\n".join(guides)

    def _extract_additional_data_context(
        self,
        additional_data: Optional[Dict[str, Any]],
        affected_sites: List[Dict]
    ) -> str:
        """Excel 추가 데이터에서 사업장별 컨텍스트 추출 (AD Agent site_specific_guidelines 활용)"""
        if not additional_data:
            return "추가 데이터 없음"

        site_guidelines = additional_data.get("site_specific_guidelines", {})
        if not site_guidelines:
            return "추가 데이터 없음"

        contexts = []

        # 영향받는 사업장들에 대한 추가 데이터 추출
        for site in affected_sites[:5]:  # 최대 5개 사업장
            site_id = site.get("site_id")
            site_name = site.get("site_name", "Unknown")

            if site_id in site_guidelines:
                guideline = site_guidelines[site_id]
                guideline_text = guideline.get("guideline", "")
                key_insights = guideline.get("key_insights", [])

                if guideline_text or key_insights:
                    context_parts = [f"**{site_name}**:"]

                    # 핵심 인사이트 추출
                    if key_insights:
                        context_parts.append(f"  - 핵심 인사이트: {', '.join(key_insights[:3])}")

                    # 가이드라인 요약 (처음 200자)
                    if guideline_text and len(guideline_text) > 50:
                        summary = guideline_text[:200] + "..." if len(guideline_text) > 200 else guideline_text
                        context_parts.append(f"  - 요약: {summary}")

                    contexts.append("\n".join(context_parts))

        if not contexts:
            return "해당 사업장에 대한 추가 데이터 없음"

        return "\n\n".join(contexts)

    def _format_sample_paragraphs(self, paragraphs: List[str]) -> str:
        """샘플 문단 포맷팅"""
        if not paragraphs:
            return "N/A"

        formatted = []
        for i, para in enumerate(paragraphs[:3], 1):
            formatted.append(f"{i}. {para}")

        return "\n".join(formatted)

    def _ensure_string(self, value: Any) -> str:
        """
        값을 문자열로 변환 (dict/list인 경우 JSON 문자열로)

        Args:
            value: 변환할 값

        Returns:
            str: 문자열 값
        """
        if value is None:
            return "분석 중"
        if isinstance(value, str):
            return value
        if isinstance(value, (dict, list)):
            return json.dumps(value, ensure_ascii=False, indent=2)
        return str(value)

    def _extract_json_from_response(self, response: str) -> Optional[str]:
        """
        LLM 응답에서 JSON 문자열 추출 (마크다운 코드 블록 처리)

        Args:
            response: LLM 응답 문자열

        Returns:
            Optional[str]: 추출된 JSON 문자열 또는 None
        """
        import re

        # 1. 마크다운 코드 블록에서 JSON 추출 (```json ... ``` 또는 ``` ... ```)
        json_block_pattern = r'```(?:json)?\s*([\s\S]*?)\s*```'
        matches = re.findall(json_block_pattern, response)

        if matches:
            # 첫 번째 코드 블록 내용 확인
            for match in matches:
                content = match.strip()
                if content.startswith('{') and content.endswith('}'):
                    return content

        # 2. 코드 블록 없이 직접 JSON인 경우
        response_stripped = response.strip()
        if response_stripped.startswith('{') and response_stripped.endswith('}'):
            return response_stripped

        # 3. 응답 내에서 { ... } 패턴 찾기
        json_pattern = r'\{[\s\S]*\}'
        match = re.search(json_pattern, response)
        if match:
            return match.group(0)

        return None

    def _parse_text_response(self, response: str, risk_type: str, rank: int, total_aal: float) -> Dict:
        """텍스트 응답을 섹션별로 분리 (간단한 파싱)"""
        # 섹션 키워드 기반 분리
        sections = {
            "financial_impact": "",
            "operational_impact": "",
            "asset_impact": "",
            "summary": ""
        }

        # 간단한 키워드 매칭 (실제로는 더 정교한 파싱 필요)
        if "재무" in response or "Financial" in response:
            sections["financial_impact"] = response[:len(response)//3]
        if "운영" in response or "Operational" in response:
            sections["operational_impact"] = response[len(response)//3:2*len(response)//3]
        if "자산" in response or "Asset" in response:
            sections["asset_impact"] = response[2*len(response)//3:]

        sections["summary"] = response[:200] + "..."

        return {
            "risk_type": risk_type,
            "rank": rank,
            "total_aal": total_aal,
            **sections
        }

    def _generate_fallback_impact(self, risk: Dict) -> Dict:
        """LLM 실패 시 기본 영향 분석 생성"""
        risk_type = risk["risk_type"]
        risk_name_kr = self.risk_name_mapping.get(risk_type, risk_type)
        total_aal = risk["total_aal"]

        return {
            "risk_type": risk_type,
            "rank": risk["rank"],
            "total_aal": total_aal,
            "financial_impact": f"{risk_name_kr} 리스크로 인한 재무적 영향은 AAL {total_aal}%로 산정되었습니다.",
            "operational_impact": f"{risk['num_affected_sites']}개 사업장의 운영에 영향을 미칠 것으로 예상됩니다.",
            "asset_impact": "자산 손상 및 설비 피해가 예상됩니다.",
            "summary": f"{risk_name_kr}는 Top {risk['rank']} 리스크로 식별되었습니다."
        }

    def _create_impact_text_blocks(
        self,
        impact_analyses: List[Dict],
        report_template: Dict
    ) -> List[Dict]:
        """
        P1~P5 영향 분석 TextBlock 생성

        Args:
            impact_analyses: 영향 분석 결과
            report_template: Node 1 템플릿

        Returns:
            List[Dict]: TextBlock x5
        """
        impact_blocks = []

        for i, impact in enumerate(impact_analyses, 1):
            risk_type = impact.get("risk_type", "Unknown")
            risk_name_kr = self.risk_name_mapping.get(risk_type, risk_type)
            total_aal = impact.get("total_aal", 0)

            # 영향 분석 내용 조합
            content_parts = []

            # 요약 (dict/list인 경우 문자열로 변환)
            summary = impact.get("summary")
            if summary:
                content_parts.append(self._ensure_string(summary))
                content_parts.append("")

            # 재무적 영향
            content_parts.append("### 재무적 영향")
            content_parts.append(self._ensure_string(impact.get("financial_impact", "분석 중")))
            content_parts.append("")

            # 운영적 영향
            content_parts.append("### 운영적 영향")
            content_parts.append(self._ensure_string(impact.get("operational_impact", "분석 중")))
            content_parts.append("")

            # 자산 영향
            content_parts.append("### 자산 영향")
            content_parts.append(self._ensure_string(impact.get("asset_impact", "분석 중")))

            content = "\n".join(content_parts)

            # TextBlock 생성
            text_block = {
                "type": "text",
                "subheading": f"P{i}. {risk_name_kr} 영향 분석 (AAL {total_aal}%)",
                "content": content
            }

            impact_blocks.append(text_block)

        return impact_blocks


# ============================================================
# Utility Functions
# ============================================================

def validate_text_block(text_block: Dict) -> bool:
    """
    TextBlock이 schemas.py 구조를 준수하는지 검증

    Args:
        text_block: 검증할 TextBlock JSON

    Returns:
        bool: 유효하면 True
    """
    try:
        TextBlock(**text_block)
        return True
    except Exception as e:
        print(f"❌ TextBlock 검증 실패: {e}")
        return False
