'''
파일명: nodes.py
최종 수정일: 2025-11-11
버전: v02
파일 개요: LangGraph 워크플로우 노드 함수 정의 (Super Agent 계층적 구조용)
변경 이력:
	- 2025-11-11: v01 - Super Agent 계층적 구조로 전면 개편, 10개 주요 노드 재구성
	- 2025-11-11: v02 - 노드 순서 변경 (Node 3: AAL 분석, Node 4: 물리적 리스크 점수 100점 스케일)
'''
from typing import Dict, Any
from workflow.state import SuperAgentState

from utils.llm_client import LLMClient
from utils.rag_engine import RAGEngine

from agents import (
	DataCollectionAgent,
	VulnerabilityAnalysisAgent,
	ReportTemplateAgent,
	StrategyGenerationAgent,
	ReportGenerationAgent,
	ValidationAgent,
	HighTemperatureScoreAgent,
	ColdWaveScoreAgent,
	WildfireScoreAgent,
	DroughtScoreAgent,
	WaterScarcityScoreAgent,
	CoastalFloodScoreAgent,
	InlandFloodScoreAgent,
	UrbanFloodScoreAgent,
	TyphoonScoreAgent,
	HighTemperatureAALAgent,
	ColdWaveAALAgent,
	WildfireAALAgent,
	DroughtAALAgent,
	WaterScarcityAALAgent,
	CoastalFloodAALAgent,
	InlandFloodAALAgent,
	UrbanFloodAALAgent,
	TyphoonAALAgent
)

# ========== Node 1: 데이터 수집 ==========
def data_collection_node(state: SuperAgentState, config: Any) -> Dict:
	"""
	데이터 수집 노드
	대상 위치의 기후 데이터를 수집

	Args:
		state: 현재 워크플로우 상태
		config: 설정 객체

	Returns:
		업데이트된 상태 딕셔너리
	"""
	print("[Node 1] 데이터 수집 시작...")

	try:
		agent = DataCollectionAgent(config)
		collected_data = agent.collect(
			state['target_location'],
			state.get('analysis_params', {})
		)

		return {
			'collected_data': collected_data,
			'data_collection_status': 'completed',
			'current_step': 'vulnerability_analysis',
			'logs': ['데이터 수집 완료']
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
			'high_temperature',
			'cold_wave',
			'wildfire',
			'drought',
			'water_scarcity',
			'coastal_flood',
			'inland_flood',
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
			'high_temperature': HighTemperatureAALAgent(),
			'cold_wave': ColdWaveAALAgent(),
			'wildfire': WildfireAALAgent(),
			'drought': DroughtAALAgent(),
			'water_scarcity': WaterScarcityAALAgent(),
			'coastal_flood': CoastalFloodAALAgent(),
			'inland_flood': InlandFloodAALAgent(),
			'urban_flood': UrbanFloodAALAgent(),
			'typhoon': TyphoonAALAgent()
		}

		collected_data = state.get('collected_data', {})
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


# ========== Node 4: 물리적 리스크 종합 점수 산출 (9개 Sub Agent AAL×자산가치 → 100점 스케일) ==========
def physical_risk_score_node(state: SuperAgentState, config: Any) -> Dict:
	"""
	물리적 리스크 종합 점수 산출 노드
	9개 Physical Risk Score Sub Agent를 사용하여 AAL×자산가치 계산 후 100점 스케일 변환

	Args:
		state: 현재 워크플로우 상태
		config: 설정 객체

	Returns:
		업데이트된 상태 딕셔너리
	"""
	print("[Node 4] 물리적 리스크 종합 점수 산출 시작 (AAL×자산가치 → 100점 스케일)...")

	try:
		# 9개 Physical Risk Score Agent 인스턴스 생성
		agents = {
			'high_temperature': HighTemperatureScoreAgent(),
			'cold_wave': ColdWaveScoreAgent(),
			'wildfire': WildfireScoreAgent(),
			'drought': DroughtScoreAgent(),
			'water_scarcity': WaterScarcityScoreAgent(),
			'coastal_flood': CoastalFloodScoreAgent(),
			'inland_flood': InlandFloodScoreAgent(),
			'urban_flood': UrbanFloodScoreAgent(),
			'typhoon': TyphoonScoreAgent()
		}

		asset_info = state.get('asset_info', {})
		aal_analysis = state.get('aal_analysis', {})

		physical_risk_scores = {}

		# 각 리스크별로 AAL × 자산가치 계산
		for risk_type, agent in agents.items():
			# 1. AAL 퍼센트 가져오기
			aal_data = aal_analysis.get(risk_type, {})
			aal_percentage = aal_data.get('aal_percentage', 0)

			# 2. AAL × 자산가치 계산 (100점 스케일 변환)
			result = agent.calculate_physical_risk_score(
				aal_percentage=aal_percentage,
				asset_info=asset_info
			)

			if result.get('status') == 'completed':
				physical_risk_scores[risk_type] = result

				print(f"  - {risk_type}: AAL={aal_percentage:.2f}%, "
				      f"재무손실={result.get('financial_loss', 0):,.0f}원, "
				      f"Score={result.get('physical_risk_score_100', 0):.2f}/100")
			else:
				print(f"  - {risk_type}: 계산 실패 - {result.get('error', 'Unknown error')}")

		return {
			'physical_risk_scores': physical_risk_scores,
			'physical_score_status': 'completed',
			'current_step': 'template_generation',
			'logs': ['물리적 리스크 종합 점수 산출 완료 (AAL×자산가치 → 100점 스케일)']
		}

	except Exception as e:
		print(f"[Node 4] 오류: {str(e)}")
		return {
			'physical_score_status': 'failed',
			'errors': [f'물리적 리스크 점수 산출 오류: {str(e)}']
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
			'current_step': 'strategy_generation',
			'logs': ['리포트 템플릿 생성 완료 (ReportTemplateAgent)']
		}

	except Exception as e:
		print(f"[Node 5] 오류: {str(e)}")
		return {
			'template_status': 'failed',
			'errors': [f'템플릿 생성 오류: {str(e)}']
		}


