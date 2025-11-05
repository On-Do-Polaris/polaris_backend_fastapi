'''
파일명: nodes.py
최종 수정일: 2025-11-05
버전: v00
파일 개요: LangGraph 워크플로우 노드 함수 정의 (총 13개 노드)
'''
from typing import Dict, Any
from workflow.state import AnalysisState
from agents.data_collection_agent import DataCollectionAgent
from agents.ssp_probability_calculator import SSPProbabilityCalculator
from agents.climate_risk_agents import (
	HighTemperatureRiskAgent,
	ColdWaveRiskAgent,
	SeaLevelRiseRiskAgent,
	DroughtRiskAgent,
	WildfireRiskAgent,
	TyphoonRiskAgent,
	WaterScarcityRiskAgent,
	FloodRiskAgent
)
from agents.risk_integration_agent import RiskIntegrationAgent
from agents.report_generation_agent import ReportGenerationAgent


# ========== Node 1: 데이터 수집 ==========
def collect_data_node(state: AnalysisState, config: Any) -> Dict:
	"""
	데이터 수집 노드
	대상 위치의 기후 데이터를 수집

	Args:
		state: 현재 워크플로우 상태
		config: 설정 객체

	Returns:
		업데이트된 상태 딕셔너리 (collected_data, status, logs 포함)
	"""
	print("[Node 1] Data collection starting...")

	try:
		agent = DataCollectionAgent(config)
		collected_data = agent.collect(
			state['target_location'],
			state['analysis_params']
		)

		return {
			'collected_data': collected_data,
			'data_collection_status': 'success',
			'current_step': 'ssp_calculation',
			'logs': ['Data collection completed']
		}

	except Exception as e:
		return {
			'data_collection_status': 'failed',
			'errors': [f'Data collection failed: {str(e)}'],
			'workflow_status': 'failed'
		}


# ========== Node 2: SSP 시나리오 확률 계산 ==========
def calculate_ssp_probabilities_node(state: AnalysisState, config: Any) -> Dict:
	"""
	SSP 시나리오 확률 계산 노드
	4가지 SSP 시나리오별 가중치 계산 (ssp1-2.6, ssp2-4.5, ssp3-7.0, ssp5-8.5)

	Args:
		state: 현재 워크플로우 상태 (collected_data 포함)
		config: 설정 객체

	Returns:
		업데이트된 상태 딕셔너리 (ssp_probabilities, status, logs 포함)
	"""
	print("[Node 2] SSP scenario probability calculation starting...")

	try:
		calculator = SSPProbabilityCalculator(config)
		ssp_probabilities = calculator.calculate_probabilities(state['collected_data'])

		return {
			'ssp_probabilities': ssp_probabilities,
			'ssp_calculation_status': 'success',
			'current_step': 'climate_risk_analysis',
			'logs': ['SSP scenario probability calculation completed']
		}

	except Exception as e:
		return {
			'ssp_calculation_status': 'failed',
			'errors': [f'SSP calculation failed: {str(e)}'],
			'workflow_status': 'failed'
		}


# ========== Node 3: 8대 기후 리스크 분석 (병렬) ==========
def analyze_high_temperature_node(state: AnalysisState, config: Any) -> Dict:
	"""
	고온 리스크 분석 노드
	폭염 및 고온 현상으로 인한 리스크 계산 (H x E x V)

	Args:
		state: 현재 워크플로우 상태 (collected_data, ssp_probabilities 포함)
		config: 설정 객체

	Returns:
		업데이트된 상태 딕셔너리 (climate_risk_scores에 high_temperature 추가)
	"""
	print("[Node 3.1] High temperature risk analysis...")
	agent = HighTemperatureRiskAgent(config)
	risk_result = agent.calculate_risk(state['collected_data'], state['ssp_probabilities'])

	return {
		'climate_risk_scores': {'high_temperature': risk_result},
		'completed_risk_analyses': ['high_temperature']
	}


