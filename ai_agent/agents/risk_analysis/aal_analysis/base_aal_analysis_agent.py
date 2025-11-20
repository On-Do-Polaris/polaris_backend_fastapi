'''
파일명: base_aal_analysis_agent.py
최종 수정일: 2025-11-20
버전: v9
파일 개요: 연평균 재무 손실률 (AAL) 분석 Base Agent
변경 이력:
	- 2025-11-11: v01 - AAL 공식 수정 (AAL% = Σ[확률×손상률×(1-보험보전율)])
	- 2025-11-11: v02 - 재무 손실액 계산 제거 (손실률만 계산)
	- 2025-11-20: v9 - AAL_final_logic_v9.md 기반 공통 프레임워크 적용
		* bin별 확률 및 손상률 계산 방식 적용
		* 취약성 점수 기반 스케일링 추가
		* AAL(j) = Σ[P[i] × DR[i,j] × (1-IR)] 공식 적용
'''
from typing import Dict, Any, List, Tuple
from abc import ABC, abstractmethod
import logging
import numpy as np


logger = logging.getLogger(__name__)


class BaseAALAnalysisAgent(ABC):
	"""
	연평균 재무 손실률 (AAL: Average Annual Loss) 분석 Base Agent

	공통 프레임워크 (v9):
	- 강도지표 X_r(t) 계산
	- bin 분류
	- bin별 발생확률 P_r[i] = (해당 bin 연도 수) / (전체 연도 수)
	- bin별 기본 손상률 DR_intensity_r[i]
	- 취약성 점수 V_score_r(j) 기반 스케일링 F_vuln_r(j)
	- 최종 손상률 DR_r[i,j] = DR_intensity_r[i] × F_vuln_r(j)
	- AAL_r(j) = Σ[P_r[i] × DR_r[i,j] × (1-IR_r)]
	"""

	def __init__(
		self,
		risk_type: str,
		bins: List[Tuple[float, float]],
		dr_intensity: List[float],
		s_min: float = 0.7,
		s_max: float = 1.3,
		insurance_rate: float = 0.0
	):
		"""
		BaseAALAnalysisAgent 초기화

		Args:
			risk_type: 리스크 타입 (예: heat, cold, fire, drought, etc.)
			bins: 강도 구간 리스트 [(min1, max1), (min2, max2), ...]
			dr_intensity: bin별 기본 손상률 리스트 [DR1, DR2, DR3, ...]
			s_min: 취약성 스케일 최소값 (기본 0.7)
			s_max: 취약성 스케일 최대값 (기본 1.3)
			insurance_rate: 보험 보전율 IR (기본 0.0)
		"""
		self.risk_type = risk_type
		self.bins = bins
		self.dr_intensity = dr_intensity
		self.s_min = s_min
		self.s_max = s_max
		self.insurance_rate = insurance_rate
		self.logger = logger
		self.logger.info(f"{risk_type} AAL 분석 Agent 초기화 (v9)")

	def analyze_aal(
		self,
		collected_data: Dict[str, Any],
		vulnerability_score: float,
		asset_info: Dict[str, Any]
	) -> Dict[str, Any]:
		"""
		연평균 재무 손실률 (AAL) 분석
		v9 공식: AAL_r(j) = Σ[P_r[i] × DR_r[i,j] × (1-IR_r)]

		Args:
			collected_data: 수집된 기후 데이터 (시계열 데이터 포함)
			vulnerability_score: 취약성 점수 V_score_r(j) (0.0 ~ 1.0)
			asset_info: 사업장 노출 자산 정보

		Returns:
			AAL 분석 결과 딕셔너리
				- bin_probabilities: bin별 발생확률 P_r[i]
				- bin_damage_rates: bin별 최종 손상률 DR_r[i,j]
				- vulnerability_score: 취약성 점수
				- vulnerability_scale: 취약성 스케일 계수 F_vuln_r(j)
				- insurance_rate: 보험 보전율
				- aal_percentage: 연평균 재무 손실률 (%)
				- calculation_details: 계산 상세 내역
				- status: 분석 상태
		"""
		self.logger.info(f"{self.risk_type} AAL 분석 시작 (v9)")

		try:
			# 1. 강도지표 X_r(t) 계산 (추상 메서드)
			intensity_values = self.calculate_intensity_indicator(collected_data)

			# 2. bin 분류 및 발생확률 P_r[i] 계산
			bin_probabilities = self._calculate_bin_probabilities(intensity_values)

			# 3. 취약성 스케일 계수 F_vuln_r(j) 계산
			f_vuln = self._calculate_vulnerability_scale(vulnerability_score)

			# 4. bin별 최종 손상률 DR_r[i,j] 계산
			bin_damage_rates = self._calculate_bin_damage_rates(f_vuln)

			# 5. AAL 계산: Σ[P_r[i] × DR_r[i,j] × (1-IR_r)]
			aal = 0.0
			for i in range(len(self.bins)):
				aal += bin_probabilities[i] * bin_damage_rates[i] * (1 - self.insurance_rate)

			aal_percentage = aal * 100  # % 단위로 변환

			result = {
				'risk_type': self.risk_type,
				'bin_probabilities': [round(p, 4) for p in bin_probabilities],
				'bin_damage_rates': [round(dr, 4) for dr in bin_damage_rates],
				'vulnerability_score': round(vulnerability_score, 4),
				'vulnerability_scale': round(f_vuln, 4),
				'insurance_rate': round(self.insurance_rate, 4),
				'aal_percentage': round(aal_percentage, 4),
				'calculation_details': self._get_calculation_details(
					bin_probabilities,
					bin_damage_rates,
					vulnerability_score,
					f_vuln,
					aal_percentage
				),
				'status': 'completed'
			}

			self.logger.info(
				f"{self.risk_type} AAL 분석 완료: "
				f"V_score={vulnerability_score:.4f}, F_vuln={f_vuln:.4f}, "
				f"AAL={aal_percentage:.4f}%"
			)

			return result

		except Exception as e:
			self.logger.error(f"{self.risk_type} AAL 분석 중 오류: {str(e)}", exc_info=True)
			return {
				'risk_type': self.risk_type,
				'status': 'failed',
				'error': str(e)
			}

	@abstractmethod
	def calculate_intensity_indicator(self, collected_data: Dict[str, Any]) -> np.ndarray:
		"""
		강도지표 X_r(t) 계산
		각 연도별 리스크 강도 값 산출

		Args:
			collected_data: 수집된 기후 데이터 (시계열)

		Returns:
			연도별 강도지표 배열 (numpy array)
		"""
		pass

	def _classify_into_bins(self, intensity_values: np.ndarray) -> np.ndarray:
		"""
		강도지표를 bin으로 분류

		Args:
			intensity_values: 연도별 강도지표 배열

		Returns:
			각 연도의 bin 인덱스 배열 (0-based)
		"""
		bin_indices = np.zeros(len(intensity_values), dtype=int)

		for idx, value in enumerate(intensity_values):
			for i, (bin_min, bin_max) in enumerate(self.bins):
				if bin_min <= value < bin_max:
					bin_indices[idx] = i
					break
			else:
				# 마지막 bin (upper bound 없음)
				bin_indices[idx] = len(self.bins) - 1

		return bin_indices

	def _calculate_bin_probabilities(self, intensity_values: np.ndarray) -> List[float]:
		"""
		bin별 발생확률 P_r[i] 계산
		P_r[i] = (해당 bin에 속한 연도 수) / (전체 연도 수)

		Args:
			intensity_values: 연도별 강도지표 배열

		Returns:
			bin별 발생확률 리스트
		"""
		bin_indices = self._classify_into_bins(intensity_values)
		total_years = len(intensity_values)

		probabilities = []
		for i in range(len(self.bins)):
			count = np.sum(bin_indices == i)
			prob = count / total_years if total_years > 0 else 0.0
			probabilities.append(prob)

		return probabilities

	def _calculate_vulnerability_scale(self, vulnerability_score: float) -> float:
		"""
		취약성 스케일 계수 F_vuln_r(j) 계산
		F_vuln_r(j) = s_min + (s_max - s_min) × V_score_r(j)

		Args:
			vulnerability_score: 취약성 점수 (0.0 ~ 1.0)

		Returns:
			취약성 스케일 계수
		"""
		return self.s_min + (self.s_max - self.s_min) * vulnerability_score

	def _calculate_bin_damage_rates(self, f_vuln: float) -> List[float]:
		"""
		bin별 최종 손상률 DR_r[i,j] 계산
		DR_r[i,j] = DR_intensity_r[i] × F_vuln_r(j)

		Args:
			f_vuln: 취약성 스케일 계수

		Returns:
			bin별 최종 손상률 리스트
		"""
		return [dr_int * f_vuln for dr_int in self.dr_intensity]

	def _get_calculation_details(
		self,
		bin_probabilities: List[float],
		bin_damage_rates: List[float],
		vulnerability_score: float,
		f_vuln: float,
		aal_percentage: float
	) -> Dict[str, Any]:
		"""
		계산 상세 내역 생성

		Args:
			bin_probabilities: bin별 발생확률
			bin_damage_rates: bin별 최종 손상률
			vulnerability_score: 취약성 점수
			f_vuln: 취약성 스케일 계수
			aal_percentage: 연평균 재무 손실률 (%)

		Returns:
			계산 상세 내역 딕셔너리
		"""
		bin_details = []
		for i in range(len(self.bins)):
			bin_details.append({
				'bin': i + 1,
				'range': f"{self.bins[i][0]} ~ {self.bins[i][1]}",
				'probability': round(bin_probabilities[i], 4),
				'base_damage_rate': round(self.dr_intensity[i], 4),
				'final_damage_rate': round(bin_damage_rates[i], 4)
			})

		return {
			'formula': 'AAL_r(j) = Σ[P_r[i] × DR_r[i,j] × (1-IR_r)]',
			'vulnerability': {
				'V_score': round(vulnerability_score, 4),
				'F_vuln': round(f_vuln, 4),
				's_min': self.s_min,
				's_max': self.s_max
			},
			'bins': bin_details,
			'insurance_rate': round(self.insurance_rate, 4),
			'result': {
				'AAL (%)': f"{aal_percentage:.4f}%"
			},
			'risk_level': self._classify_aal_level(aal_percentage)
		}

	def _classify_aal_level(self, aal_percentage: float) -> str:
		"""
		AAL 기반 위험 수준 분류

		Args:
			aal_percentage: 연평균 재무 손실률 (%)

		Returns:
			위험 수준 (Minimal, Low, Moderate, High, Critical)
		"""
		if aal_percentage < 1.0:
			return 'Minimal'
		if aal_percentage < 5.0:
			return 'Low'
		if aal_percentage < 10.0:
			return 'Moderate'
		if aal_percentage < 20.0:
			return 'High'
		return 'Critical'
