from uuid import UUID

from schemas.simulation import (
    RelocationCandidatesRequest,
    RelocationCandidatesResponse,
    RelocationSimulationRequest,
    RelocationSimulationResult,
    ClimateSimulationRequest,
    ClimateSimulationResponse,
)

# ai_agent를 호출하는 서비스
# from ai_agent import run_simulation_agent


class SimulationService:
    """시뮬레이션 서비스 - ai_agent를 사용하여 시뮬레이션 수행"""

    async def get_relocation_candidates(
        self, request: RelocationCandidatesRequest
    ) -> RelocationCandidatesResponse:
        """이전 후보지 추천"""
        # TODO: ai_agent를 사용하여 후보지 추천
        # result = await run_simulation_agent("relocation_candidates", request)
        pass

    async def compare_relocation(
        self, request: RelocationSimulationRequest
    ) -> RelocationSimulationResult:
        """이전 시뮬레이션 비교"""
        # TODO: ai_agent를 사용하여 비교 분석
        # result = await run_simulation_agent("relocation_compare", request)
        pass

    async def simulate_climate(
        self, request: ClimateSimulationRequest
    ) -> ClimateSimulationResponse:
        """기후 시뮬레이션"""
        # TODO: ai_agent를 사용하여 기후 시뮬레이션
        # result = await run_simulation_agent("climate", request)
        pass
