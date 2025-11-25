'''
파일명: extreme_heat_score_agent.py
최종 수정일: 2025-11-21
버전: v03
파일 개요: 극심한 고온 리스크 물리적 종합 점수 산출 Agent
변경 이력:
	- 2025-11-11: v01 - AAL×자산가치 방식으로 변경 (H×E×V 제거)
	- 2025-11-13: v02 - H×E×V 방식으로 복원
	- 2025-11-21: v03 - 리스크 명칭 통일 (high_temperature → extreme_heat)
'''
from typing import Dict, Any
from .base_physical_risk_score_agent import BasePhysicalRiskScoreAgent


class ExtremeHeatScoreAgent(BasePhysicalRiskScoreAgent):
	"""
	극심한 고온 리스크 물리적 종합 점수 산출 Agent
	(H + E + V) / 3 평균 기반 리스크 점수 계산
	"""

	def __init__(self):
		"""
		ExtremeHeatScoreAgent 초기화
		"""
		super().__init__(risk_type='extreme_heat')

	def calculate_hazard(self, collected_data: Dict[str, Any]) -> float:
		"""
		극심한 고온 Hazard 점수 계산
		기후 데이터 기반 폭염 위험도 평가

		Args:
			collected_data: 수집된 기후 데이터

		Returns:
			Hazard 점수 (0.0 ~ 1.0)
		"""
		climate_data = collected_data.get('climate_data', {})

		# 폭염 일수 (연간)
		heatwave_days = climate_data.get('heatwave_days', 5)

		# 최고 기온
		max_temperature = climate_data.get('max_temperature', 30)

		# Hazard 점수 계산
		# 폭염 일수 기반 (0-30일 → 0.0-0.5)
		days_score = min(heatwave_days / 60, 0.5)

		# 최고 기온 기반 (30-40도 → 0.0-0.5)
		temp_score = min(max((max_temperature - 30) / 20, 0), 0.5)

		hazard_score = days_score + temp_score

		return round(min(hazard_score, 1.0), 4)

	def calculate_exposure(self, collected_data: Dict[str, Any]) -> float:
		"""
		극심한 고온 Exposure 점수 계산 (도시 열섬 효과 기반)

		근거: extreme_heat.md
		E = 0.5 × 불투수면비율 + 0.3 × 녹지부족 + 0.15 × 저지대 + 0.05 × 수역부족

		Args:
			collected_data: 수집된 환경 데이터

		Returns:
			Exposure 점수 (0.0 ~ 1.0)
		"""
		exposure_data = collected_data.get('exposure', {})
		heat_exp = exposure_data.get('heat_exposure', {})
		location = exposure_data.get('location', {})

		# 도시 열섬 강도에 따른 기본 점수
		uhi_scores = {
			'high': 0.8,
			'medium': 0.5,
			'low': 0.2,
		}
		uhi_intensity = heat_exp.get('urban_heat_island', 'medium')
		base_score = uhi_scores.get(uhi_intensity, 0.5)

		# 녹지 접근성 보정
		if heat_exp.get('green_space_nearby', False):
			base_score *= 0.8  # 20% 감소

		# 고도 보정 (저지대일수록 열 축적)
		elevation_m = location.get('elevation_m', 50)
		if elevation_m < 50:
			base_score *= 1.2  # 20% 증가
		elif elevation_m > 200:
			base_score *= 0.9  # 10% 감소

		exposure_score = min(base_score, 1.0)
		return round(exposure_score, 4)

	def calculate_vulnerability(
		self,
		vulnerability_analysis: Dict[str, Any],
		collected_data: Dict[str, Any]
	) -> float:
		"""
		극심한 고온 Vulnerability 점수 계산
		VulnerabilityAnalysisAgent에서 계산된 extreme_heat 취약성 사용

		Args:
			vulnerability_analysis: VulnerabilityAnalysisAgent의 계산 결과
			collected_data: 수집된 데이터 (미사용, 호환성 유지)

		Returns:
			Vulnerability 점수 (0.0 ~ 1.0, 0-100 스케일을 0-1로 정규화)
		"""
		# VulnerabilityAnalysisAgent의 extreme_heat 결과 사용
		heat_vuln = vulnerability_analysis.get('extreme_heat', {})
		vuln_score = heat_vuln.get('score', 50)  # 0-100 스케일

		# 0-1 스케일로 정규화
		normalized_score = vuln_score / 100.0

		return round(normalized_score, 4)
