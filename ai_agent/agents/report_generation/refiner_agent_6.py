# refiner_agent_6.py
"""
파일명: refiner_agent_6.py
최종 수정일: 2025-12-01
버전: v06 

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
        * issue 유형 세분화 (data/strategy/text/structure/tcfd/citation)
        * citation 누락 검증 추가
        * Cross consistency (impact ↔ strategy ↔ report) 검증 강화
        * score 가중치 방식으로 개선
        * Refiner 라우팅에서 직접 사용 가능한 issue payload 구조 제공
    - v05 (2025-12-01): 프롬프트 구조 개선
    - v06 (2025-12-01): LLM 기반 Markdown Refine 프롬프트 최종 적용 (사실 확인 수정 기능 포함)
"""

from typing import Dict, Any, List, Tuple
import copy
import logging
import json

logger = logging.getLogger("RefinerAgent")


class RefinerAgent:
    """
    Refiner Agent
    - Validation 결과 기반 Draft 보완
    - JSON/Markdown 동시 개선
    """

    def __init__(self, llm_client):
        self.llm = llm_client
        logger.info("[RefinerAgent] 초기화 완료 (v06)")

    # ============================================================
    # 동기 실행 메서드 (워크플로우 노드용)
    # ============================================================
    def refine_sync(
        self,
        draft_markdown: str,
        draft_json: Dict[str, Any],
        validation_results: Dict[str, Any]
    ) -> Dict[str, Any]:

        logger.info("[RefinerAgent] 개선 시작 (동기)")

        try:
            issues = validation_results.get("issues", [])
            recommendations = validation_results.get("recommendations", [])

            updated_json = copy.deepcopy(draft_json)
            updated_markdown = draft_markdown
            applied_fixes: List[str] = []

            # 1) JSON 구조 보완
            structural_fixes = self._fix_json_structure(updated_json)
            applied_fixes.extend(structural_fixes)

            # 2) JSON 내용 보완
            content_fixes = self._fix_json_content(updated_json, issues)
            applied_fixes.extend(content_fixes)

            # 3) Markdown 텍스트 보완 (LLM 기반 - 동기)
            if self.llm and hasattr(self.llm, 'invoke'):
                text_fixes, updated_markdown = self._refine_markdown_sync_llm(
                    updated_markdown,
                    issues,
                    recommendations,
                    updated_json
                )
                applied_fixes.extend(text_fixes)
            else:
                applied_fixes.append("[텍스트 보완] LLM 없음 - 스킵")

            return {
                "refined_markdown": updated_markdown,
                "refined_json": updated_json,
                "applied_fixes": applied_fixes,
                "status": "completed"
            }

        except Exception as e:
            logger.error("[RefinerAgent] 오류 발생 (동기)", exc_info=True)
            return {
                "status": "failed",
                "error": str(e),
                "updated_markdown": draft_markdown,
                "updated_json": draft_json,
                "applied_fixes": []
            }

    # ============================================================
    # LangGraph async entrypoint
    # ============================================================
    async def refine(
        self,
        draft_markdown: str,
        draft_json: Dict[str, Any],
        validation_results: Dict[str, Any]
    ) -> Dict[str, Any]:

        logger.info("[RefinerAgent] 개선 시작 (비동기)")

        try:
            issues = validation_results.get("issues", [])
            recommendations = validation_results.get("recommendations", [])

            updated_json = copy.deepcopy(draft_json)
            updated_markdown = draft_markdown
            applied_fixes: List[str] = []

            structural_fixes = self._fix_json_structure(updated_json)
            applied_fixes.extend(structural_fixes)

            content_fixes = self._fix_json_content(updated_json, issues)
            applied_fixes.extend(content_fixes)

            text_fixes, updated_markdown = await self._refine_markdown_llm(
                updated_markdown,
                issues,
                recommendations,
                updated_json
            )
            applied_fixes.extend(text_fixes)

            tcfd_fixes, updated_markdown = self._ensure_tcfd_alignment(
                updated_markdown
            )
            applied_fixes.extend(tcfd_fixes)

            return {
                "refined_markdown": updated_markdown,
                "refined_json": updated_json,
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
    # 2) JSON 내용 보완
    # ============================================================
    def _fix_json_content(self, json_data: Dict[str, Any], issues: List[Dict[str, str]]) -> List[str]:
        fixes = []

        if not json_data.get("executive_summary") or len(json_data["executive_summary"]) < 20:
            json_data["executive_summary"] = (
                "본 보고서는 주요 환경 리스크 분석 결과와 이에 기반한 대응 전략을 요약하여 제공합니다."
            )
            fixes.append("[내용 보완] Executive Summary 자동 보강")

        st = json_data.get("sections", {}).get("strategy", "")
        if not st or len(st) < 30:
            json_data["sections"]["strategy"] = (
                "식별된 주요 리스크에 따라 회사는 예방, 대비, 완화 전략을 포함한 통합 리스크 대응 체계를 수립했습니다."
            )
            fixes.append("[내용 보완] Strategy 섹션 자동 보강")

        return fixes

    # ============================================================
    # 3) Markdown 텍스트 보완 (LLM) - 동기 버전
    # ============================================================
    def _refine_markdown_sync_llm(
        self,
        markdown: str,
        issues: List[Dict[str, str]],
        recommendations: List[str],
        json_data: Dict[str, Any]
    ) -> Tuple[List[str], str]:

        if not issues:
            return [], markdown

        issues_json = json.dumps(issues, indent=2, ensure_ascii=False)
        recommendations_json = json.dumps(recommendations, indent=2, ensure_ascii=False)
        current_json_data_json = json.dumps(json_data, indent=2, ensure_ascii=False)

        prompt = f"""
    <ROLE>
    You are a highly skilled professional editor and content specialist responsible for ensuring the top quality of TCFD and ESG reports. Your mission is to meticulously refine draft reports based on identified issues and recommendations, preserving the original intent while enhancing clarity, conciseness, and factual accuracy. You excel at correcting factual errors (`factual_error`) and filling in omitted (`omission`) information based on provided source data.
    </ROLE>

    <CONTEXT>
    You have been provided with a draft report, a structured list of identified issues (including their types and messages), specific recommendations, and the complete underlying JSON data that represents the report's content.

    <REPORT_DRAFT>
    {markdown}
    </REPORT_DRAFT>

    <ISSUES_IDENTIFIED>
    {issues_json}
    </ISSUES_IDENTIFIED>

    <RECOMMENDATIONS>
    {recommendations_json}
    </RECOMMENDATIONS>

    <CURRENT_JSON_DATA>
    {current_json_data_json}
    </CURRENT_JSON_DATA>
    </CONTEXT>

    <INSTRUCTIONS>
    Your task is to revise the <REPORT_DRAFT> to resolve all issues identified in <ISSUES_IDENTIFIED> and incorporate the <RECOMMENDATIONS>.

    Follow these logical steps for the refinement process:

    <THOUGHT_PROCESS>
    - Analyze Issues: Carefully review each issue in <ISSUES_IDENTIFIED>. Pay special attention to the 'type' of each issue. Prioritize critical errors like `factual_error` and `omission` over stylistic ones like `text` or `readability`.
    - Refer Context for Factual Issues: When addressing an issue of type `factual_error`, `omission`, or `inconsistency`, you MUST refer to the <CURRENT_JSON_DATA> to find the correct factual information (e.g., numbers, specific details) and incorporate it into the draft.
    - Plan Corrections: For each issue, determine the most effective and least intrusive way to correct the <REPORT_DRAFT> while preserving its original intent. For example, for a `factual_error`, replace the incorrect number; for an `omission`, add the missing sentence; for a `text` error, rephrase the sentence for clarity.
    - Apply Markdown Refinement: Systematically apply the planned corrections to the <REPORT_DRAFT>.
    - Verify Markdown Syntax: After all modifications, ensure the final output's Markdown syntax is valid and well-formed.
    </THOUGHT_PROCESS>

    Based on this thought process, output the fully refined Markdown text for the report.
    </INSTRUCTIONS>

    <OUTPUT_FORMAT>
    - Output ONLY the fully revised Markdown text of the report.
    - The output must be valid Markdown.
    </OUTPUT_FORMAT>

    <RULES>
    - Output ONLY the refined Markdown text. DO NOT include any explanations, apologies, or text outside the revised Markdown.
    - DO NOT alter the original intent or core message of the report. Focus strictly on correcting the identified issues.
    - Avoid unnecessary rewriting or stylistic changes to parts of the report that are not explicitly identified as problematic.
    - Ensure strict adherence to Markdown syntax in the revised output.
    - The output language must be Korean.
    </RULES>
    """

        try:
            refined = self.llm.invoke(prompt)
            if isinstance(refined, str):
                return ["[텍스트 보완] LLM 기반 Markdown 개선 수행"], refined
            else:
                refined_text = getattr(refined, 'content', str(refined))
                return ["[텍스트 보완] LLM 기반 Markdown 개선 수행"], refined_text
        except Exception as e:
            logger.warning(f"[RefinerAgent] LLM Markdown 개선 실패: {e}")
            return [f"[텍스트 보완] LLM 호출 실패: {e}"], markdown


    async def _refine_markdown_llm(
        self,
        markdown: str,
        issues: List[Dict[str, str]],
        recommendations: List[str],
        json_data: Dict[str, Any]
    ) -> Tuple[List[str], str]:

        if not issues:
            return [], markdown

        issues_json = json.dumps(issues, indent=2, ensure_ascii=False)
        recommendations_json = json.dumps(recommendations, indent=2, ensure_ascii=False)
        current_json_data_json = json.dumps(json_data, indent=2, ensure_ascii=False)

        prompt = f"""
    <ROLE>
    You are a highly skilled professional editor and content specialist responsible for ensuring the top quality of TCFD and ESG reports. Your mission is to meticulously refine draft reports based on identified issues and recommendations, preserving the original intent while enhancing clarity, conciseness, and factual accuracy. You excel at correcting factual errors (`factual_error`) and filling in omitted (`omission`) information based on provided source data.
    </ROLE>

    <CONTEXT>
    You have been provided with a draft report, a structured list of identified issues (including their types and messages), specific recommendations, and the complete underlying JSON data that represents the report's content.

    <REPORT_DRAFT>
    {markdown}
    </REPORT_DRAFT>

    <ISSUES_IDENTIFIED>
    {issues_json}
    </ISSUES_IDENTIFIED>

    <RECOMMENDATIONS>
    {recommendations_json}
    </RECOMMENDATIONS>

    <CURRENT_JSON_DATA>
    {current_json_data_json}
    </CURRENT_JSON_DATA>
    </CONTEXT>

    <INSTRUCTIONS>
    Your task is to revise the <REPORT_DRAFT> to resolve all issues identified in <ISSUES_IDENTIFIED> and incorporate the <RECOMMENDATIONS>.

    Follow these logical steps for the refinement process:

    <THOUGHT_PROCESS>
    1. **Analyze Issues**: Carefully review each issue in <ISSUES_IDENTIFIED>. Pay special attention to the 'type' of each issue. Prioritize critical errors like `factual_error` and `omission` over stylistic ones like `text` or `readability`.
    2. **Refer Context for Factual Issues**: When addressing an issue of type `factual_error`, `omission`, or `inconsistency`, you MUST refer to the <CURRENT_JSON_DATA> to find the correct factual information (e.g., numbers, specific details) and incorporate it into the draft.
    3. **Plan Corrections**: For each issue, determine the most effective and least intrusive way to correct the <REPORT_DRAFT> while preserving its original intent.
    4. **Apply Markdown Refinement**: Systematically apply the planned corrections to the <REPORT_DRAFT>.
    5. **Verify Markdown Syntax**: Ensure the final output's Markdown syntax is valid and well-formed.
    </THOUGHT_PROCESS>

    Based on this thought process, output the fully refined Markdown text for the report.
    </INSTRUCTIONS>

    <OUTPUT_FORMAT>
    - Output ONLY the fully revised Markdown text of the report.
    - The output must be valid Markdown.
    </OUTPUT_FORMAT>

    <RULES>
    - Output ONLY the refined Markdown text. DO NOT include any explanations, apologies, or text outside the revised Markdown.
    - DO NOT alter the original intent or core message of the report.
    - Avoid unnecessary rewriting or stylistic changes not explicitly identified as problematic.
    - Ensure strict adherence to Markdown syntax.
    - The output language must be Korean.
    </RULES>
    """

        refined = await self.llm.ainvoke(prompt)
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
