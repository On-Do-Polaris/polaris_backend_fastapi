'''
파일명: nodes.py
최종 수정일: 2025-12-01
버전: v06
파일 개요: LangGraph 워크플로우 노드 함수 정의 (Super Agent 계층적 구조용)
변경 이력:
	- 2025-11-11: v01 - Super Agent 계층적 구조로 전면 개편, 10개 주요 노드 재구성
	- 2025-11-11: v02 - 노드 순서 변경 (Node 3: AAL 분석, Node 4: 물리적 리스크 점수 100점 스케일)
	- 2025-11-21: v03 - Scratch Space 기반 데이터 관리 적용
	- 2025-11-25: v04 - LangSmith 트레이싱 데코레이터 추가
	- 2025-11-25: v05 - AAL Agent v11 아키텍처 적용 (AALCalculatorService + vulnerability scaling)
	- 2025-12-01: v06 - 통합 Validation 노드 구현 (Report + Building Characteristics 동시 검증)
	                   - _validate_building_characteristics 헬퍼 함수 추가
'''
from typing import Dict, Any
import numpy as np
from .state import SuperAgentState

from ..utils.llm_client import LLMClient
from ..utils.rag_engine import RAGEngine
from ..utils.scratch_manager import ScratchSpaceManager

# LangSmith traceable 임포트
try:
	from langsmith import traceable
except ImportError:
	# LangSmith 미설치 시 no-op 데코레이터
	def traceable(*args, **kwargs):
		def decorator(func):
			return func
		return decorator

from ..agents import (
	DataCollectionAgent,
	# VulnerabilityAnalysisAgent,  # 삭제됨 (ModelOps가 V 계산)
	# Physical Risk Score Agents,  # 삭제됨 (ModelOps가 H×E×V 계산)
	# AAL Analysis Agents,         # 삭제됨 (ModelOps가 AAL 계산)
	ReportAnalysisAgent,
	ImpactAnalysisAgent,
	StrategyGenerationAgent,
	ReportComposerAgent,
	ValidationAgent,
	RefinerAgent,
	FinalizerNode
)

from ..agents.primary_data.building_characteristics_agent import BuildingCharacteristicsAgent

# Scratch Space Manager 초기화 (TTL 4시간)
scratch_manager = ScratchSpaceManager(base_path="./scratch", default_ttl_hours=4)


# ========== Node 1: ModelOps API 요청 트리거 ==========
@traceable(name="modelops_trigger_node", tags=["workflow", "node", "modelops-trigger"])
def data_collection_node(state: SuperAgentState, config: Any) -> Dict:
	"""
	ModelOps API 요청 트리거 노드
	사업장 리스크 계산 요청을 ModelOps로 전송하고 200 응답 확인

	Args:
		state: 현재 워크플로우 상태
		config: 설정 객체

	Returns:
		업데이트된 상태 딕셔너리
	"""
	print("[Node 1] ModelOps API 요청 트리거...")

	# Workflow Mock 모드 체크
	if config.WORKFLOW_MOCK_MODE:
		print("  [MOCK] Using mock ModelOps request")
		return {
			'modelops_request_id': 'mock_request_12345',
			'modelops_status': 'triggered',
			'data_collection_status': 'completed',
			'current_step': 'risk_assessment',
			'logs': ['Workflow Mock: ModelOps 요청 완료']
		}

	try:
		from ai_agent.services import get_modelops_client

		# ModelOps 클라이언트 초기화
		modelops_client = get_modelops_client()

		# Step 1: 위치 및 사업장 정보 추출
		target_location = state.get('target_location', {})
		latitude = target_location.get('latitude')
		longitude = target_location.get('longitude')
		site_id = state.get('site_id', target_location.get('site_id'))

		if not latitude or not longitude:
			raise ValueError("위경도 정보가 필요합니다")

		print(f"  - 위치: lat={latitude}, lng={longitude}, site_id={site_id}")

		# Step 2: 건물 및 자산 정보 추출
		additional_data = state.get('additional_data', {})
		building_info = additional_data.get('building_info', {}) if additional_data else {}
		asset_info = additional_data.get('asset_info', {}) if additional_data else {}

		# Step 3: ModelOps API 호출 - 사업장 리스크 계산 (동기)
		print("  - ModelOps 사업장 리스크 계산 중...")
		response = modelops_client.calculate_site_risk(
			latitude=latitude,
			longitude=longitude,
			site_id=site_id,
			building_info=building_info,
			asset_info=asset_info
		)

		print(f"  [OK] 사업장 리스크 계산 완료 (HTTP 200)")
		print(f"  - site_id: {response.get('site_id')}")
		print(f"  - 계산 시각: {response.get('calculated_at')}")

		# Step 4: ModelOps API 호출 - 후보지 추천 (비동기, 콜백 방식)
		# ModelOps가 추천 완료 후 FastAPI /api/internal/modelops/recommendation-complete 호출
		# 현재는 후보지 추천 기능 미구현으로 스킵 (향후 ModelOps 측 구현 필요)

		# Step 5: State 업데이트 (Node 3에서 DB 조회에 필요한 정보만 저장)
		return {
			'modelops_request_id': response.get('site_id'),  # site_id를 request_id로 사용
			'modelops_latitude': latitude,
			'modelops_longitude': longitude,
			'modelops_site_id': site_id,
			'modelops_status': 'triggered',
			'data_collection_status': 'completed',
			'current_step': 'risk_assessment',
			'logs': [
				'ModelOps 사업장 리스크 계산 완료 (HTTP 200)',
				f'Site ID: {site_id}',
				f'위치: ({latitude}, {longitude})'
			]
		}

	except Exception as e:
		print(f"[Node 1] 오류: {str(e)}")
		import traceback
		traceback.print_exc()
		return {
			'data_collection_status': 'failed',
			'modelops_status': 'failed',
			'errors': [f'ModelOps API 요청 오류: {str(e)}']
		}


# ========== Node 2 (REMOVED): 취약성 분석 노드 삭제됨 ==========
# ModelOps가 H, E, V를 모두 계산하므로 이 노드는 더 이상 필요하지 않습니다.
# vulnerability_analysis_node 함수 삭제됨 (2025-12-01)


