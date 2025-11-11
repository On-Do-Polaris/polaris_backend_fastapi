'''
파일명: wildfire_aal_agent.py
최종 수정일: 2025-11-11
버전: v00
파일 개요: 산불 리스크 AAL 분석 Agent
'''
from typing import Dict, Any
from agents.sub_agents.aal_analysis.base_aal_analysis_agent import BaseAALAnalysisAgent


class WildfireAALAgent(BaseAALAnalysisAgent):
	def __init__(self):
		super().__init__(risk_type='wildfire')

	def calculate_hazard_probability(self, collected_data: Dict[str, Any], physical_risk_score: float) -> float:
		climate_data = collected_data.get('climate_data', {})
		fire_risk_index = climate_data.get('fire_risk_index', 0.3)
		base_probability = fire_risk_index * 0.1
		adjusted_probability = base_probability * (1 + physical_risk_score * 2)
		return round(min(adjusted_probability, 1.0), 4)

	def calculate_damage_rate(self, collected_data: Dict[str, Any], physical_risk_score: float, asset_info: Dict[str, Any]) -> float:
		if physical_risk_score >= 0.8:
			damage_rate = 0.50
		elif physical_risk_score >= 0.6:
			damage_rate = 0.30
		elif physical_risk_score >= 0.4:
			damage_rate = 0.15
		else:
			damage_rate = 0.05
		return round(damage_rate, 4)
