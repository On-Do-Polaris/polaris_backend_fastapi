'''
파일명: strategy_generation_agent.py
최종 수정일: 2025-11-11
버전: v01
파일 개요: 대응 전략 생성 에이전트 (LLM + RAG 기반)
변경 이력:
	- 2025-11-11: v01 - Super Agent 구조에 맞게 신규 생성
'''
from typing import Dict, Any
import logging


logger = logging.getLogger(__name__)


class StrategyGenerationAgent:
	"""
	대응 전략 생성 에이전트
	LLM과 RAG를 활용하여 맞춤형 대응 전략 및 권고사항 생성
	"""

	def __init__(self, llm_client, rag_engine):
		"""
		StrategyGenerationAgent 초기화

		Args:
			llm_client: LLM 클라이언트 인스턴스
			rag_engine: RAG 엔진 인스턴스
		"""
		self.llm_client = llm_client
		self.rag_engine = rag_engine
		self.logger = logger
		self.logger.info("StrategyGenerationAgent 초기화")

	def generate_strategy(
		self,
		target_location: Dict[str, Any],
		vulnerability_analysis: Dict[str, Any],
		aal_analysis: Dict[str, Any],
		physical_risk_scores: Dict[str, Any],
		report_template: Dict[str, Any]
	) -> Dict[str, Any]:
		"""
		대응 전략 생성
		LLM을 활용하여 리스크별 맞춤형 대응 전략 및 권고사항 생성

		Args:
			target_location: 분석 대상 위치 정보
			vulnerability_analysis: 취약성 분석 결과
			aal_analysis: AAL 분석 결과
			physical_risk_scores: 물리적 리스크 점수
			report_template: 리포트 템플릿

		Returns:
			대응 전략 딕셔너리
				- overall_strategy: 종합 대응 전략
				- risk_specific_strategies: 리스크별 전략
				- recommendations: 권고사항
				- priority_actions: 우선순위 조치사항
				- status: 생성 상태
		"""
		self.logger.info("대응 전략 생성 시작")

		try:
			# 1. 상위 리스크 식별
			top_risks = self._identify_top_risks(physical_risk_scores, aal_analysis)

			# 2. RAG를 통한 유사 사례 검색
			similar_cases = self._retrieve_similar_cases(top_risks, vulnerability_analysis)

			# 3. LLM을 활용한 종합 대응 전략 생성
			overall_strategy = self._generate_overall_strategy(
				target_location,
				top_risks,
				vulnerability_analysis,
				similar_cases
			)

			# 4. 리스크별 구체적 전략 생성
			risk_specific_strategies = self._generate_risk_specific_strategies(
				top_risks,
				aal_analysis,
				similar_cases
			)

			# 5. 권고사항 생성
			recommendations = self._generate_recommendations(
				vulnerability_analysis,
				top_risks,
				aal_analysis
			)

			# 6. 우선순위 조치사항 정의
			priority_actions = self._define_priority_actions(
				top_risks,
				vulnerability_analysis
			)

			result = {
				'overall_strategy': overall_strategy,
				'risk_specific_strategies': risk_specific_strategies,
				'recommendations': recommendations,
				'priority_actions': priority_actions,
				'top_risks': top_risks,
				'status': 'completed'
			}

			self.logger.info(f"대응 전략 생성 완료: {len(risk_specific_strategies)}개 리스크별 전략")
			return result

		except Exception as e:
			self.logger.error(f"대응 전략 생성 중 오류: {str(e)}", exc_info=True)
			return {
				'status': 'failed',
				'error': str(e)
			}

	def _identify_top_risks(
		self,
		physical_risk_scores: Dict[str, Any],
		aal_analysis: Dict[str, Any]
	) -> list:
		"""
		상위 리스크 식별 (점수 + AAL 기반)

		Args:
			physical_risk_scores: 물리적 리스크 점수
			aal_analysis: AAL 분석 결과

		Returns:
			상위 리스크 목록 (최대 5개)
		"""
		risk_ranking = []

		for risk_type, score_data in physical_risk_scores.items():
			risk_score = score_data.get('physical_risk_score_100', 0)
			aal_data = aal_analysis.get(risk_type, {})
			financial_loss = aal_data.get('financial_loss', 0)

			# 종합 점수 = 100점 스케일 점수 * 0.6 + AAL 재무손실 정규화 * 0.4
			combined_score = risk_score * 0.6 + min(financial_loss / 1e9, 100) * 0.4

			risk_ranking.append({
				'risk_type': risk_type,
				'risk_score': risk_score,
				'financial_loss': financial_loss,
				'combined_score': combined_score
			})

		# 종합 점수 기준 정렬
		risk_ranking.sort(key=lambda x: x['combined_score'], reverse=True)

		return risk_ranking[:5]  # 상위 5개

	def _retrieve_similar_cases(
		self,
		top_risks: list,
		vulnerability_analysis: Dict[str, Any]
	) -> list:
		"""
		RAG를 통한 유사 사례 검색

		Args:
			top_risks: 상위 리스크 목록
			vulnerability_analysis: 취약성 분석

		Returns:
			유사 사례 목록
		"""
		risk_types = [r['risk_type'] for r in top_risks]
		query = f"리스크: {', '.join(risk_types)}, 취약성: {vulnerability_analysis.get('overall_vulnerability_score', 0):.2f}"

		# RAG 검색 (Mock)
		similar_cases = self.rag_engine.retrieve_similar_reports(query, top_k=3)

		return similar_cases

	def _generate_overall_strategy(
		self,
		target_location: Dict[str, Any],
		top_risks: list,
		vulnerability_analysis: Dict[str, Any],
		similar_cases: list
	) -> str:
		"""
		LLM을 활용한 종합 대응 전략 생성

		Args:
			target_location: 위치 정보
			top_risks: 상위 리스크
			vulnerability_analysis: 취약성 분석
			similar_cases: 유사 사례

		Returns:
			종합 대응 전략 텍스트
		"""
		prompt = f"""
다음 정보를 바탕으로 종합 대응 전략을 작성하세요:

위치: {target_location.get('name', '알 수 없음')}
주요 리스크: {', '.join([r['risk_type'] for r in top_risks])}
취약성 점수: {vulnerability_analysis.get('overall_vulnerability_score', 0):.2f}

유사 사례:
{similar_cases}

종합 대응 전략을 3-5문장으로 작성하세요.
"""

		# LLM 호출
		overall_strategy = self.llm_client.generate_response_strategy(prompt, risk_data={})

		return overall_strategy

	def _generate_risk_specific_strategies(
		self,
		top_risks: list,
		aal_analysis: Dict[str, Any],
		similar_cases: list
	) -> Dict[str, str]:
		"""
		리스크별 구체적 전략 생성

		Args:
			top_risks: 상위 리스크
			aal_analysis: AAL 분석
			similar_cases: 유사 사례

		Returns:
			리스크별 전략 딕셔너리
		"""
		strategies = {}

		for risk in top_risks:
			risk_type = risk['risk_type']
			aal_data = aal_analysis.get(risk_type, {})

			prompt = f"""
리스크 타입: {risk_type}
재무 손실: {aal_data.get('financial_loss', 0):,.0f}원
AAL: {aal_data.get('aal_percentage', 0):.2f}%

이 리스크에 대한 구체적 대응 전략을 2-3문장으로 작성하세요.
"""

			strategy = self.llm_client.generate_response_strategy(prompt, risk_data=aal_data)
			strategies[risk_type] = strategy

		return strategies

	def _generate_recommendations(
		self,
		vulnerability_analysis: Dict[str, Any],
		top_risks: list,
		aal_analysis: Dict[str, Any]
	) -> list:
		"""
		권고사항 생성

		Args:
			vulnerability_analysis: 취약성 분석
			top_risks: 상위 리스크
			aal_analysis: AAL 분석

		Returns:
			권고사항 목록
		"""
		recommendations = [
			"정기적인 리스크 모니터링 체계 구축",
			"취약성 개선을 위한 시설 보강",
			"비상 대응 매뉴얼 수립 및 정기 훈련",
			"보험 가입 검토 (재무 손실 완화)",
			"리스크별 조기 경보 시스템 도입"
		]

		return recommendations[:5]

	def _define_priority_actions(
		self,
		top_risks: list,
		vulnerability_analysis: Dict[str, Any]
	) -> list:
		"""
		우선순위 조치사항 정의

		Args:
			top_risks: 상위 리스크
			vulnerability_analysis: 취약성 분석

		Returns:
			우선순위 조치사항 목록
		"""
		actions = []

		# 최우선 리스크 기반 조치
		if top_risks:
			top_risk = top_risks[0]
			actions.append({
				'priority': 1,
				'action': f"{top_risk['risk_type']} 리스크 대응 체계 즉시 구축",
				'timeline': '1개월 이내'
			})

		# 취약성 개선
		if vulnerability_analysis.get('overall_vulnerability_score', 0) > 0.6:
			actions.append({
				'priority': 2,
				'action': "건물 취약성 개선 (내진 보강, 소방 설비 개선)",
				'timeline': '6개월 이내'
			})

		# 모니터링 체계
		actions.append({
			'priority': 3,
			'action': "통합 리스크 모니터링 시스템 구축",
			'timeline': '3개월 이내'
		})

		return actions