# ========== Node 3: DB에서 리스크 결과 조회 ==========
@traceable(name="risk_results_fetch_node", tags=["workflow", "node", "risk-fetch", "database"])
def risk_assessment_node(state: SuperAgentState, config: Any) -> Dict:
	"""
	DB에서 리스크 평가 결과 조회 노드

	변경사항 (2025-12-11):
	- Node 1에서 ModelOps API 트리거 완료
	- Node 3에서 DB에서 결과 조회
	- DatabaseManager를 사용하여 site_assessment_results 테이블 쿼리

	Args:
		state: 현재 워크플로우 상태
		config: 설정 객체

	Returns:
		업데이트된 상태 딕셔너리
	"""
	print("[Node 3] DB에서 리스크 결과 조회 시작...")

	# Workflow Mock 모드 체크
	if config.WORKFLOW_MOCK_MODE:
		print("  [MOCK] Using mock risk assessment data")
		from ..utils.mock_data import get_mock_risk_assessment
		mock_data = get_mock_risk_assessment()
		return mock_data

	try:
		from ai_agent.utils.database import DatabaseManager

		# DatabaseManager 초기화
		db = DatabaseManager()

		# Step 1: Node 1에서 저장한 정보 추출
		latitude = state.get('modelops_latitude')
		longitude = state.get('modelops_longitude')
		site_id = state.get('modelops_site_id')

		if not latitude or not longitude:
			raise ValueError("위경도 정보가 필요합니다 (Node 1에서 설정되어야 함)")

		print(f"  - 조회 위치: lat={latitude}, lng={longitude}, site_id={site_id}")

		# Step 2: DB에서 결과 조회 (site_assessment_results 테이블)
		print("  - DB에서 계산 결과 조회 중...")

		# 쿼리 작성: site_id 또는 lat/lng로 최신 결과 조회
		if site_id:
			query = """
				SELECT
					site_id, latitude, longitude,
					hazard_data, exposure_data, vulnerability_data,
					integrated_risk_data, aal_data, summary_data,
					calculated_at
				FROM site_assessment_results
				WHERE site_id = %s
				ORDER BY calculated_at DESC
				LIMIT 1
			"""
			params = (site_id,)
		else:
			query = """
				SELECT
					site_id, latitude, longitude,
					hazard_data, exposure_data, vulnerability_data,
					integrated_risk_data, aal_data, summary_data,
					calculated_at
				FROM site_assessment_results
				WHERE latitude = %s AND longitude = %s
				ORDER BY calculated_at DESC
				LIMIT 1
			"""
			params = (latitude, longitude)

		result_rows = db.execute_query(query, params)

		if not result_rows or len(result_rows) == 0:
			raise ValueError(f"DB에 결과가 없습니다 (site_id={site_id}, lat={latitude}, lng={longitude})")

		# Step 3: 결과 파싱
		row = result_rows[0]
		results = {
			'site_id': row[0],
			'latitude': row[1],
			'longitude': row[2],
			'hazard': row[3],  # JSONB
			'exposure': row[4],  # JSONB
			'vulnerability': row[5],  # JSONB
			'integrated_risk': row[6],  # JSONB
			'aal_scaled': row[7],  # JSONB
			'summary': row[8],  # JSONB
			'calculated_at': row[9]
		}

		print(f"  [OK] DB 조회 완료")
		print(f"  - 계산 시각: {results.get('calculated_at')}")

		# Step 4: State 변수로 매핑 (기존 형식 호환성 유지)
		print("  - 결과 매핑 중...")

		hazard_scores = {}
		exposure_scores = {}
		vulnerability_scores = {}
		physical_risk_scores = {}
		aal_values = {}

		# 9개 리스크별 데이터 파싱
		risk_types = ['extreme_heat', 'extreme_cold', 'wildfire', 'drought',
		              'water_stress', 'sea_level_rise', 'river_flood', 'urban_flood', 'typhoon']

		for risk_type in risk_types:
			# Hazard
			h_data = results.get('hazard', {}).get(risk_type, {})
			hazard_scores[f'{risk_type}_hazard_score'] = h_data.get('hazard_score_100', 0)

			# Exposure
			e_data = results.get('exposure', {}).get(risk_type, {})
			exposure_scores[f'{risk_type}_exposure_score'] = e_data.get('exposure_score', 0)

			# Vulnerability
			v_data = results.get('vulnerability', {}).get(risk_type, {})
			vulnerability_scores[f'{risk_type}_vulnerability_score'] = v_data.get('vulnerability_score', 0)

			# Physical Risk (Integrated)
			ir_data = results.get('integrated_risk', {}).get(risk_type, {})
			physical_risk_scores[risk_type] = {
				'hazard_score': ir_data.get('h_score', 0),
				'exposure_score': ir_data.get('e_score', 0),
				'vulnerability_score': ir_data.get('v_score', 0),
				'physical_risk_score_100': ir_data.get('integrated_risk_score', 0),
				'risk_level': ir_data.get('risk_level', 'Unknown'),
				'status': 'completed'
			}

			# AAL
			aal_data = results.get('aal_scaled', {}).get(risk_type, {})
			aal_values[f'{risk_type}_aal'] = {
				'base_aal': aal_data.get('base_aal', 0),
				'final_aal_percentage': aal_data.get('final_aal', 0),
				'status': 'completed'
			}

			print(f"  - {risk_type}: "
			      f"H={ir_data.get('h_score', 0):.2f}, "
			      f"E={ir_data.get('e_score', 0):.2f}, "
			      f"V={ir_data.get('v_score', 0):.2f}, "
			      f"Risk={ir_data.get('integrated_risk_score', 0):.2f}, "
			      f"AAL={aal_data.get('final_aal', 0):.4f}%")

		# Summary 정보
		summary = results.get('summary', {})
		print(f"  - 평균 통합 리스크: {summary.get('average_integrated_risk', 0):.2f}")
		print(f"  - 총 AAL: {summary.get('total_final_aal', 0):.4f}%")

		# Vulnerability 분석 결과 (하위 호환성)
		vulnerability_analysis = {
			'vulnerability_scores': vulnerability_scores,
			'status': 'completed'
		}

		# AAL 분석 결과 (하위 호환성)
		aal_analysis = {
			'aal_scaled_results': aal_values,
			'status': 'completed',
			'db_site_id': results.get('site_id')
		}

		# Step 5: State 업데이트 반환
		return {
			'hazard_scores': hazard_scores,
			'exposure_scores': exposure_scores,
			'vulnerability_scores': vulnerability_scores,
			'vulnerability_analysis': vulnerability_analysis,
			'physical_risk_scores': physical_risk_scores,
			'physical_score_status': 'completed',
			'aal_values': aal_values,
			'aal_analysis': aal_analysis,
			'aal_status': 'completed',
			'risk_assessment_summary': summary,
			'current_step': 'impact_analysis',
			'logs': [
				f'DB에서 리스크 결과 조회 완료 (site_id={results.get("site_id")})',
				f'9개 물리적 리스크 분석 완료',
				f'평균 Hazard: {summary.get("average_hazard", 0):.2f}',
				f'평균 Exposure: {summary.get("average_exposure", 0):.2f}',
				f'평균 Vulnerability: {summary.get("average_vulnerability", 0):.2f}',
				f'평균 통합 리스크: {summary.get("average_integrated_risk", 0):.2f}',
				f'총 AAL: {summary.get("total_final_aal", 0):.4f}%',
				f'최고 리스크: {summary.get("highest_integrated_risk", {}).get("risk_type", "N/A")}'
			]
		}

	except Exception as e:
		print(f"[Node 3] 오류: {str(e)}")
		import traceback
		traceback.print_exc()
		return {
			'physical_score_status': 'failed',
			'aal_status': 'failed',
			'errors': [f'DB 결과 조회 오류: {str(e)}']
		}


