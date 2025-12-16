"""
Primary Data Agents (구 Data Processing Agents)
건물 특징 분석, 추가 데이터 분석 (2개 에이전트)

- BuildingCharacteristicsAgent: LLM 기반 건물 특징 및 리스크 점수 해석 (다중 사업장 배치 처리)
- AdditionalDataAgent: 추가 데이터 (Excel) 분석 및 가이드라인 생성 (조건부 실행)

작성일: 2025-12-15
버전: v03 (TCFD Report v2.1)

REMOVED (2025-12-15):
- DataCollectionAgent: 삭제됨 (Node 0에서 DB 직접 조회로 대체)
- VulnerabilityAnalysisAgent: 삭제됨 (ModelOps가 H, E, V 모두 계산)
- SimpleVulnerabilityAnalyzer: 삭제됨 (미사용)
"""
from .building_characteristics_agent import BuildingCharacteristicsAgent
from .additional_data_agent import AdditionalDataAgent

__all__ = [
    'BuildingCharacteristicsAgent',
    'AdditionalDataAgent'
]
