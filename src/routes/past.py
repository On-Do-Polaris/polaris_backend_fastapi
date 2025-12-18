from fastapi import APIRouter, Depends, Query
from typing import Optional
from datetime import datetime

from src.schemas.disaster_history import (
    DisasterHistoryListResponse,
    DisasterHistoryFilter,
)
from src.services.disaster_history_service import DisasterHistoryService
from src.core.auth import verify_api_key

router = APIRouter(prefix="/api/past", tags=["Past Events (Spring Boot Compatibility)"])


@router.get(
    "",
    response_model=DisasterHistoryListResponse,
    responses={
        200: {"description": "과거 재난 이력 조회 성공"},
        401: {"description": "API Key 인증 실패"},
        422: {"description": "입력 데이터 검증 실패"}
    }
)
async def get_past_events(
    year: Optional[int] = Query(None, description="연도로 필터링"),
    disaster_type: Optional[str] = Query(None, alias="disasterType", description="재난 유형 (강풍/풍랑/호우/대설/건조/지진해일/한파/태풍/황사/폭염)"),
    severity: Optional[str] = Query(None, description="강도 (주의보/경보)"),
    region: Optional[str] = Query(None, description="지역명으로 필터링"),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    api_key: str = Depends(verify_api_key),
):
    """
    과거 재난 이력 조회 (긴급재난문자 데이터)

    api_emergency_messages 테이블에서 긴급재난문자 이력을 조회합니다.

    Args:
        year: 연도 필터 (선택)
        disasterType: 재난 유형 (선택) - 9종: 강풍, 풍랑, 호우, 대설, 건조, 지진해일, 한파, 태풍, 황사, 폭염
        severity: 강도 (선택) - 주의보, 경보
        region: 지역명 (선택)
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
        disaster_type=disaster_type,
        severity=severity,
        region=region,
        start_date=start_date,
        end_date=end_date,
        limit=limit,
        offset=offset,
    )

    result = await service.get_disaster_history(filters)
    return result
