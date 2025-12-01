"""
Data Processing Agents
데이터 수집, 건물 특징 분석 (2개 에이전트, vulnerability_analysis 삭제)

- DataCollectionAgent: 기후 데이터 및 전력 사용량 수집
- BuildingCharacteristicsAgent: LLM 기반 건물 특징 및 리스크 점수 해석 (Fork-Join 병렬)

REMOVED:
- VulnerabilityAnalysisAgent: 삭제됨 (ModelOps가 H, E, V 모두 계산)
"""
from .data_collection_agent import DataCollectionAgent
# from .vulnerability_analysis_agent import VulnerabilityAnalysisAgent  # 삭제됨
from .building_characteristics_agent import BuildingCharacteristicsAgent

__all__ = [
    'DataCollectionAgent',
    # 'VulnerabilityAnalysisAgent',  # 삭제됨
    'BuildingCharacteristicsAgent'
]
