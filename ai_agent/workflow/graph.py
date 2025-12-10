'''
파일명: graph.py
최종 수정일: 2025-12-02
버전: v07
파일 개요: LangGraph 워크플로우 그래프 정의 (Phase 2: 리포트 생성 전용)
변경 이력:
	- 2025-11-11: v01 - Super Agent 계층적 구조로 전면 개편, 검증 재시도 루프 추가
	- 2025-11-11: v02 - 워크플로우 순서 변경 (AAL 분석 → 물리적 리스크 점수), 100점 스케일 적용
	- 2025-11-13: v03 - AAL과 물리적 리스크 점수를 병렬 실행으로 변경 (H×E×V 방식 복원)
	- 2025-11-13: v04 - 영향 분석 노드 추가 (report_template → impact_analysis → strategy)
	- 2025-12-01: v05 - Node 2 역할 변경 (Vulnerability → Building Characteristics)
	                   - Node 5 이후 병렬 분기 구조 추가 (2 ∥ [6→7→8→9→10→11])
	- 2025-12-01: v06 - vulnerability_analysis 노드 삭제 (ModelOps가 V 계산)
	                   - Data Collection → 직접 ModelOps (Node 1 → 2 ∥ 3)
	- 2025-12-02: v07 - Phase 1/2 분리: Node 2, 3, 4 제거 (Physical Risk Score, AAL, Risk Integration)
	                   - Node 1 (Data Collection) 유지
	                   - DB에서 H, E, V, risk_scores, AAL 로드하여 사용
'''
from langgraph.graph import StateGraph, END
from .state import SuperAgentState
from .nodes import (
	data_collection_node,
	risk_assessment_node,
	report_template_node,
	impact_analysis_node,
	strategy_generation_node,
	report_generation_node,
	validation_node,
	refiner_node,
	finalization_node,
	building_characteristics_node
)


def should_retry_validation(state: SuperAgentState) -> str:
	"""
	검증 재시도 판단 함수 (Refiner Loop 포함, Building Characteristics 재실행 지원)
	검증 실패 시 이슈 유형에 따라 적절한 노드로 분기

	Args:
		state: 현재 워크플로우 상태

	Returns:
		다음 노드 이름 ('building_characteristics', 'refiner', 'impact_analysis', 'strategy_generation', 'finalization')
	"""
	validation_status = state.get('validation_status')
	retry_count = state.get('retry_count', 0)
	refiner_loop_count = state.get('refiner_loop_count', 0)
	validation_result = state.get('validation_result', {})

	# 검증 통과
	if validation_status == 'passed':
		print("[조건부 분기] 검증 통과 -> 최종화")
		return 'finalization'

	# Refiner Loop 횟수 확인
	if refiner_loop_count >= 3:
		print(f"[조건부 분기] Refiner Loop 횟수 초과 ({refiner_loop_count}/3) -> 최종화")
		return 'finalization'

	# 재시도 횟수 확인
	if retry_count >= 3:
		print(f"[조건부 분기] 재시도 횟수 초과 ({retry_count}/3) -> 최종화")
		return 'finalization'

	# 검증 실패 - 이슈 유형 분석
	issues_found = validation_result.get('issues_found', [])

	# Building Characteristics 관련 이슈 (재실행 필요) - NEW
	building_characteristics_issues = [
		'building_characteristics_missing',
		'building_characteristics_incomplete',
		'comprehensive_analysis_missing',
		'bc_quality_low',
		'consistency',  # ModelOps 결과 불일치
		'completeness'  # BC 필수 섹션 누락
	]

	# 텍스트/구조 관련 이슈 (Refiner로 자동 수정 가능)
	refiner_fixable_issues = [
		'text_quality',
		'structure_incomplete',
		'section_missing',
		'formatting_error',
		'tcfd_alignment',
		'citation_missing'
	]

	# 영향 분석 관련 이슈 (재실행 필요)
	impact_related_issues = [
		'impact_analysis_missing',
		'impact_data_inconsistent',
		'power_consumption_analysis_incomplete',
		'risk_impact_mismatch'
	]

	# 전략 관련 이슈 (재실행 필요)
	strategy_related_issues = [
		'strategy_missing',
		'strategy_incomplete',
		'adaptation_actions_missing',
		'recommendations_insufficient'
	]

	# 이슈 분류
	has_bc_issues = any(
		issue.get('type') in building_characteristics_issues or
		'building' in issue.get('type', '').lower() or
		issue.get('description', '').lower().find('building characteristics') >= 0
		for issue in issues_found
	)

	has_refiner_issues = any(
		issue.get('type') in refiner_fixable_issues or
		any(keyword in issue.get('type', '').lower() for keyword in ['text', 'structure', 'format', 'tcfd', 'citation'])
		for issue in issues_found
	)

	has_impact_issues = any(
		issue.get('type') in impact_related_issues or 'impact' in issue.get('type', '').lower()
		for issue in issues_found
	)

	has_strategy_issues = any(
		issue.get('type') in strategy_related_issues or 'strategy' in issue.get('type', '').lower()
		for issue in issues_found
	)

	# 분기 결정 (우선순위: Building Characteristics > Refiner > Impact > Strategy)
	if has_bc_issues:
		print(f"[조건부 분기] 검증 실패 (Building Characteristics 이슈) -> Building Characteristics 재실행 (재시도 {retry_count + 1}/3)")
		return 'building_characteristics'
	elif has_refiner_issues and refiner_loop_count < 3:
		print(f"[조건부 분기] 검증 실패 (텍스트/구조 이슈) -> Refiner 자동 보완 (Loop {refiner_loop_count + 1}/3)")
		return 'refiner'
	elif has_impact_issues and not has_strategy_issues:
		print(f"[조건부 분기] 검증 실패 (영향 분석 이슈) -> 영향 분석 재실행 (재시도 {retry_count + 1}/3)")
		return 'impact_analysis'
	elif has_strategy_issues or (has_impact_issues and has_strategy_issues):
		print(f"[조건부 분기] 검증 실패 (전략 이슈) -> 대응 전략 재생성 (재시도 {retry_count + 1}/3)")
		return 'strategy_generation'
	else:
		# 기타 이슈는 Refiner로
		print(f"[조건부 분기] 검증 실패 (일반 이슈) -> Refiner 자동 보완 (Loop {refiner_loop_count + 1}/3)")
		return 'refiner'


