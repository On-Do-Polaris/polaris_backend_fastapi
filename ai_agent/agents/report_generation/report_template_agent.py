'''
파일명: report_template_agent.py
최종 수정일: 2025-11-11
버전: v02
파일 개요: 리포트 내용 구조 템플릿 생성 에이전트 (RAG 기반 유사 보고서 검색)
변경 이력:
	- 2025-11-11: v01 - Super Agent 구조에 맞게 신규 생성
	- 2025-11-11: v02 - 디자인이 아닌 내용 구조/작성 방향 중심으로 변경
'''
from typing import Dict, Any, List
import logging


logger = logging.getLogger(__name__)


class ReportTemplateAgent:
	"""
	리포트 내용 구조 템플릿 생성 에이전트
	RAG 엔진을 활용하여 유사 보고서를 검색하고 내용 작성 방향 및 구조 제시
	"""

	def __init__(self, rag_engine):
		"""
		ReportTemplateAgent 초기화

		Args:
			rag_engine: RAG 엔진 인스턴스
		"""
		self.rag_engine = rag_engine
		self.logger = logger
		self.logger.info("ReportTemplateAgent 초기화")

	def generate_template(
		self,
		target_location: Dict[str, Any],
		vulnerability_analysis: Dict[str, Any],
		aal_analysis: Dict[str, Any],
		physical_risk_scores: Dict[str, Any]
	) -> Dict[str, Any]:
		"""
		리포트 내용 구조 템플릿 생성
		유사 보고서를 검색하고 내용 작성 방향 및 구조 제시

		Args:
			target_location: 분석 대상 위치 정보
			vulnerability_analysis: 취약성 분석 결과
			aal_analysis: AAL 분석 결과
			physical_risk_scores: 물리적 리스크 점수

		Returns:
			리포트 템플릿 딕셔너리
				- content_structure: 내용 구조 (섹션별 작성 가이드)
				- similar_reports: 유사 보고서 목록
				- writing_guidelines: 작성 지침 (각 리스크에 대해)
				- key_focus_areas: 핵심 초점 영역
				- status: 생성 상태
		"""
		self.logger.info("리포트 내용 구조 템플릿 생성 시작")

		try:
			# 1. 분석 결과 요약 생성 (RAG 검색용)
			analysis_summary = self._create_analysis_summary(
				target_location,
				vulnerability_analysis,
				aal_analysis,
				physical_risk_scores
			)

			# 2. 유사 보고서 검색
			similar_reports = self.rag_engine.retrieve_similar_reports(
				query=analysis_summary,
				top_k=5
			)

			# 3. 내용 구조 정의 (섹션별 작성 가이드)
			content_structure = self._build_content_structure(
				similar_reports,
				vulnerability_analysis,
				aal_analysis,
				physical_risk_scores
			)

			# 4. 작성 지침 생성 (각 리스크에 대해)
			writing_guidelines = self._generate_writing_guidelines(
				similar_reports,
				physical_risk_scores
			)

			# 5. 핵심 초점 영역 도출
			key_focus_areas = self._identify_key_focus_areas(
				physical_risk_scores,
				aal_analysis
			)

			result = {
				'content_structure': content_structure,
				'similar_reports': similar_reports,
				'writing_guidelines': writing_guidelines,
				'key_focus_areas': key_focus_areas,
				'analysis_summary': analysis_summary,
				'status': 'completed'
			}

			self.logger.info(f"리포트 내용 구조 템플릿 생성 완료: {len(similar_reports)}개 유사 보고서 참조")
			return result

		except Exception as e:
			self.logger.error(f"리포트 템플릿 생성 중 오류: {str(e)}", exc_info=True)
			return {
				'status': 'failed',
				'error': str(e)
			}

	def _create_analysis_summary(
		self,
		target_location: Dict[str, Any],
		vulnerability_analysis: Dict[str, Any],
		aal_analysis: Dict[str, Any],
		physical_risk_scores: Dict[str, Any]
	) -> str:
		"""
		분석 결과 요약 생성 (RAG 검색용)

		Args:
			target_location: 위치 정보
			vulnerability_analysis: 취약성 분석
			aal_analysis: AAL 분석
			physical_risk_scores: 물리적 리스크 점수

		Returns:
			분석 요약 텍스트
		"""
		# 상위 3개 리스크 추출
		top_risks = sorted(
			physical_risk_scores.items(),
			key=lambda x: x[1].get('physical_risk_score_100', 0),
			reverse=True
		)[:3]

		summary = f"위치: {target_location.get('name', '알 수 없음')}\n"
		summary += f"주요 리스크: {', '.join([r[0] for r in top_risks])}\n"
		summary += f"취약성 점수: {vulnerability_analysis.get('overall_vulnerability_score', 0):.2f}"

		return summary

	def _build_content_structure(
		self,
		similar_reports: List[Dict[str, Any]],
		vulnerability_analysis: Dict[str, Any],
		aal_analysis: Dict[str, Any],
		physical_risk_scores: Dict[str, Any]
	) -> Dict[str, Any]:
		"""
		내용 구조 생성 (각 섹션별 작성 가이드)

		Args:
			similar_reports: 유사 보고서 목록
			vulnerability_analysis: 취약성 분석
			aal_analysis: AAL 분석
			physical_risk_scores: 물리적 리스크 점수

		Returns:
			내용 구조 딕셔너리
		"""
		return {
			'sections': [
				{
					'name': 'executive_summary',
					'order': 1,
					'required': True,
					'content_guide': '주요 리스크 3가지와 핵심 재무 영향 요약, 즉각적 조치 필요 사항'
				},
				{
					'name': 'vulnerability_analysis',
					'order': 2,
					'required': True,
					'content_guide': '건물 연식, 내진 설계, 접근성 등 구조적 취약점 분석 결과'
				},
				{
					'name': 'aal_analysis',
					'order': 3,
					'required': True,
					'content_guide': '각 리스크별 연평균 손실률, 발생 확률, 손상률 상세 설명'
				},
				{
					'name': 'physical_risk_scores',
					'order': 4,
					'required': True,
					'content_guide': '리스크별 재무 손실 규모, 100점 스케일 점수, 위험 등급 해석'
				},
				{
					'name': 'response_strategy',
					'order': 5,
					'required': True,
					'content_guide': '리스크별 구체적 대응 전략, 우선순위, 예산 계획'
				},
				{
					'name': 'recommendations',
					'order': 6,
					'required': True,
					'content_guide': '단기/중기/장기 권고사항, 실행 가능한 액션 아이템'
				},
				{
					'name': 'conclusion',
					'order': 7,
					'required': True,
					'content_guide': '전체 분석 종합, 핵심 메시지, 다음 단계'
				}
			],
			'similar_cases_insights': self._extract_insights_from_similar_reports(similar_reports)
		}

	def _generate_writing_guidelines(
		self,
		similar_reports: List[Dict[str, Any]],
		physical_risk_scores: Dict[str, Any]
	) -> Dict[str, str]:
		"""
		각 리스크별 작성 지침 생성

		Args:
			similar_reports: 유사 보고서 목록
			physical_risk_scores: 물리적 리스크 점수

		Returns:
			리스크별 작성 지침 딕셔너리
		"""
		guidelines = {}

		# 상위 리스크에 대한 작성 지침
		top_risks = sorted(
			physical_risk_scores.items(),
			key=lambda x: x[1].get('physical_risk_score_100', 0),
			reverse=True
		)[:5]

		for risk_type, risk_data in top_risks:
			score = risk_data.get('physical_risk_score_100', 0)

			if score >= 80:
				guidelines[risk_type] = "매우 높은 위험 - 재무 영향 강조, 즉각 조치 필요성, 구체적 대응 방안 상세 기술"
			elif score >= 60:
				guidelines[risk_type] = "높은 위험 - 발생 가능성과 영향 분석, 단계별 대응 계획 제시"
			elif score >= 40:
				guidelines[risk_type] = "중간 위험 - 모니터링 필요성, 예방적 조치 제안"
			else:
				guidelines[risk_type] = "낮은 위험 - 간략한 현황 설명, 추세 관찰 권고"

		return guidelines

	def _identify_key_focus_areas(
		self,
		physical_risk_scores: Dict[str, Any],
		aal_analysis: Dict[str, Any]
	) -> List[str]:
		"""
		보고서 작성 시 핵심 초점 영역 도출

		Args:
			physical_risk_scores: 물리적 리스크 점수
			aal_analysis: AAL 분석

		Returns:
			핵심 초점 영역 리스트
		"""
		focus_areas = []

		# 고위험 리스크 식별
		high_risks = [
			risk for risk, data in physical_risk_scores.items()
			if data.get('physical_risk_score_100', 0) >= 60
		]

		if high_risks:
			focus_areas.append(f"고위험 리스크 집중 분석: {', '.join(high_risks)}")

		# 높은 AAL 리스크 식별
		high_aal_risks = [
			risk for risk, data in aal_analysis.items()
			if data.get('aal_percentage', 0) >= 10.0
		]

		if high_aal_risks:
			focus_areas.append(f"높은 연평균 손실률 리스크: {', '.join(high_aal_risks)}")

		# 기본 초점 영역
		focus_areas.extend([
			"재무 영향의 구체적 수치화",
			"실행 가능한 대응 전략 제시",
			"우선순위 기반 권고사항"
		])

		return focus_areas

	def _extract_insights_from_similar_reports(
		self,
		similar_reports: List[Dict[str, Any]]
	) -> List[str]:
		"""
		유사 보고서에서 인사이트 추출

		Args:
			similar_reports: 유사 보고서 목록

		Returns:
			인사이트 목록
		"""
		insights = []

		# 실제로는 RAG에서 가져온 유사 보고서 내용 분석
		# 여기서는 템플릿으로 구조만 정의
		if similar_reports:
			insights.append("유사 케이스에서 효과적이었던 대응 전략 참조")
			insights.append("비슷한 리스크 프로파일의 재무 영향 비교")
			insights.append("과거 유사 사례의 권고사항 이행 결과")

		return insights
