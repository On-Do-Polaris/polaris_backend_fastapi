"""
Node 2-C: Mitigation Strategies
영향 분석 기반 단기/중기/장기 대응 방안 생성

설계 이유:
- 순차 의존성: Node 2-B의 영향 분석 결과에 따라 우선순위 결정
- 3단계 시간축: 단기(1-2년)/중기(3-5년)/장기(5년 이상)
- P1~P5 구조: SK ESG 2025 보고서 스타일 준수
- 병렬 처리: Top 5 리스크별 대응 방안 동시 생성 (60초)
- TextBlock x5 생성: P1~P5 대응 전략 텍스트 블록 JSON 생성

작성일: 2025-12-14 (v2 Refactoring)
"""

import asyncio
from typing import Dict, Any, List
from .schemas import TextBlock


class MitigationStrategiesNode:
    """
    Node 2-C: 대응 방안 생성 노드

    의존성: Node 2-B 완료 필수

    입력:
        - impact_analyses: List[dict] (Node 2-B 출력)
        - risk_insight: Dict (RiskContextBuilder)

    출력:
        - mitigation_strategies: List[dict] (단기/중기/장기 대응)
    """

    def __init__(self, llm):
        self.llm = llm

    async def execute(
        self,
        impact_analyses: List[Dict],
        risk_insight: Dict
    ) -> Dict[str, Any]:
        """
        메인 실행 함수
        """
        # 1. Top 5 리스크별 대응 방안 생성 (병렬)
        mitigation_strategies = await self._generate_strategies_parallel(
            impact_analyses,
            risk_insight
        )

        # 2. TextBlock x5 생성 (P1~P5 대응 전략)
        mitigation_blocks = self._create_mitigation_text_blocks(mitigation_strategies)

        return {
            "mitigation_strategies": mitigation_strategies,
            "mitigation_blocks": mitigation_blocks  # List[TextBlock] x5
        }

    async def _generate_strategies_parallel(
        self,
        impact_analyses: List[Dict],
        risk_insight: Dict
    ) -> List[Dict]:
        """
        Top 5 리스크 병렬 대응 방안 생성 (60초)
        """
        tasks = [
            self._generate_single_risk_strategy(impact, risk_insight)
            for impact in impact_analyses
        ]
        strategies = await asyncio.gather(*tasks)
        return strategies

    async def _generate_single_risk_strategy(
        self,
        impact: Dict,
        risk_insight: Dict
    ) -> Dict:
        """
        단일 리스크 대응 방안 생성
        """
        risk_type = impact["risk_type"]

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

        # 영향 분석 결과 요약
        financial_impact = impact.get("financial_impact", "정보 없음")
        operational_impact = impact.get("operational_impact", "정보 없음")
        asset_impact = impact.get("asset_impact", "정보 없음")

        # RiskContextBuilder에서 제공하는 인사이트 추출
        risk_specific_insight = risk_insight.get(risk_type, {})
        best_practices = risk_specific_insight.get("best_practices", "정보 없음")
        adaptation_options = risk_specific_insight.get("adaptation_options", "정보 없음")

        # LLM 프롬프트
        prompt = f"""당신은 TCFD 보고서 작성 전문가이며, 기후 리스크 대응 전략 수립을 담당하고 있습니다.

**임무:**
{risk_name_kr} 리스크에 대한 **단기/중기/장기** 대응 전략을 수립하고,
TCFD Strategy 섹션 "주요 리스크별 대응 방안" 파트에 포함될 서술문을 작성하세요.

**리스크 정보:**
- 리스크 유형: {risk_name_kr} ({risk_type})

**영향 분석 결과:**
1. **재무적 영향**: {financial_impact[:200]}...
2. **운영적 영향**: {operational_impact[:200]}...
3. **자산 영향**: {asset_impact[:200]}...

**산업 모범 사례:**
{best_practices}

**적응 옵션:**
{adaptation_options}

**출력 요구사항:**

1. **단기 조치 (1-2년)** - 3-4개 항목
   - 즉각 실행 가능한 조치 (비상 대응 체계, 모니터링 강화 등)
   - 예산 부담이 적고 신속히 효과를 볼 수 있는 조치
   - 각 항목은 1-2문장으로 구체적으로 작성

2. **중기 조치 (3-5년)** - 2-3개 항목
   - 시설 개선, 인프라 강화, 시스템 구축 등
   - 투자 및 기획이 필요한 조치
   - 각 항목은 1-2문장으로 구체적으로 작성

3. **장기 조치 (5년 이상)** - 2-3개 항목
   - 근본적 체질 개선, 사업장 이전, 대규모 투자 등
   - 전략적 의사결정이 필요한 조치
   - 각 항목은 1-2문장으로 구체적으로 작성

4. **우선순위** - "높음", "중간", "낮음" 중 선택
   - 영향 분석 결과의 심각도 기반 판단

5. **예상 비용** - 범위로 제시 (예: "5-10억원", "10-30억원", "30억원 이상")
   - 단기/중기/장기 조치 총합 비용

**출력 형식:**
JSON 형식으로 반환
{{
  "short_term": [
    "단기 조치 1 (1-2문장)",
    "단기 조치 2 (1-2문장)",
    "단기 조치 3 (1-2문장)"
  ],
  "mid_term": [
    "중기 조치 1 (1-2문장)",
    "중기 조치 2 (1-2문장)"
  ],
  "long_term": [
    "장기 조치 1 (1-2문장)",
    "장기 조치 2 (1-2문장)"
  ],
  "priority": "높음/중간/낮음",
  "estimated_cost": "X-Y억원"
}}

**톤 & 스타일:**
- 실행 가능하고 구체적인 조치 제시
- 업종 특성을 고려한 현실적인 대응 방안
- TCFD 보고서에 적합한 전문적 어조
- 과도한 기술 용어 지양, 명확한 액션 아이템 제시
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
                "short_term": result.get("short_term", ["검토 중"]),
                "mid_term": result.get("mid_term", ["검토 중"]),
                "long_term": result.get("long_term", ["검토 중"]),
                "priority": result.get("priority", "중간"),
                "estimated_cost": result.get("estimated_cost", "산정 중")
            }
        except json.JSONDecodeError:
            # JSON 파싱 실패 시 기본값 반환
            return {
                "risk_type": risk_type,
                "short_term": [response_text[:500]],
                "mid_term": ["JSON 파싱 실패"],
                "long_term": ["JSON 파싱 실패"],
                "priority": "중간",
                "estimated_cost": "산정 중"
            }

    def _create_mitigation_text_blocks(self, mitigation_strategies: List[Dict]) -> List[Dict]:
        """
        P1~P5 대응 전략 TextBlock 생성

        Returns:
            List[TextBlock] x5 (각 리스크별 대응 전략 텍스트 블록)
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

        mitigation_blocks = []

        for i, strategy in enumerate(mitigation_strategies, 1):
            risk_type = strategy.get("risk_type", "Unknown")
            risk_name_kr = risk_name_mapping.get(risk_type, risk_type)

            # 단기 조치 포맷팅
            short_term = strategy.get("short_term", [])
            short_term_str = "\n".join([f"- {item}" for item in short_term]) if short_term else "- 검토 중"

            # 중기 조치 포맷팅
            mid_term = strategy.get("mid_term", [])
            mid_term_str = "\n".join([f"- {item}" for item in mid_term]) if mid_term else "- 검토 중"

            # 장기 조치 포맷팅
            long_term = strategy.get("long_term", [])
            long_term_str = "\n".join([f"- {item}" for item in long_term]) if long_term else "- 검토 중"

            # 우선순위 및 예상 비용
            priority = strategy.get("priority", "중간")
            estimated_cost = strategy.get("estimated_cost", "산정 중")

            # 대응 전략 내용 조합
            content = f"""**우선순위**: {priority} | **예상 비용**: {estimated_cost}

**단기 조치 (1-2년)**
{short_term_str}

**중기 조치 (3-5년)**
{mid_term_str}

**장기 조치 (5년 이상)**
{long_term_str}
"""

            # TextBlock 생성
            text_block = {
                "type": "text",
                "subheading": f"P{i}. {risk_name_kr} 대응 전략",
                "content": content
            }

            mitigation_blocks.append(text_block)

        return mitigation_blocks
