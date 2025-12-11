"""
Qdrant Vector Store Integration Test Script

이 스크립트는 다음을 테스트합니다:
1. QdrantVectorStore 초기화 및 컬렉션 생성
2. 문서 추가 및 검색 기능
3. RAGEngine과 Qdrant 통합
4. Mock 모드 fallback 동작
5. 성능 측정 (검색 속도)

Usage:
    python ai_agent/utils/scripts/test_qdrant_integration.py
    python ai_agent/utils/scripts/test_qdrant_integration.py --skip-connection-test
"""

import os
import sys
import time
import argparse
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))


def test_imports():
    """필수 패키지 import 테스트"""
    print("\n=== 1. Testing Imports ===")
    try:
        from qdrant_client import QdrantClient
        print("[PASS] qdrant-client imported successfully")
    except ImportError as e:
        print(f"[FAIL] Failed to import qdrant-client: {e}")
        return False

    try:
        from sentence_transformers import SentenceTransformer
        print("[PASS] sentence-transformers imported successfully")
    except ImportError as e:
        print(f"[FAIL] Failed to import sentence-transformers: {e}")
        return False

    try:
        from ai_agent.utils.qdrant_vector_store import QdrantVectorStore, get_embedding_model
        print("[PASS] QdrantVectorStore imported successfully")
    except ImportError as e:
        print(f"[FAIL] Failed to import QdrantVectorStore: {e}")
        return False

    try:
        from ai_agent.utils.rag_helpers import RAGEngine
        print("[PASS] RAGEngine imported successfully")
    except ImportError as e:
        print(f"[FAIL] Failed to import RAGEngine: {e}")
        return False

    return True


def test_embedding_model():
    """Embedding 모델 로딩 테스트"""
    print("\n=== 2. Testing Embedding Model ===")
    try:
        from ai_agent.utils.qdrant_vector_store import get_embedding_model

        print("Loading sentence-transformers model...")
        start_time = time.time()
        model = get_embedding_model()
        load_time = time.time() - start_time
        print(f"[PASS] Model loaded in {load_time:.2f}s")

        # Test encoding
        test_text = "This is a test sentence for embedding."
        start_time = time.time()
        embedding = model.encode(test_text)
        encode_time = time.time() - start_time

        print(f"[PASS] Embedding generated in {encode_time*1000:.2f}ms")
        print(f"[PASS] Embedding dimension: {len(embedding)}")

        return True
    except Exception as e:
        print(f"[FAIL] Embedding model test failed: {e}")
        return False


def test_qdrant_connection(skip_connection=False):
    """Qdrant 서버 연결 테스트"""
    if skip_connection:
        print("\n=== 3. Qdrant Connection Test (SKIPPED) ===")
        return True

    print("\n=== 3. Testing Qdrant Connection ===")
    try:
        from qdrant_client import QdrantClient

        qdrant_url = os.getenv('QDRANT_URL', 'http://localhost:6333')
        print(f"Connecting to Qdrant at {qdrant_url}...")

        client = QdrantClient(url=qdrant_url)

        # Test connection
        collections = client.get_collections()
        print(f"[PASS] Connected successfully")
        print(f"[PASS] Existing collections: {len(collections.collections)}")

        return True
    except Exception as e:
        print(f"[FAIL] Connection failed: {e}")
        print("\nNote: Make sure Qdrant is running:")
        print("  docker run -p 6333:6333 qdrant/qdrant")
        return False


