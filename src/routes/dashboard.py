from fastapi import APIRouter, Depends, Query
from typing import Optional, List
from uuid import UUID
import logging

from src.schemas.dashboard import DashboardSummaryResponse
from src.services.dashboard_service import DashboardService
from src.core.auth import verify_api_key

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])


@router.get(
    "/summary",
    response_model=DashboardSummaryResponse,
    responses={
        200: {"description": "대시보드 요약 조회 성공"},
        401: {"description": "API Key 인증 실패"},
        422: {"description": "입력 데이터 검증 실패"}
    }
)
async def get_dashboard_summary(
    # 1. userId 제거됨
    # 2. siteIds 추가: List[UUID] 타입으로 선언하여 반복 쿼리 파라미터 처리
    site_ids: List[UUID] = Query(..., alias="siteIds", description="분석할 사업장 ID 목록"),
    api_key: str = Depends(verify_api_key)
) -> DashboardSummaryResponse:
    """
    대시보드 요약 정보 조회

    전달받은 사업장 ID 목록(siteIds)에 대한 통합 리스크 점수와 주요 기후 리스크를 반환합니다.
    """
    service = DashboardService()
    
    # 서비스 계층의 메서드도 리스트를 받도록 수정 필요
    return await service.get_dashboard_summary(site_ids)
