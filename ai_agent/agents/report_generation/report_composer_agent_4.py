# report_composer_agent_4.py
"""
파일명: report_composer_agent_4.py
최종 수정일: 2025-12-01
버전: v05

파일 개요:
    - 보고서 초안 작성 Agent (템플릿 + 분석 결과 + 전략 결합)
    - LangGraph Composer Node용
    - LLM 기반 Markdown + JSON 구조 생성
    - RAG 기반 citations 포함
    - Memory Node: draft_report + citations 저장
    - Refiner 루프 연계 가능

주요 기능:
    1. Executive Summary 생성 (상위 3개 리스크 + 종합 전략 요약)
    2. Template 기반 섹션 문단 생성
    3. Markdown/JSON Draft 구성
    4. citations 수집 및 포맷
    5. Refiner 루프용 draft 상태 제공 (Text Issue 발생 시 LLM 재호출 가능)

Refiner 루프 연계:
    - Text Issue 발생 시 route: composer
    - 기존 draft + citations 기반으로 LLM 재호출
    - Draft + citations 재생성 및 Memory Node 갱신

변경 이력:
    - v01 (2025-11-14): 초안 작성, Super-Agent 구조
    - v02 (2025-11-21): async, JSON 스키마, 상태/예외 처리 추가
    - v03 (2025-11-24): 최신 LangGraph 아키텍처 반영, Memory Node/Refiner 루프 연계
    - v04 (2025-11-24): Agent 2/3 데이터 통합, Refiner 연계 최종 완성
    - v05 (2025-12-01): 프롬프트 구조 개선
"""

from typing import Dict, Any, List
from datetime import datetime
import logging
import json

logger = logging.getLogger("ReportComposerAgent")


