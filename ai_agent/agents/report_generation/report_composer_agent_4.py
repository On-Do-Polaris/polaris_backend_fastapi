# report_composer_agent_4.py
"""
파일명: report_composer_agent_4.py
최종 수정일: 2025-12-05
버전: v08

파일 개요:
    - 보고서 초안 작성 Agent (템플릿 + 분석 결과 + 전략 결합)
    - LangGraph Composer Node용
    - LLM 기반 Markdown + JSON 구조 생성
    - RAG 기반 citations 포함
    - Memory Node: draft_report + citations 저장
    - Refiner 루프 연계 가능
    - v08: 섹션별 정량 데이터 컨텍스트 주입 및 내러티브 가이던스 추가

주요 기능:
    1. Executive Summary 생성 (상위 3개 리스크 + 종합 전략 요약)
    2. Template 기반 섹션 문단 생성
    3. Markdown/JSON Draft 구성
    4. citations 수집 및 포맷
    5. Refiner 루프용 draft 상태 제공 (Text Issue 발생 시 LLM 재호출 가능)
    6. v08: TCFD 섹션별 맞춤 정량 데이터 컨텍스트 주입
    7. v08: 섹션별 내러티브 작성 패턴 가이던스

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
    - v08 (2025-12-05): 섹션별 정량 데이터 컨텍스트 주입 강화
        - Strategy 섹션: 사업장 비교 + 투자 우선순위
        - Risk Management 섹션: H×E×V 분해 분석 + 원인 설명
        - Metrics 섹션: AAL 목표 + 재무 영향
        - 섹션별 내러티브 작성 패턴 가이던스 추가
"""

