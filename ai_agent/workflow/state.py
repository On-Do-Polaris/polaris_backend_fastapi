'''
파일명: state.py
최종 수정일: 2025-11-21
버전: v02
파일 개요: LangGraph 워크플로우 상태 정의 (계층적 Super Agent 구조용)
변경 이력:
	- 2025-11-11: v01 - Super Agent 계층적 구조로 전면 개편
	- 2025-11-21: v02 - Scratch Space 기반 데이터 관리 적용
'''
from typing import TypedDict, Dict, Any, List, Optional
from typing_extensions import Annotated
import operator


class SuperAgentState(TypedDict, total=False):
	"""
	Super Agent 최상위 계층 상태 관리
	전체 워크플로우의 상태를 추적하고 관리
	"""
	# 입력 정보
	target_location: Dict[str, Any]  # 분석 대상 위치 (위도, 경도, 주소)
	building_info: Dict[str, Any]  # 건물 정보 (연식, 구조, 용도)
	asset_info: Dict[str, Any]  # 사업장 노출 자산 정보
	analysis_params: Dict[str, Any]  # 분석 파라미터 (시간 범위, 시나리오)

	# Step 1: 데이터 수집 (Scratch Space 기반)
	scratch_session_id: str  # Scratch Space 세션 ID (데이터 참조용)
	climate_summary: Optional[Dict[str, Any]]  # 기후 데이터 요약 통계 (작은 크기)
	data_collection_status: str  # 데이터 수집 상태

	# Step 2: 취약성 분석
	vulnerability_analysis: Optional[Dict[str, Any]]  # 취약성 분석 결과 (건물 연식, 내진 설계, 소방차 진입)
	vulnerability_status: str  # 취약성 분석 상태

	# Step 3: 리스크 분석 (9개 리스크로 분기)
	selected_risks: List[str]  # 선정된 리스크 목록
	risk_analysis_status: Dict[str, str]  # 각 리스크별 분석 상태

	# Step 4: 물리적 리스크별 종합 점수 산출 (Sub Agent 9개)
	physical_risk_scores: Annotated[Dict[str, Any], operator.add]  # 리스크별 종합 점수 (병합)
	physical_score_status: str  # 물리적 리스크 점수 산출 상태

	# Step 5: 연평균 재무 손실률 분석 (Sub Agent 9개)
	aal_analysis: Annotated[Dict[str, Any], operator.add]  # 리스크별 AAL 분석 결과 (병합)
	aal_status: str  # AAL 분석 상태

	# Step 6: 기존 보고서 참고 및 템플릿 형성
	report_template: Optional[Dict[str, Any]]  # 생성된 리포트 템플릿
	template_status: str  # 템플릿 생성 상태

	# Step 7: 영향 분석 (전력 사용량 기반)
	impact_analysis: Optional[Dict[str, Any]]  # 리스크 영향 분석 결과
	impact_status: str  # 영향 분석 상태

	# Step 8: 대응 전략 생성 (LLM + RAG)
	response_strategy: Optional[Dict[str, Any]]  # LLM 기반 대응 전략
	strategy_status: str  # 전략 생성 상태
	llm_reasoning: Optional[str]  # LLM 추론 과정

	# Step 9: 리포트 생성
	generated_report: Optional[Dict[str, Any]]  # 생성된 리포트
	report_status: str  # 리포트 생성 상태

	# Step 10: 검증 (정확성/일관성 확인)
	validation_result: Optional[Dict[str, Any]]  # 검증 결과
	validation_status: str  # 검증 상태 (passed, failed)
	validation_feedback: Optional[List[str]]  # 검증 피드백 (미달 시 개선 사항)

	# Step 11: 최종 리포트
	final_report: Optional[Dict[str, Any]]  # 최종 승인된 리포트
	final_status: str  # 최종 상태

	# 에러 및 로그
	errors: Annotated[List[str], operator.add]  # 에러 목록 (병합)
	logs: Annotated[List[str], operator.add]  # 로그 목록 (병합)

	# 워크플로우 제어
	current_step: str  # 현재 실행 단계
	workflow_status: str  # 워크플로우 상태 (in_progress, completed, failed)
	retry_count: int  # 재시도 횟수 (검증 실패 시)


class PhysicalRiskScoreState(TypedDict, total=False):
	"""
	물리적 리스크별 종합 점수 산출 Sub Agent 상태
	각 리스크별로 H x E x V 기반 종합 점수 계산
	"""
	risk_type: str  # 리스크 타입 (extreme_heat, extreme_cold, wildfire, drought, water_stress, sea_level_rise, river_flood, urban_flood, typhoon)
	scratch_session_id: str  # Scratch Space 세션 ID (필요시 원본 데이터 로드)
	climate_summary: Dict[str, Any]  # 기후 데이터 요약 (요약 통계만 사용)
	vulnerability_analysis: Dict[str, Any]  # 취약성 분석 결과
	asset_info: Dict[str, Any]  # 사업장 노출 자산 정보

	# 계산 결과
	hazard_score: float  # 위해성 점수 (Hazard)
	exposure_score: float  # 노출도 점수 (Exposure)
	vulnerability_score: float  # 취약성 점수 (Vulnerability)
	physical_risk_score: float  # 물리적 리스크 종합 점수 (H x E x V)

	# 상세 정보
	calculation_details: Dict[str, Any]  # 계산 상세 내역
	status: str  # 분석 상태


class AALAnalysisState(TypedDict, total=False):
	"""
	연평균 재무 손실률 분석 Sub Agent 상태
	P(H) x 손상률 기반 AAL 계산
	"""
	risk_type: str  # 리스크 타입
	scratch_session_id: str  # Scratch Space 세션 ID (원본 데이터 로드용)
	climate_summary: Dict[str, Any]  # 기후 데이터 요약
	physical_risk_score: float  # 물리적 리스크 점수 (선행 계산 결과)
	asset_info: Dict[str, Any]  # 사업장 노출 자산 정보

	# 계산 결과
	hazard_probability: float  # P(H): 위험 발생 확률
	damage_rate: float  # 손상률
	aal: float  # AAL (연평균 재무 손실률)
	financial_loss: float  # 연평균 재무 손실액 (AAL x 노출 자산)

	# 상세 정보
	calculation_details: Dict[str, Any]  # 계산 상세 내역
	status: str  # 분석 상태


class ValidationState(TypedDict, total=False):
	"""
	검증 Agent 상태
	생성된 리포트의 정확성과 일관성 확인
	"""
	report_to_validate: Dict[str, Any]  # 검증 대상 리포트
	validation_criteria: Dict[str, Any]  # 검증 기준

	# 검증 결과
	accuracy_check: bool  # 정확성 확인
	consistency_check: bool  # 일관성 확인
	completeness_check: bool  # 완전성 확인

	# 피드백
	issues_found: List[str]  # 발견된 문제점
	improvement_suggestions: List[str]  # 개선 제안
	validation_passed: bool  # 검증 통과 여부

	# 상태
	status: str  # 검증 상태