# ========== Node 4: 리스크 통합 (물리적 리스크 + AAL 결과 통합) ==========
@traceable(name="risk_integration_node", tags=["workflow", "node", "integration"])
def risk_integration_node(state: SuperAgentState, config: Any) -> Dict:
	"""
	리스크 통합 노드
	물리적 리스크 점수(H×E×V)와 AAL 분석 결과를 통합

	Args:
		state: 현재 워크플로우 상태
		config: 설정 객체

	Returns:
		업데이트된 상태 딕셔너리
	"""
	print("[Node 4] 리스크 통합 시작 (물리적 리스크 + AAL)...")

	try:
		physical_risk_scores = state.get('physical_risk_scores', {})
		aal_analysis = state.get('aal_analysis', {})

		# 통합 리스크 분석 결과
		integrated_risks = {}

		for risk_type in physical_risk_scores.keys():
			physical_data = physical_risk_scores.get(risk_type, {})
			aal_data = aal_analysis.get(risk_type, {})

			integrated_risks[risk_type] = {
				'physical_risk': physical_data,
				'aal_analysis': aal_data,
				'combined_score': (
					physical_data.get('physical_risk_score_100', 0) * 0.5 +
					(aal_data.get('final_aal_percentage', 0) * 10) * 0.5  # AAL을 100점 스케일로 변환
				)
			}

			print(f"  - {risk_type}: 물리적={physical_data.get('physical_risk_score_100', 0):.2f}, "
			      f"AAL={aal_data.get('final_aal_percentage', 0):.2f}%, "
			      f"통합점수={integrated_risks[risk_type]['combined_score']:.2f}")

		return {
			'integrated_risks': integrated_risks,
			'integration_status': 'completed',
			'current_step': 'report_template',
			'logs': ['리스크 통합 완료 (물리적 리스크 + AAL)']
		}

	except Exception as e:
		print(f"[Node 4] 오류: {str(e)}")
		return {
			'integration_status': 'failed',
			'errors': [f'리스크 통합 오류: {str(e)}']
		}


# ========== Node 5: 기존 보고서 참고 및 템플릿 형성 (ReportAnalysisAgent) ==========
@traceable(name="report_template_node", tags=["workflow", "node", "report", "template"])
def report_template_node(state: SuperAgentState, config: Any) -> Dict:
	"""
	기존 보고서 참고 및 템플릿 형성 노드
	ReportAnalysisAgent를 사용하여 report_profile 생성

	Args:
		state: 현재 워크플로우 상태
		config: 설정 객체

	Returns:
		업데이트된 상태 딕셔너리
	"""
	print("[Node 5] 리포트 템플릿 생성 시작 (ReportAnalysisAgent)...")

	try:
		# LLM Client 초기화
		llm_client = LLMClient()

		# ReportAnalysisAgent 초기화
		analysis_agent = ReportAnalysisAgent(llm_client)

		# State에서 필요한 데이터 추출
		company_name = state.get('company_name', None)
		past_reports = state.get('past_reports', None)

		# 동기 실행 (run_sync 메서드 사용)
		report_profile = analysis_agent.run_sync(
			company_name=company_name,
			past_reports=past_reports
		)

		# report_profile을 report_template으로 저장
		print(f"  [OK] Report profile 생성 완료")
		print(f"    - Tone: {report_profile.get('tone', {}).get('style', 'N/A')}")
		print(f"    - Sections: {len(report_profile.get('section_structure', {}).get('main_sections', []))}")
		print(f"    - Citations: {len(report_profile.get('citations', []))}")

		return {
			'report_template': report_profile,
			'template_status': 'completed',
			# 'current_step' 제거 (병렬 실행 노드이므로)
			'logs': [f'리포트 템플릿 생성 완료 (ReportAnalysisAgent, company={company_name or "default"})']
		}

	except Exception as e:
		print(f"[Node 5] 오류: {str(e)}")
		import traceback
		traceback.print_exc()

		# 오류 발생 시 기본 템플릿 생성
		print("[Node 5] 기본 템플릿으로 fallback...")
		llm_client = LLMClient()
		analysis_agent = ReportAnalysisAgent(llm_client)
		default_profile = analysis_agent._get_default_profile()

		return {
			'report_template': default_profile,
			'template_status': 'completed_with_fallback',
			# 'current_step' 제거 (병렬 실행 노드이므로)
			'errors': [f'템플릿 생성 오류 (fallback 사용): {str(e)}'],
			'logs': ['리포트 템플릿 생성 완료 (기본 템플릿 사용)']
		}


