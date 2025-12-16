#!/usr/bin/env python3
"""
기존 Qdrant 컬렉션 검색 테스트 스크립트

이 스크립트는 다음을 테스트합니다:
1. ExistingCollectionSearcher 초기화
2. SK TCFD 보고서 검색
3. RAGEngine 통합 검색
4. 검색 결과 품질 확인

Usage:
    python ai_agent/utils/scripts/test_existing_collection.py
"""

import os
import sys
import time
from pathlib import Path

# 프로젝트 루트를 PYTHONPATH에 추가
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))


def test_existing_collection_searcher():
    """ExistingCollectionSearcher 직접 테스트"""
    print("\n" + "=" * 60)
    print("1. ExistingCollectionSearcher 직접 테스트")
    print("=" * 60)

    try:
        from ai_agent.utils.qdrant_vector_store import ExistingCollectionSearcher

        print("\n1.1. 초기화 중...")
        start_time = time.time()
        searcher = ExistingCollectionSearcher()
        init_time = time.time() - start_time
        print(f"✅ 초기화 완료 ({init_time:.2f}초)")
        print(f"   - 임베딩 모델 차원: {searcher.vector_size}")
        print(f"   - 사용 가능한 컬렉션: {len(searcher._available_collections)}")

        # 컬렉션 통계 출력
        print("\n1.2. 컬렉션 통계:")
        stats = searcher.get_collection_stats()
        for name, info in stats['collections'].items():
            if 'error' not in info:
                print(f"   - {name}: {info.get('points_count', 0)} points")

        # SK TCFD 보고서 검색 테스트
        print("\n1.3. SK TCFD 보고서 검색 테스트:")
        test_queries = [
            "기후 거버넌스 전략",
            "탄소중립 목표",
            "물리적 리스크 분석",
        ]

        for query in test_queries:
            print(f"\n   쿼리: '{query}'")
            start_time = time.time()
            results = searcher.search_tcfd_report(query_text=query, top_k=3)
            search_time = time.time() - start_time

            print(f"   검색 시간: {search_time * 1000:.0f}ms")
            print(f"   결과 수: {len(results)}")

            if results:
                for i, result in enumerate(results[:2], 1):
                    print(f"\n   [{i}] Score: {result['score']:.4f}")
                    print(f"       Source: {result['source']}")
                    text_preview = result['text'][:150].replace('\n', ' ')
                    print(f"       Text: {text_preview}...")

        return True

    except Exception as e:
        print(f"❌ 실패: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_rag_engine_integration():
    """RAGEngine 통합 테스트"""
    print("\n" + "=" * 60)
    print("2. RAGEngine 통합 테스트")
    print("=" * 60)

    try:
        from ai_agent.utils.rag_helpers import RAGEngine

        # 2.1. tcfd_report 모드 테스트
        print("\n2.1. RAGEngine(source='tcfd_report') 테스트:")
        rag = RAGEngine(source="tcfd_report")

        if rag.client is None:
            print("⚠️  클라이언트 초기화 실패 (Mock 모드)")
            return False

        query = "ESG 경영 전략"
        print(f"   쿼리: '{query}'")

        start_time = time.time()
        results = rag.query(query, top_k=5)
        search_time = time.time() - start_time

        print(f"   검색 시간: {search_time * 1000:.0f}ms")
        print(f"   결과 수: {len(results)}")

        if results:
            print(f"\n   상위 결과:")
            for i, result in enumerate(results[:3], 1):
                print(f"   [{i}] Score: {result['score']:.4f} | {result['source']}")

        # 2.2. existing 모드 테스트 (모든 컬렉션)
        print("\n2.2. RAGEngine(source='existing') 테스트:")
        rag_all = RAGEngine(source="existing")

        query = "물리적 리스크 평가"
        print(f"   쿼리: '{query}'")

        results = rag_all.query(query, top_k=5)
        print(f"   결과 수: {len(results)}")

        if results:
            print(f"\n   상위 결과:")
            for i, result in enumerate(results[:3], 1):
                collection = result.get('collection', 'N/A')
                print(f"   [{i}] Score: {result['score']:.4f} | Collection: {collection}")

        # 2.3. citations 테스트
        print("\n2.3. Citations 생성 테스트:")
        citations = rag.get_citations(results)
        for citation in citations[:3]:
            print(f"   - {citation}")

        return True

    except Exception as e:
        print(f"❌ 실패: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_template_loading_integration():
    """TemplateLoadingNode와의 통합 테스트"""
    print("\n" + "=" * 60)
    print("3. TemplateLoadingNode 통합 테스트 (RAG 검색만)")
    print("=" * 60)

    try:
        from ai_agent.utils.rag_helpers import RAGEngine

        # TemplateLoadingNode에서 사용하는 RAGEngine 시뮬레이션
        rag = RAGEngine(source="benchmark")  # benchmark = existing

        query = """
        SK 지속가능경영보고서 문단 구조,
        TCFD 공시 방식,
        ESG KPI 서술 스타일
        """
        print(f"   쿼리: '{query.strip()[:50]}...'")

        start_time = time.time()
        results = rag.query(query, top_k=20)
        search_time = time.time() - start_time

        print(f"   검색 시간: {search_time * 1000:.0f}ms")
        print(f"   결과 수: {len(results)}")

        if results:
            print(f"\n   상위 5개 결과 미리보기:")
            for i, result in enumerate(results[:5], 1):
                text_preview = result['text'][:80].replace('\n', ' ')
                print(f"   [{i}] {result['score']:.3f} | {text_preview}...")

            # Citations 생성
            citations = rag.get_citations(results)
            print(f"\n   생성된 Citations ({len(citations)}개):")
            for citation in citations[:5]:
                print(f"   - {citation}")

        return True

    except Exception as e:
        print(f"❌ 실패: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """메인 테스트 실행"""
    print("=" * 60)
    print("기존 Qdrant 컬렉션 검색 테스트")
    print("=" * 60)

    results = []

    # 테스트 실행
    results.append(("ExistingCollectionSearcher", test_existing_collection_searcher()))
    results.append(("RAGEngine 통합", test_rag_engine_integration()))
    results.append(("TemplateLoadingNode 통합", test_template_loading_integration()))

    # 결과 요약
    print("\n" + "=" * 60)
    print("테스트 결과 요약")
    print("=" * 60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {status}: {test_name}")

    print(f"\n   Total: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 모든 테스트 통과!")
        return 0
    else:
        print(f"\n⚠️  {total - passed} 개 테스트 실패")
        return 1


if __name__ == "__main__":
    sys.exit(main())
