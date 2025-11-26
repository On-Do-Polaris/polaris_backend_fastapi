'''
파일명: llm_client.py
최종 수정일: 2025-11-25
버전: v02
파일 개요: LLM 클라이언트 (LangChain + OpenAI + LangSmith 트레이싱 통합)
변경 이력:
	- v01 (2025-11-17): 초기 버전 (Mock 구현)
	- v02 (2025-11-25): LangChain ChatOpenAI 통합, LangSmith 트레이싱 적용
'''
from typing import Dict, Any, List, Optional, Union
import logging
import os
import json
from dotenv import load_dotenv

# .env 파일 로드 (override=True: 시스템 환경변수 덮어쓰기)
load_dotenv(override=True)

logger = logging.getLogger(__name__)

# LangSmith 환경 변수 설정
if os.getenv('LANGSMITH_ENABLED', 'false').lower() == 'true':
	os.environ['LANGCHAIN_TRACING_V2'] = 'true'
	os.environ['LANGCHAIN_PROJECT'] = os.getenv('LANGSMITH_PROJECT', 'skax-physical-risk-dev')
	os.environ['LANGCHAIN_ENDPOINT'] = os.getenv('LANGSMITH_ENDPOINT', 'https://api.smith.langchain.com')
	if os.getenv('LANGSMITH_API_KEY'):
		os.environ['LANGCHAIN_API_KEY'] = os.getenv('LANGSMITH_API_KEY')
	logger.info(f"LangSmith tracing enabled for project: {os.environ['LANGCHAIN_PROJECT']}")

# LangChain 임포트
try:
	from langchain_openai import ChatOpenAI
	from langchain_core.messages import HumanMessage, SystemMessage
	from langsmith import traceable
	LANGCHAIN_AVAILABLE = True
except ImportError:
	logger.warning("langchain-openai not installed. Using fallback mode.")
	LANGCHAIN_AVAILABLE = False
	traceable = lambda *args, **kwargs: lambda func: func  # No-op decorator


