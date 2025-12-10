from fastapi import APIRouter, Depends, HTTPException, Query, Request
from uuid import UUID
from typing import Optional
import logging

from src.schemas.analysis import (
    StartAnalysisRequest,
    EnhanceAnalysisRequest,
    AnalysisJobStatus,
    PhysicalRiskScoreResponse,
    PastEventsResponse,
    FinancialImpactResponse,
    VulnerabilityResponse,
    AnalysisTotalResponse,
)
from src.core.auth import verify_api_key

router = APIRouter(prefix="/api/analysis", tags=["Analysis"])
logger = logging.getLogger("api.routes.analysis")


def get_analysis_service():
    """Get the singleton AnalysisService instance from main app"""
    from main import analysis_service_instance
    if analysis_service_instance is None:
        raise HTTPException(status_code=503, detail="AnalysisService not initialized")
    return analysis_service_instance


@router.post("/start", response_model=AnalysisJobStatus, status_code=200)
async def start_analysis(
    request: StartAnalysisRequest,
    api_key: str = Depends(verify_api_key),
    service = Depends(get_analysis_service),
):
    """AI 리스크 분석 시작 - site.id는 request body에 포함"""
    return await service.start_analysis(request.site.id, request)


@router.post("/enhance", response_model=AnalysisJobStatus, status_code=200)
async def enhance_analysis(
    body: EnhanceAnalysisRequest,
    http_request: Request,
    api_key: str = Depends(verify_api_key),
):
    """
    추가 데이터를 반영하여 분석 향상

    기존 분석 결과(job_id)에 추가 데이터를 반영하여 Node 5 이후 재실행.
    Node 1~4 (ModelOps 데이터)는 캐시 재사용하여 효율적으로 실행.
    """
    # request_id 추출
    request_id = getattr(http_request.state, 'request_id', None)

    # Get singleton service instance
    from main import analysis_service_instance
    if analysis_service_instance is None:
        raise HTTPException(status_code=503, detail="AnalysisService not initialized")
    service = analysis_service_instance

    # additional_data 변환 (Pydantic 모델 → dict)
    additional_data_dict = {
        'raw_text': body.additional_data.raw_text,
        'metadata': body.additional_data.metadata or {},
        'building_info': body.additional_data.building_info,
        'asset_info': body.additional_data.asset_info,
        'power_usage': body.additional_data.power_usage,
        'insurance': body.additional_data.insurance
    }

    # site_id는 body에서 추출 필요 - EnhanceAnalysisRequest에 추가 필요
    # 임시로 job_id에서 조회하거나, body에 site_id 추가
    return await service.enhance_analysis(
        site_id=body.site_id,  # EnhanceAnalysisRequest에 추가 필요
        job_id=body.job_id,
        additional_data_dict=additional_data_dict,
        request_id=request_id
    )


@router.get("/status", response_model=AnalysisJobStatus)
async def get_analysis_status(
    site_id: UUID = Query(..., alias="siteId"),
    job_id: UUID = Query(..., alias="jobId"),
    api_key: str = Depends(verify_api_key),
    service = Depends(get_analysis_service),
):
    """분석 작업 상태 조회 - query parameters 사용"""
    result = await service.get_job_status(site_id, job_id)
    if not result:
        raise HTTPException(status_code=404, detail="Job not found")
    return result


@router.get("/physical-risk-scores", response_model=PhysicalRiskScoreResponse)
async def get_physical_risk_scores(
    site_id: UUID = Query(..., alias="siteId"),
    hazard_type: Optional[str] = Query(None, alias="hazardType"),
    api_key: str = Depends(verify_api_key),
    service = Depends(get_analysis_service),
):
    """시나리오별 물리적 리스크 점수 조회 - query parameters 사용"""
    result = await service.get_physical_risk_scores(site_id, hazard_type)
    if not result:
        raise HTTPException(status_code=404, detail="Analysis not found")
    return result


@router.get("/past-events", response_model=PastEventsResponse)
async def get_past_events(
    site_id: UUID = Query(..., alias="siteId"),
    api_key: str = Depends(verify_api_key),
    service = Depends(get_analysis_service),
):
    """과거 재난 이력 조회 - query parameters 사용"""
    result = await service.get_past_events(site_id)
    if not result:
        raise HTTPException(status_code=404, detail="Analysis not found")
    return result


@router.get("/financial-impacts", response_model=FinancialImpactResponse)
async def get_financial_impacts(
    site_id: UUID = Query(..., alias="siteId"),
    api_key: str = Depends(verify_api_key),
    service = Depends(get_analysis_service),
):
    """시나리오별 재무 영향(AAL) 조회 - query parameters 사용"""
    result = await service.get_financial_impacts(site_id)
    if not result:
        raise HTTPException(status_code=404, detail="Analysis not found")
    return result


@router.get("/vulnerability", response_model=VulnerabilityResponse)
async def get_vulnerability(
    site_id: UUID = Query(..., alias="siteId"),
    api_key: str = Depends(verify_api_key),
    service = Depends(get_analysis_service),
):
    """취약성 분석 - query parameters 사용"""
    result = await service.get_vulnerability(site_id)
    if not result:
        raise HTTPException(status_code=404, detail="Analysis not found")
    return result


@router.get("/total", response_model=AnalysisTotalResponse)
async def get_total_analysis(
    site_id: UUID = Query(..., alias="siteId"),
    hazard_type: str = Query(..., alias="hazardType"),
    api_key: str = Depends(verify_api_key),
    service = Depends(get_analysis_service),
):
    """특정 Hazard 기준 통합 분석 결과 - query parameters 사용"""
    result = await service.get_total_analysis(site_id, hazard_type)
    if not result:
        raise HTTPException(status_code=404, detail="Analysis not found")
    return result
