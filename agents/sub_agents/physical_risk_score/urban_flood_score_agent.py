'''
파일명: urban_flood_score_agent.py
최종 수정일: 2025-11-11
버전: v01
파일 개요: 도심 홍수 리스크 물리적 종합 점수 산출 Agent
변경 이력:
	- 2025-11-11: v01 - AAL×자산가치 방식으로 변경 (H×E×V 제거)
'''
from agents.sub_agents.physical_risk_score.base_physical_risk_score_agent import BasePhysicalRiskScoreAgent


class UrbanFloodScoreAgent(BasePhysicalRiskScoreAgent):
	"""
	도심 홍수 리스크 물리적 종합 점수 산출 Agent
	AAL(%) × 사업장 자산 가치를 기반으로 재무 손실액 계산
	"""

	def __init__(self):
		"""
		UrbanFloodScoreAgent 초기화
		"""
		super().__init__(risk_type='urban_flood')