# ========== Node 6: 영향 분석 (ImpactAnalysisAgent) ==========
@traceable(name="impact_analysis_node", tags=["workflow", "node", "impact", "llm"])
def impact_analysis_node(state: SuperAgentState, config: Any) -> Dict:
	"""
	리스크 영향 분석 노드 (v07: 단일/다중 사업장 지원)
	ImpactAnalysisAgent를 사용하여 전력 사용량 기반 구체적 영향 분석

	Args:
		state: 현재 워크플로우 상태
		config: 설정 객체

	Returns:
		업데이트된 상태 딕셔너리
	"""
	retry_count = state.get('retry_count', 0)
	validation_feedback = state.get('validation_feedback', [])

	# 다중 사업장 모드 확인
	site_ids = state.get('site_ids', [])
	is_multi_site = site_ids and len(site_ids) > 1

	if retry_count > 0:
		mode_str = "다중 사업장" if is_multi_site else "단일 사업장"
		print(f"[Node 6] 영향 분석 재실행 ({mode_str}, 재시도 {retry_count}/3)...")
		if validation_feedback:
			print(f"[Node 6] 검증 피드백 반영: {len(validation_feedback)}개 개선사항")
	else:
		mode_str = f"다중 사업장 ({len(site_ids)}개)" if is_multi_site else "단일 사업장"
		print(f"[Node 6] 영향 분석 시작 ({mode_str}, ImpactAnalysisAgent)...")

	try:
		llm_client = LLMClient()
		impact_agent = ImpactAnalysisAgent(llm_client)
		report_template = state.get('report_template', {})

		# ========== 다중 사업장 모드 ==========
		if is_multi_site:
			sites_data = state.get('sites_data', [])
			if not sites_data:
				raise ValueError("다중 사업장 모드이지만 sites_data가 비어있습니다.")

			impact_analysis = impact_agent.run_aggregated(
				sites_data=sites_data,
				report_profile=report_template
			)

			return {
				'impact_analysis': impact_analysis,
				'impact_status': 'completed',
				'logs': [f'다중 사업장 영향 분석 {"재실행" if retry_count > 0 else ""} 완료 (사업장 수: {len(sites_data)})']
			}

		# ========== 단일 사업장 모드 (기존 로직) ==========
		else:
			# State에서 필요한 데이터 추출 (DB 로드 결과)
			hazard_scores = state.get('hazard_scores', {})
			exposure_scores = state.get('exposure_scores', {})
			vulnerability_scores = state.get('vulnerability_scores', {})
			risk_scores = state.get('risk_scores', {})
			aal_values = state.get('aal_values', {})
			asset_info = state.get('asset_info', {})

			# scenario_input 구조 생성 (단일 시나리오 SSP245 가정)
			scenario_input = {
				"SSP245": {
					"H": hazard_scores,
					"E": exposure_scores,
					"V": vulnerability_scores,
					"risk_scores": risk_scores,
					"power_usage": asset_info.get('power_usage', None)
				}
			}

			tcfd_warnings = []  # 필요시 State에서 추출

			impact_analysis = impact_agent.run(
				scenario_input=scenario_input,
				AAL=aal_values,
				asset_info=asset_info,
				tcfd_warnings=tcfd_warnings,
				report_profile=report_template
			)

			return {
				'impact_analysis': impact_analysis,
				'impact_status': 'completed',
				'logs': [f'단일 사업장 영향 분석 {"재실행" if retry_count > 0 else ""} 완료']
			}

	except Exception as e:
		print(f"[Node 6] 오류: {str(e)}")
		return {
			'impact_status': 'failed',
			'errors': [f'영향 분석 오류: {str(e)}']
		}


# ========== Node 7: 대응 전략 생성 (StrategyGenerationAgent) ==========
@traceable(name="strategy_generation_node", tags=["workflow", "node", "strategy", "llm", "rag"])
def strategy_generation_node(state: SuperAgentState, config: Any) -> Dict:
	"""
	대응 전략 생성 노드 (v07: 단일/다중 사업장 지원)
	StrategyGenerationAgent를 사용하여 LLM + RAG 기반 전략 생성

	Args:
		state: 현재 워크플로우 상태
		config: 설정 객체

	Returns:
		업데이트된 상태 딕셔너리
	"""
	retry_count = state.get('retry_count', 0)
	validation_feedback = state.get('validation_feedback', [])

	# 다중 사업장 모드 확인
	site_ids = state.get('site_ids', [])
	is_multi_site = site_ids and len(site_ids) > 1

	if retry_count > 0:
		mode_str = "다중 사업장" if is_multi_site else "단일 사업장"
		print(f"[Node 7] 대응 전략 재생성 ({mode_str}, 재시도 {retry_count}/3)...")
		if validation_feedback:
			print(f"[Node 7] 검증 피드백 반영: {len(validation_feedback)}개 개선사항")
	else:
		mode_str = f"다중 사업장 ({len(site_ids)}개)" if is_multi_site else "단일 사업장"
		print(f"[Node 7] 대응 전략 생성 시작 ({mode_str}, StrategyGenerationAgent)...")

	try:
		llm_client = LLMClient()
		strategy_agent = StrategyGenerationAgent(llm_client)
		impact_analysis = state.get('impact_analysis', {})
		report_profile = state.get('report_template', {})

		# ========== 다중 사업장 모드 ==========
		if is_multi_site:
			sites_data = state.get('sites_data', [])
			if not sites_data:
				raise ValueError("다중 사업장 모드이지만 sites_data가 비어있습니다.")

			response_strategy = strategy_agent.run_aggregated(
				aggregated_impact=impact_analysis,
				sites_data=sites_data,
				report_profile=report_profile
			)

			return {
				'response_strategy': response_strategy,
				'strategy_status': 'completed',
				'logs': [f'다중 사업장 대응 전략 {"재생성" if retry_count > 0 else "생성"} 완료 (사업장 수: {len(sites_data)})']
			}

		# ========== 단일 사업장 모드 (기존 로직) ==========
		else:
			# impact_analysis를 List[Dict] 형태로 변환
			if isinstance(impact_analysis, dict):
				quant = impact_analysis.get('quantitative_result', {})
				impact_summary = []

				if not isinstance(quant, dict):
					quant = {}

				# 각 시나리오의 top3_risks를 impact_summary로 변환
				for scenario, data in quant.items():
					if scenario == "AAL":
						continue
					if not isinstance(data, dict):
						continue
					top_risks = data.get('top3_risks', [])
					for risk_name, risk_score in top_risks:
						impact_summary.append({
							"risk": risk_name,
							"scenario": scenario,
							"score": risk_score,
							"severity": data.get('severity', {}).get(risk_name, 'medium')
						})
			else:
				impact_summary = []

			facility_profile = {
				'location': state.get('target_location', {}),
				'building_info': state.get('building_info', {}),
				'asset_info': state.get('asset_info', {})
			}

			response_strategy = strategy_agent.run(
				impact_summary=impact_summary,
				facility_profile=facility_profile,
				report_profile=report_profile
			)

			return {
				'response_strategy': response_strategy,
				'strategy_status': 'completed',
				'logs': [f'단일 사업장 대응 전략 {"재생성" if retry_count > 0 else "생성"} 완료']
			}

	except Exception as e:
		print(f"[Node 7] 오류: {str(e)}")
		return {
			'strategy_status': 'failed',
			'errors': [f'대응 전략 생성 오류: {str(e)}']
		}


