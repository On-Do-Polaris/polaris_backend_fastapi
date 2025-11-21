'''
파일명: nodes.py
최종 수정일: 2025-11-21
버전: v03
파일 개요: LangGraph 워크플로우 노드 함수 정의 (Super Agent 계층적 구조용)
변경 이력:
	- 2025-11-11: v01 - Super Agent 계층적 구조로 전면 개편, 10개 주요 노드 재구성
	- 2025-11-11: v02 - 노드 순서 변경 (Node 3: AAL 분석, Node 4: 물리적 리스크 점수 100점 스케일)
	- 2025-11-21: v03 - Scratch Space 기반 데이터 관리 적용
'''
from typing import Dict, Any
import numpy as np
from .state import SuperAgentState

from ..utils.llm_client import LLMClient
from ..utils.rag_engine import RAGEngine
from ..utils.scratch_manager import ScratchSpaceManager

from ..agents import (
	DataCollectionAgent,
	VulnerabilityAnalysisAgent,
	ReportTemplateAgent,
	StrategyGenerationAgent,
	ReportGenerationAgent,
	ValidationAgent,
	ImpactAnalysisAgent,
	ExtremeHeatScoreAgent,
	ExtremeColdScoreAgent,
	WildfireScoreAgent,
	DroughtScoreAgent,
	WaterStressScoreAgent,
	SeaLevelRiseScoreAgent,
	RiverFloodScoreAgent,
	UrbanFloodScoreAgent,
	TyphoonScoreAgent,
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

# Scratch Space Manager 초기화 (TTL 4시간)
scratch_manager = ScratchSpaceManager(base_path="./scratch", default_ttl_hours=4)


# ========== Node 1: 데이터 수집 (Scratch Space 기반) ==========
def data_collection_node(state: SuperAgentState, config: Any) -> Dict:
	"""
	데이터 수집 노드 (Scratch Space 기반)
	대상 위치의 기후 데이터를 수집하고 Scratch Space에 저장

	Args:
		state: 현재 워크플로우 상태
		config: 설정 객체

	Returns:
		업데이트된 상태 딕셔너리
	"""
	print("[Node 1] 데이터 수집 시작 (Scratch Space 기반)...")

	try:
		# 1. Scratch Space 세션 생성
		session_id = scratch_manager.create_session(
			ttl_hours=4,
			metadata={
				"location": state['target_location'],
				"analysis_type": "climate_risk"
			}
		)
		print(f"  ✓ Scratch session created: {session_id}")

		# 2. 데이터 수집
		agent = DataCollectionAgent(config)
		collected_data = agent.collect(
			state['target_location'],
			state.get('analysis_params', {})
		)

		# 3. 원본 데이터 → Scratch Space 저장
		scratch_manager.save_data(
			session_id,
			"climate_raw.json",
			collected_data,
			format="json"
		)
		print(f"  ✓ Raw data saved to scratch space")

		# 4. 요약 통계 계산
		climate_data = collected_data.get('climate_data', {})
		climate_summary = {
			"location": collected_data.get('location', {}),
			"data_years": list(range(2025, 2051)),
			"ssp_scenarios": ["ssp1-2.6", "ssp2-4.5", "ssp3-7.0", "ssp5-8.5"],
			"statistics": {
				"wsdi_mean": float(np.mean(climate_data.get('wsdi', [0]))),
				"wsdi_max": float(np.max(climate_data.get('wsdi', [0]))),
				"wsdi_min": float(np.min(climate_data.get('wsdi', [0]))),
			}
		}

		# 5. State에는 참조와 요약만
		return {
			'scratch_session_id': session_id,
			'climate_summary': climate_summary,
			'data_collection_status': 'completed',
			'current_step': 'vulnerability_analysis',
			'logs': [
				'데이터 수집 완료',
				f'Scratch session: {session_id}',
				f'TTL: 4 hours'
			]
		}

	except Exception as e:
		print(f"[Node 1] 오류: {str(e)}")
		return {
			'data_collection_status': 'failed',
			'errors': [f'데이터 수집 오류: {str(e)}']
		}


# ========== Node 2: 취약성 분석 ==========
def vulnerability_analysis_node(state: SuperAgentState, config: Any) -> Dict:
	"""
	취약성 분석 노드
	건물 연식, 내진 설계, 소방차 진입 가능성 분석

	Args:
		state: 현재 워크플로우 상태
		config: 설정 객체

	Returns:
		업데이트된 상태 딕셔너리
	"""
	print("[Node 2] 취약성 분석 시작...")

	try:
		agent = VulnerabilityAnalysisAgent()
		vulnerability_result = agent.analyze_vulnerability(
			state.get('building_info', {}),
			state.get('target_location', {})
		)

		# 9개 리스크 선정
		selected_risks = [
			'extreme_heat',
			'extreme_cold',
			'wildfire',
			'drought',
			'water_stress',
			'sea_level_rise',
			'river_flood',
			'urban_flood',
			'typhoon'
		]

		return {
			'vulnerability_analysis': vulnerability_result,
			'vulnerability_status': 'completed',
			'selected_risks': selected_risks,
			'current_step': 'physical_risk_analysis',
			'logs': ['취약성 분석 완료', f'{len(selected_risks)}개 리스크 선정']
		}

	except Exception as e:
		print(f"[Node 2] 오류: {str(e)}")
		return {
			'vulnerability_status': 'failed',
			'errors': [f'취약성 분석 오류: {str(e)}']
		}


# ========== Node 3: 연평균 재무 손실률 분석 (9개 Sub Agent 병렬 실행) ==========
def aal_analysis_node(state: SuperAgentState, config: Any) -> Dict:
	"""
	연평균 재무 손실률 (AAL) 분석 노드
	9개 리스크별로 P(H) x 손상률 x (1-보험보전율) 기반 AAL(%) 계산 (병렬 실행)

	Args:
		state: 현재 워크플로우 상태
		config: 설정 객체

	Returns:
		업데이트된 상태 딕셔너리
	"""
	print("[Node 3] 연평균 재무 손실률 (AAL) 분석 시작...")

	try:
		# 9개 AAL Agent 인스턴스 생성
		agents = {
			'extreme_heat': ExtremeHeatAALAgent(),
			'extreme_cold': ExtremeColdAALAgent(),
			'wildfire': WildfireAALAgent(),
			'drought': DroughtAALAgent(),
			'water_stress': WaterStressAALAgent(),
			'sea_level_rise': SeaLevelRiseAALAgent(),
			'river_flood': RiverFloodAALAgent(),
			'urban_flood': UrbanFloodAALAgent(),
			'typhoon': TyphoonAALAgent()
		}

		# Scratch Space에서 원본 데이터 로드
		session_id = state.get('scratch_session_id')
		collected_data = scratch_manager.load_data(session_id, "climate_raw.json", format="json")
		asset_info = state.get('asset_info', {})

		aal_analysis = {}

		# 각 리스크별로 AAL 계산 (physical_risk_score 없이 독립 계산)
		for risk_type, agent in agents.items():
			result = agent.analyze_aal(
				collected_data,
				physical_risk_score=0.5,  # 더미 값 (실제로는 사용 안 함)
				asset_info=asset_info
			)
			aal_analysis[risk_type] = result
			print(f"  - {risk_type}: AAL={result.get('aal_percentage', 0):.4f}%")

		return {
			'aal_analysis': aal_analysis,
			'aal_status': 'completed',
			'current_step': 'physical_risk_score',
			'logs': ['연평균 재무 손실률 (AAL) 분석 완료 (9개)']
		}

	except Exception as e:
		print(f"[Node 3] 오류: {str(e)}")
		return {
			'aal_status': 'failed',
			'errors': [f'AAL 분석 오류: {str(e)}']
		}


# ========== Node 3a: 물리적 리스크 종합 점수 산출 (9개 Sub Agent H×E×V 기반) ==========
def physical_risk_score_node(state: SuperAgentState, config: Any) -> Dict:
	"""
	물리적 리스크 종합 점수 산출 노드 (병렬 실행)
	9개 Physical Risk Score Sub Agent를 사용하여 H×E×V 기반 리스크 점수 계산

	Args:
		state: 현재 워크플로우 상태
		config: 설정 객체

	Returns:
		업데이트된 상태 딕셔너리
	"""
	print("[Node 3a] 물리적 리스크 종합 점수 산출 시작 (H×E×V 기반)...")

	try:
		# 9개 Physical Risk Score Agent 인스턴스 생성
		agents = {
			'extreme_heat': ExtremeHeatScoreAgent(),
			'extreme_cold': ExtremeColdScoreAgent(),
			'wildfire': WildfireScoreAgent(),
			'drought': DroughtScoreAgent(),
			'water_stress': WaterStressScoreAgent(),
			'sea_level_rise': SeaLevelRiseScoreAgent(),
			'river_flood': RiverFloodScoreAgent(),
			'urban_flood': UrbanFloodScoreAgent(),
			'typhoon': TyphoonScoreAgent()
		}

		# Scratch Space에서 원본 데이터 로드
		session_id = state.get('scratch_session_id')
		collected_data = scratch_manager.load_data(session_id, "climate_raw.json", format="json")
		vulnerability_analysis = state.get('vulnerability_analysis', {})
		asset_info = state.get('asset_info', {})

		physical_risk_scores = {}

		# 각 리스크별로 H×E×V 계산
		for risk_type, agent in agents.items():
			result = agent.calculate_physical_risk_score(
				collected_data=collected_data,
				vulnerability_analysis=vulnerability_analysis,
				asset_info=asset_info
			)

			if result.get('status') == 'completed':
				physical_risk_scores[risk_type] = result

				print(f"  - {risk_type}: H={result.get('hazard_score', 0):.2f}, "
				      f"E={result.get('exposure_score', 0):.2f}, "
				      f"V={result.get('vulnerability_score', 0):.2f}, "
				      f"Score={result.get('physical_risk_score_100', 0):.2f}/100")
			else:
				print(f"  - {risk_type}: 계산 실패 - {result.get('error', 'Unknown error')}")

		return {
			'physical_risk_scores': physical_risk_scores,
			'physical_score_status': 'completed',
			'current_step': 'risk_integration',
			'logs': ['물리적 리스크 종합 점수 산출 완료 (H×E×V 기반)']
		}

	except Exception as e:
		print(f"[Node 3a] 오류: {str(e)}")
		return {
			'physical_score_status': 'failed',
			'errors': [f'물리적 리스크 점수 산출 오류: {str(e)}']
		}


# ========== Node 4: 리스크 통합 (물리적 리스크 + AAL 결과 통합) ==========
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
					(aal_data.get('aal_percentage', 0) * 10) * 0.5  # AAL을 100점 스케일로 변환
				)
			}

			print(f"  - {risk_type}: 물리적={physical_data.get('physical_risk_score_100', 0):.2f}, "
			      f"AAL={aal_data.get('aal_percentage', 0):.2f}%, "
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


# ========== Node 5: 기존 보고서 참고 및 템플릿 형성 (ReportTemplateAgent) ==========
def report_template_node(state: SuperAgentState, config: Any) -> Dict:
	"""
	기존 보고서 참고 및 템플릿 형성 노드
	ReportTemplateAgent를 사용하여 RAG 기반 템플릿 생성

	Args:
		state: 현재 워크플로우 상태
		config: 설정 객체

	Returns:
		업데이트된 상태 딕셔너리
	"""
	print("[Node 5] 리포트 템플릿 생성 시작 (ReportTemplateAgent)...")

	try:
		rag_engine = RAGEngine()
		template_agent = ReportTemplateAgent(rag_engine)

		report_template = template_agent.generate_template(
			target_location=state.get('target_location', {}),
			vulnerability_analysis=state.get('vulnerability_analysis', {}),
			aal_analysis=state.get('aal_analysis', {}),
			physical_risk_scores=state.get('physical_risk_scores', {})
		)

		return {
			'report_template': report_template,
			'template_status': 'completed',
			'current_step': 'impact_analysis',
			'logs': ['리포트 템플릿 생성 완료 (ReportTemplateAgent)']
		}

	except Exception as e:
		print(f"[Node 5] 오류: {str(e)}")
		return {
			'template_status': 'failed',
			'errors': [f'템플릿 생성 오류: {str(e)}']
		}


# ========== Node 6: 영향 분석 (ImpactAnalysisAgent) ==========
def impact_analysis_node(state: SuperAgentState, config: Any) -> Dict:
	"""
	리스크 영향 분석 노드
	ImpactAnalysisAgent를 사용하여 전력 사용량 기반 구체적 영향 분석

	Args:
		state: 현재 워크플로우 상태
		config: 설정 객체

	Returns:
		업데이트된 상태 딕셔너리
	"""
	retry_count = state.get('retry_count', 0)
	validation_feedback = state.get('validation_feedback', [])

	if retry_count > 0:
		print(f"[Node 6] 영향 분석 재실행 (재시도 {retry_count}/3)...")
		if validation_feedback:
			print(f"[Node 6] 검증 피드백 반영: {len(validation_feedback)}개 개선사항")
	else:
		print("[Node 6] 영향 분석 시작 (ImpactAnalysisAgent)...")

	try:
		impact_agent = ImpactAnalysisAgent()

		impact_analysis = impact_agent.analyze_impact(
			physical_risk_scores=state.get('physical_risk_scores', {}),
			aal_analysis=state.get('aal_analysis', {}),
			collected_data=state.get('collected_data', {}),
			vulnerability_analysis=state.get('vulnerability_analysis', {}),
			validation_feedback=validation_feedback  # 피드백 전달
		)

		return {
			'impact_analysis': impact_analysis,
			'impact_status': 'completed',
			'current_step': 'strategy_generation',
			'logs': [f'영향 분석 {"재실행" if retry_count > 0 else ""} 완료 (ImpactAnalysisAgent)']
		}

	except Exception as e:
		print(f"[Node 6] 오류: {str(e)}")
		return {
			'impact_status': 'failed',
			'errors': [f'영향 분석 오류: {str(e)}']
		}


# ========== Node 7: 대응 전략 생성 (StrategyGenerationAgent) ==========
def strategy_generation_node(state: SuperAgentState, config: Any) -> Dict:
	"""
	대응 전략 생성 노드
	StrategyGenerationAgent를 사용하여 LLM + RAG 기반 전략 생성

	Args:
		state: 현재 워크플로우 상태
		config: 설정 객체

	Returns:
		업데이트된 상태 딕셔너리
	"""
	retry_count = state.get('retry_count', 0)
	validation_feedback = state.get('validation_feedback', [])

	if retry_count > 0:
		print(f"[Node 7] 대응 전략 재생성 (재시도 {retry_count}/3)...")
		if validation_feedback:
			print(f"[Node 7] 검증 피드백 반영: {len(validation_feedback)}개 개선사항")
	else:
		print("[Node 7] 대응 전략 생성 시작 (StrategyGenerationAgent)...")

	try:
		llm_client = LLMClient()
		rag_engine = RAGEngine()
		strategy_agent = StrategyGenerationAgent(llm_client, rag_engine)

		response_strategy = strategy_agent.generate_strategy(
			target_location=state.get('target_location', {}),
			vulnerability_analysis=state.get('vulnerability_analysis', {}),
			aal_analysis=state.get('aal_analysis', {}),
			physical_risk_scores=state.get('physical_risk_scores', {}),
			impact_analysis=state.get('impact_analysis', {}),
			report_template=state.get('report_template', {}),
			validation_feedback=validation_feedback  # 피드백 전달
		)

		return {
			'response_strategy': response_strategy,
			'strategy_status': 'completed',
			'current_step': 'report_generation',
			'logs': [f'대응 전략 {"재생성" if retry_count > 0 else "생성"} 완료 (StrategyGenerationAgent)']
		}

	except Exception as e:
		print(f"[Node 7] 오류: {str(e)}")
		return {
			'strategy_status': 'failed',
			'errors': [f'대응 전략 생성 오류: {str(e)}']
		}


# ========== Node 8: 리포트 생성 (ReportGenerationAgent) ==========
def report_generation_node(state: SuperAgentState, config: Any) -> Dict:
	"""
	리포트 생성 노드
	ReportGenerationAgent를 사용하여 템플릿과 분석 결과 통합

	Args:
		state: 현재 워크플로우 상태
		config: 설정 객체

	Returns:
		업데이트된 상태 딕셔너리
	"""
	print("[Node 8] 리포트 생성 시작 (ReportGenerationAgent)...")

	try:
		report_agent = ReportGenerationAgent()

		generated_report = report_agent.generate_report(
			target_location=state.get('target_location', {}),
			building_info=state.get('building_info', {}),
			vulnerability_analysis=state.get('vulnerability_analysis', {}),
			aal_analysis=state.get('aal_analysis', {}),
			physical_risk_scores=state.get('physical_risk_scores', {}),
			impact_analysis=state.get('impact_analysis', {}),
			report_template=state.get('report_template', {}),
			response_strategy=state.get('response_strategy', {})
		)

		return {
			'generated_report': generated_report,
			'report_status': 'completed',
			'current_step': 'validation',
			'logs': ['리포트 생성 완료 (ReportGenerationAgent)']
		}

	except Exception as e:
		print(f"[Node 8] 오류: {str(e)}")
		return {
			'report_status': 'failed',
			'errors': [f'리포트 생성 오류: {str(e)}']
		}


# ========== Node 9: 검증 ==========
def validation_node(state: SuperAgentState, config: Any) -> Dict:
	"""
	검증 노드
	생성된 리포트의 정확성, 일관성, 완전성 확인

	Args:
		state: 현재 워크플로우 상태
		config: 설정 객체

	Returns:
		업데이트된 상태 딕셔너리
	"""
	retry_count = state.get('retry_count', 0)
	print(f"[Node 9] 리포트 검증 시작... (재시도 {retry_count}/3)")

	try:
		validator = ValidationAgent()
		validation_result = validator.validate_report(
			state.get('generated_report', {}),
			state.get('physical_risk_scores', {}),
			state.get('aal_analysis', {}),
			state.get('response_strategy', {}),
			state.get('impact_analysis', {})
		)

		validation_passed = validation_result.get('validation_passed', False)

		if validation_passed:
			return {
				'validation_result': validation_result,
				'validation_status': 'passed',
				'current_step': 'finalization',
				'logs': ['검증 통과']
			}
		else:
			# 검증 실패 - retry_count 증가
			new_retry_count = retry_count + 1

			return {
				'validation_result': validation_result,
				'validation_status': 'failed',
				'validation_feedback': validation_result.get('improvement_suggestions', []),
				'retry_count': new_retry_count,
				'logs': [f'검증 실패: {len(validation_result.get("issues_found", []))}개 이슈 발견']
			}

	except Exception as e:
		print(f"[Node 9] 오류: {str(e)}")
		return {
			'validation_status': 'error',
			'errors': [f'검증 오류: {str(e)}']
		}


# ========== Node 10: 최종 리포트 산출 ==========
def finalization_node(state: SuperAgentState, config: Any) -> Dict:
	"""
	최종 리포트 산출 노드
	검증 통과한 리포트를 최종 확정

	Args:
		state: 현재 워크플로우 상태
		config: 설정 객체

	Returns:
		업데이트된 상태 딕셔너리
	"""
	print("[Node 10] 최종 리포트 확정...")

	return {
		'final_report': state.get('generated_report'),
		'final_status': 'completed',
		'workflow_status': 'completed',
		'current_step': 'done',
		'logs': ['최종 리포트 확정 완료']
	}
