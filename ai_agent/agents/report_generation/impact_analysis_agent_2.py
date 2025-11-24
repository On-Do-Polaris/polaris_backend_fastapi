# impact_analysis_agent_2.py
"""
파일명: impact_analysis_agent_2.py
최종 수정일: 2025-11-24
버전: v04

파일 개요:
    - 물리적 기후 리스크 영향 분석 Agent
    - Physical Risk Scores, AAL, 취약성 데이터 기반 영향 분석 수행
    - Impact List 표준 스키마 적용
    - 향후 Strategy Generation Agent와 1:1 매핑을 위한 구조 확정
    - RAG 기반 근거 포함

주요 기능:
    1. RAG 근거 기반 기초 자료 수집
    2. LLM 호출 → 물리적 리스크 영향 분석 수행
    3. impact_list 스키마 강제 적용 및 누락 필드 자동 보정
    4. citations 포함
    5. LangGraph Memory Node용 output 생성 (impact_summary, impact_list)

변경 이력:
    - v02 (2025-11-14): 초안 작성 — 계산 기반 영향 분석
    - v03 (2025-11-21): LLM 기반 영향 분석으로 리팩토링
    - v04 (2025-11-24): 전략 생성 Agent와 1:1 매핑, impact_list 표준화
"""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel
from utils.rag_helpers import RAGEngine
from utils.citation_formatter import format_citations
import logging

# -----------------------------------------------------------
# 1) Input / Output Schema
# -----------------------------------------------------------

class ImpactAgentInput(BaseModel):
    """
    ImpactAnalysisAgent 입력 구조
    """
    physical_risk_scores: Dict[str, Any]       # 리스크별 점수
    aal_analysis: Dict[str, Any]               # 연평균 자산손실률
    collected_data: Dict[str, Any]             # 기타 수집 데이터 (ex: 전력사용량)
    vulnerability_analysis: Dict[str, Any]    # 취약성 분석 데이터
    company_name: str                          # 대상 기업명

class ImpactAgentOutput(BaseModel):
    """
    ImpactAnalysisAgent 출력 구조
    """
    impact_list: List[Dict[str, Any]]          # 표준화된 impact_list
    overall_impact_summary: str                # 전체 영향 요약
    citations: List[str]                       # RAG 근거 citations
    status: str = "completed"
    error: Optional[str] = None

# -----------------------------------------------------------
# 2) Agent Definition
# -----------------------------------------------------------

