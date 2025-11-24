# report_analysis_agent_1.py
"""
파일명: report_analysis_agent_1.py
최종 수정일: 2025-11-24
버전: v02

파일 개요:
    - 기존 ESG/TCFD 보고서를 분석하여 report_profile 생성
    - Tone, Section Style, KPI, Benchmark 추출
    - RAG 기반 근거 포함
    - 이후 LangGraph Composer/Validation/Refiner 단계에서 재사용되는 메타데이터 생성

주요 기능:
    1. RAG 기반 ESG 핵심 항목 후보 수집
    2. LLM 호출을 통해 ESG/TCFD 구조, 핵심 메트릭, 중대성, 보고서 연도, 문단 재사용 후보 추출
    3. LLM 출력 JSON 검증 및 누락 필드 자동 보정
    4. citations 포함

변경 이력:
    - v01 (2025-11-21): 초안 작성 — ESG/TCFD 분석 Agent 신규 구축
    - v02 (2025-11-24):
        * 최신 LangGraph 아키텍쳐 반영
        * report_profile 생성 (Tone, KPI, Section Style, Benchmark 포함)
        * LLM 결과 검증 및 누락 필드 자동 보정
        * RAGEngine 활용, citations 포함
"""

import json
from typing import List, Dict, Any
from utils.rag_helpers import RAGEngine
from utils.citation_formatter import format_citations_inline, format_references

class ReportAnalysisAgent:
    """
    기존 ESG/지속가능경영보고서를 분석하여 report_profile 생성

    - 출력 JSON(report_profile)은 이후 Composer, Validation, Refiner 단계에서 참조
    - Memory Node용으로 저장되며, Tone/KPI/Section Style 정보 활용 가능
    """

    def __init__(self, llm_client):
        """
        Args:
            llm_client: LLM 호출 클라이언트 (async 지원)
        """
        self.llm = llm_client
        self.rag = RAGEngine(source="benchmark")  # Benchmark RAG 활용

    async def run(self, company_name: str, past_reports: List[str]) -> Dict[str, Any]:
        """
        Agent 메인 실행 함수

        Args:
            company_name (str): 분석 대상 기업명
            past_reports (List[str]): 최근 3~5년 지속가능경영보고서 텍스트 리스트

        Returns:
            report_profile (Dict): report_profile JSON 구조
        """
        # -----------------------------------------------------
        # 1. RAG 기반 핵심 ESG 후보 수집
        # -----------------------------------------------------
        rag_docs = self.rag.query(
            query=f"{company_name} 최근 ESG/TCFD 보고서 핵심 요소",
            top_k=20
        )
        citations = self.rag.get_citations(rag_docs)

        # -----------------------------------------------------
        # 2. LLM Prompt 구성
        # -----------------------------------------------------
        prompt = self._build_prompt(company_name, past_reports, rag_docs)

        # -----------------------------------------------------
        # 3. LLM 분석 수행
        # -----------------------------------------------------
        llm_resp_raw = await self.llm.ainvoke(prompt)

        # -----------------------------------------------------
        # 4. JSON 검증 및 누락 필드 보정
        # -----------------------------------------------------
        profile = self._sanitize_llm_response(llm_resp_raw)

        # -----------------------------------------------------
        # 5. 최종 JSON 반환 (citations 포함)
        # -----------------------------------------------------
        profile["citations"] = citations
        return profile

    # ---------------------------------------------------------
    # Prompt 생성
    # ---------------------------------------------------------
    def _build_prompt(self, company_name: str, past_reports: List[str], rag_docs: List[Dict[str, Any]]) -> str:
        """
        LLM 분석용 Prompt 생성

        Args:
            company_name: 분석 대상 기업명
            past_reports: 보고서 텍스트 리스트
            rag_docs: RAG 기반 후보 문서 리스트

        Returns:
            prompt (str): LLM 입력용 Prompt
        """
        reports_text = "\n\n---\n\n".join(past_reports)
        rag_json = json.dumps(rag_docs, indent=2, ensure_ascii=False)

        prompt = f"""
당신은 ESG/TCFD 분석 전문가입니다.
다음은 {company_name}의 최근 ESG/지속가능경영보고서입니다.

분석 목표:
1. Tone, Section Style, KPI, Benchmark 추출
2. ESG 구조 (E/S/G) 분석
3. TCFD 구조 (Governance/Strategy/Risk/Metric & Target) 분석
4. Materiality, Key Metrics, 재사용 가능한 문단 추출

RAG 근거:
{rag_json}

보고서 텍스트:
{reports_text}

출력 형식: JSON ONLY. 필드:
- tone
- structure_rules
- section_style
- benchmark_KPIs
- report_years
- esg_structure
- tcfd_structure
- materiality
- key_metrics
- extracted_sections
"""
        return prompt

    # ---------------------------------------------------------
    # LLM 응답 검증/보정
    # ---------------------------------------------------------
    def _sanitize_llm_response(self, llm_resp: Any) -> Dict[str, Any]:
        """
        LLM이 반환한 dict를 검증하고 누락 필드를 보정

        Args:
            llm_resp: LLM 반환값 (dict 예상)

        Returns:
            sanitized: report_profile 구조
        """
        fields = [
            "tone", "structure_rules", "section_style", "benchmark_KPIs",
            "report_years", "esg_structure", "tcfd_structure",
            "materiality", "key_metrics", "extracted_sections"
        ]
        sanitized = {}
        for f in fields:
            sanitized[f] = llm_resp.get(f, {} if f not in ["tone","report_years"] else [])

        return sanitized
