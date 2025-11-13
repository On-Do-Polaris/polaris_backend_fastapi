'''
파일명: graph.py
최종 수정일: 2025-11-13
버전: v04
파일 개요: LangGraph 워크플로우 그래프 정의 (Super Agent 계층적 구조)
변경 이력:
	- 2025-11-11: v01 - Super Agent 계층적 구조로 전면 개편, 검증 재시도 루프 추가
	- 2025-11-11: v02 - 워크플로우 순서 변경 (AAL 분석 → 물리적 리스크 점수), 100점 스케일 적용
	- 2025-11-13: v03 - AAL과 물리적 리스크 점수를 병렬 실행으로 변경 (H×E×V 방식 복원)
	- 2025-11-13: v04 - 영향 분석 노드 추가 (report_template → impact_analysis → strategy)
'''
from langgraph.graph import StateGraph, END
from .state import SuperAgentState
from .nodes import (
	data_collection_node,
	vulnerability_analysis_node,
	physical_risk_score_node,
	aal_analysis_node,
	risk_integration_node,
	report_template_node,
	impact_analysis_node,
	strategy_generation_node,
	report_generation_node,
	validation_node,
	finalization_node
)


def should_retry_validation(state: SuperAgentState) -> str:
	"""
	검증 재시도 판단 함수
	검증 실패 시 이슈 유형에 따라 분기 결정

	Args:
		state: 현재 워크플로우 상태

	Returns:
		다음 노드 이름 ('impact_analysis', 'strategy_generation', 또는 'finalization')
	"""
	validation_status = state.get('validation_status')
	retry_count = state.get('retry_count', 0)
	validation_result = state.get('validation_result', {})

	# 검증 통과 또는 재시도 횟수 초과
	if validation_status == 'passed':
		print("[조건부 분기] 검증 통과 -> 최종화")
		return 'finalization'

	if retry_count >= 3:
		print("[조건부 분기] 재시도 횟수 초과 (3/3) -> 최종화")
		return 'finalization'

	# 검증 실패 - 이슈 유형 분석
	issues_found = validation_result.get('issues_found', [])

	# 영향 분석 관련 이슈 확인
	impact_related_issues = [
		'impact_analysis_missing',
		'impact_data_inconsistent',
		'power_consumption_analysis_incomplete',
		'risk_impact_mismatch'
	]

	# 전략 관련 이슈 확인
	strategy_related_issues = [
		'strategy_missing',
		'strategy_incomplete',
		'adaptation_actions_missing',
		'recommendations_insufficient'
	]

	# 이슈 분류
	has_impact_issues = any(
		issue.get('type') in impact_related_issues or 'impact' in issue.get('type', '').lower()
		for issue in issues_found
	)

	has_strategy_issues = any(
		issue.get('type') in strategy_related_issues or 'strategy' in issue.get('type', '').lower()
		for issue in issues_found
	)

	# 분기 결정
	if has_impact_issues and not has_strategy_issues:
		print(f"[조건부 분기] 검증 실패 (영향 분석 이슈) -> 영향 분석 재실행 (재시도 {retry_count + 1}/3)")
		return 'impact_analysis'
	elif has_strategy_issues or (has_impact_issues and has_strategy_issues):
		print(f"[조건부 분기] 검증 실패 (전략 이슈) -> 대응 전략 재생성 (재시도 {retry_count + 1}/3)")
		return 'strategy_generation'
	else:
		# 기타 이슈는 전략 재생성으로
		print(f"[조건부 분기] 검증 실패 (일반 이슈) -> 대응 전략 재생성 (재시도 {retry_count + 1}/3)")
		return 'strategy_generation'


