"""
Risk Analysis Agents
물리적 리스크 분석 및 AAL 계산 에이전트
"""
# Physical Risk Score Agents (9개)
from .physical_risk_score.extreme_heat_score_agent import ExtremeHeatScoreAgent
from .physical_risk_score.extreme_cold_score_agent import ExtremeColdScoreAgent
from .physical_risk_score.wildfire_score_agent import WildfireScoreAgent
from .physical_risk_score.drought_score_agent import DroughtScoreAgent
from .physical_risk_score.water_stress_score_agent import WaterStressScoreAgent
from .physical_risk_score.sea_level_rise_score_agent import SeaLevelRiseScoreAgent
from .physical_risk_score.river_flood_score_agent import RiverFloodScoreAgent
from .physical_risk_score.urban_flood_score_agent import UrbanFloodScoreAgent
from .physical_risk_score.typhoon_score_agent import TyphoonScoreAgent

# AAL Analysis Agents (9개)
from .aal_analysis.extreme_heat_aal_agent import ExtremeHeatAALAgent
from .aal_analysis.extreme_cold_aal_agent import ExtremeColdAALAgent
from .aal_analysis.wildfire_aal_agent import WildfireAALAgent
from .aal_analysis.drought_aal_agent import DroughtAALAgent
from .aal_analysis.water_stress_aal_agent import WaterStressAALAgent
from .aal_analysis.sea_level_rise_aal_agent import SeaLevelRiseAALAgent
from .aal_analysis.river_flood_aal_agent import RiverFloodAALAgent
from .aal_analysis.urban_flood_aal_agent import UrbanFloodAALAgent
from .aal_analysis.typhoon_aal_agent import TyphoonAALAgent

__all__ = [
    # Physical Risk Score Agents
    'ExtremeHeatScoreAgent',
    'ExtremeColdScoreAgent',
    'WildfireScoreAgent',
    'DroughtScoreAgent',
    'WaterStressScoreAgent',
    'SeaLevelRiseScoreAgent',
    'RiverFloodScoreAgent',
    'UrbanFloodScoreAgent',
    'TyphoonScoreAgent',
    # AAL Analysis Agents
    'ExtremeHeatAALAgent',
    'ExtremeColdAALAgent',
    'WildfireAALAgent',
    'DroughtAALAgent',
    'WaterStressAALAgent',
    'SeaLevelRiseAALAgent',
    'RiverFloodAALAgent',
    'UrbanFloodAALAgent',
    'TyphoonAALAgent',
]
