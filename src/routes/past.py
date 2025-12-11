from fastapi import APIRouter, Depends, Query
from uuid import UUID
from typing import Optional
from datetime import datetime

from src.schemas.disaster_history import (
    DisasterHistoryListResponse,
    DisasterHistoryFilter,
    DisasterSeverity,
)
from src.schemas.common import HazardType
from src.services.disaster_history_service import DisasterHistoryService
from src.core.auth import verify_api_key

router = APIRouter(prefix="/api/past", tags=["Past Events (Spring Boot Compatibility)"])


@router.get("", response_model=DisasterHistoryListResponse)
async def get_past_events(
    site_id: Optional[UUID] = Query(None, alias="siteId"),
    year: Optional[int] = Query(None, description="연도로 필터링"),
    disaster_type: Optional[HazardType] = Query(None, alias="disasterType"),
    severity: Optional[DisasterSeverity] = Query(None, description="심각도로 필터링"),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    api_key: str = Depends(verify_api_key),
):
    """
    과거 재난 이력 조회 (Spring Boot 호환)

    /api/disaster-history 엔드포인트의 별칭입니다.

    Args:
        siteId: 사업장 ID (선택)
        year: 연도 필터 (선택)
        disasterType: 재해 유형 (선택)
        severity: 심각도 (선택)
        limit: 조회 개수 (기본: 100)
        offset: 조회 시작 위치 (기본: 0)

    Returns:
        DisasterHistoryListResponse
    """
    service = DisasterHistoryService()

    # year 파라미터를 start_date/end_date로 변환
    start_date = None
    end_date = None
    if year:
        start_date = datetime(year, 1, 1)
        end_date = datetime(year, 12, 31, 23, 59, 59)

    filters = DisasterHistoryFilter(
        site_id=site_id,
        disaster_type=disaster_type,
        severity=severity,
        start_date=start_date,
        end_date=end_date,
        limit=limit,
        offset=offset,
    )

    result = await service.get_disaster_history(filters)
    return result
