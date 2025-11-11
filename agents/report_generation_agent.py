'''
파일명: report_generation_agent.py
최종 수정일: 2025-11-11
버전: v01
파일 개요: 최종 리포트 생성 에이전트 (템플릿 + 분석 결과 통합)
변경 이력:
	- 2025-11-11: v01 - Super Agent 구조에 맞게 재작성
'''
from typing import Dict, Any
from datetime import datetime
import logging


logger = logging.getLogger(__name__)


class ReportGenerationAgent:
	"""
	최종 리포트 생성 에이전트
	템플릿과 분석 결과를 통합하여 최종 리포트 작성
	"""

	def __init__(self):
		"""
		ReportGenerationAgent 초기화
		"""
		self.logger = logger
		self.logger.info("ReportGenerationAgent 초기화")

	def generate_report(
		self,
		target_location: Dict[str, Any],
		building_info: Dict[str, Any],
		vulnerability_analysis: Dict[str, Any],
		aal_analysis: Dict[str, Any],
		physical_risk_scores: Dict[str, Any],
		report_template: Dict[str, Any],
		response_strategy: Dict[str, Any]
	) -> Dict[str, Any]:
		"""
		최종 리포트 생성
		모든 분석 결과와 전략을 통합하여 완성된 리포트 작성

		Args:
			target_location: 분석 대상 위치 정보
			building_info: 건물 정보
			vulnerability_analysis: 취약성 분석 결과
			aal_analysis: AAL 분석 결과
			physical_risk_scores: 물리적 리스크 점수
			report_template: 리포트 템플릿
			response_strategy: 대응 전략

		Returns:
			최종 리포트 딕셔너리
				- report_content: 리포트 내용 (HTML/Markdown)
				- executive_summary: 요약
				- sections: 섹션별 내용
				- metadata: 메타데이터
				- status: 생성 상태
		"""
		self.logger.info("최종 리포트 생성 시작")

		try:
			# 1. 요약 생성
			executive_summary = self._generate_executive_summary(
				target_location,
				vulnerability_analysis,
				aal_analysis,
				physical_risk_scores,
				response_strategy
			)

			# 2. 섹션별 내용 생성
			sections = self._generate_sections(
				target_location,
				building_info,
				vulnerability_analysis,
				aal_analysis,
				physical_risk_scores,
				response_strategy,
				report_template
			)

			# 3. 전체 리포트 조합
			report_content = self._assemble_report(
				executive_summary,
				sections,
				report_template
			)

			# 4. 메타데이터 생성
			metadata = self._generate_metadata(
				target_location,
				building_info
			)

			result = {
				'report_content': report_content,
				'executive_summary': executive_summary,
				'sections': sections,
				'metadata': metadata,
				'generation_timestamp': datetime.now().isoformat(),
				'status': 'completed'
			}

			self.logger.info(f"최종 리포트 생성 완료: {len(sections)}개 섹션")
			return result

		except Exception as e:
			self.logger.error(f"최종 리포트 생성 중 오류: {str(e)}", exc_info=True)
			return {
				'status': 'failed',
				'error': str(e)
			}

	def _generate_executive_summary(
		self,
		target_location: Dict[str, Any],
		vulnerability_analysis: Dict[str, Any],
		aal_analysis: Dict[str, Any],
		physical_risk_scores: Dict[str, Any],
		response_strategy: Dict[str, Any]
	) -> str:
		"""
		요약 생성

		Args:
			target_location: 위치 정보
			vulnerability_analysis: 취약성 분석
			aal_analysis: AAL 분석
			physical_risk_scores: 물리적 리스크 점수
			response_strategy: 대응 전략

		Returns:
			요약 텍스트
		"""
		# 상위 3개 리스크 추출
		top_risks = sorted(
			physical_risk_scores.items(),
			key=lambda x: x[1].get('physical_risk_score_100', 0),
			reverse=True
		)[:3]

		# 총 재무 손실 계산
		total_financial_loss = sum(
			aal.get('financial_loss', 0) for aal in aal_analysis.values()
		)

		summary = f"""
## 요약

본 보고서는 {target_location.get('name', '대상 위치')}에 대한 물리적 기후 리스크 분석 결과를 제시합니다.

### 주요 발견사항
- 취약성 종합 점수: {vulnerability_analysis.get('overall_vulnerability_score', 0):.2f}
- 연평균 총 재무 손실 예상: {total_financial_loss:,.0f}원
- 주요 리스크 (상위 3개):
  1. {top_risks[0][0]}: {top_risks[0][1].get('physical_risk_score_100', 0):.1f}/100
  2. {top_risks[1][0]}: {top_risks[1][1].get('physical_risk_score_100', 0):.1f}/100
  3. {top_risks[2][0]}: {top_risks[2][1].get('physical_risk_score_100', 0):.1f}/100

### 권고사항
{response_strategy.get('overall_strategy', '종합 대응 전략을 수립하시기 바랍니다.')}
"""

		return summary.strip()

	def _generate_sections(
		self,
		target_location: Dict[str, Any],
		building_info: Dict[str, Any],
		vulnerability_analysis: Dict[str, Any],
		aal_analysis: Dict[str, Any],
		physical_risk_scores: Dict[str, Any],
		response_strategy: Dict[str, Any],
		report_template: Dict[str, Any]
	) -> Dict[str, str]:
		"""
		섹션별 내용 생성

		Args:
			...: 각종 분석 결과

		Returns:
			섹션별 내용 딕셔너리
		"""
		sections = {}

		# Section 1: 대상 정보
		sections['target_info'] = self._section_target_info(target_location, building_info)

		# Section 2: 취약성 분석
		sections['vulnerability_analysis'] = self._section_vulnerability(vulnerability_analysis)

		# Section 3: AAL 분석
		sections['aal_analysis'] = self._section_aal(aal_analysis)

		# Section 4: 물리적 리스크 점수
		sections['physical_risk_scores'] = self._section_risk_scores(physical_risk_scores)

		# Section 5: 대응 전략
		sections['response_strategy'] = self._section_strategy(response_strategy)

		# Section 6: 권고사항
		sections['recommendations'] = self._section_recommendations(response_strategy)

		# Section 7: 결론
		sections['conclusion'] = self._section_conclusion(physical_risk_scores, response_strategy)

		return sections

	def _section_target_info(
		self,
		target_location: Dict[str, Any],
		building_info: Dict[str, Any]
	) -> str:
		"""대상 정보 섹션"""
		return f"""
## 1. 분석 대상 정보

### 위치
- 이름: {target_location.get('name', 'N/A')}
- 위도: {target_location.get('latitude', 'N/A')}
- 경도: {target_location.get('longitude', 'N/A')}

### 건물 정보
- 건물 연식: {building_info.get('building_age', 'N/A')}년
- 층수: {building_info.get('floors', 'N/A')}층
- 내진 설계: {building_info.get('seismic_design', 'N/A')}
"""

	def _section_vulnerability(self, vulnerability_analysis: Dict[str, Any]) -> str:
		"""취약성 분석 섹션"""
		return f"""
## 2. 취약성 분석

### 종합 취약성 점수
- **{vulnerability_analysis.get('overall_vulnerability_score', 0):.2f}** (0.0 ~ 1.0 스케일)

### 세부 항목
- 건물 연식 점수: {vulnerability_analysis.get('building_age_score', 0):.2f}
- 내진 취약성 점수: {vulnerability_analysis.get('seismic_vulnerability_score', 0):.2f}
- 소방차 진입 점수: {vulnerability_analysis.get('fire_access_score', 0):.2f}
"""

	def _section_aal(self, aal_analysis: Dict[str, Any]) -> str:
		"""AAL 분석 섹션"""
		content = "## 3. 연평균 재무 손실률 (AAL) 분석\n\n"

		for risk_type, aal_data in aal_analysis.items():
			if aal_data.get('status') == 'completed':
				content += f"""
### {risk_type}
- AAL: {aal_data.get('aal_percentage', 0):.2f}%
- 연평균 재무 손실: {aal_data.get('financial_loss', 0):,.0f}원
- 위험 수준: {aal_data.get('calculation_details', {}).get('risk_level', 'N/A')}
"""

		return content

	def _section_risk_scores(self, physical_risk_scores: Dict[str, Any]) -> str:
		"""물리적 리스크 점수 섹션"""
		content = "## 4. 물리적 리스크 종합 점수 (100점 스케일)\n\n"

		# 점수순 정렬
		sorted_risks = sorted(
			physical_risk_scores.items(),
			key=lambda x: x[1].get('physical_risk_score_100', 0),
			reverse=True
		)

		for risk_type, score_data in sorted_risks:
			content += f"""
### {risk_type}
- 점수: **{score_data.get('physical_risk_score_100', 0):.1f}/100**
- 위험 수준: {score_data.get('risk_level', 'N/A')}
- AAL: {score_data.get('aal_percentage', 0):.2f}%
- 재무 손실: {score_data.get('financial_loss', 0):,.0f}원
"""

		return content

	def _section_strategy(self, response_strategy: Dict[str, Any]) -> str:
		"""대응 전략 섹션"""
		content = "## 5. 대응 전략\n\n"
		content += f"### 종합 전략\n{response_strategy.get('overall_strategy', 'N/A')}\n\n"

		risk_strategies = response_strategy.get('risk_specific_strategies', {})
		if risk_strategies:
			content += "### 리스크별 전략\n"
			for risk_type, strategy in risk_strategies.items():
				content += f"\n#### {risk_type}\n{strategy}\n"

		return content

	def _section_recommendations(self, response_strategy: Dict[str, Any]) -> str:
		"""권고사항 섹션"""
		content = "## 6. 권고사항\n\n"

		recommendations = response_strategy.get('recommendations', [])
		for i, rec in enumerate(recommendations, 1):
			content += f"{i}. {rec}\n"

		priority_actions = response_strategy.get('priority_actions', [])
		if priority_actions:
			content += "\n### 우선순위 조치사항\n"
			for action in priority_actions:
				content += f"\n**우선순위 {action['priority']}**\n"
				content += f"- 조치: {action['action']}\n"
				content += f"- 기한: {action['timeline']}\n"

		return content

	def _section_conclusion(
		self,
		physical_risk_scores: Dict[str, Any],
		response_strategy: Dict[str, Any]
	) -> str:
		"""결론 섹션"""
		top_risk = max(
			physical_risk_scores.items(),
			key=lambda x: x[1].get('physical_risk_score_100', 0)
		)

		return f"""
## 7. 결론

본 분석 결과, 가장 우선적으로 대응이 필요한 리스크는 **{top_risk[0]}** (점수: {top_risk[1].get('physical_risk_score_100', 0):.1f}/100)로 확인되었습니다.

{response_strategy.get('overall_strategy', '')}

지속적인 모니터링과 정기적인 리스크 재평가를 통해 효과적인 리스크 관리가 이루어질 수 있도록 해야 합니다.
"""

	def _assemble_report(
		self,
		executive_summary: str,
		sections: Dict[str, str],
		report_template: Dict[str, Any]
	) -> str:
		"""
		전체 리포트 조합

		Args:
			executive_summary: 요약
			sections: 섹션별 내용
			report_template: 템플릿

		Returns:
			전체 리포트 텍스트
		"""
		report = f"""
# 물리적 기후 리스크 분석 보고서

생성일: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

---

{executive_summary}

---

{sections.get('target_info', '')}

{sections.get('vulnerability_analysis', '')}

{sections.get('aal_analysis', '')}

{sections.get('physical_risk_scores', '')}

{sections.get('response_strategy', '')}

{sections.get('recommendations', '')}

{sections.get('conclusion', '')}

---

*본 보고서는 SKAX Physical Risk Analysis System을 통해 자동 생성되었습니다.*
"""

		return report.strip()

	def _generate_metadata(
		self,
		target_location: Dict[str, Any],
		building_info: Dict[str, Any]
	) -> Dict[str, Any]:
		"""
		메타데이터 생성

		Args:
			target_location: 위치 정보
			building_info: 건물 정보

		Returns:
			메타데이터 딕셔너리
		"""
		return {
			'report_title': f'{target_location.get("name", "대상 위치")} 물리적 리스크 분석 보고서',
			'generation_date': datetime.now().isoformat(),
			'location': target_location.get('name', 'N/A'),
			'building_age': building_info.get('building_age', 'N/A'),
			'report_version': 'v01',
			'system': 'SKAX Physical Risk Analysis'
		}
