'''
파일명: visualize_complete_flow.py
최종 수정일: 2025-12-01
버전: v01
파일 개요: 완전한 워크플로우 시각화 (메인 + 추가 데이터 플로우)
'''
import sys
import os

# 직접 실행될 경우 패키지 경로 추가
if __name__ == "__main__":
	current_dir = os.path.dirname(os.path.abspath(__file__))
	parent_dir = os.path.dirname(current_dir)
	sys.path.insert(0, parent_dir)

	from ai_agent.config.settings import Config
	from ai_agent.workflow.graph import create_workflow_graph
else:
	from .config.settings import Config
	from .workflow.graph import create_workflow_graph


def generate_additional_data_flow_diagram():
	"""
	추가 데이터 플로우 다이어그램 생성 (Mermaid)
	"""
	diagram = """---
config:
  flowchart:
    curve: basis
---
graph TB;
    %% 추가 데이터 플로우 (워크플로우 외부 전처리)

    Input[["사용자 입력<br/>(additional_data)"]]
    Helper["AdditionalDataHelper<br/>(LLM 1회 호출)"]
    Guidelines[["Agent별 가이드라인<br/>(additional_data_guidelines)"]]

    Input -->|"raw_text, metadata"| Helper
    Helper -->|"generate_guidelines()"| Guidelines

    subgraph AgentGuidelines["가이드라인 내용"]
        direction LR
        G1["building_characteristics:<br/>relevance, suggested_insights"]
        G2["impact_analysis:<br/>relevance, suggested_insights"]
        G3["strategy_generation:<br/>relevance, suggested_insights"]
        G4["report_generation:<br/>relevance, suggested_insights"]
    end

    Guidelines --> AgentGuidelines

    %% 메인 워크플로우 연결 (점선)
    Guidelines -.->|"State에 주입"| MainWorkflow["메인 워크플로우<br/>(LangGraph)"]

    %% 스타일
    classDef preprocessing fill:#e1f5ff,stroke:#0288d1,stroke-width:2px
    classDef guideline fill:#fff9c4,stroke:#fbc02d,stroke-width:2px
    classDef main fill:#f2f0ff,stroke:#7c4dff,stroke-width:2px

    class Input,Helper preprocessing
    class Guidelines,AgentGuidelines guideline
    class MainWorkflow main
"""
	return diagram


def generate_integrated_flow_diagram():
	"""
	통합 플로우 다이어그램 생성 (추가 데이터 + 메인 워크플로우)
	"""
	diagram = """---
config:
  flowchart:
    curve: basis
---
graph TB;
    %% ===== 추가 데이터 전처리 =====
    subgraph PreProcess["🔧 추가 데이터 전처리 (워크플로우 외부)"]
        direction TB
        UserData[["사용자 입력<br/>(additional_data)"]]
        Helper["AdditionalDataHelper<br/>(LLM 1회 호출)"]
        Guidelines{{"가이드라인 생성<br/>(4개 Agent)"}}

        UserData --> Helper
        Helper --> Guidelines
    end

    %% ===== 메인 워크플로우 =====
    subgraph MainFlow["🚀 메인 워크플로우 (LangGraph)"]
        direction TB

        Start(["__start__"])
        DC["1. Data Collection"]

        subgraph Parallel1["병렬 실행 (ModelOps)"]
            PRS["2. Physical Risk Score<br/>(H×E×V)"]
            AAL["3. AAL Analysis<br/>(P×D)"]
        end

        RI["4. Risk Integration"]

        subgraph Parallel2["Fork-Join 병렬"]
            BC["BC. Building Characteristics<br/>(LLM 정성 분석)"]

            subgraph ReportChain["Report Chain"]
                RT["5. Report Template"]
                IA["6. Impact Analysis"]
                SG["7. Strategy Generation"]
                RG["8. Report Generation"]
            end
        end

        Val["9. Validation<br/>(Report + BC 통합 검증)"]
        Fin["10. Finalization"]
        End(["__end__"])

        Start --> DC
        DC --> PRS
        DC --> AAL
        PRS --> RI
        AAL --> RI
        RI --> BC
        RI --> RT
        RT --> IA
        IA --> SG
        SG --> RG
        BC --> Val
        RG --> Val
        Val -->|"통과"| Fin
        Val -.->|"BC 이슈"| BC
        Val -.->|"Impact 이슈"| IA
        Val -.->|"Strategy 이슈"| SG
        Fin --> End
    end

    %% ===== 가이드라인 주입 (점선) =====
    Guidelines -.->|"가이드라인 주입<br/>(relevance ≥ 0.4)"| BC
    Guidelines -.->|"가이드라인 주입"| IA
    Guidelines -.->|"가이드라인 주입"| SG
    Guidelines -.->|"가이드라인 주입"| RG

    %% 스타일
    classDef preprocessing fill:#e1f5ff,stroke:#0288d1,stroke-width:3px
    classDef guideline fill:#fff9c4,stroke:#fbc02d,stroke-width:3px
    classDef main fill:#f2f0ff,stroke:#7c4dff,stroke-width:2px
    classDef parallel fill:#e8f5e9,stroke:#4caf50,stroke-width:2px

    class UserData,Helper preprocessing
    class Guidelines guideline
    class Start,DC,RI,Val,Fin,End main
    class PRS,AAL,BC,RT,IA,SG,RG parallel
"""
	return diagram


def main():
	"""
	완전한 워크플로우 시각화 생성
	"""
	print("=" * 70)
	print("Complete Workflow Visualization (Main + Additional Data Flow)")
	print("=" * 70)
	print()

	# 1. 추가 데이터 플로우 다이어그램
	print("[1] Additional Data Flow diagram generating...")
	additional_flow = generate_additional_data_flow_diagram()

	with open("additional_data_flow.mmd", 'w', encoding='utf-8') as f:
		f.write(additional_flow)
	print("  [OK] Saved to 'additional_data_flow.mmd'")

	# 2. 통합 플로우 다이어그램
	print("[2] Integrated Flow diagram generating...")
	integrated_flow = generate_integrated_flow_diagram()

	with open("integrated_workflow.mmd", 'w', encoding='utf-8') as f:
		f.write(integrated_flow)
	print("  [OK] Saved to 'integrated_workflow.mmd'")

	print()
	print("=" * 70)
	print("Generated files:")
	print("  1. additional_data_flow.mmd - 추가 데이터 전처리 플로우")
	print("  2. integrated_workflow.mmd - 통합 워크플로우 (전처리 + 메인)")
	print()
	print("View at: https://mermaid.live")
	print("=" * 70)

	print()
	print("[INFO] 추가 데이터 플로우 동작 방식:")
	print("  1. 사용자가 additional_data를 제공")
	print("  2. AdditionalDataHelper가 LLM 1회 호출")
	print("  3. 4개 Agent에 대한 가이드라인 생성")
	print("  4. State에 additional_data_guidelines 저장")
	print("  5. 각 Agent가 실행 시 가이드라인 참조")
	print("  6. relevance >= 0.4인 경우에만 적용")


if __name__ == "__main__":
	main()
