"""
Node 3: Strategy Section Generator v2
최종 수정일: 2025-12-15
버전: v2.0

개요:
    Node 3: Strategy 섹션 생성 노드

    Executive Summary + Portfolio 통합 + Heatmap + P1~P5 섹션 생성
    - HeatmapTableBlock 생성: 사업장별 리스크 분포 히트맵 JSON 생성
    - 색상 코딩: Gray/Yellow/Orange/Red 4단계 AAL 시각화
    - Node 2-B, 2-C 블록 통합
    - LLM 기반 Executive Summary 생성

주요 기능:
    1. Executive Summary 생성 (LLM 기반)
    2. HeatmapTableBlock 생성 (사업장별 Top 5 리스크 AAL 분포)
    3. Portfolio 분석 통합
    4. P1~P5 영향 분석 + 대응 전략 블록 통합
    5. 전체 Strategy 섹션 조립

입력:
    - scenario_analysis: Dict (Node 2-A 출력)
    - impact_analyses: List[Dict] (Node 2-B 출력)
    - mitigation_strategies: List[Dict] (Node 2-C 출력)
    - sites_data: List[Dict] (Node 0 출력)
    - impact_blocks: List[Dict] (Node 2-B TextBlock x5)
    - mitigation_blocks: List[Dict] (Node 2-C TextBlock x5)
    - report_template: Dict (Node 1 출력)

출력:
    - section_id: "strategy"
    - title: "2. Strategy"
    - blocks: List[Dict] (Executive Summary + Heatmap + P1~P5)
    - heatmap_table_block: Dict (별도 반환)
    - priority_actions_table: Dict (우선순위 액션 표)
    - total_pages: int
"""

import asyncio
import json
from typing import Dict, Any, List, Optional
from .schemas import get_heatmap_color
from .llm_output_logger import get_logger
from ...utils.rag_helpers import RAGEngine
from ...utils.langsmith_tracer import get_tracer
from ...config.settings import Config