def create_workflow_graph(config):
	"""
	Super Agent 워크플로우 그래프 생성
	12개 노드를 연결하고 검증 재시도 루프 포함
	AAL과 물리적 리스크 점수는 병렬 실행 (개념적)
	report_template → impact_analysis → strategy 흐름

	Args:
		config: 설정 객체

	Returns:
		컴파일된 LangGraph 워크플로우
	"""
	# StateGraph 초기화
	workflow = StateGraph(SuperAgentState)

	# ========== 노드 추가 ==========
	workflow.add_node('data_collection', lambda state: data_collection_node(state, config))
	workflow.add_node('vulnerability_analysis', lambda state: vulnerability_analysis_node(state, config))
	workflow.add_node('physical_risk_score', lambda state: physical_risk_score_node(state, config))
	workflow.add_node('aal_analysis', lambda state: aal_analysis_node(state, config))
	workflow.add_node('risk_integration', lambda state: risk_integration_node(state, config))
	workflow.add_node('report_template', lambda state: report_template_node(state, config))
	workflow.add_node('impact_analysis', lambda state: impact_analysis_node(state, config))
	workflow.add_node('strategy_generation', lambda state: strategy_generation_node(state, config))
	workflow.add_node('report_generation', lambda state: report_generation_node(state, config))
	workflow.add_node('validation', lambda state: validation_node(state, config))
	workflow.add_node('finalization', lambda state: finalization_node(state, config))

	# ========== 엣지 추가 (워크플로우 흐름) ==========

	# 시작점: 데이터 수집
	workflow.set_entry_point('data_collection')

	# 1. 데이터 수집 -> 취약성 분석
	workflow.add_edge('data_collection', 'vulnerability_analysis')

	# 2. 취약성 분석 -> 물리적 리스크 점수 (H×E×V 기반, 병렬 실행 개념)
	workflow.add_edge('vulnerability_analysis', 'physical_risk_score')

	# 3. 취약성 분석 -> AAL 분석 (병렬 실행 개념)
	workflow.add_edge('vulnerability_analysis', 'aal_analysis')

	# 4. 물리적 리스크 점수 -> 리스크 통합
	workflow.add_edge('physical_risk_score', 'risk_integration')

	# 5. AAL 분석 -> 리스크 통합
	workflow.add_edge('aal_analysis', 'risk_integration')

	# 6. 리스크 통합 -> 리포트 템플릿 생성
	workflow.add_edge('risk_integration', 'report_template')

	# 7. 리포트 템플릿 생성 -> 영향 분석
	workflow.add_edge('report_template', 'impact_analysis')

	# 8. 영향 분석 -> 대응 전략 생성
	workflow.add_edge('impact_analysis', 'strategy_generation')

	# 9. 대응 전략 생성 -> 리포트 생성
	workflow.add_edge('strategy_generation', 'report_generation')

	# 10. 리포트 생성 -> 검증
	workflow.add_edge('report_generation', 'validation')

	# 11. 검증 -> 조건부 분기 (이슈 유형에 따라 분기)
	workflow.add_conditional_edges(
		'validation',
		should_retry_validation,
		{
			'impact_analysis': 'impact_analysis',  # 영향 분석 이슈 -> 영향 분석 재실행
			'strategy_generation': 'strategy_generation',  # 전략 이슈 -> 전략 재생성
			'finalization': 'finalization'  # 검증 통과 또는 재시도 초과 -> 최종화
		}
	)

	# 12. 최종화 -> 종료
	workflow.add_edge('finalization', END)

	# 그래프 컴파일
	compiled_graph = workflow.compile()

	print("=== Super Agent 워크플로우 그래프 컴파일 완료 ===")
	print_workflow_structure()

	return compiled_graph