# ========== Node 8: 리포트 생성 (ReportComposerAgent) ==========
@traceable(name="report_generation_node", tags=["workflow", "node", "report", "composer"])
def report_generation_node(state: SuperAgentState, config: Any) -> Dict:
	"""
	리포트 생성 노드
	ReportComposerAgent를 사용하여 템플릿과 분석 결과 통합

	Args:
		state: 현재 워크플로우 상태
		config: 설정 객체

	Returns:
		업데이트된 상태 딕셔너리
	"""
	print("[Node 8] 리포트 생성 시작 (ReportComposerAgent)...")

	try:
		import asyncio
		from ai_agent.utils import citation_formatter
		from ai_agent.utils import markdown_renderer

		llm_client = LLMClient()

		# 언어 파라미터 가져오기 (기본값: 'en')
		language = state.get('language', 'en')

		# citation_formatter와 markdown_renderer는 모듈이므로 직접 전달
		report_agent = ReportComposerAgent(llm_client, citation_formatter, markdown_renderer, language=language)

		# compose_draft() 메소드의 파라미터에 맞게 변환
		report_profile = state.get('report_template', {})
		impact_summary = state.get('impact_analysis', {})

		# strategies는 List[Dict]로 반환되지만, ReportComposer는 Dict를 기대
		strategies_list = state.get('response_strategy', [])

		# List[Dict]를 Dict로 변환
		# strategies_list = [{"risk": "extreme_heat", "strategy": "...", ...}, ...]
		# → {"extreme_heat": {...}, "extreme_cold": {...}}
		strategies_dict = {}
		if isinstance(strategies_list, list):
			for strategy in strategies_list:
				risk = strategy.get('risk', 'unknown')
				strategies_dict[risk] = strategy
		else:
			strategies_dict = strategies_list  # 이미 Dict인 경우

		template = report_profile  # 동일할 수도 있음

		# async 메소드 호출
		generated_report = asyncio.run(report_agent.compose_draft(
			report_profile=report_profile,
			impact_summary=impact_summary,
			strategies=strategies_dict,
			template=template
		))

		# 키 이름 변환: draft_markdown → markdown, draft_json → json
		# finalization_node에서 'markdown', 'json' 키를 기대함
		normalized_report = {
			'markdown': generated_report.get('draft_markdown', ''),
			'json': generated_report.get('draft_json', {}),
			'citations': generated_report.get('citations', []),
			'status': generated_report.get('status', 'completed')
		}

		return {
			'generated_report': normalized_report,
			'report_status': 'completed',
			# 'current_step' 제거 (순차 실행이지만 병렬 브랜치 내부이므로)
			'logs': ['리포트 생성 완료 (ReportComposerAgent)']
		}

	except Exception as e:
		print(f"[Node 8] 오류: {str(e)}")
		return {
			'report_status': 'failed',
			'errors': [f'리포트 생성 오류: {str(e)}']
		}


