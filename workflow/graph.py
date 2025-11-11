'''
파일명: graph.py
최종 수정일: 2025-11-11
버전: v02
파일 개요: LangGraph 워크플로우 그래프 정의 (Super Agent 계층적 구조)
변경 이력:
	- 2025-11-11: v01 - Super Agent 계층적 구조로 전면 개편, 검증 재시도 루프 추가
	- 2025-11-11: v02 - 워크플로우 순서 변경 (AAL 분석 → 물리적 리스크 점수), 100점 스케일 적용
'''
from langgraph.graph import StateGraph, END
from workflow.state import SuperAgentState
from workflow.nodes import (
	data_collection_node,
	vulnerability_analysis_node,
	physical_risk_score_node,
	aal_analysis_node,
	report_template_node,
	strategy_generation_node,
	report_generation_node,
	validation_node,
	finalization_node
)


def should_retry_validation(state: SuperAgentState) -> str:
	"""
	검증 재시도 판단 함수
	검증 실패 시 재시도 여부 결정

	Args:
		state: 현재 워크플로우 상태

	Returns:
		다음 노드 이름 ('strategy_generation' 또는 'finalization')
	"""
	validation_status = state.get('validation_status')
	retry_count = state.get('retry_count', 0)

	if validation_status == 'failed' and retry_count < 3:
		print(f"[조건부 분기] 검증 실패 -> 대응 전략 재생성 (재시도 {retry_count + 1}/3)")
		return 'strategy_generation'  # 대응 전략 재생성 노드로 복귀
	else:
		print("[조건부 분기] 검증 통과 또는 재시도 횟수 초과 -> 최종화")
		return 'finalization'  # 최종화 노드로 이동


def create_workflow_graph(config):
	"""
	Super Agent 워크플로우 그래프 생성
	10개 노드를 연결하고 검증 재시도 루프 포함

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
	workflow.add_node('report_template', lambda state: report_template_node(state, config))
	workflow.add_node('strategy_generation', lambda state: strategy_generation_node(state, config))
	workflow.add_node('report_generation', lambda state: report_generation_node(state, config))
	workflow.add_node('validation', lambda state: validation_node(state, config))
	workflow.add_node('finalization', lambda state: finalization_node(state, config))

	# ========== 엣지 추가 (워크플로우 흐름) ==========

	# 시작점: 데이터 수집
	workflow.set_entry_point('data_collection')

	# 1. 데이터 수집 -> 취약성 분석
	workflow.add_edge('data_collection', 'vulnerability_analysis')

	# 2. 취약성 분석 -> AAL 분석 (순서 변경: AAL이 먼저)
	workflow.add_edge('vulnerability_analysis', 'aal_analysis')

	# 3. AAL 분석 -> 물리적 리스크 점수 산출 (AAL 결과 기반으로 100점 스케일 계산)
	workflow.add_edge('aal_analysis', 'physical_risk_score')

	# 4. 물리적 리스크 점수 산출 -> 리포트 템플릿 생성
	workflow.add_edge('physical_risk_score', 'report_template')

	# 5. 리포트 템플릿 생성 -> 대응 전략 생성
	workflow.add_edge('report_template', 'strategy_generation')

	# 6. 대응 전략 생성 -> 리포트 생성
	workflow.add_edge('strategy_generation', 'report_generation')

	# 7. 리포트 생성 -> 검증
	workflow.add_edge('report_generation', 'validation')

	# 8. 검증 -> 조건부 분기 (검증 통과/실패)
	workflow.add_conditional_edges(
		'validation',
		should_retry_validation,
		{
			'strategy_generation': 'strategy_generation',  # 검증 실패 시 재생성
			'finalization': 'finalization'  # 검증 통과 시 최종화
		}
	)

	# 9. 최종화 -> 종료
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
	+-------------------------------------------------------+
	  |
	  v
	+-------------------------------------------------------+
	|  Node 2: 취약성 분석 (vulnerability_analysis)          |
	|  - 건물 연식, 내진 설계, 소방차 진입 가능성             |
	|  - 9개 리스크 선정                                      |
	+-------------------------------------------------------+
	  |
	  v
	+-------------------------------------------------------+
	|  Node 3: 연평균 재무 손실률 분석 (aal_analysis)        |
	|  - 9개 AAL Sub Agent 병렬 실행                         |
	|  - 공식: AAL(%) = P(H) × 손상률 × (1-보험보전율)       |
	|  - 재무 손실액 = AAL(%) × 사업장 자산 / 100            |
	|    1. high_temperature   2. cold_wave                |
	|    3. wildfire           4. drought                  |
	|    5. water_scarcity     6. coastal_flood            |
	|    7. inland_flood       8. urban_flood              |
	|    9. typhoon                                        |
	+-------------------------------------------------------+
	  |
	  v
	+-------------------------------------------------------+
	|  Node 4: 물리적 리스크 종합 점수 산출                   |
	|  (physical_risk_score)                                |
	|  - AAL 재무 손실액 기반 100점 스케일 변환              |
	|  - 점수 = (재무손실액 / 최대손실액) × 100              |
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
	|  Node 6: 대응 전략 생성 (strategy_generation)          |
	|  - LLM + RAG 활용                                     |
	|  - 맞춤형 대응 전략 및 권고 사항 생성                   |
	+-------------------------------------------------------+
	  |
	  v
	+-------------------------------------------------------+
	|  Node 7: 리포트 생성 (report_generation)               |
	|  - 템플릿과 분석 결과 통합                             |
	|  - 최종 리포트 작성                                    |
	+-------------------------------------------------------+
	  |
	  v
	+-------------------------------------------------------+
	|  Node 8: 검증 (validation)                            |
	|  - 정확성 검증 (데이터 일치 여부)                       |
	|  - 일관성 검증 (논리적 모순 확인)                       |
	|  - 완전성 검증 (필수 섹션 포함 확인)                    |
	+-------------------------------------------------------+
	  |
	  +-----------------------+
	  |                       |
	  v (검증 실패)          v (검증 통과)
	[재시도 루프]            |
	최대 3회                 |
	  |                       |
	  v                       v
	Node 6으로 복귀         +---------------------------------------+
	(대응 전략 재생성)      |  Node 9: 최종 리포트 산출 (finalization) |
	                        |  - 검증 통과한 리포트 확정              |
	                        +---------------------------------------+
	                          |
	                          v
	                        END

	==============================================================
	주요 특징:
	- Super Agent 계층적 구조
	- 18개 Sub Agent (물리적 리스크 9개 + AAL 9개)
	- LLM/RAG 통합 (대응 전략 생성)
	- 검증 재시도 루프 (최대 3회)
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
