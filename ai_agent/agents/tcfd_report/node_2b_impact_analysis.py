"""
파일명: node_2b_impact_analysis_v2.py
최종 수정일: 2025-12-17
버전: v2.1 - ALL 9 RISKS

개요:
    Node 2-B: Impact Analysis (영향 분석)

    Node 2-A의 시나리오 분석 결과를 기반으로
    전체 9개 물리적 리스크의 영향을 3가지 차원에서 분석합니다:
    1. 재무적 영향 (Financial Impact)
    2. 운영적 영향 (Operational Impact)
    3. 자산 영향 (Asset Impact)

주요 기능:
    1. 전체 9개 리스크 식별 (AAL 기준 내림차순)
    2. Node 1 템플릿 참조하여 보고서 스타일 유지
    3. Node 2-A 시나리오 분석 결과 활용
    4. 병렬 LLM 분석 (9개 리스크 동시 처리)
    5. TextBlock x9 생성 (P1~P9 영향 분석 텍스트)

입력:
    - sites_data: List[dict] (사업장 리스크 데이터)
    - scenario_analysis: Dict (Node 2-A 출력)
    - report_template: Dict (Node 1 출력)
    - sites_metadata: Optional[List[dict]] (사업장 메타데이터)

출력:
    - top_risks: List[dict] (전체 9개 리스크 정보, AAL 순위별)
    - impact_analyses: List[dict] (9개 리스크별 영향 분석)
    - impact_blocks: List[TextBlock] (P1~P9 텍스트 블록)

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
from .llm_output_logger import get_logger
from ...utils.rag_helpers import RAGEngine
from ...utils.langsmith_tracer import get_tracer
from ...config.settings import Config


class ImpactAnalysisNode:
    """
    Node 2-B: 영향 분석 노드 v2.1 - ALL 9 RISKS

    역할:
        - 전체 9개 물리적 리스크 식별 (AAL 기준 내림차순)
        - 각 리스크의 재무/운영/자산 영향 분석
        - Node 1 템플릿과 Node 2-A 시나리오 분석 결과 참조

    의존성:
        - Node 2-A 완료 필수 (시나리오 분석 결과 사용)
        - Node 1 완료 필수 (템플릿 참조)
    """

    def __init__(self, llm_client, config: Config = None):
        """
        Node 초기화

        Args:
            llm_client: ainvoke 메서드를 지원하는 LLM 클라이언트
            config: 설정 객체 (LangSmith 등)
        """
        self.llm = llm_client
        self.config = config or Config()

        # RAG Engine for impact analysis context
        self.rag = RAGEngine(source="benchmark")

        # LangSmith Tracer
        self.tracer = get_tracer(self.config)

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
        sites_metadata: Optional[List[Dict]] = None,
        validation_feedback: Optional[Dict] = None
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
                - top_risks: 전체 9개 리스크 정보 (AAL 순위별)
                - impact_analyses: 영향 분석 결과
                - impact_blocks: TextBlock x9
        """
        print("\n" + "="*80)
        print("🔄 Node 2-B: Impact Analysis v2.1 - ALL 9 RISKS")
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

        # Step 1: 전체 9개 리스크 식별 (AAL 기준 내림차순)
        print("\n[1/4] 전체 9개 리스크 식별 중...")
        top_risks = self._identify_top_risks(sites_data)
        print(f"✅ 전체 {len(top_risks)}개 리스크 식별 완료:")
        for i, risk in enumerate(top_risks, 1):
            risk_name = self.risk_name_mapping.get(risk["risk_type"], risk["risk_type"])
            print(f"   P{i}. {risk_name}: AAL {risk['total_aal']:.2f}%")

        # Step 2: 사업장별 리스크 상세 데이터 추출
        print("\n[2/4] 사업장별 리스크 데이터 추출 중...")
        risks_detailed = self._extract_risk_details(
            top_risks, sites_data, sites_metadata, building_data
        )
        print(f"✅ 상세 데이터 추출 완료")

        # Step 3: LLM 기반 영향 분석 (병렬)
        print(f"\n[3/4] LLM 기반 영향 분석 중 (병렬 처리 - {len(risks_detailed)}개 리스크)...")
        impact_analyses = await self._analyze_impacts_parallel(
            risks_detailed,
            scenario_analysis,
            report_template,
            building_data,
            additional_data
        )
        print(f"✅ 영향 분석 완료")

        # Step 4: TextBlock 생성
        print(f"\n[4/4] TextBlock x{len(impact_analyses)} 생성 중...")
        impact_blocks = self._create_impact_text_blocks(impact_analyses, report_template)
        print(f"✅ TextBlock 생성 완료")

        print("\n" + "="*80)
        print("✅ Node 2-B 실행 완료!")
        print("="*80)

        return {
            "top_risks": top_risks,
            "impact_analyses": impact_analyses,
            "impact_blocks": impact_blocks
        }

    def _identify_top_risks(self, sites_data: List[Dict]) -> List[Dict]:
        """
        전체 9개 리스크 식별 (AAL 기준 내림차순)

        Args:
            sites_data: 사업장 데이터

        Returns:
            List[Dict]: [
                {"risk_type": "river_flood", "total_aal": 18.2, "rank": 1},
                {"risk_type": "typhoon", "total_aal": 15.5, "rank": 2},
                ... (총 9개)
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

        # AAL 기준 내림차순 정렬 → 전체 리스크 (9개)
        sorted_risks = sorted(risk_aal_map.items(), key=lambda x: x[1], reverse=True)

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
        top_risks: List[Dict],
        sites_data: List[Dict],
        sites_metadata: Optional[List[Dict]],
        building_data: Optional[Dict[int, Dict]] = None
    ) -> List[Dict]:
        """
        전체 리스크의 사업장별 상세 데이터 추출

        Args:
            top_risks: 전체 리스크 정보 (AAL 순위별)
            sites_data: 사업장 데이터
            sites_metadata: 사업장 메타데이터
            building_data: BC Agent 결과 (site_id -> building analysis)

        Returns:
            List[Dict]: 전체 리스크별 상세 정보 (building_data 포함)
        """
        detailed_risks = []

        for risk_info in top_risks:
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
        risks_detailed: List[Dict],
        scenario_analysis: Dict,
        report_template: Dict,
        building_data: Optional[Dict[int, Dict]] = None,
        additional_data: Optional[Dict[str, Any]] = None
    ) -> List[Dict]:
        """
        전체 리스크 병렬 영향 분석

        Args:
            risks_detailed: 전체 리스크 상세 정보 (building_characteristics 포함)
            scenario_analysis: Node 2-A 시나리오 분석 결과
            report_template: Node 1 템플릿
            building_data: BC Agent 결과 (site_id -> building analysis)
            additional_data: AD Agent 결과 (Excel 추가 데이터)

        Returns:
            List[Dict]: 전체 리스크별 영향 분석 결과
        """
        tasks = [
            self._analyze_single_risk_impact(risk, scenario_analysis, report_template, building_data, additional_data)
            for risk in risks_detailed
        ]
        impact_analyses = await asyncio.gather(*tasks)
        return impact_analyses

    async def _analyze_single_risk_impact(
        self,
        risk: Dict,
        scenario_analysis: Dict,
        report_template: Dict,
        building_data: Optional[Dict[int, Dict]] = None,
        additional_data: Optional[Dict[str, Any]] = None,
        validation_feedback: Optional[Dict] = None
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

        # RAG 컨텍스트 조회 (벤치마크 보고서에서 유사 영향 분석 사례 검색)
        rag_context = await self._get_rag_context(risk_type, risk_name_kr)

        # EXHAUSTIVE 프롬프트 작성
        prompt = f"""
