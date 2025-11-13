'''
파일명: cold_wave_aal_agent.py
최종 수정일: 2025-11-11
버전: v00
파일 개요: 극심한 한파 리스크 AAL 분석 Agent
'''
from typing import Dict, Any
from .base_aal_analysis_agent import BaseAALAnalysisAgent


class ColdWaveAALAgent(BaseAALAnalysisAgent):
	"""
	극심한 한파 리스크 AAL 분석 Agent
	"""

	def __init__(self):
		"""
		ColdWaveAALAgent 초기화
		"""
		super().__init__(risk_type='cold_wave')

	def calculate_hazard_probability(self, collected_data: Dict[str, Any], physical_risk_score: float) -> float:
		"""
		극심한 한파 위험 발생 확률 계산
		"""
		climate_data = collected_data.get('climate_data', {})
		cold_wave_days = climate_data.get('cold_wave_days', 3)
		base_probability = min(cold_wave_days / 365, 0.3)
		adjusted_probability = base_probability * (1 + physical_risk_score)
		return round(min(adjusted_probability, 1.0), 4)

	def calculate_damage_rate(self, collected_data: Dict[str, Any], physical_risk_score: float, asset_info: Dict[str, Any]) -> float:
		"""
		극심한 한파 발생 시 예상 손상률 계산
		"""
		if physical_risk_score >= 0.8:
			damage_rate = 0.12
		elif physical_risk_score >= 0.6:
			damage_rate = 0.08
		elif physical_risk_score >= 0.4:
			damage_rate = 0.04
		else:
			damage_rate = 0.02
		return round(damage_rate, 4)
