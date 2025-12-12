"""
파일명: upload_reports.py
최종 수정일: 2025-12-11
버전: v01

개요:
    기존 ESG/TCFD 보고서를 Qdrant Vector DB에 업로드하는 배치 스크립트

주요 기능:
    1. PDF 보고서 파싱 (PyMuPDF 사용)
    2. 텍스트 청킹 (섹션별, 최대 2000 tokens)
    3. 메타데이터 자동 추출 (회사명, 연도, 섹션 타입)
    4. 배치 업로드 (Qdrant)

사용법:
    python ai_agent/utils/scripts/upload_reports.py --pdf reports/sample.pdf --company "Samsung" --year 2024
    python ai_agent/utils/scripts/upload_reports.py --dir reports/ --batch
"""

import os
import sys
import argparse
import logging
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime
import re

# 프로젝트 루트 추가
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from ai_agent.utils.qdrant_vector_store import QdrantVectorStore

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)


def parse_pdf(pdf_path: str) -> Dict[str, Any]:
    """
    PDF 파일 파싱

    Args:
        pdf_path: PDF 파일 경로

    Returns:
        파싱 결과 딕셔너리
            {
                'full_text': str,
                'pages': List[str],
                'metadata': {...}
            }
    """
    try:
        import fitz  # PyMuPDF

        logger.info(f"Parsing PDF: {pdf_path}")

        doc = fitz.open(pdf_path)
        pages = []
        full_text = ""

        for page_num, page in enumerate(doc):
            text = page.get_text()
            pages.append(text)
            full_text += f"\n\n--- Page {page_num + 1} ---\n\n{text}"

        doc.close()

        logger.info(f"Parsed {len(pages)} pages")

        return {
            'full_text': full_text,
            'pages': pages,
            'metadata': {
                'page_count': len(pages),
                'file_name': Path(pdf_path).name
            }
        }

    except ImportError:
        logger.error("PyMuPDF (fitz) not installed. Run: pip install PyMuPDF")
        raise
    except Exception as e:
        logger.error(f"Failed to parse PDF: {e}")
        raise


def detect_sections(text: str) -> List[Dict[str, str]]:
    """
    텍스트에서 섹션 자동 탐지

    Args:
        text: 전체 텍스트

    Returns:
        섹션 리스트 [{'section_type': ..., 'content': ...}, ...]
    """
    sections = []

    # ESG/TCFD 보고서 주요 섹션 키워드
    section_patterns = {
        'governance': r'(거버넌스|지배구조|governance|board|이사회)',
        'strategy': r'(전략|strategy|risk management|리스크 관리)',
        'risk_management': r'(리스크 관리|위험 관리|risk management)',
        'metrics': r'(지표|metrics|targets|목표|kpi)',
        'climate': r'(기후|climate|탄소|carbon|온실가스|ghg)',
        'social': r'(사회|social|인권|human rights|노동|labor)',
        'environmental': r'(환경|environmental|에너지|energy|수자원|water)',
        'materiality': r'(중요성|materiality|이해관계자|stakeholder)'
    }

    # 텍스트를 문단으로 분리
    paragraphs = text.split('\n\n')

    current_section = 'general'
    current_content = []

    for para in paragraphs:
        if not para.strip():
            continue

        # 섹션 헤더 탐지
        detected = False
        for section_type, pattern in section_patterns.items():
            if re.search(pattern, para, re.IGNORECASE):
                # 이전 섹션 저장
                if current_content:
                    sections.append({
                        'section_type': current_section,
                        'content': '\n\n'.join(current_content)
                    })
                    current_content = []

                current_section = section_type
                detected = True
                break

        current_content.append(para)

    # 마지막 섹션 저장
    if current_content:
        sections.append({
            'section_type': current_section,
            'content': '\n\n'.join(current_content)
        })

    logger.info(f"Detected {len(sections)} sections")
    return sections


def chunk_text(text: str, max_tokens: int = 2000) -> List[str]:
    """
    텍스트 청킹 (토큰 기반)

    Args:
        text: 입력 텍스트
        max_tokens: 최대 토큰 수

    Returns:
        청크 리스트
    """
    # 간단한 청킹: 문단 단위로 분할
    paragraphs = text.split('\n\n')
    chunks = []
    current_chunk = []
    current_length = 0

    for para in paragraphs:
        para_length = len(para.split())  # 단어 수 근사치

        if current_length + para_length > max_tokens and current_chunk:
            # 현재 청크 저장
            chunks.append('\n\n'.join(current_chunk))
            current_chunk = []
            current_length = 0

        current_chunk.append(para)
        current_length += para_length

    # 마지막 청크
    if current_chunk:
        chunks.append('\n\n'.join(current_chunk))

    logger.info(f"Created {len(chunks)} chunks (max_tokens={max_tokens})")
    return chunks


