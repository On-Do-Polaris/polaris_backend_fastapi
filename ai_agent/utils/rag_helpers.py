# report_generation/utils/rag_helpers.py
"""
RAG Helper
- LangGraph 에이전트용 RAG(Query & Citation) 유틸리티
- Qdrant / Tavily / 기타 vector DB 지원
"""

from typing import List, Dict, Any
import logging
import os

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
        # TODO: 실제 API key/config 로딩
        if source == "qdrant":
            client = None  # 실제 qdrant client 초기화
        elif source == "tavily":
            client = None  # 실제 tavily client 초기화
        else:
            client = None
        return client

    def query(self, query_text: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        RAG 검색 수행
        Returns:
            [{'text': ..., 'source': ..., 'id': ...}, ...]
        """
        try:
            logger.info(f"[RAGEngine] Querying '{self.source}' for: {query_text}")
            # TODO: 실제 검색 API 호출
            results = [{
                "id": f"doc_{i+1}",
                "text": f"Sample reference text {i+1}",
                "source": f"dummy_source_{i+1}"
            } for i in range(top_k)]
            return results
        except Exception as e:
            logger.error(f"[RAGEngine] Query failed: {e}")
            return []

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
