from fastapi import APIRouter, Depends, HTTPException, Query

from src.schemas.reports import (
    CreateReportRequest,
)
from src.core.auth import verify_api_key

router = APIRouter(prefix="/api/reports", tags=["Reports"])


def get_report_service():
    """Get the singleton ReportService instance from main app"""
    from main import report_service_instance
    if report_service_instance is None:
        raise HTTPException(status_code=503, detail="ReportService not initialized")
    return report_service_instance


@router.post("", status_code=200)
async def create_report(
    request: CreateReportRequest,
    api_key: str = Depends(verify_api_key),
    service = Depends(get_report_service),
):
    """Spring Boot API 호환 - 리포트 생성"""
    return await service.create_report(request)


@router.get("/web")
async def get_report_web_view(
    report_id: str = Query(..., alias="reportId"),
    api_key: str = Depends(verify_api_key),
    service = Depends(get_report_service),
):
    """웹 리포트 뷰 조회 - 프론트엔드 렌더링용 데이터 반환 - query parameters 사용

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
    result = await service.get_report_web_view(report_id)
    if not result:
        raise HTTPException(status_code=404, detail="Report not found")
    return result


@router.get("/pdf")
async def get_report_pdf(
    report_id: str = Query(..., alias="reportId"),
    api_key: str = Depends(verify_api_key),
    service = Depends(get_report_service),
):
    """PDF 리포트 다운로드 - query parameters 사용

    Args:
        report_id: 리포트 ID (create_report에서 반환된 reportId)

    Returns:
        PDF 파일 (FileResponse)
    """
    from fastapi.responses import FileResponse
    import os

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
    service = Depends(get_report_service),
):
    """Spring Boot API 호환 - 리포트 삭제"""
    return await service.delete_report()
