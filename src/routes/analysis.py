from fastapi import APIRouter, Depends, HTTPException, Query, Request, BackgroundTasks
from uuid import UUID
from typing import Optional
from datetime import datetime
import logging

from src.schemas.analysis import (
    StartAnalysisRequest,
    # EnhanceAnalysisRequest,
    AnalysisJobStatus,
    PhysicalRiskScoreResponse,
    PastEventsResponse,
    FinancialImpactResponse,
    VulnerabilityResponse,
    AnalysisTotalResponse,
    AnalysisSummaryResponse,
)
from src.services.analysis_service import AnalysisService
from src.core.auth import verify_api_key

router = APIRouter(prefix="/api/analysis", tags=["Analysis"])
logger = logging.getLogger("api.routes.analysis")


def get_analysis_service():
    """Get the singleton AnalysisService instance from main app"""
    from main import analysis_service_instance
    if analysis_service_instance is None:
        raise HTTPException(status_code=503, detail="AnalysisService not initialized")
    return analysis_service_instance


@router.post("/start", response_model=AnalysisJobStatus, status_code=202) # 사용
async def start_analysis(
    request: StartAnalysisRequest,
    background_tasks: BackgroundTasks,
    api_key: str = Depends(verify_api_key),
    service = Depends(get_analysis_service),
):
    """
    AI 리스크 분석 시작 (비동기) - site.id는 request body에 포함

    즉시 202 Accepted를 반환하고 백그라운드에서 분석 실행
    """
    return await service.start_analysis_async(request.site.id, request, background_tasks)


# @router.get("/status", response_model=AnalysisJobStatus)
# async def get_analysis_status(
#     user_id: Optional[UUID] = Query(None, alias="userId"),
#     job_id: Optional[UUID] = Query(None, alias="jobId"),
#     api_key: str = Depends(verify_api_key),
#     service = Depends(get_analysis_service),
# ):
#     """
#     분석 작업 상태 조회 (Spring Boot 호환)

#     Args:
#         userId: 사용자 ID (최근 작업 조회)
#         jobId: 작업 ID (특정 작업 조회)

#     Returns:
#         AnalysisJobStatus: 작업 상태 정보
#     """
#     # jobId가 있으면 jobId로 조회
#     if job_id:
#         result = await service.get_job_status_by_id(job_id)
#     # userId가 있으면 userId로 최근 작업 조회
#     elif user_id:
#         result = await service.get_latest_job_status_by_user(user_id)
#     else:
#         raise HTTPException(status_code=400, detail="Either userId or jobId must be provided")

#     if not result:
#         raise HTTPException(status_code=404, detail="Analysis job not found")

#     return result


# @router.post("/enhance", response_model=AnalysisJobStatus, status_code=200)
# async def enhance_analysis(
#     body: EnhanceAnalysisRequest,
#     http_request: Request,
#     api_key: str = Depends(verify_api_key),
# ):
#     """
#     추가 데이터를 반영하여 분석 향상

#     기존 분석 결과(job_id)에 추가 데이터를 반영하여 Node 5 이후 재실행.
#     Node 1~4 (ModelOps 데이터)는 캐시 재사용하여 효율적으로 실행.
#     """
#     # request_id 추출
#     request_id = getattr(http_request.state, 'request_id', None)

#     # Get singleton service instance
#     from main import analysis_service_instance
#     if analysis_service_instance is None:
#         raise HTTPException(status_code=503, detail="AnalysisService not initialized")
#     service = analysis_service_instance

#     # additional_data 변환 (Pydantic 모델 → dict)
#     additional_data_dict = {
#         'raw_text': body.additional_data.raw_text,
#         'metadata': body.additional_data.metadata or {},
#         'building_info': body.additional_data.building_info,
#         'asset_info': body.additional_data.asset_info,
#         'power_usage': body.additional_data.power_usage,
#         'insurance': body.additional_data.insurance
#     }

#     # site_id는 body에서 추출 필요 - EnhanceAnalysisRequest에 추가 필요
#     # 임시로 job_id에서 조회하거나, body에 site_id 추가
#     return await service.enhance_analysis(
#         site_id=body.site_id,  # EnhanceAnalysisRequest에 추가 필요
#         job_id=body.job_id,
#         additional_data_dict=additional_data_dict,
#         request_id=request_id
#     )


