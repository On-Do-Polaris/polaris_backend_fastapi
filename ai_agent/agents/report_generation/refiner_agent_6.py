# refiner_agent_6.py
"""
파일명: refiner_agent_6.py
최종 수정일: 2025-11-24
버전: v04  (최신)

파일 개요:
    - Validation Agent(5)의 결과 기반으로 Draft Report(JSON/Markdown)를 자동 보완하는 Agent
    - Data Issue / Strategy Issue / Text Issue 자동 처리
    - LangGraph Refiner Loop (Validation <-> Refiner) 핵심 Agent
    - 1~4번 Agent 흐름과 호환되는 구조적 JSON/Markdown 보완 기능
 
핵심 역할:
    1. JSON 구조/필수 섹션 보완 (구조 보정)
    2. JSON 내용 보완 (누락된 impact/strategy/summary 자동 보강)
    3. Markdown 텍스트 보완 (LLM 사용)
    4. Validation 이슈 기반 자동 수정
    5. TCFD 섹션 부족 → 자동 삽입
    6. applied_fixes[] 제공 → Finalizer와 Audit Log용
    7. Refiner Loop 재검증을 위한 완성된 Draft 반환

입력:
    - draft_markdown(str)
    - draft_json(dict)
    - validation_results(dict: score, issues[], recommendations[])

출력:
    {
        "updated_markdown": str,
        "updated_json": dict,
        "applied_fixes": list[str],
        "status": "completed"
    }

변경 이력:
    - v01: 기본 구조/LLM 호출 스켈레톤
    - v02: LLM 기반 Markdown refine + JSON 보완
    - v03: Validation 연계 강화, 누락 섹션 자동 생성
    - v04 (2025-11-24, 최신):
        * Data Issue / Strategy Issue / Text Issue 패턴 기반 보완
        * LangGraph 1~4 에이전트와 완전 호환
        * TCFD 섹션 자동 생성 강화
        * applied_fixes 레벨 세분화
"""

from typing import Dict, Any, List
import copy
import logging

logger = logging.getLogger("RefinerAgent")


