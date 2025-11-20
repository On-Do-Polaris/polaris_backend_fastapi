'''
파일명: settings.py
최종 수정일: 2025-11-17
버전: v04
파일 개요: SKAX 물리적 리스크 분석 설정 클래스 정의 (Super Agent 구조)
변경 이력:
	- 2025-11-05: v00 - 초기 설정
	- 2025-11-11: v03 - Super Agent 구조에 맞게 업데이트
	- 2025-11-17: v04 - LangSmith 트레이싱 설정 추가
'''
import os
from typing import Dict, Any


class Config:
	"""
	전역 설정 클래스
	SKAX 물리적 리스크 분석 시스템의 모든 설정을 관리
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
		프로젝트의 기본값을 설정
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

		# ===== 기후 리스크 설정 (9개 리스크) =====
		self.CLIMATE_RISKS = {
			'high_temperature': {
				'enabled': True,
				'name': '극심한 고온',
				'threshold_extreme': 35.0,  # Celsius
				'threshold_heatwave': 33.0
			},
			'cold_wave': {
				'enabled': True,
				'name': '극심한 한파',
				'threshold_extreme': -15.0,  # Celsius
				'threshold_coldwave': -10.0
			},
			'wildfire': {
				'enabled': True,
				'name': '산불',
				'fire_weather_index_threshold': 30
			},
			'drought': {
				'enabled': True,
				'name': '가뭄',
				'threshold_precipitation_deficit': 0.3,  # 30% below normal
				'threshold_dry_spell_days': 30
			},
			'water_scarcity': {
				'enabled': True,
				'name': '물 부족'
			},
			'coastal_flood': {
				'enabled': True,
				'name': '해안 홍수',
				'extreme_rainfall_threshold': 100  # mm/day
			},
			'inland_flood': {
				'enabled': True,
				'name': '내륙 홍수',
				'extreme_rainfall_threshold': 150  # mm/day
			},
			'urban_flood': {
				'enabled': True,
				'name': '도심 홍수',
				'hourly_rainfall_threshold': 50  # mm/hr
			},
			'typhoon': {
				'enabled': True,
				'name': '열대성 태풍',
				'wind_speed_threshold': 17.2  # m/s (Beaufort scale 8)
			}
		}

		# ===== AAL 계산 설정 =====
		self.AAL_CONFIG = {
			'default_insurance_coverage_rate': 0.0,  # 기본 보험보전율 0%
			'max_damage_rate': 1.0  # 최대 손상률 100%
		}

		# ===== 물리적 리스크 점수 설정 =====
		self.PHYSICAL_RISK_SCORE_CONFIG = {
			'normalization_base': 1_000_000_000,  # 10억원 (100점 기준)
			'max_score': 100.0  # 최대 점수
		}

		# 리스크 등급 분류 기준 (100점 스케일)
		self.RISK_RATING_THRESHOLDS = {
			'VERY_HIGH': 80,
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

		# ===== LLM 설정 (대응 전략 생성용) =====
		self.LLM_CONFIG = {
			'provider': 'openai',  # 'openai', 'anthropic', 'local'
			'model': 'gpt-4',
			'api_key': os.getenv('OPENAI_API_KEY', ''),
			'temperature': 0.7,
			'max_tokens': 2000
		}

		# ===== RAG 설정 (유사 보고서 검색용) =====
		self.RAG_CONFIG = {
			'vector_db': 'chromadb',  # 'chromadb', 'faiss'
			'embedding_model': 'sentence-transformers/all-MiniLM-L6-v2',
			'top_k': 5,  # 검색할 유사 문서 수
			'similarity_threshold': 0.7
		}

		# ===== 검증 설정 =====
		self.VALIDATION_CONFIG = {
			'max_retry_count': 3,  # 최대 재시도 횟수
			'enable_auto_retry': True
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
			'cache_backend': 'memory'  # 'memory', 'file'
		}

		# ===== LangSmith 트레이싱 설정 =====
		self.LANGSMITH_CONFIG = {
			'enabled': os.getenv('LANGSMITH_ENABLED', 'False').lower() == 'true',
			'project_name': os.getenv('LANGSMITH_PROJECT', 'skax-physical-risk'),
			'api_key': os.getenv('LANGSMITH_API_KEY', ''),
			'endpoint': os.getenv('LANGSMITH_ENDPOINT', 'https://api.smith.langchain.com'),
			'tracing_v2': os.getenv('LANGCHAIN_TRACING_V2', 'false').lower() == 'true',
			# 추적할 항목
			'trace_inputs': True,  # 입력 데이터 추적
			'trace_outputs': True,  # 출력 데이터 추적
			'trace_errors': True,  # 에러 추적
			'trace_metadata': True,  # 메타데이터 추적 (실행 시간, Agent 정보 등)
			# 샘플링 설정
			'sampling_rate': float(os.getenv('LANGSMITH_SAMPLING_RATE', '1.0')),  # 1.0 = 100% 추적
			# 태그 설정
			'default_tags': ['physical-risk', 'climate-analysis', 'super-agent'],
		}

		# LangSmith 환경 변수 자동 설정
		if self.LANGSMITH_CONFIG['enabled']:
			os.environ['LANGCHAIN_TRACING_V2'] = 'true'
			os.environ['LANGCHAIN_PROJECT'] = self.LANGSMITH_CONFIG['project_name']
			if self.LANGSMITH_CONFIG['api_key']:
				os.environ['LANGCHAIN_API_KEY'] = self.LANGSMITH_CONFIG['api_key']
			if self.LANGSMITH_CONFIG['endpoint']:
				os.environ['LANGCHAIN_ENDPOINT'] = self.LANGSMITH_CONFIG['endpoint']

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
		"""
		Config 객체의 문자열 표현

		Returns:
			문자열 표현
		"""
		return f"Config(project={self.PROJECT_NAME}, version={self.VERSION})"


# 환경별 설정 클래스
class DevelopmentConfig(Config):
	"""
	개발 환경 설정
	디버그 모드 활성화 및 상세 로깅
	"""

	def __init__(self):
		"""
		개발 환경 설정 초기화
		"""
		super().__init__()
		self.DEBUG = True
		self.LOGGING['level'] = 'DEBUG'
		# 개발 환경에서는 LangSmith 선택적 활성화 (환경 변수로 제어)
		self.LANGSMITH_CONFIG['project_name'] = os.getenv('LANGSMITH_PROJECT', 'skax-physical-risk-dev')


class ProductionConfig(Config):
	"""
	프로덕션 환경 설정
	성능 최적화 및 에러 로깅
	"""

	def __init__(self):
		"""
		프로덕션 환경 설정 초기화
		"""
		super().__init__()
		self.DEBUG = False
		self.LOGGING['level'] = 'INFO'
		self.PERFORMANCE['max_workers'] = 8
		# 프로덕션 환경에서는 LangSmith 기본 활성화 (API 키가 있는 경우)
		if os.getenv('LANGSMITH_API_KEY'):
			self.LANGSMITH_CONFIG['enabled'] = True
			self.LANGSMITH_CONFIG['project_name'] = os.getenv('LANGSMITH_PROJECT', 'skax-physical-risk-prod')
			# 프로덕션 추가 태그
			self.LANGSMITH_CONFIG['default_tags'].extend(['production', 'monitoring'])


class TestConfig(Config):
	"""
	테스트 환경 설정
	캐싱 비활성화 및 디버그 로깅
	"""

	def __init__(self):
		"""
		테스트 환경 설정 초기화
		"""
		super().__init__()
		self.DEBUG = True
		self.DATA_COLLECTION['cache_enabled'] = False
		self.LOGGING['level'] = 'DEBUG'
		# 테스트 환경에서는 LangSmith 비활성화 (CI 성능 최적화)
		self.LANGSMITH_CONFIG['enabled'] = False
		os.environ['LANGCHAIN_TRACING_V2'] = 'false'


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
