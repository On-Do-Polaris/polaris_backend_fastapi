"""
파일명: node_2a_scenario_analysis_v2.py
최종 수정일: 2025-12-15
버전: v2.0

개요:
    Node 2-A: Scenario Analysis (시나리오 분석)

    8개 사업장의 물리적 리스크 AAL 데이터를 기반으로
    4가지 SSP 기후 시나리오별 포트폴리오 AAL 추이를 분석하고
    TableBlock JSON 형식으로 출력합니다.

주요 기능:
    1. 사업장별 시나리오 AAL 추출 (병렬 처리)
    2. 포트폴리오 레벨 집계 (8개 사업장 통합)
    3. Node 1 템플릿 참조하여 LLM 분석 품질 향상
    4. 4가지 SSP 시나리오 비교 분석 (EXHAUSTIVE 모드)
    5. TableBlock JSON 생성 (schemas.py 준수)
    6. TextBlock 생성 (시나리오 분석 결과 텍스트)

입력:
    - sites_data: List[dict] (8개 사업장 리스크 데이터)
    - report_template: dict (Node 1 출력)
    - agent_guideline: Optional[dict] (Excel 기반 가이드라인)

출력:
    - scenarios: Dict (4가지 SSP 시나리오별 AAL 추이)
    - scenario_table: TableBlock (시나리오 비교표 JSON)
    - scenario_text_block: TextBlock (시나리오 분석 텍스트)
    - comparison_analysis: str (LLM 기반 비교 분석)

설계 철학 (Node 1과 동일):
    "처음부터 완벽하게 분석하면 재분석은 필요 없다"
    - INIT 모드에서 최대한 EXHAUSTIVE하게 분석
    - Node 1 템플릿의 scenario_templates 패턴 적극 활용
    - Validation 통과를 목표로 설계

작성일: 2025-12-15 (v2 Refactoring)
"""

import asyncio
import json
from typing import Dict, Any, List, Optional
from .schemas import TableBlock, TableData, TableRow, TextBlock


