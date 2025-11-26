from fastapi import APIRouter, Depends, HTTPException, Query
from uuid import UUID
from typing import Optional

from src.schemas.analysis import (
    StartAnalysisRequest,
    AnalysisJobStatus,
    PhysicalRiskScoreResponse,
    PastEventsResponse,
    FinancialImpactResponse,
    VulnerabilityResponse,
    AnalysisTotalResponse,
)
from src.services.analysis_service import AnalysisService
from src.core.auth import verify_api_key

router = APIRouter(prefix="/api/sites", tags=["Analysis"])


@router.post("/{site_id}/analysis/start", response_model=AnalysisJobStatus, status_code=200)
async def start_analysis(
    site_id: UUID,
    request: StartAnalysisRequest,
    api_key: str = Depends(verify_api_key),
):
    """Spring Boot API 호환 - AI 리스크 분석 시작"""
    service = AnalysisService()
    return await service.start_analysis(site_id, request)


@router.get("/{site_id}/analysis/status/{job_id}", response_model=AnalysisJobStatus)
async def get_analysis_status(
    site_id: UUID,
    job_id: UUID,
    api_key: str = Depends(verify_api_key),
):
    """Spring Boot API 호환 - 분석 작업 상태 조회"""
    service = AnalysisService()
    result = await service.get_job_status(site_id, job_id)
    if not result:
        raise HTTPException(status_code=404, detail="Job not found")
    return result


@router.get("/{site_id}/analysis/physical-risk-scores", response_model=PhysicalRiskScoreResponse)
async def get_physical_risk_scores(
    site_id: UUID,
    hazard_type: Optional[str] = Query(None, alias="hazardType"),
    api_key: str = Depends(verify_api_key),
):
    """Spring Boot API 호환 - 시나리오별 물리적 리스크 점수 조회"""
    service = AnalysisService()
    result = await service.get_physical_risk_scores(site_id, hazard_type)
    if not result:
        raise HTTPException(status_code=404, detail="Analysis not found")
    return result


@router.get("/{site_id}/analysis/past-events", response_model=PastEventsResponse)
async def get_past_events(
    site_id: UUID,
    api_key: str = Depends(verify_api_key),
):
    """Spring Boot API 호환 - 과거 재난 이력 조회"""
    service = AnalysisService()
    result = await service.get_past_events(site_id)
    if not result:
        raise HTTPException(status_code=404, detail="Analysis not found")
    return result


@router.get("/{site_id}/analysis/financial-impacts", response_model=FinancialImpactResponse)
async def get_financial_impacts(
    site_id: UUID,
    api_key: str = Depends(verify_api_key),
):
    """Spring Boot API 호환 - 시나리오별 재무 영향(AAL) 조회"""
    service = AnalysisService()
    result = await service.get_financial_impacts(site_id)
    if not result:
        raise HTTPException(status_code=404, detail="Analysis not found")
    return result


@router.get("/{site_id}/analysis/vulnerability", response_model=VulnerabilityResponse)
async def get_vulnerability(
    site_id: UUID,
    api_key: str = Depends(verify_api_key),
):
    """Spring Boot API 호환 - 취약성 분석"""
    service = AnalysisService()
    result = await service.get_vulnerability(site_id)
    if not result:
        raise HTTPException(status_code=404, detail="Analysis not found")
    return result


@router.get("/{site_id}/analysis/total", response_model=AnalysisTotalResponse)
async def get_total_analysis(
    site_id: UUID,
    hazard_type: str = Query(..., alias="hazardType"),
    api_key: str = Depends(verify_api_key),
):
    """Spring Boot API 호환 - 특정 Hazard 기준 통합 분석 결과"""
    service = AnalysisService()
    result = await service.get_total_analysis(site_id, hazard_type)
    if not result:
        raise HTTPException(status_code=404, detail="Analysis not found")
    return result
