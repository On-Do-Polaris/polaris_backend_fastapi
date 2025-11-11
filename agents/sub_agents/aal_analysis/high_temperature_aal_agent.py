'''
파일명: high_temperature_aal_agent.py
최종 수정일: 2025-11-11
버전: v00
파일 개요: 극심한 고온 리스크 AAL 분석 Agent
'''
from typing import Dict, Any
from agents.sub_agents.aal_analysis.base_aal_analysis_agent import BaseAALAnalysisAgent


class HighTemperatureAALAgent(BaseAALAnalysisAgent):
	"""
	극심한 고온 리스크 AAL 분석 Agent
	"""

	def __init__(self):
		"""
		HighTemperatureAALAgent 초기화
		"""
		super().__init__(risk_type='high_temperature')

	def calculate_hazard_probability(self, collected_data: Dict[str, Any], physical_risk_score: float) -> float:
		"""
		극심한 고온 위험 발생 확률 계산
		"""
		climate_data = collected_data.get('climate_data', {})
		heatwave_days = climate_data.get('heatwave_days', 5)
		
		# 연간 폭염일수 기반 확률
		base_probability = min(heatwave_days / 365, 0.5)
		
		# 물리적 리스크 점수 반영
		adjusted_probability = base_probability * (1 + physical_risk_score)
		
		return round(min(adjusted_probability, 1.0), 4)

	def calculate_damage_rate(self, collected_data: Dict[str, Any], physical_risk_score: float, asset_info: Dict[str, Any]) -> float:
		"""
		극심한 고온 발생 시 예상 손상률 계산
		"""
		# 물리적 리스크 점수 기반 손상률 추정
		if physical_risk_score >= 0.8:
			damage_rate = 0.15
		elif physical_risk_score >= 0.6:
			damage_rate = 0.10
		elif physical_risk_score >= 0.4:
			damage_rate = 0.05
		else:
			damage_rate = 0.02
		
		return round(damage_rate, 4)
