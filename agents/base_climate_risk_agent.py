'''
파일명: base_climate_risk_agent.py
최종 수정일: 2025-11-05
버전: v00
파일 개요: 기후 리스크 에이전트 추상 베이스 클래스 정의
'''
from abc import ABC, abstractmethod
from typing import Dict, Any


class BaseClimateRiskAgent(ABC):
	"""
	기후 리스크 에이전트 추상 베이스 클래스
	모든 기후 리스크 에이전트는 이 클래스를 상속받아 구현

	리스크 계산 공식: Risk Score = Hazard * Exposure * Vulnerability
	"""

	def __init__(self, config):
		"""
		기후 리스크 에이전트 초기화

		Args:
			config: 설정 객체
		"""
		self.config = config
		self.risk_name = self.__class__.__name__.replace('RiskAgent', '')

	def calculate_risk(self, data: Dict, ssp_weights: Dict[str, float]) -> Dict[str, Any]:
		"""
		전체 리스크 스코어 계산
		H(Hazard) * E(Exposure) * V(Vulnerability) 공식 적용

		Args:
			data: 수집된 기후 데이터
			ssp_weights: SSP 시나리오별 가중치

		Returns:
			리스크 분석 결과 딕셔너리 (risk_type, hazard, exposure, vulnerability, risk_score, details 포함)
		"""
		print(f"  [{self.risk_name}] Risk calculation processing...")

		# Hazard, Exposure, Vulnerability 각각 계산
		hazard_score = self.calculate_hazard(data, ssp_weights)
		exposure_score = self.calculate_exposure(data)
		vulnerability_score = self.calculate_vulnerability(data)

		# Risk Score = H * E * V
		risk_score = hazard_score * exposure_score * vulnerability_score

		result = {
			'risk_type': self.risk_name,
			'hazard': hazard_score,
			'exposure': exposure_score,
			'vulnerability': vulnerability_score,
			'risk_score': risk_score,
			'details': self._get_detailed_analysis(data, ssp_weights)
		}

		return result

	@abstractmethod
	def calculate_hazard(self, data: Dict, ssp_weights: Dict[str, float]) -> float:
		"""
		Hazard (위해성) 지수 계산
		기후 현상의 강도와 빈도를 평가하고 SSP 시나리오별 가중치 적용

		Args:
			data: 수집된 기후 데이터
			ssp_weights: SSP 시나리오별 가중치

		Returns:
			Hazard 스코어 (0-1 범위)
		"""
		pass

	@abstractmethod
	def calculate_exposure(self, data: Dict) -> float:
		"""
		Exposure (노출도) 지수 계산
		자산, 인구, 인프라의 위치와 규모를 평가하고 리스크 영향 범위 내 노출 정도 계산

		Args:
			data: 수집된 기후 데이터

		Returns:
			Exposure 스코어 (0-1 범위)
		"""
		pass

	@abstractmethod
	def calculate_vulnerability(self, data: Dict) -> float:
		"""
		Vulnerability (취약성) 지수 계산
		적응 능력, 민감도, 대응 역량 평가

		Args:
			data: 수집된 기후 데이터

		Returns:
			Vulnerability 스코어 (0-1 범위)
		"""
		pass

	def _get_detailed_analysis(self, data: Dict, ssp_weights: Dict[str, float]) -> Dict:
		"""
		상세 분석 정보 생성 (하위 클래스에서 선택적 구현)

		Args:
			data: 수집된 기후 데이터
			ssp_weights: SSP 시나리오별 가중치

		Returns:
			상세 분석 결과 딕셔너리
		"""
		return {}

	def _normalize_score(self, score: float, min_val: float = 0.0, max_val: float = 1.0) -> float:
		"""
		스코어 정규화 (0-1 범위로 제한)

		Args:
			score: 정규화할 스코어
			min_val: 최소값 (기본값: 0.0)
			max_val: 최대값 (기본값: 1.0)

		Returns:
			정규화된 스코어 (min_val ~ max_val 범위)
		"""
		if score < min_val:
			return min_val
		if score > max_val:
			return max_val
		return score