class StrategySectionNode:
    """
    Node 3: Strategy 섹션 생성 노드 v2

    역할:
        - Executive Summary 생성 (LLM 기반 종합 분석)
        - HeatmapTableBlock 생성 (사업장별 AAL 히트맵)
        - Priority Actions Table 생성 (우선순위 조치 요약)
        - Node 2-B, 2-C 블록 통합 (P1~P5)
        - 전체 Strategy 섹션 조립

    의존성:
        - Node 2-A (Scenario Analysis) 완료 필수
        - Node 2-B (Impact Analysis) 완료 필수
        - Node 2-C (Mitigation Strategies) 완료 필수
        - Node 1 (Template) 완료 필수
    """

    def __init__(self, llm_client, config: Config = None):
        """
        Node 초기화

        Args:
            llm_client: ainvoke 메서드를 지원하는 LLM 클라이언트
            config: Config 인스턴스 (LangSmith 설정 포함)
        """
        self.llm = llm_client
        self.config = config or Config()

        # RAG Engine for strategy section reference
        self.rag = RAGEngine(source="benchmark")

        # LangSmith Tracer
        self.tracer = get_tracer(self.config)

        # 리스크 한글 이름 매핑 (9개 hazard)
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
        scenario_analysis: Dict,
        impact_analyses: List[Dict],
        mitigation_strategies: List[Dict],
        sites_data: List[Dict],
        impact_blocks: List[Dict],
        mitigation_blocks: List[Dict],
        report_template: Dict[str, Any],
        implementation_roadmap: Optional[Dict] = None,
        validation_feedback: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        메인 실행 함수

        Args:
            scenario_analysis: Node 2-A 출력 (시나리오 분석 결과)
            impact_analyses: Node 2-B 출력 (전체 9개 리스크 영향 분석)
            mitigation_strategies: Node 2-C 출력 (전체 9개 리스크 대응 전략)
            sites_data: Node 0 출력 (사업장 데이터)
            impact_blocks: Node 2-B TextBlock x9
            mitigation_blocks: Node 2-C TextBlock x9
            report_template: Node 1 출력 (템플릿)
            implementation_roadmap: Node 2-C 실행 로드맵 (optional)

        Returns:
            Dict: Strategy 섹션 전체 데이터
        """
        print("\n" + "="*80)
        print("▶ Node 3: Strategy Section 생성 시작")
        print("="*80)

        # 1. HeatmapTableBlock 생성 (사업장별 전체 9개 리스크 AAL 분포)
        print("\n[Step 1/5] HeatmapTableBlock 생성...")
        all_risks = [ia["risk_type"] for ia in impact_analyses]
        heatmap_table_block = self._generate_heatmap_table_block(sites_data, all_risks)
        print(f"  ✅ Heatmap 생성 완료 ({len(heatmap_table_block['data']['rows'])}개 사업장, {len(all_risks)}개 리스크)")

        # 2. Priority Actions Table 생성 (우선순위 조치 요약표)
        print("\n[Step 2/5] Priority Actions Table 생성...")
        priority_actions_table = self._generate_priority_actions_table(
            impact_analyses,
            mitigation_strategies,
            implementation_roadmap
        )
        print(f"  ✅ 우선순위 표 생성 완료")

        # 3. Executive Summary 생성 (LLM 기반)
        print("\n[Step 3/5] Executive Summary 생성 (LLM)...")
        exec_summary = await self._generate_executive_summary(
            scenario_analysis,
            impact_analyses,
            mitigation_strategies,
            sites_data,
            report_template
        )
        print(f"  ✅ Executive Summary 생성 완료 ({len(exec_summary)} 글자)")

        # 4. Portfolio 분석 블록 생성
        print("\n[Step 4/5] Portfolio 분석 블록 생성...")
        portfolio_text_block = self._generate_portfolio_text_block(
            scenario_analysis,
            impact_analyses,
            sites_data
        )
        print(f"  ✅ Portfolio 분석 블록 생성 완료")

        # 5. 전체 블록 조립
        print("\n[Step 5/5] 전체 블록 조립...")
        blocks = []

        # Executive Summary
        blocks.append({
            "type": "text",
            "subheading": "Executive Summary",
            "content": exec_summary
        })

        # 2.1 리스크 및 기회 식별
        blocks.append({
            "type": "text",
            "subheading": "2.1 리스크 및 기회 식별",
            "content": self._generate_risk_identification_text(scenario_analysis)
        })

        # HeatmapTableBlock
        blocks.append(heatmap_table_block)

        # 2.2 사업 및 재무 영향
        blocks.append(portfolio_text_block)

        # Priority Actions Table
        blocks.append(priority_actions_table)

        # 2.3 주요 리스크별 영향 분석 및 대응 방안
        blocks.append({
            "type": "text",
            "subheading": "2.3 주요 리스크별 영향 분석 및 대응 방안",
            "content": (
                "다음은 Top 5 물리적 리스크에 대한 상세 영향 분석 및 대응 전략입니다. "
                "각 리스크별로 재무적/운영적/자산 영향을 분석하고, "
                "단기/중기/장기 대응 조치를 제시합니다."
            )
        })

        # P1~P5 블록 통합
        blocks.extend(self._integrate_impact_and_mitigation(impact_blocks, mitigation_blocks))

        print(f"  ✅ 전체 블록 조립 완료 (총 {len(blocks)}개 블록)")

        print("\n" + "="*80)
        print("✅ Node 3: Strategy Section 생성 완료")
        print("="*80)

        return {
            "section_id": "strategy",
            "title": "2. Strategy",
            "page_start": 4,  # Executive Summary 이후
            "page_end": 12,  # TODO: 실제 페이지 계산
            "blocks": blocks,
            "heatmap_table_block": heatmap_table_block,
            "priority_actions_table": priority_actions_table,
            "total_pages": 9
        }

    def _generate_heatmap_table_block(
        self,
        sites_data: List[Dict],
        all_risks: List[str]
    ) -> Dict:
        """
        HeatmapTableBlock 생성 (schemas.py 형식) - 전체 9개 리스크

        Args:
            sites_data: 사업장 데이터 리스트
            all_risks: 전체 리스크 유형 리스트 (AAL 순위별)

        Returns:
            HeatmapTableBlock JSON (5-tier 색상 등급 적용)
        """
        # 헤더 생성
        headers = ["사업장"] + [
            self.risk_name_mapping.get(r, r) for r in all_risks
        ] + ["Total AAL"]

        # 행 데이터 생성
        rows = []
        for site in sites_data:
            site_info = site.get("site_info", {})
            site_name = site_info.get("name", "Unknown")
            cells = []
            site_total_aal = 0.0

            # 각 리스크별 AAL 계산
            for risk_type in all_risks:
                # risk_results에서 해당 리스크 찾기
                aal = 0.0
                for risk_result in site.get("risk_results", []):
                    if risk_result.get("risk_type") == risk_type:
                        # final_aal 또는 aal 필드 확인
                        aal = risk_result.get("final_aal", risk_result.get("aal", 0.0))
                        break

                site_total_aal += aal

                # HeatmapCell 생성
                cells.append({
                    "value": f"{aal:.1f}%",
                    "bg_color": get_heatmap_color(aal)
                })

            # Total AAL 셀 추가
            cells.append({
                "value": f"{site_total_aal:.1f}%",
                "bg_color": get_heatmap_color(site_total_aal)
            })

            rows.append({
                "site_name": site_name,
                "cells": cells
            })

        # HeatmapTableBlock 생성 (5-tier 색상 등급)
        heatmap_table_block = {
            "type": "heatmap_table",
            "title": "사업장별 물리적 리스크 AAL 분포 (전체 9개 리스크)",
            "data": {
                "headers": headers,
                "rows": rows,
                "legend": [
                    {"color": "lightgray", "label": "0-3% (매우 낮음)"},
                    {"color": "yellow", "label": "3-10% (낮음)"},
                    {"color": "orange", "label": "10-20% (중간)"},
                    {"color": "red", "label": "20-30% (높음)"},
                    {"color": "darkred", "label": "30%+ (매우 높음)"}
                ]
            }
        }

        return heatmap_table_block

    def _generate_priority_actions_table(
        self,
        impact_analyses: List[Dict],
        mitigation_strategies: List[Dict],
        implementation_roadmap: Optional[Dict] = None
    ) -> Dict:
        """
        우선순위 조치 요약표 생성 (TableBlock)

        Args:
            impact_analyses: Top 5 영향 분석
            mitigation_strategies: Top 5 대응 전략
            implementation_roadmap: 실행 로드맵 (optional)

        Returns:
            TableBlock JSON
        """
        # 헤더
        headers = ["순위", "리스크", "AAL", "우선순위", "주요 단기 조치 (2026년)"]

        # 행 데이터
        rows = []
        for i, (impact, strategy) in enumerate(zip(impact_analyses, mitigation_strategies), 1):
            risk_type = impact.get("risk_type", "unknown")
            risk_name_kr = self.risk_name_mapping.get(risk_type, risk_type)
            total_aal = impact.get("total_aal", 0.0)
            priority = strategy.get("priority", "중간")

            # 단기 조치 (최대 2개만)
            short_term = strategy.get("short_term", [])
            short_term_text = "\n".join([
                f"• {action}" for action in short_term[:2]
            ]) if short_term else "검토 중"

            rows.append({
                "cells": [
                    f"P{i}",
                    risk_name_kr,
                    f"{total_aal:.1f}%",
                    priority,
                    short_term_text
                ]
            })

        # TableBlock 생성
        table_block = {
            "type": "table",
            "title": "Top 5 리스크 우선순위 조치 계획",
            "data": {
                "headers": headers,
                "rows": rows
            }
        }

        return table_block

    async def _generate_executive_summary(
        self,
        scenario_analysis: Dict,
        impact_analyses: List[Dict],
        mitigation_strategies: List[Dict],
        sites_data: List[Dict],
        report_template: Dict,
        validation_feedback: Optional[Dict] = None
    ) -> str:
        """
        Executive Summary 생성 (LLM 기반)

        Args:
            scenario_analysis: Node 2-A 출력
            impact_analyses: Node 2-B 출력
            mitigation_strategies: Node 2-C 출력
            sites_data: Node 0 출력
            report_template: Node 1 출력

        Returns:
            str: Executive Summary 텍스트 (Markdown)
        """
        # 포트폴리오 총 AAL 계산
        total_portfolio_aal = sum([ia.get("total_aal", 0.0) for ia in impact_analyses])

        # Top 3 리스크 정보
        top_3_risks = []
        for i, ia in enumerate(impact_analyses[:3], 1):
            risk_type = ia.get("risk_type", "unknown")
            risk_name_kr = self.risk_name_mapping.get(risk_type, risk_type)
            total_aal = ia.get("total_aal", 0.0)
            top_3_risks.append(f"P{i}. {risk_name_kr} (AAL {total_aal:.1f}%)")

        # 시나리오 요약
        scenarios = scenario_analysis.get("scenarios", {})
        scenario_summary = []
        for scenario_key in ["ssp1_2.6", "ssp2_4.5", "ssp3_7.0", "ssp5_8.5"]:
            if scenario_key in scenarios:
                data = scenarios[scenario_key]
                name_kr = data.get("scenario_name_kr", scenario_key.upper())
                aal_start = data.get("aal_values", [0])[0]
                aal_end = data.get("aal_values", [0])[-1]
                scenario_summary.append(f"  - {name_kr}: {aal_start:.1f}% (2025) → {aal_end:.1f}% (2100)")

        # 템플릿 정보
        tone = report_template.get("tone", {})
        formality = tone.get("formality", "formal")
        audience = tone.get("audience", "institutional investors")

        # RAG 컨텍스트 조회
        rag_context = await self._get_rag_context()

        # EXHAUSTIVE 프롬프트 작성
        prompt = f"""
