'''
파일명: water_scarcity_aal_agent.py
최종 수정일: 2025-11-11
버전: v00
파일 개요: 물부족 리스크 AAL 분석 Agent
'''
from typing import Dict, Any
from .base_aal_analysis_agent import BaseAALAnalysisAgent


class WaterScarcityAALAgent(BaseAALAnalysisAgent):
	def __init__(self):
		super().__init__(risk_type='water_scarcity')

	def calculate_hazard_probability(self, collected_data: Dict[str, Any], physical_risk_score: float) -> float:
		climate_data = collected_data.get('climate_data', {})
		water_stress_index = climate_data.get('water_stress_index', 0.4)
		base_probability = water_stress_index * 0.5
		adjusted_probability = base_probability * (1 + physical_risk_score)
		return round(min(adjusted_probability, 1.0), 4)

	def calculate_damage_rate(self, collected_data: Dict[str, Any], physical_risk_score: float, asset_info: Dict[str, Any]) -> float:
		water_dependency = asset_info.get('water_dependency', 0.5)
		if physical_risk_score >= 0.8:
			damage_rate = 0.25 * water_dependency
		elif physical_risk_score >= 0.6:
			damage_rate = 0.15 * water_dependency
		elif physical_risk_score >= 0.4:
			damage_rate = 0.08 * water_dependency
		else:
			damage_rate = 0.03 * water_dependency
		return round(damage_rate, 4)