def print_workflow_structure():
	"""
	워크플로우 구조를 텍스트로 출력
	"""
	structure = """
	==============================================================
	     SKAX Physical Risk Analysis Workflow (Super Agent)
	==============================================================

	START
	  |
	  v
	+-------------------------------------------------------+
	|  Node 1: 데이터 수집 (data_collection)                |
	|  - 대상 위치 기후 데이터 수집                           |
	|  - 과거~현재 전력 사용량 데이터 수집                    |
	+-------------------------------------------------------+
	  |
	  v
	+-------------------------------------------------------+
	|  Node 2: 취약성 분석 (vulnerability_analysis)          |
	|  - 건물 연식, 내진 설계, 소방차 진입 가능성             |
	|  - 9개 리스크 선정                                      |
	+-------------------------------------------------------+
	  |
	  +------------------------+------------------------+
	  |                        |                        |
	  v                        v                        |
	+------------------+ +------------------+           |
	| Node 3a: 물리적  | | Node 3b: AAL    |           |
	| 리스크 점수 산출 | | 분석 (병렬실행) |           |
	| (H×E×V 기반)     | | (P×D 기반)      |           |
	| • 9개 Sub Agent | | • 9개 Sub Agent |           |
	| • Hazard        | | • 확률×손상률   |           |
	| • Exposure      | | • 재무손실액    |           |
	| • Vulnerability | |                 |           |
	+------------------+ +------------------+           |
	  |                        |                        |
	  +------------------------+------------------------+
	  |
	  v
	+-------------------------------------------------------+
	|  Node 4: 리스크 통합 (risk_integration)               |
	|  - 물리적 리스크 점수 + AAL 분석 결과 통합             |
	+-------------------------------------------------------+
	  |
	  v
	+-------------------------------------------------------+
	|  Node 5: 리포트 템플릿 형성 (report_template)          |
	|  - RAG 엔진 활용                                       |
	|  - 유사 기존 보고서 검색 및 참조                        |
	+-------------------------------------------------------+
	  |
	  v
	+-------------------------------------------------------+
	|  Node 6: 영향 분석 (impact_analysis)                  |
	|  - 전력 사용량 기반 구체적 영향 분석                    |
	|  - 리스크별 과거 데이터 패턴 분석                       |
	|  - 운영 비용 및 설비 영향 평가                         |
	+-------------------------------------------------------+
	  |
	  v
	+-------------------------------------------------------+
	|  Node 7: 대응 전략 생성 (strategy_generation)          |
	|  - LLM + RAG 활용                                     |
	|  - 물리적 리스크, AAL, 영향 분석 기반 전략 수립         |
	|  - 맞춤형 대응 전략 및 권고 사항 생성                   |
	+-------------------------------------------------------+
	  |
	  v
	+-------------------------------------------------------+
	|  Node 8: 리포트 생성 (report_generation)               |
	|  - 템플릿과 분석 결과 통합                             |
	|  - 최종 리포트 작성                                    |
	+-------------------------------------------------------+
	  |
	  v
	+-------------------------------------------------------+
	|  Node 9: 검증 (validation)                            |
	|  - 정확성 검증 (데이터 일치 여부)                       |
	|  - 일관성 검증 (논리적 모순 확인)                       |
	|  - 완전성 검증 (필수 섹션 포함 확인)                    |
	|  - 이슈 유형 분석 (영향 분석 / 전략 이슈)               |
	+-------------------------------------------------------+
	  |
	  +-----------------------------------+
	  |                 |                 |
	  v (영향분석 이슈) v (전략 이슈)    v (검증 통과)
	[재시도 루프]      [재시도 루프]    |
	최대 3회            최대 3회          |
	  |                 |                 |
	  v                 v                 v
	Node 6으로 복귀    Node 7으로 복귀   +---------------------------------------+
	(영향 분석 재실행) (대응 전략 재생성)|  Node 10: 최종 리포트 산출 (finalization)|
	                                     |  - 검증 통과한 리포트 확정              |
	                                     +---------------------------------------+
	                                       |
	                                       v
	                                     END

	==============================================================
	주요 특징:
	- Super Agent 계층적 구조 (25개 에이전트)
	- 데이터 처리: 2개 (데이터 수집, 취약성 분석)
	- 리스크 분석: 18개 (물리적 리스크 9개 + AAL 9개, 병렬 실행)
	- 보고서 생성: 5개 (템플릿, 영향 분석, 전략, 생성, 검증)
	- 물리적 리스크(H×E×V)와 AAL 병렬 계산
	- 전력 사용량 기반 영향 분석 (신규)
	- LLM/RAG 통합 (대응 전략 생성)
	- 지능형 검증 재시도 루프 (최대 3회, 이슈 유형별 분기)
	  * 영향 분석 이슈 → Node 6 (영향 분석) 재실행
	  * 전략 이슈 → Node 7 (대응 전략) 재생성
	  * 검증 피드백 자동 반영
	- 취약성 분석 기반 리스크 선정
	==============================================================
	"""

	print(structure)


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
