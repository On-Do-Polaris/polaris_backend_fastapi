# report_generation/utils/rag_helpers.py
"""
RAG Helper
- LangGraph 에이전트용 RAG(Query & Citation) 유틸리티
- Qdrant / Tavily / 기타 vector DB 지원
"""

import os
import logging
from typing import List, Dict, Any

logger = logging.getLogger("RAGHelper")
if not logger.handlers:
    ch = logging.StreamHandler()
    ch.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
    logger.addHandler(ch)
logger.setLevel(logging.INFO)


# ============================================================
# RAG Engine
# ============================================================
class RAGEngine:
    def __init__(self, source: str = "qdrant"):
        """
        Args:
            source: "qdrant", "tavily" 등 선택
        """
        self.source = source
        self.client = self._init_client(source)
        logger.info(f"[RAGEngine] Initialized with source={source}")

    def _init_client(self, source: str):
        """
        백엔드 클라이언트 초기화
        """
        # Mock 모드 체크
        if os.getenv('RAG_MOCK_MODE', 'false').lower() == 'true':
            logger.info("[RAGEngine] Running in Mock mode (RAG_MOCK_MODE=true)")
            return None

        try:
            if source in ["qdrant", "benchmark"]:
                # QdrantVectorStore 초기화
                from .qdrant_vector_store import QdrantVectorStore

                qdrant_url = os.getenv('QDRANT_URL', 'http://localhost:6333')
                qdrant_api_key = os.getenv('QDRANT_API_KEY')
                collection_name = os.getenv('QDRANT_COLLECTION', 'esg_tcfd_reports')

                logger.info(f"[RAGEngine] Initializing Qdrant client: {qdrant_url}")
                client = QdrantVectorStore(
                    url=qdrant_url,
                    api_key=qdrant_api_key,
                    collection_name=collection_name
                )
                logger.info("[RAGEngine] Qdrant client initialized successfully")
                return client

            elif source == "tavily":
                # Tavily는 향후 구현
                logger.warning("[RAGEngine] Tavily not implemented yet")
                return None
            else:
                logger.warning(f"[RAGEngine] Unknown source: {source}")
                return None

        except Exception as e:
            logger.error(f"[RAGEngine] Failed to initialize client: {e}")
            logger.warning("[RAGEngine] Falling back to Mock mode")
            return None

    def query(self, query_text: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        RAG 검색 수행
        Returns:
            [{'text': ..., 'source': ..., 'id': ...}, ...]
        """
        # Mock 모드 또는 클라이언트 없을 때
        if self.client is None:
            logger.info(f"[RAGEngine] Mock mode - returning {top_k} dummy results")
            return self._get_mock_results(top_k)

        try:
            logger.info(f"[RAGEngine] Querying '{self.source}' for: {query_text}")

            # Qdrant 검색 실행
            results = self.client.search(
                query_text=query_text,
                top_k=top_k
            )

            logger.info(f"[RAGEngine] Found {len(results)} results")
            return results

        except Exception as e:
            logger.error(f"[RAGEngine] Query failed: {e}")
            logger.warning("[RAGEngine] Falling back to mock results")
            return self._get_mock_results(top_k)

    def _get_mock_results(self, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Mock 더미 결과 반환 (Qdrant 없을 때 Fallback)

        Returns:
            Mock 문서 리스트
        """
        return [{
            "id": f"doc_{i+1}",
            "text": f"Sample reference text {i+1} - ESG/TCFD benchmark example",
            "source": f"dummy_source_{i+1}",
            "score": 0.85 - (i * 0.05),
            "metadata": {
                "company_name": f"Company {i+1}",
                "report_year": 2024 - i,
                "report_type": "ESG",
                "section_type": "governance"
            }
        } for i in range(top_k)]

    def get_citations(self, doc_list: List[Dict[str, Any]]) -> List[str]:
        """
        검색 결과 → citation 텍스트
        """
        citations = []
        for doc in doc_list:
            source = doc.get("source", "unknown_source")
            doc_id = doc.get("id", "")
            citations.append(f"{doc_id} - {source}")
        return citations


# ============================================================
# 유틸 함수: 간단 RAG 쿼리 + citation 추출
# ============================================================
def rag_query(query_text: str, top_k: int = 5) -> List[Dict[str, Any]]:
    """
    에이전트에서 바로 호출 가능한 RAG 검색
    Returns: [{'text':..., 'source':..., 'id':...}, ...]
    """
    rag = RAGEngine()
    docs = rag.query(query_text, top_k)
    return docs


def format_citations_from_docs(doc_list: List[Dict[str, Any]]) -> List[str]:
    """
    문서 리스트 → citation 텍스트
    """
    rag = RAGEngine()
    return rag.get_citations(doc_list)
