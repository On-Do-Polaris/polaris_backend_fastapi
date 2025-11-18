from uuid import UUID, uuid4
from typing import Optional
from datetime import datetime

from schemas.analysis import (
    StartAnalysisRequest,
    AnalysisJobStatus,
    AnalysisOverviewResponse,
    PhysicalRiskScoreResponse,
    PastEventsResponse,
    SSPProjectionResponse,
    FinancialImpactResponse,
    VulnerabilityResponse,
    AnalysisTotalResponse,
)
from schemas.common import HazardType, TimeScale

# ai_agent를 호출하는 서비스
# from ai_agent import run_analysis_agent


class AnalysisService:
    """분석 서비스 - ai_agent를 호출하여 분석 수행"""

    async def start_analysis(self, request: StartAnalysisRequest) -> AnalysisJobStatus:
        """분석 작업 시작"""
        job_id = uuid4()

        # TODO: ai_agent 호출
        # result = await run_analysis_agent(request.site, request.hazard_types)

        return AnalysisJobStatus(
            jobId=job_id,
            siteId=request.site.id,
            status="queued",
            progress=0,
            startedAt=datetime.now(),
        )

    async def get_job_status(self, job_id: UUID) -> Optional[AnalysisJobStatus]:
        """작업 상태 조회"""
        # TODO: 작업 상태 조회 구현
        pass

    async def get_overview(self, site_id: UUID) -> Optional[AnalysisOverviewResponse]:
        """분석 개요 조회"""
        # TODO: ai_agent 결과에서 개요 조회
        pass

    async def get_physical_risk_scores(
        self, site_id: UUID, hazard_type: Optional[HazardType]
    ) -> Optional[PhysicalRiskScoreResponse]:
        """물리적 리스크 점수 조회"""
        # TODO: ai_agent 결과에서 물리적 리스크 점수 조회
        pass

    async def get_past_events(
        self,
        site_id: UUID,
        hazard_type: Optional[HazardType],
        start_year: Optional[int],
        end_year: Optional[int],
    ) -> Optional[PastEventsResponse]:
        """과거 이벤트 조회"""
        # TODO: ai_agent 결과에서 과거 이벤트 조회
        pass

    async def get_ssp_projection(
        self,
        site_id: UUID,
        hazard_type: Optional[HazardType],
        time_scale: Optional[TimeScale],
    ) -> Optional[SSPProjectionResponse]:
        """SSP 전망 조회"""
        # TODO: ai_agent 결과에서 SSP 전망 조회
        pass

    async def get_financial_impacts(
        self, site_id: UUID, hazard_type: Optional[HazardType]
    ) -> Optional[FinancialImpactResponse]:
        """재무 영향 조회"""
        # TODO: ai_agent 결과에서 재무 영향 조회
        pass

    async def get_vulnerability(self, site_id: UUID) -> Optional[VulnerabilityResponse]:
        """취약성 분석 조회"""
        # TODO: ai_agent 결과에서 취약성 분석 조회
        pass

    async def get_total_analysis(
        self,
        site_id: UUID,
        hazard_type: HazardType,
        time_scale: Optional[TimeScale],
    ) -> Optional[AnalysisTotalResponse]:
        """통합 분석 결과 조회"""
        # TODO: ai_agent 결과에서 통합 분석 조회
        pass
