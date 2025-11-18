from uuid import UUID, uuid4
from typing import Optional
from datetime import datetime

from schemas.reports import (
    ReportGenerationRequest,
    ReportGenerationStatus,
    ReportContent,
)

# ai_agent를 호출하는 서비스
# from ai_agent import run_report_agent


class ReportService:
    """리포트 서비스 - ai_agent의 LLM을 사용하여 리포트 생성"""

    async def generate_report(self, request: ReportGenerationRequest) -> ReportGenerationStatus:
        """리포트 생성 시작"""
        report_id = uuid4()

        # TODO: ai_agent의 LLM 기반 리포트 생성 호출
        # result = await run_report_agent(request)

        return ReportGenerationStatus(
            reportId=report_id,
            scope=request.scope,
            siteId=request.site_id,
            siteIds=request.site_ids,
            status="queued",
            progress=0,
            startedAt=datetime.now(),
        )

    async def get_report_status(self, report_id: UUID) -> Optional[ReportGenerationStatus]:
        """리포트 생성 상태 조회"""
        # TODO: 리포트 생성 상태 조회 구현
        pass

    async def get_report_content(self, report_id: UUID) -> Optional[ReportContent]:
        """리포트 컨텐츠 조회"""
        # TODO: 생성된 리포트 컨텐츠 조회
        pass

    async def get_report_file(self, report_id: UUID, format: str) -> Optional[str]:
        """리포트 파일 경로 반환"""
        # TODO: PDF/DOCX 파일 생성 및 경로 반환
        pass
