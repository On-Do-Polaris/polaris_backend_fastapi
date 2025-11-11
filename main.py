'''
파일명: main.py
최종 수정일: 2025-11-11
버전: v03
파일 개요: SKAX 물리적 리스크 분석 메인 오케스트레이터 (Super Agent 계층 구조)
변경 이력:
	- 2025-11-05: v00 - 초기 LangGraph 구조
	- 2025-11-11: v03 - Super Agent 계층 구조로 전면 개편
'''
from config.settings import Config
from workflow import create_workflow_graph, print_workflow_structure


class SKAXPhysicalRiskAnalyzer:
	"""
	SKAX 물리적 리스크 분석 메인 오케스트레이터
	Super Agent 계층 구조: 18개 Sub Agent (AAL 9개 + Physical Risk Score 9개)
	"""

	def __init__(self, config: Config):
		"""
		분석기 초기화

		Args:
			config: 설정 객체
		"""
		self.config = config

		# LangGraph 워크플로우 생성
		print("[INFO] LangGraph workflow creating (Super Agent structure)...")
		self.workflow_graph = create_workflow_graph(config)
		print("[INFO] Workflow creation completed (9 Nodes, 18 Sub Agents)")

	def analyze(
		self,
		target_location: dict,
		building_info: dict,
		asset_info: dict,
		analysis_params: dict
	) -> dict:
		"""
		전체 물리적 리스크 분석 실행

		Args:
			target_location: 분석 대상 위치 정보
				- latitude: 위도
				- longitude: 경도
				- name: 위치명
			building_info: 건물 정보
				- building_age: 건물 연식 (년)
				- has_seismic_design: 내진 설계 여부 (bool)
				- fire_access: 소방차 진입 가능 여부 (bool)
			asset_info: 자산 정보
				- total_asset_value: 총 자산 가치 (원)
				- insurance_coverage_rate: 보험보전율 (0.0 ~ 1.0)
			analysis_params: 분석 파라미터
				- time_horizon: 분석 시점 (예: '2050')
				- analysis_period: 분석 기간 (예: '2025-2050')

		Returns:
			분석 결과 딕셔너리
				- vulnerability_analysis: 취약성 분석 결과
				- aal_analysis: AAL 분석 결과 (9개 리스크)
				- physical_risk_scores: 물리적 리스크 점수 (9개 리스크, 100점 스케일)
				- report_template: 보고서 내용 구조 템플릿
				- response_strategy: 대응 전략
				- generated_report: 최종 보고서
				- validation_result: 검증 결과
				- workflow_status: 워크플로우 상태
		"""
		print("\n" + "=" * 70)
		print("SKAX Physical Risk Analysis Start (Super Agent Structure)")
		print("=" * 70)

		# 초기 상태 설정
		initial_state = {
			'target_location': target_location,
			'building_info': building_info,
			'asset_info': asset_info,
			'analysis_params': analysis_params,
			'errors': [],
			'logs': [],
			'current_step': 'data_collection',
			'workflow_status': 'in_progress',
			'retry_count': 0
		}

		# 워크플로우 실행
		print("\n[INFO] Workflow executing...\n")

		try:
			# LangGraph 실행 (스트리밍 모드)
			final_state = None
			for state in self.workflow_graph.stream(initial_state):
				# 중간 상태 출력 (디버그 모드)
				if self.config.DEBUG:
					print(f"  > Current step: {state}")
				final_state = state

			# 최종 상태 추출
			if final_state:
				# 마지막 노드의 상태 가져오기
				last_node_key = list(final_state.keys())[-1]
				result = final_state[last_node_key]

				print("\n" + "=" * 70)
				print("Workflow execution completed")
				print("=" * 70)

				# 결과 요약 출력
				self._print_summary(result)

				return result
			else:
				raise Exception("No workflow execution result")

		except Exception as e:
			print(f"\n[ERROR] Workflow execution failed: {e}")
			return {
				'workflow_status': 'failed',
				'errors': [str(e)]
			}

	def _print_summary(self, result: dict):
		"""
		분석 결과 요약 출력

		Args:
			result: 분석 결과 딕셔너리
		"""
		print("\n[RESULT] Analysis Result Summary:")
		print("-" * 70)

		# 워크플로우 상태
		status = result.get('workflow_status', 'unknown')
		print(f"Status: {status}")

		# 로그
		logs = result.get('logs', [])
		if logs:
			print(f"\n[OK] Completed steps: {len(logs)}")
			for log in logs:
				print(f"  - {log}")

		# 에러
		errors = result.get('errors', [])
		if errors:
			print(f"\n[WARN] Errors: {len(errors)}")
			for error in errors:
				print(f"  - {error}")

		# 물리적 리스크 점수
		physical_risk_scores = result.get('physical_risk_scores', {})
		if physical_risk_scores:
			print(f"\n[SCORE] Physical Risk Scores (100-point scale):")
			sorted_risks = sorted(
				physical_risk_scores.items(),
				key=lambda x: x[1].get('physical_risk_score_100', 0),
				reverse=True
			)
			for risk_type, risk_data in sorted_risks[:5]:
				score = risk_data.get('physical_risk_score_100', 0)
				level = risk_data.get('risk_level', 'Unknown')
				financial_loss = risk_data.get('financial_loss', 0)
				print(f"  {risk_type}: {score:.2f}/100 ({level}) - Loss: {financial_loss:,.0f}원")

		# 검증 결과
		validation_result = result.get('validation_result', {})
		if validation_result:
			is_valid = validation_result.get('is_valid', False)
			print(f"\n[VALIDATION] Valid: {is_valid}")

		# 리포트
		report = result.get('generated_report')
		if report:
			print(f"\n[REPORT] Report generated successfully")

		print("-" * 70)

	def visualize(self, output_path: str = "workflow_graph.png"):
		"""
		워크플로우 시각화

		Args:
			output_path: 출력 파일 경로 (기본값: workflow_graph.png)
		"""
		from workflow import visualize_workflow
		visualize_workflow(self.workflow_graph, output_path)

	def print_structure(self):
		"""
		워크플로우 구조 텍스트 출력
		"""
		print_workflow_structure()


def main():
	"""
	메인 실행 함수
	전체 분석 프로세스 실행 및 시각화

	Returns:
		분석 결과 딕셔너리
	"""
	# 설정 로드
	config = Config()

	# 분석기 초기화
	analyzer = SKAXPhysicalRiskAnalyzer(config)

	# 워크플로우 구조 출력
	print("\n")
	analyzer.print_structure()

	# 분석 대상 위치 설정 (예시)
	target_location = {
		'latitude': 37.5665,
		'longitude': 126.9780,
		'name': 'Seoul, South Korea'
	}

	# 건물 정보 설정
	building_info = {
		'building_age': 25,
		'has_seismic_design': True,
		'fire_access': True
	}

	# 자산 정보 설정
	asset_info = {
		'total_asset_value': 50000000000,  # 500억원
		'insurance_coverage_rate': 0.7      # 보험보전율 70%
	}

	# 분석 파라미터 설정
	analysis_params = {
		'time_horizon': '2050',
		'analysis_period': '2025-2050'
	}

	# 분석 실행
	results = analyzer.analyze(target_location, building_info, asset_info, analysis_params)

	# 워크플로우 시각화
	print("\n[INFO] Workflow graph generating...")
	try:
		analyzer.visualize("workflow_graph.png")
	except Exception as e:
		print(f"[ERROR] Visualization failed: {e}")

	return results


if __name__ == "__main__":
	main()
