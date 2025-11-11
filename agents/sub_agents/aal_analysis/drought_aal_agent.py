'''
파일명: drought_aal_agent.py
최종 수정일: 2025-11-11
버전: v00
파일 개요: 가뭄 리스크 AAL 분석 Agent
'''
from typing import Dict, Any
from agents.sub_agents.aal_analysis.base_aal_analysis_agent import BaseAALAnalysisAgent


class DroughtAALAgent(BaseAALAnalysisAgent):
	def __init__(self):
		super().__init__(risk_type='drought')

	def calculate_hazard_probability(self, collected_data: Dict[str, Any], physical_risk_score: float) -> float:
		climate_data = collected_data.get('climate_data', {})
		drought_index = climate_data.get('drought_index', 0.3)
		base_probability = drought_index
		adjusted_probability = base_probability * (1 + physical_risk_score)
		return round(min(adjusted_probability, 1.0), 4)

	def calculate_damage_rate(self, collected_data: Dict[str, Any], physical_risk_score: float, asset_info: Dict[str, Any]) -> float:
		water_dependency = asset_info.get('water_dependency', 0.5)
		if physical_risk_score >= 0.8:
			damage_rate = 0.20 * water_dependency
		elif physical_risk_score >= 0.6:
			damage_rate = 0.12 * water_dependency
		elif physical_risk_score >= 0.4:
			damage_rate = 0.06 * water_dependency
		else:
			damage_rate = 0.02 * water_dependency
		return round(damage_rate, 4)
