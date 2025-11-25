"""
파일명: report_analysis_agent_1.py
최종 수정일: 2025-11-24
버전: v03

개요:
    기존 지속가능경영보고서(ESG/TCFD)에서 문체·구조·KPI·템플릿 정보를 추출하여
    report_profile 메타데이터를 생성하는 Agent.

    이 report_profile은 아래 Agent에서 공통적으로 참조됨:
        - Impact Analysis Agent (2번)
        - Strategy Generation Agent (3번)
        - Report Composer Agent (4번)
        - Validation Agent (5번)
        - Refiner Agent (6번)
        - Finalizer Node (7번)

주요 기능:
    1. RAG 기반으로 보고서 문단 스타일/구조/표현 규칙에 대한 레퍼런스 수집
    2. LLM 분석을 통해 ESG/TCFD 문서 구조, 문체, KPI, 시나리오 템플릿, 재사용 문단 추출
    3. JSON Schema 기반으로 누락 필드 자동 보정
    4. citations 포함

변경 이력:
    - v01 (2025-11-21): 초안 작성
    - v02 (2025-11-24): LangGraph 연동, baseline report_profile 구조 구축
    - v03 (2025-11-24): 
        * section_structure / hazard_templates / scenario_templates 항목 추가
        * Prompt 전면 개선 (정확도 + 일관성 극대화)
        * JSON 누락 자동 보정 기능 강화
"""

import json
from typing import List, Dict, Any
from .utils.rag_helpers import RAGEngine


