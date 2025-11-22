'''
파일명: base_aal_analysis_agent.py
최종 수정일: 2025-11-21
버전: v10
파일 개요: 연평균 재무 손실률 (AAL) 분석 Base Agent
변경 이력:
	- 2025-11-21: v10 - V 스케일링과 최종 AAL 계산만 수행
		* P(H) 계산 제거 (외부에서 입력받음)
		* bin별 기본 손상률 입력받음
		* 취약성 스케일링 F_vuln 및 최종 AAL 계산만 수행
'''
from typing import Dict, Any, List
from abc import ABC
import logging


logger = logging.getLogger(__name__)


class BaseAALAnalysisAgent(ABC):
	"""
	연평균 재무 손실률 (AAL: Average Annual Loss) 분석 Base Agent

	입력: bin별 발생확률 P_r[i], bin별 기본 손상률 DR_intensity_r[i], 취약성 점수 V_score
	처리:
	- 취약성 스케일 계수 F_vuln_r(j) 계산
	- 최종 손상률 DR_r[i,j] = DR_intensity_r[i] × F_vuln_r(j)
	- AAL_r(j) = Σ[P_r[i] × DR_r[i,j] × (1-IR_r)]
	"""

	def __init__(
		self,
		risk_type: str,
		s_min: float = 0.7,
		s_max: float = 1.3,
		insurance_rate: float = 0.0
	):
		"""
		BaseAALAnalysisAgent 초기화

		Args:
			risk_type: 리스크 타입 (예: heat, cold, fire, drought, etc.)
			s_min: 취약성 스케일 최소값 (기본 0.7)
			s_max: 취약성 스케일 최대값 (기본 1.3)
			insurance_rate: 보험 보전율 IR (기본 0.0)
		"""
		self.risk_type = risk_type
		self.s_min = s_min
		self.s_max = s_max
		self.insurance_rate = insurance_rate
		self.logger = logger
		self.logger.info(f"{risk_type} AAL 분석 Agent 초기화 (v10)")

	def analyze_aal(
		self,
		bin_probabilities: List[float],
		bin_base_damage_rates: List[float],
		vulnerability_score: float
	) -> Dict[str, Any]:
		"""
		연평균 재무 손실률 (AAL) 분석
		공식: AAL_r(j) = Σ[P_r[i] × DR_r[i,j] × (1-IR_r)]

		Args:
			bin_probabilities: bin별 발생확률 P_r[i] (외부에서 계산됨)
			bin_base_damage_rates: bin별 기본 손상률 DR_intensity_r[i] (외부에서 계산됨)
			vulnerability_score: 취약성 점수 V_score_r(j) (0.0 ~ 1.0)

		Returns:
			AAL 분석 결과 딕셔너리
				- vulnerability_score: 취약성 점수
				- vulnerability_scale: 취약성 스케일 계수 F_vuln_r(j)
				- bin_final_damage_rates: bin별 최종 손상률 DR_r[i,j]
				- insurance_rate: 보험 보전율
				- aal_percentage: 연평균 재무 손실률 (%)
				- calculation_details: 계산 상세 내역
				- status: 분석 상태
		"""
		self.logger.info(f"{self.risk_type} AAL 분석 시작 (v10)")

		try:
			# 1. 취약성 스케일 계수 F_vuln_r(j) 계산
			f_vuln = self._calculate_vulnerability_scale(vulnerability_score)

			# 2. bin별 최종 손상률 DR_r[i,j] 계산
			bin_final_damage_rates = self._calculate_bin_damage_rates(
				bin_base_damage_rates, f_vuln
			)

			# 3. AAL 계산: Σ[P_r[i] × DR_r[i,j] × (1-IR_r)]
			aal = 0.0
			for i in range(len(bin_probabilities)):
				aal += bin_probabilities[i] * bin_final_damage_rates[i] * (1 - self.insurance_rate)

			aal_percentage = aal * 100  # % 단위로 변환

			result = {
				'risk_type': self.risk_type,
				'vulnerability_score': round(vulnerability_score, 4),
				'vulnerability_scale': round(f_vuln, 4),
				'bin_final_damage_rates': [round(dr, 4) for dr in bin_final_damage_rates],
				'insurance_rate': round(self.insurance_rate, 4),
				'aal_percentage': round(aal_percentage, 4),
				'calculation_details': self._get_calculation_details(
					bin_probabilities,
					bin_base_damage_rates,
					bin_final_damage_rates,
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

	def _calculate_bin_damage_rates(
		self,
		bin_base_damage_rates: List[float],
		f_vuln: float
	) -> List[float]:
		"""
		bin별 최종 손상률 DR_r[i,j] 계산
		DR_r[i,j] = DR_intensity_r[i] × F_vuln_r(j)

		Args:
			bin_base_damage_rates: bin별 기본 손상률
			f_vuln: 취약성 스케일 계수

		Returns:
			bin별 최종 손상률 리스트
		"""
		return [dr_base * f_vuln for dr_base in bin_base_damage_rates]

	def _get_calculation_details(
		self,
		bin_probabilities: List[float],
		bin_base_damage_rates: List[float],
		bin_final_damage_rates: List[float],
		vulnerability_score: float,
		f_vuln: float,
		aal_percentage: float
	) -> Dict[str, Any]:
		"""
		계산 상세 내역 생성

		Args:
			bin_probabilities: bin별 발생확률
			bin_base_damage_rates: bin별 기본 손상률
			bin_final_damage_rates: bin별 최종 손상률
			vulnerability_score: 취약성 점수
			f_vuln: 취약성 스케일 계수
			aal_percentage: 연평균 재무 손실률 (%)

		Returns:
			계산 상세 내역 딕셔너리
		"""
		bin_details = []
		for i in range(len(bin_probabilities)):
			bin_details.append({
				'bin': i + 1,
				'probability': round(bin_probabilities[i], 4),
				'base_damage_rate': round(bin_base_damage_rates[i], 4),
				'final_damage_rate': round(bin_final_damage_rates[i], 4),
				'contribution': round(
					bin_probabilities[i] * bin_final_damage_rates[i] * (1 - self.insurance_rate) * 100,
					4
				)
			})

		return {
			'formula': 'AAL_r(j) = Σ[P_r[i] × DR_r[i,j] × (1-IR_r)]',
			'vulnerability': {
				'V_score': round(vulnerability_score, 4),
				'F_vuln': round(f_vuln, 4),
				's_min': self.s_min,
				's_max': self.s_max,
				'description': f'F_vuln = {self.s_min} + ({self.s_max} - {self.s_min}) × V_score'
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