def create_workflow_graph(config):
	"""
	Phase 2 워크플로우 그래프 생성 (리포트 생성, Node 1 유지)

	새로운 구조 (v07 - Phase 1/2 분리):
	START → DataCollection → (BC ∥ [Template→Impact→Strategy→Report]) → Validation → Refiner → Finalization → END

	노드 설명:
	- Node 1 (Data Collection): 데이터 수집 (Phase 1 유일한 유지 노드)
	- Node BC (Building Characteristics): 건물 특징 분석 (LLM 기반, 각 사업장별)
	- Node Template: Report Template (report_profile 생성)
	- Node Impact: Impact Analysis (영향 분석, 단일/다중 사업장 지원)
	- Node Strategy: Strategy Generation (전략 생성, 단일/다중 사업장 지원)
	- Node Report: Report Generation (리포트 생성)
	- Node Validation: 검증
	- Node Refiner: 개선 (선택적)
	- Node Finalization: 최종화

	Phase 1 제거된 노드 (DB에서 로드):
	- Node 2: Physical Risk Score (제거 - DB에서 risk_scores 로드)
	- Node 3: AAL Analysis (제거 - DB에서 AAL 로드)
	- Node 4: Risk Integration (제거 - DB에서 H, E, V 로드)

	Args:
		config: 설정 객체

	Returns:
		컴파일된 LangGraph 워크플로우
	"""
	# StateGraph 초기화
	workflow = StateGraph(SuperAgentState)

	# ========== 노드 추가 (Node 1, 3 + Phase 2) ==========
	workflow.add_node('data_collection', lambda state: data_collection_node(state, config))
	workflow.add_node('risk_assessment', lambda state: risk_assessment_node(state, config))
	workflow.add_node('building_characteristics', lambda state: building_characteristics_node(state, config))
	workflow.add_node('report_template', lambda state: report_template_node(state, config))
	workflow.add_node('impact_analysis', lambda state: impact_analysis_node(state, config))
	workflow.add_node('strategy_generation', lambda state: strategy_generation_node(state, config))
	workflow.add_node('report_generation', lambda state: report_generation_node(state, config))
	workflow.add_node('validation', lambda state: validation_node(state, config))
	workflow.add_node('refiner', lambda state: refiner_node(state, config))
	workflow.add_node('finalization', lambda state: finalization_node(state, config))

	# ========== 엣지 추가 (워크플로우 흐름) ==========

	# 시작점: Data Collection (Node 1)
	workflow.set_entry_point('data_collection')

	# 1. Data Collection -> Risk Assessment (통합 H×E×V×AAL 계산)
	workflow.add_edge('data_collection', 'risk_assessment')

	# 2. Risk Assessment -> Report Template (Phase 2 진입)
	workflow.add_edge('risk_assessment', 'report_template')

	# 2. Report Template -> Building Characteristics (병렬 브랜치 1)
	workflow.add_edge('report_template', 'building_characteristics')

	# 3. Report Template -> Impact Analysis (병렬 브랜치 2 시작)
	workflow.add_edge('report_template', 'impact_analysis')

	# ========== 리포트 체인 (순차 실행 Template→Impact→Strategy→Report) ==========

	# 4. 영향 분석 -> 대응 전략 생성
	workflow.add_edge('impact_analysis', 'strategy_generation')

	# 5. 대응 전략 생성 -> 리포트 생성
	workflow.add_edge('strategy_generation', 'report_generation')

	# ========== 병합: Building Characteristics와 Report Generation이 모두 완료되면 Validation으로 ==========

	# 10. Building Characteristics -> 검증 (병렬 브랜치 1 완료)
	workflow.add_edge('building_characteristics', 'validation')

	# 11. 리포트 생성 -> 검증 (병렬 브랜치 2 완료)
	workflow.add_edge('report_generation', 'validation')

	# 12. 검증 -> 조건부 분기 (Building Characteristics, Refiner Loop 포함)
	workflow.add_conditional_edges(
		'validation',
		should_retry_validation,
		{
			'building_characteristics': 'building_characteristics',  # NEW: BC 이슈 -> BC 재실행
			'refiner': 'refiner',  # 텍스트/구조 이슈 -> Refiner 자동 보완
			'impact_analysis': 'impact_analysis',  # 영향 분석 이슈 -> 영향 분석 재실행
			'strategy_generation': 'strategy_generation',  # 전략 이슈 -> 전략 재생성
			'finalization': 'finalization'  # 검증 통과 또는 재시도 초과 -> 최종화
		}
	)

	# 13. Refiner -> 검증 (재검증 루프)
	workflow.add_edge('refiner', 'validation')

	# 14. 최종화 -> 종료 (단일 종료점)
	workflow.add_edge('finalization', END)

	# 그래프 컴파일
	compiled_graph = workflow.compile()

	print("=== Super Agent 워크플로우 그래프 컴파일 완료 (v07 Phase 1/2 분리) ===")
	print_workflow_structure()

	return compiled_graph


