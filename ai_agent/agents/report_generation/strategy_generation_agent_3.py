# strategy_generation_agent_3.py
"""
파일명: strategy_generation_agent_3.py
최종 수정일: 2025-11-24
버전: v04

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
    4. citations 생성 및 정리 (기존 citations 무시, 항상 전체 재생성)
    5. Memory Node용 output 구성 (strategies[], citations[])

Refiner 루프 연계:
    - Strategy Issue 발생 시 route: strategy
    - LLM 재호출로 strategies[] + citations 재생성

변경 이력:
    - v01 (2025-11-14): 초안 작성, 물리적 리스크별 대응 전략 생성
    - v02 (2025-11-21): RAG + LLM 구조로 리팩토링, citations 포함
    - v03 (2025-11-24): 최신 LangGraph 아키텍처 반영, Memory Node/Refiner 루프 연계
    - v04 (2025-11-24): Impact Analysis Agent와 1:1 매핑, 전략별 citations 자동 재생성
"""

from typing import Dict, List, Any

class StrategyGenerationAgent:
    """
    Strategy Generation Agent (Agent 3)
    ------------------------------------
    목적:
    - Agent 2 영향 분석 결과를 기반으로, 리스크별 대응 전략 자동 생성
    - 국제 기준 RAG 근거 포함
    - Composer/보고서용 구조화 output 생성

    구성:
    - Layer 1: Quantitative/Context Mapping (영향→전략 후보)
    - Layer 2: LLM Narrative Generation (전략 설명 + 비용/효과 분석)
    """

    def __init__(self, llm_client):
        """
        llm_client: OpenAI, Anthropic, Vertex 등 LLM 객체
        """
        self.llm = llm_client

    # ----------------------------------------------------------------------
    # Layer 1: Quantitative/Context Mapping
    # ----------------------------------------------------------------------
    def map_strategies(self, impact_summary: List[Dict], facility_profile: Dict) -> List[Dict]:
        """
        영향 분석 결과와 시설 정보 기반 전략 후보 생성
        각 impact_summary 항목과 1:1 매핑
        """
        strategy_candidates = []

        for impact in impact_summary:
            risk = impact.get("risk")
            # 기본 템플릿 전략 후보
            strategy_candidates.append({
                "risk": risk,
                "strategy": f"{risk} 대응 기본 전략 후보",  # 초기 placeholder
                "impact": impact,  # 나중에 LLM에 context로 사용
            })

        return strategy_candidates

    # ----------------------------------------------------------------------
    # Layer 2: LLM Narrative Generation
    # ----------------------------------------------------------------------
    def generate_strategy_narrative(self, strategy_candidates: List[Dict],
                                    facility_profile: Dict,
                                    report_profile: Dict) -> List[Dict]:
        """
        LLM을 통해 리스크별 전략 내러티브, 비용/효과 분석, 정책/운영/기술 권고 작성
        citations는 항상 전체 재생성
        """
        strategies_output = []

        for candidate in strategy_candidates:
            risk = candidate["risk"]
            impact = candidate["impact"]

            prompt = f"""
당신은 Strategy Generation Agent 3입니다.
역할:
- 영향 분석 결과를 기반으로 리스크별 전략 작성
- 비용/효과 분석 포함
- 정책/운영/기술 대응 권고 포함
- 국제 기준 RAG 기반 citations 자동 생성

===== 입력 데이터 =====
영향 분석 결과:
{impact}

시설 정보:
{facility_profile}

보고서 스타일 프로필:
{report_profile}

===== 출력 요구사항 =====
1. 리스크별 전략(strategy)
2. 대응 근거 citations (항상 전체 재생성)
3. 전략 내러티브에 비용/효과 및 정책/운영/기술 권고 포함

출력 형식:
{{ "risk": "<리스크>", "strategy": "<전략>", "citation": "<RAG 근거>" }}
출력 언어: 한국어
전문적인 TCFD 지속가능경영 보고서 톤 유지
"""
            response = self.llm.generate(prompt)

            # LLM 결과를 바로 strategies_output에 저장
            strategies_output.append({
                "risk": risk,
                "strategy": response.get("strategy", f"{risk} 대응 전략"),
                "citation": response.get("citation", f"TCFD(2023)-Adaptation {risk}"),
            })

        return strategies_output

    # ----------------------------------------------------------------------
    # Main API method
    # ----------------------------------------------------------------------
    def run(self, impact_summary: List[Dict],
            facility_profile: Dict,
            report_profile: Dict) -> List[Dict]:
        """
        에이전트 3 전체 파이프라인 실행
        """

        # Layer 1: 전략 후보 매핑
        strategy_candidates = self.map_strategies(
            impact_summary=impact_summary,
            facility_profile=facility_profile
        )

        # Layer 2: LLM 기반 전략 내러티브 및 citations 생성
        strategies_output = self.generate_strategy_narrative(
            strategy_candidates=strategy_candidates,
            facility_profile=facility_profile,
            report_profile=report_profile
        )

        return strategies_output