# ========== Helper: Building Characteristics Validation ==========
def _validate_building_characteristics(
	building_characteristics: Dict[str, Any],
	physical_risk_scores: Dict[str, Any],
	aal_analysis: Dict[str, Any]
) -> Dict[str, Any]:
	"""
	건물 특징 분석 검증 헬퍼 함수

	검증 항목:
	1. 분석 완전성: 필수 섹션 존재 여부
	2. ModelOps 결과 일관성: Physical Risk Score 및 AAL 데이터와의 정합성
	3. 분석 품질: 종합 분석, 주요 발견사항, 리스크 해석 존재 여부

	Args:
		building_characteristics: 건물 특징 분석 결과
		physical_risk_scores: 물리적 리스크 점수 (ModelOps 계산)
		aal_analysis: AAL 분석 결과 (ModelOps 계산)

	Returns:
		검증 결과 딕셔너리
			- passed: 검증 통과 여부 (bool)
			- score: 검증 점수 (0.0 ~ 1.0)
			- issues: 발견된 이슈 리스트
			- recommendations: 개선 권장사항
	"""
	issues = []
	score = 1.0
	recommendations = []

	# 1. 존재 여부 확인
	if not building_characteristics:
		return {
			'passed': False,
			'score': 0.0,
			'issues': [{'type': 'structure', 'description': 'Building Characteristics 분석 결과가 없습니다.'}],
			'recommendations': ['Building Characteristics Agent를 실행하여 건물 특징 분석을 수행하세요.']
		}

	# 2. 분석 상태 확인
	analysis_status = building_characteristics.get('analysis_status', 'unknown')
	if analysis_status != 'completed':
		issues.append({
			'type': 'structure',
			'description': f'Building Characteristics 분석이 완료되지 않았습니다 (status: {analysis_status})'
		})
		score -= 0.3
		recommendations.append('Building Characteristics 분석을 완료하세요.')

	# 3. 종합 분석 (comprehensive_analysis) 존재 여부
	comprehensive = building_characteristics.get('comprehensive_analysis', {})

	# comprehensive가 문자열인 경우 방어 처리
	if isinstance(comprehensive, str):
		comprehensive = {}

	if not comprehensive:
		issues.append({
			'type': 'completeness',
			'description': 'comprehensive_analysis 섹션이 누락되었습니다.'
		})
		score -= 0.2
		recommendations.append('종합 분석(comprehensive_analysis)을 추가하세요.')
	else:
		# 종합 분석 내 필수 필드 확인
		required_fields = ['summary', 'key_findings', 'risk_interpretation']
		for field in required_fields:
			if not comprehensive.get(field):
				issues.append({
					'type': 'completeness',
					'description': f'comprehensive_analysis.{field} 필드가 누락되었습니다.'
				})
				score -= 0.1
				recommendations.append(f'종합 분석의 {field}를 추가하세요.')

	# 4. ModelOps 결과와의 일관성 확인
	# Physical Risk Scores와 Building Characteristics가 동일한 리스크 타입을 다루는지 확인
	bc_risk_types = set()
	for section_key, section_data in building_characteristics.items():
		if isinstance(section_data, dict) and 'risk_type' in section_data:
			bc_risk_types.add(section_data['risk_type'])

	modelops_risk_types = set(physical_risk_scores.keys())

	# 누락된 리스크 타입이 있는지 확인
	missing_risks = modelops_risk_types - bc_risk_types
	if missing_risks and len(missing_risks) > 0:
		issues.append({
			'type': 'consistency',
			'description': f'ModelOps에서 계산된 일부 리스크가 Building Characteristics에 반영되지 않았습니다: {", ".join(missing_risks)}'
		})
		score -= 0.15
		recommendations.append(f'누락된 리스크 타입({", ".join(missing_risks)})에 대한 건물 특징 분석을 추가하세요.')

	# 5. 분석 품질 확인 (텍스트 길이 기반 간단한 품질 체크)
	if comprehensive:
		summary = comprehensive.get('summary', '')
		key_findings = comprehensive.get('key_findings', [])

		# Summary가 너무 짧으면 경고
		if len(summary) < 50:
			issues.append({
				'type': 'quality',
				'description': 'comprehensive_analysis.summary가 너무 짧습니다 (최소 50자 권장).'
			})
			score -= 0.1
			recommendations.append('종합 분석의 요약을 더 상세하게 작성하세요.')

		# Key findings가 비어있으면 경고
		if not key_findings or len(key_findings) == 0:
			issues.append({
				'type': 'quality',
				'description': 'comprehensive_analysis.key_findings가 비어있습니다.'
			})
			score -= 0.1
			recommendations.append('주요 발견사항(key_findings)을 추가하세요.')

	# 6. 최종 검증 통과 여부 결정 (score >= 0.7)
	passed = score >= 0.7

	return {
		'passed': passed,
		'score': max(0.0, score),  # 음수 방지
		'issues': issues,
		'recommendations': recommendations
	}


# ========== Node 9: 검증 ==========
@traceable(name="validation_node", tags=["workflow", "node", "validation"])
def validation_node(state: SuperAgentState, config: Any) -> Dict:
	"""
	검증 노드 (통합 검증)
	생성된 리포트 및 건물 특징 분석의 정확성, 일관성, 완전성 확인

	검증 대상:
	1. Report Validation: 리포트 내용, 구조, TCFD 정합성
	2. Building Characteristics Validation: 건물 특징 분석 완전성, ModelOps 결과와의 일관성

	Args:
		state: 현재 워크플로우 상태
		config: 설정 객체

	Returns:
		업데이트된 상태 딕셔너리
	"""
	retry_count = state.get('retry_count', 0)
	print(f"[Node 9] 통합 검증 시작 (Report + Building Characteristics)... (재시도 {retry_count}/3)")

	try:
		import asyncio
		validator = ValidationAgent()

		# ========== 1. Report Validation ==========
		print("  [1/2] Report Validation...")
		generated_report = state.get('generated_report', {})

		# generated_report가 문자열인 경우 방어 처리
		if isinstance(generated_report, str):
			draft_markdown = generated_report
			draft_json = {}
		else:
			draft_markdown = generated_report.get('markdown', '')
			draft_json = generated_report.get('json', {})
		# 다른 state 값들도 방어 처리
		report_profile = state.get('report_template', {})
		if not isinstance(report_profile, dict):
			report_profile = {}

		impact_summary = state.get('impact_analysis', {})
		if not isinstance(impact_summary, dict):
			impact_summary = {}

		# response_strategy는 List[Dict] 형태로 반환되므로 Dict로 변환 필요
		strategies_list = state.get('response_strategy', [])
		strategies = {}
		if isinstance(strategies_list, list):
			for strategy in strategies_list:
				risk = strategy.get('risk', 'unknown')
				strategies[risk] = strategy
		elif isinstance(strategies_list, dict):
			strategies = strategies_list  # 이미 Dict인 경우
		else:
			strategies = {}

		# Call async validate method for Report
		report_validation = asyncio.run(validator.validate(
			draft_markdown=draft_markdown,
			draft_json=draft_json,
			report_profile=report_profile,
			impact_summary=impact_summary,
			strategies=strategies,
			citations=None
		))

		# ========== 2. Building Characteristics Validation ==========
		print("  [2/2] Building Characteristics Validation...")
		building_characteristics = state.get('building_characteristics', {})
		bc_validation = _validate_building_characteristics(
			building_characteristics=building_characteristics,
			physical_risk_scores=state.get('physical_risk_scores', {}),
			aal_analysis=state.get('aal_analysis', {})
		)

		# ========== 3. 통합 검증 결과 ==========
		report_passed = report_validation.get('passed', False)
		bc_passed = bc_validation.get('passed', False)
		overall_passed = report_passed and bc_passed

		# 통합 validation_result 생성
		validation_result = {
			'report_validation': report_validation,
			'building_characteristics_validation': bc_validation,
			'passed': overall_passed,
			'report_score': report_validation.get('score', 0.0),
			'bc_score': bc_validation.get('score', 0.0),
			'overall_score': (report_validation.get('score', 0.0) + bc_validation.get('score', 0.0)) / 2,
			'issues_found': report_validation.get('issues', []) + bc_validation.get('issues', []),
			'improvement_suggestions': report_validation.get('recommendations', []) + bc_validation.get('recommendations', [])
		}

		if overall_passed:
			print(f"  [OK] 통합 검증 통과 (Report: {report_validation.get('score', 0):.2f}, BC: {bc_validation.get('score', 0):.2f})")
			return {
				'validation_result': validation_result,
				'validation_status': 'passed',
				'current_step': 'finalization',
				'logs': ['통합 검증 통과 (Report + Building Characteristics)']
			}
		else:
			# 검증 실패 - retry_count 증가
			new_retry_count = retry_count + 1
			failed_parts = []
			if not report_passed:
				failed_parts.append('Report')
			if not bc_passed:
				failed_parts.append('Building Characteristics')

			print(f"  [FAIL] 검증 실패: {', '.join(failed_parts)}")
			return {
				'validation_result': validation_result,
				'validation_status': 'failed',
				'validation_feedback': validation_result.get('improvement_suggestions', []),
				'retry_count': new_retry_count,
				'logs': [f'검증 실패 ({", ".join(failed_parts)}): {len(validation_result.get("issues_found", []))}개 이슈 발견']
			}

	except Exception as e:
		print(f"[Node 9] 오류: {str(e)}")
		import traceback
		traceback.print_exc()
		return {
			'validation_status': 'error',
			'errors': [f'검증 오류: {str(e)}']
		}


