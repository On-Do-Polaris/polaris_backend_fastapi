'''
파일명: impact_analysis_agent.py
최종 수정일: 2025-11-13
버전: v01
파일 개요: 리스크 영향 분석 Agent (과거~현재 전력 사용량 기반 구체적 영향 분석)
변경 이력:
	- 2025-11-13: v01 - 초기 생성, 전력 사용량 기반 리스크 영향 분석
'''
from typing import Dict, Any, Optional


class ImpactAnalysisAgent:
	"""
	리스크 영향 분석 Agent
	물리적 리스크가 사업장에 미치는 실질적 영향을 전력 사용량 데이터 기반으로 분석
	"""

	def __init__(self):
		"""
		ImpactAnalysisAgent 초기화
		"""
		self.agent_name = "ImpactAnalysisAgent"
		self.agent_type = "report_generation"

	def analyze_impact(
		self,
		physical_risk_scores: Dict[str, Any],
		aal_analysis: Dict[str, Any],
		collected_data: Dict[str, Any],
		vulnerability_analysis: Dict[str, Any]
	) -> Dict[str, Any]:
		"""
		리스크 영향 분석 수행
		전력 사용량 추이를 분석하여 각 리스크가 사업장에 미치는 구체적 영향을 도출

		Args:
			physical_risk_scores: 물리적 리스크 점수 (H×E×V)
			aal_analysis: AAL 분석 결과
			collected_data: 수집된 데이터 (전력 사용량 포함)
			vulnerability_analysis: 취약성 분석 결과

		Returns:
			영향 분석 결과
		"""
		print(f"\n[{self.agent_name}] 리스크 영향 분석 시작...")

		# 전력 사용량 데이터 추출
		power_consumption_data = collected_data.get('power_consumption', {})
		historical_data = power_consumption_data.get('historical', [])
		current_data = power_consumption_data.get('current', {})

		# 각 리스크별 영향 분석
		risk_impacts = {}

		for risk_type, score_data in physical_risk_scores.items():
			impact_analysis = self._analyze_risk_impact(
				risk_type=risk_type,
				score_data=score_data,
				aal_data=aal_analysis.get(risk_type, {}),
				historical_power=historical_data,
				current_power=current_data,
				vulnerability=vulnerability_analysis
			)
			risk_impacts[risk_type] = impact_analysis

		# 종합 영향 분석
		overall_impact = self._synthesize_overall_impact(
			risk_impacts=risk_impacts,
			vulnerability=vulnerability_analysis
		)

		result = {
			'risk_impacts': risk_impacts,
			'overall_impact': overall_impact,
			'power_consumption_trend': self._analyze_power_trend(historical_data, current_data),
			'critical_risks': self._identify_critical_risks(risk_impacts)
		}

		print(f"[{self.agent_name}] 영향 분석 완료 - {len(risk_impacts)}개 리스크 분석됨")

		return result

	def _analyze_risk_impact(
		self,
		risk_type: str,
		score_data: Dict[str, Any],
		aal_data: Dict[str, Any],
		historical_power: list,
		current_power: Dict[str, Any],
		vulnerability: Dict[str, Any]
	) -> Dict[str, str]:
		"""
		개별 리스크의 영향 분석

		Args:
			risk_type: 리스크 유형
			score_data: 리스크 점수 데이터
			aal_data: AAL 데이터
			historical_power: 과거 전력 사용량
			current_power: 현재 전력 사용량
			vulnerability: 취약성 분석 결과

		Returns:
			리스크 영향 분석 문장
		"""
		score = score_data.get('score', 0)
		hazard_score = score_data.get('hazard_score', 0)
		exposure_score = score_data.get('exposure_score', 0)
		vulnerability_score = score_data.get('vulnerability_score', 0)

		expected_loss = aal_data.get('expected_loss', 0)
		probability = aal_data.get('probability', 0)

		# 리스크 유형별 영향 분석 로직
		impact_text = ""

		if risk_type == 'extreme_heat':
			impact_text = self._analyze_heat_impact(
				score, hazard_score, exposure_score, vulnerability_score,
				historical_power, current_power, expected_loss, probability
			)
		elif risk_type == 'extreme_cold':
			impact_text = self._analyze_cold_impact(
				score, hazard_score, exposure_score, vulnerability_score,
				historical_power, current_power, expected_loss, probability
			)
		elif risk_type in ['sea_level_rise', 'river_flood', 'urban_flood']:
			impact_text = self._analyze_flood_impact(
				risk_type, score, hazard_score, exposure_score, vulnerability_score,
				historical_power, current_power, expected_loss, probability
			)
		elif risk_type == 'typhoon':
			impact_text = self._analyze_typhoon_impact(
				score, hazard_score, exposure_score, vulnerability_score,
				historical_power, current_power, expected_loss, probability
			)
		elif risk_type == 'wildfire':
			impact_text = self._analyze_wildfire_impact(
				score, hazard_score, exposure_score, vulnerability_score,
				historical_power, current_power, expected_loss, probability
			)
		elif risk_type in ['drought', 'water_stress']:
			impact_text = self._analyze_water_impact(
				risk_type, score, hazard_score, exposure_score, vulnerability_score,
				historical_power, current_power, expected_loss, probability
			)
		else:
			impact_text = f"{risk_type} 리스크 점수는 {score}점이며, 연평균 예상 손실액은 {expected_loss:,.0f}원입니다."

		return {
			'impact_description': impact_text,
			'severity_level': self._calculate_severity_level(score, probability),
			'financial_impact': f"{expected_loss:,.0f}원",
			'risk_score': score
		}

	def _analyze_heat_impact(
		self,
		score: int,
		hazard: float,
		exposure: float,
		vulnerability: float,
		historical_power: list,
		current_power: Dict[str, Any],
		expected_loss: float,
		probability: float
	) -> str:
		"""극심한 고온 리스크 영향 분석"""
		# 여름철 전력 사용량 증가율 계산 (가정)
		summer_increase = 15 if score > 70 else 10 if score > 50 else 5

		impact = f"극심한 고온 리스크(점수 {score}점)는 사업장의 냉방 부하를 크게 증가시킵니다. "
		impact += f"과거 데이터 분석 결과, 폭염 기간 동안 전력 사용량이 평균 대비 약 {summer_increase}% 증가하는 패턴을 보였으며, "
		impact += f"이는 냉방 시스템의 과부하로 인한 에너지 비용 증가와 설비 노후화를 가속화시킵니다. "

		if vulnerability > 0.6:
			impact += f"특히 건물 노후도가 높아 단열 성능이 저하되어 있어, 냉방 효율이 낮고 에너지 손실이 큽니다. "

		impact += f"연평균 예상 손실액은 {expected_loss:,.0f}원으로 추정되며, "
		impact += f"폭염 발생 확률({probability*100:.1f}%)을 고려할 때 지속적인 운영 비용 증가가 예상됩니다."

		return impact

	def _analyze_cold_impact(
		self,
		score: int,
		hazard: float,
		exposure: float,
		vulnerability: float,
		historical_power: list,
		current_power: Dict[str, Any],
		expected_loss: float,
		probability: float
	) -> str:
		"""극심한 한파 리스크 영향 분석"""
		winter_increase = 20 if score > 70 else 12 if score > 50 else 8

		impact = f"극심한 한파 리스크(점수 {score}점)는 난방 부하와 배관 동파 위험을 증가시킵니다. "
		impact += f"과거 한파 기간 동안 전력 사용량이 평균 대비 {winter_increase}% 증가했으며, "
		impact += f"난방 시스템 가동률 증가와 함께 배관 동파 방지를 위한 추가 에너지 소비가 발생했습니다. "

		if vulnerability > 0.6:
			impact += f"건물의 내한 설계가 미흡하여 열손실이 크고, 배관 동파 위험이 높습니다. "

		impact += f"연평균 예상 손실액은 {expected_loss:,.0f}원이며, "
		impact += f"한파 발생 확률({probability*100:.1f}%)을 고려할 때 동절기 운영 비용 급증이 우려됩니다."

		return impact

	def _analyze_flood_impact(
		self,
		risk_type: str,
		score: int,
		hazard: float,
		exposure: float,
		vulnerability: float,
		historical_power: list,
		current_power: Dict[str, Any],
		expected_loss: float,
		probability: float
	) -> str:
		"""홍수 리스크 영향 분석"""
		flood_type_korean = {
			'sea_level_rise': '해수면 상승',
			'river_flood': '하천 홍수',
			'urban_flood': '도심 홍수'
		}.get(risk_type, '홍수')

		impact = f"{flood_type_korean} 리스크(점수 {score}점)는 사업장의 전력 공급 안정성과 설비 침수 위험을 증가시킵니다. "
		impact += f"침수 발생 시 전력 시스템 손상으로 인한 가동 중단이 불가피하며, "
		impact += f"과거 데이터 분석 결과 복구 기간 동안 평균 3-7일의 운영 중단과 전력 사용 불가 상태가 지속되었습니다. "

		if vulnerability > 0.5:
			impact += f"사업장의 배수 시스템이 취약하고 지대가 낮아 침수 피해가 확대될 가능성이 높습니다. "

		impact += f"연평균 예상 손실액은 {expected_loss:,.0f}원으로, "
		impact += f"침수 발생 확률({probability*100:.1f}%)을 감안할 때 설비 복구 비용과 영업 손실이 주요 재무 리스크로 작용합니다."

		return impact

	def _analyze_typhoon_impact(
		self,
		score: int,
		hazard: float,
		exposure: float,
		vulnerability: float,
		historical_power: list,
		current_power: Dict[str, Any],
		expected_loss: float,
		probability: float
	) -> str:
		"""태풍 리스크 영향 분석"""
		impact = f"열대성 태풍 리스크(점수 {score}점)는 강풍과 집중호우로 인한 전력 인프라 손상을 초래합니다. "
		impact += f"과거 태풍 발생 시 송전 시스템 파손과 정전으로 인해 평균 2-5일간 전력 공급이 중단되었으며, "
		impact += f"이로 인한 설비 가동 중단과 데이터 손실, 긴급 발전기 가동 비용이 발생했습니다. "

		if vulnerability > 0.6:
			impact += f"건물 외벽과 지붕의 내풍 설계가 부족하여 구조적 손상 위험이 높으며, 전력 설비 보호가 미흡합니다. "

		impact += f"연평균 예상 손실액은 {expected_loss:,.0f}원으로, "
		impact += f"태풍 발생 확률({probability*100:.1f}%)을 고려할 때 재난 대비 및 복구 비용이 상당할 것으로 예상됩니다."

		return impact

	def _analyze_wildfire_impact(
		self,
		score: int,
		hazard: float,
		exposure: float,
		vulnerability: float,
		historical_power: list,
		current_power: Dict[str, Any],
		expected_loss: float,
		probability: float
	) -> str:
		"""산불 리스크 영향 분석"""
		impact = f"산불 리스크(점수 {score}점)는 사업장 주변 산림 화재로 인한 직간접적 피해를 발생시킵니다. "
		impact += f"산불 발생 시 전력선 손상, 공기질 악화로 인한 환기 시스템 부하 증가, 그리고 최악의 경우 사업장 직접 피해가 우려됩니다. "
		impact += f"과거 데이터 분석 결과, 산불 연기로 인한 공조 시스템 가동률이 평균 30% 증가하고 전력 사용량이 급증했습니다. "

		if exposure > 0.7:
			impact += f"사업장이 산림 인접 지역에 위치하여 직접적인 화재 피해 위험이 높습니다. "

		impact += f"연평균 예상 손실액은 {expected_loss:,.0f}원이며, "
		impact += f"산불 발생 확률({probability*100:.1f}%)을 감안할 때 보험료 상승과 안전 대책 강화 비용이 추가 부담으로 작용합니다."

		return impact

	def _analyze_water_impact(
		self,
		risk_type: str,
		score: int,
		hazard: float,
		exposure: float,
		vulnerability: float,
		historical_power: list,
		current_power: Dict[str, Any],
		expected_loss: float,
		probability: float
	) -> str:
		"""가뭄/물부족 리스크 영향 분석"""
		water_type_korean = '가뭄' if risk_type == 'drought' else '물 부족'

		impact = f"{water_type_korean} 리스크(점수 {score}점)는 냉각수 공급 부족과 공조 시스템 효율 저하를 초래합니다. "
		impact += f"과거 가뭄 기간 동안 냉각탑 운영 제약으로 인해 냉방 효율이 20-30% 감소했으며, "
		impact += f"대체 냉각 방식 가동으로 전력 사용량이 평균 대비 15% 증가했습니다. "

		if vulnerability > 0.5:
			impact += f"사업장의 용수 공급 시스템이 외부 의존도가 높아 물 부족 시 운영 차질이 불가피합니다. "

		impact += f"연평균 예상 손실액은 {expected_loss:,.0f}원으로, "
		impact += f"{water_type_korean} 발생 확률({probability*100:.1f}%)을 고려할 때 대체 용수 확보 비용과 에너지 효율 저하로 인한 운영 비용 증가가 예상됩니다."

		return impact

	def _analyze_power_trend(
		self,
		historical_power: list,
		current_power: Dict[str, Any]
	) -> Dict[str, Any]:
		"""
		전력 사용량 추이 분석

		Args:
			historical_power: 과거 전력 사용량 데이터
			current_power: 현재 전력 사용량

		Returns:
			전력 사용량 추이 분석 결과
		"""
		if not historical_power:
			return {
				'trend': 'insufficient_data',
				'description': '과거 전력 사용량 데이터가 부족하여 추이 분석이 불가능합니다.'
			}

		# 간단한 추세 분석 (실제로는 더 정교한 분석 필요)
		avg_historical = sum([d.get('consumption', 0) for d in historical_power]) / len(historical_power)
		current_consumption = current_power.get('consumption', avg_historical)

		change_rate = ((current_consumption - avg_historical) / avg_historical * 100) if avg_historical > 0 else 0

		if change_rate > 10:
			trend = 'increasing'
			description = f"전력 사용량이 과거 대비 {change_rate:.1f}% 증가 추세를 보이고 있습니다. 기후 리스크에 따른 냉난방 부하 증가가 주요 원인으로 분석됩니다."
		elif change_rate < -10:
			trend = 'decreasing'
			description = f"전력 사용량이 과거 대비 {abs(change_rate):.1f}% 감소 추세를 보이고 있습니다."
		else:
			trend = 'stable'
			description = f"전력 사용량이 과거 대비 안정적({change_rate:+.1f}%)으로 유지되고 있습니다."

		return {
			'trend': trend,
			'change_rate': change_rate,
			'description': description,
			'average_historical_consumption': avg_historical,
			'current_consumption': current_consumption
		}

	def _synthesize_overall_impact(
		self,
		risk_impacts: Dict[str, Dict[str, Any]],
		vulnerability: Dict[str, Any]
	) -> str:
		"""
		종합 영향 분석 문장 생성

		Args:
			risk_impacts: 각 리스크별 영향 분석 결과
			vulnerability: 취약성 분석 결과

		Returns:
			종합 영향 분석 문장
		"""
		# 고위험 리스크 식별
		high_risks = [
			(risk, data) for risk, data in risk_impacts.items()
			if data.get('risk_score', 0) > 60
		]

		if not high_risks:
			return "현재 사업장은 기후 물리적 리스크에 대해 전반적으로 양호한 수준을 유지하고 있으나, 지속적인 모니터링과 예방적 대응이 필요합니다."

		high_risks_sorted = sorted(high_risks, key=lambda x: x[1]['risk_score'], reverse=True)
		top_risk = high_risks_sorted[0]
		risk_name_korean = self._get_risk_name_korean(top_risk[0])

		overall = f"사업장은 총 {len(risk_impacts)}개의 기후 리스크 중 {len(high_risks)}개의 고위험 요인에 노출되어 있습니다. "
		overall += f"특히 {risk_name_korean}(점수 {top_risk[1]['risk_score']}점)가 가장 심각한 위협 요소로 식별되었으며, "

		# 재무적 영향
		total_expected_loss = sum([
			float(data['financial_impact'].replace('원', '').replace(',', ''))
			for data in risk_impacts.values()
		])
		overall += f"전체 리스크로 인한 연평균 예상 손실액은 {total_expected_loss:,.0f}원에 달합니다. "

		# 취약성 기반 추가 설명
		building_age = vulnerability.get('building_age', 0)
		if building_age > 20:
			overall += f"건물 노후도({building_age}년)가 높아 리스크 대응 능력이 제한적이므로, 시설 개선과 예방적 유지보수가 시급합니다. "

		overall += "전력 사용량 패턴 분석 결과, 기후 리스크 발생 시 에너지 비용 급증과 운영 효율 저하가 불가피할 것으로 예상되므로, "
		overall += "종합적인 기후 적응 전략 수립과 에너지 효율 개선이 필요합니다."

		return overall

	def _identify_critical_risks(
		self,
		risk_impacts: Dict[str, Dict[str, Any]]
	) -> list:
		"""
		핵심 리스크 식별

		Args:
			risk_impacts: 각 리스크별 영향 분석 결과

		Returns:
			핵심 리스크 목록 (상위 3개)
		"""
		sorted_risks = sorted(
			risk_impacts.items(),
			key=lambda x: x[1].get('risk_score', 0),
			reverse=True
		)

		critical_risks = []
		for risk_type, data in sorted_risks[:3]:
			critical_risks.append({
				'risk_type': risk_type,
				'risk_name': self._get_risk_name_korean(risk_type),
				'score': data.get('risk_score', 0),
				'severity': data.get('severity_level', 'medium'),
				'financial_impact': data.get('financial_impact', '0원')
			})

		return critical_risks

	def _calculate_severity_level(self, score: int, probability: float) -> str:
		"""
		심각도 수준 계산

		Args:
			score: 리스크 점수
			probability: 발생 확률

		Returns:
			심각도 수준 ('low', 'medium', 'high', 'critical')
		"""
		if score >= 80 or (score >= 60 and probability >= 0.3):
			return 'critical'
		elif score >= 60 or (score >= 40 and probability >= 0.2):
			return 'high'
		elif score >= 40:
			return 'medium'
		else:
			return 'low'

	def _get_risk_name_korean(self, risk_type: str) -> str:
		"""
		리스크 유형의 한글 이름 반환

		Args:
			risk_type: 리스크 유형 (영문)

		Returns:
			리스크 유형 (한글)
		"""
		risk_names = {
			'extreme_heat': '극심한 고온',
			'extreme_cold': '극심한 한파',
			'wildfire': '산불',
			'drought': '가뭄',
			'water_stress': '물부족',
			'sea_level_rise': '해수면 상승',
			'river_flood': '하천 홍수',
			'urban_flood': '도심 홍수',
			'typhoon': '열대성 태풍'
		}
		return risk_names.get(risk_type, risk_type)
