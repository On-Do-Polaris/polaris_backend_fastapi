'''
파일명: coastal_flood_aal_agent.py
최종 수정일: 2025-11-11
버전: v00
파일 개요: 해안 홍수 리스크 AAL 분석 Agent
'''
from typing import Dict, Any
from agents.sub_agents.aal_analysis.base_aal_analysis_agent import BaseAALAnalysisAgent


class CoastalFloodAALAgent(BaseAALAnalysisAgent):
	def __init__(self):
		super().__init__(risk_type='coastal_flood')

	def calculate_hazard_probability(self, collected_data: Dict[str, Any], physical_risk_score: float) -> float:
		climate_data = collected_data.get('climate_data', {})
		sea_level_rise = climate_data.get('sea_level_rise', 0.0)
		base_probability = min(sea_level_rise * 0.5, 0.3)
		adjusted_probability = base_probability * (1 + physical_risk_score * 2)
		return round(min(adjusted_probability, 1.0), 4)

	def calculate_damage_rate(self, collected_data: Dict[str, Any], physical_risk_score: float, asset_info: Dict[str, Any]) -> float:
		if physical_risk_score >= 0.8:
			damage_rate = 0.60
		elif physical_risk_score >= 0.6:
			damage_rate = 0.40
		elif physical_risk_score >= 0.4:
			damage_rate = 0.20
		else:
			damage_rate = 0.05
		return round(damage_rate, 4)
