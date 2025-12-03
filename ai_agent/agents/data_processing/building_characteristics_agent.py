'''
파일명: building_characteristics_agent.py
최종 수정일: 2025-12-01
버전: v01
파일 개요: 건물 특징 분석 Agent (Node 2 - 병렬 독립 실행)
변경 이력:
	- 2025-12-01: v01 - 초기 생성 (Vulnerability Analysis에서 분리)

역할:
	- Node 5 (Integration) 이후 독립적으로 실행
	- Physical Risk Score와 AAL 결과를 받아서 건물 특징을 분석
	- LLM 기반 정성적 분석
	- "왜 이런 점수가 나왔는지" 해석
'''
from typing import Dict, Any
import logging


logger = logging.getLogger(__name__)


class BuildingCharacteristicsAgent:
	"""
	건물 특징 분석 Agent

	역할:
	- ModelOps에서 계산된 Physical Risk Score와 AAL 결과 해석
	- 건물의 구조적, 위치적, 기능적 특징 분석
	- LLM 기반 정성적 분석 제공
	- 리포트 체인과 완전히 독립적으로 실행

	입력:
	- building_info: 건물 정보
	- physical_risk_results: Node 3 결과 (9개 리스크별 점수)
	- aal_results: Node 4 결과 (9개 리스크별 AAL)
	- integrated_risk: Node 5 결과 (통합 리스크)

	출력:
	- building_characteristics: 건물 특징 분석 결과
		- structural_features: 구조적 특징
		- location_features: 위치적 특징
		- risk_interpretation: 리스크 점수 해석
		- vulnerability_factors: 주요 취약 요인
		- resilience_factors: 주요 회복력 요인
	"""

	def __init__(self, llm_client=None):
		"""
		BuildingCharacteristicsAgent 초기화

		Args:
			llm_client: LLM 클라이언트 (선택사항)
		"""
		self.logger = logger
		self.llm_client = llm_client
		self.logger.info("BuildingCharacteristicsAgent 초기화 완료")

	def analyze(
		self,
		building_info: Dict[str, Any],
		physical_risk_results: Dict[str, Any],
		aal_results: Dict[str, Any],
		integrated_risk: Dict[str, Any],
		additional_data_guideline: Dict[str, Any] = None
	) -> Dict[str, Any]:
		"""
		건물 특징 분석 수행

		Args:
			building_info: 건물 정보
			physical_risk_results: Physical Risk Score 결과
			aal_results: AAL 분석 결과
			integrated_risk: 통합 리스크 분석 결과
			additional_data_guideline: 추가 데이터 가이드라인 (선택)

		Returns:
			건물 특징 분석 결과
		"""
		self.logger.info("건물 특징 분석 시작")

		# 1. 구조적 특징 분석
		structural_features = self._analyze_structural_features(building_info)

		# 2. 위치적 특징 분석
		location_features = self._analyze_location_features(building_info)

		# 3. 리스크 점수 해석
		risk_interpretation = self._interpret_risk_scores(
			physical_risk_results,
			aal_results,
			integrated_risk
		)

		# 4. 취약 요인 추출
		vulnerability_factors = self._extract_vulnerability_factors(
			building_info,
			physical_risk_results,
			aal_results
		)

		# 5. 회복력 요인 추출
		resilience_factors = self._extract_resilience_factors(
			building_info,
			physical_risk_results
		)

		# 6. LLM 기반 종합 분석 (선택적)
		comprehensive_analysis = None
		if self.llm_client:
			try:
				comprehensive_analysis = self._llm_comprehensive_analysis(
					building_info,
					structural_features,
					location_features,
					risk_interpretation,
					vulnerability_factors,
					resilience_factors,
					additional_data_guideline
				)
			except Exception as e:
				self.logger.error(f"LLM 종합 분석 중 오류 발생: {str(e)}")
				# 오류 발생 시 기본 분석 결과 생성
				comprehensive_analysis = self._generate_fallback_analysis(
					structural_features,
					vulnerability_factors,
					resilience_factors,
					risk_interpretation
				)
		else:
			# LLM 클라이언트가 없을 경우 기본 분석 생성
			self.logger.warning("LLM 클라이언트가 없어 기본 분석 생성")
			comprehensive_analysis = self._generate_fallback_analysis(
				structural_features,
				vulnerability_factors,
				resilience_factors,
				risk_interpretation
			)

		result = {
			'structural_features': structural_features,
			'location_features': location_features,
			'risk_interpretation': risk_interpretation,
			'vulnerability_factors': vulnerability_factors,
			'resilience_factors': resilience_factors,
			'comprehensive_analysis': comprehensive_analysis,
			'analysis_metadata': {
				'agent': 'BuildingCharacteristicsAgent',
				'version': 'v01',
				'guideline_applied': additional_data_guideline is not None
			},
			'status': 'completed'  # 상태 추가
		}

		self.logger.info("건물 특징 분석 완료")
		return result

	def _analyze_structural_features(self, building_info: Dict) -> Dict:
		"""구조적 특징 분석 (building_info가 비어있을 수 있음)"""
		if not building_info:
			self.logger.warning("building_info가 비어있음. 기본값 사용")
			building_info = {}

		return {
			'building_age': building_info.get('building_age', 0),
			'structure_type': building_info.get('structure', 'Unknown'),
			'building_height': building_info.get('building_height', 0),
			'gross_floor_area': building_info.get('gross_floor_area', 0),
			'seismic_design': building_info.get('seismic_design', False),
			'fire_access': building_info.get('fire_access', 'Unknown'),
			'structural_grade': self._calculate_structural_grade(building_info)
		}

	def _analyze_location_features(self, building_info: Dict) -> Dict:
		"""위치적 특징 분석 (building_info가 비어있을 수 있음)"""
		if not building_info:
			building_info = {}

		location = building_info.get('location', {})
		return {
			'latitude': location.get('latitude', 0),
			'longitude': location.get('longitude', 0),
			'address': location.get('address', 'Unknown'),
			'region': location.get('region', 'Unknown'),
			'proximity_to_water': self._assess_water_proximity(location),
			'elevation': location.get('elevation', 0),
			'urban_density': location.get('urban_density', 'Medium')
		}

	def _interpret_risk_scores(
		self,
		physical_risk_results: Dict,
		aal_results: Dict,
		integrated_risk: Dict
	) -> Dict:
		"""리스크 점수 해석"""
		interpretations = {}

		# Physical Risk Score 해석
		for hazard_type, result in physical_risk_results.items():
			score = result.get('score', 0)
			level = result.get('level', 'Unknown')

			interpretation = self._interpret_single_risk(hazard_type, score, level)
			interpretations[hazard_type] = interpretation

		# AAL 해석 추가
		for hazard_type, aal_result in aal_results.items():
			aal_value = aal_result.get('aal', 0)
			if hazard_type in interpretations:
				interpretations[hazard_type]['aal_interpretation'] = self._interpret_aal(
					hazard_type,
					aal_value
				)

		# 통합 리스크 해석
		interpretations['integrated'] = {
			'overall_risk_level': integrated_risk.get('overall_level', 'Unknown'),
			'top_risks': integrated_risk.get('top_risks', []),
			'total_aal': integrated_risk.get('total_aal', 0),
			'interpretation': self._interpret_integrated_risk(integrated_risk)
		}

		return interpretations

	def _extract_vulnerability_factors(
		self,
		building_info: Dict,
		physical_risk_results: Dict,
		aal_results: Dict
	) -> list:
		"""주요 취약 요인 추출 (building_info가 비어있을 수 있음)"""
		factors = []

		if not building_info:
			building_info = {}

		# 건물 연식
		age = building_info.get('building_age', 0)
		if age > 30:
			factors.append({
				'factor': 'High Building Age',
				'value': age,
				'severity': 'High',
				'description': f'건물 연식이 {age}년으로 노후화 우려'
			})

		# 내진 설계 부재
		if not building_info.get('seismic_design', False):
			factors.append({
				'factor': 'No Seismic Design',
				'severity': 'High',
				'description': '내진 설계가 적용되지 않아 지진/태풍 취약'
			})

		# 고위험 리스크 추출
		for hazard_type, result in physical_risk_results.items():
			level = result.get('level', 'Unknown')
			if level in ['Very High', 'High']:
				factors.append({
					'factor': f'{hazard_type} Risk',
					'value': result.get('score', 0),
					'severity': level,
					'description': f'{hazard_type} 리스크가 {level} 수준'
				})

		return factors

	def _extract_resilience_factors(
		self,
		building_info: Dict,
		physical_risk_results: Dict
	) -> list:
		"""주요 회복력 요인 추출 (building_info가 비어있을 수 있음)"""
		factors = []

		if not building_info:
			building_info = {}

		# 내진 설계
		if building_info.get('seismic_design', False):
			factors.append({
				'factor': 'Seismic Design',
				'strength': 'High',
				'description': '내진 설계로 구조적 안정성 확보'
			})

		# 소방차 진입 가능
		fire_access = building_info.get('fire_access', 'Unknown')
		if fire_access == 'Easy':
			factors.append({
				'factor': 'Fire Access',
				'strength': 'Medium',
				'description': '소방차 진입이 용이하여 화재 대응 가능'
			})

		# 저위험 리스크
		low_risk_count = sum(
			1 for result in physical_risk_results.values()
			if result.get('level') in ['Low', 'Very Low']
		)

		if low_risk_count >= 5:
			factors.append({
				'factor': 'Low Risk Profile',
				'strength': 'High',
				'description': f'{low_risk_count}개 리스크가 저위험 수준'
			})

		return factors

	def _calculate_structural_grade(self, building_info: Dict) -> str:
		"""구조적 등급 계산"""
		score = 0

		# 건물 연식
		age = building_info.get('building_age', 0)
		if age < 10:
			score += 3
		elif age < 20:
			score += 2
		elif age < 30:
			score += 1

		# 내진 설계
		if building_info.get('seismic_design', False):
			score += 2

		# 구조 타입
		structure = building_info.get('structure', '').lower()
		if 'steel' in structure or 'rc' in structure:
			score += 2
		elif 'wood' in structure:
			score += 1

		# 등급 부여
		if score >= 6:
			return 'Excellent'
		elif score >= 4:
			return 'Good'
		elif score >= 2:
			return 'Fair'
		else:
			return 'Poor'

	def _assess_water_proximity(self, location: Dict) -> str:
		"""수계 근접성 평가 (향후 GIS 데이터 활용 가능)"""
		# 현재는 간단한 평가, 향후 GIS 데이터 연동 필요
		return 'Unknown'

	def _interpret_single_risk(self, hazard_type: str, score: float, level: str) -> Dict:
		"""개별 리스크 해석"""
		interpretation = {
			'hazard_type': hazard_type,
			'score': score,
			'level': level,
			'explanation': ''
		}

		if level == 'Very High':
			interpretation['explanation'] = f'{hazard_type} 리스크가 매우 높음. 즉각적인 대응 필요.'
		elif level == 'High':
			interpretation['explanation'] = f'{hazard_type} 리스크가 높음. 중장기 대응 계획 수립 권장.'
		elif level == 'Medium':
			interpretation['explanation'] = f'{hazard_type} 리스크가 중간 수준. 모니터링 필요.'
		elif level == 'Low':
			interpretation['explanation'] = f'{hazard_type} 리스크가 낮음. 정기 점검으로 충분.'
		else:
			interpretation['explanation'] = f'{hazard_type} 리스크가 매우 낮음.'

		return interpretation

	def _interpret_aal(self, hazard_type: str, aal_value: float) -> str:
		"""AAL 해석"""
		if aal_value > 100000000:  # 1억 이상
			return f'연평균 {aal_value/100000000:.1f}억원 손실 예상. 보험 및 재무 대응 필수.'
		elif aal_value > 10000000:  # 1천만 이상
			return f'연평균 {aal_value/10000000:.1f}천만원 손실 예상. 재무 계획 필요.'
		elif aal_value > 1000000:  # 100만 이상
			return f'연평균 {aal_value/1000000:.1f}백만원 손실 예상. 예비비 확보 권장.'
		else:
			return f'연평균 {aal_value:,.0f}원 손실 예상. 경미한 수준.'

	def _interpret_integrated_risk(self, integrated_risk: Dict) -> str:
		"""통합 리스크 해석"""
		overall_level = integrated_risk.get('overall_level', 'Unknown')
		top_risks = integrated_risk.get('top_risks', [])

		interpretation = f'전체 리스크 수준: {overall_level}. '

		if top_risks:
			top_3 = top_risks[:3]
			risk_names = ', '.join([r.get('hazard_type', 'Unknown') for r in top_3])
			interpretation += f'주요 리스크: {risk_names}. '

		return interpretation

	def _generate_fallback_analysis(
		self,
		structural_features: Dict,
		vulnerability_factors: list,
		resilience_factors: list,
		risk_interpretation: Dict
	) -> str:
		"""LLM 실패 시 기본 분석 생성"""
		analysis = "## 건물 특징 종합 분석\n\n"

		# 1. 건물 특징 요약
		analysis += "### 1. 건물 특징 요약\n"
		grade = structural_features.get('structural_grade', 'Unknown')
		age = structural_features.get('building_age', 0)
		structure = structural_features.get('structure_type', 'Unknown')
		analysis += f"이 건물은 {age}년차 {structure} 구조로, 구조적 등급은 {grade}입니다.\n\n"

		# 2. 주요 리스크 요인
		analysis += "### 2. 주요 리스크 요인\n"
		if vulnerability_factors:
			for factor in vulnerability_factors[:3]:  # Top 3
				analysis += f"- {factor.get('factor', 'Unknown')}: {factor.get('description', 'N/A')}\n"
		else:
			analysis += "- 특별한 취약 요인이 발견되지 않았습니다.\n"
		analysis += "\n"

		# 3. 건물의 강점
		analysis += "### 3. 건물의 강점\n"
		if resilience_factors:
			for factor in resilience_factors[:3]:  # Top 3
				analysis += f"- {factor.get('factor', 'Unknown')}: {factor.get('description', 'N/A')}\n"
		else:
			analysis += "- 구조적 강점이 제한적입니다.\n"
		analysis += "\n"

		# 4. 통합 리스크 요약
		analysis += "### 4. 종합 의견\n"
		integrated = risk_interpretation.get('integrated', {})
		overall_level = integrated.get('overall_risk_level', 'Unknown')
		top_risks = integrated.get('top_risks', [])
		if top_risks:
			top_3_names = ', '.join([r.get('hazard_type', 'Unknown') for r in top_risks[:3]])
			analysis += f"전체 리스크 수준은 {overall_level}이며, 주요 리스크는 {top_3_names}입니다. "
		analysis += "지속적인 모니터링과 적절한 대응 계획이 필요합니다.\n"

		return analysis

	def _llm_comprehensive_analysis(
		self,
		building_info: Dict,
		structural_features: Dict,
		location_features: Dict,
		risk_interpretation: Dict,
		vulnerability_factors: list,
		resilience_factors: list,
		additional_data_guideline: Dict = None
	) -> str:
		"""LLM 기반 종합 분석"""
		# 추가 데이터 가이드라인 적용 여부 확인
		relevance = 0.0
		suggested_insights = []

		if additional_data_guideline:
			relevance = additional_data_guideline.get('relevance', 0.0)
			suggested_insights = additional_data_guideline.get('suggested_insights', [])

		# relevance 0.4 미만이면 가이드라인 무시
		apply_guideline = relevance >= 0.4

		prompt = f"""당신은 건물 특징 분석 전문가입니다.

다음 정보를 바탕으로 건물의 종합적인 특징을 분석해주세요:

## 건물 기본 정보
- 건물 연식: {building_info.get('building_age', 0)}년
- 구조: {building_info.get('structure', 'Unknown')}
- 위치: {location_features.get('address', 'Unknown')}

## 구조적 특징
{structural_features}

## 리스크 분석 결과
{risk_interpretation}

## 취약 요인
{vulnerability_factors}

## 회복력 요인
{resilience_factors}

"""

		if apply_guideline and suggested_insights:
			prompt += f"""
## 추가 고려사항 (사용자 제공 데이터)
관련도: {relevance:.2f}
{chr(10).join([f'- {insight}' for insight in suggested_insights])}
"""

		prompt += """
다음 형식으로 종합 분석을 작성해주세요:

1. 건물 특징 요약 (3-5문장)
2. 주요 리스크 요인 (구체적으로)
3. 건물의 강점
4. 개선이 필요한 부분
5. 종합 의견
"""

		try:
			if self.llm_client:
				response = self.llm_client.invoke(prompt)
				self.logger.info(f"LLM 종합 분석 완료 (가이드라인 적용: {apply_guideline})")
				return response
			else:
				return "LLM 클라이언트 미설정"
		except Exception as e:
			self.logger.error(f"LLM 분석 실패: {str(e)}")
			return f"LLM 분석 실패: {str(e)}"
