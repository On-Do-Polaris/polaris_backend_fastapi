from fastapi import APIRouter, Depends, Query

from src.schemas.simulation import (
    RelocationSimulationRequest,
    RelocationSimulationResponse,
    ClimateSimulationRequest,
    ClimateSimulationResponse,
    LocationRecommendationResponse,
)
from src.services.simulation_service import SimulationService
from src.core.auth import verify_api_key

router = APIRouter(prefix="/api/simulation", tags=["Simulation"])


@router.post("/relocation/compare", response_model=RelocationSimulationResponse)
async def compare_relocation(
    request: RelocationSimulationRequest,
    api_key: str = Depends(verify_api_key),
):
    """
    Spring Boot API 호환 - 사업장 이전 시뮬레이션 (비교)

    candidate_sites 테이블에서 좌표로 후보지를 조회하여 반환.
    DB에 없으면 ai_agent로 실시간 분석 수행.
    """
    service = SimulationService()
    return await service.compare_relocation_with_db(request)


@router.post("/climate", response_model=ClimateSimulationResponse)
async def run_climate_simulation(
    request: ClimateSimulationRequest,
    api_key: str = Depends(verify_api_key),
):
    """Spring Boot API 호환 - 기후 시뮬레이션"""
    service = SimulationService()
    return await service.run_climate_simulation(request)


@router.get("/location/recommendation", response_model=LocationRecommendationResponse)
async def get_location_recommendation(
    site_id: str = Query(..., alias="siteId"),
    api_key: str = Depends(verify_api_key),
):
    """
    이전 후보지 추천 (Spring Boot 호환)

    candidate_sites 테이블에서 종합 AAL이 가장 낮은 상위 3개의 후보지를 반환합니다.

    Args:
        siteId: 사업장 ID

    Returns:
        추천 후보지 상위 3개 (AAL 기준 오름차순)
    """
    service = SimulationService()
    return await service.get_location_recommendation(site_id)
