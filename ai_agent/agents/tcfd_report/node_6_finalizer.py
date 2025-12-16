"""
Node 9: Finalizer
JSONB DB 저장 및 메타데이터 업데이트 (PDF 제거)
"""

from typing import Dict, Any
from datetime import datetime


class FinalizerNode:
    """
    Node 9: Finalizer 노드

    입력:
        - report: Dict (Node 8 출력)
        - user_id: int
        - site_ids: List[int]

    출력:
        - success: bool
        - report_id: int
        - download_url: str
        - meta: Dict
    """

    def __init__(self, db_session):
        self.db = db_session

    async def execute(
        self,
        report: Dict,
        user_id: int,
        site_ids: list
    ) -> Dict[str, Any]:
        """
        메인 실행 함수
        """
        # 1. JSONB로 DB 저장
        db_report_id = await self._save_to_db(report, user_id)

        # 2. 사업장-보고서 관계 저장
        await self._save_report_sites(db_report_id, site_ids)

        # PDF 생성 제거 - 프론트엔드에서 처리

        return {
            "success": True,
            "report_id": db_report_id,
            "download_url": f"/api/reports/{db_report_id}/download",
            "meta": report["meta"]
        }

    async def _save_to_db(self, report: Dict, user_id: int) -> int:
        """DB 저장 (JSONB)"""
        # TODO: DB 저장 로직
        # db_report = Report(
        #     user_id=user_id,
        #     title=report["meta"]["title"],
        #     report_type="TCFD",
        #     content=report,  # JSONB 컬럼
        #     total_pages=report["meta"]["total_pages"],
        #     total_aal=report["meta"]["total_aal"],
        #     site_count=report["meta"]["site_count"],
        #     generated_at=datetime.now(),
        #     llm_model=report["meta"]["llm_model"],
        #     status="completed"
        # )
        # await self.db.add(db_report)
        # await self.db.commit()
        # return db_report.id

        return 123  # TODO

    async def _save_report_sites(self, report_id: int, site_ids: list):
        """사업장-보고서 관계 저장"""
        # TODO: ReportSite 테이블에 저장
        pass
