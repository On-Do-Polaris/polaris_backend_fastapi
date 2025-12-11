from fastapi import APIRouter, Depends
from typing import Optional
from uuid import UUID
import logging

from src.schemas.dashboard import DashboardSummaryResponse
from src.services.dashboard_service import DashboardService
from src.core.auth import verify_api_key

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])


@router.get("/summary", response_model=DashboardSummaryResponse)
async def get_dashboard_summary(
    api_key: str = Depends(verify_api_key)
) -> DashboardSummaryResponse:
    """
    대시보드 요약 정보 조회

    전체 사업장의 통합 리스크 점수와 주요 기후 리스크를 반환합니다.
    """
    service = DashboardService()
    return await service.get_dashboard_summary()
