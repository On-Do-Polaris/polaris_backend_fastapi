# strategy_generation_agent_3.py
"""
파일명: strategy_generation_agent_3.py
최종 수정일: 2025-11-24
버전: v03

파일 개요:
    - LangGraph StrategyGeneration Node용 대응 전략 생성 Agent
    - 입력: report_profile, impact_analysis_result, vulnerability_analysis, AAL, physical_risk_scores
    - 출력: risk_specific_strategies, overall_strategy, recommendations, priority_actions, citations
    - RAG 기반 사례 검색 + LLM 기반 전략 생성

주요 기능:
    1. 상위 물리적 리스크 선정 (ImpactScore + AAL)
    2. RAG 기반 유사 사례 검색 (Graph RAG)
    3. LLM 기반 전략 생성
       - 종합 전략(overall_strategy)
       - 리스크별 전략(risk_specific_strategies)
       - 권고사항, 우선 조치
    4. citations 생성 및 정리
    5. Memory Node용 output 구성 (strategies[], citations[])

Refiner 루프 연계:
    - Strategy Issue 발생 시 route: strategy
    - LLM 재호출로 strategies[] + citations 재생성

변경 이력:
    - v01 (2025-11-14): 초안 작성, 물리적 리스크별 대응 전략 생성
    - v02 (2025-11-21): RAG + LLM 구조로 리팩토링, citations 포함
    - v03 (2025-11-24): 최신 LangGraph 아키텍처 반영, Memory Node/Refiner 루프 연계
"""

from typing import Dict, Any, List
import logging
from utils.rag_helpers import RAGEngine
from utils.citation_formatter import format_citations

logger = logging.getLogger("StrategyGenerationAgent")

