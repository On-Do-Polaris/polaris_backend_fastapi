# validation_agent_5.py
"""
파일명: validation_agent_5.py
최종 수정일: 2025-12-01
버전: v06

파일 개요:
    - 보고서 품질 검증 Agent (ValidationAgent)
    - LLM-as-Judge 기반 Accuracy / Consistency / Completeness / TCFD Alignment 평가
    - Refiner 루프(6번)에서 사용할 issue flags와 score를 반환
    - Memory Node 연동을 위한 validation_metadata 구조 포함

주요 기능:
    1. 데이터 정확성 검증 (Impact Summary ↔ Draft)
    2. 전략 적용 검증 (Strategy Agent 결과와 Draft 비교)
    3. 섹션 완전성 검증 (필수 Section, 템플릿 구조)
    4. TCFD Alignment 정합성 점수 산정
    5. citation 누락/오류 검증
    6. 종합 score 계산 및 issue 분류(type: data/strategy/text/tcfd/structure)      
    7. Refiner Agent 재호출을 위한 판단 근거 생성
    8. **LLM Judge를 통한 사실 확인 및 데이터 일관성 검증 추가**

변경 이력:
    - v01 (2025-11-14): 기본 구조 작성
    - v02 (2025-11-21): async / JSON Schema / TCFD 점수화 추가
    - v03 (2025-11-24): Memory Node 인터페이스 정비
    - v04 (2025-11-24, 최신):
        * issue 유형 세분화 (data/strategy/text/structure/tcfd/citation)
        * citation 누락 검증 추가
        * Cross consistency (impact ↔ strategy ↔ report) 검증 강화
        * score 가중치 방식으로 개선
        * Refiner 라우팅에서 직접 사용 가능한 issue payload 구조 제공
    - v05 (2025-12-01): 프롬프트 구조 개선
    - v06 (2025-12-01): LLM Judge 사실 확인 기능 및 프롬프트 최종 적용
"""

import json
from typing import Dict, Any, List, Tuple
import logging

logger = logging.getLogger("ValidationAgent")