def analyze_cold_wave_node(state: AnalysisState, config: Any) -> Dict:
	"""
	한파 리스크 분석 노드
	한파 및 폭설로 인한 리스크 계산 (H x E x V)

	Args:
		state: 현재 워크플로우 상태 (collected_data, ssp_probabilities 포함)
		config: 설정 객체

	Returns:
		업데이트된 상태 딕셔너리 (climate_risk_scores에 cold_wave 추가)
	"""
	print("[Node 3.2] Cold wave risk analysis...")
	agent = ColdWaveRiskAgent(config)
	risk_result = agent.calculate_risk(state['collected_data'], state['ssp_probabilities'])

	return {
		'climate_risk_scores': {'cold_wave': risk_result},
		'completed_risk_analyses': ['cold_wave']
	}


def analyze_sea_level_rise_node(state: AnalysisState, config: Any) -> Dict:
	"""
	해수면 상승 리스크 분석 노드 (FROZEN)
	해수면 상승으로 인한 침수 리스크 계산 (H x E x V)

	Args:
		state: 현재 워크플로우 상태 (collected_data, ssp_probabilities 포함)
		config: 설정 객체

	Returns:
		업데이트된 상태 딕셔너리 (climate_risk_scores에 sea_level_rise 추가)
	"""
	print("[Node 3.3] Sea level rise risk analysis (FROZEN)...")
	agent = SeaLevelRiseRiskAgent(config)
	risk_result = agent.calculate_risk(state['collected_data'], state['ssp_probabilities'])

	return {
		'climate_risk_scores': {'sea_level_rise': risk_result},
		'completed_risk_analyses': ['sea_level_rise']
	}


def analyze_drought_node(state: AnalysisState, config: Any) -> Dict:
	"""
	가뭄 리스크 분석 노드
	강수량 부족 및 가뭄으로 인한 리스크 계산 (H x E x V)

	Args:
		state: 현재 워크플로우 상태 (collected_data, ssp_probabilities 포함)
		config: 설정 객체

	Returns:
		업데이트된 상태 딕셔너리 (climate_risk_scores에 drought 추가)
	"""
	print("[Node 3.4] Drought risk analysis...")
	agent = DroughtRiskAgent(config)
	risk_result = agent.calculate_risk(state['collected_data'], state['ssp_probabilities'])

	return {
		'climate_risk_scores': {'drought': risk_result},
		'completed_risk_analyses': ['drought']
	}


def analyze_wildfire_node(state: AnalysisState, config: Any) -> Dict:
	"""
	산불 리스크 분석 노드
	기후 조건에 따른 산불 발생 리스크 계산 (H x E x V)

	Args:
		state: 현재 워크플로우 상태 (collected_data, ssp_probabilities 포함)
		config: 설정 객체

	Returns:
		업데이트된 상태 딕셔너리 (climate_risk_scores에 wildfire 추가)
	"""
	print("[Node 3.5] Wildfire risk analysis...")
	agent = WildfireRiskAgent(config)
	risk_result = agent.calculate_risk(state['collected_data'], state['ssp_probabilities'])

	return {
		'climate_risk_scores': {'wildfire': risk_result},
		'completed_risk_analyses': ['wildfire']
	}


def analyze_typhoon_node(state: AnalysisState, config: Any) -> Dict:
	"""
	태풍 리스크 분석 노드
	태풍 및 강풍으로 인한 리스크 계산 (H x E x V)

	Args:
		state: 현재 워크플로우 상태 (collected_data, ssp_probabilities 포함)
		config: 설정 객체

	Returns:
		업데이트된 상태 딕셔너리 (climate_risk_scores에 typhoon 추가)
	"""
	print("[Node 3.6] Typhoon risk analysis...")
	agent = TyphoonRiskAgent(config)
	risk_result = agent.calculate_risk(state['collected_data'], state['ssp_probabilities'])

	return {
		'climate_risk_scores': {'typhoon': risk_result},
		'completed_risk_analyses': ['typhoon']
	}


