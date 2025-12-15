"""
Node 2-B: Impact Analysis
시나리오 분석 결과 기반 영향 분석

설계 이유:
- 순차 의존성: Node 2-A의 시나리오 분석 결과를 기반으로 수행
- Top 5 리스크 집중: 9개 전체 리스크 중 AAL 상위 5개만 상세 분석
- 3가지 영향 차원: 재무/운영/자산 영향 분리 분석
- 병렬 처리: Top 5 리스크를 동시 분석 (60초)
- TextBlock x5 생성: P1~P5 영향 분석 텍스트 블록 JSON 생성

작성일: 2025-12-14 (v2 Refactoring)
"""

import asyncio
from typing import Dict, Any, List
from .schemas import TextBlock


class ImpactAnalysisNode:
    """
    Node 2-B: 영향 분석 노드

    의존성: Node 2-A 완료 필수

    입력:
        - sites_data: List[dict]
        - scenario_analysis: Dict (Node 2-A 출력)
        - risk_insight: Dict (RiskContextBuilder)

    출력:
        - top_5_risks: List[dict]
        - impact_analyses: List[dict] (재무/운영/자산 영향)
    """

    def __init__(self, llm):
        self.llm = llm

    async def execute(
        self,
        sites_data: List[Dict],
        scenario_analysis: Dict,
        risk_insight: Dict
    ) -> Dict[str, Any]:
        """
        메인 실행 함수
        """
        # 1. Top 5 리스크 식별
        top_5_risks = self._identify_top_risks(sites_data)

        # 2. Top 5 리스크별 영향 분석 (병렬)
        impact_analyses = await self._analyze_impacts_parallel(
            top_5_risks,
            scenario_analysis,
            risk_insight
        )

        # 3. TextBlock x5 생성 (P1~P5 영향 분석)
        impact_blocks = self._create_impact_text_blocks(impact_analyses)

        return {
            "top_5_risks": top_5_risks,
            "impact_analyses": impact_analyses,
            "impact_blocks": impact_blocks  # List[TextBlock] x5
        }

    def _identify_top_risks(self, sites_data: List[Dict]) -> List[Dict]:
        """
        Top 5 리스크 식별 (AAL 기준)
        """
        risk_aal_map = {}

        for site in sites_data:
            for risk_result in site.get("risk_results", []):
                risk_type = risk_result.get("risk_type")
                aal = risk_result.get("final_aal", 0)
                risk_aal_map[risk_type] = risk_aal_map.get(risk_type, 0) + aal

        # AAL 기준 내림차순 정렬 → Top 5
        top_5 = sorted(risk_aal_map.items(), key=lambda x: x[1], reverse=True)[:5]

        return [{"risk_type": r[0], "total_aal": r[1]} for r in top_5]

    async def _analyze_impacts_parallel(
        self,
        top_5_risks: List[Dict],
        scenario_analysis: Dict,
        risk_insight: Dict
    ) -> List[Dict]:
        """
        Top 5 리스크 병렬 영향 분석 (60초)
        """
        tasks = [
            self._analyze_single_risk_impact(risk, scenario_analysis, risk_insight)
            for risk in top_5_risks
        ]
        impact_analyses = await asyncio.gather(*tasks)
        return impact_analyses

    async def _analyze_single_risk_impact(
        self,
        risk: Dict,
        scenario_analysis: Dict,
        risk_insight: Dict
    ) -> Dict:
        """
        단일 리스크 영향 분석
        """
        risk_type = risk["risk_type"]
        total_aal = risk["total_aal"]

        # 리스크 한글명 매핑
        risk_name_mapping = {
            "river_flood": "하천 범람",
            "typhoon": "태풍",
            "urban_flood": "도시 침수",
            "extreme_heat": "극심한 고온",
            "sea_level_rise": "해수면 상승",
            "drought": "가뭄",
            "landslide": "산사태",
            "wildfire": "산불",
            "cold_wave": "한파"
        }
        risk_name_kr = risk_name_mapping.get(risk_type, risk_type)

        # 시나리오 분석 요약 (SSP2-4.5 기준)
        scenarios = scenario_analysis.get("scenarios", {})
        ssp245 = scenarios.get("ssp2_4.5", {})
        ssp245_summary = ssp245.get("summary", "시나리오 분석 결과 없음")

        # RiskContextBuilder에서 제공하는 인사이트 추출
        risk_specific_insight = risk_insight.get(risk_type, {})
        vulnerability_factors = risk_specific_insight.get("vulnerability_factors", "정보 없음")
        historical_events = risk_specific_insight.get("historical_events", "정보 없음")

        # Top 5에서의 순위 (1~5)
        priority_index = self.top_5_risks.index(risk) + 1 if hasattr(self, 'top_5_risks') else 1

        # LLM 프롬프트
        prompt = f"""당신은 TCFD 보고서 작성 전문가이며, 기후 리스크 영향 분석을 담당하고 있습니다.

**임무:**
{risk_name_kr} 리스크가 기업에 미치는 영향을 **재무적/운영적/자산** 3개 차원에서 분석하고,
TCFD Strategy 섹션 "주요 리스크별 영향 분석" 파트에 포함될 서술문을 작성하세요.

**리스크 정보:**
- 리스크 유형: {risk_name_kr} ({risk_type})
- 포트폴리오 총 AAL: {total_aal:.4f} (연평균 손실률)
- SSP2-4.5 시나리오 분석: {ssp245_summary}

**취약성 요인:**
{vulnerability_factors}

**과거 사건 사례:**
{historical_events}

**출력 요구사항:**

1. **재무적 영향** (4-6문장)
   - AAL 기반 연간 예상 손실액 (백만원/억원 단위로 환산)
   - 보험료 증가, 자산 가치 하락, 복구 비용 등
   - 정량적 수치와 함께 서술 (예: "연간 약 X억원의 손실 예상")

2. **운영적 영향** (4-6문장)
   - 사업 중단 가능성 및 기간 (예: "연 X일의 운영 중단 예상")
   - 생산성 저하, 공급망 차질, 인력 안전 문제
   - 고객 서비스 영향, 평판 리스크

3. **자산 영향** (4-6문장)
   - 건물, 설비, 인프라 손상 가능성
   - 물리적 피해 유형 (침수, 파손, 노후화 가속 등)
   - 자산 내용연수 단축, 교체 필요성

**출력 형식:**
JSON 형식으로 반환
{{
  "financial_impact": "재무적 영향 서술문 (4-6문장)",
  "operational_impact": "운영적 영향 서술문 (4-6문장)",
  "asset_impact": "자산 영향 서술문 (4-6문장)"
}}

**톤 & 스타일:**
- 객관적이고 전문적인 어조
- 정량적 데이터 우선, 정성적 설명 보완
- TCFD 보고서에 적합한 형식적 문체
- 과도한 위협 강조 지양, 사실 기반 서술
"""

        # LLM 호출
        response = await self.llm.ainvoke(prompt)

        # 응답 파싱 (JSON 형식 기대)
        import json
        try:
            if hasattr(response, 'content'):
                response_text = response.content
            elif isinstance(response, str):
                response_text = response
            else:
                response_text = str(response)

            # JSON 파싱 시도
            result = json.loads(response_text)

            return {
                "risk_type": risk_type,
                "financial_impact": result.get("financial_impact", "분석 중"),
                "operational_impact": result.get("operational_impact", "분석 중"),
                "asset_impact": result.get("asset_impact", "분석 중")
            }
        except json.JSONDecodeError:
            # JSON 파싱 실패 시 전체 텍스트를 financial_impact에 담기
            return {
                "risk_type": risk_type,
                "financial_impact": response_text,
                "operational_impact": "분석 중 (JSON 파싱 실패)",
                "asset_impact": "분석 중 (JSON 파싱 실패)"
            }

    def _create_impact_text_blocks(self, impact_analyses: List[Dict]) -> List[Dict]:
        """
        P1~P5 영향 분석 TextBlock 생성

        Returns:
            List[TextBlock] x5 (각 리스크별 영향 분석 텍스트 블록)
        """
        risk_name_mapping = {
            "river_flood": "하천 범람",
            "typhoon": "태풍",
            "urban_flood": "도시 침수",
            "extreme_heat": "극심한 고온",
            "sea_level_rise": "해수면 상승",
            "drought": "가뭄",
            "landslide": "산사태",
            "wildfire": "산불",
            "cold_wave": "한파"
        }

        impact_blocks = []

        for i, impact in enumerate(impact_analyses, 1):
            risk_type = impact.get("risk_type", "Unknown")
            risk_name_kr = risk_name_mapping.get(risk_type, risk_type)

            # 영향 분석 내용 조합
            content = f"""**재무적 영향**
{impact.get('financial_impact', '분석 중')}

**운영적 영향**
{impact.get('operational_impact', '분석 중')}

**자산 영향**
{impact.get('asset_impact', '분석 중')}
"""

            # TextBlock 생성
            text_block = {
                "type": "text",
                "subheading": f"P{i}. {risk_name_kr} 영향 분석",
                "content": content
            }

            impact_blocks.append(text_block)

        return impact_blocks
