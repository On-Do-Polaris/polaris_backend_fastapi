'''
파일명: visualize_tcfd_workflow.py
작성일: 2025-12-14
버전: v01
파일 개요: TCFD Report Workflow 시각화 스크립트 (Mermaid 다이어그램 생성)
변경 이력:
    - 2025-12-14: v01 - 7개 노드 구조 (Option 1) 시각화
'''
import os


def generate_mermaid_diagram() -> str:
    """
    TCFD Report Workflow Mermaid 다이어그램 생성 (7개 노드 구조)

    Returns:
        str: Mermaid 다이어그램 텍스트
    """
    diagram = """graph TB
    subgraph Input
        START([🔵 시작<br/>site_ids: List int<br/>excel_file: str optional<br/>user_id: int])
    end

    subgraph "Phase 1: Data Collection"
        N0["<b>Node 0: Data Loading</b><br/>─────────────────<br/>▸ DB 직접 쿼리 8 사업장<br/>▸ Building Characteristics Agent<br/>▸ Additional Data Agent 조건부<br/><br/>📤 sites_data, building_guidelines, excel_guidelines"]

        N1["<b>Node 1: Template Loading</b><br/>─────────────────<br/>▸ RAG 엔진<br/>▸ TCFD 구조 로딩<br/>▸ 스타일 참조<br/><br/>📤 tcfd_structure, style_references, citations"]
    end

    subgraph "Phase 2: Analysis Layer"
        N2A["<b>Node 2-A: Scenario Analysis</b><br/>─────────────────<br/>▸ 4개 시나리오 AAL 계산<br/>▸ 8개 사업장 병렬 처리<br/><br/>📊 TableBlock 생성<br/>시나리오별 AAL 비교표<br/><br/>📤 scenarios, scenario_table"]

        N2B["<b>Node 2-B: Impact Analysis</b><br/>─────────────────<br/>▸ Top 5 리스크 영향 분석<br/>▸ 5개 리스크 병렬 처리<br/><br/>📝 TextBlock 생성 5개<br/>P1~P5 영향 분석<br/><br/>📤 top_5_risks, impact_blocks"]

        N2C["<b>Node 2-C: Mitigation Strategies</b><br/>─────────────────<br/>▸ Top 5 리스크 대응 방안<br/>▸ 5개 리스크 병렬 처리<br/><br/>📝 TextBlock 생성 5개<br/>P1~P5 대응 전략<br/><br/>📤 mitigation_strategies, mitigation_blocks"]
    end

    subgraph "Phase 3: Formatting Layer"
        N3["<b>Node 3: Strategy Section</b><br/>─────────────────<br/>▸ Node 2-A/B/C 결과 조립<br/>▸ Executive Summary 생성<br/><br/>🔥 HeatmapTableBlock 생성<br/>사업장별 리스크 AAL 분포<br/><br/>📤 strategy_section Section"]
    end

    subgraph "Phase 4: Validation & Composition"
        N4["<b>Node 4: Validator</b><br/>─────────────────<br/>▸ TCFD 7대 원칙 검증<br/>▸ 누락 섹션 체크<br/>▸ 1회 재생성 필요시<br/><br/>📤 validated_sections, validation_result"]

        N5["<b>Node 5: Composer</b><br/>─────────────────<br/>▸ Risk Management 템플릿<br/>▸ Governance 하드코딩<br/>▸ Appendix 하드코딩<br/>▸ Metrics & Targets<br/><br/>📈 LineChartBlock 생성<br/>AAL 추이 차트 2024-2100<br/><br/>▸ 목차 생성<br/>▸ 전체 조립<br/><br/>📤 report TCFDReport"]
    end

    subgraph "Phase 5: Finalization"
        N6["<b>Node 6: Finalizer</b><br/>─────────────────<br/>▸ JSONB DB 저장<br/>▸ 사업장-보고서 관계 저장<br/><br/>📤 success, report_id, download_url"]
    end

    subgraph Output
        END([🟢 완료<br/>report_id: int<br/>download_url: str])
    end

    START --> N0
    N0 --> N1
    N1 --> N2A
    N2A --> N2B
    N2B --> N2C
    N2C --> N3
    N3 --> N4
    N4 --> N5
    N5 --> N6
    N6 --> END

    style START fill:#4CAF50,stroke:#2E7D32,stroke-width:3px,color:#fff
    style END fill:#2196F3,stroke:#1565C0,stroke-width:3px,color:#fff

    style N0 fill:#E3F2FD,stroke:#1976D2,stroke-width:2px
    style N1 fill:#FFF3E0,stroke:#F57C00,stroke-width:2px

    style N2A fill:#F3E5F5,stroke:#7B1FA2,stroke-width:2px
    style N2B fill:#F3E5F5,stroke:#7B1FA2,stroke-width:2px
    style N2C fill:#F3E5F5,stroke:#7B1FA2,stroke-width:2px

    style N3 fill:#E8F5E9,stroke:#388E3C,stroke-width:2px

    style N4 fill:#FFF9C4,stroke:#F9A825,stroke-width:2px
    style N5 fill:#FFEBEE,stroke:#C62828,stroke-width:2px

    style N6 fill:#FCE4EC,stroke:#AD1457,stroke-width:2px
"""
    return diagram