class ValidationAgent:
    """
    Validation Agent
    - draft_markdown / draft_json 평가
    - issue 구조는 Refiner Agent(6번) 라우팅 규칙에 최적화되어 있음
    """

    def __init__(self, llm_client=None):
        self.llm = llm_client
        logger.info("[ValidationAgent] 초기화 완료")

    # ============================================================
    # LangGraph ENTRYPOINT
    # ============================================================
    async def validate(
        self,
        draft_markdown: str,
        draft_json: Dict[str, Any],
        report_profile: Dict[str, Any],
        impact_summary: Dict[str, Any],
        strategies: List[Dict[str, Any]],  # <<-- 수정됨: Dict에서 List[Dict]로
        citations: List[Dict[str, Any]] = None
    ) -> Dict[str, Any]:

        logger.info("[ValidationAgent] 검증 시작")

        try:
            all_issues: List[Dict[str, str]] = []

            # 1. Accuracy 검증
            acc_score, acc_issues = await self._check_accuracy(
                draft_json, impact_summary, strategies
            )
            all_issues.extend(acc_issues)

            # 2. Consistency 검증
            con_score, con_issues = await self._check_consistency(
                draft_json, strategies
            )
            all_issues.extend(con_issues)

            # 3. Completeness 검증
            comp_score, comp_issues = await self._check_completeness(draft_json)
            all_issues.extend(comp_issues)

            # 4. Citation 검증
            cit_score, cit_issues = await self._check_citations(
                draft_markdown, citations
            )
            all_issues.extend(cit_issues)

            # 5. TCFD Alignment
            tcfd_score, tcfd_issues = await self._check_tcfd_alignment(draft_markdown)
            all_issues.extend(tcfd_issues)

            # 6. LLM-as-Judge 미세조정 (선택) - 사실 확인 기능 강화
            judge_issues = []
            judge_score = 1.0
            if self.llm:
                judge_score, judge_issues = await self._llm_judge(
                    draft_markdown,
                    impact_summary,
                    strategies
                )
                all_issues.extend(judge_issues)

            # 7. 최종 score 계산
            score = self._compute_score(
                acc_score, con_score, comp_score, cit_score, tcfd_score, judge_score
            )

            # 8. 개선 권고 생성
            recommendations = self._generate_recommendations(all_issues)

            return {
                "status": "completed",
                "score": score,
                "issues": all_issues,
                "recommendations": recommendations,
                "passed": score >= 0.70,
                "validation_metadata": {
                    "accuracy": acc_score,
                    "consistency": con_score,
                    "completeness": comp_score,
                    "citation": cit_score,
                    "tcfd": tcfd_score,
                    "judge": judge_score,
                }
            }

        except Exception as e:
            logger.error("[ValidationAgent] 검증 중 오류 발생", exc_info=True)
            return {"status": "failed", "error": str(e)}

    # ============================================================
    # 1. Accuracy 검증 (Impact ↔ Strategy ↔ Report)
    # ============================================================
    async def _check_accuracy(
        self,
        draft_json: Dict[str, Any],
        impact_summary: Dict[str, Any],
        strategies: List[Dict[str, Any]]  # <<-- 수정됨: Dict에서 List[Dict]로
    ) -> Tuple[float, List[Dict[str, str]]]:

        issues = []
        score = 1.0

        # (A) 주요 리스크 반영 여부
        top_risks = impact_summary.get("top_risks", [])
        risk_names = {r["risk_type"] for r in top_risks}
        report_text = draft_json.get("sections", {}).get("risk_overview", "")

        for r in risk_names:
            if r not in report_text:
                issues.append({
                    "type": "data",
                    "msg": f"주요 리스크 '{r}'가 보고서에 반영되지 않음"
                })
                score -= 0.1

        # (B) 총 예상 재무손실 반영 여부
        summary_text = draft_json.get("executive_summary", "")
        total_loss = impact_summary.get("total_financial_loss")
        if total_loss and str(total_loss) not in summary_text:
            issues.append({
                "type": "data",
                "msg": "총 예상 재무손실(total_financial_loss)이 Executive Summary에 없음"
            })
            score -= 0.1

        return max(score, 0), issues

    # ============================================================
    # 2. Consistency 검증 (전략 ↔ 전략 섹션)
    # ============================================================
    async def _check_consistency(
        self,
        draft_json: Dict[str, Any],
        strategies: List[Dict[str, Any]]
    ) -> Tuple[float, List[Dict[str, str]]]:

        issues = []
        score = 1.0

        strategy_section = draft_json.get("sections", {}).get("strategy", "")

        # strategies가 List[Dict]일 경우 Dict로 변환
        if isinstance(strategies, list):
            strategies_dict = {}
            for strategy in strategies:
                if isinstance(strategy, dict):
                    risk = strategy.get('risk', 'unknown')
                    strategies_dict[risk] = strategy.get('strategy', '')
            strategies = strategies_dict

        # Dict인 경우에만 items() 호출
        if isinstance(strategies, dict):
            for key, text in strategies.items():
                if isinstance(text, str) and text[:40] not in strategy_section:
                    issues.append({
                        "type": "strategy",
                        "msg": f"전략 '{key}' 내용이 전략 섹션에 충분히 반영되지 않음"
                    })
                    score -= 0.1

        return max(score, 0), issues

    # ============================================================
    # 3. Completeness 검증
    # ============================================================
    async def _check_completeness(self, draft_json: Dict[str, Any]) -> Tuple[float, List[Dict[str, str]]]:

        issues = []
        score = 1.0

        required = ["executive_summary", "sections"]
        for sec in required:
            if sec not in draft_json or not draft_json[sec]:
                issues.append({
                    "type": "structure",
                    "msg": f"필수 섹션 '{sec}' 누락"
                })
                score -= 0.2

        if "sections" in draft_json and len(draft_json["sections"]) < 3:
            issues.append({
                "type": "structure",
                "msg": "sections 내 하위 섹션 수가 부족 (최소 3개 필요)"
            })
            score -= 0.1

        return max(score, 0), issues

    # ============================================================
    # 4. Citation 검증
    # ============================================================
    async def _check_citations(
        self,
        markdown: str,
        citations: List[Dict[str, Any]]
    ) -> Tuple[float, List[Dict[str, str]]]:

        if citations is None:
            return 1.0, []

        issues = []
        score = 1.0

        for c in citations:
            ref_id = c.get("ref_id")
            if ref_id not in markdown:
                issues.append({
                    "type": "citation",
                    "msg": f"citation '{ref_id}'가 본문에 존재하지 않음"
                })
                score -= 0.05

        return max(score, 0), issues

    # ============================================================
    # 5. TCFD Alignment 검증
    # ============================================================
    async def _check_tcfd_alignment(self, markdown: str) -> Tuple[float, List[Dict[str, str]]]:

        score = 1.0
        issues = []

        required = ["Governance", "Strategy", "Risk Management", "Metrics", "Targets"]
        for kw in required:
            if kw.lower() not in markdown.lower():
                issues.append({
                    "type": "tcfd",
                    "msg": f"TCFD 요소 '{kw}' 부족"
                })
                score -= 0.1

        return max(score, 0), issues

    # ============================================================
    # 6. LLM Judge (선택) - 강화된 버전: 품질 및 사실 관계 검증
    # ============================================================
    async def _llm_judge(self, markdown: str, impact_summary: Dict, strategies: List[Dict]) -> Tuple[float, List[Dict[str, str]]]:

        if not self.llm:
            return 1.0, []

        prompt = f"""
<ROLE>
You are an independent and highly critical Report Auditor and Fact-Checker, specializing in ensuring the highest quality and factual accuracy of TCFD and ESG reports. Your dual role is:
1.  **Quality Judge**: Rigorously evaluate the draft report for logical consistency, adherence to TCFD guidelines, readability, and professional presentation.
2.  **Fact-Checker**: Meticulously verify that all claims, figures, and summaries in the report draft are perfectly consistent with the provided source data. There is no room for error, omission, or exaggeration.
</ROLE>

<CONTEXT>
You have been provided with a draft report AND the original source data used to create it.

<SOURCE_IMPACT_DATA>
{json.dumps(impact_summary, indent=2, ensure_ascii=False)}
</SOURCE_IMPACT_DATA>

<SOURCE_STRATEGIES_DATA>
{json.dumps(strategies, indent=2, ensure_ascii=False)}
</SOURCE_STRATEGIES_DATA>

<REPORT_DRAFT_TO_VALIDATE>
{markdown}
</REPORT_DRAFT_TO_VALIDATE>
</CONTEXT>

<INSTRUCTIONS>
Your primary task is to critically evaluate the <REPORT_DRAFT_TO_VALIDATE> against the <SOURCE_IMPACT_DATA> and <SOURCE_STRATEGIES_DATA>.
1.  **Fact-Check**: Cross-reference the draft against the source data. Identify any inconsistencies, factual errors, omissions, or exaggerations.
2.  **Quality-Check**: Assess the overall quality of the writing, structure, and adherence to professional standards.
3.  **Assign Score**: Based on both checks, assign an overall quality score between 0.0 and 1.0.
4.  **List Issues**: Detail all identified issues in the specified JSON format.
</INSTRUCTIONS>

<OUTPUT_FORMAT>
- Output ONLY a single, raw JSON object.
- The JSON object must have the following structure:
  {{
    "score": float,
    "issues": [
      {{
        "type": "string",
        "msg": "string"
      }}
    ]
  }}
</OUTPUT_FORMAT>

<RULES>
- Output ONLY a single raw JSON object. DO NOT include any text outside the JSON object.
- Be extremely critical.
- Every claim in the draft must be traceable to the source data.
- For factual_error, specify incorrect and correct values.
- The output must be valid JSON.
</RULES>

JSON_ONLY:
"""

        resp_raw = await self.llm.ainvoke(prompt)

        try:
            resp = json.loads(resp_raw)
            score = resp.get("score", 0.0)
            issues_list = resp.get("issues", [])
        except (json.JSONDecodeError, AttributeError):
            logger.error(f"LLM Judge response parsing failed: {resp_raw}")
            score = 0.0
            issues_list = [{"type": "system_error", "msg": "LLM Judge output could not be parsed."}]

        formatted_issues = [{"type": i.get("type", "unknown"), "msg": i.get("msg", str(i))} for i in issues_list]
        return score, formatted_issues

    # ============================================================
    # Score 계산
    # ============================================================
    def _compute_score(
        self,
        acc: float, con: float, comp: float,
        cit: float, tcfd: float, judge: float
    ) -> float:

        weights = {
            "accuracy": 0.22,
            "consistency": 0.20,
            "completeness": 0.18,
            "citation": 0.10,
            "tcfd": 0.20,
            "judge": 0.10
        }

        score = (
            acc * weights["accuracy"]
            + con * weights["consistency"]
            + comp * weights["completeness"]
            + cit * weights["citation"]
            + tcfd * weights["tcfd"]
            + judge * weights["judge"]
        )

        return round(score, 3)

    # ============================================================
    # Recommendation 생성
    # ============================================================
    def _generate_recommendations(self, issues: List[Dict[str, str]]) -> List[str]:
        recs = []
        for i in issues:
            msg = i["msg"]
            recs.append(f"개선 제안: {msg}을(를) 보완하세요.")
        return recs
