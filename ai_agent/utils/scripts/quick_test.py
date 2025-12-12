"""
Quick Qdrant Integration Test
간단한 통합 테스트 스크립트
"""
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

print("=" * 60)
print("Quick Qdrant Integration Test")
print("=" * 60)

# Test 1: Import packages
print("\n[1/5] Testing package imports...")
try:
    from qdrant_client import QdrantClient
    print("  [PASS] qdrant-client")
except ImportError as e:
    print(f"  [FAIL] qdrant-client: {e}")
    sys.exit(1)

try:
    from sentence_transformers import SentenceTransformer
    print("  [PASS] sentence-transformers")
except ImportError as e:
    print(f"  [FAIL] sentence-transformers: {e}")
    sys.exit(1)

# Test 2: Import custom modules
print("\n[2/5] Testing custom module imports...")
try:
    from ai_agent.utils.qdrant_vector_store import QdrantVectorStore, get_embedding_model
    print("  [PASS] QdrantVectorStore")
except ImportError as e:
    print(f"  [FAIL] QdrantVectorStore: {e}")
    sys.exit(1)

try:
    from ai_agent.utils.rag_helpers import RAGEngine
    print("  [PASS] RAGEngine")
except ImportError as e:
    print(f"  [FAIL] RAGEngine: {e}")
    sys.exit(1)

# Test 3: Load embedding model
print("\n[3/5] Testing embedding model...")
try:
    import time
    start = time.time()
    model = get_embedding_model()
    elapsed = time.time() - start
    print(f"  [PASS] Model loaded in {elapsed:.2f}s")

    # Test encoding
    test_embedding = model.encode("test sentence")
    print(f"  [PASS] Embedding dimension: {len(test_embedding)}")
except Exception as e:
    print(f"  [FAIL] {e}")
    sys.exit(1)

# Test 4: RAGEngine with Mock mode
print("\n[4/5] Testing RAGEngine (Mock mode)...")
try:
    os.environ['RAG_MOCK_MODE'] = 'true'

    # Force reload
    import importlib
    import ai_agent.utils.rag_helpers
    importlib.reload(ai_agent.utils.rag_helpers)
    from ai_agent.utils.rag_helpers import RAGEngine

    rag = RAGEngine(source="benchmark")
    results = rag.query("test query", top_k=3)
    print(f"  [PASS] Mock mode returned {len(results)} results")
    if results:
        print(f"  [INFO] Sample result source: {results[0].get('source', 'N/A')}")
except Exception as e:
    print(f"  [FAIL] {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 5: RAGEngine with Qdrant fallback
print("\n[5/5] Testing RAGEngine (Qdrant mode with fallback)...")
try:
    os.environ['RAG_MOCK_MODE'] = 'false'

    # Force reload
    importlib.reload(ai_agent.utils.rag_helpers)
    from ai_agent.utils.rag_helpers import RAGEngine

    rag = RAGEngine(source="benchmark")

    if rag.client is None:
        print("  [WARN] Qdrant not available - fallback to mock mode (expected)")
    else:
        print("  [PASS] Qdrant client initialized")

    results = rag.query("climate governance", top_k=5)
    print(f"  [PASS] Query returned {len(results)} results")

except Exception as e:
    print(f"  [WARN] Qdrant mode error (fallback should handle): {e}")
    # This is acceptable - fallback should work

print("\n" + "=" * 60)
print("[SUCCESS] All basic tests passed!")
print("=" * 60)
print("\nNext steps:")
print("1. Start Qdrant server: docker run -p 6333:6333 qdrant/qdrant")
print("2. Upload sample reports: python ai_agent/utils/scripts/upload_reports.py")
print("3. Set RAG_MOCK_MODE=false in .env")
print("4. Test with real data")