def generate_chart_matrix_diagram() -> str:
    """
    표/차트 생성 매트릭스 다이어그램

    Returns:
        str: Mermaid 다이어그램 텍스트
    """
    diagram = """graph LR
    subgraph "JSON Block 생성"
        N2A[Node 2-A] -->|TableBlock| T1["📊 시나리오별 AAL 비교표<br/>SSP1-2.6, SSP2-4.5, SSP3-7.0, SSP5-8.5"]

        N2B[Node 2-B] -->|TextBlock x5| T2["📝 P1: 하천범람 영향<br/>📝 P2: 태풍 영향<br/>📝 P3: 도시침수 영향<br/>📝 P4: 극심한고온 영향<br/>📝 P5: 해수면상승 영향"]

        N2C[Node 2-C] -->|TextBlock x5| T3["📝 P1: 하천범람 대응<br/>📝 P2: 태풍 대응<br/>📝 P3: 도시침수 대응<br/>📝 P4: 극심한고온 대응<br/>📝 P5: 해수면상승 대응"]

        N3[Node 3] -->|HeatmapTableBlock| T4["🔥 사업장별 리스크 분포<br/>Gray/Yellow/Orange/Red<br/>8개 사업장 x 9개 리스크"]

        N5[Node 5] -->|LineChartBlock| T5["📈 AAL 추이 차트<br/>2024-2100<br/>4개 시나리오 비교"]
    end

    style N2A fill:#F3E5F5,stroke:#7B1FA2
    style N2B fill:#F3E5F5,stroke:#7B1FA2
    style N2C fill:#F3E5F5,stroke:#7B1FA2
    style N3 fill:#E8F5E9,stroke:#388E3C
    style N5 fill:#FFEBEE,stroke:#C62828

    style T1 fill:#FFF9C4
    style T2 fill:#FFF9C4
    style T3 fill:#FFF9C4
    style T4 fill:#FFCCBC
    style T5 fill:#BBDEFB
"""
    return diagram


def print_workflow_structure():
    """
    TCFD Report Workflow 텍스트 구조 출력
    """
    structure = """
TCFD Report Generation Workflow (7 Nodes)
==========================================

Input:
  - site_ids: List[int] (8개 사업장)
  - excel_file: Optional[str] (추가 데이터)
  - user_id: int

─────────────────────────────────────────

Phase 1: Data Collection
-------------------------
Node 0: Data Loading
  ├─ DB 직접 쿼리 (8개 사업장)
  ├─ Building Characteristics Agent
  └─ Additional Data Agent (조건부)
  Output: sites_data, building_guidelines, excel_guidelines

Node 1: Template Loading
  ├─ RAG 엔진
  ├─ TCFD 구조 로딩
  └─ 스타일 참조
  Output: tcfd_structure, style_references, citations

─────────────────────────────────────────

Phase 2: Analysis Layer
------------------------
Node 2-A: Scenario Analysis
  ├─ 4개 시나리오 AAL 계산
  ├─ 8개 사업장 병렬 처리
  └─ 📊 TableBlock 생성 (시나리오별 AAL 비교표)
  Output: scenarios, scenario_table

Node 2-B: Impact Analysis
  ├─ Top 5 리스크 영향 분석
  ├─ 5개 리스크 병렬 처리
  └─ 📝 TextBlock 생성 x5 (P1~P5 영향)
  Output: top_5_risks, impact_blocks

Node 2-C: Mitigation Strategies
  ├─ Top 5 리스크 대응 방안
  ├─ 5개 리스크 병렬 처리
  └─ 📝 TextBlock 생성 x5 (P1~P5 대응)
  Output: mitigation_strategies, mitigation_blocks

─────────────────────────────────────────

Phase 3: Formatting Layer
--------------------------
Node 3: Strategy Section
  ├─ Node 2-A/B/C 결과 조립
  ├─ Executive Summary 생성
  └─ 🔥 HeatmapTableBlock 생성 (사업장별 리스크 분포)
  Output: strategy_section (Section)

─────────────────────────────────────────

Phase 4: Validation & Composition
----------------------------------
Node 4: Validator
  ├─ TCFD 7대 원칙 검증
  ├─ 누락 섹션 체크
  └─ 1회 재생성 (필요시)
  Output: validated_sections, validation_result

Node 5: Composer
  ├─ Risk Management (템플릿)
  ├─ Governance (하드코딩)
  ├─ Appendix (하드코딩)
  ├─ Metrics & Targets
  ├─ 📈 LineChartBlock 생성 (AAL 추이 차트)
  ├─ 목차 생성
  └─ 전체 조립
  Output: report (TCFDReport)

─────────────────────────────────────────

Phase 5: Finalization
----------------------
Node 6: Finalizer
  ├─ JSONB DB 저장
  └─ 사업장-보고서 관계 저장
  Output: success, report_id, download_url

─────────────────────────────────────────

Output:
  - report_id: int
  - download_url: str

==========================================
Total Processing Time: 3.5-4.5 minutes (8 sites)
==========================================
"""
    print(structure)


