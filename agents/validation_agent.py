'''
파일명: validation_agent.py
최종 수정일: 2025-11-11
버전: v00
파일 개요: 리포트 검증 Agent (정확성, 일관성, 완전성 확인)
'''
from typing import Dict, Any, List
import logging


logger = logging.getLogger(__name__)


class ValidationAgent:
	"""
	리포트 검증 Agent
	생성된 리포트의 정확성, 일관성, 완전성을 검증하고 피드백 제공
	"""

	def __init__(self):
		"""
		ValidationAgent 초기화
		"""
		self.logger = logger
		self.logger.info("ValidationAgent 초기화 완료")

	def validate_report(
		self,
		generated_report: Dict[str, Any],
		physical_risk_scores: Dict[str, Any],
		aal_analysis: Dict[str, Any],
		response_strategy: Dict[str, Any]
	) -> Dict[str, Any]:
		"""
		리포트 종합 검증

		Args:
			generated_report: 생성된 리포트
			physical_risk_scores: 물리적 리스크 점수 (원본 데이터)
			aal_analysis: AAL 분석 결과 (원본 데이터)
			response_strategy: 대응 전략 (원본 데이터)

		Returns:
			검증 결과 딕셔너리
				- accuracy_check: 정확성 확인 결과
				- consistency_check: 일관성 확인 결과
				- completeness_check: 완전성 확인 결과
				- issues_found: 발견된 문제점 리스트
				- improvement_suggestions: 개선 제안 리스트
				- validation_passed: 검증 통과 여부
				- status: 검증 상태
		"""
		self.logger.info("리포트 검증 시작")

		try:
			# 1. 정확성 검증 (데이터 일치 여부)
			accuracy_check, accuracy_issues = self._check_accuracy(
				generated_report,
				physical_risk_scores,
				aal_analysis
			)

			# 2. 일관성 검증 (논리적 모순 여부)
			consistency_check, consistency_issues = self._check_consistency(
				generated_report,
				response_strategy
			)

			# 3. 완전성 검증 (필수 섹션 포함 여부)
			completeness_check, completeness_issues = self._check_completeness(generated_report)

			# 전체 이슈 통합
			all_issues = accuracy_issues + consistency_issues + completeness_issues

			# 개선 제안 생성
			improvement_suggestions = self._generate_improvement_suggestions(all_issues)

			# 검증 통과 여부 판단
			validation_passed = accuracy_check and consistency_check and completeness_check

			result = {
				'accuracy_check': accuracy_check,
				'consistency_check': consistency_check,
				'completeness_check': completeness_check,
				'issues_found': all_issues,
				'improvement_suggestions': improvement_suggestions,
				'validation_passed': validation_passed,
				'status': 'completed'
			}

			if validation_passed:
				self.logger.info("리포트 검증 통과")
			else:
				self.logger.warning(f"리포트 검증 미달: {len(all_issues)}개 이슈 발견")

			return result

		except Exception as e:
			self.logger.error(f"리포트 검증 중 오류: {str(e)}", exc_info=True)
			return {
				'status': 'failed',
				'error': str(e)
			}

	def _check_accuracy(
		self,
		generated_report: Dict[str, Any],
		physical_risk_scores: Dict[str, Any],
		aal_analysis: Dict[str, Any]
	) -> tuple[bool, List[str]]:
		"""
		정확성 검증
		리포트에 기재된 수치가 원본 데이터와 일치하는지 확인

		Args:
			generated_report: 생성된 리포트
			physical_risk_scores: 물리적 리스크 점수 원본
			aal_analysis: AAL 분석 결과 원본

		Returns:
			(정확성 통과 여부, 발견된 이슈 리스트)
		"""
		issues = []

		# 리포트에서 리스크 점수 추출 및 비교
		report_risk_scores = generated_report.get('risk_scores', {})
		for risk_type, original_score in physical_risk_scores.items():
			report_score = report_risk_scores.get(risk_type, {}).get('physical_risk_score')
			original_value = original_score.get('physical_risk_score')

			if report_score is None:
				issues.append(f"정확성 오류: {risk_type} 리스크 점수 누락")
			elif abs(report_score - original_value) > 0.01:  # 오차 허용 범위 0.01
				issues.append(
					f"정확성 오류: {risk_type} 리스크 점수 불일치 "
					f"(리포트: {report_score:.4f}, 원본: {original_value:.4f})"
				)

		# AAL 데이터 검증
		report_aal = generated_report.get('aal_results', {})
		for risk_type, original_aal in aal_analysis.items():
			report_aal_value = report_aal.get(risk_type, {}).get('aal')
			original_aal_value = original_aal.get('aal')

			if report_aal_value is None:
				issues.append(f"정확성 오류: {risk_type} AAL 데이터 누락")
			elif abs(report_aal_value - original_aal_value) > 0.001:
				issues.append(
					f"정확성 오류: {risk_type} AAL 불일치 "
					f"(리포트: {report_aal_value:.4f}, 원본: {original_aal_value:.4f})"
				)

		accuracy_passed = len(issues) == 0
		return accuracy_passed, issues

	def _check_consistency(
		self,
		generated_report: Dict[str, Any],
		response_strategy: Dict[str, Any]
	) -> tuple[bool, List[str]]:
		"""
		일관성 검증
		리포트 내용 간 논리적 모순이 없는지 확인

		Args:
			generated_report: 생성된 리포트
			response_strategy: 대응 전략

		Returns:
			(일관성 통과 여부, 발견된 이슈 리스트)
		"""
		issues = []

		# 우선순위 리스크와 대응 전략 일치 여부 확인
		report_priority_risks = generated_report.get('high_priority_risks', [])
		strategy_priority_risks = response_strategy.get('strategy', {}).get('high_priority_risks', [])

		if set(report_priority_risks) != set(strategy_priority_risks):
			issues.append(
				f"일관성 오류: 리포트의 우선순위 리스크({report_priority_risks})와 "
				f"전략의 우선순위 리스크({strategy_priority_risks})가 불일치"
			)

		# 리스크 점수와 우선순위 순서 일치 여부 확인
		report_risk_scores = generated_report.get('risk_scores', {})
		if report_priority_risks:
			top_risk = report_priority_risks[0]
			top_risk_score = report_risk_scores.get(top_risk, {}).get('physical_risk_score', 0)

			for risk_type, risk_data in report_risk_scores.items():
				if risk_type != top_risk:
					other_score = risk_data.get('physical_risk_score', 0)
					if other_score > top_risk_score:
						issues.append(
							f"일관성 오류: 최우선 리스크({top_risk}, {top_risk_score:.4f})보다 "
							f"{risk_type}의 점수({other_score:.4f})가 더 높음"
						)

		consistency_passed = len(issues) == 0
		return consistency_passed, issues

	def _check_completeness(self, generated_report: Dict[str, Any]) -> tuple[bool, List[str]]:
		"""
		완전성 검증
		필수 섹션 및 정보가 모두 포함되어 있는지 확인

		Args:
			generated_report: 생성된 리포트

		Returns:
			(완전성 통과 여부, 발견된 이슈 리스트)
		"""
		issues = []

		# 필수 섹션 목록
		required_sections = [
			'executive_summary',
			'methodology',
			'risk_scores',
			'aal_results',
			'response_strategy',
			'recommendations'
		]

		# 섹션 존재 여부 확인
		for section in required_sections:
			if section not in generated_report or not generated_report[section]:
				issues.append(f"완전성 오류: 필수 섹션 '{section}' 누락 또는 비어있음")

		# 각 섹션별 최소 내용 확인
		if 'risk_scores' in generated_report:
			risk_scores = generated_report['risk_scores']
			if len(risk_scores) == 0:
				issues.append("완전성 오류: 리스크 점수 섹션에 데이터 없음")

		if 'recommendations' in generated_report:
			recommendations = generated_report['recommendations']
			if not isinstance(recommendations, list) or len(recommendations) < 3:
				issues.append("완전성 오류: 권장사항이 3개 미만")

		completeness_passed = len(issues) == 0
		return completeness_passed, issues

	def _generate_improvement_suggestions(self, issues: List[str]) -> List[str]:
		"""
		개선 제안 생성
		발견된 이슈를 바탕으로 구체적인 개선 제안 생성

		Args:
			issues: 발견된 이슈 리스트

		Returns:
			개선 제안 리스트
		"""
		suggestions = []

		for issue in issues:
			if '누락' in issue:
				suggestions.append(f"개선 제안: {issue.split(':')[1].strip()}을(를) 추가하세요")
			elif '불일치' in issue:
				suggestions.append(f"개선 제안: {issue.split(':')[1].strip()}을(를) 원본 데이터와 일치시키세요")
			elif '비어있음' in issue:
				suggestions.append(f"개선 제안: {issue.split(':')[1].strip()}에 내용을 채우세요")
			else:
				suggestions.append(f"개선 제안: {issue} 문제를 해결하세요")

		return suggestions
