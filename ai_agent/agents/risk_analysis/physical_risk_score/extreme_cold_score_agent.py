'''
파일명: extreme_cold_score_agent.py
최종 수정일: 2025-11-13
버전: v02
파일 개요: 극심한 한파 리스크 물리적 종합 점수 산출 Agent
변경 이력:
	- 2025-11-11: v01 - AAL×자산가치 방식으로 변경 (H×E×V 제거)
	- 2025-11-13: v02 - H×E×V 방식으로 복원
'''
from typing import Dict, Any
from .base_physical_risk_score_agent import BasePhysicalRiskScoreAgent


class ExtremeColdScoreAgent(BasePhysicalRiskScoreAgent):
	"""
	극심한 한파 리스크 물리적 종합 점수 산출 Agent
	(H + E + V) / 3 평균 기반 리스크 점수 계산
	"""

	def __init__(self):
		"""
		ExtremeColdScoreAgent 초기화
		"""
		super().__init__(risk_type='extreme_cold')

	def calculate_hazard(self, collected_data: Dict[str, Any]) -> float:
		"""
		극심한 한파 Hazard 점수 계산
		기후 데이터 기반 한파일수 위험도 평가

		Args:
			collected_data: 수집된 기후 데이터

		Returns:
			Hazard 점수 (0.0 ~ 1.0)
		"""
		climate_data = collected_data.get('climate_data', {})

		# 한파일수 관련 데이터
		risk_days = climate_data.get('coldwave_days', 5)

		# Hazard 점수 계산 (임시 구현)
		hazard_score = min(risk_days / 30, 1.0)

		return round(hazard_score, 4)

	def calculate_exposure(self, collected_data: Dict[str, Any]) -> float:
		"""
		극심한 한파 Exposure 점수 계산 (도시 열섬 효과 유사)

		Args:
			collected_data: 수집된 환경 데이터

		Returns:
			Exposure 점수 (0.0 ~ 1.0)
		"""
		exposure_data = collected_data.get('exposure', {})
		heat_exp = exposure_data.get('heat_exposure', {})
		location = exposure_data.get('location', {})

		# 도시 열섬 강도 (한파는 반대 효과 - 열섬이 높으면 노출 낮음)
		uhi_scores = {
			'high': 0.3,  # 도심은 한파 영향 적음
			'medium': 0.5,
			'low': 0.8,  # 외곽은 한파 영향 큼
		}
		uhi_intensity = heat_exp.get('urban_heat_island', 'medium')
		base_score = uhi_scores.get(uhi_intensity, 0.5)

		# 고도 보정 (고지대일수록 한파 심함)
		elevation_m = location.get('elevation_m', 50)
		if elevation_m > 200:
			base_score *= 1.2
		elif elevation_m < 50:
			base_score *= 0.9

		exposure_score = min(base_score, 1.0)
		return round(exposure_score, 4)

	def calculate_vulnerability(
		self,
		vulnerability_analysis: Dict[str, Any],
		collected_data: Dict[str, Any]
	) -> float:
		"""
		극심한 한파 Vulnerability 점수 계산

		Args:
			vulnerability_analysis: VulnerabilityAnalysisAgent의 계산 결과
			collected_data: 수집된 데이터 (미사용)

		Returns:
			Vulnerability 점수 (0.0 ~ 1.0)
		"""
		cold_vuln = vulnerability_analysis.get('extreme_cold', {})
		vuln_score = cold_vuln.get('score', 50)
		normalized_score = vuln_score / 100.0
		return round(normalized_score, 4)