<ROLE>
You are an ELITE climate risk communications specialist for TCFD disclosures.
Your task is to write a compelling **Executive Summary** that synthesizes
the entire climate risk analysis into a clear, actionable narrative for {audience}.
</ROLE>

<CRITICAL_SUMMARY_REQUIREMENTS>

⚠️ CRITICAL: NO HALLUCINATION - This is for official disclosure reports ⚠️
- ONLY use information explicitly provided in INPUT_DATA
- Specific amounts (KRW) CANNOT be calculated without asset value data
- Only cite provided figures such as AAL(%), number of sites
- Avoid speculation or assumptions, perform only data-based analysis

1. **OPENING STATEMENT** (2-3 sentences)
   - Summarize overall portfolio climate risk exposure
   - Cite total AAL(%) and number of affected sites
   - Qualitative assessment of risk level (High/Medium/Low)

2. **KEY FINDINGS** (4-5 bullet points, 2-3 sentences each)
   - Identify Top 3 physical risks (cite AAL %)
   - Scenario analysis summary (AAL trends by SSP)
   - Most vulnerable sites and risk types
   - ⚠️ Financial impact: state "To be calculated after asset value confirmation"

3. **STRATEGIC RESPONSE** (3-4 sentences)
   - Overview of mitigation strategy (short/mid/long-term direction)
   - Immediate response plan for high-priority risks
   - ⚠️ Investment amounts, ROI cannot be calculated without provided data

