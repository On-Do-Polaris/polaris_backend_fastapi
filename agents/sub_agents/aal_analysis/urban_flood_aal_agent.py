'''
파일명: urban_flood_aal_agent.py
최종 수정일: 2025-11-11
버전: v00
파일 개요: 도시 집중 홍수 리스크 AAL 분석 Agent
'''
from typing import Dict, Any
from agents.sub_agents.aal_analysis.base_aal_analysis_agent import BaseAALAnalysisAgent


class UrbanFloodAALAgent(BaseAALAnalysisAgent):
	def __init__(self):
		super().__init__(risk_type='urban_flood')

	def calculate_hazard_probability(self, collected_data: Dict[str, Any], physical_risk_score: float) -> float:
		climate_data = collected_data.get('climate_data', {})
		max_hourly_rainfall = climate_data.get('max_hourly_rainfall', 50)
		base_probability = min(max_hourly_rainfall / 200, 0.4)
		adjusted_probability = base_probability * (1 + physical_risk_score * 2)
		return round(min(adjusted_probability, 1.0), 4)

	def calculate_damage_rate(self, collected_data: Dict[str, Any], physical_risk_score: float, asset_info: Dict[str, Any]) -> float:
		basement_floors = asset_info.get('basement_floors', 0)
		base_damage = 0.10 if physical_risk_score >= 0.6 else 0.05
		basement_multiplier = 1 + (basement_floors * 0.5)
		damage_rate = base_damage * basement_multiplier
		return round(min(damage_rate, 0.8), 4)
