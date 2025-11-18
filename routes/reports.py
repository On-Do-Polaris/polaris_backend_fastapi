from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from uuid import UUID
from typing import Optional

from schemas.reports import (
    ReportGenerationRequest,
    ReportGenerationStatus,
    ReportContent,
    ReportDownloadInfo,
)
from services.report_service import ReportService
from core.auth import verify_api_key

router = APIRouter(prefix="/api/v1/reports", tags=["Reports"])


@router.post("/generate", response_model=ReportGenerationStatus, status_code=202)
async def generate_report(
    request: ReportGenerationRequest,
    api_key: str = Depends(verify_api_key),
):
    """리포트 생성 시작 (LLM 기반)"""
    service = ReportService()
    return await service.generate_report(request)


@router.get("/{report_id}/status", response_model=ReportGenerationStatus)
async def get_report_status(
    report_id: UUID,
    api_key: str = Depends(verify_api_key),
):
    """리포트 생성 상태 조회"""
    service = ReportService()
    result = await service.get_report_status(report_id)
    if not result:
        raise HTTPException(status_code=404, detail="Report not found")
    return result


@router.get("/{report_id}/content", response_model=ReportContent)
async def get_report_content(
    report_id: UUID,
    api_key: str = Depends(verify_api_key),
):
    """리포트 컨텐츠 조회"""
    service = ReportService()
    result = await service.get_report_content(report_id)
    if not result:
        raise HTTPException(status_code=404, detail="Report not found or not ready")
    return result


@router.get("/{report_id}/download")
async def download_report(
    report_id: UUID,
    format: str = Query("pdf", enum=["pdf", "docx", "json"]),
    api_key: str = Depends(verify_api_key),
):
    """리포트 파일 다운로드"""
    service = ReportService()
    file_path = await service.get_report_file(report_id, format)
    if not file_path:
        raise HTTPException(status_code=404, detail="Report file not found")

    media_types = {
        "pdf": "application/pdf",
        "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "json": "application/json",
    }

    return FileResponse(
        path=file_path,
        media_type=media_types.get(format, "application/octet-stream"),
        filename=f"report_{report_id}.{format}",
    )