# ========== Node 9a: Refiner (검증 실패 시 자동 보완) ==========
@traceable(name="refiner_node", tags=["workflow", "node", "refiner", "llm"])
def refiner_node(state: SuperAgentState, config: Any) -> Dict:
	"""
	Refiner 노드
	검증 실패 시 Draft Report를 자동으로 보완

	Args:
		state: 현재 워크플로우 상태
		config: 설정 객체

	Returns:
		업데이트된 상태 딕셔너리
	"""
	refiner_loop_count = state.get('refiner_loop_count', 0) + 1
	print(f"[Node 9a] Refiner 시작... (Loop {refiner_loop_count}/3)")

	try:
		# LLM Client 초기화
		llm_client = LLMClient()

		# RefinerAgent 초기화
		refiner = RefinerAgent(llm_client)

		# State에서 필요한 데이터 추출
		generated_report = state.get('generated_report', {})
		validation_result = state.get('validation_result', {})

		# Draft Markdown/JSON 추출
		draft_markdown = generated_report.get('markdown', '')
		draft_json = generated_report.get('json', {})

		# Markdown이 없으면 JSON에서 생성 시도
		if not draft_markdown and draft_json:
			draft_markdown = "# Climate Risk Report\n\n(보고서 내용)"

		# RefinerAgent 동기 실행
		refine_result = refiner.refine_sync(
			draft_markdown=draft_markdown,
			draft_json=draft_json,
			validation_results=validation_result
		)

		# 개선된 보고서 구성
		refined_report = {
			'markdown': refine_result.get('updated_markdown', draft_markdown),
			'json': refine_result.get('updated_json', draft_json),
			'status': refine_result.get('status', 'completed')
		}

		applied_fixes = refine_result.get('applied_fixes', [])

		print(f"  [OK] Refiner 완료")
		print(f"    - 적용된 수정: {len(applied_fixes)}개")
		for fix in applied_fixes[:3]:  # 처음 3개만 출력
			print(f"      * {fix}")

		# 개선된 보고서를 generated_report로 교체 (재검증용)
		return {
			'generated_report': refined_report,
			'refined_report': refined_report,
			'applied_fixes': applied_fixes,
			'refiner_status': 'completed',
			'refiner_loop_count': refiner_loop_count,
			'current_step': 'validation',  # 다시 검증으로
			'logs': [f'Refiner 완료 (Loop {refiner_loop_count}, {len(applied_fixes)}개 수정)']
		}

	except Exception as e:
		print(f"[Node 9a] 오류: {str(e)}")
		import traceback
		traceback.print_exc()

		return {
			'refiner_status': 'failed',
			'refiner_loop_count': refiner_loop_count,
			'errors': [f'Refiner 오류: {str(e)}'],
			'current_step': 'finalization',  # 오류 시 최종화로
			'logs': ['Refiner 실패 - 최종화로 진행']
		}


