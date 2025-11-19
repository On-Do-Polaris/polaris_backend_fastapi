from fastapi import APIRouter, Depends, HTTPException, Query
from uuid import UUID
from typing import Optional

from src.schemas.analysis import (
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
from src.schemas.common import HazardType, TimeScale
from src.services.analysis_service import AnalysisService
from src.core.auth import verify_api_key

router = APIRouter(prefix="/api/v1/analysis", tags=["Analysis"])


@router.post("/start", response_model=AnalysisJobStatus, status_code=202)
async def start_analysis(
    request: StartAnalysisRequest,
    api_key: str = Depends(verify_api_key),
):
    """AI 리스크 분석 시작"""
    service = AnalysisService()
    return await service.start_analysis(request)


@router.get("/status/{job_id}", response_model=AnalysisJobStatus)
async def get_analysis_status(
    job_id: UUID,
    api_key: str = Depends(verify_api_key),
):
    """분석 작업 상태 조회"""
    service = AnalysisService()
    result = await service.get_job_status(job_id)
    if not result:
        raise HTTPException(status_code=404, detail="Job not found")
    return result


@router.get("/{site_id}/overview", response_model=AnalysisOverviewResponse)
async def get_analysis_overview(
    site_id: UUID,
    api_key: str = Depends(verify_api_key),
):
    """사업장 리스크 분석 개요 조회"""
    service = AnalysisService()
    result = await service.get_overview(site_id)
    if not result:
        raise HTTPException(status_code=404, detail="Analysis not found")
    return result


@router.get("/{site_id}/physical-risk-scores", response_model=PhysicalRiskScoreResponse)
async def get_physical_risk_scores(
    site_id: UUID,
    hazard_type: Optional[HazardType] = Query(None, alias="hazardType"),
    api_key: str = Depends(verify_api_key),
):
    """Hazard별 물리적 리스크 점수 조회"""
    service = AnalysisService()
    result = await service.get_physical_risk_scores(site_id, hazard_type)
    if not result:
        raise HTTPException(status_code=404, detail="Analysis not found")
    return result


@router.get("/{site_id}/past-events", response_model=PastEventsResponse)
async def get_past_events(
    site_id: UUID,
    hazard_type: Optional[HazardType] = Query(None, alias="hazardType"),
    start_year: Optional[int] = Query(None, alias="startYear"),
    end_year: Optional[int] = Query(None, alias="endYear"),
    api_key: str = Depends(verify_api_key),
):
    """과거 재난 이력 조회"""
    service = AnalysisService()
    result = await service.get_past_events(site_id, hazard_type, start_year, end_year)
    if not result:
        raise HTTPException(status_code=404, detail="Analysis not found")
    return result


@router.get("/{site_id}/ssp", response_model=SSPProjectionResponse)
async def get_ssp_projection(
    site_id: UUID,
    hazard_type: Optional[HazardType] = Query(None, alias="hazardType"),
    time_scale: Optional[TimeScale] = Query(None, alias="timeScale"),
    api_key: str = Depends(verify_api_key),
):
    """SSP 시나리오별 리스크 전망"""
    service = AnalysisService()
    result = await service.get_ssp_projection(site_id, hazard_type, time_scale)
    if not result:
        raise HTTPException(status_code=404, detail="Analysis not found")
    return result


@router.get("/{site_id}/financial-impacts", response_model=FinancialImpactResponse)
async def get_financial_impacts(
    site_id: UUID,
    hazard_type: Optional[HazardType] = Query(None, alias="hazardType"),
    api_key: str = Depends(verify_api_key),
):
    """Hazard별 재무 영향(AAL) 조회"""
    service = AnalysisService()
    result = await service.get_financial_impacts(site_id, hazard_type)
    if not result:
        raise HTTPException(status_code=404, detail="Analysis not found")
    return result


@router.get("/{site_id}/vulnerability", response_model=VulnerabilityResponse)
async def get_vulnerability(
    site_id: UUID,
    api_key: str = Depends(verify_api_key),
):
    """취약성 분석"""
    service = AnalysisService()
    result = await service.get_vulnerability(site_id)
    if not result:
        raise HTTPException(status_code=404, detail="Analysis not found")
    return result


@router.get("/{site_id}/total", response_model=AnalysisTotalResponse)
async def get_total_analysis(
    site_id: UUID,
    hazard_type: HazardType = Query(..., alias="hazardType"),
    time_scale: Optional[TimeScale] = Query(None, alias="timeScale"),
    api_key: str = Depends(verify_api_key),
):
    """특정 Hazard 기준 통합 분석 결과"""
    service = AnalysisService()
    result = await service.get_total_analysis(site_id, hazard_type, time_scale)
    if not result:
        raise HTTPException(status_code=404, detail="Analysis not found")
    return result
