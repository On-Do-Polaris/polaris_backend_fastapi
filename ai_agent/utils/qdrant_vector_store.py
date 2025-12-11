"""
파일명: qdrant_vector_store.py
최종 수정일: 2025-12-11
버전: v01

개요:
    Qdrant Vector Store 클라이언트 래퍼 클래스
    기존 ESG/TCFD 보고서를 벡터 DB에 저장하고 유사도 검색 제공

주요 기능:
    1. Qdrant 클라이언트 초기화 및 컬렉션 관리
    2. sentence-transformers 기반 임베딩 생성
    3. 유사도 검색 (cosine similarity)
    4. 배치 업로드 및 메타데이터 필터링
    5. Singleton 패턴으로 임베딩 모델 재사용

컬렉션 스키마:
    - Collection Name: esg_tcfd_reports
    - Vector Size: 384 (all-MiniLM-L6-v2)
    - Distance: Cosine
    - Payload: document_id, company_name, report_year, report_type,
               section_type, content, content_summary, metadata, tags
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


# Singleton 임베딩 모델 (메모리 최적화)
_embedding_model = None


def get_embedding_model(model_name: str = 'sentence-transformers/all-MiniLM-L6-v2'):
    """
    임베딩 모델 Singleton 인스턴스 반환

    Args:
        model_name: Hugging Face 모델 이름

    Returns:
        SentenceTransformer 인스턴스
    """
    global _embedding_model

    if _embedding_model is None:
        try:
            from sentence_transformers import SentenceTransformer
            logger.info(f"Loading embedding model: {model_name}")
            _embedding_model = SentenceTransformer(model_name)
            logger.info("Embedding model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load embedding model: {e}")
            raise

    return _embedding_model


class QdrantVectorStore:
    """
    Qdrant Vector Store 클라이언트 래퍼

    Features:
        - 컬렉션 자동 생성 및 인덱스 설정
        - 벡터 임베딩 자동 생성
        - 유사도 검색 (필터 지원)
        - 배치 업로드
    """

    def __init__(
        self,
        url: str = "http://localhost:6333",
        api_key: Optional[str] = None,
        collection_name: str = "esg_tcfd_reports",
        embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    ):
        """
        Qdrant 클라이언트 및 임베딩 모델 초기화

        Args:
            url: Qdrant 서버 URL
            api_key: Qdrant API 키 (Cloud 사용 시)
            collection_name: 컬렉션 이름
            embedding_model: 임베딩 모델 이름
        """
        try:
            from qdrant_client import QdrantClient
            from qdrant_client.models import Distance, VectorParams

            self.url = url
            self.api_key = api_key
            self.collection_name = collection_name
            self.embedding_model_name = embedding_model

            # Qdrant 클라이언트 초기화
            if api_key:
                self.client = QdrantClient(url=url, api_key=api_key)
            else:
                self.client = QdrantClient(url=url)

            logger.info(f"Qdrant client initialized: {url}")

            # 임베딩 모델 로드
            self.embedding_model = get_embedding_model(embedding_model)
            self.vector_size = self.embedding_model.get_sentence_embedding_dimension()

            logger.info(f"Vector size: {self.vector_size}")

            # 컬렉션 확인 및 생성
            self._ensure_collection()

        except ImportError as e:
            logger.error("qdrant-client not installed. Run: pip install qdrant-client")
            raise
        except Exception as e:
            logger.error(f"Failed to initialize Qdrant client: {e}")
            raise

    def _ensure_collection(self):
        """
        컬렉션 존재 확인 및 생성
        """
        try:
            from qdrant_client.models import Distance, VectorParams

            # 컬렉션 존재 확인
            collections = self.client.get_collections().collections
            collection_names = [c.name for c in collections]

            if self.collection_name not in collection_names:
                logger.info(f"Creating collection: {self.collection_name}")

                # 컬렉션 생성
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=self.vector_size,
                        distance=Distance.COSINE
                    )
                )

                # 인덱스 생성 (Payload 필드)
                self.client.create_payload_index(
                    collection_name=self.collection_name,
                    field_name="company_name",
                    field_schema="keyword"
                )

                self.client.create_payload_index(
                    collection_name=self.collection_name,
                    field_name="report_year",
                    field_schema="integer"
                )

                self.client.create_payload_index(
                    collection_name=self.collection_name,
                    field_name="section_type",
                    field_schema="keyword"
                )

                logger.info(f"Collection created with indexes: {self.collection_name}")
            else:
                logger.info(f"Collection already exists: {self.collection_name}")

        except Exception as e:
            logger.error(f"Failed to ensure collection: {e}")
            raise

    def search(
        self,
        query_text: str,
        top_k: int = 5,
        filters: Optional[Dict[str, Any]] = None,
        score_threshold: float = 0.0
    ) -> List[Dict[str, Any]]:
        """
        유사도 검색

        Args:
            query_text: 검색 쿼리 텍스트
            top_k: 반환할 문서 개수
            filters: Payload 필터 (예: {"company_name": "Samsung"})
            score_threshold: 최소 유사도 점수 (0.0 ~ 1.0)

        Returns:
            검색 결과 리스트 [{'id': ..., 'text': ..., 'source': ..., 'score': ...}, ...]
        """
        try:
            from qdrant_client.models import Filter, FieldCondition, MatchValue

            # 쿼리 텍스트 임베딩
            query_vector = self.embedding_model.encode(query_text).tolist()

            # 필터 생성
            search_filter = None
            if filters:
                conditions = []
                for key, value in filters.items():
                    conditions.append(
                        FieldCondition(key=key, match=MatchValue(value=value))
                    )
                search_filter = Filter(must=conditions)

            # 검색 실행
            search_results = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_vector,
                limit=top_k,
                query_filter=search_filter,
                score_threshold=score_threshold
            )

            # 결과 포맷팅
            results = []
            for hit in search_results:
                payload = hit.payload
                results.append({
                    'id': payload.get('document_id', hit.id),
                    'text': payload.get('content', ''),
                    'source': f"{payload.get('company_name', 'Unknown')} - {payload.get('report_year', 'N/A')} ({payload.get('section_type', 'N/A')})",
                    'score': hit.score,
                    'metadata': {
                        'company_name': payload.get('company_name'),
                        'report_year': payload.get('report_year'),
                        'report_type': payload.get('report_type'),
                        'section_type': payload.get('section_type')
                    }
                })

            logger.info(f"Search completed: {len(results)} results found")
            return results

        except Exception as e:
            logger.error(f"Search failed: {e}")
            raise

    def add_documents(
        self,
        documents: List[Dict[str, Any]],
        batch_size: int = 100
    ) -> int:
        """
        배치 문서 업로드

        Args:
            documents: 문서 리스트
                [
                    {
                        'id': 'uuid-or-string',
                        'content': 'text content',
                        'company_name': 'Company',
                        'report_year': 2024,
                        'report_type': 'ESG',
                        'section_type': 'governance',
                        'content_summary': 'summary...',
                        'metadata': {...},
                        'tags': [...]
                    },
                    ...
                ]
            batch_size: 배치 크기

        Returns:
            업로드된 문서 개수
        """
        try:
            from qdrant_client.models import PointStruct

            if not documents:
                logger.warning("No documents to upload")
                return 0

            total_uploaded = 0

            # 배치 단위로 업로드
            for i in range(0, len(documents), batch_size):
                batch = documents[i:i + batch_size]
                points = []

                for doc in batch:
                    # 필수 필드 확인
                    if 'content' not in doc:
                        logger.warning(f"Skipping document without content: {doc.get('id')}")
                        continue

                    # 임베딩 생성
                    vector = self.embedding_model.encode(doc['content']).tolist()

                    # Payload 구성
                    payload = {
                        'document_id': doc.get('id', f"doc_{i}"),
                        'company_name': doc.get('company_name', 'Unknown'),
                        'report_year': doc.get('report_year', 2024),
                        'report_type': doc.get('report_type', 'ESG'),
                        'section_type': doc.get('section_type', 'general'),
                        'content': doc.get('content', ''),
                        'content_summary': doc.get('content_summary', ''),
                        'metadata': doc.get('metadata', {}),
                        'tags': doc.get('tags', []),
                        'indexed_at': datetime.now().isoformat()
                    }

                    # Point 생성
                    point = PointStruct(
                        id=doc.get('id', f"doc_{total_uploaded + len(points)}"),
                        vector=vector,
                        payload=payload
                    )
                    points.append(point)

                # 배치 업로드
                if points:
                    self.client.upsert(
                        collection_name=self.collection_name,
                        points=points
                    )
                    total_uploaded += len(points)
                    logger.info(f"Uploaded batch: {len(points)} documents (total: {total_uploaded})")

            logger.info(f"Upload completed: {total_uploaded} documents")
            return total_uploaded

        except Exception as e:
            logger.error(f"Upload failed: {e}")
            raise

    def get_collection_info(self) -> Dict[str, Any]:
        """
        컬렉션 정보 조회

        Returns:
            컬렉션 정보 딕셔너리
        """
        try:
            collection_info = self.client.get_collection(self.collection_name)

            return {
                'collection_name': self.collection_name,
                'points_count': collection_info.points_count,
                'vector_size': collection_info.config.params.vectors.size,
                'distance': collection_info.config.params.vectors.distance.name,
                'status': collection_info.status.name
            }

        except Exception as e:
            logger.error(f"Failed to get collection info: {e}")
            raise

    def delete_documents(self, document_ids: List[str]) -> bool:
        """
        문서 삭제

        Args:
            document_ids: 삭제할 문서 ID 리스트

        Returns:
            성공 여부
        """
        try:
            self.client.delete(
                collection_name=self.collection_name,
                points_selector=document_ids
            )
            logger.info(f"Deleted {len(document_ids)} documents")
            return True

        except Exception as e:
            logger.error(f"Delete failed: {e}")
            return False