def print_chart_generation_table():
    """
    표/차트 생성 책임 테이블 출력
    """
    table = """
JSON Block 생성 책임
===================

┌─────────┬──────────────────────────────┬────────────────────────┐
│  노드   │         생성 항목            │      스키마 타입       │
├─────────┼──────────────────────────────┼────────────────────────┤
│ Node 2-A│ 시나리오별 AAL 비교표        │ TableBlock             │
├─────────┼──────────────────────────────┼────────────────────────┤
│ Node 2-B│ P1~P5 영향 분석 텍스트       │ List[TextBlock] (5개)  │
├─────────┼──────────────────────────────┼────────────────────────┤
│ Node 2-C│ P1~P5 대응 방안 텍스트       │ List[TextBlock] (5개)  │
├─────────┼──────────────────────────────┼────────────────────────┤
│ Node 3  │ 사업장별 리스크 Heatmap      │ HeatmapTableBlock      │
├─────────┼──────────────────────────────┼────────────────────────┤
│ Node 5  │ AAL 추이 차트 (2024-2100)    │ LineChartBlock         │
└─────────┴──────────────────────────────┴────────────────────────┘

각 노드가 자기 섹션의 표/차트를 직접 생성
"""
    print(table)


def main():
    """
    TCFD Report Workflow 시각화 메인 함수
    """
    print("=" * 70)
    print("TCFD Report Generation Workflow Visualization (7 Nodes)")
    print("=" * 70)
    print()

    # 텍스트 구조 출력
    print("[1] Workflow structure:")
    print_workflow_structure()
    print()

    # 표/차트 생성 책임 테이블
    print("[2] Chart generation responsibilities:")
    print_chart_generation_table()
    print()

    # 시각화
    print("[3] Mermaid diagram generating...")

    # 3-1. 메인 워크플로우 다이어그램
    print("  [3-1] Main workflow diagram...")
    try:
        mermaid_diagram = generate_mermaid_diagram()

        # 현재 스크립트 위치에 저장
        output_path = os.path.join(
            os.path.dirname(__file__),
            "tcfd_workflow_diagram.mmd"
        )

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(mermaid_diagram)

        print(f"  [OK] Saved to '{output_path}'")

    except Exception as e:
        print(f"  [ERROR] Failed: {e}")

    # 3-2. 표/차트 매트릭스 다이어그램
    print("  [3-2] Chart generation matrix diagram...")
    try:
        chart_diagram = generate_chart_matrix_diagram()

        output_path = os.path.join(
            os.path.dirname(__file__),
            "tcfd_chart_matrix.mmd"
        )

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(chart_diagram)

        print(f"  [OK] Saved to '{output_path}'")

    except Exception as e:
        print(f"  [ERROR] Failed: {e}")

    print()
    print("=" * 70)
    print("Generated files:")
    print("  - tcfd_workflow_diagram.mmd (Main workflow)")
    print("  - tcfd_chart_matrix.mmd (Chart generation matrix)")
    print()
    print("View Mermaid diagrams: https://mermaid.live")
    print("  (Copy & paste .mmd file content)")
    print("=" * 70)

    print()
    print("[COMPLETED] TCFD workflow visualization completed")


if __name__ == "__main__":
    main()
