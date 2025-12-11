'''
파일명: state.py
최종 수정일: 2025-12-02
버전: v05
파일 개요: LangGraph 워크플로우 상태 정의 (Phase 2 전용 + 다중 사업장 지원)
변경 이력:
	- 2025-11-11: v01 - Super Agent 계층적 구조로 전면 개편
	- 2025-11-21: v02 - Scratch Space 기반 데이터 관리 적용
	- 2025-11-25: v03 - AALAnalysisState를 v11 아키텍처에 맞게 업데이트
	- 2025-12-01: v04 - Building Characteristics 분석 필드 추가 (Fork-Join 병렬 구조)
	                   - Additional Data Guidelines 필드 추가
	- 2025-12-02: v05 - Phase 1/2 분리: Phase 1 필드 제거 (physical_risk_scores, aal_analysis, risk_analysis_status 등)
	                   - 다중 사업장 지원 필드 추가 (site_ids, sites_data)
	                   - DB 로드 기반 데이터 관리
'''
from typing import TypedDict, Dict, Any, List, Optional
from typing_extensions import Annotated
import operator


class SuperAgentState(TypedDict, total=False):
	"""
	Super Agent 최상위 계층 상태 관리 (v05 - Phase 2 전용 + 다중 사업장 지원)
	전체 워크플로우의 상태를 추적하고 관리
	"""
	# ========== 입력 정보 ==========
	target_location: Dict[str, Any]  # 분석 대상 위치 (위도, 경도, 주소) - 단일 사업장
	building_info: Dict[str, Any]  # 건물 정보 (연식, 구조, 용도) - 단일 사업장
	asset_info: Dict[str, Any]  # 사업장 노출 자산 정보 - 단일 사업장
	analysis_params: Dict[str, Any]  # 분석 파라미터 (시간 범위, 시나리오)
	company_name: Optional[str]  # 회사명 (Report Analysis용)
	past_reports: Optional[List[str]]  # 기존 보고서 텍스트 리스트 (Report Analysis용)
	language: Optional[str]  # 보고서 출력 언어 ('ko', 'en') - 기본값: 'en'

	# ========== 다중 사업장 지원 (NEW in v05) ==========
	site_ids: Optional[List[str]]  # 다중 사업장 ID 리스트 (analyze_integrated용)
	sites_data: Optional[List[Dict[str, Any]]]  # 사업장별 데이터 (H, E, V, risk_scores, AAL, building_info, asset_info)

	# ========== 추가 데이터 ==========
	additional_data: Optional[Dict[str, Any]]  # 사용자 제공 추가 데이터 (raw_text, metadata)
	additional_data_guidelines: Optional[Dict[str, Any]]  # Agent별 가이드라인 (Pre-processing 결과)

	# ========== Step 1: 데이터 수집 (DB 로드) ==========
	scratch_session_id: str  # Scratch Space 세션 ID (데이터 참조용)
	climate_summary: Optional[Dict[str, Any]]  # 기후 데이터 요약 통계 (작은 크기)
	data_collection_status: str  # 데이터 수집 상태

	# ========== Phase 1 결과 (DB에서 로드) ==========
	# 단일 사업장
	hazard_scores: Optional[Dict[str, float]]  # H 값 (DB 로드)
	exposure_scores: Optional[Dict[str, float]]  # E 값 (DB 로드)
	vulnerability_scores: Optional[Dict[str, float]]  # V 값 (DB 로드)
	risk_scores: Optional[Dict[str, float]]  # 물리적 리스크 점수 (DB 로드)
	aal_values: Optional[Dict[str, float]]  # AAL 값 (DB 로드)

	# ========== 건물 특징 분석 (Phase 2) ==========
	building_characteristics: Optional[Dict[str, Any]]  # 건물 특징 분석 결과 (LLM 기반 정성 분석)
	building_analysis_status: str  # 건물 특징 분석 상태

	# ========== Phase 1 필드 (DEPRECATED - v05에서 제거) ==========
	# 다음 필드들은 Phase 1 전용이므로 Phase 2에서는 사용하지 않음
	# vulnerability_analysis: 제거 (ModelOps가 V 계산)
	# vulnerability_status: 제거
	# selected_risks: 제거 (DB에서 로드된 risk_scores 사용)
	# risk_analysis_status: 제거
	# physical_risk_scores: 제거 (risk_scores로 대체)
	# physical_score_status: 제거
	# aal_analysis: 제거 (aal_values로 대체)
	# aal_status: 제거

	# ========== Step 5: 리포트 템플릿 생성 ==========
	report_template: Optional[Dict[str, Any]]  # 생성된 리포트 템플릿
	template_status: str  # 템플릿 생성 상태

	# ========== Step 6: 영향 분석 (전력 사용량 기반) ==========
	impact_analysis: Optional[Dict[str, Any]]  # 리스크 영향 분석 결과
	impact_status: str  # 영향 분석 상태

	# ========== Step 7: 대응 전략 생성 (LLM + RAG) ==========
	response_strategy: Optional[Dict[str, Any]]  # LLM 기반 대응 전략
	strategy_status: str  # 전략 생성 상태
	llm_reasoning: Optional[str]  # LLM 추론 과정

	# ========== Step 8: 리포트 생성 ==========
	generated_report: Optional[Dict[str, Any]]  # 생성된 리포트
	report_status: str  # 리포트 생성 상태

	# ========== Step 9: 검증 (정확성/일관성 확인) ==========
	validation_result: Optional[Dict[str, Any]]  # 검증 결과
	validation_status: str  # 검증 상태 (passed, failed)
	validation_feedback: Optional[List[str]]  # 검증 피드백 (미달 시 개선 사항)

	# ========== Step 10: Refiner (검증 실패 시 자동 보완) ==========
	refined_report: Optional[Dict[str, Any]]  # Refiner가 개선한 보고서
	refiner_status: str  # Refiner 상태
	applied_fixes: Optional[List[str]]  # 적용된 수정사항 목록
	refiner_loop_count: int  # Refiner Loop 실행 횟수

	# ========== Step 11: 최종 리포트 ==========
	final_report: Optional[Dict[str, Any]]  # 최종 승인된 리포트
	final_status: str  # 최종 상태
	output_paths: Optional[Dict[str, str]]  # 최종 출력 파일 경로 (md, json, pdf)

	# ========== 에러 및 로그 ==========
	errors: Annotated[List[str], operator.add]  # 에러 목록 (병합)
	logs: Annotated[List[str], operator.add]  # 로그 목록 (병합)

	# ========== 워크플로우 제어 ==========
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
	연평균 재무 손실률 분석 Sub Agent 상태 (v11)

	v11 변경사항:
	- AALCalculatorService로 base_aal 계산 (외부 서비스)
	- AAL Agent는 vulnerability scaling만 수행
	- 공식: AAL = base_aal × F_vuln × (1-IR)
	"""
	risk_type: str  # 리스크 타입
	scratch_session_id: str  # Scratch Space 세션 ID (원본 데이터 로드용)
	climate_summary: Dict[str, Any]  # 기후 데이터 요약
	vulnerability_score: float  # 취약성 점수 (0-100 스케일)

	# 계산 입력
	base_aal: float  # 기본 AAL (AALCalculatorService가 계산)

	# 계산 결과 (v11)
	vulnerability_scale: float  # F_vuln: 취약성 스케일 계수
	insurance_rate: float  # 보험 보전율 IR
	final_aal_percentage: float  # 최종 AAL (%)
	risk_level: str  # 위험 수준 (Minimal, Low, Moderate, High, Critical)

	# 상태
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
