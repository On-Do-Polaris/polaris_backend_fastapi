# validation_agent_5.py
"""
파일명: validation_agent_5.py
최종 수정일: 2025-11-24
버전: v03

파일 개요:
    - 보고서 검증 Agent
    - Accuracy / Consistency / Completeness / TCFD Alignment 평가
    - Refiner 루프용 issue, recommendations, score 제공
    - Memory Node: validation_history 저장 가능

주요 기능:
    1. Executive Summary / Sections 정확성 검증
    2. Draft 내 전략 반영 여부 확인
    3. 필수 섹션 및 문단 완전성 검증
    4. TCFD Alignment 확인
    5. 종합 score 계산 (0~1)
    6. Refiner Node 판단 기준 제공
    7. JSON 구조 출력

Refiner 루프 연계:
    - score < 0.7 → RefinerAgent route 결정
        - Data Issue → 2_ImpactAnalysisAgent
        - Strategy Issue → 3_StrategyGenerationAgent
        - Text Issue → 4_ReportComposerAgent

변경 이력:
    - v01 (2025-11-14): 초안
        * LangGraph 기반 검증 노드 구조 정의
        * Executive Summary / Strategy / Sections 검증 기능 초기 구현
    - v02 (2025-11-21):
        * async 지원, LLM 호출 가능하도록 구조 개선
        * JSON 스키마화 (score, issues, recommendations, passed, status)
        * 예외 처리 강화
    - v03 (2025-11-24, 최신):
        * Memory Node 활용 가능하도록 validation 결과 구조화
        * Refiner 루프 연계 (score 기반 routing)
        * TCFD Alignment 점수 0~1 반영 및 종합 score 계산
        * 권고사항 recommendations 생성 로직 개선
        * 로그 메시지 통일화 및 상태 출력 명확화
"""

from typing import Dict, Any, List, Tuple
import logging

logger = logging.getLogger("ValidationAgent")


class ValidationAgent:
    """
    리포트 검증 Agent
    - draft_markdown / draft_json 기반 검증
    - Memory Node에 validation_history 저장 가능
    """

    def __init__(self, llm_client):
        self.llm = llm_client
        logger.info("[ValidationAgent] 초기화 완료")

    # ============================================================
    # LangGraph Node async 진입점
    # ============================================================
    async def validate(
        self,
        draft_markdown: str,
        draft_json: Dict[str, Any],
        report_profile: Dict[str, Any],
        impact_summary: Dict[str, Any],
        strategies: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        검증 수행
        Returns:
            {
                score: float,
                issues: List[str],
                recommendations: List[str],
                passed: bool,
                status: str
            }
        """
        logger.info("[ValidationAgent] 검증 시작")
        try:
            # 1. 정확성 검증
            acc_passed, acc_issues = await self._check_accuracy(draft_json, impact_summary, strategies)

            # 2. 일관성 검증
            con_passed, con_issues = await self._check_consistency(draft_json, strategies)

            # 3. 완전성 검증
            comp_passed, comp_issues = await self._check_completeness(draft_json)

            # 4. TCFD Alignment
            tcfd_score, tcfd_issues = await self._check_tcfd_alignment(draft_markdown)

            # 5. 종합 Issue + score + recommendations
            issues = acc_issues + con_issues + comp_issues + tcfd_issues
            score = self._compute_score(acc_passed, con_passed, comp_passed, tcfd_score)
            recs = self._generate_recommendations(issues)

            return {
                "score": score,
                "issues": issues,
                "recommendations": recs,
                "passed": score >= 0.7,
                "status": "completed"
            }

        except Exception as e:
            logger.error("[ValidationAgent] 검증 중 오류 발생", exc_info=True)
            return {"status": "failed", "error": str(e)}

    # ============================================================
    # Internal Methods
    # ============================================================
    async def _check_accuracy(
        self,
        draft_json: Dict[str, Any],
        impact_summary: Dict[str, Any],
        strategies: Dict[str, Any]
    ) -> Tuple[bool, List[str]]:
        """
        Executive Summary 및 Sections 정확성 확인
        """
        issues = []

        # Top Risks consistency
        reported_top = draft_json.get("sections", {}).get("risk_overview", "")
        true_top = impact_summary.get("top_risks", [])
        if true_top:
            true_names = {r["risk_type"] for r in true_top}
            for risk in true_names:
                if risk not in reported_top:
                    issues.append(f"정확성 오류: 주요 리스크 '{risk}'가 보고서 요약에 반영되지 않음")

        # 총 예상 재무손실 반영 확인
        draft_summary = draft_json.get("executive_summary", "")
        expected_loss = impact_summary.get("total_financial_loss")
        if expected_loss and str(expected_loss) not in draft_summary:
            issues.append("정확성 오류: 총 예상 재무손실 값이 Executive Summary에 반영되지 않음")

        # 핵심 전략 반영 여부
        strategy_main = strategies.get("overall_strategy", "")
        if strategy_main and strategy_main not in draft_summary:
            issues.append("정확성 오류: 핵심 대응 전략이 요약문에 반영되지 않음")

        return len(issues) == 0, issues

    async def _check_consistency(
        self,
        draft_json: Dict[str, Any],
        strategies: Dict[str, Any]
    ) -> Tuple[bool, List[str]]:
        """
        전략 / 리스크 일관성 확인
        """
        issues = []
        sec = draft_json.get("sections", {})

        if "strategy" in sec:
            strategy_text = sec["strategy"]
            for k, v in strategies.items():
                if isinstance(v, str) and len(v) > 50:
                    if v[:40] not in strategy_text:
                        issues.append(f"일관성 오류: 전략 '{k}'가 문서 전략 섹션에 충분히 반영되지 않음")
        return len(issues) == 0, issues

    async def _check_completeness(
        self,
        draft_json: Dict[str, Any]
    ) -> Tuple[bool, List[str]]:
        """
        필수 섹션 및 문단 존재 확인
        """
        required_sections = ["executive_summary", "sections"]
        issues = []

        for sec in required_sections:
            if sec not in draft_json or not draft_json[sec]:
                issues.append(f"완전성 오류: '{sec}' 섹션 누락 또는 비어있음")

        if "sections" in draft_json and len(draft_json["sections"].keys()) < 3:
            issues.append("완전성 오류: 섹션 수가 너무 적음 (최소 3개 이상 필요)")

        return len(issues) == 0, issues

    async def _check_tcfd_alignment(self, markdown: str) -> Tuple[float, List[str]]:
        """
        TCFD Alignment 점검
        """
        issues = []
        score = 1.0
        required_keywords = ["Governance", "Strategy", "Risk Management", "Metrics", "Targets"]
        for kw in required_keywords:
            if kw.lower() not in markdown.lower():
                score -= 0.1
                issues.append(f"TCFD 기준 부족: '{kw}' 관련 내용 부족")
        return score, issues

    def _compute_score(self, acc: bool, con: bool, comp: bool, tcfd_score: float) -> float:
        """
        종합 score 계산 (0~1)
        """
        base = 0
        base += 0.25 if acc else 0
        base += 0.25 if con else 0
        base += 0.25 if comp else 0
        base += 0.25 * tcfd_score
        return round(base, 3)

    def _generate_recommendations(self, issues: List[str]) -> List[str]:
        """
        각 Issue 기반 개선 권고문 생성
        """
        return [f"개선 제안: {i.replace('오류:', '').strip()}을(를) 보완하세요." for i in issues]