def print_workflow_structure():
	"""
	워크플로우 구조를 텍스트로 출력
	"""
	structure = """
	==============================================================
	     SKAX Physical Risk Analysis Workflow (v07)
	==============================================================

	START
	  |
	  v
	+-------------------------------------------------------+
	|  Node 1: 데이터 수집 (data_collection)                |
	|  - 대상 위치 기후 데이터 수집                           |
	|  - 과거~현재 전력 사용량 데이터 수집                    |
	|  - DB에서 H, E, V, risk_scores, AAL 로드 (Phase 1 결과)|
	+-------------------------------------------------------+
	  |
	  v
	+-------------------------------------------------------+
	|  Node 5: 리포트 템플릿 (report_template)             |
	|  - RAG 엔진 활용                                       |
	|  - 보고서 구조 설정                                    |
	+-------------------------------------------------------+
	  |
	  +---------------------------+---------------------------+
	  |                           |                           |
	  v (병렬 브랜치 1)           v (병렬 브랜치 2)           |
	+---------------------------+ +---------------------------+
	| Node BC: 건물 특징 분석   | | Node 6: 영향 분석         |
	| (Building Characteristics)| | (impact_analysis)        |
	| • LLM 기반 정성 분석      | | • 전력 사용량 기반 영향   |
	| • Score/AAL 결과 해석     | | • 단일/다중 사업장 지원   |
	| • 취약점/회복력 분석      | +---------------------------+
	+---------------------------+   |
	  |                             v
	  |                           +---------------------------+
	  |                           | Node 7: 대응 전략 생성    |
	  |                           | (strategy_generation)    |
	  |                           | • LLM + RAG 활용         |
	  |                           | • 단일/다중 사업장 지원   |
	  |                           +---------------------------+
	  |                             |
	  |                             v
	  |                           +---------------------------+
	  |                           | Node 8: 리포트 생성       |
	  |                           | (report_generation)      |
	  |                           +---------------------------+
	  |                             |
	  +-----------------------------+-----------------------------+
	  |                                                           |
	  v                                                           v
	+---------------------------------------------------------------+
	|  Node 9: 검증 (병합 노드)                                    |
	|  - 정확성 검증 (데이터 일치 여부)                             |
	|  - 일관성 검증 (논리적 모순 확인)                             |
	|  - 완전성 검증 (필수 섹션 포함 확인)                          |
	|  - Building Characteristics 결과 활용                       |
	+---------------------------------------------------------------+
	  |
	  +---> [재시도 루프: building_characteristics / refiner /
	  |      impact_analysis / strategy_generation]
	  |
	  v
	+-------------------------------------------------------+
	|  Node 10: 최종화 (finalization)                       |
	|  - 검증 통과한 리포트 확정                             |
	|  - Building Characteristics 결과 포함                |
	+-------------------------------------------------------+
	  |
	  v
	END (단일 종료점)

	==============================================================
	주요 특징 (v07 - Phase 1/2 분리):
	- Phase 1 (제거): Node 2, 3, 4 (Physical Risk Score, AAL, Risk Integration)
	- Phase 1 결과는 DB에서 로드 (H, E, V, risk_scores, AAL)
	- Phase 2 (유지): Node 1 (Data Collection) + 리포트 생성 노드들
	- 다중 사업장 지원: Impact/Strategy Agent가 집계형 분석 수행
	- Building Characteristics: 사업장별 독립 분석 (집계 안 함)

	Phase 2 노드 구성:
	- 데이터 수집: 1개 (Node 1 - Data Collection, DB 로더 역할)
	- 보고서 생성: 5개 (Template, Impact, Strategy, Report, Validation)
	- 건물 분석: 1개 (Building Characteristics, 병렬 실행, LLM 기반)
	- 개선/최종화: 2개 (Refiner, Finalization)

	NEW v07 변경사항:
	- Phase 1 노드 제거 (Node 2, 3, 4)
	- Node 1 (Data Collection) 유지: DB에서 Phase 1 결과 로드
	- Node 1 → Template 직접 연결
	- Template 이후 병렬 분기 구조:
	  * 브랜치 1: Building Characteristics (병렬 실행)
	  * 브랜치 2: Report Chain (6→7→8, 순차 실행)
	  * Node 9에서 병합: Validation (두 브랜치 결과 합침)
	- 다중 사업장 지원: Impact/Strategy Agent에 run_aggregated() 메서드 추가
	==============================================================
	"""

	try:
		print(structure)
	except UnicodeEncodeError:
		# Windows cp949 인코딩 문제 회피 - ASCII 문자만 출력
		import re
		ascii_structure = re.sub(r'[^\x00-\x7F]+', '?', structure)
		print(ascii_structure)


