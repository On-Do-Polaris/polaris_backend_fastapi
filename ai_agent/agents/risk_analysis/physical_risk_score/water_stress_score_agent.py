'''
파일명: water_stress_score_agent.py
최종 수정일: 2025-11-13
버전: v02
파일 개요: 물 부족 리스크 물리적 종합 점수 산출 Agent
변경 이력:
	- 2025-11-11: v01 - AAL×자산가치 방식으로 변경 (H×E×V 제거)
	- 2025-11-13: v02 - H×E×V 방식으로 복원
'''
from typing import Dict, Any
from .base_physical_risk_score_agent import BasePhysicalRiskScoreAgent


class WaterStressScoreAgent(BasePhysicalRiskScoreAgent):
	"""
	물 부족 리스크 물리적 종합 점수 산출 Agent
	(H + E + V) / 3 평균 기반 리스크 점수 계산
	"""

	def __init__(self):
		"""
		WaterStressScoreAgent 초기화
		"""
		super().__init__(risk_type='water_stress')

	def calculate_hazard(self, collected_data: Dict[str, Any]) -> float:
		"""
		물 부족 Hazard 점수 계산
		기후 데이터 기반 물부족수준 위험도 평가

		Args:
			collected_data: 수집된 기후 데이터

		Returns:
			Hazard 점수 (0.0 ~ 1.0)
		"""
		climate_data = collected_data.get('climate_data', {})

		# 물부족수준 관련 데이터
		risk_days = climate_data.get('water_stress_level', 5)

		# Hazard 점수 계산 (임시 구현)
		hazard_score = min(risk_days / 30, 1.0)

		return round(hazard_score, 4)

	def calculate_exposure(self, collected_data: Dict[str, Any]) -> float:
		"""
		수자원 스트레스 Exposure 점수 계산 (용수 의존도, 가뭄과 유사)

		Args:
			collected_data: 수집된 환경 데이터

		Returns:
			Exposure 점수 (0.0 ~ 1.0)
		"""
		exposure_data = collected_data.get('exposure', {})
		building = exposure_data.get('building', {})

		# 건물 용도에 따른 용수 의존도
		main_purpose = building.get('main_purpose', '단독주택')

		water_dependency_scores = {
			'공장': 0.95,
			'숙박시설': 0.85,
			'업무시설': 0.65,
			'상업시설': 0.55,
			'단독주택': 0.45,
			'아파트': 0.35,
		}

		exposure_score = 0.5  # 기본값
		for purpose_key, score in water_dependency_scores.items():
			if purpose_key in main_purpose:
				exposure_score = score
				break

		return round(exposure_score, 4)

	def calculate_vulnerability(
		self,
		vulnerability_analysis: Dict[str, Any],
		collected_data: Dict[str, Any]
	) -> float:
		"""
		수자원 스트레스 Vulnerability 점수 계산

		Args:
			vulnerability_analysis: VulnerabilityAnalysisAgent의 계산 결과
			collected_data: 수집된 데이터 (미사용)

		Returns:
			Vulnerability 점수 (0.0 ~ 1.0)
		"""
		water_vuln = vulnerability_analysis.get('water_stress', {})
		vuln_score = water_vuln.get('score', 35)
		normalized_score = vuln_score / 100.0
		return round(normalized_score, 4)