class ReportAnalysisAgent:
    """
    기존 ESG/지속가능경영보고서를 분석하여 report_profile 생성.

    - 출력된 report_profile은 전체 파이프라인의 '정책/문체/구조 기본 템플릿'
    - HEV/AAL 값과 직접 연결되지 않음 → 2번 Impact Agent에서 본격 사용
    """

    def __init__(self, llm_client):
        self.llm = llm_client
        self.rag = RAGEngine(source="benchmark")

        # report_profile의 최종 JSON Schema
        self.required_fields = {
            "tone": {},
            "section_structure": {},
            "section_style": {},
            "formatting_rules": {},
            "report_years": [],
            "esg_structure": {},
            "tcfd_structure": {},
            "materiality": {},
            "benchmark_KPIs": {},
            "scenario_templates": {},
            "hazard_template_blocks": {},
            "reusable_paragraphs": {}
        }

    # ---------------------------------------------------------
    # 메인 실행 (비동기)
    # ---------------------------------------------------------
    async def run(self, company_name: str, past_reports: List[str]) -> Dict[str, Any]:
        """비동기 실행 메서드"""
        # 1) RAG: 스타일/구조 후보 수집
        rag_docs = self.rag.query(
            query=f"{company_name} 지속가능경영보고서 문단 구조 및 스타일",
            top_k=20
        )
        citations = self.rag.get_citations(rag_docs)

        # 2) Prompt 생성
        prompt = self._build_prompt(company_name, past_reports, rag_docs)

        # 3) LLM 실행
        llm_resp_raw = await self.llm.ainvoke(prompt)

        # 4) JSON 보정
        profile = self._sanitize_llm_response(llm_resp_raw)

        # 5) citations 추가
        profile["citations"] = citations
        return profile

    # ---------------------------------------------------------
    # 메인 실행 (동기) - 워크플로우 노드용
    # ---------------------------------------------------------
    def run_sync(self, company_name: str = None, past_reports: List[str] = None) -> Dict[str, Any]:
        """
        동기 실행 메서드 (워크플로우 노드에서 사용)

        Args:
            company_name: 회사명 (optional, 기본값 사용 가능)
            past_reports: 기존 보고서 리스트 (optional, 없으면 기본 템플릿)

        Returns:
            report_profile 딕셔너리
        """
        # 기본값 설정
        if not company_name:
            company_name = "Target Company"

        if not past_reports or len(past_reports) == 0:
            # 기존 보고서가 없는 경우 기본 템플릿 반환
            return self._get_default_profile()

        try:
            # 1) RAG: 스타일/구조 후보 수집
            rag_docs = self.rag.query(
                query=f"{company_name} 지속가능경영보고서 문단 구조 및 스타일",
                top_k=20
            )
            citations = self.rag.get_citations(rag_docs)

            # 2) Prompt 생성
            prompt = self._build_prompt(company_name, past_reports, rag_docs)

            # 3) LLM 실행 (동기)
            llm_resp_raw = self.llm.invoke(prompt)

            # 4) JSON 보정
            profile = self._sanitize_llm_response(llm_resp_raw)

            # 5) citations 추가
            profile["citations"] = citations
            return profile

        except Exception as e:
            print(f"[ReportAnalysisAgent] 오류 발생, 기본 프로필 반환: {e}")
            return self._get_default_profile()

    # ---------------------------------------------------------
    # 기본 프로필 생성
    # ---------------------------------------------------------
    def _get_default_profile(self) -> Dict[str, Any]:
        """
        기존 보고서가 없거나 분석 실패 시 사용할 기본 report_profile
        """
        return {
            "tone": {
                "style": "formal",
                "tense": "present",
                "vocabulary_level": "professional",
                "sentence_structure": "clear and concise"
            },
            "section_structure": {
                "main_sections": [
                    "executive_summary",
                    "governance",
                    "strategy",
                    "risk_management",
                    "metrics_and_targets"
                ],
                "subsections": {
                    "governance": ["board_oversight", "management_role"],
                    "strategy": ["climate_risks", "climate_opportunities", "resilience"],
                    "risk_management": ["identification", "assessment", "management"],
                    "metrics_and_targets": ["metrics", "targets", "performance"]
                }
            },
            "section_style": {
                "heading_format": "Title Case",
                "max_heading_length": 100,
                "subheading_depth": 3,
                "bullet_points": "allowed",
                "numbering": "hierarchical"
            },
            "formatting_rules": {
                "tables": "allowed",
                "charts": "allowed",
                "numerical_format": "comma_separated",
                "unit_display": "always_show"
            },
            "report_years": [2024, 2025, 2030, 2050],
            "esg_structure": {
                "environmental": ["climate_change", "resource_management", "pollution"],
                "social": ["labor_practices", "human_rights", "community"],
                "governance": ["board_structure", "ethics", "compliance"]
            },
            "tcfd_structure": {
                "governance": "Climate governance structure and processes",
                "strategy": "Climate-related risks and opportunities",
                "risk_management": "Risk identification, assessment and management",
                "metrics_targets": "Key metrics and targets for climate performance"
            },
            "materiality": {
                "high": ["climate_change", "carbon_emissions"],
                "medium": ["water_management", "waste"],
                "low": ["biodiversity"]
            },
            "benchmark_KPIs": {
                "carbon": ["scope1", "scope2", "scope3"],
                "energy": ["total_consumption", "renewable_percentage"],
                "water": ["withdrawal", "consumption", "recycling_rate"]
            },
            "scenario_templates": {
                "ssp1_2.6": "Low emissions scenario",
                "ssp2_4.5": "Moderate emissions scenario",
                "ssp3_7.0": "High emissions scenario",
                "ssp5_8.5": "Very high emissions scenario"
            },
            "hazard_template_blocks": {
                "extreme_heat": "극한 고온으로 인한 영향: {description}. 예상 피해: {impact}.",
                "extreme_cold": "극한 저온으로 인한 영향: {description}. 예상 피해: {impact}.",
                "wildfire": "산불 리스크 영향: {description}. 예상 피해: {impact}.",
                "drought": "가뭄으로 인한 영향: {description}. 예상 피해: {impact}.",
                "water_stress": "물 부족 리스크 영향: {description}. 예상 피해: {impact}.",
                "sea_level_rise": "해수면 상승 영향: {description}. 예상 피해: {impact}.",
                "river_flood": "하천 홍수 리스크: {description}. 예상 피해: {impact}.",
                "urban_flood": "도시 침수 리스크: {description}. 예상 피해: {impact}.",
                "typhoon": "태풍 리스크 영향: {description}. 예상 피해: {impact}."
            },
            "reusable_paragraphs": {
                "disclaimer": "본 분석은 기후 시나리오를 기반으로 한 것이며, 실제 결과는 다를 수 있습니다.",
                "methodology": "TCFD 프레임워크를 기반으로 물리적 리스크를 평가하였습니다.",
                "data_sources": "기후 데이터는 CMIP6 및 국제 표준 데이터를 활용하였습니다."
            },
            "citations": []
        }

    # ---------------------------------------------------------
    # Prompt 생성 — 고품질 버전
    # ---------------------------------------------------------
    def _build_prompt(self, company_name: str, past_reports: List[str], rag_docs: List[Dict[str, Any]]) -> str:

        reports_text = "\n\n----- REPORT -----\n\n".join(past_reports)
        rag_json = json.dumps(rag_docs, indent=2, ensure_ascii=False)

        # 최적화된 Prompt
        prompt = f"""
당신은 ESG/TCFD 보고서 분석 전문가이며,
지속가능경영보고서의 문체·구조·KPI 템플릿을 정밀 분석하는 역할을 맡았습니다.

아래 텍스트는 {company_name}의 기존 지속가능경영보고서입니다.
또한 RAG 검색으로 확보한 참고 문서들도 함께 제공합니다.

#######################################
### RAG 참고 문서(JSON)
#######################################
{rag_json}

#######################################
### 분석 대상 REPORT 텍스트
#######################################
{reports_text}

#######################################
### 분석 목표
#######################################
다음 12개 항목을 JSON으로만 출력하십시오.

1. tone: 문체·표현 스타일·시제·어휘 수준
2. section_structure: 목차 구조 (TCFD/ESG 포함)
3. section_style: 문단 규칙 (제목 길이, 소제목 depth, bullet 규칙)
4. formatting_rules: 표/그래프/수치 표현 규칙
5. report_years: 보고서가 다루는 연도 목록
6. esg_structure: E/S/G 항목별 내용 구성 규칙
7. tcfd_structure: Governance/Strategy/Risk/Metrics & Targets 형태
8. materiality: 중대성 이슈 그룹 및 설명
9. benchmark_KPIs: 기존 보고서에서 사용하는 KPI 구조·예시
10. scenario_templates: 기후 리스크 시나리오 문단 구성 템플릿
11. hazard_template_blocks: 
    9개 기후리스크(extreme_heat, extreme_cold, wildfire, drought,
    water_stress, sea_level_rise, river_flood, urban_flood, typhoon)
    각각의 문단 템플릿 (문장 구조/패턴)
12. reusable_paragraphs: 재사용 가능한 문단 리스트 (목적별 구분)

#######################################
### 출력 형식
#######################################
* 반드시 JSON만 출력
* 문자열 내 " 를 반드시 escape
* 모든 필드를 포함
* 누락 없이 key를 모두 포함

JSON ONLY:
"""
        return prompt

    # ---------------------------------------------------------
    # JSON 누락 자동 보정
    # ---------------------------------------------------------
    def _sanitize_llm_response(self, llm_resp: Any) -> Dict[str, Any]:

        # 만약 LLM이 문자열을 반환했으면 파싱 시도
        if isinstance(llm_resp, str):
            try:
                llm_resp = json.loads(llm_resp)
            except:
                llm_resp = {}

        sanitized = {}

        for field, default_val in self.required_fields.items():
            sanitized[field] = llm_resp.get(field, default_val)

            # 빈 값 보정
            if sanitized[field] in [None, ""]:
                sanitized[field] = default_val

        return sanitized
