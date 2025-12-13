#!/usr/bin/env python3
"""
파일명: ingest_rag_documents.py
최종 수정일: 2025-12-12
버전: v01
파일 개요: RAG 문서 파싱 및 Qdrant 업로드 실행 스크립트

주의사항:
- LlamaParse Free Tier: 1,000 pages/month
- 실행 전 LLAMA_CLOUD_API_KEY 환경변수 확인
- Qdrant 서버 실행 확인 (http://localhost:6333)
- 처음 실행 시에만 파싱 수행 (이후 캐시 사용)

사용법:
    # 전체 문서 수집
    python scripts/ingest_rag_documents.py --all

    # 특정 문서만 수집
    python scripts/ingest_rag_documents.py --document tcfd

    # 캐시 무시하고 재파싱 (주의!)
    python scripts/ingest_rag_documents.py --all --force-reparse

    # 통계만 확인
    python scripts/ingest_rag_documents.py --stats
"""

import os
import sys
import argparse
import json
from pathlib import Path

# 프로젝트 루트를 PYTHONPATH에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
from ai_agent.services.rag_ingestion_service import RAGIngestionService

# 환경변수 로드
load_dotenv()


# ============================================================
# 문서 설정
# ============================================================
DOCUMENT_CONFIGS = [
    {
        'file_path': '각종 자료/For_RAG/FINAL-2017-TCFD-Report.pdf',
        'metadata': {
            'document_id': 'tcfd_official_2017',
            'document_type': 'guideline',
            'source': 'TCFD',
            'year': 2017,
            'title': 'Final Report: Recommendations of the TCFD',
            'tags': ['tcfd', 'governance', 'strategy', 'risk_management', 'metrics', 'guidelines']
        }
    },
    {
        'file_path': '각종 자료/For_RAG/SnP_Climanomics_PangyoDC_Summary_Report_SK C&C_2024-02-08.pdf',
        'metadata': {
            'document_id': 'snp_climanomics_pangyo_2024',
            'document_type': 'analysis',
            'source': 'S&P Global',
            'year': 2024,
            'title': 'Climanomics Pangyo DC Summary Report - SK C&C',
            'tags': ['s&p', 'climanomics', 'physical_risk', 'data_center', 'pangyo', 'analysis']
        }
    }
]


def validate_environment():
    """
    환경변수 및 필수 파일 검증

    Returns:
        bool: 검증 성공 여부
    """
    print("\n🔍 Validating environment...")

    # 1. LLAMA_CLOUD_API_KEY 확인
    api_key = os.getenv('LLAMA_CLOUD_API_KEY')
    if not api_key:
        print("❌ LLAMA_CLOUD_API_KEY not found in environment variables")
        print("   Please add it to .env file")
        return False
    print(f"✅ LLAMA_CLOUD_API_KEY: {api_key[:10]}...")

    # 2. PDF 파일 존재 확인
    missing_files = []
    for config in DOCUMENT_CONFIGS:
        file_path = project_root / config['file_path']
        if not file_path.exists():
            missing_files.append(config['file_path'])
        else:
            print(f"✅ Found: {config['file_path']}")

    if missing_files:
        print(f"\n❌ Missing files:")
        for file in missing_files:
            print(f"   - {file}")
        return False

    # 3. Qdrant 연결 확인 (선택사항)
    qdrant_url = os.getenv('QDRANT_URL', 'http://localhost:6333')
    print(f"\n⚠️  Qdrant URL: {qdrant_url}")
    print("   (If Qdrant is not running, ingestion will validate structure only)")

    return True


def show_stats():
    """
    파싱 및 RAG 통계 출력
    """
    print("\n📊 RAG Ingestion Statistics\n" + "=" * 60)

    try:
        service = RAGIngestionService()
        stats = service.get_ingestion_stats()

        print(json.dumps(stats, indent=2, ensure_ascii=False))

        # LlamaParse 사용량 계산
        parser_stats = stats.get('parser_stats', {})
        total_pages = parser_stats.get('total_pages_used', 0)
        remaining = parser_stats.get('remaining_pages', 1000)

        print(f"\n📄 LlamaParse Usage:")
        print(f"   Total pages used: {total_pages} / 1,000")
        print(f"   Remaining: {remaining} pages")

        # Qdrant 상태
        if stats.get('qdrant_available'):
            print(f"\n📦 Qdrant Collections:")

            if 'tcfd_documents' in stats:
                doc_info = stats['tcfd_documents']
                print(f"   tcfd_documents: {doc_info.get('points_count', 0)} documents")

            if 'tcfd_tables' in stats:
                table_info = stats['tcfd_tables']
                print(f"   tcfd_tables: {table_info.get('points_count', 0)} tables")
        else:
            print(f"\n⚠️  Qdrant: Not available")

    except Exception as e:
        print(f"❌ Failed to get statistics: {e}")