<ROLE>
You are an ELITE climate risk impact analyst specializing in TCFD disclosures.
Your task is to analyze the impact of {risk_name_kr} ({risk_type}) risk
on the company's operations, assets, and financial performance.
</ROLE>

<CRITICAL_ANALYSIS_REQUIREMENTS>

⚠️ STRICT NO-HALLUCINATION POLICY - Official Disclosure Report ⚠️
- Use ONLY data provided in INPUT_DATA
- DO NOT generate specific monetary amounts (억원/KRW) - asset value data not provided
- DO NOT mention insurance coverage, deductibles, or specific costs
- For unknown information, state "추가 분석 필요" or "데이터 확보 후 산정 예정"

1. FINANCIAL IMPACT (재무적 영향) - Based on PROVIDED data only
   - Analyze relative financial exposure using AAL ({total_aal}%)
   - Explain TYPES of potential financial impacts (revenue, asset value, restoration costs)
   - Describe general financial impact mechanisms for {risk_type}
   - Interpret severity: AAL 0-3% (Low), 3-10% (Medium), 10-30% (High), 30%+ (Very High)
   - ⚠️ DO NOT estimate specific KRW amounts without asset value data

2. OPERATIONAL IMPACT (운영적 영향) - Based on PROVIDED data only
   - Identify operational areas at risk based on site characteristics
   - Analyze using number of affected sites ({risk["num_affected_sites"]}) from INPUT_DATA
   - If building data provided, use those characteristics for vulnerability analysis
   - Describe potential operational disruption types
   - ⚠️ DO NOT estimate specific downtime hours without operational data