def analyze_water_scarcity_node(state: AnalysisState, config: Any) -> Dict:
	"""
	물부족 리스크 분석 노드 (FROZEN)
	수자원 부족으로 인한 리스크 계산 (H x E x V)

	Args:
		state: 현재 워크플로우 상태 (collected_data, ssp_probabilities 포함)
		config: 설정 객체

	Returns:
		업데이트된 상태 딕셔너리 (climate_risk_scores에 water_scarcity 추가)
	"""
	print("[Node 3.7] Water scarcity risk analysis (FROZEN)...")
	agent = WaterScarcityRiskAgent(config)
	risk_result = agent.calculate_risk(state['collected_data'], state['ssp_probabilities'])

	return {
		'climate_risk_scores': {'water_scarcity': risk_result},
		'completed_risk_analyses': ['water_scarcity']
	}


def analyze_flood_node(state: AnalysisState, config: Any) -> Dict:
	"""
	홍수 리스크 분석 노드
	집중 호우 및 홍수로 인한 리스크 계산 (H x E x V)

	Args:
		state: 현재 워크플로우 상태 (collected_data, ssp_probabilities 포함)
		config: 설정 객체

	Returns:
		업데이트된 상태 딕셔너리 (climate_risk_scores에 flood 추가)
	"""
	print("[Node 3.8] Flood risk analysis...")
	agent = FloodRiskAgent(config)
	risk_result = agent.calculate_risk(state['collected_data'], state['ssp_probabilities'])

	return {
		'climate_risk_scores': {'flood': risk_result},
		'completed_risk_analyses': ['flood']
	}


# ========== Node 4: 리스크 통합 ==========
def integrate_risks_node(state: AnalysisState, config: Any) -> Dict:
	"""
	리스크 통합 노드
	8개 개별 기후 리스크를 통합하여 종합 리스크 스코어 계산

	Args:
		state: 현재 워크플로우 상태 (climate_risk_scores, ssp_probabilities 포함)
		config: 설정 객체

	Returns:
		업데이트된 상태 딕셔너리 (integrated_risk, status, logs 포함)
	"""
	print("[Node 4] Risk integration calculation starting...")

	try:
		agent = RiskIntegrationAgent(config)
		integrated_risk = agent.integrate(
			climate_risk_scores=state['climate_risk_scores'],
			ssp_probabilities=state['ssp_probabilities']
		)

		return {
			'integrated_risk': integrated_risk,
			'integration_status': 'success',
			'current_step': 'report_generation',
			'logs': ['Risk integration completed']
		}

	except Exception as e:
		return {
			'integration_status': 'failed',
			'errors': [f'Risk integration failed: {str(e)}'],
			'workflow_status': 'failed'
		}


# ========== Node 5: 리포트 생성 ==========
def generate_report_node(state: AnalysisState, config: Any) -> Dict:
	"""
	리포트 생성 노드
	전체 분석 결과를 기반으로 최종 리포트 생성

	Args:
		state: 현재 워크플로우 상태 (모든 분석 결과 포함)
		config: 설정 객체

	Returns:
		업데이트된 상태 딕셔너리 (report, status, logs 포함)
	"""
	print("[Node 5] Report generation starting...")

	try:
		agent = ReportGenerationAgent(config)

		# 전체 분석 결과 패키징
		analysis_results = {
			'collected_data': state['collected_data'],
			'ssp_probabilities': state['ssp_probabilities'],
			'climate_risk_scores': state['climate_risk_scores'],
			'integrated_risk': state['integrated_risk']
		}

		report = agent.generate(
			location=state['target_location'],
			analysis_results=analysis_results
		)

		return {
			'report': report,
			'report_status': 'success',
			'current_step': 'completed',
			'workflow_status': 'completed',
			'logs': ['Report generation completed']
		}

	except Exception as e:
		return {
			'report_status': 'failed',
			'errors': [f'Report generation failed: {str(e)}'],
			'workflow_status': 'failed'
		}
