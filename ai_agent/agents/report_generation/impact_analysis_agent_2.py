# impact_analysis_agent_2.py
"""
파일명: impact_analysis_agent_2.py
최종 수정일: 2025-11-24
버전: v05

파일 개요:
    - 물리적 기후 리스크 영향 분석 Agent
    - Physical Risk Scores, AAL, 취약성 데이터, 전력 사용량 기반 영향 분석 수행
    - Impact List 표준 스키마 적용
    - 향후 Strategy Generation Agent와 1:1 매핑을 위한 구조 확정
    - RAG 기반 근거 포함

주요 기능:
    1. RAG 근거 기반 기초 자료 수집
    2. LLM 호출 → 물리적 리스크 영향 분석 수행
    3. impact_list 스키마 강제 적용 및 누락 필드 자동 보정
    4. 전력 사용량 기반 HEV 가중치 반영
    5. citations 포함
    6. LangGraph Memory Node용 output 생성 (impact_summary, impact_list)

Refiner 루프 연계:
    - Impact Issue 발생 시 route: impact
    - 필요한 입력만 유지한 상태로 Impact Analysis 재실행
    - 정량/정성 impact_summary 재생성

변경 이력:
    - v02 (2025-11-14): 초안 작성 — 계산 기반 영향 분석
    - v03 (2025-11-21): LLM 기반 영향 분석으로 리팩토링
    - v04 (2025-11-24): 전략 생성 Agent와 1:1 매핑, impact_list 표준화
    - v05 (2025-11-24): 전력 사용량 기반 영향 분석 Layer1 통합
"""

import numpy as np
from typing import Dict, Any, List

