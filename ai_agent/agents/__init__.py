"""
Agents Package
Super Agent 계층적 구조 (v05)

구조:
- data_processing: 데이터 수집 및 취약성 분석 (2개)
- risk_analysis: 물리적 리스크 분석 및 AAL 계산 (18개 Sub Agent)
- report_generation: 보고서 생성, 영향 분석, 전략 수립, 검증 (5개)

총 25개 에이전트
"""
# Data Processing Agents
from .data_processing import (
    DataCollectionAgent,
    VulnerabilityAnalysisAgent
)

# Risk Analysis Agents (18개)
from .risk_analysis import (
    # Physical Risk Score Agents (9개)
    ExtremeHeatScoreAgent,
    ExtremeColdScoreAgent,
    WildfireScoreAgent,
    DroughtScoreAgent,
    WaterStressScoreAgent,
    SeaLevelRiseScoreAgent,
    RiverFloodScoreAgent,
    UrbanFloodScoreAgent,
    TyphoonScoreAgent,
    # AAL Analysis Agents (9개)
    ExtremeHeatAALAgent,
    ExtremeColdAALAgent,
    WildfireAALAgent,
    DroughtAALAgent,
    WaterStressAALAgent,
    SeaLevelRiseAALAgent,
    RiverFloodAALAgent,
    UrbanFloodAALAgent,
    TyphoonAALAgent
)

# Report Generation Agents (7개)
from .report_generation import (
    ReportAnalysisAgent,
    ImpactAnalysisAgent,
    StrategyGenerationAgent,
    ReportComposerAgent,
    ValidationAgent,
    RefinerAgent,
    FinalizerNode
)



__all__ = [
    # Data Processing
    'DataCollectionAgent',
    'VulnerabilityAnalysisAgent',
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
    # Report Generation (7개)
    'ReportAnalysisAgent',
    'ImpactAnalysisAgent',
    'StrategyGenerationAgent',
    'ReportComposerAgent',
    'ValidationAgent',
    'RefinerAgent',
    'FinalizerNode',
]
