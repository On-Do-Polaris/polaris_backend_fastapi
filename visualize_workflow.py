"""
Workflow Visualization Script
워크플로우 시각화 스크립트
"""
from config.settings import Config
from workflow import create_workflow_graph, visualize_workflow, print_workflow_structure


def main():
    """
    워크플로우 그래프 생성 및 시각화
    """
    print("=" * 70)
    print("SKAX 물리적 리스크 분석 워크플로우 시각화")
    print("=" * 70)
    print()

    # 설정 로드
    config = Config()

    # 워크플로우 그래프 생성
    print("[1] 워크플로우 그래프 생성 중...")
    graph = create_workflow_graph(config)
    print("[OK] 워크플로우 그래프 생성 완료")
    print()

    # 텍스트 구조 출력
    print("[2] 워크플로우 구조 출력:")
    print_workflow_structure()
    print()

    # 시각화
    print("[3] 워크플로우 시각화 생성 중...")

    # 3-1. Mermaid 다이어그램 생성
    print("  [3-1] Mermaid 다이어그램 생성 중...")
    try:
        mermaid_diagram = graph.get_graph().draw_mermaid()

        # workflow_diagram.mmd 파일로 저장
        with open("workflow_diagram.mmd", 'w', encoding='utf-8') as f:
            f.write(mermaid_diagram)

        print("  [OK] Mermaid 다이어그램이 'workflow_diagram.mmd'에 저장되었습니다.")

    except Exception as e:
        print(f"  [ERROR] Mermaid 다이어그램 생성 실패: {e}")

    # 3-2. PNG 이미지 생성
    print("  [3-2] PNG 이미지 생성 중...")
    try:
        png_data = graph.get_graph().draw_mermaid_png()

        # workflow_diagram.png 파일로 저장
        with open("workflow_diagram.png", 'wb') as f:
            f.write(png_data)

        print("  [OK] PNG 이미지가 'workflow_diagram.png'에 저장되었습니다.")

    except ImportError as e:
        print("  [WARN] PNG 생성을 위한 라이브러리가 없습니다.")
        print("  [INFO] 설치: pip install 'pygraphviz' 또는 'pillow'")
    except Exception as e:
        print(f"  [WARN] PNG 이미지 생성 실패: {e}")
        print("  [INFO] Mermaid 다이어그램 파일(.mmd)을 https://mermaid.live 에서 변환하세요.")

    print()
    print("=" * 70)
    print("생성된 파일:")
    print("  - workflow_diagram.mmd (Mermaid 다이어그램)")
    print("  - workflow_diagram.png (PNG 이미지, 생성 가능한 경우)")
    print()
    print("Mermaid 다이어그램 보기: https://mermaid.live")
    print("=" * 70)

    print()
    print("[완료] 워크플로우 시각화 프로세스 완료")


if __name__ == "__main__":
    main()
