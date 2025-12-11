from fastapi import APIRouter, Depends, HTTPException, Query
from uuid import UUID
from typing import Optional

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


@router.get("")
async def get_reports_by_user(
    user_id: UUID = Query(..., alias="userId"),
    api_key: str = Depends(verify_api_key),
    service = Depends(get_report_service),
):
    """
    사용자별 리포트 조회 (Spring Boot 호환)

    Args:
        userId: 사용자 ID

    Returns:
        최신 리포트 데이터
    """
    result = await service.get_reports_by_user_id(user_id)
    if not result:
        raise HTTPException(
            status_code=404,
            detail=f"No reports found for userId: {user_id}"
        )
    return result


@router.get("/web")
async def get_report_web_view(
    report_id: Optional[str] = Query(None, alias="reportId"),
    user_id: Optional[UUID] = Query(None, alias="userId"),
    api_key: str = Depends(verify_api_key),
    service = Depends(get_report_service),
):
    """
    웹 리포트 뷰 조회 (Spring Boot 호환)

    Args:
        reportId: 리포트 ID (선택)
        userId: 사용자 ID (선택)

    둘 중 하나는 필수입니다.
    """
    # reportId와 userId 둘 다 없으면 에러
    if not report_id and not user_id:
        raise HTTPException(
            status_code=400,
            detail="Either reportId or userId is required"
        )

    # 둘 다 있으면 에러
    if report_id and user_id:
        raise HTTPException(
            status_code=400,
            detail="Cannot specify both reportId and userId"
        )

    # reportId 우선
    if report_id:
        result = await service.get_report_web_view(report_id)
    else:
        # userId로 최신 리포트 조회
        result = await service.get_latest_report_by_user(user_id)

    if not result:
        raise HTTPException(status_code=404, detail="Report not found")
    return result


@router.get("/pdf")
async def get_report_pdf(
    report_id: Optional[str] = Query(None, alias="reportId"),
    user_id: Optional[UUID] = Query(None, alias="userId"),
    api_key: str = Depends(verify_api_key),
    service = Depends(get_report_service),
):
    """
    PDF 리포트 다운로드 (Spring Boot 호환)

    Args:
        reportId: 리포트 ID (선택)
        userId: 사용자 ID (선택)

    둘 중 하나는 필수입니다.
    """
    from fastapi.responses import FileResponse
    import os

    # 파라미터 검증
    if not report_id and not user_id:
        raise HTTPException(
            status_code=400,
            detail="Either reportId or userId is required"
        )

    if report_id and user_id:
        raise HTTPException(
            status_code=400,
            detail="Cannot specify both reportId and userId"
        )

    # userId로 조회하는 경우, 먼저 reportId를 얻어야 함
    if user_id and not report_id:
        # userId의 최신 리포트 조회
        user_report = await service.get_latest_report_by_user(user_id)
        if not user_report:
            raise HTTPException(status_code=404, detail=f"No reports found for userId: {user_id}")
        # reportId 추출 (구현 방식에 따라 다를 수 있음)
        # 임시로 user_reports에서 가져오기
        report_ids = service._user_reports.get(user_id, [])
        if report_ids:
            report_id = str(report_ids[-1])

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


@router.post("/data", status_code=200)
async def register_report_data(
    request: dict,
    api_key: str = Depends(verify_api_key),
    service = Depends(get_report_service),
):
    """
    리포트 추가 데이터 등록 (Spring Boot 호환)

    Args:
        request: {"userId": "...", "additionalData": {...}}
    """
    user_id = request.get("userId")
    if not user_id:
        raise HTTPException(status_code=400, detail="userId is required")

    result = await service.register_report_data(user_id, request)
    return result


@router.delete("", status_code=200)
async def delete_report(
    api_key: str = Depends(verify_api_key),
    service = Depends(get_report_service),
):
    """Spring Boot API 호환 - 리포트 삭제 (전체)"""
    return await service.delete_report()
