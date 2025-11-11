"""
Agents Package
Super Agent 계층적 구조 (v03)
"""
from .data_collection_agent import DataCollectionAgent
from .vulnerability_analysis_agent import VulnerabilityAnalysisAgent
from .validation_agent import ValidationAgent
from .report_template_agent import ReportTemplateAgent
from .strategy_generation_agent import StrategyGenerationAgent
from .report_generation_agent import ReportGenerationAgent
# Physical Risk Score Agents (9개)
from .sub_agents.physical_risk_score.high_temperature_score_agent import HighTemperatureScoreAgent
from .sub_agents.physical_risk_score.cold_wave_score_agent import ColdWaveScoreAgent
from .sub_agents.physical_risk_score.wildfire_score_agent import WildfireScoreAgent
from .sub_agents.physical_risk_score.drought_score_agent import DroughtScoreAgent
from .sub_agents.physical_risk_score.water_scarcity_score_agent import WaterScarcityScoreAgent
from .sub_agents.physical_risk_score.coastal_flood_score_agent import CoastalFloodScoreAgent
from .sub_agents.physical_risk_score.inland_flood_score_agent import InlandFloodScoreAgent
from .sub_agents.physical_risk_score.urban_flood_score_agent import UrbanFloodScoreAgent
from .sub_agents.physical_risk_score.typhoon_score_agent import TyphoonScoreAgent

# AAL Analysis Agents (9개)
from .sub_agents.aal_analysis.high_temperature_aal_agent import HighTemperatureAALAgent
from .sub_agents.aal_analysis.cold_wave_aal_agent import ColdWaveAALAgent
from .sub_agents.aal_analysis.wildfire_aal_agent import WildfireAALAgent
from .sub_agents.aal_analysis.drought_aal_agent import DroughtAALAgent
from .sub_agents.aal_analysis.water_scarcity_aal_agent import WaterScarcityAALAgent
from .sub_agents.aal_analysis.coastal_flood_aal_agent import CoastalFloodAALAgent
from .sub_agents.aal_analysis.inland_flood_aal_agent import InlandFloodAALAgent
from .sub_agents.aal_analysis.urban_flood_aal_agent import UrbanFloodAALAgent
from .sub_agents.aal_analysis.typhoon_aal_agent import TyphoonAALAgent



__all__ = [
	'DataCollectionAgent',
	'VulnerabilityAnalysisAgent',
	'ValidationAgent',
	'ReportTemplateAgent',
	'StrategyGenerationAgent',
	'ReportGenerationAgent',
    'HighTemperatureScoreAgent',
    'ColdWaveScoreAgent',
    'WildfireScoreAgent',
    'DroughtScoreAgent',
    'WaterScarcityScoreAgent',
    'CoastalFloodScoreAgent',
    'InlandFloodScoreAgent',
    'UrbanFloodScoreAgent',
    'TyphoonScoreAgent',
    'HighTemperatureAALAgent',
    'ColdWaveAALAgent',
    'WildfireAALAgent',
    'DroughtAALAgent',
    'WaterScarcityAALAgent',
    'CoastalFloodAALAgent',
    'InlandFloodAALAgent',
    'UrbanFloodAALAgent',
    'TyphoonAALAgent',
]
