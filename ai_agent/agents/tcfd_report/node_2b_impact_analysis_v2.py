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
        sites_metadata: Optional[List[Dict]] = None
    ) -> Dict[str, Any]:
        """
        메인 실행 함수

        Args:
            sites_data: 8개 사업장 리스크 데이터
            scenario_analysis: Node 2-A 시나리오 분석 결과
            report_template: Node 1 보고서 템플릿
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

        # Step 1: Top 5 리스크 식별
        print("\n[1/4] Top 5 리스크 식별 중...")
        top_5_risks = self._identify_top_risks(sites_data)
        print(f"✅ Top 5 리스크 식별 완료:")
        for i, risk in enumerate(top_5_risks, 1):
            risk_name = self.risk_name_mapping.get(risk["risk_type"], risk["risk_type"])
            print(f"   P{i}. {risk_name}: AAL {risk['total_aal']:.2f}%")

        # Step 2: 사업장별 리스크 상세 데이터 추출
        print("\n[2/4] 사업장별 리스크 데이터 추출 중...")
        top_5_detailed = self._extract_risk_details(top_5_risks, sites_data, sites_metadata)
        print(f"✅ 상세 데이터 추출 완료")

        # Step 3: LLM 기반 영향 분석 (병렬)
        print("\n[3/4] LLM 기반 영향 분석 중 (병렬 처리)...")
        impact_analyses = await self._analyze_impacts_parallel(
            top_5_detailed,
            scenario_analysis,
            report_template
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
        sites_metadata: Optional[List[Dict]]
    ) -> List[Dict]:
        """
        Top 5 리스크의 사업장별 상세 데이터 추출

        Args:
            top_5_risks: Top 5 리스크 정보
            sites_data: 사업장 데이터
            sites_metadata: 사업장 메타데이터

        Returns:
            List[Dict]: Top 5 리스크별 상세 정보
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
                            affected_sites.append({
                                "site_id": site_id,
                                "site_name": site_name,
                                "aal": round(aal, 2),
                                "risk_details": risk_result
                            })

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
        report_template: Dict
    ) -> List[Dict]:
        """
        Top 5 리스크 병렬 영향 분석 (~30초)

        Args:
            top_5_detailed: Top 5 리스크 상세 정보
            scenario_analysis: Node 2-A 시나리오 분석 결과
            report_template: Node 1 템플릿

        Returns:
            List[Dict]: 5개 리스크별 영향 분석 결과
        """
        tasks = [
            self._analyze_single_risk_impact(risk, scenario_analysis, report_template)
            for risk in top_5_detailed
        ]
        impact_analyses = await asyncio.gather(*tasks)
        return impact_analyses

    async def _analyze_single_risk_impact(
        self,
        risk: Dict,
        scenario_analysis: Dict,
        report_template: Dict
    ) -> Dict:
        """
        단일 리스크 영향 분석 (EXHAUSTIVE 프롬프트)

        Args:
            risk: 리스크 상세 정보
            scenario_analysis: 시나리오 분석 결과
            report_template: Node 1 템플릿

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

        # 사업장 정보 포맷팅
        sites_info = self._format_affected_sites(affected_sites)

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

2. OPERATIONAL IMPACT (운영적 영향)
   - Identify critical operations at risk
   - Estimate potential downtime (hours/days)
   - Assess supply chain disruptions
   - Evaluate impact on service delivery
   - Consider cascading effects on other sites

3. ASSET IMPACT (자산 영향)
   - Assess physical damage to buildings and equipment
   - Identify vulnerable infrastructure (power, cooling, IT)
   - Evaluate long-term asset degradation
   - Consider replacement vs. retrofit costs
   - Assess impact on asset lifespan

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

Affected Sites:
{sites_info}

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
- 2-3 paragraphs

2. 운영적 영향 (Operational Impact)
- Critical operations at risk
- Estimated downtime or service disruption
- Supply chain and interdependency effects
- 2-3 paragraphs

3. 자산 영향 (Asset Impact)
- Physical damage assessment
- Infrastructure vulnerabilities
- Long-term asset degradation
- 2-3 paragraphs

Summary (1 paragraph)
- Overall assessment of risk severity
- Key numbers: AAL, estimated loss, affected sites
- Urgency level: immediate action needed or manageable?

Formatting:
- Use Markdown for structure
- Bold key metrics (AAL, costs, downtime)
- Use bullet points for lists
- Cite specific numbers from input data

Length: 600-900 words total (comprehensive but concise)

</OUTPUT_REQUIREMENTS>

<QUALITY_CHECKLIST>
Before submitting, verify:
- [ ] All 3 impact dimensions are analyzed with equal depth
- [ ] Financial impact includes specific KRW estimates
- [ ] Operational impact cites affected sites and operations
- [ ] Asset impact describes physical vulnerabilities
- [ ] Summary synthesizes key findings
- [ ] Tone matches the reference template style
- [ ] Output is ready for direct inclusion in TCFD Strategy section
</QUALITY_CHECKLIST>

Now, generate the impact analysis as a JSON object with keys:
"financial_impact", "operational_impact", "asset_impact", "summary"
"""

        # LLM 호출
        try:
            response = await self.llm.ainvoke(prompt)

            # JSON 파싱 시도
            if response.strip().startswith("{"):
                parsed = json.loads(response)
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

    def _format_sample_paragraphs(self, paragraphs: List[str]) -> str:
        """샘플 문단 포맷팅"""
        if not paragraphs:
            return "N/A"

        formatted = []
        for i, para in enumerate(paragraphs[:3], 1):
            formatted.append(f"{i}. {para}")

        return "\n".join(formatted)

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
            "operational_impact": f"{risk["num_affected_sites"]}개 사업장의 운영에 영향을 미칠 것으로 예상됩니다.",
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

            # 요약
            if impact.get("summary"):
                content_parts.append(impact["summary"])
                content_parts.append("")

            # 재무적 영향
            content_parts.append("### 재무적 영향")
            content_parts.append(impact.get("financial_impact", "분석 중"))
            content_parts.append("")

            # 운영적 영향
            content_parts.append("### 운영적 영향")
            content_parts.append(impact.get("operational_impact", "분석 중"))
            content_parts.append("")

            # 자산 영향
            content_parts.append("### 자산 영향")
            content_parts.append(impact.get("asset_impact", "분석 중"))

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
