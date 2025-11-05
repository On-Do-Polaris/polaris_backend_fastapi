"""
LangGraph State Definition
워크플로우 상태 정의
"""
from typing import TypedDict, Dict, Any, List, Optional
from typing_extensions import Annotated
import operator


class AnalysisState(TypedDict, total=False):
    """
    전체 분석 워크플로우의 상태
    """
    # 입력 정보
    target_location: Dict[str, Any]
    analysis_params: Dict[str, Any]

    # Step 1: 데이터 수집
    collected_data: Optional[Dict[str, Any]]
    data_collection_status: str

    # Step 2: SSP 시나리오 확률
    ssp_probabilities: Optional[Dict[str, float]]
    ssp_calculation_status: str

    # Step 3: 8대 기후 리스크 (병렬 처리)
    climate_risk_scores: Annotated[Dict[str, Any], operator.add]
    completed_risk_analyses: Annotated[List[str], operator.add]

    # Step 4: 리스크 통합
    integrated_risk: Optional[Dict[str, Any]]
    integration_status: str

    # Step 5: 리포트 생성
    report: Optional[Dict[str, Any]]
    report_status: str

    # 에러 및 로그
    errors: Annotated[List[str], operator.add]
    logs: Annotated[List[str], operator.add]

    # 워크플로우 제어
    current_step: str
    workflow_status: str  # 'in_progress', 'completed', 'failed'


class ClimateRiskState(TypedDict, total=False):
    """
    개별 기후 리스크 분석 상태
    """
    risk_type: str
    collected_data: Dict[str, Any]
    ssp_weights: Dict[str, float]

    # 계산 결과
    hazard_score: float
    exposure_score: float
    vulnerability_score: float
    risk_score: float

    # 상세 정보
    details: Dict[str, Any]
    status: str