class LLMClient:
	"""
	LLM 클라이언트
	LangChain ChatOpenAI를 활용한 대응 전략 생성 및 자연어 처리
	LangSmith 자동 트레이싱 지원
	"""

	def __init__(self, model: str = 'gpt-4o-mini', temperature: float = 0.7, max_tokens: int = 8192):
		"""
		LLMClient 초기화

		Args:
			model: 사용할 LLM 모델 (기본값: gpt-4o-mini)
			temperature: 생성 다양성 (0.0 ~ 1.0)
			max_tokens: 최대 생성 토큰 수 (기본값: 8192, 상세한 리포트 생성용)
		"""
		self.model = model
		self.temperature = temperature
		self.max_tokens = max_tokens
		self.api_key = os.getenv('OPENAI_API_KEY', '')
		self.logger = logger

		# DEBUG: API 키 확인
		self.logger.info(f"[DEBUG] LLMClient init - API key length: {len(self.api_key) if self.api_key else 0}")
		self.logger.info(f"[DEBUG] LLMClient init - API key present: {bool(self.api_key)}")

		# LangChain ChatOpenAI 초기화
		if LANGCHAIN_AVAILABLE and self.api_key:
			self.llm = ChatOpenAI(
				model=model,
				temperature=temperature,
				max_tokens=max_tokens,  # 최대 토큰 수 제한
				openai_api_key=self.api_key
				# response_format JSON 모드는 프롬프트에 "json" 키워드 필수
				# 기본적으로 비활성화하고, 각 Agent에서 필요시 개별 설정
			)
			self.logger.info(f"LLMClient 초기화 완료: {model} (max_tokens={max_tokens}, LangChain + LangSmith)")
		else:
			self.llm = None
			self.logger.warning(f"LLMClient 초기화 (Fallback 모드): LangChain 미설치 또는 API 키 없음")

	@traceable(name="llm_invoke", tags=["llm", "invoke"])
	def invoke(self, prompt: Union[str, List[Dict[str, str]]], **kwargs) -> str:
		"""
		LLM 동기 호출 (LangSmith 트레이싱)

		Args:
			prompt: 프롬프트 문자열 또는 메시지 리스트
			**kwargs: 추가 파라미터

		Returns:
			LLM 응답 문자열
		"""
		if self.llm is None:
			return self._fallback_invoke(prompt)

		try:
			if isinstance(prompt, str):
				messages = [HumanMessage(content=prompt)]
			elif isinstance(prompt, list):
				messages = [
					SystemMessage(content=msg["content"]) if msg.get("role") == "system"
					else HumanMessage(content=msg["content"])
					for msg in prompt
				]
			else:
				messages = [HumanMessage(content=str(prompt))]

			response = self.llm.invoke(messages)
			return response.content

		except Exception as e:
			self.logger.error(f"LLM 호출 실패: {e}")
			return self._fallback_invoke(prompt)

	@traceable(name="llm_ainvoke", tags=["llm", "async"])
	async def ainvoke(self, prompt: Union[str, List[Dict[str, str]]], **kwargs) -> str:
		"""
		LLM 비동기 호출 (LangSmith 트레이싱)

		Args:
			prompt: 프롬프트 문자열 또는 메시지 리스트
			**kwargs: 추가 파라미터

		Returns:
			LLM 응답 문자열
		"""
		if self.llm is None:
			return self._fallback_invoke(prompt)

		try:
			if isinstance(prompt, str):
				messages = [HumanMessage(content=prompt)]
			elif isinstance(prompt, list):
				messages = [
					SystemMessage(content=msg["content"]) if msg.get("role") == "system"
					else HumanMessage(content=msg["content"])
					for msg in prompt
				]
			else:
				messages = [HumanMessage(content=str(prompt))]

			response = await self.llm.ainvoke(messages)
			return response.content

		except Exception as e:
			self.logger.error(f"LLM 비동기 호출 실패: {e}")
			return self._fallback_invoke(prompt)

	def generate(self, prompt: Union[str, List[Dict[str, str]]], **kwargs) -> str:
		"""
		generate() 메소드는 invoke()의 alias입니다.
		일부 Agent가 generate()를 호출하므로 호환성을 위해 제공합니다.
		"""
		return self.invoke(prompt, **kwargs)

	def _fallback_invoke(self, _prompt: Union[str, List]) -> str:
		"""Fallback 응답 (LangChain 미설치 시)"""
		self.logger.warning("Fallback 모드로 동작 중 - Mock 응답 반환")
		return json.dumps({
			"status": "fallback",
			"message": "LangChain not available. Please install langchain-openai."
		})

	@traceable(name="generate_response_strategy", tags=["strategy", "generation"])
	def generate_response_strategy(
		self,
		risk_analysis_results: Dict[str, Any],
		report_template: Dict[str, Any],
		context: Optional[Dict[str, Any]] = None
	) -> Dict[str, Any]:
		"""
		대응 전략 생성
		리스크 분석 결과를 바탕으로 LLM 기반 대응 전략 생성

		Args:
			risk_analysis_results: 리스크 분석 결과
				- physical_risk_scores: 물리적 리스크 점수
				- aal_analysis: AAL 분석 결과
			report_template: 리포트 템플릿
			context: 추가 컨텍스트 정보

		Returns:
			대응 전략 딕셔너리
				- strategy: 생성된 대응 전략
				- reasoning: LLM 추론 과정
				- recommendations: 권장 사항 리스트
				- status: 생성 상태
		"""
		self.logger.info("LLM 기반 대응 전략 생성 시작")

		try:
			# 프롬프트 구성
			prompt = self._build_strategy_prompt(risk_analysis_results, report_template, context)

			# LLM 호출
			if self.llm:
				response_text = self.invoke(prompt)
				try:
					# JSON 응답 파싱 시도
					strategy_result = json.loads(response_text)
					strategy_result['status'] = 'completed'
				except json.JSONDecodeError:
					# JSON 파싱 실패 시 텍스트 응답 사용
					strategy_result = {
						'strategy': {'overview': response_text},
						'status': 'completed'
					}
			else:
				# Fallback: Mock 응답
				strategy_result = self._generate_mock_strategy(risk_analysis_results)

			self.logger.info("대응 전략 생성 완료")
			return strategy_result

		except Exception as e:
			self.logger.error(f"대응 전략 생성 중 오류: {str(e)}", exc_info=True)
			return {
				'status': 'failed',
				'error': str(e)
			}

	def _build_strategy_prompt(
		self,
		risk_analysis_results: Dict[str, Any],
		report_template: Dict[str, Any],
		context: Optional[Dict[str, Any]]
	) -> str:
		"""
		대응 전략 생성을 위한 LLM 프롬프트 구성

		Args:
			risk_analysis_results: 리스크 분석 결과
			report_template: 리포트 템플릿
			context: 추가 컨텍스트

		Returns:
			구성된 프롬프트 문자열
		"""
		prompt = f"""
당신은 기후 리스크 대응 전략 전문가입니다.
다음 리스크 분석 결과를 바탕으로 구체적이고 실행 가능한 대응 전략을 제시하세요.

## 리스크 분석 결과
{self._format_risk_results(risk_analysis_results)}

## 요구사항
1. 각 리스크별 구체적 대응 방안 제시
2. 우선순위가 높은 리스크부터 순서대로 기술
3. 단기(1년 이내), 중기(1-3년), 장기(3년 이상) 대응 계획 구분
4. 예상 투자 비용 및 효과 명시
5. 실행 가능한 액션 아이템 제공

## 출력 형식
JSON 형식으로 다음 구조에 맞춰 응답하세요:
{{
	"strategy": {{
		"overview": "전체 전략 개요",
		"high_priority_risks": ["리스크1", "리스크2"],
		"action_plans": [
			{{
				"risk_type": "리스크 타입",
				"short_term": "단기 대응 방안",
				"mid_term": "중기 대응 방안",
				"long_term": "장기 대응 방안",
				"estimated_cost": "예상 비용",
				"expected_effect": "기대 효과"
			}}
		]
	}},
	"recommendations": ["권장사항1", "권장사항2", "..."],
	"reasoning": "전략 수립 근거 및 추론 과정"
}}
"""
		return prompt

	def _format_risk_results(self, risk_analysis_results: Dict[str, Any]) -> str:
		"""
		리스크 분석 결과를 프롬프트용 텍스트로 포맷팅

		Args:
			risk_analysis_results: 리스크 분석 결과

		Returns:
			포맷팅된 텍스트
		"""
		physical_scores = risk_analysis_results.get('physical_risk_scores', {})
		aal_analysis = risk_analysis_results.get('aal_analysis', {})

		formatted_text = "### 물리적 리스크 점수\n"
		for risk_type, score_data in physical_scores.items():
			formatted_text += f"- {risk_type}: {score_data.get('physical_risk_score', 0):.4f}\n"

		formatted_text += "\n### 연평균 재무 손실\n"
		for risk_type, aal_data in aal_analysis.items():
			formatted_text += f"- {risk_type}: {aal_data.get('financial_loss', 0):,.0f}원\n"

		return formatted_text

	def _generate_mock_strategy(self, risk_analysis_results: Dict[str, Any]) -> Dict[str, Any]:
		"""
		임시 Mock 대응 전략 생성 (실제 LLM 구현 전 테스트용)

		Args:
			risk_analysis_results: 리스크 분석 결과

		Returns:
			Mock 전략 딕셔너리
		"""
		physical_scores = risk_analysis_results.get('physical_risk_scores', {})

		# 리스크 점수 기준 정렬
		sorted_risks = sorted(
			physical_scores.items(),
			key=lambda x: x[1].get('physical_risk_score', 0),
			reverse=True
		)

		high_priority_risks = [risk[0] for risk in sorted_risks[:3]]

		return {
			'strategy': {
				'overview': '분석 결과 기반 기후 리스크 대응 전략을 수립하였습니다',
				'high_priority_risks': high_priority_risks,
				'action_plans': [
					{
						'risk_type': risk_type,
						'short_term': f'{risk_type} 모니터링 시스템 구축',
						'mid_term': f'{risk_type} 대응 인프라 강화',
						'long_term': f'{risk_type} 복원력 확보',
						'estimated_cost': '1억 ~ 5억원',
						'expected_effect': '리스크 노출도 30% 감소'
					}
					for risk_type in high_priority_risks
				]
			},
			'recommendations': [
				'정기적인 리스크 재평가 실시',
				'비상 대응 매뉴얼 수립',
				'보험 가입 검토'
			],
			'reasoning': '물리적 리스크 점수가 높은 상위 3개 리스크를 우선 대응 대상으로 선정하였습니다',
			'status': 'completed'
		}
