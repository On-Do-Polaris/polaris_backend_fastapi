'''
파일명: aal_calculator.py
최종 수정일: 2025-11-25
버전: v01
파일 개요: AAL 기본값 계산 서비스 (DB 기반 로직)
설명:
	AAL Agent v11에서 요구하는 base_aal을 계산하는 서비스
	collected_data에서 기후 데이터를 읽어 bin별 분류 및 확률 계산
	Σ[P_r[i] × DR_intensity_r[i]] 형태로 base_aal 반환
'''

from typing import Dict, Any
import numpy as np
import logging

logger = logging.getLogger(__name__)


class AALCalculatorService:
	"""
	AAL 기본값 계산 서비스

	입력: collected_data (기후 데이터)
	출력: base_aal (기본 연평균 손실률, 취약성 미반영)

	공식: base_aal = Σ_i [P_r[i] × DR_intensity_r[i]]
	"""

	def __init__(self):
		"""AALCalculatorService 초기화"""
		self.logger = logger
		self.logger.info("AALCalculatorService 초기화")

		# 리스크별 bin 정의 및 기본 손상률
		self._init_risk_configs()

	def _init_risk_configs(self):
		"""
		리스크별 bin 경계 및 기본 손상률 정의
		aal_final_logic_v2.md 기준
		"""
		self.risk_configs = {
			'extreme_heat': {
				'data_key': 'wsdi',  # WSDI (Warm Spell Duration Index)
				'bins': [0, 3, 8, 20, float('inf')],
				'base_damage_rates': [0.001, 0.003, 0.010, 0.020]  # 0.1%, 0.3%, 1.0%, 2.0%
			},
			'extreme_cold': {
				'data_key': 'csdi',  # CSDI (Cold Spell Duration Index)
				'bins': [0, 3, 7, 15, float('inf')],
				'base_damage_rates': [0.0005, 0.0020, 0.0060, 0.0150]  # 0.05%, 0.20%, 0.60%, 1.50%
			},
			'wildfire': {
				'data_key': 'fwi',  # FWI (Fire Weather Index)
				'bins': [11.2, 21.3, 38, 50, float('inf')],
				'base_damage_rates': [0.01, 0.03, 0.10, 0.25]  # 1%, 3%, 10%, 25%
			},
			'drought': {
				'data_key': 'spei12',  # SPEI12
				'bins': [float('-inf'), -2.0, -1.5, -1.0, float('inf')],
				'base_damage_rates': [0.20, 0.07, 0.02, 0.00]  # 역순 (더 낮을수록 심각)
			},
			'water_stress': {
				'data_key': 'wsi',  # WSI (Water Stress Index)
				'bins': [0, 0.2, 0.4, 0.8, float('inf')],
				'base_damage_rates': [0.01, 0.03, 0.07, 0.15]  # 1%, 3%, 7%, 15%
			},
			'sea_level_rise': {
				'data_key': 'slr_depth',  # 침수 깊이 (m)
				'bins': [0, 0.001, 0.3, 1.0, float('inf')],
				'base_damage_rates': [0.00, 0.02, 0.15, 0.35]  # 0%, 2%, 15%, 35%
			},
			'river_flood': {
				'data_key': 'rx1day',  # RX1DAY (일 최대 강수량)
				'bins': [0, 80, 95, 99, float('inf')],  # 백분위수 기준 (실제는 동적 계산 필요)
				'base_damage_rates': [0.00, 0.02, 0.08, 0.20]  # 0%, 2%, 8%, 20%
			},
			'urban_flood': {
				'data_key': 'rain80',  # RAIN80
				'bins': [0, 0.3, 1.0, float('inf'), float('inf')],  # 침수 깊이 기준
				'base_damage_rates': [0.00, 0.05, 0.25, 0.50]  # 0%, 5%, 25%, 50%
			},
			'typhoon': {
				'data_key': 'tc_exposure',  # 태풍 노출 지수
				'bins': [0, 5, 15, float('inf'), float('inf')],
				'base_damage_rates': [0.00, 0.02, 0.10, 0.30]  # 0%, 2%, 10%, 30%
			}
		}

	def calculate_base_aal(
		self,
		collected_data: Dict[str, Any],
		risk_type: str
	) -> float:
		"""
		기본 AAL 계산: Σ_i [P_r[i] × DR_intensity_r[i]]

		Args:
			collected_data: 기후 데이터 딕셔너리
			risk_type: 리스크 타입 (예: 'extreme_heat', 'drought')

		Returns:
			base_aal: 기본 연평균 손실률 (0~1 사이의 비율)
		"""
		self.logger.info(f"{risk_type} base_aal 계산 시작")

		try:
			# 리스크 설정 조회
			if risk_type not in self.risk_configs:
				self.logger.warning(f"{risk_type} 설정 없음, 기본값 0.01 반환")
				return 0.01  # 기본값 1%

			config = self.risk_configs[risk_type]
			data_key = config['data_key']
			bins = config['bins']
			base_damage_rates = config['base_damage_rates']

			# 기후 데이터 추출
			climate_data = collected_data.get('climate_data', {})
			risk_data = climate_data.get(data_key, [])

			if not risk_data:
				self.logger.warning(f"{risk_type} 데이터 없음 ({data_key}), 기본값 0.01 반환")
				return 0.01

			# numpy 배열로 변환
			risk_data = np.array(risk_data)

			# bin별 확률 계산
			bin_counts = np.zeros(len(base_damage_rates))
			total_count = len(risk_data)

			for i in range(len(base_damage_rates)):
				if i == 0:
					# 첫 번째 bin: < bins[1]
					mask = risk_data < bins[1]
				elif i == len(base_damage_rates) - 1:
					# 마지막 bin: >= bins[i]
					mask = risk_data >= bins[i]
				else:
					# 중간 bin: bins[i] <= data < bins[i+1]
					mask = (risk_data >= bins[i]) & (risk_data < bins[i+1])

				bin_counts[i] = np.sum(mask)

			# 확률 계산: P_r[i]
			probabilities = bin_counts / total_count if total_count > 0 else np.zeros_like(bin_counts)

			# base_aal 계산: Σ[P_r[i] × DR_intensity_r[i]]
			base_aal = np.sum(probabilities * np.array(base_damage_rates))

			self.logger.info(
				f"{risk_type} base_aal 계산 완료: {base_aal:.6f} "
				f"(bins: {bin_counts}, probs: {probabilities})"
			)

			return float(base_aal)

		except Exception as e:
			self.logger.error(f"{risk_type} base_aal 계산 오류: {str(e)}", exc_info=True)
			return 0.01  # 오류 시 기본값 1%

	def calculate_all_base_aal(
		self,
		collected_data: Dict[str, Any]
	) -> Dict[str, float]:
		"""
		모든 리스크의 base_aal 일괄 계산

		Args:
			collected_data: 기후 데이터 딕셔너리

		Returns:
			리스크별 base_aal 딕셔너리
		"""
		results = {}

		for risk_type in self.risk_configs.keys():
			results[risk_type] = self.calculate_base_aal(collected_data, risk_type)

		return results


# 싱글톤 인스턴스 (선택적)
_aal_calculator_instance = None

def get_aal_calculator() -> AALCalculatorService:
	"""AALCalculatorService 싱글톤 인스턴스 반환"""
	global _aal_calculator_instance
	if _aal_calculator_instance is None:
		_aal_calculator_instance = AALCalculatorService()
	return _aal_calculator_instance
