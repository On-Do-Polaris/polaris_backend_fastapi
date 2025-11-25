'''
파일명: base_aal_analysis_agent.py
최종 수정일: 2025-11-25
버전: v11
파일 개요: 연평균 재무 손실률 (AAL) 분석 Base Agent
변경 이력:
	- 2025-11-21: v10 - V 스케일링과 최종 AAL 계산만 수행
		* P(H) 계산 제거 (외부에서 입력받음)
		* bin별 기본 손상률 입력받음
		* 취약성 스케일링 F_vuln 및 최종 AAL 계산만 수행
	- 2025-11-25: v11 - DB에서 bin별 P(H)*기본손상률 합계를 입력받아,
           취약성 스케일링 적용한 최종 AAL 계산 수행
		* bin별 최종 손상률 DR_r[i,j] 계산 제거
		* P(H) 관련 로직 완전 제거 (외부/DB에서 처리)
        * 입력: base_aal_from_db, vulnerability_score(0~100)
        * 출력: final_aal, f_vuln, risk_level
'''

from typing import Dict, Any
from abc import ABC
import logging


logger = logging.getLogger(__name__)


class BaseAALAnalysisAgent(ABC):
	"""
	연평균 재무 손실률 (AAL: Average Annual Loss) 분석 Base Agent

	입력: base_aal (DB에서 계산된 기본 AAL), vulnerability_score (취약성 점수 0~100)
	처리:
	- 취약성 스케일 계수 F_vuln_r(j) 계산
	- 최종 AAL 계산: AAL_r(j) = base_aal × F_vuln_r(j) × (1-IR_r)
	"""

	def __init__(
		self,
		risk_type: str,
		s_min: float = 0.9,
		s_max: float = 1.1,
		insurance_rate: float = 0.0
	):
		"""
		BaseAALAnalysisAgent 초기화

		Args:
			risk_type: 리스크 타입 (예: heat, cold, fire, drought, etc.)
			s_min: 취약성 스케일 최소값 (기본 0.9)
			s_max: 취약성 스케일 최대값 (기본 1.1)
			insurance_rate: 보험 보전율 IR (기본 0.0)
		"""
		self.risk_type = risk_type
		self.s_min = s_min
		self.s_max = s_max
		self.insurance_rate = insurance_rate
		self.logger = logger
		self.logger.info(f"{risk_type} AAL 분석 Agent 초기화 (v11)")

	def analyze_aal(
		self,
		base_aal: float,
		vulnerability_score: float
	) -> Dict[str, Any]:
		"""
		연평균 재무 손실률 (AAL) 분석
		공식: AAL_r(j) = base_aal × F_vuln_r(j) × (1-IR_r)

		Args:
			base_aal: DB에서 계산된 기본 AAL (Σ[P_r[i] × DR_intensity_r[i]])
			vulnerability_score: 취약성 점수 V_score_r(j) (0.0 ~ 100.0)

		Returns:
			AAL 분석 결과 딕셔너리
				- risk_type: 리스크 타입
				- vulnerability_score: 취약성 점수
				- vulnerability_scale: 취약성 스케일 계수 F_vuln_r(j)
				- base_aal: 기본 AAL
				- insurance_rate: 보험 보전율
				- final_aal_percentage: 최종 연평균 재무 손실률 (%)
				- risk_level: 위험 수준 (Minimal, Low, Moderate, High, Critical)
				- status: 분석 상태
		"""
		self.logger.info(f"{self.risk_type} AAL 분석 시작 (v11)")

		try:
			# 1. 취약성 스케일 계수 F_vuln_r(j) 계산
			f_vuln = self._calculate_vulnerability_scale(vulnerability_score)

			# 2. 최종 AAL 계산: base_aal × F_vuln_r(j) × (1-IR_r)
			final_aal = base_aal * f_vuln * (1 - self.insurance_rate)
			final_aal_percentage = final_aal * 100.0

			result = {
				'risk_type': self.risk_type,
				'vulnerability_score': round(vulnerability_score, 4),
				'vulnerability_scale': round(f_vuln, 4),
				'base_aal': round(base_aal, 6),
				'insurance_rate': round(self.insurance_rate, 4),
				'final_aal_percentage': round(final_aal_percentage, 4),
				'risk_level': self._classify_aal_level(final_aal_percentage),
				'status': 'completed'
			}

			self.logger.info(
				f"{self.risk_type} AAL 분석 완료: "
				f"V_score={vulnerability_score:.4f}, F_vuln={f_vuln:.4f}, "
				f"AAL={final_aal_percentage:.4f}%"
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
			vulnerability_score: 취약성 점수 (0~100점)

		Returns:
			취약성 스케일 계수
		"""
		v_clamped = max(0.0, min(100.0, vulnerability_score))  # 0~100으로 보정
		v_norm = v_clamped / 100.0                             # 0~1로 정규화
		return self.s_min + (self.s_max - self.s_min) * v_norm

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
