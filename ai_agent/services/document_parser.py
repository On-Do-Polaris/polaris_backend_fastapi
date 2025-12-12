"""
파일명: document_parser.py
최종 수정일: 2025-12-12
버전: v01
파일 개요: LlamaParse를 활용한 PDF 문서 파싱 서비스

주의사항:
- LlamaParse Free Tier: 1,000 pages/month
- 파싱 결과는 로컬 캐시에 저장하여 재사용
- 실제 파싱 실행은 scripts/parse_rag_documents.py에서만 수행
"""

import os
import json
from typing import List, Dict, Any, Optional
from pathlib import Path
from llama_parse import LlamaParse
from dotenv import load_dotenv


load_dotenv()


class DocumentParser:
    """
    LlamaParse를 활용한 PDF 문서 파싱 클래스

    주요 기능:
    - PDF → Markdown 변환
    - 테이블 구조 보존
    - 파싱 결과 캐싱 (재파싱 방지)
    """

    def __init__(
        self,
        result_type: str = "markdown",
        verbose: bool = True,
        cache_dir: str = "data/parsed_docs"
    ):
        """
        Args:
            result_type: 파싱 결과 형식 ("text", "markdown", "json")
            verbose: 파싱 진행 상황 로깅 여부
            cache_dir: 파싱 결과 캐시 디렉토리
        """
        api_key = os.getenv("LLAMA_CLOUD_API_KEY")
        if not api_key:
            raise ValueError(
                "LLAMA_CLOUD_API_KEY not found in environment variables. "
                "Please add it to .env file."
            )

        self.parser = LlamaParse(
            api_key=api_key,
            result_type=result_type,
            verbose=verbose
        )

        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # 파싱 메타데이터 파일
        self.metadata_file = self.cache_dir / "parsing_metadata.json"
        self._init_metadata()

    def _init_metadata(self):
        """메타데이터 파일 초기화"""
        if not self.metadata_file.exists():
            with open(self.metadata_file, 'w', encoding='utf-8') as f:
                json.dump({
                    "parsed_documents": [],
                    "total_pages_used": 0,
                    "last_updated": None
                }, f, indent=2)

    def _load_metadata(self) -> Dict[str, Any]:
        """메타데이터 로드"""
        with open(self.metadata_file, 'r', encoding='utf-8') as f:
            return json.load(f)

    def _save_metadata(self, metadata: Dict[str, Any]):
        """메타데이터 저장"""
        with open(self.metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)

    def _get_cache_path(self, file_path: str) -> Path:
        """파일 경로에서 캐시 파일 경로 생성"""
        file_name = Path(file_path).stem
        return self.cache_dir / f"{file_name}_parsed.json"

    def _save_to_cache(
        self,
        documents: List[Any],
        cache_path: Path,
        source_file: str,
        page_count: int
    ):
        """파싱 결과를 캐시에 저장"""
        cache_data = {
            "source_file": source_file,
            "page_count": page_count,
            "documents": [
                {
                    "text": doc.text,
                    "metadata": doc.metadata
                }
                for doc in documents
            ]
        }

        with open(cache_path, 'w', encoding='utf-8') as f:
            json.dump(cache_data, f, indent=2, ensure_ascii=False)

        # 메타데이터 업데이트
        metadata = self._load_metadata()
        metadata["parsed_documents"].append({
            "source_file": source_file,
            "cache_path": str(cache_path),
            "page_count": page_count,
            "parsed_at": str(Path().absolute())
        })
        metadata["total_pages_used"] += page_count

        from datetime import datetime
        metadata["last_updated"] = datetime.now().isoformat()

        self._save_metadata(metadata)

        print(f"✅ Cached to: {cache_path}")
        print(f"📊 Total pages used: {metadata['total_pages_used']} / 1,000 (Free Tier)")

    def _load_from_cache(self, cache_path: Path) -> List[Dict[str, Any]]:
        """캐시에서 파싱 결과 로드"""
        if not cache_path.exists():
            return None

        with open(cache_path, 'r', encoding='utf-8') as f:
            cache_data = json.load(f)

        print(f"✅ Loaded from cache: {cache_path}")
        return cache_data["documents"]

    def parse_pdf(
        self,
        file_path: str,
        force_reparse: bool = False
    ) -> List[Dict[str, Any]]:
        """
        PDF 파싱 (캐시 우선 사용)

        Args:
            file_path: PDF 파일 경로
            force_reparse: True면 캐시 무시하고 재파싱 (주의: 사용량 소진)

        Returns:
            파싱된 문서 리스트
        """
        if not Path(file_path).exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        cache_path = self._get_cache_path(file_path)

        # 캐시 확인
        if not force_reparse:
            cached_docs = self._load_from_cache(cache_path)
            if cached_docs:
                return cached_docs

        # 실제 파싱 실행 (주의: LlamaParse API 호출)
        print(f"⚠️  Parsing {file_path} using LlamaParse...")
        print(f"⚠️  This will consume Free Tier quota.")

        documents = self.parser.load_data(file_path)

        # 페이지 수 추정 (문서 메타데이터에서 확인)
        page_count = self._estimate_page_count(documents)

        # 캐시 저장
        self._save_to_cache(documents, cache_path, file_path, page_count)

        return [
            {
                "text": doc.text,
                "metadata": doc.metadata
            }
            for doc in documents
        ]

    def _estimate_page_count(self, documents: List[Any]) -> int:
        """파싱된 문서에서 페이지 수 추정"""
        # LlamaParse는 메타데이터에 페이지 정보 포함
        pages = set()
        for doc in documents:
            if hasattr(doc, 'metadata') and 'page' in doc.metadata:
                pages.add(doc.metadata['page'])

        return len(pages) if pages else len(documents)

    def extract_tables_from_markdown(
        self,
        markdown_text: str
    ) -> List[Dict[str, Any]]:
        """
        Markdown 텍스트에서 테이블 추출

        Args:
            markdown_text: Markdown 형식 텍스트

        Returns:
            테이블 리스트 [{"markdown": "...", "data": {...}}]
        """
        import re

        tables = []

        # Markdown 테이블 패턴: | header | header |
        table_pattern = r'(\|[^\n]+\|\n\|[-:\s|]+\|\n(?:\|[^\n]+\|\n)+)'

        matches = re.finditer(table_pattern, markdown_text, re.MULTILINE)

        for match in matches:
            table_markdown = match.group(0)

            # 테이블 데이터 파싱
            lines = table_markdown.strip().split('\n')
            if len(lines) < 3:  # header + separator + at least 1 row
                continue

            # Header 추출
            headers = [cell.strip() for cell in lines[0].split('|') if cell.strip()]

            # Rows 추출 (separator 제외)
            rows = []
            for line in lines[2:]:
                cells = [cell.strip() for cell in line.split('|') if cell.strip()]
                if len(cells) == len(headers):
                    rows.append(cells)

            tables.append({
                "markdown": table_markdown,
                "data": {
                    "headers": headers,
                    "rows": rows
                }
            })

        return tables

    def get_parsing_stats(self) -> Dict[str, Any]:
        """파싱 통계 반환"""
        metadata = self._load_metadata()

        return {
            "total_documents_parsed": len(metadata["parsed_documents"]),
            "total_pages_used": metadata["total_pages_used"],
            "free_tier_limit": 1000,
            "remaining_pages": 1000 - metadata["total_pages_used"],
            "last_updated": metadata["last_updated"],
            "documents": metadata["parsed_documents"]
        }


# 사용 예시
if __name__ == "__main__":
    parser = DocumentParser()

    # 통계 확인
    stats = parser.get_parsing_stats()
    print("\n📊 Parsing Statistics:")
    print(json.dumps(stats, indent=2, ensure_ascii=False))

    # 파싱 예시 (주의: 실제로 실행하지 말 것!)
    # documents = parser.parse_pdf("path/to/document.pdf")
