# report_composer_agent_4.py
"""
파일명: report_composer_agent_4.py
최종 수정일: 2025-11-24
버전: v03

파일 개요:
    - 보고서 초안 작성 Agent (템플릿 + 분석 결과 + 전략 결합)
    - LangGraph Composer Node용
    - LLM 기반 Markdown + JSON 구조 생성
    - RAG 기반 citations 포함
    - Memory Node: draft_report + citations 저장

주요 기능:
    1. Executive Summary 생성
    2. Template 기반 섹션 문단 생성
    3. Markdown/JSON Draft 구성
    4. citations 수집 및 포맷
    5. Refiner 루프용 draft 상태 제공

Refiner 루프 연계:
    - Text Issue 발생 시 route: composer
    - LLM 재호출로 문장 품질/구조 개선
    - Draft + citations 재생성

변경 이력:
    - v01 (2025-11-14): 초안 작성, Super-Agent 구조
    - v02 (2025-11-21): async, JSON 스키마, 상태/예외 처리 추가
    - v03 (2025-11-24): 최신 LangGraph 아키텍처 반영, Memory Node/Refiner 루프 연계
"""

from typing import Dict, Any
from datetime import datetime
import logging

logger = logging.getLogger("ReportComposerAgent")


class ReportComposerAgent:
    """
    보고서 초안 작성 Agent
    - Executive Summary + Template 기반 섹션 + 전략/영향 분석 결합
    - Citation 포함 Draft Report 생성
    - Memory Node: draft_report + citations 저장
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
        strategies: Dict[str, Any],
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
            # 1. Executive Summary
            executive_summary = await self._generate_executive_summary(
                report_profile, impact_summary, strategies
            )

            # 2. Section 문단 생성
            sections = await self._generate_sections(template, report_profile, impact_summary, strategies)

            # 3. Markdown Draft 구성
            draft_md = self.render.render_markdown({
                "executive_summary": executive_summary,
                "sections": sections,
                "template": template
            })

            # 4. JSON Draft 구성
            draft_json = {
                "executive_summary": executive_summary,
                "sections": sections,
                "metadata": template.get("metadata", {}),
                "generated_at": datetime.now().isoformat()
            }

            # 5. citations 수집
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
        strategies: Dict[str, Any]
    ) -> str:
        """
        Executive Summary 생성 (LLM)
        - 상위 3개 리스크 및 종합 전략 요약
        """
        top_risks = impact_summary.get("top_risks", [])
        top3 = ", ".join([r["risk_type"] for r in top_risks[:3]])
        prompt = f"""
당신은 기후 리스크 전문 보고서 작성자입니다.

다음 정보를 기반으로 Executive Summary를 작성하세요.
- 기존 보고서 패턴/톤: {report_profile.get('tone', 'N/A')}
- 상위 주요 리스크: {top3}
- 총 예상 재무손실: {impact_summary.get('total_financial_loss','N/A')}
- 종합 대응 전략: {strategies.get('overall_strategy', '')}

형식: Markdown, 4~6문장, 기업 보고서 스타일
"""
        summary = await self.llm.ainvoke(prompt)
        return summary.strip()

    async def _generate_sections(
        self,
        template: Dict[str, Any],
        report_profile: Dict[str, Any],
        impact_summary: Dict[str, Any],
        strategies: Dict[str, Any]
    ) -> Dict[str, str]:
        """
        Template 기반 섹션 생성 (LLM)
        - 각 섹션별 Markdown 문단 생성
        - 필요시 citation 포맷 삽입
        """
        sections = {}
        section_defs = template.get("sections", {})

        for sec_key, sec_info in section_defs.items():
            prompt = f"""
당신은 ESG/TCFD 보고서 전문 작성자입니다.

섹션 제목: {sec_info.get("title")}
역할: {sec_info.get("description")}

분석 데이터:
- report_profile: {report_profile}
- impact_summary: {impact_summary}
- strategies: {strategies}

요구:
- Markdown 문단 2~4개 생성
- 필요 시 citation 포맷 삽입 (형식: [[ref-id]])
"""
            result = await self.llm.ainvoke(prompt)
            sections[sec_key] = result.strip()

        return sections
