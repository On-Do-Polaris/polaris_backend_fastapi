'''
파일명: visualize_workflow.py
최종 수정일: 2025-11-05
버전: v00
파일 개요: 워크플로우 시각화 스크립트 (Mermaid 다이어그램 및 PNG 생성)
'''
from config.settings import Config
from workflow import create_workflow_graph, visualize_workflow, print_workflow_structure


def main():
	"""
	워크플로우 그래프 생성 및 시각화
	Mermaid 다이어그램(.mmd)과 PNG 이미지 생성

	Returns:
		None
	"""
	print("=" * 70)
	print("SKAX Physical Risk Analysis Workflow Visualization")
	print("=" * 70)
	print()

	# 설정 로드
	config = Config()

	# 워크플로우 그래프 생성
	print("[1] Workflow graph creating...")
	graph = create_workflow_graph(config)
	print("[OK] Workflow graph creation completed")
	print()

	# 텍스트 구조 출력
	print("[2] Workflow structure:")
	print_workflow_structure()
	print()

	# 시각화
	print("[3] Workflow visualization generating...")

	# 3-1. Mermaid 다이어그램 생성
	print("  [3-1] Mermaid diagram generating...")
	try:
		mermaid_diagram = graph.get_graph().draw_mermaid()

		# workflow_diagram.mmd 파일로 저장
		with open("workflow_diagram.mmd", 'w', encoding='utf-8') as f:
			f.write(mermaid_diagram)

		print("  [OK] Mermaid diagram saved to 'workflow_diagram.mmd'")

	except Exception as e:
		print(f"  [ERROR] Mermaid diagram generation failed: {e}")

	# 3-2. PNG 이미지 생성
	print("  [3-2] PNG image generating...")
	try:
		png_data = graph.get_graph().draw_mermaid_png()

		# workflow_diagram.png 파일로 저장
		with open("workflow_diagram.png", 'wb') as f:
			f.write(png_data)

		print("  [OK] PNG image saved to 'workflow_diagram.png'")

	except ImportError as e:
		print("  [WARN] Required library for PNG generation not found")
		print("  [INFO] Install: pip install 'pillow'")
	except Exception as e:
		print(f"  [WARN] PNG image generation failed: {e}")
		print("  [INFO] Convert Mermaid diagram(.mmd) at https://mermaid.live")

	print()
	print("=" * 70)
	print("Generated files:")
	print("  - workflow_diagram.mmd (Mermaid diagram)")
	print("  - workflow_diagram.png (PNG image, if available)")
	print()
	print("View Mermaid diagram: https://mermaid.live")
	print("  (SVG/PNG conversion available)")
	print("=" * 70)

	print()
	print("[COMPLETED] Workflow visualization process completed")


if __name__ == "__main__":
	main()
