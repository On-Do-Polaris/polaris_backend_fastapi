"""
파일명: additional_data_helper.py
최종 수정일: 2025-12-01
버전: v01
파일 개요: 추가 데이터 관련성 판단 헬퍼 (LLM 기반)

사용자가 제공한 자유 형식의 추가 데이터가 특정 Agent에 관련이 있는지 LLM으로 판단하고,
관련 있는 경우 데이터를 추출하여 Agent가 활용할 수 있도록 지원합니다.

변경 이력:
    - v01 (2025-12-01): 초기 버전 (LLM 기반 관련성 판단)
"""

from typing import Dict, Any, Optional
import logging
import json

from ai_agent.utils.llm_client import LLMClient

logger = logging.getLogger(__name__)


class AdditionalDataHelper:
    """
    추가 데이터 관련성 판단 헬퍼

    각 Agent가 사용자 추가 데이터를 판단하고 활용할 수 있도록 지원하는 유틸리티

    주요 기능:
    - LLM 기반 관련성 판단
    - 관련 데이터 추출 및 구조화
    - Agent별 적용 가능 여부 확인
    """

    def __init__(self, llm_client: Optional[LLMClient] = None):
        """
        AdditionalDataHelper 초기화

        Args:
            llm_client: LLM 클라이언트 인스턴스 (없으면 자동 생성)
        """
        self.llm_client = llm_client or LLMClient(
            model='gpt-4o-mini',
            temperature=0.3,  # 관련성 판단은 낮은 temperature 사용
            max_tokens=4096  # 가이드라인 생성 시 더 많은 토큰 필요
        )
        self.logger = logger

    def generate_guidelines(
        self,
        additional_data: Dict[str, Any],
        agent_configs: list[Dict[str, str]]
    ) -> Dict[str, Any]:
        """
        중앙 가이드라인 생성 (하이브리드 방식)

        LLM을 1회 호출하여 모든 Agent에 대한 관련성 및 제안 인사이트 생성

        Args:
            additional_data: 사용자가 제공한 추가 데이터
                {
                    'raw_text': '건물 리모델링 2023년 완료, 태양광 200kW 설치 예정',
                    'metadata': {...}
                }
            agent_configs: Agent 설정 리스트
                [
                    {'name': 'impact_analysis', 'purpose': '전력 사용량 및 운영 영향 분석'},
                    {'name': 'strategy_generation', 'purpose': '대응 전략 수립'},
                    ...
                ]

        Returns:
            Agent별 가이드라인 딕셔너리
            {
                'impact_analysis': {
                    'relevance': 0.85,
                    'suggested_insights': ['인사이트 1', '인사이트 2'],
                    'reasoning': '판단 근거'
                },
                ...
            }
        """
        raw_text = additional_data.get('raw_text', '')

        if not raw_text or not raw_text.strip():
            # 추가 데이터가 없으면 빈 가이드라인 반환
            return {agent['name']: {'relevance': 0.0, 'suggested_insights': [], 'reasoning': '추가 데이터 없음'}
                    for agent in agent_configs}

        try:
            prompt = self._build_guidelines_prompt(raw_text, agent_configs)
            response_text = self.llm_client.invoke(prompt)

            # JSON 파싱 시도
            try:
                guidelines = json.loads(response_text)
                self.logger.info(f"중앙 가이드라인 생성 완료: {len(guidelines)}개 Agent")
                return guidelines
            except json.JSONDecodeError:
                self.logger.warning(f"LLM 응답 JSON 파싱 실패: {response_text[:200]}...")
                # fallback: 빈 가이드라인 반환
                return {agent['name']: {'relevance': 0.0, 'suggested_insights': [], 'reasoning': 'JSON 파싱 실패'}
                        for agent in agent_configs}

        except Exception as e:
            self.logger.error(f"가이드라인 생성 중 오류: {str(e)}", exc_info=True)
            return {agent['name']: {'relevance': 0.0, 'suggested_insights': [], 'reasoning': f'오류: {str(e)}'}
                    for agent in agent_configs}

    def _build_guidelines_prompt(
        self,
        raw_text: str,
        agent_configs: list[Dict[str, str]]
    ) -> str:
        """
        중앙 가이드라인 생성을 위한 LLM 프롬프트 구성

        Args:
            raw_text: 사용자 추가 데이터
            agent_configs: Agent 설정 리스트

        Returns:
            구성된 프롬프트 문자열
        """
        agent_list = "\n".join([f"- **{agent['name']}**: {agent['purpose']}" for agent in agent_configs])

        prompt = f"""
당신은 기후 리스크 분석 시스템의 데이터 분류 전문가입니다.
사용자가 제공한 추가 정보를 분석하여, 각 분석 Agent에 대한 가이드라인을 생성하세요.

## 사용자 추가 정보
```
{raw_text}
```

## 분석할 Agent 목록
{agent_list}

## 작업
각 Agent에 대해 다음을 생성하세요:
1. **관련성 점수 (relevance)**: 0.0 (전혀 무관) ~ 1.0 (매우 관련)
   - 0.7 이상: 매우 관련 (Agent가 반드시 활용해야 함)
   - 0.4 ~ 0.6: 부분 관련 (Agent가 선택적으로 활용)
   - 0.3 이하: 무관 (Agent가 무시해도 됨)

2. **제안 인사이트 (suggested_insights)**: Agent가 활용할 수 있는 핵심 정보 리스트
   - 구체적이고 실행 가능한 인사이트 제공
   - 관련성이 낮으면 빈 리스트 반환

3. **판단 근거 (reasoning)**: 관련성 점수 및 인사이트를 도출한 근거

## 출력 형식 (JSON)
**중요**: 반드시 아래 JSON 형식으로만 응답하세요. 마크다운이나 추가 설명 없이 순수 JSON만 출력하세요.

{{
    "impact_analysis": {{
        "relevance": 0.85,
        "suggested_insights": [
            "태양광 200kW 설치 계획으로 전력 사용량 15% 감소 예상",
            "리모델링으로 단열 성능 향상, 냉난방 에너지 10% 절감 가능"
        ],
        "reasoning": "전력 사용량 및 에너지 효율과 직접 연관됨"
    }},
    "strategy_generation": {{
        "relevance": 0.75,
        "suggested_insights": [
            "태양광 설치 계획을 재생에너지 전략으로 포함",
            "리모델링 완료로 추가 시설 개선 우선순위 낮음"
        ],
        "reasoning": "대응 전략 수립 시 기존 계획을 반영 가능"
    }},
    "vulnerability_analysis": {{
        "relevance": 0.30,
        "suggested_insights": [],
        "reasoning": "건물 구조 및 재료 정보 부족, 취약성 평가에 직접 사용 어려움"
    }},
    "report_generation": {{
        "relevance": 0.60,
        "suggested_insights": [
            "리모델링 및 태양광 계획을 긍정적 개선 사항으로 명시"
        ],
        "reasoning": "보고서에 포함할 만한 긍정적 요소"
    }}
}}
"""
        return prompt

    def check_relevance(
        self,
        additional_data: Dict[str, Any],
        agent_name: str,
        agent_purpose: str
    ) -> Dict[str, Any]:
        """
        추가 데이터가 특정 Agent에 관련이 있는지 판단

        Args:
            additional_data: 사용자가 제공한 추가 데이터
                {
                    'raw_text': '건물 리모델링 2023년 완료, 태양광 패널 200kW 설치 예정',
                    'metadata': {'source': 'user_input', 'timestamp': '2025-12-01'}
                }
            agent_name: Agent 이름 (예: 'impact_analysis', 'strategy_generation')
            agent_purpose: Agent의 목적/역할 설명 (예: '전력 사용량 및 운영 영향 분석')

        Returns:
            관련성 판단 결과
            {
                'is_relevant': True/False,
                'relevance_score': 0.0 ~ 1.0,
                'extracted_insights': ['insight1', 'insight2', ...],
                'reasoning': 'LLM 판단 근거'
            }
        """
        raw_text = additional_data.get('raw_text', '')

        if not raw_text or not raw_text.strip():
            return {
                'is_relevant': False,
                'relevance_score': 0.0,
                'extracted_insights': [],
                'reasoning': '추가 데이터가 비어있습니다.'
            }

        try:
            prompt = self._build_relevance_prompt(raw_text, agent_name, agent_purpose)
            response_text = self.llm_client.invoke(prompt)

            # JSON 파싱 시도
            try:
                result = json.loads(response_text)
                return {
                    'is_relevant': result.get('is_relevant', False),
                    'relevance_score': result.get('relevance_score', 0.0),
                    'extracted_insights': result.get('extracted_insights', []),
                    'reasoning': result.get('reasoning', '')
                }
            except json.JSONDecodeError:
                # JSON 파싱 실패 시 fallback
                self.logger.warning(f"LLM 응답 JSON 파싱 실패: {response_text[:100]}...")
                return {
                    'is_relevant': False,
                    'relevance_score': 0.0,
                    'extracted_insights': [],
                    'reasoning': f'JSON 파싱 실패: {response_text[:100]}'
                }

        except Exception as e:
            self.logger.error(f"관련성 판단 중 오류: {str(e)}", exc_info=True)
            return {
                'is_relevant': False,
                'relevance_score': 0.0,
                'extracted_insights': [],
                'reasoning': f'오류 발생: {str(e)}'
            }

    def _build_relevance_prompt(
        self,
        raw_text: str,
        agent_name: str,
        agent_purpose: str
    ) -> str:
        """
        관련성 판단을 위한 LLM 프롬프트 구성

        Args:
            raw_text: 사용자 추가 데이터 (자유 형식 텍스트)
            agent_name: Agent 이름
            agent_purpose: Agent 목적/역할

        Returns:
            구성된 프롬프트 문자열
        """
        prompt = f"""
당신은 데이터 분석 전문가입니다.
사용자가 제공한 추가 정보가 특정 분석 Agent와 관련이 있는지 판단해주세요.

## Agent 정보
- **Agent 이름**: {agent_name}
- **Agent 목적**: {agent_purpose}

## 사용자 추가 정보
```
{raw_text}
```

## 작업
1. 위 추가 정보가 이 Agent의 분석에 관련이 있는지 판단하세요.
2. 관련성 점수를 0.0 (전혀 무관) ~ 1.0 (매우 관련) 사이로 평가하세요.
3. 관련이 있다면, Agent가 활용할 수 있는 핵심 인사이트를 추출하세요.
4. 판단 근거를 명확히 설명하세요.

## 판단 기준
- 0.7 이상: 매우 관련 (Agent 분석에 직접 활용 가능)
- 0.4 ~ 0.6: 부분 관련 (일부 활용 가능)
- 0.3 이하: 무관 (Agent 분석과 무관)

## 출력 형식 (JSON)
{{
    "is_relevant": true/false,  // 0.4 이상이면 true
    "relevance_score": 0.85,
    "extracted_insights": [
        "인사이트 1",
        "인사이트 2"
    ],
    "reasoning": "판단 근거 설명"
}}

**중요**: 반드시 위 JSON 형식으로만 응답하세요. 추가 설명이나 마크다운 없이 순수 JSON만 출력하세요.
"""
        return prompt

    def apply_guideline(
        self,
        base_analysis: Dict[str, Any],
        guideline: Dict[str, Any],
        additional_data: Dict[str, Any],
        domain_context: str
    ) -> Dict[str, Any]:
        """
        Agent가 가이드라인을 적용하여 분석 결과를 보강

        Args:
            base_analysis: 기본 분석 결과
            guideline: 중앙 노드가 생성한 가이드라인
                {
                    'relevance': 0.85,
                    'suggested_insights': ['인사이트 1', '인사이트 2'],
                    'reasoning': '판단 근거'
                }
            additional_data: 원본 추가 데이터
            domain_context: Agent의 도메인 컨텍스트 (예: '전력 사용량 및 운영 영향')

        Returns:
            보강된 분석 결과
        """
        # 가이드라인 인사이트를 분석 결과에 추가
        enhanced_analysis = base_analysis.copy()

        if 'additional_insights' not in enhanced_analysis:
            enhanced_analysis['additional_insights'] = []

        # 가이드라인의 제안 인사이트 추가
        suggested_insights = guideline.get('suggested_insights', [])
        enhanced_analysis['additional_insights'].extend(suggested_insights)

        # 메타데이터 추가
        enhanced_analysis['enhanced_by_guideline'] = True
        enhanced_analysis['guideline_relevance'] = guideline.get('relevance', 0.0)
        enhanced_analysis['guideline_reasoning'] = guideline.get('reasoning', '')

        self.logger.info(
            f"가이드라인 적용 완료 (domain: {domain_context}, "
            f"relevance: {guideline.get('relevance', 0.0):.2f}, "
            f"insights: {len(suggested_insights)}개)"
        )

        return enhanced_analysis

    def extract_applicable_data(
        self,
        additional_data: Dict[str, Any],
        agent_name: str,
        relevance_result: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        관련성 판단 결과를 바탕으로 Agent에 적용 가능한 데이터를 추출

        Args:
            additional_data: 원본 추가 데이터
            agent_name: Agent 이름
            relevance_result: check_relevance()의 반환 결과

        Returns:
            Agent에 적용 가능한 데이터 (None이면 적용 불가)
            {
                'source': 'additional_data',
                'agent_name': 'impact_analysis',
                'insights': ['인사이트 1', '인사이트 2'],
                'raw_text': '원본 텍스트',
                'metadata': {...}
            }
        """
        if not relevance_result.get('is_relevant', False):
            return None

        if relevance_result.get('relevance_score', 0.0) < 0.4:
            return None

        return {
            'source': 'additional_data',
            'agent_name': agent_name,
            'insights': relevance_result.get('extracted_insights', []),
            'raw_text': additional_data.get('raw_text', ''),
            'metadata': additional_data.get('metadata', {}),
            'relevance_score': relevance_result.get('relevance_score', 0.0),
            'reasoning': relevance_result.get('reasoning', '')
        }

    def apply_to_agent_context(
        self,
        state: Dict[str, Any],
        agent_name: str,
        agent_purpose: str
    ) -> Optional[Dict[str, Any]]:
        """
        State에서 추가 데이터를 확인하고, 관련성이 있으면 Agent 컨텍스트에 적용

        이 메서드는 각 Agent에서 호출하여 간편하게 추가 데이터를 활용할 수 있습니다.

        Args:
            state: LangGraph State (additional_data 포함)
            agent_name: Agent 이름
            agent_purpose: Agent 목적

        Returns:
            적용 가능한 데이터 (None이면 적용 불가)

        Example:
            >>> helper = AdditionalDataHelper()
            >>> applicable_data = helper.apply_to_agent_context(
            ...     state,
            ...     'impact_analysis',
            ...     '전력 사용량 및 운영 영향 분석'
            ... )
            >>> if applicable_data:
            ...     print(f"추가 인사이트: {applicable_data['insights']}")
        """
        additional_data = state.get('additional_data')

        if not additional_data:
            return None

        # 관련성 판단
        relevance_result = self.check_relevance(
            additional_data,
            agent_name,
            agent_purpose
        )

        # 적용 가능한 데이터 추출
        applicable_data = self.extract_applicable_data(
            additional_data,
            agent_name,
            relevance_result
        )

        if applicable_data:
            self.logger.info(
                f"[{agent_name}] 추가 데이터 적용 가능 "
                f"(relevance_score={applicable_data['relevance_score']:.2f})"
            )
            return applicable_data
        else:
            self.logger.debug(f"[{agent_name}] 추가 데이터 무관 또는 관련성 낮음")
            return None


# Agent 사용 예시 (주석)
"""
from ai_agent.utils.additional_data_helper import AdditionalDataHelper


class ImpactAnalysisAgent:
    def __init__(self):
        self.additional_data_helper = AdditionalDataHelper()

    def analyze(self, state):
        # 추가 데이터 확인
        applicable_data = self.additional_data_helper.apply_to_agent_context(
            state,
            agent_name='impact_analysis',
            agent_purpose='전력 사용량 및 운영 영향 분석'
        )

        # 기본 분석 수행
        impact_result = self._perform_basic_analysis(state)

        # 추가 데이터가 관련 있으면 분석에 반영
        if applicable_data:
            impact_result = self._enhance_analysis_with_additional_data(
                impact_result,
                applicable_data
            )

        return impact_result

    def _enhance_analysis_with_additional_data(self, base_result, applicable_data):
        # 추가 인사이트를 분석 결과에 통합
        base_result['additional_insights'] = applicable_data['insights']
        base_result['enhanced_by_user_data'] = True

        # 예: 태양광 패널 설치 계획이 있으면 전력 영향 조정
        for insight in applicable_data['insights']:
            if '태양광' in insight or 'solar' in insight.lower():
                base_result['energy_impact_adjustment'] = -0.15  # 15% 감소
                base_result['notes'].append(
                    f"사용자 추가 정보 반영: {insight}"
                )

        return base_result
"""
