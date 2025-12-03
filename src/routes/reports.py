from fastapi import APIRouter, Depends, HTTPException

from src.schemas.reports import (
    CreateReportRequest,
)
from src.services.report_service import ReportService
from src.core.auth import verify_api_key

router = APIRouter(prefix="/api/reports", tags=["Reports"])


@router.post("", status_code=200)
async def create_report(
    request: CreateReportRequest,
    api_key: str = Depends(verify_api_key),
):
    """Spring Boot API 호환 - 리포트 생성"""
    service = ReportService()
    return await service.create_report(request)


@router.get("/web/{report_id}")
async def get_report_web_view(
    report_id: str,
    api_key: str = Depends(verify_api_key),
):
    """웹 리포트 뷰 조회 - 프론트엔드 렌더링용 데이터 반환

    Args:
        report_id: 리포트 ID (create_report에서 반환된 reportId)

    Returns:
        {
            "siteId": "...",
            "reportData": {
                "markdown": "# 리포트 텍스트...",
                "json": {...},
                "metadata": {...}
            },
            "createdAt": "2025-12-03T..."
        }
    """
    service = ReportService()
    result = await service.get_report_web_view(report_id)
    if not result:
        raise HTTPException(status_code=404, detail="Report not found")
    return result


@router.get("/pdf/{report_id}")
async def get_report_pdf(
    report_id: str,
    api_key: str = Depends(verify_api_key),
):
    """PDF 리포트 다운로드

    Args:
        report_id: 리포트 ID (create_report에서 반환된 reportId)

    Returns:
        PDF 파일 (FileResponse)
    """
    from fastapi.responses import FileResponse
    import os

    service = ReportService()
    result = await service.get_report_pdf(report_id)

    if not result:
        raise HTTPException(status_code=404, detail="Report not found")

    pdf_path = result.get('pdfPath')

    if not pdf_path or not os.path.exists(pdf_path):
        raise HTTPException(status_code=404, detail="PDF file not found")

    return FileResponse(
        path=pdf_path,
        media_type='application/pdf',
        filename=os.path.basename(pdf_path)
    )


@router.delete("", status_code=200)
async def delete_report(
    api_key: str = Depends(verify_api_key),
):
    """Spring Boot API 호환 - 리포트 삭제"""
    service = ReportService()
    return await service.delete_report()
