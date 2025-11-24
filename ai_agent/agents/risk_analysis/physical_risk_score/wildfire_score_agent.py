'''
파일명: wildfire_score_agent.py
최종 수정일: 2025-11-13
버전: v02
파일 개요: 산불 리스크 물리적 종합 점수 산출 Agent
변경 이력:
	- 2025-11-11: v01 - AAL×자산가치 방식으로 변경 (H×E×V 제거)
	- 2025-11-13: v02 - H×E×V 방식으로 복원
'''
from typing import Dict, Any
from .base_physical_risk_score_agent import BasePhysicalRiskScoreAgent


class WildfireScoreAgent(BasePhysicalRiskScoreAgent):
	"""
	산불 리스크 물리적 종합 점수 산출 Agent
	(H + E + V) / 3 평균 기반 리스크 점수 계산
	"""

	def __init__(self):
		"""
		WildfireScoreAgent 초기화
		"""
		super().__init__(risk_type='wildfire')

	def calculate_hazard(self, collected_data: Dict[str, Any]) -> float:
		"""
		산불 Hazard 점수 계산
		기후 데이터 기반 산불위험일수 위험도 평가

		Args:
			collected_data: 수집된 기후 데이터

		Returns:
			Hazard 점수 (0.0 ~ 1.0)
		"""
		climate_data = collected_data.get('climate_data', {})

		# 산불위험일수 관련 데이터
		risk_days = climate_data.get('fire_risk_days', 5)

		# Hazard 점수 계산 (임시 구현)
		hazard_score = min(risk_days / 30, 1.0)

		return round(hazard_score, 4)

	def calculate_exposure(self, collected_data: Dict[str, Any]) -> float:
		"""
		산불 Exposure 점수 계산 (산림 거리 + 경사도)

		Args:
			collected_data: 수집된 환경 데이터

		Returns:
			Exposure 점수 (0.0 ~ 1.0)
		"""
		exposure_data = collected_data.get('exposure', {})
		wildfire_exp = exposure_data.get('wildfire_exposure', {})

		# 산림까지 거리
		distance_to_forest_m = wildfire_exp.get('distance_to_forest_m', 5000)

		# 거리 기반 점수 (500m 이내: 1.0, 5km 이상: 0.1)
		if distance_to_forest_m < 500:
			distance_score = 1.0
		elif distance_to_forest_m < 2000:
			distance_score = 0.8
		elif distance_to_forest_m < 5000:
			distance_score = 0.4
		else:
			distance_score = 0.1

		# 식생 유형
		vegetation_type = wildfire_exp.get('vegetation_type', 'urban')
		vegetation_scores = {
			'forest': 1.0,
			'grassland': 0.6,
			'urban': 0.2
		}
		vegetation_score = vegetation_scores.get(vegetation_type, 0.2)

		# 가중 평균
		exposure_score = (distance_score * 0.7) + (vegetation_score * 0.3)

		return round(min(exposure_score, 1.0), 4)

	def calculate_vulnerability(
		self,
		vulnerability_analysis: Dict[str, Any],
		collected_data: Dict[str, Any]
	) -> float:
		"""
		산불 Vulnerability 점수 계산

		Args:
			vulnerability_analysis: VulnerabilityAnalysisAgent의 계산 결과
			collected_data: 수집된 데이터 (미사용)

		Returns:
			Vulnerability 점수 (0.0 ~ 1.0)
		"""
		wildfire_vuln = vulnerability_analysis.get('wildfire', {})
		vuln_score = wildfire_vuln.get('score', 30)
		normalized_score = vuln_score / 100.0
		return round(normalized_score, 4)
