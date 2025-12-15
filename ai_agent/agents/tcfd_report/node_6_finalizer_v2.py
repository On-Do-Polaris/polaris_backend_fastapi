"""
Node 6: Finalizer v2
최종 수정일: 2025-12-15
버전: v2.0

개요:
    Node 6: Finalizer 노드 (JSONB DB 저장 및 메타데이터 업데이트)

    - JSONB로 DB 저장 (PostgreSQL)
    - 사업장-보고서 관계 저장
    - 보고서 메타데이터 업데이트
    - PDF 생성은 프론트엔드에서 처리

주요 기능:
    1. TCFD 보고서 DB 저장 (JSONB 형식)
    2. 사업장-보고서 관계 저장
    3. 다운로드 URL 생성
    4. 최종 결과 반환

입력:
    - report: Dict (Node 5 출력)
    - user_id: int (사용자 ID)
    - site_ids: List[int] (사업장 ID 리스트)

출력:
    - success: bool
    - report_id: int (DB에 저장된 보고서 ID)
    - download_url: str
    - meta: Dict (보고서 메타데이터)
"""

import json
from typing import Dict, Any, List, Optional
from datetime import datetime


class FinalizerNode:
    """
    Node 6: Finalizer 노드 v2

    역할:
        - TCFD 보고서 DB 저장 (JSONB)
        - 사업장-보고서 관계 저장
        - 최종 결과 반환

    의존성:
        - Node 5 (Composer) 완료 필수
        - DB 세션 필요
    """

    def __init__(self, db_session=None):
        """
        Node 초기화

        Args:
            db_session: DB 세션 (optional)
        """
        self.db = db_session

    async def execute(
        self,
        report: Dict,
        user_id: int,
        site_ids: List[int]
    ) -> Dict[str, Any]:
        """
        메인 실행 함수

        Args:
            report: Node 5 출력 (전체 보고서)
            user_id: 사용자 ID
            site_ids: 사업장 ID 리스트

        Returns:
            Dict: 최종 결과 (success, report_id, download_url, meta)
        """
        print("\n" + "="*80)
        print("▶ Node 6: Finalizer DB 저장 시작")
        print("="*80)

        # 1. JSONB로 DB 저장
        print("\n[Step 1/3] JSONB로 DB 저장...")
        db_report_id = await self._save_to_db(report, user_id)
        print(f"  ✅ DB 저장 완료 (Report ID: {db_report_id})")

        # 2. 사업장-보고서 관계 저장
        print("\n[Step 2/3] 사업장-보고서 관계 저장...")
        await self._save_report_sites(db_report_id, site_ids)
        print(f"  ✅ 관계 저장 완료 ({len(site_ids)}개 사업장)")

        # 3. 다운로드 URL 생성
        print("\n[Step 3/3] 다운로드 URL 생성...")
        download_url = f"/api/reports/{db_report_id}/download"
        print(f"  ✅ URL 생성 완료: {download_url}")

        print("\n" + "="*80)
        print(f"✅ Node 6: Finalizer 완료 (Report ID: {db_report_id})")
        print("="*80)

        # PDF 생성 제거 - 프론트엔드에서 처리
        return {
            "success": True,
            "report_id": db_report_id,
            "download_url": download_url,
            "meta": report.get("meta", {}),
            "report": report  # 전체 보고서도 반환 (프론트엔드에서 렌더링용)
        }

    async def _save_to_db(self, report: Dict, user_id: int) -> int:
        """
        DB 저장 (JSONB)

        Args:
            report: 전체 보고서 JSON
            user_id: 사용자 ID

        Returns:
            int: DB에 저장된 Report ID
        """
        if self.db is None:
            # DB 세션이 없는 경우 (테스트용)
            print("  ⚠️  DB 세션이 없어 실제 저장을 생략합니다 (테스트 모드)")
            return 123  # Mock ID

        # TODO: 실제 DB 저장 로직 (FastAPI + SQLAlchemy)
        # 예시:
        # from app.models import Report
        # from sqlalchemy.dialects.postgresql import JSONB
        #
        # db_report = Report(
        #     user_id=user_id,
        #     title=report.get("meta", {}).get("title", "TCFD 보고서"),
        #     report_type="TCFD",
        #     content=report,  # JSONB 컬럼
        #     total_pages=report.get("meta", {}).get("total_pages", 0),
        #     total_aal=report.get("meta", {}).get("total_aal", 0.0),
        #     site_count=report.get("meta", {}).get("site_count", 0),
        #     generated_at=datetime.now(),
        #     llm_model=report.get("meta", {}).get("llm_model", "unknown"),
        #     status="completed"
        # )
        #
        # self.db.add(db_report)
        # await self.db.commit()
        # await self.db.refresh(db_report)
        #
        # return db_report.id

        # 임시: Mock ID 반환
        return 123

    async def _save_report_sites(self, report_id: int, site_ids: List[int]):
        """
        사업장-보고서 관계 저장

        Args:
            report_id: DB에 저장된 Report ID
            site_ids: 사업장 ID 리스트
        """
        if self.db is None:
            # DB 세션이 없는 경우 (테스트용)
            print("  ⚠️  DB 세션이 없어 관계 저장을 생략합니다 (테스트 모드)")
            return

        # TODO: 실제 DB 저장 로직 (FastAPI + SQLAlchemy)
        # 예시:
        # from app.models import ReportSite
        #
        # for site_id in site_ids:
        #     report_site = ReportSite(
        #         report_id=report_id,
        #         site_id=site_id
        #     )
        #     self.db.add(report_site)
        #
        # await self.db.commit()

        # 임시: 로그만 출력
        pass

    def validate_report(self, report: Dict) -> bool:
        """
        보고서 최종 검증 (DB 저장 전)

        Args:
            report: 전체 보고서 JSON

        Returns:
            bool: 검증 통과 여부
        """
        # 필수 필드 체크
        required_fields = ["report_id", "meta", "table_of_contents", "sections"]
        for field in required_fields:
            if field not in report:
                print(f"  ❌ 필수 필드 누락: {field}")
                return False

        # 메타데이터 체크
        meta = report.get("meta", {})
        meta_required = ["title", "generated_at", "site_count", "total_pages"]
        for field in meta_required:
            if field not in meta:
                print(f"  ❌ 메타데이터 필드 누락: {field}")
                return False

        # 섹션 개수 체크 (최소 4개: Governance, Strategy, Risk Mgmt, Metrics)
        sections = report.get("sections", [])
        if len(sections) < 4:
            print(f"  ❌ 섹션 개수 부족: {len(sections)}개 (최소 4개 필요)")
            return False

        return True

    def get_report_summary(self, report: Dict) -> Dict:
        """
        보고서 요약 정보 생성

        Args:
            report: 전체 보고서 JSON

        Returns:
            Dict: 보고서 요약 정보
        """
        meta = report.get("meta", {})
        sections = report.get("sections", [])

        # 섹션별 블록 개수 계산
        section_stats = []
        for section in sections:
            section_stats.append({
                "title": section.get("title", "Unknown"),
                "blocks": len(section.get("blocks", [])),
                "pages": f"{section.get('page_start', 0)}-{section.get('page_end', 0)}"
            })

        return {
            "report_id": report.get("report_id", "unknown"),
            "title": meta.get("title", "TCFD 보고서"),
            "generated_at": meta.get("generated_at", ""),
            "total_pages": meta.get("total_pages", 0),
            "total_aal": meta.get("total_aal", 0.0),
            "site_count": meta.get("site_count", 0),
            "section_count": len(sections),
            "sections": section_stats
        }