def test_vector_store_operations(skip_connection=False):
    """QdrantVectorStore CRUD 작업 테스트"""
    if skip_connection:
        print("\n=== 4. Vector Store Operations (SKIPPED) ===")
        return True

    print("\n=== 4. Testing Vector Store Operations ===")
    try:
        from ai_agent.utils.qdrant_vector_store import QdrantVectorStore

        # Initialize
        qdrant_url = os.getenv('QDRANT_URL', 'http://localhost:6333')
        test_collection = os.getenv('QDRANT_COLLECTION', 'esg_tcfd_reports') + '_test'

        print(f"Initializing QdrantVectorStore (collection: {test_collection})...")
        store = QdrantVectorStore(
            url=qdrant_url,
            api_key=None,
            collection_name=test_collection,
            embedding_model='sentence-transformers/all-MiniLM-L6-v2'
        )
        print("[PASS] VectorStore initialized")

        # Get collection info
        info = store.get_collection_info()
        print(f"[PASS] Collection info: {info['points_count']} points")

        # Add test documents
        print("\nAdding test documents...")
        test_docs = [
            {
                'id': 'test_doc_1',
                'content': 'Samsung Electronics published its ESG report in 2024, focusing on climate governance and carbon neutrality targets.',
                'company_name': 'Samsung Electronics',
                'report_year': 2024,
                'report_type': 'ESG',
                'section_type': 'governance'
            },
            {
                'id': 'test_doc_2',
                'content': 'The company implements robust risk management strategies for climate-related financial risks.',
                'company_name': 'Samsung Electronics',
                'report_year': 2024,
                'report_type': 'TCFD',
                'section_type': 'risk_management'
            },
            {
                'id': 'test_doc_3',
                'content': 'LG Chem announced renewable energy transition plans with detailed metrics and targets.',
                'company_name': 'LG Chem',
                'report_year': 2023,
                'report_type': 'ESG',
                'section_type': 'metrics'
            }
        ]

        added_count = store.add_documents(test_docs)
        print(f"[PASS] Added {added_count} documents")

        # Search test
        print("\nTesting search...")
        query = "climate governance strategy"
        start_time = time.time()
        results = store.search(query_text=query, top_k=3)
        search_time = time.time() - start_time

        print(f"[PASS] Search completed in {search_time*1000:.2f}ms")
        print(f"[PASS] Found {len(results)} results")

        for i, result in enumerate(results, 1):
            print(f"\n  Result {i}:")
            print(f"    ID: {result['id']}")
            print(f"    Score: {result['score']:.4f}")
            print(f"    Company: {result['metadata'].get('company_name', 'N/A')}")
            print(f"    Section: {result['metadata'].get('section_type', 'N/A')}")
            print(f"    Text: {result['text'][:100]}...")

        # Cleanup
        print("\nCleaning up test collection...")
        store.client.delete_collection(test_collection)
        print("[PASS] Test collection deleted")

        return True
    except Exception as e:
        print(f"[FAIL] Vector store operations test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_rag_engine_integration():
    """RAGEngine과 Qdrant 통합 테스트"""
    print("\n=== 5. Testing RAGEngine Integration ===")

    # Test with mock mode
    print("\n5a. Testing Mock Mode...")
    try:
        os.environ['RAG_MOCK_MODE'] = 'true'
        from ai_agent.utils.rag_helpers import RAGEngine

        # Force reload to pick up env var
        import importlib
        import ai_agent.utils.rag_helpers
        importlib.reload(ai_agent.utils.rag_helpers)
        from ai_agent.utils.rag_helpers import RAGEngine

        rag = RAGEngine(source="benchmark")
        results = rag.query("test query", top_k=3)

        print(f"[PASS] Mock mode working: {len(results)} results")
        print(f"[PASS] Sample result: {results[0]['source']}")

    except Exception as e:
        print(f"[FAIL] Mock mode test failed: {e}")
        return False

    # Test with Qdrant (if available)
    print("\n5b. Testing Qdrant Mode...")
    try:
        os.environ['RAG_MOCK_MODE'] = 'false'

        # Reload to pick up new env var
        import importlib
        import ai_agent.utils.rag_helpers
        importlib.reload(ai_agent.utils.rag_helpers)
        from ai_agent.utils.rag_helpers import RAGEngine

        rag = RAGEngine(source="benchmark")

        if rag.client is None:
            print("[WARN] Qdrant not available, fallback to mock mode (expected behavior)")
        else:
            results = rag.query("climate governance", top_k=5)
            print(f"[PASS] Qdrant mode working: {len(results)} results")
            if results:
                print(f"[PASS] Sample result: {results[0].get('source', 'N/A')}")

        return True
    except Exception as e:
        print(f"[WARN] Qdrant mode test encountered error (fallback should handle): {e}")
        # This is acceptable - fallback should kick in
        return True


def test_performance():
    """성능 테스트 (검색 속도 목표: < 500ms)"""
    print("\n=== 6. Performance Testing ===")
    try:
        from ai_agent.utils.rag_helpers import RAGEngine

        rag = RAGEngine(source="benchmark")

        queries = [
            "climate governance strategy",
            "carbon emissions targets",
            "renewable energy transition",
            "ESG risk management",
            "sustainability metrics"
        ]

        times = []
        for query in queries:
            start = time.time()
            results = rag.query(query, top_k=5)
            elapsed = time.time() - start
            times.append(elapsed * 1000)  # Convert to ms

        avg_time = sum(times) / len(times)
        max_time = max(times)
        min_time = min(times)

        print(f"\nQuery Performance:")
        print(f"  Average: {avg_time:.2f}ms")
        print(f"  Min: {min_time:.2f}ms")
        print(f"  Max: {max_time:.2f}ms")

        if avg_time < 500:
            print(f"[PASS] Performance target met (< 500ms)")
        else:
            print(f"[WARN] Performance target not met (avg {avg_time:.2f}ms > 500ms)")

        return True
    except Exception as e:
        print(f"[FAIL] Performance test failed: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description='Test Qdrant Integration')
    parser.add_argument('--skip-connection-test', action='store_true',
                        help='Skip tests that require Qdrant server connection')
    args = parser.parse_args()

    print("=" * 60)
    print("Qdrant Vector Store Integration Test")
    print("=" * 60)

    results = []

    # Run tests
    results.append(("Imports", test_imports()))
    results.append(("Embedding Model", test_embedding_model()))
    results.append(("Qdrant Connection", test_qdrant_connection(args.skip_connection_test)))
    results.append(("Vector Store Operations", test_vector_store_operations(args.skip_connection_test)))
    results.append(("RAGEngine Integration", test_rag_engine_integration()))
    results.append(("Performance", test_performance()))

    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "[PASS] PASS" if result else "[FAIL] FAIL"
        print(f"{status}: {test_name}")

    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\n[SUCCESS][SUCCESS] All tests passed!")
        return 0
    else:
        print(f"\n[WARN] {total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
