from fastapi import APIRouter, Depends, HTTPException, Query
from uuid import UUID
from typing import Optional
from datetime import datetime

from src.schemas.disaster_history import (
    DisasterHistoryRecord,
    DisasterHistoryListResponse,
    DisasterHistoryFilter,
    DisasterStatistics,
    DisasterSeverity,
)
from src.schemas.common import HazardType
from src.services.disaster_history_service import DisasterHistoryService
from src.core.auth import verify_api_key

router = APIRouter(prefix="/api/disaster-history", tags=["Disaster History"])


@router.get("", response_model=DisasterHistoryListResponse)
async def get_disaster_history(
    site_id: Optional[UUID] = Query(None, alias="siteId", description="사업장 ID로 필터링"),
    disaster_type: Optional[HazardType] = Query(None, alias="disasterType", description="재해 유형으로 필터링"),
    severity: Optional[DisasterSeverity] = Query(None, description="심각도로 필터링"),
    start_date: Optional[datetime] = Query(None, alias="startDate", description="시작 날짜 (이후 발생)"),
    end_date: Optional[datetime] = Query(None, alias="endDate", description="종료 날짜 (이전 발생)"),
    limit: int = Query(100, description="조회 개수 제한", ge=1, le=1000),
    offset: int = Query(0, description="조회 시작 위치", ge=0),
    api_key: str = Depends(verify_api_key),
):
    """
    재해이력 목록 조회

    - **site_id**: 사업장 ID로 필터링 (선택)
    - **disaster_type**: 재해 유형으로 필터링 (선택)
    - **severity**: 심각도로 필터링 (선택)
    - **start_date**: 시작 날짜 이후 발생한 재해만 조회 (선택)
    - **end_date**: 종료 날짜 이전 발생한 재해만 조회 (선택)
    - **limit**: 한 번에 조회할 개수 (기본: 100, 최대: 1000)
    - **offset**: 조회 시작 위치 (페이징용, 기본: 0)

    Returns:
        전체 재해이력 수와 필터링된 재해이력 목록
    """
    service = DisasterHistoryService()

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


@router.get("/detail", response_model=DisasterHistoryRecord)
async def get_disaster_by_id(
    disaster_id: UUID = Query(..., alias="disasterId"),
    api_key: str = Depends(verify_api_key),
):
    """
    특정 재해이력 상세 조회 - query parameters 사용

    - **disaster_id**: 재해이력 ID

    Returns:
        재해이력 상세 정보
    """
    service = DisasterHistoryService()
    result = await service.get_disaster_by_id(disaster_id)

    if not result:
        raise HTTPException(status_code=404, detail="Disaster history not found")

    return result


@router.get("/statistics/summary", response_model=DisasterStatistics)
async def get_disaster_statistics(
    site_id: Optional[UUID] = Query(None, alias="siteId", description="사업장 ID (전체 통계는 생략)"),
    api_key: str = Depends(verify_api_key),
):
    """
    재해 통계 조회

    - **site_id**: 사업장 ID로 필터링 (None이면 전체 통계)

    Returns:
        재해 통계 (총 건수, 총 피해액, 인명피해, 유형별/심각도별 통계)
    """
    service = DisasterHistoryService()
    result = await service.get_disaster_statistics(site_id)
    return result
