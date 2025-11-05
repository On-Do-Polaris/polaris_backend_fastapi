"""
Configuration Settings
SKAX 물리적 리스크 분석 설정
"""
import os
from typing import Dict, Any


class Config:
    """
    전역 설정 클래스
    """

    def __init__(self, config_dict: Dict = None):
        """
        설정 초기화

        Args:
            config_dict: 사용자 정의 설정 딕셔너리 (선택)
        """
        # 기본 설정 로드
        self._load_default_config()

        # 사용자 정의 설정 오버라이드
        if config_dict:
            self._override_config(config_dict)

    def _load_default_config(self):
        """
        기본 설정 로드
        """
        # ===== 일반 설정 =====
        self.PROJECT_NAME = "SKAX Physical Risk Analyzer"
        self.VERSION = "1.0.0"
        self.DEBUG = os.getenv("DEBUG", "False").lower() == "true"

        # ===== 데이터 수집 설정 =====
        self.DATA_COLLECTION = {
            'timeout': 30,  # seconds
            'retry_count': 3,
            'cache_enabled': True,
            'cache_ttl': 3600  # 1 hour
        }

        # 데이터 API 엔드포인트 (예시)
        self.DATA_SOURCES = {
            'climate_api': os.getenv('CLIMATE_API_URL', 'https://api.climate.example.com'),
            'climate_api_key': os.getenv('CLIMATE_API_KEY', ''),
            'geographic_api': os.getenv('GEOGRAPHIC_API_URL', 'https://api.geo.example.com'),
            'geographic_api_key': os.getenv('GEOGRAPHIC_API_KEY', ''),
        }

        # ===== SSP 시나리오 설정 =====
        self.SSP_SCENARIOS = ['ssp1-2.6', 'ssp2-4.5', 'ssp3-7.0', 'ssp5-8.5']

        self.SSP_CONFIG = {
            'default_probabilities': {
                'ssp1-2.6': 0.20,
                'ssp2-4.5': 0.35,
                'ssp3-7.0': 0.25,
                'ssp5-8.5': 0.20
            },
            'probability_calculation_method': 'bayesian'  # 'bayesian', 'expert', 'equal'
        }

        # ===== 기후 리스크 설정 =====
        self.CLIMATE_RISKS = {
            'high_temperature': {
                'enabled': True,
                'threshold_extreme': 35.0,  # Celsius
                'threshold_heatwave': 33.0,
                'weight': 1.0
            },
            'cold_wave': {
                'enabled': True,
                'threshold_extreme': -15.0,  # Celsius
                'threshold_coldwave': -10.0,
                'snowstorm_weight': 0.2,
                'weight': 1.0
            },
            'sea_level_rise': {
                'enabled': False,  # FROZEN
                'weight': 0.8
            },
            'drought': {
                'enabled': True,
                'threshold_precipitation_deficit': 0.3,  # 30% below normal
                'threshold_dry_spell_days': 30,
                'weight': 1.2
            },
            'wildfire': {
                'enabled': True,
                'fire_weather_index_threshold': 30,
                'weight': 1.1
            },
            'typhoon': {
                'enabled': True,
                'wind_speed_threshold': 17.2,  # m/s (Beaufort scale 8)
                'weight': 1.3
            },
            'water_scarcity': {
                'enabled': False,  # FROZEN
                'weight': 0.8
            },
            'flood': {
                'enabled': True,
                'extreme_rainfall_threshold': 100,  # mm/day
                'weight': 1.2
            }
        }

        # ===== 리스크 통합 설정 =====
        self.RISK_INTEGRATION = {
            'normalization_method': 'min-max',  # 'min-max', 'z-score', 'percentile'
            'aggregation_method': 'weighted_average',  # 'weighted_average', 'maximum', 'geometric_mean'
            'compound_risk_weight': 0.15,
            'correlation_threshold': 0.5
        }

        # 리스크 등급 분류 기준
        self.RISK_RATING_THRESHOLDS = {
            'CRITICAL': 80,
            'HIGH': 60,
            'MEDIUM': 40,
            'LOW': 20,
            'VERY_LOW': 0
        }

        # ===== 리포트 설정 =====
        self.REPORT_CONFIG = {
            'output_dir': './reports',
            'formats': ['json', 'pdf', 'html'],
            'include_visualizations': True,
            'language': 'ko',  # 'ko', 'en'
            'template_dir': './templates'
        }

        # ===== 분석 파라미터 =====
        self.ANALYSIS_PARAMS = {
            'default_time_horizon': '2050',
            'default_analysis_period': '2025-2050',
            'baseline_period': '1995-2014',
            'time_step': 'yearly'  # 'monthly', 'yearly', 'decadal'
        }

        # ===== 로깅 설정 =====
        self.LOGGING = {
            'level': 'INFO',  # 'DEBUG', 'INFO', 'WARNING', 'ERROR'
            'log_dir': './logs',
            'log_file': 'skax_analyzer.log',
            'console_output': True
        }

        # ===== 성능 설정 =====
        self.PERFORMANCE = {
            'max_workers': 4,  # 병렬 처리 워커 수
            'batch_size': 100,
            'enable_caching': True,
            'cache_backend': 'memory'  # 'memory', 'redis', 'file'
        }

    def _override_config(self, config_dict: Dict):
        """
        사용자 정의 설정으로 오버라이드

        Args:
            config_dict: 오버라이드할 설정 딕셔너리
        """
        for key, value in config_dict.items():
            if hasattr(self, key):
                if isinstance(getattr(self, key), dict) and isinstance(value, dict):
                    # 딕셔너리 설정은 병합
                    getattr(self, key).update(value)
                else:
                    setattr(self, key, value)

    def get(self, key: str, default: Any = None) -> Any:
        """
        설정값 가져오기

        Args:
            key: 설정 키
            default: 기본값

        Returns:
            설정값
        """
        return getattr(self, key, default)

    def to_dict(self) -> Dict:
        """
        설정을 딕셔너리로 변환

        Returns:
            설정 딕셔너리
        """
        return {
            key: value
            for key, value in self.__dict__.items()
            if not key.startswith('_')
        }

    def __repr__(self):
        return f"Config(project={self.PROJECT_NAME}, version={self.VERSION})"


# 환경별 설정 클래스
class DevelopmentConfig(Config):
    """
    개발 환경 설정
    """

    def __init__(self):
        super().__init__()
        self.DEBUG = True
        self.LOGGING['level'] = 'DEBUG'


class ProductionConfig(Config):
    """
    프로덕션 환경 설정
    """

    def __init__(self):
        super().__init__()
        self.DEBUG = False
        self.LOGGING['level'] = 'INFO'
        self.PERFORMANCE['max_workers'] = 8


class TestConfig(Config):
    """
    테스트 환경 설정
    """

    def __init__(self):
        super().__init__()
        self.DEBUG = True
        self.DATA_COLLECTION['cache_enabled'] = False
        self.LOGGING['level'] = 'DEBUG'


# 환경에 따른 설정 로드
def load_config(env: str = None) -> Config:
    """
    환경에 따른 설정 로드

    Args:
        env: 환경 ('development', 'production', 'test')

    Returns:
        Config 인스턴스
    """
    if env is None:
        env = os.getenv('ENVIRONMENT', 'development')

    config_map = {
        'development': DevelopmentConfig,
        'production': ProductionConfig,
        'test': TestConfig
    }

    config_class = config_map.get(env.lower(), Config)
    return config_class()