def ingest_documents(
    document_filter: str = 'all',
    force_reparse: bool = False
):
    """
    문서 파싱 및 Qdrant 업로드

    Args:
        document_filter: 'all', 'tcfd', 'snp'
        force_reparse: 캐시 무시하고 재파싱 여부
    """
    # 필터링
    configs_to_process = DOCUMENT_CONFIGS

    if document_filter == 'tcfd':
        configs_to_process = [c for c in DOCUMENT_CONFIGS if 'tcfd' in c['metadata']['document_id']]
    elif document_filter == 'snp':
        configs_to_process = [c for c in DOCUMENT_CONFIGS if 'snp' in c['metadata']['document_id']]

    print(f"\n🚀 Starting ingestion for {len(configs_to_process)} documents...")
    print(f"   Force reparse: {force_reparse}")
    print("=" * 60)

    # RAG Ingestion Service 초기화
    service = RAGIngestionService()

    # 문서 처리
    results = []

    for i, config in enumerate(configs_to_process, 1):
        print(f"\n[{i}/{len(configs_to_process)}] Processing: {config['metadata']['title']}")
        print(f"   File: {config['file_path']}")

        # 절대 경로로 변환
        file_path = project_root / config['file_path']

        try:
            result = service.ingest_pdf(
                file_path=str(file_path),
                document_metadata=config['metadata'],
                force_reparse=force_reparse
            )

            results.append(result)

            # 결과 출력
            print(f"   ✅ Success:")
            print(f"      - Parsed chunks: {result.get('parsed_chunks', 0)}")
            print(f"      - Text chunks: {result.get('text_chunks_created', 0)}")
            print(f"      - Tables: {result.get('tables_extracted', 0)}")

            if result.get('uploaded_to_qdrant'):
                print(f"      - Uploaded to Qdrant: {result.get('documents_uploaded', 0)} docs, {result.get('tables_uploaded', 0)} tables")
            else:
                print(f"      - Qdrant upload: Skipped (offline mode)")

        except Exception as e:
            print(f"   ❌ Failed: {e}")
            results.append({
                'file_path': config['file_path'],
                'error': str(e),
                'status': 'failed'
            })

    # 최종 요약
    print("\n" + "=" * 60)
    print("📋 Ingestion Summary:")

    success_count = sum(1 for r in results if r.get('uploaded_to_qdrant') or 'error' not in r)
    fail_count = len(results) - success_count

    print(f"   Total: {len(results)} documents")
    print(f"   Success: {success_count}")
    print(f"   Failed: {fail_count}")

    # 통계 출력
    show_stats()


def main():
    """
    메인 실행 함수
    """
    parser = argparse.ArgumentParser(
        description='RAG Document Ingestion Script',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )

    parser.add_argument(
        '--all',
        action='store_true',
        help='Ingest all documents'
    )

    parser.add_argument(
        '--document',
        choices=['tcfd', 'snp'],
        help='Ingest specific document type only'
    )

    parser.add_argument(
        '--force-reparse',
        action='store_true',
        help='Force reparse (ignore cache) - WARNING: consumes LlamaParse quota'
    )

    parser.add_argument(
        '--stats',
        action='store_true',
        help='Show statistics only'
    )

    args = parser.parse_args()

    # 환경변수 검증
    if not validate_environment():
        print("\n❌ Environment validation failed. Please fix the issues above.")
        sys.exit(1)

    # 통계만 출력
    if args.stats:
        show_stats()
        return

    # 문서 수집
    if args.all:
        ingest_documents(document_filter='all', force_reparse=args.force_reparse)
    elif args.document:
        ingest_documents(document_filter=args.document, force_reparse=args.force_reparse)
    else:
        parser.print_help()
        print("\n💡 Tip: Use --all to ingest all documents, or --document tcfd/snp for specific ones")
        print("        Use --stats to see current statistics without ingesting")


if __name__ == "__main__":
    main()
