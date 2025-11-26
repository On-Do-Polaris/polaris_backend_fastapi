from fastapi import APIRouter, Depends

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
