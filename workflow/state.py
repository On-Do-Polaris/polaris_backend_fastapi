'''
파일명: state.py
최종 수정일: 2025-11-05
버전: v00
파일 개요: LangGraph 워크플로우 상태 정의 (TypedDict 기반)
'''
from typing import TypedDict, Dict, Any, List, Optional
from typing_extensions import Annotated
import operator


class AnalysisState(TypedDict, total=False):
	"""
	전체 분석 워크플로우의 상태 관리
	LangGraph의 StateGraph에서 사용되는 상태 딕셔너리
	"""
	# 입력 정보
	target_location: Dict[str, Any]  # 분석 대상 위치 (위도, 경도, 이름)
	analysis_params: Dict[str, Any]  # 분석 파라미터 (시간 범위, 분석 기간)

	# Step 1: 데이터 수집
	collected_data: Optional[Dict[str, Any]]  # 수집된 기후 데이터
	data_collection_status: str  # 데이터 수집 상태

	# Step 2: SSP 시나리오 확률
	ssp_probabilities: Optional[Dict[str, float]]  # SSP 시나리오별 가중치
	ssp_calculation_status: str  # SSP 계산 상태

	# Step 3: 8대 기후 리스크 (병렬 처리)
	climate_risk_scores: Annotated[Dict[str, Any], operator.add]  # 기후 리스크 점수 (병합)
	completed_risk_analyses: Annotated[List[str], operator.add]  # 완료된 리스크 분석 목록 (병합)

	# Step 4: 리스크 통합
	integrated_risk: Optional[Dict[str, Any]]  # 통합 리스크 결과
	integration_status: str  # 통합 상태

	# Step 5: 리포트 생성
	report: Optional[Dict[str, Any]]  # 최종 리포트
	report_status: str  # 리포트 생성 상태

	# 에러 및 로그
	errors: Annotated[List[str], operator.add]  # 에러 목록 (병합)
	logs: Annotated[List[str], operator.add]  # 로그 목록 (병합)

	# 워크플로우 제어
	current_step: str  # 현재 실행 단계
	workflow_status: str  # 워크플로우 상태 (in_progress, completed, failed)


class ClimateRiskState(TypedDict, total=False):
	"""
	개별 기후 리스크 분석 상태
	각 기후 리스크 에이전트가 사용하는 상태 구조
	"""
	risk_type: str  # 리스크 타입 (예: high_temperature, flood)
	collected_data: Dict[str, Any]  # 수집된 데이터
	ssp_weights: Dict[str, float]  # SSP 시나리오별 가중치

	# 계산 결과
	hazard_score: float  # 위해성 점수 (Hazard)
	exposure_score: float  # 노출도 점수 (Exposure)
	vulnerability_score: float  # 취약성 점수 (Vulnerability)
	risk_score: float  # 최종 리스크 점수 (H x E x V)

	# 상세 정보
	details: Dict[str, Any]  # 상세 분석 결과
	status: str  # 분석 상태
