# refiner_agent_6.py
"""
파일명: refiner_agent_6.py
최종 수정일: 2025-11-24
버전: v03

파일 개요:
    - Validation 결과 기반 Draft 개선 Agent
    - Markdown + JSON 구조 자동 보완 및 품질 향상
    - LangGraph 반복 루프(Validation <-> Refiner) 지원
    - Memory Node 연계 가능 (history 기록)

주요 기능:
    1. JSON 구조/내용 자동 보완
    2. Markdown 텍스트 개선 (LLM 기반)
    3. Validation Agent 결과(issue + recommendations) 반영
    4. TCFD Alignment, 핵심 전략 누락, Section 부족 자동 보완
    5. applied_fixes 기록 제공 (수정 내역 추적)
    6. Refiner 반복 루프 지원 (Validation → Refiner → Validation)

변경 이력:
    - v01 (2025-11-14): 초안
        * 기본 JSON 구조 보완
        * Markdown 개선 함수 skeleton 작성
    - v02 (2025-11-21):
        * LLM 기반 Markdown 보완 구현
        * JSON content 자동 보완 강화
        * applied_fixes 리턴
        * LangGraph async 구조 지원
    - v03 (2025-11-24, 최신):
        * Memory Node 연계 구조 반영
        * Validation 결과 기반 TCFD / Strategy 누락 보완 로직 개선
        * JSON/Markdown 보완 동시 적용 및 applied_fixes 상세 기록
        * 예외 처리 강화, 상태(status) 명확화
"""

from typing import Dict, Any, List
import logging
import copy

logger = logging.getLogger("RefinerAgent")


class RefinerAgent:
    """
    리포트 Refiner Agent
    - Validation 결과 기반 Draft Markdown/JSON 자동 보완
    - LangGraph 반복 루프(Validation <-> Refiner) 지원
    """

    def __init__(self, llm_client):
        self.llm = llm_client
        logger.info("[RefinerAgent] 초기화 완료")

    # ============================================================
    # LangGraph async Entry
    # ============================================================
    async def refine(
        self,
        draft_markdown: str,
        draft_json: Dict[str, Any],
        validation_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        logger.info("[RefinerAgent] 리포트 개선 시작")

        try:
            issues = validation_results.get("issues", [])
            recs = validation_results.get("recommendations", [])

            updated_json = copy.deepcopy(draft_json)
            updated_markdown = draft_markdown

            # 1. JSON 구조 보완
            structural_fixes = self._fix_json_structure(updated_json)

            # 2. Markdown 텍스트 개선 (LLM)
            text_fixes, updated_markdown = self._refine_markdown(
                updated_markdown, issues, recs, updated_json
            )

            # 3. JSON 내용 보완 (누락 데이터 / summaries 반영)
            content_fixes = self._fix_json_content(updated_json, issues)

            applied_fixes = structural_fixes + text_fixes + content_fixes

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
    # 1. JSON 구조 보완
    # ============================================================
    def _fix_json_structure(self, json_data: Dict[str, Any]) -> List[str]:
        fixes = []
        required_sections = ["executive_summary", "sections"]

        for sec in required_sections:
            if sec not in json_data:
                json_data[sec] = "" if sec == "executive_summary" else {}
                fixes.append(f"누락 섹션 '{sec}' 자동 생성")

        if "sections" in json_data:
            if not isinstance(json_data["sections"], dict):
                json_data["sections"] = {}
                fixes.append("sections 구조 손상 → 빈 dict로 복원")

            minimal_keys = ["risk_overview", "impact_analysis", "strategy"]
            for k in minimal_keys:
                if k not in json_data["sections"]:
                    json_data["sections"][k] = ""
                    fixes.append(f"섹션 내부 누락 '{k}' 자동 추가")

        return fixes

    # ============================================================
    # 2. Markdown 텍스트 개선 (LLM 기반)
    # ============================================================
    def _refine_markdown(
        self,
        markdown: str,
        issues: List[str],
        recs: List[str],
        json_data: Dict[str, Any]
    ):
        if not issues:
            return [], markdown

        prompt = f"""
다음은 환경 리스크 분석 보고서 Markdown 초안입니다. 문제점과 개선 요구사항을 기반으로 텍스트를 보완하세요.

[초안]
{markdown}

[발견된 문제점]
{issues}

[개선 요구사항]
{recs}

[JSON 데이터]
{json_data}

규칙:
- 보고서 구조 유지
- 의미 변형 최소화
- 누락 정보 JSON 기반 보완
- TCFD 섹션 부족시 자동 삽입
- Markdown 문법 유지

출력: 수정된 Markdown 텍스트만
"""
        refined_text = self.llm.generate_refined_markdown(prompt)
        return ["LLM 기반 텍스트 개선 수행"], refined_text

    # ============================================================
    # 3. JSON 내용 보완
    # ============================================================
    def _fix_json_content(self, json_data: Dict[str, Any], issues: List[str]):
        fixes = []

        if not json_data.get("executive_summary"):
            json_data["executive_summary"] = (
                "본 보고서는 주요 환경 리스크 분석과 대응 전략을 요약한 문서입니다."
            )
            fixes.append("Executive Summary 자동 생성")

        if "sections" in json_data and "strategy" in json_data["sections"]:
            if len(json_data["sections"]["strategy"]) < 20:
                json_data["sections"]["strategy"] = (
                    "본 문서는 식별된 주요 리스크에 대한 대응 전략을 포함하며, "
                    "위험 완화를 위한 구체적 조치사항을 제시합니다."
                )
                fixes.append("Strategy 섹션 내용 자동 보완")

        return fixes
