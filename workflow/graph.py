"""
LangGraph Workflow Graph Definition
워크플로우 그래프 정의
"""
from typing import Literal
from langgraph.graph import StateGraph, END
from workflow.state import AnalysisState
from workflow import nodes


def create_workflow_graph(config):
    """
    SKAX 물리적 리스크 분석 워크플로우 그래프 생성

    워크플로우 구조:
    START
      ↓
    [1. 데이터 수집]
      ↓
    [2. SSP 확률 계산]
      ↓
    [3. 8대 기후 리스크 분석] (병렬)
      ├─ 3.1 고온
      ├─ 3.2 한파
      ├─ 3.3 해수면 (frozen)
      ├─ 3.4 가뭄
      ├─ 3.5 산불
      ├─ 3.6 태풍
      ├─ 3.7 물부족 (frozen)
      └─ 3.8 홍수
      ↓
    [4. 리스크 통합]
      ↓
    [5. 리포트 생성]
      ↓
    END
    """

    # StateGraph 생성
    workflow = StateGraph(AnalysisState)

    # ===== 노드 추가 =====

    # Step 1: 데이터 수집
    workflow.add_node(
        "collect_data",
        lambda state: nodes.collect_data_node(state, config)
    )

    # Step 2: SSP 확률 계산
    workflow.add_node(
        "calculate_ssp",
        lambda state: nodes.calculate_ssp_probabilities_node(state, config)
    )

    # Step 3: 8대 기후 리스크 분석 (병렬 노드)
    workflow.add_node(
        "analyze_high_temperature",
        lambda state: nodes.analyze_high_temperature_node(state, config)
    )
    workflow.add_node(
        "analyze_cold_wave",
        lambda state: nodes.analyze_cold_wave_node(state, config)
    )
    workflow.add_node(
        "analyze_sea_level_rise",
        lambda state: nodes.analyze_sea_level_rise_node(state, config)
    )
    workflow.add_node(
        "analyze_drought",
        lambda state: nodes.analyze_drought_node(state, config)
    )
    workflow.add_node(
        "analyze_wildfire",
        lambda state: nodes.analyze_wildfire_node(state, config)
    )
    workflow.add_node(
        "analyze_typhoon",
        lambda state: nodes.analyze_typhoon_node(state, config)
    )
    workflow.add_node(
        "analyze_water_scarcity",
        lambda state: nodes.analyze_water_scarcity_node(state, config)
    )
    workflow.add_node(
        "analyze_flood",
        lambda state: nodes.analyze_flood_node(state, config)
    )

    # Step 4: 리스크 통합
    workflow.add_node(
        "integrate_risks",
        lambda state: nodes.integrate_risks_node(state, config)
    )

    # Step 5: 리포트 생성
    workflow.add_node(
        "generate_report",
        lambda state: nodes.generate_report_node(state, config)
    )

    # ===== 엣지 추가 =====

    # 시작점 → 데이터 수집
    workflow.set_entry_point("collect_data")

    # 데이터 수집 → SSP 확률 계산
    workflow.add_edge("collect_data", "calculate_ssp")

    # SSP 확률 계산 → 8대 기후 리스크 분석 (병렬)
    workflow.add_edge("calculate_ssp", "analyze_high_temperature")
    workflow.add_edge("calculate_ssp", "analyze_cold_wave")
    workflow.add_edge("calculate_ssp", "analyze_sea_level_rise")
    workflow.add_edge("calculate_ssp", "analyze_drought")
    workflow.add_edge("calculate_ssp", "analyze_wildfire")
    workflow.add_edge("calculate_ssp", "analyze_typhoon")
    workflow.add_edge("calculate_ssp", "analyze_water_scarcity")
    workflow.add_edge("calculate_ssp", "analyze_flood")

    # 8대 기후 리스크 분석 → 리스크 통합
    workflow.add_edge("analyze_high_temperature", "integrate_risks")
    workflow.add_edge("analyze_cold_wave", "integrate_risks")
    workflow.add_edge("analyze_sea_level_rise", "integrate_risks")
    workflow.add_edge("analyze_drought", "integrate_risks")
    workflow.add_edge("analyze_wildfire", "integrate_risks")
    workflow.add_edge("analyze_typhoon", "integrate_risks")
    workflow.add_edge("analyze_water_scarcity", "integrate_risks")
    workflow.add_edge("analyze_flood", "integrate_risks")

    # 리스크 통합 → 리포트 생성
    workflow.add_edge("integrate_risks", "generate_report")

    # 리포트 생성 → 종료
    workflow.add_edge("generate_report", END)

    # 그래프 컴파일
    compiled_graph = workflow.compile()

    return compiled_graph