def visualize_workflow(graph, output_path: str = "workflow_graph.png"):
	"""
	워크플로우 그래프 시각화

	Args:
		graph: 컴파일된 LangGraph
		output_path: 출력 파일 경로

	Returns:
		생성된 이미지 데이터 또는 Mermaid 다이어그램 텍스트
	"""
	try:
		from IPython.display import Image, display
		import io

		# LangGraph 내장 시각화
		graph_image = graph.get_graph().draw_mermaid_png()

		# 파일로 저장
		with open(output_path, 'wb') as f:
			f.write(graph_image)

		print(f"[INFO] Workflow graph saved to '{output_path}'")

		return graph_image

	except Exception as e:
		print(f"[WARN] Visualization failed: {e}")
		print("[INFO] Generating Mermaid diagram instead...")

		# Mermaid 다이어그램 텍스트 생성
		mermaid_diagram = graph.get_graph().draw_mermaid()

		# 텍스트 파일로 저장
		mermaid_path = output_path.replace('.png', '.mmd')
		with open(mermaid_path, 'w', encoding='utf-8') as f:
			f.write(mermaid_diagram)

		print(f"[INFO] Mermaid diagram saved to '{mermaid_path}'")
		print("[INFO] You can visualize it at https://mermaid.live")

		return mermaid_diagram
