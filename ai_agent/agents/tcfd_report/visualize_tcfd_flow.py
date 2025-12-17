"""
파일명: visualize_tcfd_flow.py
최종 수정일: 2025-12-17
버전: v1.0
파일 개요: TCFD Report 7-Node Pipeline 워크플로우 시각화 (Mermaid)
"""
import os


def generate_tcfd_workflow_diagram():
    """
    TCFD Report Pipeline 다이어그램 생성 (이미지 스타일)

    Node 구조:
    - Node 0: Data Collection
    - Node 1: Report Template
    - Node 2A: Scenario Analysis
    - Node 2B: Impact Analysis
    - Node 2C: Mitigation Strategies
    - Node 3: Strategy Section
    - Node 4: Validator (+ Refiner 역할)
    - Node 5: Composer
    - Node 6: Finalizer
    """
    diagram = """flowchart TB
    %% TCFD Report 7-Node Pipeline
    %% 스타일 정의
    classDef startEnd fill:#e8e0ff,stroke:#7c4dff,stroke-width:2px,rx:20,ry:20
    classDef dataNode fill:#e8e0ff,stroke:#7c4dff,stroke-width:2px
    classDef processNode fill:#f5f5ff,stroke:#9090ff,stroke-width:1px
    classDef validationNode fill:#f5f5ff,stroke:#9090ff,stroke-width:1px

    %% 노드 정의
    __start__(["__start__"])
    data_collection{{"data_collection"}}
    report_template{{"report_template"}}
    building_characteristics["building_characteristics"]
    validation["validation"]
    impact_analysis["impact_analysis"]
    refiner["refiner"]
    finalization["finalization"]
    strategy_generation["strategy_generation"]
    report_generation{{"report_generation"}}
    __end__(["__end__"])

    %% 메인 플로우
    __start__ --> data_collection
    data_collection --> report_template
    report_template --> building_characteristics
    report_template --> validation
    building_characteristics --> validation

    %% Validation에서 분기
    validation -.-> impact_analysis
    validation -.-> refiner
    validation -.-> finalization

    %% Report Chain
    impact_analysis --> strategy_generation
    strategy_generation --> report_generation
    report_generation --> validation

    %% 종료
    finalization --> __end__

    %% 스타일 적용
    class __start__,__end__ startEnd
    class data_collection,report_template,report_generation dataNode
    class building_characteristics,validation,impact_analysis,refiner,finalization,strategy_generation processNode
"""
    return diagram


def generate_tcfd_detailed_diagram():
    """
    TCFD Report Pipeline 상세 다이어그램 (7-Node 구조 반영)
    """
    diagram = """flowchart TB
    %% TCFD Report 7-Node Pipeline (Detailed)

    classDef startEnd fill:#e8e0ff,stroke:#7c4dff,stroke-width:2px,rx:20,ry:20
    classDef dataNode fill:#e1f5fe,stroke:#0288d1,stroke-width:2px
    classDef analysisNode fill:#e8f5e9,stroke:#4caf50,stroke-width:2px
    classDef validationNode fill:#fff3e0,stroke:#ff9800,stroke-width:2px
    classDef outputNode fill:#fce4ec,stroke:#e91e63,stroke-width:2px

    %% Start
    __start__(["__start__"])

    %% Node 0: Data Collection
    subgraph Node0["Node 0: Data Collection"]
        DC["sites_data 수집<br/>(8개 사업장)"]
    end

    %% Node 1: Template Loading
    subgraph Node1["Node 1: Template Loading"]
        TL["PDF 템플릿 로딩<br/>(report_template)"]
    end

    %% Node 2: Analysis (병렬)
    subgraph Node2["Node 2: Analysis (Parallel)"]
        direction TB
        N2A["Node 2A<br/>Scenario Analysis<br/>(4 SSP 시나리오)"]
        N2B["Node 2B<br/>Impact Analysis<br/>(9개 리스크)"]
        N2C["Node 2C<br/>Mitigation Strategies<br/>(3단계 시간축)"]
    end

    %% Node 3: Strategy Section
    subgraph Node3["Node 3: Strategy Section"]
        SS["Executive Summary<br/>+ Heatmap<br/>+ Priority Table"]
    end

    %% Node 4: Validator
    subgraph Node4["Node 4: Validator"]
        VAL["TCFD 7대 원칙 검증<br/>+ 길이 검증<br/>+ LLM Semantic 검증"]
    end

    %% Node 5: Composer
    subgraph Node5["Node 5: Composer"]
        COMP["전체 보고서 조립<br/>(Governance + Strategy<br/>+ Risk Mgmt + Metrics)"]
    end

    %% Node 6: Finalizer
    subgraph Node6["Node 6: Finalizer"]
        FIN["DB 저장 (JSONB)<br/>+ 다운로드 URL 생성"]
    end

    %% End
    __end__(["__end__"])

    %% 메인 플로우
    __start__ --> Node0
    Node0 --> Node1
    Node1 --> Node2

    %% Node 2 내부 플로우
    N2A --> N2B
    N2B --> N2C

    %% Node 2 → Node 3
    Node2 --> Node3

    %% Node 3 → Node 4
    Node3 --> Node4

    %% Validation 분기
    Node4 -->|"✅ Pass"| Node5
    Node4 -.->|"❌ Retry"| N2A
    Node4 -.->|"❌ Retry"| N2B
    Node4 -.->|"❌ Retry"| N2C
    Node4 -.->|"❌ Retry"| Node3

    %% Node 5 → Node 6
    Node5 --> Node6
    Node6 --> __end__

    %% 스타일 적용
    class __start__,__end__ startEnd
    class DC,TL dataNode
    class N2A,N2B,N2C,SS analysisNode
    class VAL validationNode
    class COMP,FIN outputNode
"""
    return diagram