def visualize_workflow(graph, output_path: str = "workflow_graph.png"):
    """
    워크플로우 그래프 시각화

    Args:
        graph: 컴파일된 LangGraph
        output_path: 출력 파일 경로
    """
    try:
        from IPython.display import Image, display
        import io

        # LangGraph 내장 시각화
        graph_image = graph.get_graph().draw_mermaid_png()

        # 파일로 저장
        with open(output_path, 'wb') as f:
            f.write(graph_image)

        print(f"워크플로우 그래프가 '{output_path}'에 저장되었습니다.")

        return graph_image

    except Exception as e:
        print(f"시각화 생성 실패: {e}")
        print("대신 Mermaid 다이어그램을 생성합니다...")

        # Mermaid 다이어그램 텍스트 생성
        mermaid_diagram = graph.get_graph().draw_mermaid()

        # 텍스트 파일로 저장
        mermaid_path = output_path.replace('.png', '.mmd')
        with open(mermaid_path, 'w', encoding='utf-8') as f:
            f.write(mermaid_diagram)

        print(f"Mermaid 다이어그램이 '{mermaid_path}'에 저장되었습니다.")
        print("https://mermaid.live 에서 시각화할 수 있습니다.")

        return mermaid_diagram


def print_workflow_structure():
    """
    워크플로우 구조를 텍스트로 출력
    """
    structure = """
    ==============================================================
         SKAX Physical Risk Analysis Workflow Structure
    ==============================================================

    START
      |
      v
    +---------------------------------------+
    |  Step 1: Data Collection              |
    |  (collect_data)                       |
    +---------------------------------------+
      |
      v
    +---------------------------------------+
    |  Step 2: SSP Scenario Probability     |
    |  (calculate_ssp)                      |
    +---------------------------------------+
      |
      v
    +-----------------------------------------------------------+
    |  Step 3: 8 Climate Risks Analysis (Parallel)            |
    +-----------------------------------------------------------+
    |  3.1  analyze_high_temperature  (High Temperature)      |
    |  3.2  analyze_cold_wave         (Cold Wave + Snow)      |
    |  3.3  analyze_sea_level_rise    (Sea Level) [FROZEN]    |
    |  3.4  analyze_drought           (Drought)               |
    |  3.5  analyze_wildfire          (Wildfire)              |
    |  3.6  analyze_typhoon           (Typhoon)               |
    |  3.7  analyze_water_scarcity    (Water) [FROZEN]        |
    |  3.8  analyze_flood             (Flood)                 |
    +-----------------------------------------------------------+
      |  (After all risk analyses completed)
      v
    +---------------------------------------+
    |  Step 4: Risk Integration             |
    |  (integrate_risks)                    |
    +---------------------------------------+
      |
      v
    +---------------------------------------+
    |  Step 5: Report Generation            |
    |  (generate_report)                    |
    +---------------------------------------+
      |
      v
    END

    ==============================================================
    Key Features:
    - Step 3: 8 risk analyses run in parallel using LangGraph
    - Each risk: H(Hazard) x E(Exposure) x V(Vulnerability)
    - SSP scenario weights applied to all risk calculations
    ==============================================================
    """

    print(structure)
