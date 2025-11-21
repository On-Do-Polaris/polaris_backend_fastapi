'''
파일명: urban_flood_aal_agent.py
최종 수정일: 2025-11-21
버전: v2
파일 개요: 도시 집중 홍수 리스크 AAL 분석 Agent (AAL_final_logic_v2 기반)
변경 이력:
	- 2025-11-11: v00 - 초기 생성
	- 2025-11-20: v9 - AAL_final_logic_v9.md 로직 적용
	- 2025-11-21: v2 - AAL_final_logic_v2.md 로직 적용
		* 강도지표: X_pflood(t,j) = k_depth × max(0, R_peak - drain_capacity)
		* bin: [0), [0~0.3m), [0.3~1.0m), [≥1.0m)
		* DR_intensity: [0.00, 0.05, 0.25, 0.50]
'''
from typing import Dict, Any
import numpy as np
from .base_aal_analysis_agent import BaseAALAnalysisAgent


class UrbanFloodAALAgent(BaseAALAnalysisAgent):
	"""
	도시 집중 홍수 리스크 AAL 분석 Agent (v2)

	사용 데이터: KMA RAIN80 (연 강한 단시간 강우)
	강도지표: X_pflood(t,j) = k_depth × E_pflood(t,j)
	E_pflood = max(0, R_peak - drain_capacity)
	"""

	def __init__(self):
		"""
		UrbanFloodAALAgent 초기화 (v2)

		bin 구간 (침수 깊이):
			- bin1: 0 m (침수 없음)
			- bin2: 0 ~ 0.3 m (경미~중간 피해)
			- bin3: 0.3 ~ 1.0 m (본격적 피해)
			- bin4: >= 1.0 m (광범위·중대 피해)

		기본 손상률 (DR_intensity):
			- bin1: 0%
			- bin2: 5%
			- bin3: 25%
			- bin4: 50%
		"""
		bins = [
			(0, 0),          # bin1: 침수 없음
			(0, 0.3),        # bin2: 0 ~ 0.3m
			(0.3, 1.0),      # bin3: 0.3 ~ 1.0m
			(1.0, float('inf'))  # bin4: >= 1.0m
		]

		dr_intensity = [
			0.00,   # 0%
			0.05,   # 5%
			0.25,   # 25%
			0.50    # 50%
		]

		super().__init__(
			risk_type='도시 홍수',
			bins=bins,
			dr_intensity=dr_intensity,
			s_min=0.7,
			s_max=1.3,
			insurance_rate=0.0
		)

		# 변환 계수 (튜닝 필요)
		self.c_rain = 1.0      # RAIN80 → mm/h 변환 계수
		self.k_depth = 0.01    # 초과강우 → 침수심 변환 계수

	def calculate_intensity_indicator(self, collected_data: Dict[str, Any]) -> np.ndarray:
		"""
		도시 집중 홍수 강도지표 X_pflood(t,j) 계산

		Args:
			collected_data: 수집된 기후 및 지형 데이터
				- rain80: 연도별 RAIN80 값 리스트
				- drain_capacity: 배수능력 (mm/h) - 사이트별

		Returns:
			연도별 침수 깊이 값 배열 (m)
		"""
		climate_data = collected_data.get('climate_data', {})
		rain80_data = climate_data.get('rain80', [])
		drain_capacity = climate_data.get('drain_capacity', 60.0)  # 기본값 60 mm/h

		if not rain80_data:
			self.logger.warning("RAIN80 데이터가 없습니다. 기본값 0으로 설정합니다.")
			return np.array([0.0])

		yearly_inundation_depth = []

		for rain80 in rain80_data:
			# RAIN80 → mm/h 변환
			r_peak_mmph = self.c_rain * rain80

			# 강우 초과분 계산
			e_pflood = max(0, r_peak_mmph - drain_capacity)

			# 침수 깊이 변환 (m)
			inundation_depth = self.k_depth * e_pflood

			yearly_inundation_depth.append(inundation_depth)

		depth_array = np.array(yearly_inundation_depth, dtype=float)
		self.logger.info(
			f"침수 깊이 데이터: {len(depth_array)}개 연도, "
			f"범위: {depth_array.min():.3f}m ~ {depth_array.max():.3f}m"
		)

		return depth_array

	def _classify_into_bins(self, intensity_values: np.ndarray) -> np.ndarray:
		"""
		침수 깊이를 bin으로 분류 (도시 홍수 전용)

		Args:
			intensity_values: 연도별 침수 깊이 배열 (m)

		Returns:
			각 연도의 bin 인덱스 배열 (0-based)
		"""
		bin_indices = np.zeros(len(intensity_values), dtype=int)

		for idx, depth in enumerate(intensity_values):
			if depth == 0:
				bin_indices[idx] = 0  # bin1: 침수 없음
			elif depth < 0.3:
				bin_indices[idx] = 1  # bin2: 0 ~ 0.3m
			elif depth < 1.0:
				bin_indices[idx] = 2  # bin3: 0.3 ~ 1.0m
			else:
				bin_indices[idx] = 3  # bin4: >= 1.0m

		return bin_indices
