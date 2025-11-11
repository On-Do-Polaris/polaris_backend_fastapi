'''
파일명: base_physical_risk_score_agent.py
최종 수정일: 2025-11-11
버전: v01
파일 개요: 물리적 리스크 종합 점수 산출 베이스 Agent (AAL × 자산가치 기반)
변경 이력:
	- 2025-11-11: v01 - H×E×V 방식에서 AAL×자산가치 방식으로 변경
'''
from typing import Dict, Any
from abc import ABC
import logging


logger = logging.getLogger(__name__)


class BasePhysicalRiskScoreAgent(ABC):
	"""
	물리적 리스크 종합 점수 산출 베이스 Agent
	AAL(%) × 사업장 자산 가치를 기반으로 재무 손실액 계산 후 100점 스케일로 변환
	"""

	def __init__(self, risk_type: str):
		"""
		BasePhysicalRiskScoreAgent 초기화

		Args:
			risk_type: 리스크 타입 (예: 'high_temperature', 'typhoon')
		"""
		self.risk_type = risk_type
		self.logger = logger
		self.logger.info(f"{risk_type} Physical Risk Score Agent 초기화")

	def calculate_physical_risk_score(
		self,
		aal_percentage: float,
		asset_info: Dict[str, Any]
	) -> Dict[str, Any]:
		"""
		물리적 리스크 종합 점수 계산 (AAL × 자산가치)

		Args:
			aal_percentage: AAL 퍼센트 (0.0 ~ 100.0)
			asset_info: 사업장 자산 정보
				- total_asset_value: 총 자산 가치 (원)

		Returns:
			물리적 리스크 종합 점수 딕셔너리
				- risk_type: 리스크 타입
				- aal_percentage: AAL 퍼센트
				- total_asset_value: 총 자산 가치
				- financial_loss: 연평균 재무 손실액 (원)
				- physical_risk_score_100: 100점 스케일 점수
				- risk_level: 위험 등급
				- status: 계산 상태
		"""
		self.logger.info(f"{self.risk_type} Physical Risk Score 계산 시작 (AAL: {aal_percentage}%)")

		try:
			# 1. 총 자산 가치 추출
			total_asset_value = asset_info.get('total_asset_value', 0)

			if total_asset_value == 0:
				self.logger.warning(f"{self.risk_type}: 자산 가치가 0입니다.")
				return {
					'risk_type': self.risk_type,
					'status': 'failed',
					'error': '자산 가치가 0입니다.'
				}

			# 2. 재무 손실액 계산: AAL(%) × 총 자산 가치
			financial_loss = (aal_percentage / 100.0) * total_asset_value

			# 3. 100점 스케일 변환
			# 기준: 10억원 손실 = 100점
			# 점수 = min(재무손실액 / 10억 * 100, 100)
			normalization_base = 1_000_000_000  # 10억원
			physical_risk_score_100 = min((financial_loss / normalization_base) * 100, 100.0)

			# 4. 위험 등급 산출
			risk_level = self.get_risk_level(physical_risk_score_100)

			result = {
				'risk_type': self.risk_type,
				'aal_percentage': round(aal_percentage, 4),
				'total_asset_value': total_asset_value,
				'financial_loss': round(financial_loss, 2),
				'physical_risk_score_100': round(physical_risk_score_100, 2),
				'risk_level': risk_level,
				'status': 'completed'
			}

			self.logger.info(
				f"{self.risk_type} Physical Risk Score 계산 완료: "
				f"{physical_risk_score_100:.2f}/100 (재무손실: {financial_loss:,.0f}원)"
			)
			return result

		except Exception as e:
			self.logger.error(f"{self.risk_type} Physical Risk Score 계산 중 오류: {str(e)}", exc_info=True)
			return {
				'risk_type': self.risk_type,
				'status': 'failed',
				'error': str(e)
			}

	def get_risk_level(self, physical_risk_score_100: float) -> str:
		"""
		물리적 리스크 점수에 따른 위험 등급 반환

		Args:
			physical_risk_score_100: 물리적 리스크 종합 점수 (0 ~ 100)

		Returns:
			위험 등급 문자열
				- 'Very High': 80 이상
				- 'High': 60 ~ 80
				- 'Medium': 40 ~ 60
				- 'Low': 20 ~ 40
				- 'Very Low': 20 미만
		"""
		if physical_risk_score_100 >= 80:
			return 'Very High'
		elif physical_risk_score_100 >= 60:
			return 'High'
		elif physical_risk_score_100 >= 40:
			return 'Medium'
		elif physical_risk_score_100 >= 20:
			return 'Low'
		else:
			return 'Very Low'

	def get_recommendation(self, physical_risk_score_100: float) -> str:
		"""
		물리적 리스크 점수에 따른 권고사항 생성

		Args:
			physical_risk_score_100: 물리적 리스크 종합 점수 (0 ~ 100)

		Returns:
			권고사항 문자열
		"""
		risk_level = self.get_risk_level(physical_risk_score_100)

		recommendations = {
			'Very High': f'{self.risk_type} 리스크에 대한 즉각적인 대응 조치가 필요합니다. 비상 대응 계획을 수립하고 정기적 모니터링을 실시하세요.',
			'High': f'{self.risk_type} 리스크가 높습니다. 예방적 조치를 강화하고 대응 체계를 점검하세요.',
			'Medium': f'{self.risk_type} 리스크를 지속적으로 모니터링하고 필요시 대응 방안을 마련하세요.',
			'Low': f'{self.risk_type} 리스크는 낮으나 정기적인 모니터링이 필요합니다.',
			'Very Low': f'{self.risk_type} 리스크는 매우 낮지만 기후 변화 추세를 주시하세요.'
		}

		return recommendations.get(risk_level, '정기적인 리스크 재평가가 필요합니다.')