# ========== Node 6: 대응 전략 생성 (StrategyGenerationAgent) ==========
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
	print("[Node 6] 대응 전략 생성 시작 (StrategyGenerationAgent)...")

	try:
		llm_client = LLMClient()
		rag_engine = RAGEngine()
		strategy_agent = StrategyGenerationAgent(llm_client, rag_engine)

		response_strategy = strategy_agent.generate_strategy(
			target_location=state.get('target_location', {}),
			vulnerability_analysis=state.get('vulnerability_analysis', {}),
			aal_analysis=state.get('aal_analysis', {}),
			physical_risk_scores=state.get('physical_risk_scores', {}),
			report_template=state.get('report_template', {})
		)

		return {
			'response_strategy': response_strategy,
			'strategy_status': 'completed',
			'current_step': 'report_generation',
			'logs': ['대응 전략 생성 완료 (StrategyGenerationAgent)']
		}

	except Exception as e:
		print(f"[Node 6] 오류: {str(e)}")
		return {
			'strategy_status': 'failed',
			'errors': [f'대응 전략 생성 오류: {str(e)}']
		}


# ========== Node 7: 리포트 생성 (ReportGenerationAgent) ==========
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
	print("[Node 7] 리포트 생성 시작 (ReportGenerationAgent)...")

	try:
		report_agent = ReportGenerationAgent()

		generated_report = report_agent.generate_report(
			target_location=state.get('target_location', {}),
			building_info=state.get('building_info', {}),
			vulnerability_analysis=state.get('vulnerability_analysis', {}),
			aal_analysis=state.get('aal_analysis', {}),
			physical_risk_scores=state.get('physical_risk_scores', {}),
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
		print(f"[Node 7] 오류: {str(e)}")
		return {
			'report_status': 'failed',
			'errors': [f'리포트 생성 오류: {str(e)}']
		}


# ========== Node 8: 검증 ==========
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
	print("[Node 8] 리포트 검증 시작...")

	try:
		validator = ValidationAgent()
		validation_result = validator.validate_report(
			state.get('generated_report', {}),
			state.get('physical_risk_scores', {}),
			state.get('aal_analysis', {}),
			state.get('response_strategy', {})
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
			return {
				'validation_result': validation_result,
				'validation_status': 'failed',
				'validation_feedback': validation_result.get('improvement_suggestions', []),
				'logs': [f'검증 실패: {len(validation_result.get("issues_found", []))}개 이슈 발견']
			}

	except Exception as e:
		print(f"[Node 8] 오류: {str(e)}")
		return {
			'validation_status': 'error',
			'errors': [f'검증 오류: {str(e)}']
		}


# ========== Node 9: 최종 리포트 산출 ==========
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
	print("[Node 9] 최종 리포트 확정...")

	return {
		'final_report': state.get('generated_report'),
		'final_status': 'completed',
		'workflow_status': 'completed',
		'current_step': 'done',
		'logs': ['최종 리포트 확정 완료']
	}