3. ASSET IMPACT (자산 영향) - Based on PROVIDED data only
   - Analyze using building structural grades IF provided in INPUT_DATA
   - Describe general impact mechanisms of {risk_type} on physical assets
   - Evaluate vulnerabilities based on provided building characteristics only
   - Provide qualitative assessment of long-term asset value impact
   - ⚠️ DO NOT estimate replacement/retrofit costs without cost data

4. SCENARIO-SPECIFIC ANALYSIS
   - How does this risk evolve across SSP scenarios (based on provided scenario data)?
   - Which scenario poses the greatest threat based on AAL projections?

5. DATA-DRIVEN COMMUNICATION
   - Use clear, data-driven language
   - Support claims ONLY with numbers from INPUT_DATA (AAL, sites affected, etc.)
   - Frame impacts in qualitative business terms when quantitative data is unavailable

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

<RAG_REFERENCE_CONTEXT>
The following are relevant excerpts from benchmark TCFD/ESG reports for reference on writing style and structure:
{rag_context}
</RAG_REFERENCE_CONTEXT>
{self._format_validation_feedback(validation_feedback)}

</INPUT_DATA>

<OUTPUT_REQUIREMENTS>

Generate a comprehensive impact analysis in **Korean** with 3 sections:

⚠️ CRITICAL: NO HALLUCINATION - This is for official disclosure ⚠️
- Use ONLY information explicitly provided in INPUT_DATA
- For missing information, state "추가 분석 필요" (additional analysis required) or "데이터 확보 후 산정 예정" (to be calculated after data acquisition)
- DO NOT infer specific monetary amounts (억원/KRW) from AAL(%) - asset value data is required for monetary calculations
- Avoid speculation, assumptions, or generalizations - perform data-driven analysis only

1. Financial Impact (재무적 영향) - Minimum 400 words
- Analyze relative financial exposure based on AAL(%) (state that absolute amounts cannot be calculated without asset value data)
- Explain potential impact types on financial statements (revenue, asset value, restoration costs, etc.)
- Describe general financial impact mechanisms for this risk type
- Interpret relative severity based on AAL level (provide High/Medium/Low criteria)
- **4-5 paragraphs (80-100 words each)**

2. Operational Impact (운영적 영향) - Minimum 400 words
- Identify operational areas that may be affected by this risk
- Analyze based on number and characteristics of affected sites (use affected_sites from INPUT_DATA)
- If building characteristics data is available, analyze vulnerabilities based on that information
- Describe expected types of operational disruption when risk occurs
- **4-5 paragraphs (80-100 words each)**

3. Asset Impact (자산 영향) - Minimum 400 words
- Analyze based on building structural grades and vulnerability data (only if provided in INPUT_DATA)
- Describe general impact mechanisms of this risk type on assets
- Evaluate vulnerabilities based on provided building characteristics (age, structure type, etc.)
- Provide qualitative assessment of long-term asset value impact
- **4-5 paragraphs (80-100 words each)**