from typing import Dict, Any
from datetime import datetime
import logging
from ...utils.prompt_loader import PromptLoader
from ai_agent.utils.knowledge import RiskContextBuilder

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
        self.risk_context_builder = RiskContextBuilder()
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
        Template 기반 섹션 생성 (LLM) - v08 섹션별 컨텍스트 주입 강화
        - 각 섹션별 Markdown 문단 생성
        - 필요시 citation 포맷 삽입
        - NEW: 섹션별 정량 데이터 컨텍스트 주입
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

            # NEW: 섹션별 컨텍스트 구성
            section_context = self._build_section_context(
                sec_key, impact_summary, strategies
            )

            # NEW: 섹션별 내러티브 가이드 생성
            narrative_guidance = self._build_narrative_guidance(sec_key)

            # NEW: RiskContextBuilder를 사용하여 리스크 지식 베이스 추가
            # 분석된 리스크 타입 추출
            risk_types = []
            if "top_risks" in impact_summary:
                risk_types = [r.get("risk_type") for r in impact_summary.get("top_risks", [])]

            # Report Composer용 리스크 컨텍스트 생성
            risk_knowledge = ""
            if risk_types:
                risk_context = self.risk_context_builder.get_report_context(risk_types)
                risk_knowledge = self.risk_context_builder.format_for_prompt(risk_context, format_type="json")

            # PromptLoader를 사용하여 프롬프트 로드 및 출력 언어 지시자 추가
            prompt_template = self.prompt_loader.load('section_generation', output_language=self.language)

            # 변수 치환 (기존 + NEW 컨텍스트)
            prompt = prompt_template.format(
                section_title=section_title,
                section_description=sec_description,
                report_profile=report_profile,
                impact_summary=impact_summary,
                strategies=strategies
            )

            # NEW: 섹션별 컨텍스트 추가 (프롬프트 끝에 삽입)
            if section_context:
                prompt += f"\n\n<SECTION_CONTEXT>\n{section_context}\n</SECTION_CONTEXT>"

            if narrative_guidance:
                prompt += f"\n\n<NARRATIVE_GUIDANCE>\n{narrative_guidance}\n</NARRATIVE_GUIDANCE>"

            if risk_knowledge:
                prompt += f"\n\n<RISK_KNOWLEDGE_BASE>\nThis knowledge base provides comprehensive information about each climate risk for report writing, including:\n- Full definitions and units\n- Bin descriptions for qualitative interpretation\n- Impact targets (impacts_on)\n- Data sources for citation\n\n{risk_knowledge}\n</RISK_KNOWLEDGE_BASE>"

            result = await self.llm.ainvoke(prompt)
            sections[sec_key] = result.strip()

        return sections

    def _build_section_context(
        self,
        section_key: str,
        impact_summary: Dict[str, Any],
        strategies: Dict[str, Any]
    ) -> str:
        """
        섹션별 정량 데이터 컨텍스트 구성 (v08)

        각 TCFD 섹션에 필요한 정량 데이터를 필터링하여 제공

        Args:
            section_key: TCFD 섹션 키 (governance, strategy, risk_management, metrics_and_targets)
            impact_summary: Impact Analysis Agent의 run_aggregated() 결과
            strategies: Strategy Generation Agent 결과

        Returns:
            섹션별 맞춤 컨텍스트 문자열
        """
        import json

        # quantitative_deep_dive와 qualitative_insights 추출
        quant_deep_dive = impact_summary.get("quantitative_deep_dive", {})
        qual_insights = impact_summary.get("qualitative_insights", {})

        if section_key == "strategy":
            # Strategy 섹션: 사업장 비교 + 투자 우선순위
            context_parts = []

            context_parts.append("### 사업장별 리스크 비교 및 투자 우선순위")
            context_parts.append("")

            for risk in quant_deep_dive.get("top_risks", [])[:3]:  # Top 3만
                risk_type = risk.get("risk_type")
                site_comparison = risk.get("site_comparison", [])
                priority_matrix = risk.get("priority_matrix", {})

                if site_comparison:
                    context_parts.append(f"**{risk_type}**:")
                    for site in site_comparison:
                        context_parts.append(
                            f"- {site['site_name']}: AAL {site['aal_percentage']}% "
                            f"(약 {site['aal_amount']:,.0f}원), "
                            f"Risk Score {site['risk_score']}, "
                            f"핵심 요인: {', '.join(site['key_factors'])}"
                        )

                    if priority_matrix:
                        invest_rec = priority_matrix.get("investment_recommendation", "")
                        context_parts.append(f"  → 투자 권고: {invest_rec}")

                context_parts.append("")

            # 정성 인사이트 추가
            site_insights = qual_insights.get("site_comparison_insights", [])
            if site_insights:
                context_parts.append("### 정성 인사이트")
                for insight in site_insights[:3]:
                    context_parts.append(f"- {insight}")

            return "\n".join(context_parts)

        elif section_key == "risk_management":
            # Risk Management 섹션: H×E×V 분해 분석
            context_parts = []

            context_parts.append("### H×E×V 요소별 원인 분석")
            context_parts.append("")

            hev_interp = qual_insights.get("hev_interpretation", {})

            for risk in quant_deep_dive.get("top_risks", [])[:3]:  # Top 3만
                risk_type = risk.get("risk_type")
                hev_breakdown = risk.get("hev_breakdown", {})

                context_parts.append(f"**{risk_type}**:")

                # H, E, V 점수
                h_data = hev_breakdown.get("H", {})
                e_data = hev_breakdown.get("E", {})
                v_data = hev_breakdown.get("V", {})

                context_parts.append(f"- Hazard (H): 평균 {h_data.get('average', 0)}, "
                                   f"범위 {h_data.get('site_range', {}).get('min', 0)}-{h_data.get('site_range', {}).get('max', 0)}")

                # H 원인
                risk_hev = hev_interp.get(risk_type, {})
                if risk_hev.get("H_high_reason"):
                    context_parts.append(f"  - 원인: {risk_hev['H_high_reason']}")

                context_parts.append(f"- Exposure (E): 평균 {e_data.get('average', 0)}, "
                                   f"범위 {e_data.get('site_range', {}).get('min', 0)}-{e_data.get('site_range', {}).get('max', 0)}")

                if risk_hev.get("E_high_reason"):
                    context_parts.append(f"  - 원인: {risk_hev['E_high_reason']}")

                context_parts.append(f"- Vulnerability (V): 평균 {v_data.get('average', 0)}, "
                                   f"범위 {v_data.get('site_range', {}).get('min', 0)}-{v_data.get('site_range', {}).get('max', 0)}")

                if risk_hev.get("V_high_reason"):
                    context_parts.append(f"  - 원인: {risk_hev['V_high_reason']}")

                if risk_hev.get("mitigation_potential"):
                    context_parts.append(f"  - 완화 가능성: {risk_hev['mitigation_potential']}")

                context_parts.append("")

            return "\n".join(context_parts)

        elif section_key == "metrics_and_targets" or section_key == "metrics_targets":
            # Metrics 섹션: AAL 목표 및 재무 영향
            context_parts = []

            context_parts.append("### 현재 AAL 및 재무 영향")
            context_parts.append("")

            for risk in quant_deep_dive.get("top_risks", [])[:3]:  # Top 3만
                risk_type = risk.get("risk_type")
                financial_impact = risk.get("financial_impact", {})

                context_parts.append(f"**{risk_type}**:")
                context_parts.append(f"- 평균 AAL: {financial_impact.get('average_aal_percentage', 0)}%")
                context_parts.append(f"- 총 AAL 손실: {financial_impact.get('total_aal_amount', 0):,.0f}원")

                # 사업장별
                site_breakdown = financial_impact.get("site_breakdown", [])
                if site_breakdown:
                    context_parts.append("  - 사업장별:")
                    for site in site_breakdown[:3]:
                        context_parts.append(
                            f"    - {site['site_name']}: {site['aal_percentage']}% "
                            f"({site['aal_amount']:,.0f}원)"
                        )

                # 목표 제시 (현재 AAL의 50% 감축 가정)
                current_aal = financial_impact.get('average_aal_percentage', 0)
                target_aal = round(current_aal * 0.5, 4)
                context_parts.append(f"  → 목표: {target_aal}% (현재 대비 50% 감축)")

                context_parts.append("")

            return "\n".join(context_parts)

        elif section_key == "governance":
            # Governance 섹션: 전체 요약 (간단히)
            top_site = impact_summary.get("top_site", {})
            if top_site:
                site_info = top_site.get("site_info", {})
                site_name = site_info.get("site_name", "Unknown")
                total_score = top_site.get("total_score", 0)

                return f"### 최고 리스크 사업장\n- {site_name}: 총 Risk Score {total_score:.2f}"

        return ""

    def _build_narrative_guidance(self, section_key: str) -> str:
        """
        섹션별 내러티브 가이던스 (요구 패턴)

        Args:
            section_key: TCFD 섹션 키

        Returns:
            LLM에게 제공할 작성 패턴 가이드
        """
        if section_key == "strategy":
            return """
**중요**: 결과 나열이 아닌 '개선 방안과 효과'에 초점을 맞춰 작성하세요.

반드시 아래 패턴을 따라주세요:

1. **투자 시나리오별 개선 효과를 최우선으로 작성**:
   ❌ 잘못된 예: "현재 AAL이 0.87%입니다."
   ✅ 올바른 예: "현재 AAL 0.87%에서, 예산의 50%를 부산 배수 시스템 개선에 투입할 경우 AAL이 0.40%로 감소하여 54%의 위험 저감 효과가 예상됩니다."

2. **구체적인 대응 방안을 디테일하게 제시** (추상적 표현 금지):
   ❌ 잘못된 예: "지속 가능한 에너지 시스템을 도입하고 이해관계자 협력 체계를 구축합니다."
   ✅ 올바른 예: "RE100 참여: 2030년까지 재생에너지 100% 전환을 목표로, 2025년 Q2까지 태양광 패널 500kW 설치(투자 5억원), 2027년까지 풍력 발전 계약 체결(연간 탄소 배출 40% 감축). SBTi 기준: 2030년까지 Scope 1+2 배출량 50% 감축."

3. **사업장 비교는 구체적 수치 + 개선 방안과 함께**:
   - 예: "부산 물류센터(AAL 10.2%)가 서울 본사(6.5%) 대비 1.57배 높은 리스크를 나타냅니다. 부산에 우선 투자 시 배수 용량 50mm/hr → 120mm/hr 증설로 AAL을 6.2%까지 낮출 수 있으며, 이는 연간 4억원의 예상 손실을 2억원으로 절감하는 효과를 가져옵니다."

4. **투자 ROI 및 재무 효과를 명확히**:
   - 예: "총 투자액 12억원, 연간 절감액 5.2억원, 투자 회수 기간 2.3년"

5. **국제 표준 프로그램을 구체적으로**:
   - 예: "CDP Climate Change 응답 등급 A- 달성 목표, ISO 14090(기후변화 적응) 인증 추진, TCFD 권고안 완전 준수"
"""

        elif section_key == "risk_management":
            return """
**중요**: 리스크 분석에서도 '개선 가능성과 방법'을 함께 제시하세요.

반드시 아래 패턴을 따라주세요:

1. **H×E×V 분석 시 개선 방안을 함께 제시**:
   ❌ 잘못된 예: "river_flood의 경우 H=83.2, V=77.5입니다."
   ✅ 올바른 예: "river_flood의 경우 H=83.2 (해안 인접 45% + 저지대 35%), V=77.5 (건물 노후화 40% + 배수 불량 35%)입니다. 배수 시스템을 50mm/hr에서 120mm/hr 용량으로 개선하면 V가 77.5→45.0으로 감소하며, 이를 통해 AAL을 0.87%→0.40%로 54% 절감할 수 있습니다."

2. **완화 가능성을 투자액 및 기간과 함께**:
   - 예: "배수 시스템 개선(투자 8억원, 공사 기간 18개월): V 77.5→45.0, AAL 0.87%→0.40%, 연간 손실 4.35억원→2억원 (투자 회수 3.4년)"

3. **사업장별 차이는 개선 우선순위와 함께**:
   - 예: "부산(H=88.1)은 서울(H=65.3) 대비 해안 노출도가 35% 높아 최우선 투자 대상입니다. 부산 배수 시스템에 60% 예산 투입, 서울에 40% 투입하면 포트폴리오 전체 AAL을 15% 절감할 수 있습니다."

4. **구체적인 기술적 조치**:
   - 예: "그린 인프라 도입: 건물 옥상 30%에 녹화 지붕 설치로 빗물 유출 40% 감소, Nature-based Solutions: 바이오스웨일(bioswale) 설치로 우수 유출량 35% 저감"
"""

        elif section_key == "metrics_and_targets" or section_key == "metrics_targets":
            return """
**중요**: 단순한 목표 제시가 아닌 '목표 달성 방법과 마일스톤'을 상세히 작성하세요.

반드시 아래 패턴을 따라주세요:

1. **현재 AAL → 목표 AAL → 달성 방법을 구체적으로**:
   ❌ 잘못된 예: "river_flood 현재 AAL 0.87% → 목표 0.40%"
   ✅ 올바른 예: "river_flood 현재 AAL 0.87% → 목표 0.40% (2030년까지 54% 감축). 달성 경로: 1단계(2025-2026) 배수 시스템 개선으로 AAL 0.65% 달성, 2단계(2027-2028) 그린 인프라 구축으로 AAL 0.50% 달성, 3단계(2029-2030) 실시간 모니터링 시스템 구축으로 최종 목표 0.40% 달성."

2. **재무 영향은 투자 대비 절감액으로**:
   - 예: "현재 연간 예상 손실 4억 3,500만원 → 목표 달성 시 2억원으로 절감 (연간 2.35억원 절감). 총 투자액 12억원, 투자 회수 기간 5.1년, NPV 8.7억원 (할인율 5% 적용)"

3. **사업장별 목표는 단계별 실행 계획과 함께**:
   - 예: "부산(현재 0.87% → 목표 0.40%): 2025년 배수 용량 증설, 2026년 녹화 지붕 설치, 2028년 실시간 센서 배치 / 서울(현재 0.42% → 목표 0.20%): 2026년 우수 저류 시설 확충"

4. **KPI와 모니터링 체계를 구체적으로**:
   - 예: "월별 KPI: AAL 감소율, V 점수 개선도, 투자 집행률 / 분기별 리뷰: 이사회 보고, CDP 제출 준비 / 연간 목표: ISO 14090 인증, TCFD 권고안 완전 준수"

5. **국제 표준 목표를 명시**:
   - 예: "2026년 CDP Climate Change 응답 등급 B 달성, 2028년 A- 등급 달성, 2030년 SBTi 검증 완료"
"""

        return ""
