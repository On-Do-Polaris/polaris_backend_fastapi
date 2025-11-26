from fastapi import APIRouter, Depends, HTTPException

from src.schemas.reports import (
    CreateReportRequest,
    ReportWebViewResponse,
    ReportPdfResponse,
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


@router.get("/web", response_model=ReportWebViewResponse)
async def get_report_web_view(
    api_key: str = Depends(verify_api_key),
):
    """Spring Boot API 호환 - 웹 리포트 뷰 조회"""
    service = ReportService()
    result = await service.get_report_web_view()
    if not result:
        raise HTTPException(status_code=404, detail="Report not found")
    return result


@router.get("/pdf", response_model=ReportPdfResponse)
async def get_report_pdf(
    api_key: str = Depends(verify_api_key),
):
    """Spring Boot API 호환 - PDF 리포트 조회"""
    service = ReportService()
    result = await service.get_report_pdf()
    if not result:
        raise HTTPException(status_code=404, detail="Report not found")
    return result


@router.delete("", status_code=200)
async def delete_report(
    api_key: str = Depends(verify_api_key),
):
    """Spring Boot API 호환 - 리포트 삭제"""
    service = ReportService()
    return await service.delete_report()