class ScenarioAnalysisNode:
    """
    Node 2-A: 시나리오 분석 노드 v2

    역할:
        - 8개 사업장의 시나리오별 AAL 데이터를 포트폴리오 레벨로 통합
        - 4가지 SSP 시나리오(1-2.6, 2-4.5, 3-7.0, 5-8.5) 비교 분석
        - Node 1 템플릿을 참조하여 보고서 스타일에 맞는 분석 수행

    주의:
        - Node 1의 report_template_profile을 반드시 입력으로 받아야 함
        - TableBlock은 schemas.py의 Pydantic 검증을 통과해야 함
    """

    def __init__(self, llm_client):
        """
        Node 초기화

        Args:
            llm_client: ainvoke 메서드를 지원하는 LLM 클라이언트
        """
        self.llm = llm_client

        # SSP 시나리오 메타데이터
        self.scenario_metadata = {
            "ssp1_2.6": {
                "name_kr": "지속가능 발전",
                "name_en": "Sustainability",
                "temp_rise": "1.5°C",
                "description": "친환경 정책과 국제 협력으로 온실가스 감축 성공"
            },
            "ssp2_4.5": {
                "name_kr": "중간 경로",
                "name_en": "Middle of the Road",
                "temp_rise": "2.0-2.5°C",
                "description": "현재 추세 유지, 점진적 기후 대응"
            },
            "ssp3_7.0": {
                "name_kr": "지역 경쟁",
                "name_en": "Regional Rivalry",
                "temp_rise": "3.0-3.5°C",
                "description": "국가 간 경쟁 심화, 기후 대응 미흡"
            },
            "ssp5_8.5": {
                "name_kr": "화석연료 집약",
                "name_en": "Fossil-fueled Development",
                "temp_rise": "4.0°C+",
                "description": "화석연료 의존 지속, 최악의 기후변화 시나리오"
            }
        }

    async def execute(
        self,
        sites_data: List[Dict],
        report_template: Dict[str, Any],
        agent_guideline: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        메인 실행 함수

        Args:
            sites_data: 8개 사업장 리스크 데이터
            report_template: Node 1에서 생성한 보고서 템플릿
            agent_guideline: Excel 기반 작성 가이드라인 (optional)

        Returns:
            Dict containing:
                - scenarios: 4가지 시나리오별 AAL 추이
                - scenario_table: TableBlock JSON
                - scenario_text_block: TextBlock JSON
                - comparison_analysis: 시나리오 비교 분석 텍스트
        """
        print("\n" + "="*80)
        print("🔄 Node 2-A: Scenario Analysis v2 실행 시작")
        print("="*80)

        # Step 1: 사업장별 시나리오 AAL 추출 (병렬)
        print("\n[1/5] 사업장별 시나리오 AAL 추출 중...")
        site_scenario_results = await self._calculate_scenarios_parallel(sites_data)
        print(f"✅ {len(site_scenario_results)}개 사업장 처리 완료")

        # Step 2: 포트폴리오 통합 분석
        print("\n[2/5] 포트폴리오 레벨 집계 중...")
        scenarios = self._aggregate_scenarios(site_scenario_results)
        print(f"✅ 4가지 시나리오 집계 완료")

        # Step 3: LLM 기반 시나리오 비교 분석 (EXHAUSTIVE)
        print("\n[3/5] LLM 기반 시나리오 비교 분석 중...")
        comparison_analysis = await self._analyze_scenarios_with_llm(
            scenarios,
            report_template,
            agent_guideline
        )
        print(f"✅ 비교 분석 완료 ({len(comparison_analysis)} 글자)")

        # Step 4: TableBlock 생성
        print("\n[4/5] TableBlock JSON 생성 중...")
        scenario_table = self._create_scenario_table(scenarios)
        print(f"✅ TableBlock 생성 완료")

        # Step 5: TextBlock 생성
        print("\n[5/5] TextBlock 생성 중...")
        scenario_text_block = self._create_scenario_text_block(
            scenarios,
            comparison_analysis,
            report_template
        )
        print(f"✅ TextBlock 생성 완료")

        print("\n" + "="*80)
        print("✅ Node 2-A 실행 완료!")
        print("="*80)

        return {
            "scenarios": scenarios,
            "scenario_table": scenario_table,
            "scenario_text_block": scenario_text_block,
            "comparison_analysis": comparison_analysis
        }

    async def _calculate_scenarios_parallel(self, sites_data: List[Dict]) -> List[Dict]:
        """
        8개 사업장 시나리오 AAL 병렬 계산 (~10초)

        Args:
            sites_data: 사업장 리스트

        Returns:
            List[Dict]: 사업장별 시나리오 AAL 결과
        """
        tasks = [self._calculate_site_scenario_aal(site) for site in sites_data]
        results = await asyncio.gather(*tasks)
        return results

    async def _calculate_site_scenario_aal(self, site: Dict) -> Dict:
        """
        단일 사업장의 시나리오별 AAL 계산

        Args:
            site: 사업장 데이터 (risk_results 포함)

        Returns:
            Dict: {
                "site_id": str,
                "site_name": str,
                "ssp1_2.6": {"timeline": [...], "aal_values": [...]},
                "ssp2_4.5": {...},
                "ssp3_7.0": {...},
                "ssp5_8.5": {...}
            }
        """
        site_id = site.get("site_id", "unknown")
        site_name = site.get("site_name", "Unknown Site")
        risk_results = site.get("risk_results", [])

        # 시나리오별 AAL 추출
        scenario_data = {}

        for scenario_key in ["ssp1_2.6", "ssp2_4.5", "ssp3_7.0", "ssp5_8.5"]:
            # 타임라인 기본값 (2025, 2030, 2040, 2050, 2100)
            timeline = [2025, 2030, 2040, 2050, 2100]
            aal_values = []

            # risk_results에서 시나리오별 AAL 추출
            for year in timeline:
                # 해당 연도의 AAL 값 찾기
                year_aal = 0.0

                for risk in risk_results:
                    # risk 데이터 구조에 따라 조정 필요
                    # 예시: risk["scenarios"][scenario_key][year]
                    scenarios = risk.get("scenarios", {})
                    scenario_aal = scenarios.get(scenario_key, {})

                    if isinstance(scenario_aal, dict):
                        year_aal += scenario_aal.get(str(year), 0.0)
                    elif isinstance(scenario_aal, (int, float)):
                        year_aal += scenario_aal

                aal_values.append(round(year_aal, 2))

            scenario_data[scenario_key] = {
                "timeline": timeline,
                "aal_values": aal_values
            }

        return {
            "site_id": site_id,
            "site_name": site_name,
            **scenario_data
        }

    def _aggregate_scenarios(self, site_results: List[Dict]) -> Dict:
        """
        포트폴리오 시나리오 집계

        8개 사업장의 AAL을 포트폴리오 레벨로 통합
        방법: 각 시나리오별 연도별 AAL의 평균 계산

        Args:
            site_results: 사업장별 시나리오 AAL 결과

        Returns:
            Dict: {
                "ssp1_2.6": {
                    "timeline": [2024, 2030, 2040, 2050, 2100],
                    "aal_values": [52.9, 51.2, 49.5, 47.3, 45.0],
                    "summary": "...",
                    "key_points": [...]
                },
                ...
            }
        """
        portfolio_scenarios = {}

        for scenario_key in ["ssp1_2.6", "ssp2_4.5", "ssp3_7.0", "ssp5_8.5"]:
            timeline = [2025, 2030, 2040, 2050, 2100]
            portfolio_aal = [0.0] * len(timeline)

            # 각 사업장의 AAL을 합산
            for site in site_results:
                scenario_data = site.get(scenario_key, {})
                site_aal_values = scenario_data.get("aal_values", [0.0] * len(timeline))

                for i, aal in enumerate(site_aal_values):
                    if i < len(portfolio_aal):
                        portfolio_aal[i] += aal

            # 평균 계산 (8개 사업장)
            num_sites = len(site_results) if site_results else 1
            portfolio_aal = [round(aal / num_sites, 2) for aal in portfolio_aal]

            # 메타데이터 추가
            metadata = self.scenario_metadata.get(scenario_key, {})

            # 증감율 계산
            if portfolio_aal[0] > 0:
                change_rate = ((portfolio_aal[-1] - portfolio_aal[0]) / portfolio_aal[0]) * 100
            else:
                change_rate = 0.0

            portfolio_scenarios[scenario_key] = {
                "timeline": timeline,
                "aal_values": portfolio_aal,
                "scenario_name_kr": metadata.get("name_kr", ""),
                "scenario_name_en": metadata.get("name_en", ""),
                "temp_rise": metadata.get("temp_rise", ""),
                "description": metadata.get("description", ""),
                "change_rate": round(change_rate, 1),
                "summary": "",  # LLM에서 채움
                "key_points": []  # LLM에서 채움
            }

        return portfolio_scenarios

    async def _analyze_scenarios_with_llm(
        self,
        scenarios: Dict,
        report_template: Dict,
        agent_guideline: Optional[Dict]
    ) -> str:
        """
        LLM 기반 시나리오 비교 분석 (EXHAUSTIVE 모드)

        Node 1 철학 적용: "처음부터 완벽하게 분석"

        Args:
            scenarios: 포트폴리오 시나리오 데이터
            report_template: Node 1 템플릿
            agent_guideline: 작성 가이드라인

        Returns:
            str: 시나리오 비교 분석 텍스트 (Markdown)
        """
        # Node 1 템플릿에서 참조할 정보 추출
        scenario_templates = report_template.get("scenario_templates", {})
        tone = report_template.get("tone", {})
        formatting_rules = report_template.get("formatting_rules", {})
        reusable_paragraphs = report_template.get("reusable_paragraphs", [])

        # 시나리오 데이터 포맷팅
        scenario_summary = self._format_scenarios_for_prompt(scenarios)

        # EXHAUSTIVE 프롬프트 작성
        prompt = f"""
<ROLE>
You are an ELITE climate scenario analyst specializing in TCFD disclosures.
Your task is to analyze 4 SSP climate scenarios and provide COMPREHENSIVE insights
for institutional investors and stakeholders.
</ROLE>

<CRITICAL_ANALYSIS_REQUIREMENTS>

1. SCENARIO DIFFERENTIATION (최우선)
   - Clearly distinguish between 4 scenarios (SSP1-2.6, SSP2-4.5, SSP3-7.0, SSP5-8.5)
   - Explain the unique characteristics and implications of each scenario
   - Highlight the divergence points in AAL trajectories
   - Quantify the difference in financial impact between best and worst case

2. TIMELINE ANALYSIS (2024 → 2100)
   - Break down AAL trends into 3 phases:
     * Short-term (2024-2030): Immediate risks
     * Mid-term (2030-2050): Transition period
     * Long-term (2050-2100): Terminal impact
   - Identify inflection points where AAL accelerates or decelerates
   - Explain WHY the portfolio AAL changes over time

3. RISK INTERPRETATION
   - Translate AAL percentages into business impact:
     * What does AAL mean for asset values?
     * What operational disruptions are expected?
     * What is the financial exposure range?
   - Compare portfolio AAL to industry benchmarks (if available)
   - Assess whether the risk level is acceptable or requires action

4. STRATEGIC IMPLICATIONS
   - For each scenario, recommend:
     * Priority actions (what to do first)
     * Investment needs (adaptation budget)
     * Timeline for implementation
   - Identify "no-regret" strategies that work across all scenarios
   - Highlight scenario-specific strategies (e.g., for SSP5-8.5 only)

5. STAKEHOLDER COMMUNICATION
   - Use clear, data-driven language (avoid jargon)
   - Support claims with specific numbers from the scenarios
   - Frame risks in terms of opportunities (where applicable)
   - Address investor concerns: "Is this company climate-resilient?"

</CRITICAL_ANALYSIS_REQUIREMENTS>

<INPUT_DATA>

**Portfolio Scenario Analysis Results:**

{scenario_summary}

**Reference Template (from previous reports):**

Tone: {json.dumps(tone, ensure_ascii=False, indent=2)}

Scenario Templates: {json.dumps(scenario_templates, ensure_ascii=False, indent=2)}

Formatting Rules: {json.dumps(formatting_rules, ensure_ascii=False, indent=2)}

Sample Paragraphs:
{self._format_sample_paragraphs(reusable_paragraphs[:5])}

{self._format_guideline(agent_guideline)}

</INPUT_DATA>

<OUTPUT_REQUIREMENTS>

Generate a comprehensive scenario analysis in Korean (or English if specified) with:

1. Executive Summary (2-3 sentences)
   - Overall portfolio AAL trend across scenarios
   - Key finding: which scenario poses the greatest risk?

2. Scenario-by-Scenario Analysis (4 subsections)
   For each SSP scenario:
   - AAL trajectory summary (start → end values)
   - Key inflection points
   - Business implications
   - Recommended response

3. Comparative Analysis
   - Table or bullet list comparing all 4 scenarios
   - Sensitivity analysis: how much does the scenario choice matter?
   - Risk range: best case vs worst case AAL delta

4. Strategic Recommendations
   - Top 3 priorities for climate adaptation
   - Investment roadmap (short/mid/long term)
   - Monitoring plan: when to reassess scenarios

5. Stakeholder Messaging
   - 1-2 sentences suitable for investor communications
   - Address the question: "Is our portfolio resilient?"

Formatting:
- Use Markdown headings (##, ###)
- Include bullet points for lists
- **Bold** key metrics (AAL values, percentages)
- Cite specific numbers from the scenario data

Length: 800-1200 words (comprehensive but concise)

</OUTPUT_REQUIREMENTS>

<QUALITY_CHECKLIST>
Before submitting, verify:
- [ ] All 4 scenarios are discussed with equal depth
- [ ] AAL values are cited accurately from input data
- [ ] Analysis explains WHY trends occur (not just WHAT happens)
- [ ] Recommendations are specific and actionable
- [ ] Tone matches the reference template style
- [ ] Output is ready for direct inclusion in TCFD Strategy section
</QUALITY_CHECKLIST>

Now, generate the scenario analysis:
"""

        # LLM 호출
        try:
            response = await self.llm.ainvoke(prompt)

            # JSON 응답인 경우 파싱
            if response.strip().startswith("{"):
                parsed = json.loads(response)
                return parsed.get("analysis", response)

            return response

        except Exception as e:
            print(f"⚠️  LLM 분석 실패: {e}")
            # Fallback: 기본 분석 반환
            return self._generate_fallback_analysis(scenarios)

    def _format_scenarios_for_prompt(self, scenarios: Dict) -> str:
        """시나리오 데이터를 프롬프트용으로 포맷팅"""
        lines = []

        for scenario_key, data in scenarios.items():
            name_kr = data.get("scenario_name_kr", "")
            name_en = data.get("scenario_name_en", "")
            temp_rise = data.get("temp_rise", "")
            timeline = data.get("timeline", [])
            aal_values = data.get("aal_values", [])
            change_rate = data.get("change_rate", 0.0)

            lines.append(f"**{scenario_key.upper()} ({name_kr} / {name_en})**")
            lines.append(f"  - Temperature Rise: {temp_rise}")
            lines.append(f"  - AAL Timeline:")

            for year, aal in zip(timeline, aal_values):
                lines.append(f"    * {year}: {aal}%")

            lines.append(f"  - Change Rate (2024→2100): {change_rate:+.1f}%")
            lines.append("")

        return "\n".join(lines)

    def _format_sample_paragraphs(self, paragraphs: List[str]) -> str:
        """샘플 문단 포맷팅"""
        if not paragraphs:
            return "N/A"

        formatted = []
        for i, para in enumerate(paragraphs[:5], 1):
            formatted.append(f"{i}. {para}")

        return "\n".join(formatted)

    def _format_guideline(self, guideline: Optional[Dict]) -> str:
        """가이드라인 포맷팅"""
        if not guideline:
            return ""

        return f"""
Agent Guideline (Excel):
{json.dumps(guideline, ensure_ascii=False, indent=2)}
"""

    def _generate_fallback_analysis(self, scenarios: Dict) -> str:
        """LLM 실패 시 기본 분석 생성"""
        lines = ["## 시나리오 분석 결과\n"]

        for scenario_key, data in scenarios.items():
            name_kr = data.get("scenario_name_kr", "")
            aal_start = data.get("aal_values", [0])[0]
            aal_end = data.get("aal_values", [0])[-1]
            change_rate = data.get("change_rate", 0.0)

            lines.append(f"### {scenario_key.upper()} ({name_kr})")
            lines.append(f"- 2024년 AAL: {aal_start}%")
            lines.append(f"- 2100년 AAL: {aal_end}%")
            lines.append(f"- 증감율: {change_rate:+.1f}%\n")

        return "\n".join(lines)

    def _create_scenario_table(self, scenarios: Dict) -> Dict:
        """
        시나리오별 AAL 비교 TableBlock 생성

        schemas.py의 TableBlock 형식을 정확히 준수

        Args:
            scenarios: 포트폴리오 시나리오 데이터

        Returns:
            Dict: TableBlock JSON (Pydantic 검증 통과)
        """
        # 테이블 헤더
        headers = ["시나리오", "2025", "2030", "2040", "2050", "2100", "증감율"]

        # 시나리오 순서
        scenario_order = ["ssp1_2.6", "ssp2_4.5", "ssp3_7.0", "ssp5_8.5"]

        # 테이블 행 생성
        rows = []

        for scenario_key in scenario_order:
            scenario_data = scenarios.get(scenario_key, {})

            # 시나리오 이름
            name_kr = scenario_data.get("scenario_name_kr", scenario_key)
            temp_rise = scenario_data.get("temp_rise", "")
            scenario_label = f"{scenario_key.upper()}\n({name_kr}, {temp_rise})"

            # AAL 값들
            aal_values = scenario_data.get("aal_values", [0, 0, 0, 0, 0])

            # 증감율
            change_rate = scenario_data.get("change_rate", 0.0)
            change_str = f"{change_rate:+.1f}%"

            # 행 셀 구성
            row_cells = [scenario_label]

            for aal in aal_values:
                row_cells.append(f"{aal}%")

            row_cells.append(change_str)

            # TableRow 형식으로 추가
            rows.append({"cells": row_cells})

        # TableBlock 생성 (schemas.py 구조 준수)
        table_block = {
            "type": "table",
            "title": "시나리오별 포트폴리오 AAL 추이 비교",
            "data": {
                "headers": headers,
                "rows": rows
            }
        }

        return table_block

    def _create_scenario_text_block(
        self,
        scenarios: Dict,
        comparison_analysis: str,
        report_template: Dict
    ) -> Dict:
        """
        시나리오 분석 결과 TextBlock 생성

        Args:
            scenarios: 시나리오 데이터
            comparison_analysis: LLM 비교 분석 결과
            report_template: Node 1 템플릿

        Returns:
            Dict: TextBlock JSON
        """
        # 템플릿에서 재사용 가능한 문단 참조
        reusable_paragraphs = report_template.get("reusable_paragraphs", [])

        # TextBlock 내용 구성
        content_parts = []

        # 도입부 (템플릿 참조)
        intro = next(
            (p for p in reusable_paragraphs if "시나리오" in p or "TCFD" in p),
            "우리는 TCFD 권고안에 따라 4가지 기후 시나리오를 분석했습니다."
        )
        content_parts.append(intro)
        content_parts.append("")

        # LLM 분석 결과
        content_parts.append(comparison_analysis)
        content_parts.append("")

        # 요약 (시나리오별 핵심 수치)
        content_parts.append("## 주요 수치 요약")
        content_parts.append("")

        for scenario_key, data in scenarios.items():
            name_kr = data.get("scenario_name_kr", "")
            aal_start = data.get("aal_values", [0])[0]
            aal_end = data.get("aal_values", [0])[-1]
            change_rate = data.get("change_rate", 0.0)

            content_parts.append(
                f"- **{scenario_key.upper()} ({name_kr})**: "
                f"2025년 {aal_start}% → 2100년 {aal_end}% ({change_rate:+.1f}%)"
            )

        content = "\n".join(content_parts)

        # TextBlock 생성
        text_block = {
            "type": "text",
            "subheading": "2.1 시나리오 분석 결과",
            "content": content
        }

        return text_block


# ============================================================
# Utility Functions
# ============================================================

def validate_table_block(table_block: Dict) -> bool:
    """
    TableBlock이 schemas.py 구조를 준수하는지 검증

    Args:
        table_block: 검증할 TableBlock JSON

    Returns:
        bool: 유효하면 True
    """
    try:
        # Pydantic 검증
        TableBlock(**table_block)
        return True
    except Exception as e:
        print(f"❌ TableBlock 검증 실패: {e}")
        return False


def validate_text_block(text_block: Dict) -> bool:
    """
    TextBlock이 schemas.py 구조를 준수하는지 검증

    Args:
        text_block: 검증할 TextBlock JSON

    Returns:
        bool: 유효하면 True
    """
    try:
        # Pydantic 검증
        TextBlock(**text_block)
        return True
    except Exception as e:
        print(f"❌ TextBlock 검증 실패: {e}")
        return False
