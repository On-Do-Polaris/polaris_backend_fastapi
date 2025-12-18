# report_generation/utils/rag_helpers.py
"""
RAG Helper
- LangGraph 에이전트용 RAG(Query & Citation) 유틸리티
- Qdrant / Tavily / 기타 vector DB 지원
- 기존 컬렉션 검색 지원 (1024 차원, named vector)

수정 이력:
- 2025-12-16: 기존 컬렉션 검색 지원 추가 (ExistingCollectionSearcher)
"""

import os
import logging
from typing import List, Dict, Any, Optional

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
    """
    RAG 검색 엔진

    지원하는 source 타입:
    - "qdrant": 기본 QdrantVectorStore (384 차원, 새 컬렉션용)
    - "benchmark": qdrant와 동일
    - "existing": 기존 컬렉션 검색 (1024 차원, SK 보고서 등)
    - "tcfd_report": SK TCFD 보고서 전용 검색
    - "risk_rag": 물리적 리스크 RAG 컬렉션 검색
    """

    def __init__(self, source: str = "existing", collection_names: Optional[List[str]] = None):
        """
        Args:
            source: "qdrant", "existing", "tcfd_report", "risk_rag" 등 선택
            collection_names: 검색할 컬렉션 이름 리스트 (existing 모드에서만 사용)
        """
        self.source = source
        self.collection_names = collection_names
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

        qdrant_url = os.getenv('QDRANT_URL', 'http://localhost:6333')
        # Docker 컨테이너로 띄운 Qdrant는 API 키가 필요 없음
        # qdrant_api_key = os.getenv('QDRANT_API_KEY')  # 제거

        try:
            # 기존 컬렉션 검색 모드 (1024 차원, named vector)
            if source in ["existing", "tcfd_report", "risk_rag", "benchmark"]:
                from .qdrant_vector_store import ExistingCollectionSearcher

                logger.info(f"[RAGEngine] Initializing ExistingCollectionSearcher: {qdrant_url}")
                # api_key 파라미터 제거 (Docker 컨테이너는 API 키 불필요)
                client = ExistingCollectionSearcher(url=qdrant_url)
                logger.info("[RAGEngine] ExistingCollectionSearcher initialized successfully")
                return client

            elif source == "qdrant":
                # 기본 QdrantVectorStore (384 차원, 새 컬렉션용)
                from .qdrant_vector_store import QdrantVectorStore

                collection_name = os.getenv('QDRANT_COLLECTION', 'esg_tcfd_reports')

                logger.info(f"[RAGEngine] Initializing QdrantVectorStore: {qdrant_url}")
                # api_key 파라미터 제거 (Docker 컨테이너는 API 키 불필요)
                client = QdrantVectorStore(
                    url=qdrant_url,
                    collection_name=collection_name
                )
                logger.info("[RAGEngine] QdrantVectorStore initialized successfully")
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
            logger.info(f"[RAGEngine] Querying '{self.source}' for: {query_text[:50]}...")

            # source 타입에 따라 검색 방식 결정
            if self.source == "tcfd_report":
                # SK TCFD 보고서 전용 검색
                results = self.client.search_tcfd_report(
                    query_text=query_text,
                    top_k=top_k
                )
            elif self.source == "risk_rag":
                # 물리적 리스크 RAG 컬렉션 검색
                results = self.client.search_risk_rag(
                    query_text=query_text,
                    top_k=top_k
                )
            elif self.source in ["existing", "benchmark"]:
                # 기존 컬렉션 검색 (collection_names 지정 가능)
                results = self.client.search(
                    query_text=query_text,
                    collection_names=self.collection_names,
                    top_k=top_k
                )
            else:
                # 기본 QdrantVectorStore 검색
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
