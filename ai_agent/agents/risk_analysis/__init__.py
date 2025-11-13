"""
Risk Analysis Agents
물리적 리스크 분석 및 AAL 계산 에이전트
"""
# Physical Risk Score Agents (9개)
from .physical_risk_score.high_temperature_score_agent import HighTemperatureScoreAgent
from .physical_risk_score.cold_wave_score_agent import ColdWaveScoreAgent
from .physical_risk_score.wildfire_score_agent import WildfireScoreAgent
from .physical_risk_score.drought_score_agent import DroughtScoreAgent
from .physical_risk_score.water_scarcity_score_agent import WaterScarcityScoreAgent
from .physical_risk_score.coastal_flood_score_agent import CoastalFloodScoreAgent
from .physical_risk_score.inland_flood_score_agent import InlandFloodScoreAgent
from .physical_risk_score.urban_flood_score_agent import UrbanFloodScoreAgent
from .physical_risk_score.typhoon_score_agent import TyphoonScoreAgent

# AAL Analysis Agents (9개)
from .aal_analysis.high_temperature_aal_agent import HighTemperatureAALAgent
from .aal_analysis.cold_wave_aal_agent import ColdWaveAALAgent
from .aal_analysis.wildfire_aal_agent import WildfireAALAgent
from .aal_analysis.drought_aal_agent import DroughtAALAgent
from .aal_analysis.water_scarcity_aal_agent import WaterScarcityAALAgent
from .aal_analysis.coastal_flood_aal_agent import CoastalFloodAALAgent
from .aal_analysis.inland_flood_aal_agent import InlandFloodAALAgent
from .aal_analysis.urban_flood_aal_agent import UrbanFloodAALAgent
from .aal_analysis.typhoon_aal_agent import TyphoonAALAgent

__all__ = [
    # Physical Risk Score Agents
    'HighTemperatureScoreAgent',
    'ColdWaveScoreAgent',
    'WildfireScoreAgent',
    'DroughtScoreAgent',
    'WaterScarcityScoreAgent',
    'CoastalFloodScoreAgent',
    'InlandFloodScoreAgent',
    'UrbanFloodScoreAgent',
    'TyphoonScoreAgent',
    # AAL Analysis Agents
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
