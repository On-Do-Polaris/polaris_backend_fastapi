"""
Mock DB Data Loader
Phase 1 결과(H, E, V, Risk Scores, AAL)를 Mock 데이터로 생성하는 헬퍼

Phase 2 테스트를 위해 DB가 없어도 Phase 1 결과를 시뮬레이션
"""
import random
from typing import Dict, List, Any


class MockDBLoader:
    """Mock DB 데이터 로더"""

    # 9가지 리스크 타입
    RISK_TYPES = [
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

    @staticmethod
    def generate_phase1_results(
        site_id: str,
        site_name: str,
        location: dict,
        building_info: dict = None,
        asset_info: dict = None,
        variation_seed: int = None
    ) -> Dict[str, Any]:
        """
        단일 사업장의 Phase 1 결과 생성 (Mock)

        Args:
            site_id: 사업장 ID
            site_name: 사업장 이름
            location: 위치 정보 (latitude, longitude)
            building_info: 건물 정보 (선택)
            asset_info: 자산 정보 (선택)
            variation_seed: 난수 시드 (재현성을 위해)

        Returns:
            Phase 1 결과 딕셔너리
        """
        if variation_seed is not None:
            random.seed(variation_seed)

        # 위치 기반 특성 반영 (위도가 높을수록 추위 리스크 증가)
        latitude = location.get('latitude', 37.0)
        is_coastal = location.get('is_coastal', False)
        elevation = location.get('elevation', 50)

        # H, E, V 값 생성 (0-100)
        hazard_scores = {}
        exposure_scores = {}
        vulnerability_scores = {}
        risk_scores = {}
        aal_values = {}

        for risk_type in MockDBLoader.RISK_TYPES:
            # Hazard: 위치 특성 반영
            if risk_type == 'extreme_heat':
                h = random.uniform(40, 85) - (latitude - 30) * 2  # 위도가 낮을수록 높음
            elif risk_type == 'extreme_cold':
                h = random.uniform(30, 80) + (latitude - 30) * 2  # 위도가 높을수록 높음
            elif risk_type in ['sea_level_rise', 'typhoon']:
                h = random.uniform(60, 90) if is_coastal else random.uniform(10, 30)
            elif risk_type in ['river_flood', 'urban_flood']:
                h = random.uniform(50, 85) if elevation < 100 else random.uniform(20, 50)
            else:
                h = random.uniform(30, 70)

            # Exposure: 자산 가치 기반
            asset_value = asset_info.get('total_asset_value', 50000000000) if asset_info else 50000000000
            e = min(100, 30 + (asset_value / 1000000000) * 2)  # 자산 가치에 비례

            # Vulnerability: 건물 연식 기반
            building_age = building_info.get('building_age', 20) if building_info else 20
            has_seismic = building_info.get('has_seismic_design', False) if building_info else False
            v = min(100, 40 + building_age * 1.5 - (10 if has_seismic else 0))

            # Risk Score: (H + E + V) / 3
            risk_score = (h + e + v) / 3

            # AAL: Risk Score 기반 (0.01% ~ 2%)
            aal = (risk_score / 100) * random.uniform(0.5, 2.0)

            hazard_scores[risk_type] = round(h, 2)
            exposure_scores[risk_type] = round(e, 2)
            vulnerability_scores[risk_type] = round(v, 2)
            risk_scores[risk_type] = round(risk_score, 2)
            aal_values[risk_type] = round(aal, 4)

        return {
            'site_id': site_id,
            'site_name': site_name,
            'location': location,
            'building_info': building_info or {},
            'asset_info': asset_info or {},
            'hazard_scores': hazard_scores,
            'exposure_scores': exposure_scores,
            'vulnerability_scores': vulnerability_scores,
            'risk_scores': risk_scores,
            'aal_values': aal_values
        }

    @staticmethod
    def generate_multi_site_data(
        num_sites: int = 3,
        company_name: str = "Test Company"
    ) -> List[Dict[str, Any]]:
        """
        다중 사업장 Mock 데이터 생성

        Args:
            num_sites: 사업장 개수
            company_name: 회사명

        Returns:
            사업장 데이터 리스트
        """
        sites_data = []

        # 샘플 사업장 위치 (서울, 부산, 제주)
        sample_locations = [
            {
                'site_id': 'site_001',
                'site_name': '서울 본사',
                'location': {
                    'latitude': 37.5665,
                    'longitude': 126.9780,
                    'name': 'Seoul HQ',
                    'is_coastal': False,
                    'elevation': 50
                },
                'building_info': {
                    'building_age': 15,
                    'has_seismic_design': True,
                    'structure': '철근콘크리트',
                    'floors_above': 20
                },
                'asset_info': {
                    'total_asset_value': 100000000000  # 1000억
                }
            },
            {
                'site_id': 'site_002',
                'site_name': '부산 지사',
                'location': {
                    'latitude': 35.1796,
                    'longitude': 129.0756,
                    'name': 'Busan Branch',
                    'is_coastal': True,
                    'elevation': 10
                },
                'building_info': {
                    'building_age': 25,
                    'has_seismic_design': False,
                    'structure': '철근콘크리트',
                    'floors_above': 10
                },
                'asset_info': {
                    'total_asset_value': 50000000000  # 500억
                }
            },
            {
                'site_id': 'site_003',
                'site_name': '제주 데이터센터',
                'location': {
                    'latitude': 33.4996,
                    'longitude': 126.5312,
                    'name': 'Jeju Data Center',
                    'is_coastal': True,
                    'elevation': 30
                },
                'building_info': {
                    'building_age': 5,
                    'has_seismic_design': True,
                    'structure': '철골구조',
                    'floors_above': 3
                },
                'asset_info': {
                    'total_asset_value': 200000000000  # 2000억
                }
            }
        ]

        for i in range(min(num_sites, len(sample_locations))):
            site_config = sample_locations[i]
            site_data = MockDBLoader.generate_phase1_results(
                site_id=site_config['site_id'],
                site_name=site_config['site_name'],
                location=site_config['location'],
                building_info=site_config['building_info'],
                asset_info=site_config['asset_info'],
                variation_seed=i * 100  # 재현성
            )
            sites_data.append(site_data)

        return sites_data


# 편의 함수
def load_mock_phase1_results(site_id: str, **kwargs) -> Dict[str, Any]:
    """단일 사업장 Mock Phase 1 결과 로드"""
    return MockDBLoader.generate_phase1_results(site_id, **kwargs)


def load_mock_multi_site_data(num_sites: int = 3, company_name: str = "Test Company") -> List[Dict[str, Any]]:
    """다중 사업장 Mock 데이터 로드"""
    return MockDBLoader.generate_multi_site_data(num_sites, company_name)