Summary (2-3 paragraphs, minimum 150 words)
- Overall risk assessment based on AAL
- Cite only provided data (number of affected sites, AAL figures, etc.)
- Recommendations for risk management direction

Formatting:
- Use Markdown for structure (###, ####)
- **Bold** key metrics (AAL %, number of affected sites)
- Clearly indicate that data source is INPUT_DATA
- Mark uncertain information as "추정" (estimated) or "추가 분석 필요" (additional analysis required)

**CRITICAL: Length MUST be 1,200-1,800 words total (report-level detailed analysis required)**
**Each section must be at least 400 words**
**⚠️ DO NOT generate unprovided information (insurance, specific amounts, quarterly schedules, etc.)**

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
            # AIMessage에서 content 추출
            response_text = response.content if hasattr(response, 'content') else str(response)

            # JSON 파싱 시도 (마크다운 코드 블록 처리)
            json_str = self._extract_json_from_response(response_text)
            if json_str:
                parsed = json.loads(json_str)
                result = {
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
                result = self._parse_text_response(response, risk_type, risk["rank"], total_aal)

            # LLM 출력 로깅
            logger = get_logger()
            logger.log_output(
                node_name="node_2b",
                output_type="impact",
                content=response_text,
                metadata={
                    "total_aal": total_aal,
                    "num_affected_sites": risk["num_affected_sites"],
                    "prompt_length": len(prompt)
                },
                risk_type=risk_type,
                risk_rank=risk["rank"]
            )

            return result

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

    async def _get_rag_context(self, risk_type: str, risk_name_kr: str) -> str:
        """
        RAG 엔진에서 해당 리스크 유형에 대한 벤치마크 컨텍스트 조회

        Args:
            risk_type: 리스크 유형 (영문)
            risk_name_kr: 리스크 유형 (한글)

        Returns:
            str: RAG에서 검색된 관련 컨텍스트
        """
        try:
            # 리스크 유형에 맞는 쿼리 생성
            query = f"TCFD physical risk impact analysis {risk_type} {risk_name_kr} financial operational asset"

            # RAG 검색 수행 (query 메서드는 동기 메서드)
            results = self.rag.query(query, top_k=3)

            if not results:
                return "No benchmark reference available for this risk type."

            # 결과 포맷팅
            context_parts = []
            for i, result in enumerate(results, 1):
                content = result.get("text", "")[:500]  # 각 결과 최대 500자
                source = result.get("source", "Unknown")
                context_parts.append(f"[Reference {i}] (Source: {source})\n{content}")

            return "\n\n".join(context_parts)

        except Exception as e:
            print(f"⚠️  RAG 조회 실패: {e}")
            return "RAG context unavailable - proceed with provided data only."

    def _format_validation_feedback(self, feedback: Optional[Dict]) -> str:
        """재실행 시 Validator 피드백 포맷팅"""
        if not feedback:
            return ""

        # 현재 노드에 대한 피드백 추출
        node_guidance = feedback.get("node_specific_guidance", {}).get("node_2b_impact_analysis", {})

        if not node_guidance:
            return ""

        issues = node_guidance.get("issues", [])
        suggestions = node_guidance.get("retry_guidance", "")

        feedback_text = "\n<VALIDATION_FEEDBACK>\n"
        feedback_text += "⚠️ Previous attempt had issues. Please address the following:\n\n"

        if issues:
            feedback_text += "Issues Found:\n"
            for i, issue in enumerate(issues, 1):
                feedback_text += f"{i}. {issue}\n"
            feedback_text += "\n"

        if suggestions:
            feedback_text += f"Retry Guidance:\n{suggestions}\n"

        feedback_text += "</VALIDATION_FEEDBACK>\n"

        return feedback_text

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
        P1~P9 영향 분석 TextBlock 생성

        Args:
            impact_analyses: 영향 분석 결과
            report_template: Node 1 템플릿

        Returns:
            List[Dict]: TextBlock (전체 리스크 수만큼)
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
