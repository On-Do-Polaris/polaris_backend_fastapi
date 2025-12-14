"""
파일명: rag_ingestion_service.py
최종 수정일: 2025-12-12
버전: v01
파일 개요: LlamaParse 파싱 결과를 Qdrant에 저장하는 RAG Ingestion 서비스

주요 기능:
- DocumentParser를 사용하여 PDF 파싱
- 파싱된 문서를 적절한 크기로 청킹
- 두 개의 Qdrant 컬렉션에 저장:
  1. tcfd_documents: 일반 문서 청크
  2. tcfd_tables: 테이블 데이터
- 메타데이터 관리 및 추적

주의사항:
- 실제 실행은 scripts/ingest_rag_documents.py에서만 수행
- 로컬 환경에서 Qdrant 연결 불가 시 코드 구조만 확인
"""

import os
import json
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
from datetime import datetime
import re

from ai_agent.services.document_parser import DocumentParser
from ai_agent.utils.qdrant_vector_store import QdrantVectorStore

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class RAGIngestionService:
    """
    RAG 문서 수집 및 Qdrant 저장 서비스

    워크플로우:
    1. DocumentParser로 PDF 파싱 (캐시 우선)
    2. 텍스트 청킹 (512 토큰 단위)
    3. 테이블 추출 및 분리 저장
    4. Qdrant에 업로드 (2개 컬렉션)
    """

    def __init__(
        self,
        qdrant_url: str = "http://localhost:6333",
        qdrant_api_key: Optional[str] = None,
        chunk_size: int = 512,
        chunk_overlap: int = 50
    ):
        """
        Args:
            qdrant_url: Qdrant 서버 URL
            qdrant_api_key: Qdrant API 키
            chunk_size: 청킹 크기 (토큰 단위)
            chunk_overlap: 청크 간 오버랩 크기
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

        # DocumentParser 초기화
        self.parser = DocumentParser()

        # Qdrant Vector Stores 초기화 (2개 컬렉션)
        try:
            # 1. 일반 문서 컬렉션
            self.doc_store = QdrantVectorStore(
                url=qdrant_url,
                api_key=qdrant_api_key,
                collection_name="tcfd_documents"
            )

            # 2. 테이블 전용 컬렉션
            self.table_store = QdrantVectorStore(
                url=qdrant_url,
                api_key=qdrant_api_key,
                collection_name="tcfd_tables"
            )

            logger.info("Qdrant stores initialized successfully")

        except Exception as e:
            logger.warning(f"Failed to initialize Qdrant: {e}")
            logger.warning("Running in offline mode (structure validation only)")
            self.doc_store = None
            self.table_store = None

    def ingest_pdf(
        self,
        file_path: str,
        document_metadata: Dict[str, Any],
        force_reparse: bool = False
    ) -> Dict[str, Any]:
        """
        PDF 파싱 및 Qdrant 저장

        Args:
            file_path: PDF 파일 경로
            document_metadata: 문서 메타데이터
                {
                    'document_id': 'tcfd_official_2017',
                    'document_type': 'guideline',  # guideline, benchmark, analysis
                    'source': 'TCFD',
                    'year': 2017,
                    'title': 'Final Report: Recommendations of the TCFD',
                    'tags': ['tcfd', 'governance', 'strategy']
                }
            force_reparse: 캐시 무시하고 재파싱 여부

        Returns:
            수집 결과 딕셔너리
        """
        logger.info(f"Starting ingestion for: {file_path}")

        # 1. PDF 파싱
        parsed_docs = self.parser.parse_pdf(file_path, force_reparse)
        logger.info(f"Parsed {len(parsed_docs)} document chunks")

        # 2. 전체 텍스트 결합
        full_text = "\n\n".join([doc['text'] for doc in parsed_docs])

        # 3. 텍스트 청킹
        text_chunks = self._chunk_text(full_text)
        logger.info(f"Created {len(text_chunks)} text chunks")

        # 4. 테이블 추출
        tables = self.parser.extract_tables_from_markdown(full_text)
        logger.info(f"Extracted {len(tables)} tables")

        # 5. Qdrant에 저장
        result = {
            'document_id': document_metadata.get('document_id'),
            'file_path': file_path,
            'parsed_chunks': len(parsed_docs),
            'text_chunks_created': len(text_chunks),
            'tables_extracted': len(tables),
            'uploaded_to_qdrant': False
        }

        if self.doc_store and self.table_store:
            # 일반 문서 청크 업로드
            doc_count = self._upload_text_chunks(
                text_chunks,
                document_metadata
            )

            # 테이블 업로드
            table_count = self._upload_tables(
                tables,
                document_metadata
            )

            result['uploaded_to_qdrant'] = True
            result['documents_uploaded'] = doc_count
            result['tables_uploaded'] = table_count

            logger.info(f"✅ Ingestion completed: {doc_count} docs, {table_count} tables")
        else:
            logger.warning("⚠️  Qdrant not available - skipping upload (structure validated)")

        return result

    def _chunk_text(
        self,
        text: str,
        max_chunk_size: int = None
    ) -> List[Dict[str, Any]]:
        """
        텍스트를 의미 단위로 청킹

        전략:
        1. 섹션/헤더 단위로 1차 분할
        2. 크기 초과 시 문장 단위로 2차 분할
        3. 오버랩 적용하여 문맥 보존

        Args:
            text: 원본 텍스트
            max_chunk_size: 최대 청크 크기 (문자 단위, 기본값: self.chunk_size * 4)

        Returns:
            청크 리스트 [{'text': ..., 'chunk_index': ...}, ...]
        """
        if max_chunk_size is None:
            # 대략 1 토큰 = 4 글자로 추정
            max_chunk_size = self.chunk_size * 4

        chunks = []

        # Markdown 헤더로 1차 분할 (섹션 단위)
        sections = re.split(r'\n(#{1,3}\s+.+)\n', text)

        current_chunk = ""
        chunk_index = 0

        for section in sections:
            # 빈 섹션 스킵
            if not section.strip():
                continue

            # 현재 청크에 추가 시 크기 확인
            if len(current_chunk) + len(section) < max_chunk_size:
                current_chunk += section + "\n"
            else:
                # 현재 청크 저장
                if current_chunk.strip():
                    chunks.append({
                        'text': current_chunk.strip(),
                        'chunk_index': chunk_index,
                        'char_count': len(current_chunk)
                    })
                    chunk_index += 1

                # 새 청크 시작 (오버랩 적용)
                overlap_text = self._get_overlap_text(current_chunk)
                current_chunk = overlap_text + section + "\n"

        # 마지막 청크 저장
        if current_chunk.strip():
            chunks.append({
                'text': current_chunk.strip(),
                'chunk_index': chunk_index,
                'char_count': len(current_chunk)
            })

        return chunks

    def _get_overlap_text(self, text: str) -> str:
        """
        청크 오버랩용 텍스트 추출 (마지막 N 문자)

        Args:
            text: 원본 텍스트

        Returns:
            오버랩 텍스트
        """
        overlap_size = self.chunk_overlap * 4  # 토큰 → 문자 변환

        if len(text) < overlap_size:
            return text

        # 마지막 N 문자에서 문장 경계 찾기
        overlap_text = text[-overlap_size:]

        # 문장 시작 위치 찾기 (마침표 뒤)
        sentence_start = overlap_text.find('. ')
        if sentence_start != -1:
            return overlap_text[sentence_start + 2:]

        return overlap_text

    def _upload_text_chunks(
        self,
        chunks: List[Dict[str, Any]],
        metadata: Dict[str, Any]
    ) -> int:
        """
        텍스트 청크를 tcfd_documents 컬렉션에 업로드

        Args:
            chunks: 청크 리스트
            metadata: 문서 메타데이터

        Returns:
            업로드된 청크 개수
        """
        documents = []

        for chunk in chunks:
            doc = {
                'id': f"{metadata['document_id']}_chunk_{chunk['chunk_index']}",
                'content': chunk['text'],
                'company_name': metadata.get('source', 'Unknown'),
                'report_year': metadata.get('year', 2024),
                'report_type': metadata.get('document_type', 'guideline'),
                'section_type': 'general',  # 섹션 자동 감지 시 업데이트
                'content_summary': chunk['text'][:200] + '...' if len(chunk['text']) > 200 else chunk['text'],
                'metadata': {
                    'document_id': metadata['document_id'],
                    'title': metadata.get('title', 'Unknown'),
                    'chunk_index': chunk['chunk_index'],
                    'char_count': chunk['char_count'],
                    'tags': metadata.get('tags', [])
                },
                'tags': metadata.get('tags', [])
            }
            documents.append(doc)

        # Qdrant 업로드
        uploaded_count = self.doc_store.add_documents(documents)
        logger.info(f"Uploaded {uploaded_count} text chunks to tcfd_documents")

        return uploaded_count

    def _upload_tables(
        self,
        tables: List[Dict[str, Any]],
        metadata: Dict[str, Any]
    ) -> int:
        """
        테이블을 tcfd_tables 컬렉션에 업로드

        Args:
            tables: 테이블 리스트
            metadata: 문서 메타데이터

        Returns:
            업로드된 테이블 개수
        """
        documents = []

        for idx, table in enumerate(tables):
            # 테이블 내용을 자연어로 변환 (검색 최적화)
            table_text = self._table_to_text(table['data'])

            doc = {
                'id': f"{metadata['document_id']}_table_{idx}",
                'content': table_text,
                'company_name': metadata.get('source', 'Unknown'),
                'report_year': metadata.get('year', 2024),
                'report_type': metadata.get('document_type', 'guideline'),
                'section_type': 'table',
                'content_summary': f"Table with {len(table['data']['headers'])} columns and {len(table['data']['rows'])} rows",
                'metadata': {
                    'document_id': metadata['document_id'],
                    'title': metadata.get('title', 'Unknown'),
                    'table_index': idx,
                    'markdown': table['markdown'],
                    'headers': table['data']['headers'],
                    'row_count': len(table['data']['rows']),
                    'column_count': len(table['data']['headers']),
                    'tags': metadata.get('tags', [])
                },
                'tags': metadata.get('tags', []) + ['table']
            }
            documents.append(doc)

        if documents:
            uploaded_count = self.table_store.add_documents(documents)
            logger.info(f"Uploaded {uploaded_count} tables to tcfd_tables")
            return uploaded_count

        return 0

    def _table_to_text(self, table_data: Dict[str, Any]) -> str:
        """
        테이블 데이터를 자연어 텍스트로 변환 (임베딩 최적화)

        Args:
            table_data: {'headers': [...], 'rows': [[...], ...]}

        Returns:
            자연어 텍스트
        """
        headers = table_data['headers']
        rows = table_data['rows']

        # 헤더 설명
        text_parts = [
            f"This table contains {len(rows)} rows with the following columns: {', '.join(headers)}."
        ]

        # 각 행을 문장으로 변환
        for row in rows[:5]:  # 최대 5개 행만 포함 (너무 길어지지 않도록)
            row_text = " | ".join([f"{headers[i]}: {cell}" for i, cell in enumerate(row) if i < len(headers)])
            text_parts.append(row_text)

        if len(rows) > 5:
            text_parts.append(f"... and {len(rows) - 5} more rows.")

        return "\n".join(text_parts)

    def get_ingestion_stats(self) -> Dict[str, Any]:
        """
        RAG 수집 통계 반환

        Returns:
            통계 딕셔너리
        """
        stats = {
            'parser_stats': self.parser.get_parsing_stats(),
            'qdrant_available': self.doc_store is not None and self.table_store is not None
        }

        if self.doc_store and self.table_store:
            try:
                stats['tcfd_documents'] = self.doc_store.get_collection_info()
                stats['tcfd_tables'] = self.table_store.get_collection_info()
            except Exception as e:
                logger.warning(f"Failed to get Qdrant stats: {e}")
                stats['qdrant_error'] = str(e)

        return stats

    def ingest_multiple_pdfs(
        self,
        pdf_configs: List[Dict[str, Any]],
        force_reparse: bool = False
    ) -> List[Dict[str, Any]]:
        """
        여러 PDF를 배치로 수집

        Args:
            pdf_configs: PDF 설정 리스트
                [
                    {
                        'file_path': 'path/to/file.pdf',
                        'metadata': {...}
                    },
                    ...
                ]
            force_reparse: 캐시 무시 여부

        Returns:
            수집 결과 리스트
        """
        results = []

        for config in pdf_configs:
            try:
                result = self.ingest_pdf(
                    file_path=config['file_path'],
                    document_metadata=config['metadata'],
                    force_reparse=force_reparse
                )
                results.append(result)
            except Exception as e:
                logger.error(f"Failed to ingest {config['file_path']}: {e}")
                results.append({
                    'file_path': config['file_path'],
                    'error': str(e),
                    'status': 'failed'
                })

        return results


# 사용 예시
if __name__ == "__main__":
    # RAG Ingestion Service 초기화
    service = RAGIngestionService()

    # 통계 확인
    stats = service.get_ingestion_stats()
    print("\n📊 RAG Ingestion Statistics:")
    print(json.dumps(stats, indent=2, ensure_ascii=False))

    # 실제 수집 예시 (주의: 실행하지 말 것!)
    # result = service.ingest_pdf(
    #     file_path="각종 자료/For_RAG/FINAL-2017-TCFD-Report.pdf",
    #     document_metadata={
    #         'document_id': 'tcfd_official_2017',
    #         'document_type': 'guideline',
    #         'source': 'TCFD',
    #         'year': 2017,
    #         'title': 'Final Report: Recommendations of the TCFD',
    #         'tags': ['tcfd', 'governance', 'strategy', 'risk_management', 'metrics']
    #     }
    # )
