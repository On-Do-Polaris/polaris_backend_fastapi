'''
파일명: mock_data.py
생성일: 2025-12-11
버전: v01
파일 개요: Workflow 테스트용 Mock 데이터 생성
'''


def get_mock_climate_data():
    """
    Node 1 (Data Collection)용 Mock 기후 데이터

    Returns:
        dict: Mock 기후 데이터 (climate_summary 포함)
    """
    return {
        'climate_summary': {
            'location': {
                'latitude': 37.5665,
                'longitude': 126.9780,
                'name': 'Seoul Test Site (Mock)'
            },
            'data_years': list(range(2025, 2051)),
            'ssp_scenarios': ['ssp1-2.6', 'ssp2-4.5', 'ssp3-7.0', 'ssp5-8.5'],
            'statistics': {
                'wsdi_mean': 25.5,
                'wsdi_max': 35.2,
                'wsdi_min': 15.8,
                'temperature_mean': 12.5,
                'precipitation_mean': 1200.0
            }
        },
        'climate_data': {
            'wsdi': [20, 22, 24, 26, 28, 30],  # Mock WSDI 데이터
            'temperature': [11.5, 12.0, 12.5, 13.0, 13.5, 14.0],
            'precipitation': [1100, 1150, 1200, 1250, 1300, 1350]
        }
    }


def get_mock_risk_assessment():
    """
    Node 3 (Risk Assessment)용 Mock H×E×V×AAL 데이터
    9개 물리적 리스크에 대한 Mock 데이터 반환

    Returns:
        dict: Mock 리스크 평가 데이터
            - hazard_scores: H 값 (9개 리스크)
            - exposure_scores: E 값 (9개 리스크)
            - vulnerability_scores: V 값 (9개 리스크)
            - physical_risk_scores: 물리적 리스크 점수 (9개 리스크)
            - aal_values: AAL 값 (9개 리스크)
            - vulnerability_analysis: 취약성 분석 결과
            - aal_analysis: AAL 분석 결과
    """
    # 9개 리스크 타입
    risk_types = [
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

    # Mock 점수 (실제 범위와 유사하게 설정)
    mock_scores = {
        'extreme_heat': {'h': 75.5, 'e': 60.2, 'v': 55.8, 'risk': 72.3, 'aal': 0.15},
        'extreme_cold': {'h': 45.2, 'e': 50.3, 'v': 48.1, 'risk': 47.9, 'aal': 0.08},
        'wildfire': {'h': 30.1, 'e': 25.5, 'v': 40.2, 'risk': 31.9, 'aal': 0.05},
        'drought': {'h': 55.8, 'e': 48.7, 'v': 62.3, 'risk': 55.6, 'aal': 0.12},
        'water_stress': {'h': 62.3, 'e': 55.1, 'v': 58.9, 'risk': 58.8, 'aal': 0.10},
        'sea_level_rise': {'h': 20.5, 'e': 15.2, 'v': 25.8, 'risk': 20.5, 'aal': 0.03},
        'river_flood': {'h': 68.9, 'e': 72.3, 'v': 65.4, 'risk': 68.9, 'aal': 0.18},
        'urban_flood': {'h': 70.2, 'e': 68.5, 'v': 71.2, 'risk': 69.9, 'aal': 0.16},
        'typhoon': {'h': 58.7, 'e': 61.2, 'v': 54.3, 'risk': 58.1, 'aal': 0.14}
    }

    # Hazard Scores
    hazard_scores = {}
    for risk_type in risk_types:
        hazard_scores[f'{risk_type}_hazard_score'] = mock_scores[risk_type]['h']

    # Exposure Scores
    exposure_scores = {}
    for risk_type in risk_types:
        exposure_scores[f'{risk_type}_exposure_score'] = mock_scores[risk_type]['e']

    # Vulnerability Scores
    vulnerability_scores = {}
    for risk_type in risk_types:
        vulnerability_scores[f'{risk_type}_vulnerability_score'] = mock_scores[risk_type]['v']

    # Physical Risk Scores
    physical_risk_scores = {}
    for risk_type in risk_types:
        score_data = mock_scores[risk_type]
        physical_risk_scores[risk_type] = {
            'hazard_score': score_data['h'],
            'exposure_score': score_data['e'],
            'vulnerability_score': score_data['v'],
            'physical_risk_score_100': score_data['risk'],
            'risk_level': _get_risk_level(score_data['risk']),
            'status': 'completed'
        }

    # AAL Values
    aal_values = {}
    for risk_type in risk_types:
        score_data = mock_scores[risk_type]
        aal_values[f'{risk_type}_aal'] = {
            'base_aal': score_data['aal'] * 0.8,  # base_aal은 final보다 약간 낮음
            'final_aal_percentage': score_data['aal'],
            'status': 'completed'
        }

    # Vulnerability Analysis (하위 호환성)
    vulnerability_analysis = {
        'vulnerability_scores': vulnerability_scores,
        'status': 'completed'
    }

    # AAL Analysis (하위 호환성)
    aal_analysis = {
        'aal_scaled_results': aal_values,
        'status': 'completed',
        'request_id': 'mock_request_12345'
    }

    # Summary 정보
    avg_risk = sum(mock_scores[r]['risk'] for r in risk_types) / len(risk_types)
    total_aal = sum(mock_scores[r]['aal'] for r in risk_types)

    risk_assessment_summary = {
        'average_hazard': sum(mock_scores[r]['h'] for r in risk_types) / len(risk_types),
        'average_exposure': sum(mock_scores[r]['e'] for r in risk_types) / len(risk_types),
        'average_vulnerability': sum(mock_scores[r]['v'] for r in risk_types) / len(risk_types),
        'average_integrated_risk': avg_risk,
        'total_final_aal': total_aal,
        'highest_integrated_risk': {
            'risk_type': 'extreme_heat',
            'score': 72.3
        }
    }

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
        'risk_assessment_summary': risk_assessment_summary,
        'current_step': 'report_template',
        'logs': [
            'Workflow Mock: 통합 리스크 평가 완료 (request_id=mock_request_12345)',
            '9개 물리적 리스크 Mock 데이터 로드',
            f'평균 Hazard: {risk_assessment_summary["average_hazard"]:.2f}',
            f'평균 Exposure: {risk_assessment_summary["average_exposure"]:.2f}',
            f'평균 Vulnerability: {risk_assessment_summary["average_vulnerability"]:.2f}',
            f'평균 통합 리스크: {avg_risk:.2f}',
            f'총 AAL: {total_aal:.4f}%',
            '최고 리스크: extreme_heat'
        ]
    }


def _get_risk_level(score: float) -> str:
    """
    리스크 점수에 따른 리스크 레벨 반환

    Args:
        score: 리스크 점수 (0-100)

    Returns:
        str: 리스크 레벨 ('Very Low', 'Low', 'Medium', 'High', 'Very High')
    """
    if score >= 80:
        return 'Very High'
    elif score >= 60:
        return 'High'
    elif score >= 40:
        return 'Medium'
    elif score >= 20:
        return 'Low'
    else:
        return 'Very Low'
