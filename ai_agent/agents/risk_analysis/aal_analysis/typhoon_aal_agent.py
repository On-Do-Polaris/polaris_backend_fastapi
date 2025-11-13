'''
파일명: typhoon_aal_agent.py
최종 수정일: 2025-11-11
버전: v00
파일 개요: 열대성 태풍 리스크 AAL 분석 Agent
'''
from typing import Dict, Any
from .base_aal_analysis_agent import BaseAALAnalysisAgent


class TyphoonAALAgent(BaseAALAnalysisAgent):
	def __init__(self):
		super().__init__(risk_type='typhoon')

	def calculate_hazard_probability(self, collected_data: Dict[str, Any], physical_risk_score: float) -> float:
		climate_data = collected_data.get('climate_data', {})
		typhoon_frequency = climate_data.get('typhoon_frequency', 2)
		base_probability = min(typhoon_frequency / 10, 0.5)
		adjusted_probability = base_probability * (1 + physical_risk_score * 1.5)
		return round(min(adjusted_probability, 1.0), 4)

	def calculate_damage_rate(self, collected_data: Dict[str, Any], physical_risk_score: float, asset_info: Dict[str, Any]) -> float:
		climate_data = collected_data.get('climate_data', {})
		max_wind_speed = climate_data.get('max_wind_speed', 30)
		if max_wind_speed >= 50:
			base_damage = 0.70
		elif max_wind_speed >= 40:
			base_damage = 0.50
		elif max_wind_speed >= 30:
			base_damage = 0.30
		else:
			base_damage = 0.10
		damage_rate = base_damage * (0.5 + physical_risk_score * 0.5)
		return round(min(damage_rate, 0.9), 4)
