#!/usr/bin/env python3
"""
Node 1 RAG 연동 테스트
- RAGEngine으로 실제 벡터 DB에서 스타일 참조 가져오기
"""

import asyncio
import json
import sys
from pathlib import Path

# 프로젝트 루트 추가
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))


async def test_node1_rag():
    """Node 1에서 사용하는 RAG 검색 테스트"""
    print("=" * 60)
    print("Node 1 RAG 연동 테스트")
    print("=" * 60)

    from ai_agent.utils.rag_helpers import RAGEngine

    # Node 1에서 사용하는 것과 동일한 설정
    rag = RAGEngine(source="benchmark")

    company_name = "SK"

    # Node 1의 _load_rag_references와 동일한 쿼리
    query_text = f"""
    {company_name} 지속가능경영보고서 문단 구조,
    TCFD 공시 방식,
    ESG KPI 서술 스타일
    """

    print(f"\n📝 검색 쿼리:\n{query_text.strip()}\n")

    # RAG 검색 실행
    style_references = rag.query(query_text=query_text, top_k=20)

    print(f"✅ 검색 결과: {len(style_references)}개 문서\n")

    # 결과 상세 출력
    print("-" * 60)
    print("상위 5개 결과:")
    print("-" * 60)

    for i, ref in enumerate(style_references[:5], 1):
        print(f"\n[{i}] Score: {ref['score']:.4f}")
        print(f"    Source: {ref['source']}")
        print(f"    Collection: {ref.get('collection', 'N/A')}")
        text_preview = ref['text'][:200].replace('\n', ' ')
        print(f"    Text: {text_preview}...")

    # Citations 생성
    citations = rag.get_citations(style_references)

    print("\n" + "-" * 60)
    print("생성된 Citations:")
    print("-" * 60)
    for citation in citations[:5]:
        print(f"  - {citation}")

    # JSON으로 저장
    output_file = Path(__file__).parent / "test_node1_rag_output.json"
    output_data = {
        "query": query_text.strip(),
        "total_results": len(style_references),
        "style_references": style_references,
        "citations": citations
    }

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)

    print(f"\n📁 결과 저장: {output_file}")

    return style_references, citations


if __name__ == "__main__":
    asyncio.run(test_node1_rag())
