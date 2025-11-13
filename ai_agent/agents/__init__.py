"""
Agents Package
Super Agent 계층적 구조 (v04)

구조:
- data_processing: 데이터 수집 및 취약성 분석
- risk_analysis: 물리적 리스크 분석 및 AAL 계산 (18개 Sub Agent)
- report_generation: 보고서 생성, 전략 수립, 검증
"""
# Data Processing Agents
from .data_processing import (
    DataCollectionAgent,
    VulnerabilityAnalysisAgent
)

# Risk Analysis Agents (18개)
from .risk_analysis import (
    # Physical Risk Score Agents (9개)
    HighTemperatureScoreAgent,
    ColdWaveScoreAgent,
    WildfireScoreAgent,
    DroughtScoreAgent,
    WaterScarcityScoreAgent,
    CoastalFloodScoreAgent,
    InlandFloodScoreAgent,
    UrbanFloodScoreAgent,
    TyphoonScoreAgent,
    # AAL Analysis Agents (9개)
    HighTemperatureAALAgent,
    ColdWaveAALAgent,
    WildfireAALAgent,
    DroughtAALAgent,
    WaterScarcityAALAgent,
    CoastalFloodAALAgent,
    InlandFloodAALAgent,
    UrbanFloodAALAgent,
    TyphoonAALAgent
)

# Report Generation Agents
from .report_generation import (
    ValidationAgent,
    ReportGenerationAgent,
    StrategyGenerationAgent,
    ReportTemplateAgent
)



__all__ = [
    # Data Processing
    'DataCollectionAgent',
    'VulnerabilityAnalysisAgent',
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
    # Report Generation
    'ValidationAgent',
    'ReportGenerationAgent',
    'StrategyGenerationAgent',
    'ReportTemplateAgent',
]