class ImpactAnalysisAgent:
    """
    물리적 기후 리스크 영향 분석 Agent (LLM + RAG)
    
    - Memory Node 저장: impact_list, overall_impact_summary, citations
    - Refiner 루프 시 route 결정 기준: Data Issue 발생 시 impact_list 재분석
    """

    def __init__(self, llm_client):
        """
        Args:
            llm_client: async LLM 호출 클라이언트
        """
        self.llm = llm_client
        self.rag = RAGEngine(source="graph")  # Graph RAG 기반 리스크 참고
        self.logger = logging.getLogger("ImpactAnalysisAgent")
        self.logger.info("[ImpactAnalysisAgent] 초기화 완료")

    # -------------------------------------------------------
    # LangGraph 실행 진입점
    # -------------------------------------------------------
    async def run(self, input_data: ImpactAgentInput) -> ImpactAgentOutput:
        """
        Agent 메인 실행

        Args:
            input_data: ImpactAgentInput 구조

        Returns:
            ImpactAgentOutput 구조
        """
        self.logger.info("[ImpactAnalysisAgent] 영향 분석 시작")

        try:
            # ---------------------------------------------------
            # 1) RAG 기반 근거 검색
            # ---------------------------------------------------
            rag_docs = self.rag.query(
                query=f"{input_data.company_name} 물리적 기후 리스크 영향 분석 5개년",
                top_k=10
            )

            # ---------------------------------------------------
            # 2) LLM 프롬프트 구성
            # ---------------------------------------------------
            prompt = self._build_prompt(
                company_name=input_data.company_name,
                physical_risk_scores=input_data.physical_risk_scores,
                aal_analysis=input_data.aal_analysis,
                collected_data=input_data.collected_data,
                vulnerability=input_data.vulnerability_analysis,
                rag_results=rag_docs
            )

            # ---------------------------------------------------
            # 3) LLM 호출
            # ---------------------------------------------------
            llm_response = await self.llm.ainvoke(prompt)

            # ---------------------------------------------------
            # 4) impact_list 스키마 보정
            # ---------------------------------------------------
            impact_list = self._normalize_impact_list(llm_response)

            # ---------------------------------------------------
            # 5) RAG citations 정리
            # ---------------------------------------------------
            citations = self.rag.get_citations(rag_docs)

            # ---------------------------------------------------
            # 6) 최종 Output
            # ---------------------------------------------------
            return ImpactAgentOutput(
                impact_list=impact_list,
                overall_impact_summary=llm_response.get("overall_impact_summary", ""),
                citations=citations,
                status="completed"
            )

        except Exception as e:
            self.logger.error(f"[ImpactAnalysisAgent] 영향 분석 실패: {e}", exc_info=True)
            return ImpactAgentOutput(
                impact_list=[],
                overall_impact_summary="",
                citations=[],
                status="failed",
                error=str(e)
            )

    # -------------------------------------------------------
    # LLM Prompt 생성
    # -------------------------------------------------------
    def _build_prompt(
        self,
        company_name: str,
        physical_risk_scores: Dict[str, Any],
        aal_analysis: Dict[str, Any],
        collected_data: Dict[str, Any],
        vulnerability: Dict[str, Any],
        rag_results: List[Dict[str, Any]]
    ) -> str:
        """
        LLM 분석용 Prompt 생성

        출력 impact_list 스키마 준수 필수
        """
        rag_json = json.dumps(rag_results, indent=2, ensure_ascii=False)

        prompt = f"""
당신은 기후 리스크 분석 전문가입니다.
아래 데이터를 기반으로 {company_name}의 물리적 기후 리스크 영향을 분석하십시오.

### 입력 데이터
- Physical Risk Scores: {physical_risk_scores}
- AAL (연평균 자산손실률): {aal_analysis}
- 기타 수집 데이터: {collected_data}
- 취약성 정보: {vulnerability}

### RAG 근거
{rag_json}

### 출력 형식(JSON)
impact_list = [
  {{
    "risk_type": "flood",
    "severity_level": "low/medium/high/critical",
    "financial_impact": float,
    "impact_description": "정성적 설명",
    "drivers": ["요인1", "요인2"],
    "supporting_metrics": {{
        "aal": float,
        "power_consumption_change": float
    }}
  }},
  ...
]

overall_impact_summary = "전체 리스크 영향 요약 문장"

### 작성 규칙
- impact_list 최소 3개 이상 포함
- risk_type 고유
- supporting_metrics 존재하지 않으면 0 또는 null
- StrategyAgent에서 그대로 사용 가능하도록 risk_type 명칭 유지
- JSON ONLY
"""
        return prompt

    # -------------------------------------------------------
    # LLM 응답 스키마 보정
    # -------------------------------------------------------
    def _normalize_impact_list(self, llm_response: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        impact_list가 표준 스키마를 따르도록 부족한 필드를 보정

        - severity_level 기본값: medium
        - financial_impact 기본값: 0
        - supporting_metrics 기본값: 0
        """
        raw_list = llm_response.get("impact_list", [])
        normalized = []

        for item in raw_list:
            normalized.append({
                "risk_type": item.get("risk_type", "unknown"),
                "severity_level": item.get("severity_level", "medium"),
                "financial_impact": item.get("financial_impact", 0),
                "impact_description": item.get("impact_description", ""),
                "drivers": item.get("drivers", []),
                "supporting_metrics": {
                    "aal": item.get("supporting_metrics", {}).get("aal", 0),
                    "power_consumption_change": item.get("supporting_metrics", {}).get("power_consumption_change", 0),
                }
            })

        return normalized
