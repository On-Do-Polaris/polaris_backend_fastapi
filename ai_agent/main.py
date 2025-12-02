'''
파일명: main.py
최종 수정일: 2025-12-01
버전: v08
파일 개요: SKAX 물리적 리스크 분석 메인 오케스트레이터 (Super Agent 계층 구조 + Fork-Join 병렬)
변경 이력:
	- 2025-11-05: v00 - 초기 LangGraph 구조
	- 2025-11-11: v03 - Super Agent 계층 구조로 전면 개편
	- 2025-11-13: v04 - 물리적 리스크 점수를 H×E×V 방식으로 복원, AAL과 병렬 실행
	- 2025-11-17: v05 - LangSmith 트레이싱 통합
	- 2025-11-25: v06 - LangSmith 트레이싱 데코레이터 적용
	- 2025-11-25: v07 - AAL Agent v11 호환 (_print_summary에서 final_aal_percentage 사용)
	- 2025-12-01: v08 - Fork-Join 병렬 구조 적용 (Node 5 이후 2 ∥ [6→7→8→9])
	                   - Building Characteristics Agent 추가 (Node 2)
	                   - Additional Data API 통합
	                   - vulnerability_analysis 노드 삭제 (ModelOps가 V 계산)
'''
from .config.settings import Config
from .workflow import create_workflow_graph, print_workflow_structure
from .utils.langsmith_tracer import get_tracer
from datetime import datetime
import logging

# LangSmith traceable 임포트
try:
	from langsmith import traceable
except ImportError:
	# LangSmith 미설치 시 no-op 데코레이터
	def traceable(*args, **kwargs):
		def decorator(func):
			return func
		return decorator