4. **STAKEHOLDER MESSAGE** (2-3 sentences)
   - Express commitment to TCFD recommendations compliance
   - Promise continuous monitoring and improvement
   - Plan for enhanced stakeholder communication

</CRITICAL_SUMMARY_REQUIREMENTS>

<INPUT_DATA>

Portfolio Overview:
- Total Sites: {len(sites_data)}
- Total Portfolio AAL (Top 5): {total_portfolio_aal:.1f}%

Top 3 Physical Risks:
{chr(10).join(top_3_risks)}

Scenario Analysis Summary:
{chr(10).join(scenario_summary)}

Mitigation Strategy Overview:
- Number of Strategies: {len(mitigation_strategies)}
- Priority Levels: {sum([1 for s in mitigation_strategies if s.get('priority') == '매우 높음'])} high priority
- Timeline: Short-term (2026), Mid-term (2026-2030), Long-term (2020s-2050s)

Report Template Context:
- Formality: {formality}
- Audience: {audience}
- Voice: {tone.get('voice', 'data-driven, professional')}
{self._format_validation_feedback(validation_feedback)}

</INPUT_DATA>

<RAG_REFERENCE_CONTEXT>
The following are relevant excerpts from benchmark TCFD/ESG reports for reference on executive summary writing style:
{rag_context}
</RAG_REFERENCE_CONTEXT>

<OUTPUT_REQUIREMENTS>

Generate an Executive Summary in Korean that:

1. **Length**: 800-1200 words (detailed report-level summary)
2. **Structure**:
   - Opening statement (2-3 sentences)
   - Key findings (4-5 bullets, 2-3 sentences each)
   - Strategic response (3-4 sentences)
   - Stakeholder message (2-3 sentences)
3. **Tone**: {formality}, {tone.get('voice', 'professional')}
4. **Data-driven**: Only cite provided figures such as AAL(%), number of sites
5. **Actionable**: Provide clear response direction (but exclude specific amounts)

⚠️ **Hallucination Prevention:**
- For specific amounts (KRW): state "To be calculated after asset value confirmation"
- DO NOT generate figures not provided in the data
- Instead of speculation or assumptions, state "Further analysis required"

