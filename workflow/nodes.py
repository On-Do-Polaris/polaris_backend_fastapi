"""
LangGraph Workflow Nodes
워크플로우 노드 정의
"""
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
    """
    print("[Node 1] 데이터 수집 시작...")

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
            'logs': ['데이터 수집 완료']
        }

    except Exception as e:
        return {
            'data_collection_status': 'failed',
            'errors': [f'데이터 수집 실패: {str(e)}'],
            'workflow_status': 'failed'
        }


# ========== Node 2: SSP 시나리오 확률 계산 ==========
def calculate_ssp_probabilities_node(state: AnalysisState, config: Any) -> Dict:
    """
    SSP 시나리오 확률 계산 노드
    """
    print("[Node 2] SSP 시나리오 확률 계산 시작...")

    try:
        calculator = SSPProbabilityCalculator(config)
        ssp_probabilities = calculator.calculate_probabilities(state['collected_data'])

        return {
            'ssp_probabilities': ssp_probabilities,
            'ssp_calculation_status': 'success',
            'current_step': 'climate_risk_analysis',
            'logs': ['SSP 시나리오 확률 계산 완료']
        }

    except Exception as e:
        return {
            'ssp_calculation_status': 'failed',
            'errors': [f'SSP 계산 실패: {str(e)}'],
            'workflow_status': 'failed'
        }


# ========== Node 3: 8대 기후 리스크 분석 (병렬) ==========
def analyze_high_temperature_node(state: AnalysisState, config: Any) -> Dict:
    """고온 리스크 분석"""
    print("[Node 3.1] 고온 리스크 분석...")
    agent = HighTemperatureRiskAgent(config)
    risk_result = agent.calculate_risk(state['collected_data'], state['ssp_probabilities'])

    return {
        'climate_risk_scores': {'high_temperature': risk_result},
        'completed_risk_analyses': ['high_temperature']
    }


def analyze_cold_wave_node(state: AnalysisState, config: Any) -> Dict:
    """한파 리스크 분석"""
    print("[Node 3.2] 한파 리스크 분석...")
    agent = ColdWaveRiskAgent(config)
    risk_result = agent.calculate_risk(state['collected_data'], state['ssp_probabilities'])

    return {
        'climate_risk_scores': {'cold_wave': risk_result},
        'completed_risk_analyses': ['cold_wave']
    }


def analyze_sea_level_rise_node(state: AnalysisState, config: Any) -> Dict:
    """해수면 상승 리스크 분석 (FROZEN)"""
    print("[Node 3.3] 해수면 상승 리스크 분석 (FROZEN)...")
    agent = SeaLevelRiseRiskAgent(config)
    risk_result = agent.calculate_risk(state['collected_data'], state['ssp_probabilities'])

    return {
        'climate_risk_scores': {'sea_level_rise': risk_result},
        'completed_risk_analyses': ['sea_level_rise']
    }


def analyze_drought_node(state: AnalysisState, config: Any) -> Dict:
    """가뭄 리스크 분석"""
    print("[Node 3.4] 가뭄 리스크 분석...")
    agent = DroughtRiskAgent(config)
    risk_result = agent.calculate_risk(state['collected_data'], state['ssp_probabilities'])

    return {
        'climate_risk_scores': {'drought': risk_result},
        'completed_risk_analyses': ['drought']
    }


def analyze_wildfire_node(state: AnalysisState, config: Any) -> Dict:
    """산불 리스크 분석"""
    print("[Node 3.5] 산불 리스크 분석...")
    agent = WildfireRiskAgent(config)
    risk_result = agent.calculate_risk(state['collected_data'], state['ssp_probabilities'])

    return {
        'climate_risk_scores': {'wildfire': risk_result},
        'completed_risk_analyses': ['wildfire']
    }


def analyze_typhoon_node(state: AnalysisState, config: Any) -> Dict:
    """태풍 리스크 분석"""
    print("[Node 3.6] 태풍 리스크 분석...")
    agent = TyphoonRiskAgent(config)
    risk_result = agent.calculate_risk(state['collected_data'], state['ssp_probabilities'])

    return {
        'climate_risk_scores': {'typhoon': risk_result},
        'completed_risk_analyses': ['typhoon']
    }


def analyze_water_scarcity_node(state: AnalysisState, config: Any) -> Dict:
    """물부족 리스크 분석 (FROZEN)"""
    print("[Node 3.7] 물부족 리스크 분석 (FROZEN)...")
    agent = WaterScarcityRiskAgent(config)
    risk_result = agent.calculate_risk(state['collected_data'], state['ssp_probabilities'])

    return {
        'climate_risk_scores': {'water_scarcity': risk_result},
        'completed_risk_analyses': ['water_scarcity']
    }


def analyze_flood_node(state: AnalysisState, config: Any) -> Dict:
    """홍수 리스크 분석"""
    print("[Node 3.8] 홍수 리스크 분석...")
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
    """
    print("[Node 4] 리스크 통합 계산 시작...")

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
            'logs': ['리스크 통합 완료']
        }

    except Exception as e:
        return {
            'integration_status': 'failed',
            'errors': [f'리스크 통합 실패: {str(e)}'],
            'workflow_status': 'failed'
        }


# ========== Node 5: 리포트 생성 ==========
def generate_report_node(state: AnalysisState, config: Any) -> Dict:
    """
    리포트 생성 노드
    """
    print("[Node 5] 리포트 생성 시작...")

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
            'logs': ['리포트 생성 완료']
        }

    except Exception as e:
        return {
            'report_status': 'failed',
            'errors': [f'리포트 생성 실패: {str(e)}'],
            'workflow_status': 'failed'
        }
