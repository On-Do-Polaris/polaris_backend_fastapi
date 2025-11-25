'''
파일명: river_flood_score_agent.py
최종 수정일: 2025-11-13
버전: v02
파일 개요: 내륙 홍수 리스크 물리적 종합 점수 산출 Agent
변경 이력:
	- 2025-11-11: v01 - AAL×자산가치 방식으로 변경 (H×E×V 제거)
	- 2025-11-13: v02 - H×E×V 방식으로 복원
'''
from typing import Dict, Any
from .base_physical_risk_score_agent import BasePhysicalRiskScoreAgent


class RiverFloodScoreAgent(BasePhysicalRiskScoreAgent):
	"""
	내륙 홍수 리스크 물리적 종합 점수 산출 Agent
	(H + E + V) / 3 평균 기반 리스크 점수 계산
	"""

	def __init__(self):
		"""
		RiverFloodScoreAgent 초기화
		"""
		super().__init__(risk_type='river_flood')

	def calculate_hazard(self, collected_data: Dict[str, Any]) -> float:
		"""
		내륙 홍수 Hazard 점수 계산
		기후 데이터 기반 내륙홍수위험 위험도 평가

		Args:
			collected_data: 수집된 기후 데이터

		Returns:
			Hazard 점수 (0.0 ~ 1.0)
		"""
		climate_data = collected_data.get('climate_data', {})

		# 내륙홍수위험 관련 데이터
		risk_days = climate_data.get('river_flood_risk', 5)

		# Hazard 점수 계산 (임시 구현)
		hazard_score = min(risk_days / 30, 1.0)

		return round(hazard_score, 4)

	def calculate_exposure(self, collected_data: Dict[str, Any]) -> float:
		"""
		내륙 홍수 Exposure 점수 계산 (하천 거리 + 저지대 기반)

		근거: inland_flood_risk.md
		E = 0.4 × 하천거리 + 0.35 × 침수이력 + 0.25 × 저지대여부

		Args:
			collected_data: 수집된 환경 데이터

		Returns:
			Exposure 점수 (0.0 ~ 1.0)
		"""
		exposure_data = collected_data.get('exposure', {})
		flood_exp = exposure_data.get('flood_exposure', {})
		location = exposure_data.get('location', {})

		# 하천까지 거리
		distance_to_river_m = flood_exp.get('distance_to_river_m', 1000)

		# 거리 기반 점수 (100m 이내: 1.0, 2km 이상: 0.0)
		if distance_to_river_m <= 100:
			distance_score = 1.0
		elif distance_to_river_m >= 2000:
			distance_score = 0.0
		else:
			distance_score = 1.0 - ((distance_to_river_m - 100) / 1900)

		# 홍수 위험 구역 여부
		in_flood_zone = flood_exp.get('in_flood_zone', False)
		flood_zone_score = 1.0 if in_flood_zone else 0.3

		# 고도 (저지대일수록 위험)
		elevation_m = location.get('elevation_m', 50)
		if elevation_m < 10:
			elevation_score = 1.0
		elif elevation_m < 50:
			elevation_score = 0.6
		else:
			elevation_score = 0.2

		# 가중 평균
		exposure_score = (distance_score * 0.5) + (flood_zone_score * 0.3) + (elevation_score * 0.2)

		return round(min(exposure_score, 1.0), 4)

	def calculate_vulnerability(
		self,
		vulnerability_analysis: Dict[str, Any],
		collected_data: Dict[str, Any]
	) -> float:
		"""
		내륙 홍수 Vulnerability 점수 계산
		VulnerabilityAnalysisAgent에서 계산된 inland_flood 취약성 사용

		Args:
			vulnerability_analysis: VulnerabilityAnalysisAgent의 계산 결과
			collected_data: 수집된 데이터 (미사용, 호환성 유지)

		Returns:
			Vulnerability 점수 (0.0 ~ 1.0)
		"""
		# VulnerabilityAnalysisAgent의 inland_flood 결과 사용
		flood_vuln = vulnerability_analysis.get('inland_flood', {})
		vuln_score = flood_vuln.get('score', 40)  # 0-100 스케일

		# 0-1 스케일로 정규화
		normalized_score = vuln_score / 100.0

		return round(normalized_score, 4)