class RefinerAgent:
    """
    Refiner Agent
    - Validation 결과 기반 Draft 보완
    - JSON/Markdown 동시 개선
    """

    def __init__(self, llm_client):
        self.llm = llm_client
        logger.info("[RefinerAgent] 초기화 완료 (v04)")

    # ============================================================
    # LangGraph async entrypoint
    # ============================================================
    async def refine(
        self,
        draft_markdown: str,
        draft_json: Dict[str, Any],
        validation_results: Dict[str, Any]
    ) -> Dict[str, Any]:

        logger.info("[RefinerAgent] 개선 시작")

        try:
            issues = validation_results.get("issues", [])
            recommendations = validation_results.get("recommendations", [])

            updated_json = copy.deepcopy(draft_json)
            updated_markdown = draft_markdown
            applied_fixes: List[str] = []

            # --------------------------------------------------------
            # 1) JSON 구조 보완 (필수 섹션/키 생성)
            # --------------------------------------------------------
            structural_fixes = self._fix_json_structure(updated_json)
            applied_fixes.extend(structural_fixes)

            # --------------------------------------------------------
            # 2) JSON 내용 보완 (누락된 summary / strategy 보완)
            # --------------------------------------------------------
            content_fixes = self._fix_json_content(updated_json, issues)
            applied_fixes.extend(content_fixes)

            # --------------------------------------------------------
            # 3) Markdown 텍스트 보완 (LLM 기반)
            # --------------------------------------------------------
            text_fixes, updated_markdown = await self._refine_markdown(
                updated_markdown,
                issues,
                recommendations,
                updated_json
            )
            applied_fixes.extend(text_fixes)

            # --------------------------------------------------------
            # 4) TCFD Alignment 자동 보완
            # --------------------------------------------------------
            tcfd_fixes, updated_markdown = self._ensure_tcfd_alignment(
                updated_markdown
            )
            applied_fixes.extend(tcfd_fixes)

            # --------------------------------------------------------
            # 결과 반환
            # --------------------------------------------------------
            return {
                "updated_markdown": updated_markdown,
                "updated_json": updated_json,
                "applied_fixes": applied_fixes,
                "status": "completed"
            }

        except Exception as e:
            logger.error("[RefinerAgent] 오류 발생", exc_info=True)
            return {"status": "failed", "error": str(e)}

    # ============================================================
    # 1) JSON 구조 보완
    # ============================================================
    def _fix_json_structure(self, json_data: Dict[str, Any]) -> List[str]:
        fixes = []
        required_sections = ["executive_summary", "sections"]

        for sec in required_sections:
            if sec not in json_data:
                json_data[sec] = "" if sec == "executive_summary" else {}
                fixes.append(f"[구조 보완] '{sec}' 자동 생성")

        if "sections" in json_data:
            minimal_keys = ["risk_overview", "impact_analysis", "strategy"]

            for key in minimal_keys:
                if key not in json_data["sections"]:
                    json_data["sections"][key] = ""
                    fixes.append(f"[구조 보완] sections/{key} 자동 생성")

        return fixes

    # ============================================================
    # 2) JSON 내용 보완 (Executive Summary, Strategy 등)
    # ============================================================
    def _fix_json_content(self, json_data: Dict[str, Any], issues: List[str]) -> List[str]:
        fixes = []

        # Executive Summary가 너무 짧을 경우 자동 생성
        if not json_data.get("executive_summary") or len(json_data["executive_summary"]) < 20:
            json_data["executive_summary"] = (
                "본 보고서는 주요 환경 리스크 분석 결과와 이에 기반한 대응 전략을 요약하여 제공합니다."
            )
            fixes.append("[내용 보완] Executive Summary 자동 보강")

        # Strategy 내용이 비어있을 경우 자동 보완
        st = json_data.get("sections", {}).get("strategy", "")
        if not st or len(st) < 30:
            json_data["sections"]["strategy"] = (
                "식별된 주요 리스크에 따라 회사는 예방, 대비, 완화 전략을 포함한 통합 리스크 대응 체계를 수립했습니다."
            )
            fixes.append("[내용 보완] Strategy 섹션 자동 보강")

        return fixes

    # ============================================================
    # 3) Markdown 텍스트 보완 (LLM)
    # ============================================================
    async def _refine_markdown(
        self,
        markdown: str,
        issues: List[str],
        recommendations: List[str],
        json_data: Dict[str, Any]
    ):
        if not issues:
            return [], markdown

        prompt = f"""
다음은 환경 리스크 분석 보고서의 Markdown 초안입니다.
Validation 단계에서 발견된 문제를 해결하도록 텍스트를 보완하세요.

[초안 Markdown]
{markdown}

[발견된 문제]
{issues}

[개선 요구]
{recommendations}

[현재 JSON 데이터]
{json_data}

규칙:
- 전체 구조는 유지하되 누락된 정보는 JSON으로부터 보완
- 문장을 매끄럽게 보정하되 과도한 재작성 금지
- TCFD 4대 섹션 표현을 보완할 것
- Markdown 문법은 반드시 유지

출력: 보완된 Markdown 전체
"""

        refined = self.llm.generate_refined_markdown(prompt)
        return ["[텍스트 보완] LLM 기반 Markdown 개선 수행"], refined

    # ============================================================
    # 4) TCFD Alignment 자동 보완
    # ============================================================
    def _ensure_tcfd_alignment(self, markdown: str):
        required = {
            "Governance": "## Governance\n기후 관련 리스크와 기회에 대해 경영진이 감독 및 의사결정을 수행하고 있습니다.",
            "Strategy": "## Strategy\n주요 환경 리스크에 대한 단기·중기·장기 전략을 수립했습니다.",
            "Risk Management": "## Risk Management\n리스크 식별·평가·관리 프로세스를 운영하고 있습니다.",
            "Metrics": "## Metrics & Targets\n관련 지표와 목표를 정의하여 진행 상황을 모니터링합니다."
        }

        fixes = []
        updated = markdown

        lower_text = markdown.lower()
        for key, block in required.items():
            if key.lower() not in lower_text:
                updated += f"\n\n{block}\n"
                fixes.append(f"[TCFD 보완] '{key}' 섹션 자동 추가")

        return fixes, updated
