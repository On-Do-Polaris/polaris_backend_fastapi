'''
파일명: base_aal_analysis_agent.py
최종 수정일: 2025-11-11
버전: v02
파일 개요: 연평균 재무 손실률 (AAL) 분석 Base Agent
변경 이력:
	- 2025-11-11: v01 - AAL 공식 수정 (AAL% = Σ[확률×손상률×(1-보험보전율)])
	- 2025-11-11: v02 - 재무 손실액 계산 제거 (손실률만 계산)
'''
from typing import Dict, Any
from abc import ABC, abstractmethod
import logging


logger = logging.getLogger(__name__)


class BaseAALAnalysisAgent(ABC):
	"""
	연평균 재무 손실률 (AAL: Average Annual Loss) 분석 Base Agent
	각 기후 리스크별로 AAL(%) = Σ[확률 × 손상률 × (1-보험보전율)] 계산
	"""

	def __init__(self, risk_type: str):
		"""
		BaseAALAnalysisAgent 초기화

		Args:
			risk_type: 리스크 타입 (예: high_temperature, coastal_flood)
		"""
		self.risk_type = risk_type
		self.logger = logger
		self.logger.info(f"{risk_type} AAL 분석 Agent 초기화")

	def analyze_aal(
		self,
		collected_data: Dict[str, Any],
		physical_risk_score: float,
		asset_info: Dict[str, Any]
	) -> Dict[str, Any]:
		"""
		연평균 재무 손실률 (AAL) 분석
		공식: AAL(%) = Σ[확률 × 손상률 × (1-보험보전율)]

		Args:
			collected_data: 수집된 기후 데이터
			physical_risk_score: 물리적 리스크 점수 (선행 계산 결과)
			asset_info: 사업장 노출 자산 정보
				- insurance_coverage_rate: 보험보전율 (0.0 ~ 1.0, 기본값 0.0)

		Returns:
			AAL 분석 결과 딕셔너리
				- hazard_probability: P(H) 위험 발생 확률
				- damage_rate: 손상률 (0.0 ~ 1.0)
				- insurance_coverage_rate: 보험보전율 (0.0 ~ 1.0)
				- aal_percentage: 연평균 재무 손실률 (%) - 0.0 ~ 100.0
				- calculation_details: 계산 상세 내역
				- status: 분석 상태
		"""
		self.logger.info(f"{self.risk_type} AAL 분석 시작")

		try:
			# 1. P(H): 위험 발생 확률 계산
			hazard_probability = self.calculate_hazard_probability(collected_data, physical_risk_score)

			# 2. 손상률 계산
			damage_rate = self.calculate_damage_rate(collected_data, physical_risk_score, asset_info)

			# 3. 보험보전율 (기본값 0.0)
			insurance_coverage_rate = asset_info.get('insurance_coverage_rate', 0.0)

			# 4. AAL(%) 계산: AAL(%) = 확률 × 손상률 × (1 - 보험보전율) × 100
			aal_percentage = hazard_probability * damage_rate * (1 - insurance_coverage_rate) * 100

			result = {
				'risk_type': self.risk_type,
				'hazard_probability': round(hazard_probability, 4),
				'damage_rate': round(damage_rate, 4),
				'insurance_coverage_rate': round(insurance_coverage_rate, 4),
				'aal_percentage': round(aal_percentage, 4),  # % 단위
				'calculation_details': self._get_calculation_details(
					hazard_probability,
					damage_rate,
					insurance_coverage_rate,
					aal_percentage
				),
				'status': 'completed'
			}

			self.logger.info(
				f"{self.risk_type} AAL 분석 완료: "
				f"P(H)={hazard_probability:.4f}, Damage Rate={damage_rate:.4f}, "
				f"Insurance Coverage={insurance_coverage_rate:.4f}, "
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
	def calculate_hazard_probability(self, collected_data: Dict[str, Any], physical_risk_score: float) -> float:
		"""
		P(H): 위험 발생 확률 계산
		기후 데이터 및 물리적 리스크 점수 기반으로 연간 발생 확률 추정

		Args:
			collected_data: 수집된 기후 데이터
			physical_risk_score: 물리적 리스크 점수

		Returns:
			위험 발생 확률 (0.0 ~ 1.0)
		"""
		pass

	@abstractmethod
	def calculate_damage_rate(
		self,
		collected_data: Dict[str, Any],
		physical_risk_score: float,
		asset_info: Dict[str, Any]
	) -> float:
		"""
		손상률 계산
		리스크 발생 시 예상 자산 손상 비율

		Args:
			collected_data: 수집된 기후 데이터
			physical_risk_score: 물리적 리스크 점수
			asset_info: 사업장 노출 자산 정보

		Returns:
			손상률 (0.0 ~ 1.0)
		"""
		pass

	def _get_calculation_details(
		self,
		hazard_probability: float,
		damage_rate: float,
		insurance_coverage_rate: float,
		aal_percentage: float
	) -> Dict[str, Any]:
		"""
		계산 상세 내역 생성

		Args:
			hazard_probability: 위험 발생 확률
			damage_rate: 손상률
			insurance_coverage_rate: 보험보전율
			aal_percentage: 연평균 재무 손실률 (%)

		Returns:
			계산 상세 내역 딕셔너리
		"""
		return {
			'formula': 'AAL(%) = P(H) × 손상률 × (1 - 보험보전율) × 100',
			'components': {
				'P(H) (Hazard Probability)': round(hazard_probability, 4),
				'Damage Rate': round(damage_rate, 4),
				'Insurance Coverage Rate': round(insurance_coverage_rate, 4)
			},
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
		if aal_percentage < 1.0:  # 1% 미만
			return 'Minimal'
		if aal_percentage < 5.0:  # 5% 미만
			return 'Low'
		if aal_percentage < 10.0:  # 10% 미만
			return 'Moderate'
		if aal_percentage < 20.0:  # 20% 미만
			return 'High'
		return 'Critical'  # 20% 이상
