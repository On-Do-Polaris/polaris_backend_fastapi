'''
파일명: sea_level_rise_score_agent.py
최종 수정일: 2025-11-13
버전: v02
파일 개요: 해안 홍수 리스크 물리적 종합 점수 산출 Agent
변경 이력:
	- 2025-11-11: v01 - AAL×자산가치 방식으로 변경 (H×E×V 제거)
	- 2025-11-13: v02 - H×E×V 방식으로 복원
'''
from typing import Dict, Any
from .base_physical_risk_score_agent import BasePhysicalRiskScoreAgent


class SeaLevelRiseScoreAgent(BasePhysicalRiskScoreAgent):
	"""
	해안 홍수 리스크 물리적 종합 점수 산출 Agent
	(H + E + V) / 3 평균 기반 리스크 점수 계산
	"""

	def __init__(self):
		"""
		SeaLevelRiseScoreAgent 초기화
		"""
		super().__init__(risk_type='sea_level_rise')

	def calculate_hazard(self, collected_data: Dict[str, Any]) -> float:
		"""
		해안 홍수 Hazard 점수 계산
		기후 데이터 기반 해안홍수위험 위험도 평가

		Args:
			collected_data: 수집된 기후 데이터

		Returns:
			Hazard 점수 (0.0 ~ 1.0)
		"""
		climate_data = collected_data.get('climate_data', {})

		# 해안홍수위험 관련 데이터
		risk_days = climate_data.get('sea_level_rise_risk', 5)

		# Hazard 점수 계산 (임시 구현)
		hazard_score = min(risk_days / 30, 1.0)

		return round(hazard_score, 4)

	def calculate_exposure(self, collected_data: Dict[str, Any]) -> float:
		"""
		해안 홍수 Exposure 점수 계산 (해안 거리 기반)

		Args:
			collected_data: 수집된 환경 데이터

		Returns:
			Exposure 점수 (0.0 ~ 1.0)
		"""
		exposure_data = collected_data.get('exposure', {})
		typhoon_exp = exposure_data.get('typhoon_exposure', {})
		location = exposure_data.get('location', {})

		# 해안 노출 여부
		coastal_exposure = typhoon_exp.get('coastal_exposure', False)
		distance_to_coast_m = typhoon_exp.get('distance_to_coast_m', 50000)

		if not coastal_exposure or distance_to_coast_m > 50000:
			return 0.05  # 해안에서 멀리 떨어진 경우 거의 노출 없음

		# 해안 거리 기반 (5km 이내 고위험)
		if distance_to_coast_m < 5000:
			distance_score = 1.0
		elif distance_to_coast_m < 20000:
			distance_score = 1.0 - ((distance_to_coast_m - 5000) / 15000) * 0.7
		else:
			distance_score = 0.3

		# 고도 보정 (저지대일수록 위험)
		elevation_m = location.get('elevation_m', 50)
		if elevation_m < 5:
			elevation_factor = 1.3
		elif elevation_m < 20:
			elevation_factor = 1.0
		else:
			elevation_factor = 0.7

		exposure_score = distance_score * elevation_factor

		return round(min(exposure_score, 1.0), 4)

	def calculate_vulnerability(
		self,
		vulnerability_analysis: Dict[str, Any],
		collected_data: Dict[str, Any]
	) -> float:
		"""
		해안 홍수 Vulnerability 점수 계산

		Args:
			vulnerability_analysis: VulnerabilityAnalysisAgent의 계산 결과
			collected_data: 수집된 데이터 (미사용)

		Returns:
			Vulnerability 점수 (0.0 ~ 1.0)
		"""
		coastal_vuln = vulnerability_analysis.get('coastal_flood', {})
		vuln_score = coastal_vuln.get('score', 50)
		normalized_score = vuln_score / 100.0
		return round(normalized_score, 4)
