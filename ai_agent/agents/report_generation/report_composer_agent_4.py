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
    - v05 (2025-12-01): 프롬프트 구조 개선 (영어 프롬프트 적용)
"""

from typing import Dict, Any
from datetime import datetime
import logging
from .utils.prompt_loader import PromptLoader

logger = logging.getLogger("ReportComposerAgent")


# 섹션 제목 다국어화
SECTION_TITLES = {
    'en': {
        'executive_summary': 'Executive Summary',
        'governance': 'Governance',
        'strategy': 'Strategy',
        'risk_management': 'Risk Management',
        'metrics_and_targets': 'Metrics and Targets',
        'metrics_targets': 'Metrics and Targets',
    },
    'ko': {
        'executive_summary': '경영진 요약',
        'governance': '거버넌스',
        'strategy': '전략',
        'risk_management': '리스크 관리',
        'metrics_and_targets': '지표 및 목표',
        'metrics_targets': '지표 및 목표',
    }
}


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

    def __init__(self, llm_client, citation_formatter, markdown_renderer, language: str = 'en'):
        """
        Args:
            llm_client: async LLM 호출 클라이언트
            citation_formatter: Citation 처리 유틸
            markdown_renderer: Markdown → HTML/PDF 변환 유틸
            language: 보고서 출력 언어 ('ko', 'en')
        """
        self.llm = llm_client
        self.citation = citation_formatter
        self.render = markdown_renderer
        self.language = language
        self.prompt_loader = PromptLoader()
        logger.info(f"[ReportComposerAgent] 초기화 완료 (output_language={language})")

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
            # 1. Executive Summary 생성
            executive_summary = await self._generate_executive_summary(
                report_profile, impact_summary, strategies
            )

            # 2. Template 기반 섹션 문단 생성
            sections = await self._generate_sections(
                template, report_profile, impact_summary, strategies
            )

            # 3. Markdown Draft 구성
            # Markdown 문자열 생성
            report_title = template.get('title', 'Physical Risk Analysis Report')
            if self.language == 'ko':
                report_title = '물리적 리스크 분석 보고서'

            md_text = f"# {report_title}\n\n"

            # Executive Summary 제목 다국어화
            exec_summary_title = SECTION_TITLES.get(self.language, SECTION_TITLES['en']).get('executive_summary', 'Executive Summary')
            md_text += f"## {exec_summary_title}\n\n{executive_summary}\n\n"

            # sections는 dict {sec_key: content_text} 형태
            # executive_summary는 이미 추가했으므로 제외
            for sec_key, content_text in sections.items():
                # Executive Summary 중복 방지
                if sec_key == "executive_summary":
                    continue

                # 다국어 제목 가져오기
                section_title = SECTION_TITLES.get(self.language, SECTION_TITLES['en']).get(
                    sec_key,
                    sec_key.replace('_', ' ').title()
                )

                md_text += f"## {section_title}\n\n{content_text}\n\n"

            # Markdown → HTML 변환
            draft_md = md_text  # HTML로 변환하지 않고 Markdown 그대로 저장

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
        strategies: Dict[str, Any]
    ) -> str:
        """
        Executive Summary 생성 (LLM)
        - 상위 3개 리스크 및 종합 전략 요약
        """
        top_risks = impact_summary.get("top_risks", [])
        top3 = ", ".join([r["risk_type"] for r in top_risks[:3]])
        total_loss = impact_summary.get("total_financial_loss", "N/A")

        # strategies가 List[Dict]일 경우 Dict로 변환
        if isinstance(strategies, list):
            overall_strategy = " / ".join([s.get('strategy', '')[:100] for s in strategies if isinstance(s, dict)])
        elif isinstance(strategies, dict):
            overall_strategy = strategies.get("overall_strategy", "")
        else:
            overall_strategy = ""

        # PromptLoader를 사용하여 프롬프트 로드 및 출력 언어 지시자 추가
        prompt_template = self.prompt_loader.load('executive_summary', output_language=self.language)

        # 변수 치환
        prompt = prompt_template.format(
            tone=report_profile.get('tone', 'N/A'),
            top_risks=top3,
            total_loss=total_loss,
            overall_strategy=overall_strategy
        )

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

        # template은 report_profile과 동일하므로 section_structure를 사용
        section_structure = template.get("section_structure", {})
        main_sections = section_structure.get("main_sections", [])
        tcfd_structure = template.get("tcfd_structure", {})

        for sec_key in main_sections:
            # Executive Summary는 별도로 생성되므로 스킵
            if sec_key == "executive_summary":
                continue

            # TCFD 구조에서 설명 가져오기
            sec_description = tcfd_structure.get(sec_key, f"{sec_key} section")
            section_title = sec_key.replace('_', ' ').title()

            # PromptLoader를 사용하여 프롬프트 로드 및 출력 언어 지시자 추가
            prompt_template = self.prompt_loader.load('section_generation', output_language=self.language)

            # 변수 치환
            prompt = prompt_template.format(
                section_title=section_title,
                section_description=sec_description,
                report_profile=report_profile,
                impact_summary=impact_summary,
                strategies=strategies
            )

            result = await self.llm.ainvoke(prompt)
            sections[sec_key] = result.strip()

        return sections
