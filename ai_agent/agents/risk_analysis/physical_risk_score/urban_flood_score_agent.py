'''
파일명: urban_flood_score_agent.py
최종 수정일: 2025-11-13
버전: v02
파일 개요: 도심 홍수 리스크 물리적 종합 점수 산출 Agent
변경 이력:
	- 2025-11-11: v01 - AAL×자산가치 방식으로 변경 (H×E×V 제거)
	- 2025-11-13: v02 - H×E×V 방식으로 복원
'''
from typing import Dict, Any
from .base_physical_risk_score_agent import BasePhysicalRiskScoreAgent


class UrbanFloodScoreAgent(BasePhysicalRiskScoreAgent):
	"""
	도심 홍수 리스크 물리적 종합 점수 산출 Agent
	(H + E + V) / 3 평균 기반 리스크 점수 계산
	"""

	def __init__(self):
		"""
		UrbanFloodScoreAgent 초기화
		"""
		super().__init__(risk_type='urban_flood')

	def calculate_hazard(self, collected_data: Dict[str, Any]) -> float:
		"""
		도심 홍수 Hazard 점수 계산
		기후 데이터 기반 도심홍수위험 위험도 평가

		Args:
			collected_data: 수집된 기후 데이터

		Returns:
			Hazard 점수 (0.0 ~ 1.0)
		"""
		climate_data = collected_data.get('climate_data', {})

		# 도심홍수위험 관련 데이터
		risk_days = climate_data.get('urban_flood_risk', 5)

		# Hazard 점수 계산 (임시 구현)
		hazard_score = min(risk_days / 30, 1.0)

		return round(hazard_score, 4)

	def calculate_exposure(self, collected_data: Dict[str, Any]) -> float:
		"""
		도시 홍수 Exposure 점수 계산 (배수 시스템 + 지하층)

		Args:
			collected_data: 수집된 환경 데이터

		Returns:
			Exposure 점수 (0.0 ~ 1.0)
		"""
		exposure_data = collected_data.get('exposure', {})
		building = exposure_data.get('building', {})
		location = exposure_data.get('location', {})

		# 지하층 존재 여부
		floors_below = building.get('floors_below', 0)
		basement_score = 0.8 if floors_below > 0 else 0.3

		# 토지 이용 (도시화 지역일수록 노출 높음)
		land_use = location.get('land_use', 'mixed')
		land_use_scores = {
			'commercial': 0.9,
			'industrial': 0.8,
			'residential': 0.6,
			'mixed': 0.5
		}
		land_use_score = land_use_scores.get(land_use, 0.5)

		# 가중 평균
		exposure_score = (basement_score * 0.6) + (land_use_score * 0.4)

		return round(min(exposure_score, 1.0), 4)

	def calculate_vulnerability(
		self,
		vulnerability_analysis: Dict[str, Any],
		collected_data: Dict[str, Any]
	) -> float:
		"""
		도시 홍수 Vulnerability 점수 계산

		Args:
			vulnerability_analysis: VulnerabilityAnalysisAgent의 계산 결과
			collected_data: 수집된 데이터 (미사용)

		Returns:
			Vulnerability 점수 (0.0 ~ 1.0)
		"""
		urban_vuln = vulnerability_analysis.get('urban_flood', {})
		vuln_score = urban_vuln.get('score', 40)
		normalized_score = vuln_score / 100.0
		return round(normalized_score, 4)