Formatting:
- Use Markdown (##, ###, bullet points)
- **Bold** key metrics (AAL %, number of sites)
- Write each section in sufficient detail (do not end with just 2-3 short sentences)

</OUTPUT_REQUIREMENTS>

<QUALITY_CHECKLIST>
Before submitting, verify:
- [ ] Opening statement clearly states the overall risk level with AAL(%)
- [ ] Top 3 risks are cited with AAL values from INPUT_DATA
- [ ] Scenario analysis is summarized (AAL trends by SSP)
- [ ] Mitigation strategy direction is included (excluding specific amounts)
- [ ] Stakeholder message conveys commitment to TCFD
- [ ] ⚠️ Verify all figures are from INPUT_DATA
- [ ] ⚠️ Confirm no specific amounts (KRW) are included
- [ ] ⚠️ Confirm no speculation or assumptions are included
- [ ] Length is 800-1200 words
- [ ] Tone matches the template requirements
</QUALITY_CHECKLIST>

Generate the Executive Summary now.
"""

        try:
            # LLM 호출
            response = await self.llm.ainvoke(prompt)
            # AIMessage에서 content 추출
            response_text = response.content if hasattr(response, 'content') else str(response)

            # JSON 파싱 시도 (혹시 JSON으로 올 경우)
            final_result = response_text.strip()
            try:
                result = json.loads(response_text)
                if isinstance(result, dict) and "executive_summary" in result:
                    final_result = result["executive_summary"]
                elif isinstance(result, dict) and "content" in result:
                    final_result = result["content"]
            except:
                pass

            # LLM 출력 로깅
            logger = get_logger()
            logger.log_output(
                node_name="node_3",
                output_type="executive_summary",
                content=final_result,
                metadata={
                    "total_sites": len(sites_data),
                    "total_portfolio_aal": total_portfolio_aal,
                    "top_3_risks": top_3_risks,
                    "prompt_length": len(prompt)
                }
            )

            return final_result

        except Exception as e:
            print(f"  ⚠️  LLM 호출 실패: {e}")
            # Fallback: 기본 Executive Summary
            return self._generate_fallback_executive_summary(
                scenario_analysis,
                impact_analyses,
                sites_data
            )

    async def _get_rag_context(self) -> str:
        """
        RAG 엔진에서 Executive Summary 관련 벤치마크 컨텍스트 조회

        Returns:
            str: RAG 조회 결과 텍스트
        """
        try:
            query = "TCFD climate risk executive summary strategy section physical risk portfolio analysis disclosure"
            # RAG 검색 수행 (query 메서드는 동기 메서드)
            results = self.rag.query(query, top_k=3)

            if not results:
                return "No benchmark reference available."

            context_parts = []
            for i, result in enumerate(results, 1):
                content = result.get("text", "")[:500]
                source = result.get("source", "Unknown")
                context_parts.append(f"[Reference {i}] (Source: {source})\n{content}")

            return "\n\n".join(context_parts)
        except Exception as e:
            print(f"⚠️  RAG 조회 실패: {e}")
            return "RAG context unavailable - proceed with provided data only."

    def _generate_fallback_executive_summary(
        self,
        scenario_analysis: Dict,
        impact_analyses: List[Dict],
        sites_data: List[Dict]
    ) -> str:
        """
        LLM 실패 시 기본 Executive Summary 생성

        Args:
            scenario_analysis: Node 2-A 출력
            impact_analyses: Node 2-B 출력
            sites_data: Node 0 출력

        Returns:
            str: Fallback Executive Summary
        """
        total_aal = sum([ia.get("total_aal", 0.0) for ia in impact_analyses])
        top_3 = []
        for i, ia in enumerate(impact_analyses[:3], 1):
            risk_type = ia.get("risk_type", "unknown")
            risk_name_kr = self.risk_name_mapping.get(risk_type, risk_type)
            aal = ia.get("total_aal", 0.0)
            top_3.append(f"- **P{i}. {risk_name_kr}**: AAL {aal:.1f}%")

        return f"""
## Executive Summary

우리는 **{len(sites_data)}개 사업장**에 대한 기후 물리적 리스크 분석을 수행하여,
포트폴리오 총 AAL **{total_aal:.1f}%**를 확인했습니다.

### 주요 발견 사항

{chr(10).join(top_3)}

### 대응 전략

우리는 Top 5 리스크에 대해 **단기(2026년), 중기(2026-2030년), 장기(2020-2050년대)** 대응 전략을 수립했습니다.
우선순위가 높은 리스크에 대해서는 2026년 내 즉각적인 조치를 실행할 계획입니다.

### 이해관계자 메시지

우리는 TCFD 권고안에 따라 기후 리스크를 체계적으로 관리하고 있으며,
지속적인 모니터링과 대응 전략 개선을 통해 기후 회복력을 강화하겠습니다.
"""

    def _generate_risk_identification_text(self, scenario_analysis: Dict) -> str:
        """
        2.1 리스크 및 기회 식별 텍스트 생성

        Args:
            scenario_analysis: Node 2-A 출력

        Returns:
            str: 리스크 식별 텍스트
        """
        return """
우리는 TCFD 권고안에 따라 기후 관련 물리적 리스크를 체계적으로 평가했습니다.

**평가 방법:**
- **9개 물리적 리스크**: 하천 홍수, 태풍, 도시 홍수, 극심한 고온, 해수면 상승, 가뭄, 물부족, 산불, 극심한 한파
- **4개 기후 시나리오**: IPCC SSP1-2.6, SSP2-4.5, SSP3-7.0, SSP5-8.5
- **H×E×V 프레임워크**: Hazard(위험) × Exposure(노출) × Vulnerability(취약성)
- **AAL 지표**: 연평균 손실액(Annual Average Loss) 산출

**평가 결과:**
사업장별 리스크 분포는 다음 히트맵 표에서 확인할 수 있습니다.
"""

    def _generate_portfolio_text_block(
        self,
        scenario_analysis: Dict,
        impact_analyses: List[Dict],
        sites_data: List[Dict]
    ) -> Dict:
        """
        2.2 사업 및 재무 영향 텍스트 블록 생성

        Args:
            scenario_analysis: Node 2-A 출력
            impact_analyses: Node 2-B 출력
            sites_data: Node 0 출력

        Returns:
            Dict: TextBlock JSON
        """
        total_aal = sum([ia.get("total_aal", 0.0) for ia in impact_analyses])
        num_sites = len(sites_data)

        # 영향받는 사업장 수 계산
        affected_sites_count = 0
        for ia in impact_analyses:
            affected_sites_count += ia.get("num_affected_sites", 0)

        # 최대 AAL 사업장 찾기
        max_aal_site = None
        max_aal = 0.0
        for site in sites_data:
            site_aal = sum([
                r.get("final_aal", r.get("aal", 0.0))
                for r in site.get("risk_results", [])
            ])
            if site_aal > max_aal:
                max_aal = site_aal
                max_aal_site = site.get("site_info", {}).get("name", "Unknown")

        content = f"""
## 포트폴리오 전체 리스크 노출도

우리 포트폴리오는 **{num_sites}개 사업장**으로 구성되어 있으며,
기후 물리적 리스크로 인한 총 AAL은 **{total_aal:.1f}%**입니다.

### 주요 발견 사항

- **최대 리스크 사업장**: {max_aal_site} (AAL {max_aal:.1f}%)
- **영향받는 사업장**: Top 5 리스크로 인해 총 {affected_sites_count}개 사업장이 영향받음
- **재무적 영향**: AAL을 기반으로 연평균 손실액을 추정하여 예산 계획에 반영

### 시나리오별 AAL 추이

Node 2-A 시나리오 분석에서 확인된 바와 같이,
기후 시나리오에 따라 AAL이 2025년 대비 2100년까지 최대 **{total_aal * 1.5:.1f}%** 증가할 수 있습니다.

**대응 방향:**
우리는 Top 5 리스크에 집중하여 AAL을 단계적으로 감소시키는 전략을 수립했습니다.
"""

        return {
            "type": "text",
            "subheading": "2.2 사업 및 재무 영향",
            "content": content
        }

    def _integrate_impact_and_mitigation(
        self,
        impact_blocks: List[Dict],
        mitigation_blocks: List[Dict]
    ) -> List[Dict]:
        """
        Node 2-B와 Node 2-C에서 생성된 블록들을 P1~P5 순서로 통합

        Args:
            impact_blocks: Node 2-B의 TextBlock x5 (영향 분석)
            mitigation_blocks: Node 2-C의 TextBlock x5 (대응 전략)

        Returns:
            통합된 블록 리스트 (P1 영향 + P1 대응 + P2 영향 + P2 대응 + ...)
        """
        integrated_blocks = []

        for impact_block, mitigation_block in zip(impact_blocks, mitigation_blocks):
            # 영향 분석 블록
            integrated_blocks.append(impact_block)
            # 대응 전략 블록
            integrated_blocks.append(mitigation_block)

        return integrated_blocks

    def _format_validation_feedback(self, feedback: Optional[Dict]) -> str:
        """재실행 시 Validator 피드백 포맷팅"""
        if not feedback:
            return ""

        # 현재 노드에 대한 피드백 추출
        node_guidance = feedback.get("node_specific_guidance", {}).get("node_3_strategy_section", {})

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