def upload_report(
    vector_store: QdrantVectorStore,
    pdf_path: str,
    company_name: str,
    report_year: int,
    report_type: str = "ESG"
) -> int:
    """
    단일 보고서 업로드

    Args:
        vector_store: Qdrant Vector Store 인스턴스
        pdf_path: PDF 파일 경로
        company_name: 회사명
        report_year: 보고서 연도
        report_type: 보고서 타입 (ESG, TCFD, Sustainability)

    Returns:
        업로드된 문서 개수
    """
    logger.info(f"Uploading report: {company_name} - {report_year}")

    try:
        # 1. PDF 파싱
        parsed = parse_pdf(pdf_path)

        # 2. 섹션 탐지
        sections = detect_sections(parsed['full_text'])

        # 3. 문서 리스트 생성
        documents = []

        for idx, section in enumerate(sections):
            section_type = section['section_type']
            content = section['content']

            # 청킹 (섹션이 너무 길면)
            chunks = chunk_text(content, max_tokens=2000)

            for chunk_idx, chunk in enumerate(chunks):
                if not chunk.strip():
                    continue

                # 요약 생성 (첫 200자)
                summary = chunk[:200] + "..." if len(chunk) > 200 else chunk

                doc = {
                    'id': f"{company_name}_{report_year}_{section_type}_{idx}_{chunk_idx}",
                    'content': chunk,
                    'company_name': company_name,
                    'report_year': report_year,
                    'report_type': report_type,
                    'section_type': section_type,
                    'content_summary': summary,
                    'metadata': {
                        'file_name': Path(pdf_path).name,
                        'section_index': idx,
                        'chunk_index': chunk_idx,
                        'total_chunks': len(chunks)
                    },
                    'tags': [company_name.lower(), str(report_year), report_type.lower(), section_type]
                }

                documents.append(doc)

        logger.info(f"Created {len(documents)} document chunks")

        # 4. 배치 업로드
        uploaded_count = vector_store.add_documents(documents, batch_size=50)

        logger.info(f"Successfully uploaded {uploaded_count} documents")
        return uploaded_count

    except Exception as e:
        logger.error(f"Upload failed: {e}")
        raise


def main():
    """
    메인 실행 함수
    """
    parser = argparse.ArgumentParser(description="Upload ESG/TCFD reports to Qdrant")

    # 단일 파일 업로드
    parser.add_argument('--pdf', type=str, help='PDF file path')
    parser.add_argument('--company', type=str, help='Company name')
    parser.add_argument('--year', type=int, help='Report year')
    parser.add_argument('--type', type=str, default='ESG', help='Report type (ESG, TCFD, Sustainability)')

    # 배치 업로드
    parser.add_argument('--dir', type=str, help='Directory containing PDF files')
    parser.add_argument('--batch', action='store_true', help='Batch upload mode')

    # Qdrant 설정
    parser.add_argument('--qdrant-url', type=str, default=None, help='Qdrant URL (default: env QDRANT_URL)')
    parser.add_argument('--collection', type=str, default=None, help='Collection name (default: env QDRANT_COLLECTION)')

    args = parser.parse_args()

    # Qdrant Vector Store 초기화
    try:
        qdrant_url = args.qdrant_url or os.getenv('QDRANT_URL', 'http://localhost:6333')
        qdrant_api_key = os.getenv('QDRANT_API_KEY')
        collection_name = args.collection or os.getenv('QDRANT_COLLECTION', 'esg_tcfd_reports')

        logger.info(f"Connecting to Qdrant: {qdrant_url}")
        vector_store = QdrantVectorStore(
            url=qdrant_url,
            api_key=qdrant_api_key,
            collection_name=collection_name
        )

        # 컬렉션 정보 확인
        info = vector_store.get_collection_info()
        logger.info(f"Collection: {info['collection_name']}")
        logger.info(f"Existing documents: {info['points_count']}")

    except Exception as e:
        logger.error(f"Failed to initialize Qdrant: {e}")
        sys.exit(1)

    # 단일 파일 업로드
    if args.pdf:
        if not args.company or not args.year:
            logger.error("--company and --year are required for single file upload")
            sys.exit(1)

        if not Path(args.pdf).exists():
            logger.error(f"File not found: {args.pdf}")
            sys.exit(1)

        try:
            count = upload_report(
                vector_store=vector_store,
                pdf_path=args.pdf,
                company_name=args.company,
                report_year=args.year,
                report_type=args.type
            )

            logger.info(f"Upload completed: {count} documents")

        except Exception as e:
            logger.error(f"Upload failed: {e}")
            sys.exit(1)

    # 배치 업로드
    elif args.batch and args.dir:
        if not Path(args.dir).exists():
            logger.error(f"Directory not found: {args.dir}")
            sys.exit(1)

        pdf_files = list(Path(args.dir).glob('*.pdf'))

        if not pdf_files:
            logger.warning(f"No PDF files found in {args.dir}")
            sys.exit(0)

        logger.info(f"Found {len(pdf_files)} PDF files")

        total_uploaded = 0

        for pdf_path in pdf_files:
            try:
                # 파일명에서 회사명/연도 추출 시도
                # 예: Samsung_ESG_2024.pdf → Samsung, 2024
                file_name = pdf_path.stem
                parts = file_name.split('_')

                company_name = parts[0] if parts else "Unknown"
                report_year = 2024  # 기본값

                for part in parts:
                    if part.isdigit() and len(part) == 4:
                        report_year = int(part)
                        break

                logger.info(f"Processing: {pdf_path.name} ({company_name}, {report_year})")

                count = upload_report(
                    vector_store=vector_store,
                    pdf_path=str(pdf_path),
                    company_name=company_name,
                    report_year=report_year,
                    report_type=args.type
                )

                total_uploaded += count

            except Exception as e:
                logger.error(f"Failed to upload {pdf_path.name}: {e}")
                continue

        logger.info(f"Batch upload completed: {total_uploaded} documents from {len(pdf_files)} files")

    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