class ImpactAnalysisAgent:
    """
    Impact Analysis Agent (Agent 2)
    --------------------------------
    목적:
    - 9대 기후리스크 × 최대 4개 시나리오에 대해
      정량 + 정성 Impact Analysis 결과 생성

    구성:
    - Layer 1 Quantitative Engine (H/E/V + 전력 사용량 기반 HEV 가중치 계산)
    - Layer 2 LLM Contextual Narrative Engine (정성 내러티브)
    """

    def __init__(self, llm_client):
        """
        llm_client: OpenAI, Anthropic, Vertex 등 LLM 객체
        """
        self.llm = llm_client

        self.risk_list = [
            "extreme_heat", "extreme_cold", "drought", "inland_flood",
            "urban_flood", "coastal_flood", "typhoon", "wildfire", "water_stress"
        ]

    # ----------------------------------------------------------------------
    # Layer 1 : Quantitative Engine
    # ----------------------------------------------------------------------

    def compute_severity(self, risk_score: float) -> str:
        """정량 위험등급 분류기"""
        if risk_score < 10:
            return "minimal"
        elif risk_score < 20:
            return "low"
        elif risk_score < 35:
            return "medium"
        elif risk_score < 55:
            return "high"
        else:
            return "extreme"

    def aggregate_HEV(self, H: Dict, E: Dict, V: Dict, power_usage: Dict = None) -> Dict:
        """
        리스크별 H/E/V 평균치 구조화
        전력 사용량(power_usage)이 주어지면 HEV_mean에 가중치 반영
        """
        result = {}
        for r in self.risk_list:
            h_val = H.get(r)
            e_val = E.get(r)
            v_val = V.get(r)
            hev_mean = np.mean([h_val, e_val, v_val])

            # 전력 사용량 기반 가중치 반영
            if power_usage:
                it_factor = power_usage.get("IT", 0) / 30000  # 정규화 예시
                cooling_factor = power_usage.get("Cooling", 0) / 10000
                hev_mean *= (1 + 0.1 * (it_factor + cooling_factor))

            result[r] = {
                "H": h_val,
                "E": e_val,
                "V": v_val,
                "HEV_mean": hev_mean
            }
        return result

    def build_quantitative_output(self, scenario_input: Dict, AAL: Dict) -> Dict:
        """
        scenario_input 구조:
        {
            "SSP126": { "H": {...}, "E": {...}, "V": {...}, "risk_scores": {...}, "power_usage": {...} },
            ...
        }

        AAL:
        {
            "extreme_heat": 2.94,
            "extreme_cold": 1.13,
            ...
        }
        """
        output = {}

        for scenario, data in scenario_input.items():
            H, E, V = data["H"], data["E"], data["V"]
            power_usage = data.get("power_usage", None)

            # 1) 리스크별 HEV 평균 (전력 사용량 가중치 포함)
            hev_avg = self.aggregate_HEV(H, E, V, power_usage=power_usage)

            # 2) severity 계산
            severity = {
                r: self.compute_severity(data["risk_scores"].get(r, 0))
                for r in self.risk_list
            }

            # 3) scenario 내 상위 위험 순위
            sorted_risks = sorted(
                data["risk_scores"].items(),
                key=lambda x: x[1],
                reverse=True
            )
            top3 = sorted_risks[:3]

            output[scenario] = {
                "HEV_average": hev_avg,
                "risk_scores": data["risk_scores"],
                "severity": severity,
                "top3_risks": top3,
                "power_usage": power_usage  # Layer 2 참고용
            }

        # 4) 모든 시나리오 공통 AAL 추가
        output["AAL"] = AAL

        return output

    # ----------------------------------------------------------------------
    # Layer 2 : LLM-Based Narrative Generation
    # ----------------------------------------------------------------------

    def generate_risk_narrative(self, quant_output: Dict, asset_info: Dict,
                                tcfd_warnings: List, report_profile: Dict) -> str:
        """
        LLM에게 정성 분석을 요청하는 프롬프트 생성 및 호출
        """
        prompt = f"""
당신은 Impact Analysis Agent 2입니다.
역할:
- 구조화된 정량적 기후 리스크 데이터를 바탕으로 전문가 수준의
  TCFD 기준 영향 분석 내러티브를 작성합니다.

===== 입력 데이터 =====
정량적 분석 결과 (JSON):
{quant_output}

자산 정보:
{asset_info}

TCFD 데이터 품질 경고:
{tcfd_warnings}

보고서 스타일 프로필 (Agent 1 기준):
{report_profile}

===== 출력 요구사항 =====
다음 항목을 포함한 전체 영향 평가 보고서 섹션을 작성하세요:

1. 리스크별 상세 내러티브
   - H/E/V 조건 설명
   - 주요 원인 강조 (예: 최고 강수량, 홍수 이력, 최대 풍속, 폭염일수 등)
   - 취약성 논의 (건물 연령, 구조, 배수, 토지이용 등)
   - AAL(연평균 손실액) 해석 통합
   - 전력 사용량 기반 영향 고려 (IT/냉방 전력)
   - report_profile에 정의된 톤/스타일 적용

2. 시나리오별 영향 비교 (SSP126/245/370/585)
   - 시나리오 간 추세 분석
   - 강화 또는 안정화 경향에 대한 고급 내러티브

3. 리스크 간 상호작용
   - 예: 고온 x 가뭄, 태풍 x 도시홍수 등

4. 취약 자산 평가
   - 구조, 연령, 배수능력, 고도, 토지이용 기반 평가

5. 데이터 품질 및 불확실성 (TCFD)
   - 경고 내용을 전문가 수준으로 해석하여 설명

6. 통합 요약
   - 핵심 리스크 식별
   - 대응/적응 전략에 반영할 사항 간략 예시

출력 언어: 한국어
전문적인 TCFD 지속가능경영 보고서 톤 유지
JSON 자체 반복 금지, 해석만 작성
"""
        response = self.llm.generate(prompt)
        return response

    # ----------------------------------------------------------------------
    # Main API method
    # ----------------------------------------------------------------------

    def run(self, scenario_input: Dict, AAL: Dict,
            asset_info: Dict, tcfd_warnings: List,
            report_profile: Dict) -> Dict:
        """
        에이전트 2 전체 파이프라인 실행
        """

        # Layer 1: Quantitative 결과 생성 (전력 사용량 기반 HEV 포함)
        quantitative_result = self.build_quantitative_output(
            scenario_input=scenario_input,
            AAL=AAL
        )

        # Layer 2: LLM 정성 내러티브 생성
        narrative = self.generate_risk_narrative(
            quant_output=quantitative_result,
            asset_info=asset_info,
            tcfd_warnings=tcfd_warnings,
            report_profile=report_profile
        )

        return {
            "quantitative_result": quantitative_result,
            "narrative": narrative
        }
