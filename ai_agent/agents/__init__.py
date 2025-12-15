"""
Agents Package
Phase 2 구조 (v08 - Phase 1 Agents ModelOps 이관)

구조:
- primary_data: 데이터 수집, 건물 특징 분석, 추가 데이터 분석 (3개)
- risk_analysis: ModelOps로 이관 (Phase 1 제거)
- report_generation: 보고서 생성, 영향 분석, 전략 수립, 검증, 보완 (7개)
- tcfd_report: TCFD 보고서 생성 (7-Node Refactoring)

총 10개 에이전트 (Phase 2 전용)
"""
# Primary Data Agents (구 data_processing)
from .primary_data import (
    # DataCollectionAgent 삭제 (Node 0에서 DB 직접 조회)
    # VulnerabilityAnalysisAgent 삭제 (ModelOps가 V 계산)
    BuildingCharacteristicsAgent,
    AdditionalDataAgent
)

# Risk Analysis Agents - ModelOps로 이관 (Phase 1)
# Physical Risk Score Agents (9개) - 삭제됨
# AAL Analysis Agents (9개) - 삭제됨

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
    # Primary Data (2개)
    'BuildingCharacteristicsAgent',
    'AdditionalDataAgent',
    # Report Generation (7개)
    'ReportAnalysisAgent',
    'ImpactAnalysisAgent',
    'StrategyGenerationAgent',
    'ReportComposerAgent',
    'ValidationAgent',
    'RefinerAgent',
    'FinalizerNode',
]
