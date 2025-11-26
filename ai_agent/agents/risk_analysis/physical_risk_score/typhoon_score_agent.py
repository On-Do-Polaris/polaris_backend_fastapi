'''
파일명: typhoon_score_agent.py
최종 수정일: 2025-11-13
버전: v02
파일 개요: 열대성 태풍 리스크 물리적 종합 점수 산출 Agent
변경 이력:
	- 2025-11-11: v01 - AAL×자산가치 방식으로 변경 (H×E×V 제거)
	- 2025-11-13: v02 - H×E×V 방식으로 복원
'''
from typing import Dict, Any
from .base_physical_risk_score_agent import BasePhysicalRiskScoreAgent


class TyphoonScoreAgent(BasePhysicalRiskScoreAgent):
	"""
	열대성 태풍 리스크 물리적 종합 점수 산출 Agent
	(H + E + V) / 3 평균 기반 리스크 점수 계산
	"""

	def __init__(self):
		"""
		TyphoonScoreAgent 초기화
		"""
		super().__init__(risk_type='typhoon')

	def calculate_hazard(self, collected_data: Dict[str, Any]) -> float:
		"""
		열대성 태풍 Hazard 점수 계산
		기후 데이터 기반 태풍위험 위험도 평가

		Args:
			collected_data: 수집된 기후 데이터

		Returns:
			Hazard 점수 (0.0 ~ 1.0)
		"""
		climate_data = collected_data.get('climate_data', {})

		# 태풍위험 관련 데이터
		risk_days = climate_data.get('typhoon_risk', 5)

		# Hazard 점수 계산 (임시 구현)
		hazard_score = min(risk_days / 30, 1.0)

		return round(hazard_score, 4)

	def calculate_exposure(self, collected_data: Dict[str, Any]) -> float:
		"""
		태풍 Exposure 점수 계산 (해안 거리 기반)

		근거: typhoon_risk.md
		E = 해안 거리 기반 (10km 이내 고위험)

		Args:
			collected_data: 수집된 환경 데이터

		Returns:
			Exposure 점수 (0.0 ~ 1.0)
		"""
		exposure_data = collected_data.get('exposure', {})
		typhoon_exp = exposure_data.get('typhoon_exposure', {})

		# 해안 노출 여부
		coastal_exposure = typhoon_exp.get('coastal_exposure', False)
		distance_to_coast_m = typhoon_exp.get('distance_to_coast_m', 50000)

		if not coastal_exposure or distance_to_coast_m > 50000:
			# 내륙 또는 해안에서 매우 멀리 떨어진 경우
			return 0.1  # 최소 노출도

		# 해안 거리 기반 점수 (0-10km: 1.0 → 0.3)
		if distance_to_coast_m < 10000:
			exposure_score = 1.0
		elif distance_to_coast_m < 30000:
			# 10-30km: 선형 감소
			exposure_score = 1.0 - ((distance_to_coast_m - 10000) / 20000) * 0.5
		else:
			# 30-50km: 낮은 노출
			exposure_score = 0.3

		return round(exposure_score, 4)

	def calculate_vulnerability(
		self,
		vulnerability_analysis: Dict[str, Any],
		collected_data: Dict[str, Any]
	) -> float:
		"""
		태풍 Vulnerability 점수 계산
		VulnerabilityAnalysisAgent에서 계산된 typhoon 취약성 사용

		Args:
			vulnerability_analysis: VulnerabilityAnalysisAgent의 계산 결과
			collected_data: 수집된 데이터 (미사용, 호환성 유지)

		Returns:
			Vulnerability 점수 (0.0 ~ 1.0)
		"""
		# VulnerabilityAnalysisAgent의 typhoon 결과 사용
		typhoon_vuln = vulnerability_analysis.get('typhoon', {})
		vuln_score = typhoon_vuln.get('score', 45)  # 0-100 스케일

		# 0-1 스케일로 정규화
		normalized_score = vuln_score / 100.0

		return round(normalized_score, 4)
