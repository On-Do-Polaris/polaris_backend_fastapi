'''
파일명: water_stress_aal_agent.py
최종 수정일: 2025-11-20
버전: v9
파일 개요: 물부족 리스크 AAL 분석 Agent (AAL_final_logic_v9 기반)
변경 이력:
	- 2025-11-11: v00 - 초기 생성
	- 2025-11-20: v9 - AAL_final_logic_v9.md 로직 적용
		* 강도지표: X_wst(t) = WSI(t) = Withdrawal(t) / ARWR(t)
		* bin: [<0.2), [0.2~0.4), [0.4~0.8), [≥0.8)
		* DR_intensity: [0.01, 0.03, 0.07, 0.15]
'''
from typing import Dict, Any
import numpy as np
from .base_aal_analysis_agent import BaseAALAnalysisAgent


class WaterStressAALAgent(BaseAALAnalysisAgent):
	"""
	물부족 리스크 AAL 분석 Agent (v9)

	사용 데이터: WAMIS 용수이용량 및 재생가능수자원
	강도지표: X_wst(t) = WSI(t) = Withdrawal(t) / ARWR(t)
	- WSI: Water Stress Index
	- ARWR = TRWR × 0.63 (환경유지유량 차감)
	"""

	def __init__(self):
		"""
		WaterStressAALAgent 초기화 (v9)

		bin 구간 (WRI 기준):
			- bin1: WSI < 0.2 (낮은 물 스트레스)
			- bin2: 0.2 <= WSI < 0.4 (중간 물 스트레스)
			- bin3: 0.4 <= WSI < 0.8 (높은 물 스트레스)
			- bin4: WSI >= 0.8 (극심한 물 스트레스)

		기본 손상률 (DR_intensity):
			- bin1: 1%
			- bin2: 3%
			- bin3: 7%
			- bin4: 15%
		"""
		bins = [
			(0, 0.2),
			(0.2, 0.4),
			(0.4, 0.8),
			(0.8, float('inf'))
		]

		dr_intensity = [
			0.01,   # 1%
			0.03,   # 3%
			0.07,   # 7%
			0.15    # 15%
		]

		super().__init__(
			risk_type='물부족',
			bins=bins,
			dr_intensity=dr_intensity,
			s_min=0.7,
			s_max=1.3,
			insurance_rate=0.0
		)

	def calculate_intensity_indicator(self, collected_data: Dict[str, Any]) -> np.ndarray:
		"""
		물부족 강도지표 X_wst(t) 계산
		X_wst(t) = WSI(t) = Withdrawal(t) / ARWR(t)

		Args:
			collected_data: 수집된 수자원 데이터
				- water_data: 연도별 용수이용량 및 ARWR 데이터 리스트
					각 원소는 {'year': int, 'withdrawal': float, 'arwr': float}

		Returns:
			연도별 WSI 값 배열
		"""
		water_data = collected_data.get('water_data', [])

		if not water_data:
			self.logger.warning("수자원 데이터가 없습니다. 기본값 0으로 설정합니다.")
			return np.array([0.0])

		yearly_wsi = []

		for year_data in water_data:
			year = year_data.get('year')
			withdrawal = year_data.get('withdrawal', 0.0)  # 용수이용량
			arwr = year_data.get('arwr', 1.0)              # 가용 재생 수자원

			# WSI 계산
			if arwr > 0:
				wsi = withdrawal / arwr
			else:
				wsi = 0.0

			yearly_wsi.append(wsi)

		wsi_array = np.array(yearly_wsi, dtype=float)
		self.logger.info(f"WSI 데이터: {len(wsi_array)}개 연도, 범위: {wsi_array.min():.2f} ~ {wsi_array.max():.2f}")

		return wsi_array
