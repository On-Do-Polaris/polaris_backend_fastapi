from fastapi import APIRouter, Depends
from uuid import UUID

from src.schemas.simulation import (
    RelocationSimulationRequest,
    RelocationSimulationResult,
    ClimateSimulationRequest,
    ClimateSimulationResponse,
)
from src.services.simulation_service import SimulationService
from src.core.auth import verify_api_key

router = APIRouter(prefix="/api/v1/simulation", tags=["Simulation"])


@router.post("/relocation/compare", response_model=RelocationSimulationResult)
async def compare_relocation(
    request: RelocationSimulationRequest,
    api_key: str = Depends(verify_api_key),
):
    """사업장 이전 시뮬레이션 (비교)"""
    service = SimulationService()
    return await service.compare_relocation(request)


@router.post("/climate", response_model=ClimateSimulationResponse)
async def simulate_climate(
    request: ClimateSimulationRequest,
    api_key: str = Depends(verify_api_key),
):
    """기후 시뮬레이션"""
    service = SimulationService()
    return await service.simulate_climate(request)
