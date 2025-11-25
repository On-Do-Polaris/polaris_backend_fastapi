'''
파일명: typhoon_aal_agent.py
최종 수정일: 2025-11-21
버전: v10
파일 개요: 태풍 리스크 AAL 분석 Agent
변경 이력:
	- 2025-11-21: v10 - V 스케일링과 최종 AAL 계산만 수행
		* P(H) 및 기본 손상률 계산 제거
		* 외부에서 입력받은 데이터로 AAL 계산
'''
from .base_aal_analysis_agent import BaseAALAnalysisAgent


class TyphoonAALAgent(BaseAALAnalysisAgent):
	"""
	태풍 리스크 AAL 분석 Agent
	V 스케일링과 최종 AAL 계산만 수행
	"""

	def __init__(self):
		super().__init__(
			risk_type='태풍',
			insurance_rate=0.0
		)