@router.get("/status", response_model=AnalysisJobStatus) # 사용
async def get_analysis_status(
    user_id: UUID = Query(..., alias="userId"),
    job_id: Optional[UUID] = Query(None, alias="jobid"),
    api_key: str = Depends(verify_api_key),
    service = Depends(get_analysis_service),
):
    """
    분석 작업 상태 조회 (Spring Boot 호환)

    Args:
        userId: 사용자 ID (필수, Spring Boot 클라이언트 호환)
        jobid: 작업 ID (선택)

    Returns:
        AnalysisJobStatus: 작업 상태 정보
        - status: "queued" | "running" | "processing" | "completed" | "failed"
        - progress: 0-100
    """
    # userId로 가장 최근 분석 작업 조회 (jobid가 없는 경우)
    if job_id:
        result = await service.get_job_status_by_id(job_id)
    else:
        result = await service.get_latest_job_status_by_user(user_id)

    if not result:
        raise HTTPException(
            status_code=404,
            detail=f"No analysis job found for userId: {user_id}"
        )
    return result


@router.get("/physical-risk-scores", response_model=PhysicalRiskScoreResponse) # 사용
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


# @router.get("/past-events", response_model=PastEventsResponse) # 사용
# async def get_past_events(
#     site_id: UUID = Query(..., alias="siteId"),
#     api_key: str = Depends(verify_api_key),
#     service = Depends(get_analysis_service),
# ):
#     """과거 재난 이력 조회 - query parameters 사용"""
#     result = await service.get_past_events(site_id)
#     if not result:
#         raise HTTPException(status_code=404, detail="Analysis not found")
#     return result


@router.get("/financial-impacts", response_model=FinancialImpactResponse) # 사용
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


@router.get("/vulnerability", response_model=VulnerabilityResponse) # 사용
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


# @router.get("/total", response_model=AnalysisTotalResponse) # 사용
# async def get_total_analysis(
#     site_id: UUID = Query(..., alias="siteId"),
#     hazard_type: str = Query(..., alias="hazardType"),
#     api_key: str = Depends(verify_api_key),
#     service = Depends(get_analysis_service),
# ):
#     """특정 Hazard 기준 통합 분석 결과 - query parameters 사용"""
#     result = await service.get_total_analysis(site_id, hazard_type)
#     if not result:
#         raise HTTPException(status_code=404, detail="Analysis not found")
#     return result


@router.get("/summary", response_model=AnalysisSummaryResponse) # 사용
async def get_analysis_summary(
    site_id: UUID = Query(..., alias="siteId"),
    latitude: float = Query(..., description="사업장 위도"),
    longitude: float = Query(..., description="사업장 경도"),
    api_key: str = Depends(verify_api_key),
    service: AnalysisService = Depends(get_analysis_service),
):
    """
    분석 요약 조회 - 2040년 SSP2-4.5 시나리오 기준

    9대 물리적 리스크 점수 및 AAL 요약을 반환합니다.

    - **siteId**: 사업장 ID
    - **latitude**: 사업장 위도
    - **longitude**: 사업장 경도
    """
    try:
        logger.info(f"GET /summary called for siteId={site_id}, lat={latitude}, lon={longitude}")
        result = await service.get_analysis_summary(site_id, latitude, longitude)
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"분석 요약 조회 실패: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


# @router.get("/ssp", response_model=PhysicalRiskScoreResponse) # 사용
# async def get_ssp_projection(
#     site_id: UUID = Query(..., alias="siteId"),
#     hazard_type: Optional[str] = Query(None, alias="hazardType"),
#     api_key: str = Depends(verify_api_key),
#     service = Depends(get_analysis_service),
# ):
#     """
#     SSP 시나리오별 리스크 전망 (Spring Boot 호환)

#     physical-risk-scores와 동일한 데이터를 반환합니다.
#     """
#     result = await service.get_physical_risk_scores(site_id, hazard_type)
#     if not result:
#         raise HTTPException(status_code=404, detail="Analysis not found")
#     return result


@router.post("/modelops/recommendation-completed", status_code=200) # ModelOps 전용
async def mark_recommendation_completed(
    user_id: UUID = Query(..., alias="userId"),
    api_key: str = Depends(verify_api_key),
    service = Depends(get_analysis_service),
):
    """
    ModelOps 서버에서 후보지 추천 완료 시 호출하는 엔드포인트

    Args:
        userId: 사용자 ID

    Returns:
        200 OK
    """
    await service.mark_modelops_recommendation_completed(user_id)
    return {"status": "success", "message": f"Recommendation completed for user {user_id}"}