class StrategyGenerationAgent:
    """
    대응 전략 생성 Agent (RAG + LLM 기반)
    - LangGraph StrategyGeneration Node에서 실행
    - ImpactAnalysisAgent 출력에 기반하여 전략 생성
    - Memory Node 저장용: strategies[], citations
    """

    def __init__(self, llm_client, rag_engine: RAGEngine):
        """
        Args:
            llm_client: async LLM 호출 클라이언트
            rag_engine: Graph RAG Engine
        """
        self.llm_client = llm_client
        self.rag_engine = rag_engine
        logger.info("[StrategyGenerationAgent] 초기화 완료")

    # -------------------------------------------------------
    # PUBLIC: 노드 실행 엔트리
    # -------------------------------------------------------
    async def run(
        self,
        report_profile: Dict[str, Any],
        impact_analysis: Dict[str, Any],
        vulnerability_analysis: Dict[str, Any],
        aal_analysis: Dict[str, Any],
        physical_risk_scores: Dict[str, Any],
        target_location: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        LangGraph Node 호출용 전략 생성 메인

        Returns:
            {
                overall_strategy,
                risk_specific_strategies,
                recommendations,
                priority_actions,
                top_risks,
                citations,
                status
            }
        """
        logger.info("[StrategyGenerationAgent] 전략 생성 시작")
        try:
            # 1) 상위 리스크 선정
            top_risks = self._identify_top_risks(physical_risk_scores, aal_analysis)

            # 2) RAG 기반 유사 사례 검색
            similar_cases = await self._retrieve_similar_cases(top_risks, vulnerability_analysis)

            # 3) 종합 전략 생성
            overall_strategy = await self._generate_overall_strategy(
                target_location, top_risks, vulnerability_analysis, similar_cases
            )

            # 4) 리스크별 전략 생성
            risk_strategies = await self._generate_risk_specific_strategies(
                top_risks, aal_analysis, similar_cases
            )

            # 5) 권고사항
            recommendations = self._generate_recommendations(vulnerability_analysis, top_risks, aal_analysis)

            # 6) 우선 조치
            priority_actions = self._define_priority_actions(top_risks, vulnerability_analysis)

            # 7) citations 생성
            citations = self._generate_citations(similar_cases)

            logger.info("[StrategyGenerationAgent] 전략 생성 완료")

            return {
                "overall_strategy": overall_strategy,
                "risk_specific_strategies": risk_strategies,
                "recommendations": recommendations,
                "priority_actions": priority_actions,
                "top_risks": top_risks,
                "citations": citations,
                "status": "completed"
            }

        except Exception as e:
            logger.error(f"[StrategyGenerationAgent] 전략 생성 실패: {e}", exc_info=True)
            return {"status": "failed", "error": str(e)}

    # -------------------------------------------------------
    # INTERNAL METHODS
    # -------------------------------------------------------
    def _identify_top_risks(self, physical_risk_scores: Dict[str, Any], aal_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        상위 물리적 리스크 선정
        - 점수 + AAL 재무손실 기반
        - LangGraph Memory Node용 top_risks 반환
        """
        ranked = []
        for risk_type, risk_data in physical_risk_scores.items():
            score_100 = risk_data.get("physical_risk_score_100", 0)
            financial_loss = aal_analysis.get(risk_type, {}).get("financial_loss", 0)
            combined_score = score_100 * 0.6 + min(financial_loss / 1e9, 100) * 0.4
            ranked.append({
                "risk_type": risk_type,
                "risk_score": score_100,
                "financial_loss": financial_loss,
                "combined_score": combined_score
            })
        ranked.sort(key=lambda x: x["combined_score"], reverse=True)
        return ranked[:5]

    async def _retrieve_similar_cases(self, top_risks: List[Dict[str, Any]], vulnerability_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Graph RAG 기반 유사 사례 검색
        """
        risk_names = [r["risk_type"] for r in top_risks]
        vuln_score = vulnerability_analysis.get("overall_vulnerability_score", 0)
        query = f"리스크 유형: {risk_names}, 취약성 점수: {vuln_score:.2f}"
        return self.rag_engine.query(query, top_k=3)

    async def _generate_overall_strategy(self, target_location: Dict[str, Any], top_risks: List[Dict[str, Any]], vulnerability_analysis: Dict[str, Any], similar_cases: List[Dict[str, Any]]) -> str:
        """
        LLM 기반 종합 대응 전략 생성
        """
        location = target_location.get("name", "대상 지역 미확인")
        risk_list = ", ".join([r["risk_type"] for r in top_risks])
        vuln_score = vulnerability_analysis.get("overall_vulnerability_score", 0)

        prompt = f"""
다음 정보를 바탕으로 종합 대응 전략을 작성하세요.

대상 지역: {location}
상위 리스크: {risk_list}
취약성 점수: {vuln_score:.2f}

유사 사례:
{similar_cases}

요구사항:
- 3~5문장
- 정책적, 기술적 대응 전략 포함
- ESG/TCFD 맥락 반영
"""
        return await self.llm_client.ainvoke(prompt)

    async def _generate_risk_specific_strategies(self, top_risks: List[Dict[str, Any]], aal_analysis: Dict[str, Any], similar_cases: List[Dict[str, Any]]) -> Dict[str, str]:
        """
        LLM 기반 리스크별 대응 전략 생성
        - Memory Node용 risk_specific_strategies 반환
        """
        strategies = {}
        for r in top_risks:
            risk_type = r["risk_type"]
            aal_data = aal_analysis.get(risk_type, {})
            prompt = f"""
리스크 유형: {risk_type}
예상 재무 손실: {aal_data.get('financial_loss', 0):,.0f}원
AAL: {aal_data.get('aal_percentage', 0):.2f}%

유사 사례 기반 리스크 대응 전략을 2~3문장으로 만드세요.
"""
            strategies[risk_type] = await self.llm_client.ainvoke(prompt)
        return strategies

    def _generate_recommendations(self, vulnerability_analysis: Dict[str, Any], top_risks: List[Dict[str, Any]], aal_analysis: Dict[str, Any]) -> List[str]:
        """
        표준 권고사항 목록
        """
        base = [
            "기후 리스크 모니터링 체계 강화",
            "시설 취약성 개선(내풍·내수·내한 설계 보완)",
            "정기적 기후 시나리오 분석 수행",
            "비상 대응 매뉴얼 업데이트 및 직원 교육",
            "보험 커버리지 확대 검토"
        ]
        return base

    def _define_priority_actions(self, top_risks: List[Dict[str, Any]], vulnerability_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        우선 순위 조치 정의
        """
        actions = []
        if top_risks:
            top_risk = top_risks[0]
            actions.append({
                "priority": 1,
                "action": f"{top_risk['risk_type']} 대응 역량 강화 조치",
                "timeline": "1개월"
            })
        if vulnerability_analysis.get("overall_vulnerability_score", 0) > 0.6:
            actions.append({
                "priority": 2,
                "action": "건물 취약성 개선 공사(단열·내풍·배수 등)",
                "timeline": "3~6개월"
            })
        actions.append({
            "priority": 3,
            "action": "기후 리스크 통합 모니터링 시스템 도입",
            "timeline": "3개월"
        })
        return actions

    def _generate_citations(self, similar_cases: List[Dict[str, Any]]) -> List[str]:
        """
        RAG 검색 결과 기반 citations 생성
        - Memory Node용 citations 저장
        """
        citations = []
        for c in similar_cases:
            if "source" in c:
                citations.append(f"{c.get('title','사례')} - {c['source']}")
        return citations[:5]