class ReportComposerAgent:
    """
    보고서 초안 작성 Agent (Agent 4)
    ---------------------------------
    목적:
    - Executive Summary + Template 기반 섹션 + 전략/영향 분석 결합
    - Citation 포함 Draft Report 생성
    - Memory Node: draft_report + citations 저장
    - Refiner 루프 연계 가능
    """

    def __init__(self, llm_client, citation_formatter, markdown_renderer):
        """
        Args:
            llm_client: async LLM 호출 클라이언트
            citation_formatter: Citation 처리 유틸
            markdown_renderer: Markdown → HTML/PDF 변환 유틸
        """
        self.llm = llm_client
        self.citation = citation_formatter
        self.render = markdown_renderer
        logger.info("[ReportComposerAgent] 초기화 완료")

    # ============================================================
    # PUBLIC: LangGraph Node async 실행 진입점
    # ============================================================
    async def compose_draft(
        self,
        report_profile: Dict[str, Any],
        impact_summary: Dict[str, Any],
        strategies: List[Dict[str, Any]],
        template: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Draft 보고서 생성
        Returns:
            {
                draft_markdown,
                draft_json,
                citations,
                status
            }
        """
        logger.info("[ReportComposerAgent] 보고서 초안 생성 시작")
        try:
            # 1. Executive Summary 생성
            executive_summary = await self._generate_executive_summary(
                report_profile, impact_summary, strategies
            )

            # 2. Template 기반 섹션 문단 생성
            sections = await self._generate_sections(
                template, report_profile, impact_summary, strategies
            )

            # 3. Markdown Draft 구성
            draft_md = self.render.render_markdown({
                "executive_summary": executive_summary,
                "sections": sections,
                "template": template
            })

            # 4. JSON Draft 구성 (Memory Node용)
            draft_json = {
                "executive_summary": executive_summary,
                "sections": sections,
                "metadata": template.get("metadata", {}),
                "generated_at": datetime.now().isoformat()
            }

            # 5. citations 수집 및 포맷
            citations = self.citation.collect_all(draft_md)

            return {
                "draft_markdown": draft_md,
                "draft_json": draft_json,
                "citations": citations,
                "status": "completed"
            }

        except Exception as e:
            logger.error("[ReportComposerAgent] 초안 생성 실패", exc_info=True)
            return {
                "status": "failed",
                "error": str(e)
            }

    # ============================================================
    # Internal Methods
    # ============================================================
    async def _generate_executive_summary(
        self,
        report_profile: Dict[str, Any],
        impact_summary: Dict[str, Any],
        strategies: List[Dict[str, Any]]
    ) -> str:
        """
        Executive Summary 생성 (LLM)
        - 상위 3개 리스크 및 종합 전략 요약
        """
        top_risks = impact_summary.get("top_risks", [])
        top3_risk_names = ", ".join([r["risk_type"] for r in top_risks[:3]]) if top_risks else "N/A"
        total_financial_loss = impact_summary.get("total_financial_loss", "N/A")

        overall_strategy_summary_parts = [s.get("strategy_summary", "") for s in strategies if s.get("strategy_summary")]
        overall_strategy = ". ".join(overall_strategy_summary_parts[:2]) + ("..." if len(overall_strategy_summary_parts) > 2 else "") if overall_strategy_summary_parts else "N/A"

        prompt = f"""
<ROLE>
You are an expert report writer specializing in TCFD and ESG disclosures for investors and regulatory bodies. Your talent lies in synthesizing vast amounts of data into concise, compelling narratives, ensuring readers quickly grasp key messages. Your writing is consistently clear, error-free, and highly persuasive.
</ROLE>

<CONTEXT>
You are provided with a summary of the company's report profile, key impact analysis findings, and an overview of proposed strategies. Your goal is to distill this into an Executive Summary.

<REPORT_PROFILE_TONE>
{json.dumps(report_profile.get('tone', {}), indent=2, ensure_ascii=False)}
</REPORT_PROFILE_TONE>

<TOP_RISKS_SUMMARY>
The top 3 identified climate risks are: {top3_risk_names}.
</TOP_RISKS_SUMMARY>

<TOTAL_FINANCIAL_LOSS_SUMMARY>
The total estimated financial loss (AAL/other metrics) is: {total_financial_loss}.
</TOTAL_FINANCIAL_LOSS_SUMMARY>

<OVERALL_STRATEGY_SUMMARY>
The proposed overall strategic approach involves: {overall_strategy}.
</OVERALL_STRATEGY_SUMMARY>
</CONTEXT>

<INSTRUCTIONS>
Your task is to draft a compelling Executive Summary for a TCFD/ESG report.
</INSTRUCTIONS>

<OUTPUT_FORMAT>
- The summary must be a Markdown formatted text of 4 to 6 sentences.
- It must clearly state the most significant climate-related risks and the company's overarching strategic response.
- The tone and style should align with a formal corporate report.
</OUTPUT_FORMAT>

<RULES>
- Output ONLY the Markdown formatted Executive Summary. DO NOT include any explanations, apologies, or text outside the summary itself.
- DO NOT invent details or go beyond the provided context.
- Maintain the tone and style of a high-level corporate report, as indicated in the <REPORT_PROFILE_TONE>.
- Ensure strict adherence to Markdown syntax.
</RULES>
"""
        summary = await self.llm.ainvoke(prompt)
        return summary.strip()

    async def _generate_sections(
        self,
        template: Dict[str, Any],
        report_profile: Dict[str, Any],
        impact_summary: Dict[str, Any],
        strategies: List[Dict[str, Any]]
    ) -> Dict[str, str]:
        """
        Template 기반 섹션 생성 (LLM)
        - 각 섹션별 Markdown 문단 생성
        - 필요시 citation 포맷 삽입
        """
        sections = {}
        section_defs = template.get("sections", {})

        for sec_key, sec_info in section_defs.items():
            section_title = sec_info.get("title", sec_key.replace("_", " ").title())
            section_description = sec_info.get("description", "No specific description provided.")
            
            strategies_for_prompt = json.dumps(strategies, indent=2, ensure_ascii=False)

            prompt = f"""
<ROLE>
You are an expert report writer specializing in TCFD and ESG disclosures for investors and regulatory bodies. Your talent lies in synthesizing vast amounts of data into concise, compelling narratives, ensuring readers quickly grasp key messages. Your writing is consistently clear, error-free, and highly persuasive.
</ROLE>

<CONTEXT>
You are tasked with writing a specific section of a comprehensive TCFD/ESG report. You are provided with the overall report style, key impact analysis findings, and detailed proposed strategies.

<SECTION_DETAILS>
Section Title: {section_title}
Section Purpose: {section_description}
</SECTION_DETAILS>

<REPORT_PROFILE>
{json.dumps(report_profile, indent=2, ensure_ascii=False)}
</REPORT_PROFILE>

<IMPACT_ANALYSIS_SUMMARY>
{json.dumps(impact_summary, indent=2, ensure_ascii=False)}
</IMPACT_ANALYSIS_SUMMARY>

<STRATEGIES_DETAILS>
{strategies_for_prompt}
</STRATEGIES_DETAILS>
</CONTEXT>

<INSTRUCTIONS>
Your task is to write the content for the section titled "{section_title}".
</INSTRUCTIONS>

<OUTPUT_FORMAT>
- The section content must be in Markdown format.
- Generate between 2 to 4 concise paragraphs for this section.
- If relevant and justified by the context, insert citation placeholders in the format "[[ref-id]]".
</OUTPUT_FORMAT>

<RULES>
- Output ONLY the Markdown formatted section content. DO NOT include any explanations, apologies, or text outside the section content itself.
- DO NOT invent details or go beyond the provided context.
- Maintain the tone and style of a high-level corporate report, as indicated in the <REPORT_PROFILE>.
- Strictly adhere to Markdown syntax.
</RULES>
"""
            result = await self.llm.ainvoke(prompt)
            sections[sec_key] = result.strip()

        return sections