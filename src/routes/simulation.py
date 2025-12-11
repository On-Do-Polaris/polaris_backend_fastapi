from fastapi import APIRouter, Depends, Query

from src.schemas.simulation import (
    RelocationSimulationRequest,
    RelocationSimulationResponse,
    ClimateSimulationRequest,
    ClimateSimulationResponse,
)
from src.services.simulation_service import SimulationService
from src.core.auth import verify_api_key

router = APIRouter(prefix="/api/simulation", tags=["Simulation"])


@router.post("/relocation/compare", response_model=RelocationSimulationResponse)
async def compare_relocation(
    request: RelocationSimulationRequest,
    api_key: str = Depends(verify_api_key),
):
    """Spring Boot API 호환 - 사업장 이전 시뮬레이션 (비교)"""
    service = SimulationService()
    return await service.compare_relocation(request)


@router.post("/climate", response_model=ClimateSimulationResponse)
async def run_climate_simulation(
    request: ClimateSimulationRequest,
    api_key: str = Depends(verify_api_key),
):
    """Spring Boot API 호환 - 기후 시뮬레이션"""
    service = SimulationService()
    return await service.run_climate_simulation(request)


@router.get("/location/recommendation")
async def get_location_recommendation(
    site_id: str = Query(..., alias="siteId"),
    api_key: str = Depends(verify_api_key),
):
    """
    이전 후보지 추천 (Spring Boot 호환 - STUB)

    현재는 빈 데이터를 반환합니다.
    향후 실제 추천 로직 구현 필요.

    Args:
        siteId: 사업장 ID

    Returns:
        추천 후보지 목록 (현재는 빈 배열)
    """
    return {
        "siteId": site_id,
        "recommendations": [],
        "status": "not_implemented",
        "message": "Location recommendation feature is under development."
    }