class SKAXPhysicalRiskAnalyzer:
	"""
	SKAX 물리적 리스크 분석 메인 오케스트레이터
	Super Agent 계층 구조: 26개 Agent (Fork-Join 병렬)

	구조:
	- Data Processing (2개): 데이터 수집, 건물 특징 분석
	- Physical Risk Score (9개): H×E×V 기반 리스크 점수 계산 (ModelOps)
	- AAL Analysis (9개): 확률×손상률 기반 재무 손실률 계산 (ModelOps)
	- Report Generation (5개): 템플릿, 영향 분석, 전략, 생성, 검증

	병렬 실행:
	- Node 2 ∥ Node 3: Physical Risk Score와 AAL 병렬 실행 (ModelOps)
	- Node BC ∥ Nodes 5-8: Building Characteristics와 Report Chain 병렬 실행
	- Node 9에서 병합 후 Node 10에서 최종화
	"""

	def __init__(self, config: Config):
		"""
		분석기 초기화

		Args:
			config: 설정 객체
		"""
		self.config = config
		self.logger = logging.getLogger("ai_agent.orchestrator")

		# LangSmith Tracer 초기화
		self.tracer = get_tracer(config)

		# LangGraph 워크플로우 생성
		print("[INFO] LangGraph workflow creating (Super Agent structure with Fork-Join)...")
		self.logger.info("Creating LangGraph workflow (Super Agent structure with Fork-Join)")
		self.workflow_graph = create_workflow_graph(config)
		print("[INFO] Workflow creation completed (11 Nodes, 25 Agents, Fork-Join Parallel Execution)")
		self.logger.info("Workflow creation completed (11 Nodes, 25 Agents, Fork-Join Parallel Execution)")

	@traceable(name="skax_physical_risk_analyze", tags=["workflow", "main", "orchestrator"])
	def analyze(
		self,
		target_location: dict,
		building_info: dict,
		asset_info: dict,
		analysis_params: dict,
		additional_data: dict = None,
		language: str = 'ko'
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
			additional_data: 추가 데이터 (선택사항)
				- raw_text: 자유 형식 텍스트
				- metadata: 메타데이터
			language: 보고서 언어 ('ko' 또는 'en', 기본값: 'ko')

		Returns:
			분석 결과 딕셔너리
				- physical_risk_scores: 물리적 리스크 점수 (9개, H×E×V 기반, ModelOps)
				- aal_analysis: AAL 분석 결과 (9개, 확률×손상률 기반, ModelOps)
				- integrated_risks: 통합 리스크 분석 결과
				- building_characteristics: 건물 특징 분석 결과 (LLM 기반 정성 분석)
				- report_template: 보고서 내용 구조 템플릿
				- impact_analysis: 영향 분석 결과
				- response_strategy: 대응 전략
				- generated_report: 최종 보고서
				- validation_result: 검증 결과
				- workflow_status: 워크플로우 상태
		"""
		print("\n" + "=" * 70)
		print("SKAX Physical Risk Analysis Start (Super Agent Structure)")
		print("=" * 70)

		# 실행 시작 시간 기록
		workflow_start_time = datetime.now()

		# 초기 상태 설정
		initial_state = {
			'target_location': target_location,
			'building_info': building_info,
			'asset_info': asset_info,
			'analysis_params': analysis_params,
			'language': language,
			'errors': [],
			'logs': [],
			'current_step': 'data_collection',
			'workflow_status': 'in_progress',
			'retry_count': 0,
			'_workflow_start_time': workflow_start_time.isoformat()
		}

		# 추가 데이터가 있으면 state에 추가
		if additional_data:
			initial_state['additional_data'] = additional_data

		# 추가 데이터 전처리 (워크플로우 외부에서 독립적으로 실행)
		initial_state = self._preprocess_additional_data(initial_state)

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

				# 워크플로우 실행 시간 계산
				workflow_execution_time = (datetime.now() - workflow_start_time).total_seconds()

				print("\n" + "=" * 70)
				print("Workflow execution completed")
				print("=" * 70)

				# LangSmith 메트릭 기록
				self.tracer.log_metric(
					metric_name="workflow_execution_time",
					value=workflow_execution_time,
					metadata={
						'total_nodes': 11,
						'total_agents': 25,
						'location': target_location.get('name', 'unknown'),
						'status': result.get('workflow_status', 'unknown'),
						'architecture': 'fork-join-parallel',
						'vulnerability_node_removed': True
					}
				)

				# 결과 요약 출력
				self._print_summary(result)

				return result
			else:
				raise Exception("No workflow execution result")

		except Exception as e:
			# 워크플로우 실행 시간 계산 (실패 시)
			workflow_execution_time = (datetime.now() - workflow_start_time).total_seconds()

			print(f"\n[ERROR] Workflow execution failed: {e}")

			# LangSmith 에러 기록
			self.tracer.log_agent_execution(
				agent_name="workflow_orchestrator",
				execution_time=workflow_execution_time,
				status="failed",
				input_data={
					'location': target_location.get('name', 'unknown')
				},
				error=e
			)

			return {
				'workflow_status': 'failed',
				'errors': [str(e)]
			}

	def _preprocess_additional_data(self, state: dict) -> dict:
		"""
		추가 데이터 전처리 (워크플로우 외부에서 독립적으로 실행)

		추가 데이터가 있으면 LLM을 1회 호출하여 모든 Agent에 대한 가이드라인 생성

		Args:
			state: 초기 상태 딕셔너리

		Returns:
			가이드라인이 추가된 상태 딕셔너리
		"""
		additional_data = state.get('additional_data')

		if not additional_data:
			# 추가 데이터가 없으면 그대로 반환
			return state

		print("\n[INFO] Additional data preprocessing...")

		try:
			from .utils.additional_data_helper import AdditionalDataHelper

			helper = AdditionalDataHelper()

			# LLM 1회 호출로 모든 Agent에 대한 가이드라인 생성
			guidelines = helper.generate_guidelines(
				additional_data=additional_data,
				agent_configs=self._get_agent_configs()
			)

			# State에 가이드라인 추가
			state['additional_data_guidelines'] = guidelines

			print(f"[OK] Guidelines generated for {len(guidelines)} agents")

			# 가이드라인 요약 출력
			for agent_name, guideline in guidelines.items():
				relevance = guideline.get('relevance', 0.0)
				insights_count = len(guideline.get('suggested_insights', []))
				if relevance >= 0.4:
					print(f"  - {agent_name}: relevance={relevance:.2f}, insights={insights_count}")

		except Exception as e:
			print(f"[WARN] Additional data preprocessing failed: {e}")
			# 실패해도 워크플로우는 계속 진행
			state['additional_data_guidelines'] = {}

		return state

	@traceable(name="skax_enhance_with_additional_data", tags=["workflow", "enhance", "additional-data"])
	def enhance_with_additional_data(
		self,
		cached_state: dict,
		additional_data: dict
	) -> dict:
		"""
		캐싱된 State에 추가 데이터를 반영하여 Node 5 이후 재실행

		Args:
			cached_state: 1차 분석의 State (Node 1~4 결과 포함)
			additional_data: 추가 데이터
				- raw_text: 자유 형식 텍스트
				- metadata: 메타데이터

		Returns:
			향상된 분석 결과 딕셔너리
		"""
		print("\n" + "=" * 70)
		print("SKAX Analysis Enhancement with Additional Data")
		print("=" * 70)

		# 로깅용 컨텍스트 (request_id 추출)
		request_id = cached_state.get('_request_id')
		log_extra = {"request_id": request_id} if request_id else {}

		self.logger.info(
			"Enhancement workflow started",
			extra={**log_extra, "has_additional_data": bool(additional_data)}
		)

		# 실행 시작 시간 기록
		workflow_start_time = datetime.now()

		# cached_state 복사 (원본 보존)
		enhanced_state = cached_state.copy()

		# 추가 데이터 State에 추가
		enhanced_state['additional_data'] = additional_data

		self.logger.info(
			"Preprocessing additional data to generate guidelines",
			extra=log_extra
		)

		# 추가 데이터 전처리 (가이드라인 생성)
		enhanced_state = self._preprocess_additional_data(enhanced_state)

		# Node 5 이후 재실행을 위한 State 준비
		enhanced_state['current_step'] = 'risk_integration'  # Node 4 완료 상태로 설정
		enhanced_state['workflow_status'] = 'in_progress'
		enhanced_state['retry_count'] = 0
		enhanced_state['_workflow_start_time'] = workflow_start_time.isoformat()

		# 기존 Node 5 이후 결과 초기화 (재실행 대상)
		enhanced_state['building_characteristics'] = None
		enhanced_state['report_template'] = None
		enhanced_state['impact_analysis'] = None
		enhanced_state['response_strategy'] = None
		enhanced_state['generated_report'] = None
		enhanced_state['validation_result'] = None
		enhanced_state['refined_report'] = None
		enhanced_state['final_report'] = None

		# 상태 초기화
		enhanced_state['building_analysis_status'] = 'pending'
		enhanced_state['template_status'] = 'pending'
		enhanced_state['impact_status'] = 'pending'
		enhanced_state['strategy_status'] = 'pending'
		enhanced_state['report_status'] = 'pending'
		enhanced_state['validation_status'] = 'pending'
		enhanced_state['refiner_status'] = 'pending'
		enhanced_state['final_status'] = 'pending'

		print("\n[INFO] Re-executing workflow from Node 5 (Risk Integration) onwards...\n")

		self.logger.info(
			"Re-executing workflow from Node 5 onwards",
			extra={**log_extra, "nodes_to_rerun": "Node 5-10"}
		)

		try:
			# LangGraph 실행 (risk_integration부터 시작)
			final_state = None
			for state in self.workflow_graph.stream(enhanced_state):
				if self.config.DEBUG:
					print(f"  > Current step: {state}")
				final_state = state

			# 최종 상태 추출
			if final_state:
				last_node_key = list(final_state.keys())[-1]
				result = final_state[last_node_key]

				# 워크플로우 실행 시간 계산
				workflow_execution_time = (datetime.now() - workflow_start_time).total_seconds()

				print("\n" + "=" * 70)
				print("Enhancement execution completed")
				print("=" * 70)

				self.logger.info(
					"Enhancement workflow completed successfully",
					extra={
						**log_extra,
						"execution_time_s": f"{workflow_execution_time:.2f}",
						"workflow_status": result.get('workflow_status', 'unknown')
					}
				)

				# LangSmith 메트릭 기록
				self.tracer.log_metric(
					metric_name="enhancement_execution_time",
					value=workflow_execution_time,
					metadata={
						'nodes_rerun': 'Node 5 onwards',
						'status': result.get('workflow_status', 'unknown'),
						'additional_data_applied': True
					}
				)

				# 결과 요약 출력
				self._print_summary(result)

				return result
			else:
				raise Exception("No workflow execution result")

		except Exception as e:
			workflow_execution_time = (datetime.now() - workflow_start_time).total_seconds()

			print(f"\n[ERROR] Enhancement workflow failed: {e}")

			self.logger.error(
				f"Enhancement workflow failed: {str(e)}",
				extra={
					**log_extra,
					"execution_time_s": f"{workflow_execution_time:.2f}",
					"error_type": type(e).__name__
				},
				exc_info=True
			)

			# LangSmith 에러 기록
			self.tracer.log_agent_execution(
				agent_name="enhancement_orchestrator",
				execution_time=workflow_execution_time,
				status="failed",
				input_data={
					'additional_data': additional_data
				},
				error=e
			)

			return {
				'workflow_status': 'failed',
				'errors': [str(e)]
			}

	def _get_agent_configs(self) -> list:
		"""
		Agent 설정 목록 반환 (Additional Data Guideline 생성용)

		Returns:
			Agent 설정 리스트
		"""
		return [
			{'name': 'building_characteristics', 'purpose': '건물 특징 및 리스크 점수 해석 (LLM 기반 정성 분석)'},
			{'name': 'impact_analysis', 'purpose': '전력 사용량 및 운영 영향 분석'},
			{'name': 'strategy_generation', 'purpose': '기후 리스크 대응 전략 수립'},
			# 'vulnerability_analysis' 삭제됨 (ModelOps가 V 계산)
			{'name': 'report_generation', 'purpose': '최종 리포트 작성 및 톤 조정'}
		]

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

		# 물리적 리스크 점수 및 AAL
		physical_risk_scores = result.get('physical_risk_scores', {})
		aal_analysis = result.get('aal_analysis', {})

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

				# AAL v11: final_aal_percentage 사용
				aal_data = aal_analysis.get(risk_type, {})
				aal_percentage = aal_data.get('final_aal_percentage', 0)

				print(f"  {risk_type}: {score:.2f}/100 ({level}) - AAL: {aal_percentage:.4f}%")

		# 건물 특징 분석 (NEW)
		building_characteristics = result.get('building_characteristics', {})
		if building_characteristics:
			print(f"\n[BUILDING] Building Characteristics Analysis:")
			analysis_status = building_characteristics.get('analysis_status', 'unknown')
			print(f"  Status: {analysis_status}")

			# 종합 분석이 있으면 요약 출력
			comprehensive = building_characteristics.get('comprehensive_analysis', {})
			if comprehensive:
				summary = comprehensive.get('summary', 'N/A')
				print(f"  Summary: {summary[:100]}..." if len(summary) > 100 else f"  Summary: {summary}")

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
		from .workflow import visualize_workflow
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
