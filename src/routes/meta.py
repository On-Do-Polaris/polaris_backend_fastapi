from fastapi import APIRouter, Depends, Query
from typing import Optional
from datetime import datetime

from src.schemas.meta import HazardTypeInfo, HealthCheckResponse, DatabaseHealthCheckResponse
from src.services.meta_service import MetaService
from src.core.auth import verify_api_key

router = APIRouter(prefix="/api/v1", tags=["Meta"])


@router.get(
    "/meta/hazards",
    response_model=list[HazardTypeInfo],
    responses={
        200: {"description": "위험 유형 목록 조회 성공"},
        401: {"description": "API Key 인증 실패"}
    }
)
async def get_hazards(
    category: Optional[str] = Query(None, enum=["temperature", "water", "wind", "other"]),
    api_key: str = Depends(verify_api_key),
):
    """지원하는 기후 리스크(위험요인) 목록"""
    service = MetaService()
    return await service.get_hazards(category)


@router.get(
    "/health",
    response_model=HealthCheckResponse,
    responses={
        200: {"description": "헬스체크 성공"}
    }
)
async def health_check():
    """헬스체크"""
    service = MetaService()
    return await service.health_check()


@router.get(
    "/health/database",
    response_model=DatabaseHealthCheckResponse,
    responses={
        200: {"description": "데이터베이스 헬스체크 성공"}
    }
)
async def database_health_check():
    """데이터베이스 헬스체크 - batch_jobs 테이블 접근 테스트"""
    service = MetaService()
    return await service.database_health_check()