# ========== Node 10: 최종 리포트 산출 (FinalizerNode) ==========
@traceable(name="finalization_node", tags=["workflow", "node", "finalization"])
def finalization_node(state: SuperAgentState, config: Any) -> Dict:
	"""
	최종 리포트 산출 노드
	FinalizerNode를 사용하여 Markdown/JSON/PDF 파일 저장 및 DB 로깅

	Args:
		state: 현재 워크플로우 상태
		config: 설정 객체

	Returns:
		업데이트된 상태 딕셔너리
	"""
	print("[Node 10] 최종 리포트 확정 및 파일 저장 (FinalizerNode)...")

	# ========== IDEMPOTENCY GUARD ==========
	# 이미 finalization이 완료된 경우 스킵 (중복 실행 방지)
	existing_output_paths = state.get('output_paths', {})
	if existing_output_paths and existing_output_paths.get('markdown'):
		print("  [SKIP] Finalization already completed")
		print(f"    Existing output: {existing_output_paths.get('markdown')}")
		return {
			'final_status': 'already_completed',
			'logs': ['Finalization 중복 호출 방지 - 이미 완료됨']
		}
	# ========================================

	try:
		# FinalizerNode 초기화
		finalizer = FinalizerNode()

		# 최종 보고서 추출 (Refiner를 거쳤으면 refined_report, 아니면 generated_report)
		final_report = state.get('refined_report') or state.get('generated_report', {})

		# Markdown/JSON 추출
		refined_markdown = final_report.get('markdown', '')
		refined_json = final_report.get('json', {})

		# Markdown이 없으면 기본 구조 생성
		if not refined_markdown:
			refined_markdown = "# Climate Physical Risk Report\n\n검증을 통과한 최종 보고서입니다.\n\n"
			refined_markdown += f"Generated: {state.get('current_step', 'N/A')}\n"

		# Citations 추출
		citations_final = []
		if isinstance(refined_json, dict):
			citations_final = refined_json.get('citations', [])

		# 추가로 report_template의 citations도 포함
		report_template = state.get('report_template', {})
		if isinstance(report_template, dict) and 'citations' in report_template:
			citations_final.extend(report_template.get('citations', []))

		# Metadata 구성
		metadata = {
			'report_name': 'physical_risk_analysis',
			'version': 'v1.0',
			'facility': state.get('target_location', {}).get('name', 'facility'),
			'company_name': state.get('company_name', 'Unknown Company'),
			'generated_at': 'auto',
			'validation_passed': state.get('validation_status') == 'passed',
			'refiner_loops': state.get('refiner_loop_count', 0)
		}

		# Validation Result 추출
		validation_result = state.get('validation_result', {})

		# FinalizerInput 구성 (딕셔너리로 전달)
		finalizer_input = {
			'refined_markdown': refined_markdown,
			'refined_json': refined_json,
			'citations_final': citations_final,
			'validation_result': validation_result,
			'metadata': metadata,
			'export_formats': ['md', 'json', 'pdf']
		}

		# FinalizerNode 실행
		from ai_agent.agents.report_generation.finalizer_node_7 import FinalizerInput
		finalizer_input_obj = FinalizerInput(**finalizer_input)
		finalizer_output = finalizer.run(finalizer_input_obj)

		# 출력 경로 저장
		output_paths = {
			'markdown': finalizer_output.md_path,
			'json': finalizer_output.json_path,
			'pdf': finalizer_output.pdf_path
		}

		print(f"  [OK] 파일 저장 완료")
		print(f"    - Markdown: {finalizer_output.md_path}")
		print(f"    - JSON: {finalizer_output.json_path}")
		if finalizer_output.pdf_path:
			print(f"    - PDF: {finalizer_output.pdf_path}")
		if finalizer_output.db_log_id:
			print(f"    - DB Log ID: {finalizer_output.db_log_id}")

		return {
			'final_report': final_report,
			'output_paths': output_paths,
			'final_status': 'completed',
			'workflow_status': 'completed',
			'current_step': 'done',
			'logs': [f'최종 리포트 확정 완료 (Markdown: {finalizer_output.md_path})']
		}

	except Exception as e:
		print(f"[Node 10] 오류: {str(e)}")
		import traceback
		traceback.print_exc()

		# 오류 시에도 최소한의 정보 저장
		final_report = state.get('refined_report') or state.get('generated_report', {})

		return {
			'final_report': final_report,
			'final_status': 'completed_with_errors',
			'workflow_status': 'completed',
			'current_step': 'done',
			'errors': [f'Finalizer 오류: {str(e)}'],
			'logs': ['최종 리포트 확정 (오류 발생, 파일 저장 실패)']
		}


# ========== Node 2 (NEW): 건물 특징 분석 (병렬 독립 실행) ==========
@traceable(name="building_characteristics_node", tags=["workflow", "node", "building-analysis"])
def building_characteristics_node(state: SuperAgentState, config: Any) -> Dict:
	"""
	건물 특징 분석 노드 (Node 5 이후 병렬 실행)

	Physical Risk Score와 AAL 결과를 받아서 건물 특징을 분석
	LLM 기반 정성적 분석 제공
	리포트 체인(6-11)과 완전히 독립적으로 실행

	Args:
		state: 현재 워크플로우 상태
		config: 설정 객체

	Returns:
		업데이트된 상태 딕셔너리
	"""
	print("[Node 2] 건물 특징 분석 시작 (독립 병렬 실행)...")

	try:
		# 1. 필요한 데이터 추출
		building_info = state.get('building_info', {})
		physical_risk_results = state.get('physical_risk_results', {})
		aal_results = state.get('aal_results', {})
		integrated_risk = state.get('integrated_risk', {})

		# 2. Additional data guideline 확인
		additional_data_guidelines = state.get('additional_data_guidelines', {})
		guideline = additional_data_guidelines.get('building_characteristics', {})

		# 3. LLM 클라이언트 초기화
		llm_client = LLMClient()

		# 4. Building Characteristics Agent 실행
		agent = BuildingCharacteristicsAgent(llm_client=llm_client)

		analysis_result = agent.analyze(
			building_info=building_info,
			physical_risk_results=physical_risk_results,
			aal_results=aal_results,
			integrated_risk=integrated_risk,
			additional_data_guideline=guideline if guideline.get('relevance', 0.0) >= 0.4 else None
		)

		print(f"  [OK] 건물 특징 분석 완료")
		print(f"    - 구조적 등급: {analysis_result['structural_features'].get('structural_grade', 'Unknown')}")
		print(f"    - 취약 요인: {len(analysis_result.get('vulnerability_factors', []))}개")
		print(f"    - 회복력 요인: {len(analysis_result.get('resilience_factors', []))}개")

		if guideline.get('relevance', 0.0) >= 0.4:
			print(f"    - 가이드라인 적용됨 (relevance: {guideline.get('relevance', 0.0):.2f})")

		return {
			'building_characteristics': analysis_result,
			'building_analysis_status': 'completed',
			'logs': [
				'건물 특징 분석 완료 (독립 브랜치)',
				f'구조적 등급: {analysis_result["structural_features"].get("structural_grade", "Unknown")}'
			]
		}

	except Exception as e:
		print(f"[Node 2] 오류: {str(e)}")
		import traceback
		traceback.print_exc()

		return {
			'building_analysis_status': 'failed',
			'errors': [f'건물 특징 분석 오류: {str(e)}']
		}