def generate_simple_image_style_diagram():
    """
    사용자가 보여준 이미지와 동일한 스타일의 다이어그램
    """
    diagram = """flowchart TB
    %% Simple style matching the reference image

    __start__(["__start__"])
    data_collection{{"data_collection"}}
    report_template{{"report_template"}}
    building_characteristics["building_characteristics"]
    validation["validation"]
    impact_analysis["impact_analysis"]
    refiner["refiner"]
    finalization["finalization"]
    strategy_generation["strategy_generation"]
    report_generation{{"report_generation"}}
    __end__(["__end__"])

    __start__ --> data_collection
    data_collection --> report_template
    report_template --> building_characteristics
    building_characteristics --> validation
    report_template -.-> validation

    validation -.-> impact_analysis
    validation -.-> refiner
    validation --> finalization

    impact_analysis --> strategy_generation
    strategy_generation --> report_generation
    report_generation -.-> validation

    finalization --> __end__

    %% Styling
    classDef default fill:#f5f5ff,stroke:#9090ff,stroke-width:1px
    classDef terminal fill:#e8e0ff,stroke:#7c4dff,stroke-width:2px,rx:15,ry:15
    classDef hexagon fill:#e8e0ff,stroke:#7c4dff,stroke-width:2px

    class __start__,__end__ terminal
    class data_collection,report_template,report_generation hexagon
"""
    return diagram


def main():
    """
    TCFD 워크플로우 시각화 생성
    """
    print("=" * 70)
    print("TCFD Report Workflow Visualization")
    print("=" * 70)
    print()

    # 출력 디렉토리
    output_dir = os.path.dirname(os.path.abspath(__file__))

    # 1. 이미지 스타일 다이어그램
    print("[1] Simple (Image Style) diagram generating...")
    simple_diagram = generate_simple_image_style_diagram()

    simple_path = os.path.join(output_dir, "tcfd_workflow_simple.mmd")
    with open(simple_path, 'w', encoding='utf-8') as f:
        f.write(simple_diagram)
    print(f"  [OK] Saved to '{simple_path}'")

    # 2. 기본 다이어그램
    print("[2] Basic TCFD diagram generating...")
    basic_diagram = generate_tcfd_workflow_diagram()

    basic_path = os.path.join(output_dir, "tcfd_workflow.mmd")
    with open(basic_path, 'w', encoding='utf-8') as f:
        f.write(basic_diagram)
    print(f"  [OK] Saved to '{basic_path}'")

    # 3. 상세 다이어그램
    print("[3] Detailed TCFD diagram generating...")
    detailed_diagram = generate_tcfd_detailed_diagram()

    detailed_path = os.path.join(output_dir, "tcfd_workflow_detailed.mmd")
    with open(detailed_path, 'w', encoding='utf-8') as f:
        f.write(detailed_diagram)
    print(f"  [OK] Saved to '{detailed_path}'")

    print()
    print("=" * 70)
    print("Generated files:")
    print(f"  1. tcfd_workflow_simple.mmd - 이미지 스타일 (단순)")
    print(f"  2. tcfd_workflow.mmd - 기본 워크플로우")
    print(f"  3. tcfd_workflow_detailed.mmd - 상세 7-Node 구조")
    print()
    print("View at: https://mermaid.live")
    print("=" * 70)


if __name__ == "__main__":
    main()
