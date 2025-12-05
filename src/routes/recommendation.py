from fastapi import APIRouter, Depends, HTTPException
from uuid import UUID

from src.schemas.recommendation import (
    SiteRecommendationRequest,
    SiteRecommendationBatchResponse,
    BatchProgressResponse,
    SiteRecommendationResultResponse,
)
from src.services.recommendation_service import RecommendationService
from src.core.auth import verify_api_key

router = APIRouter(prefix="/api/recommendation", tags=["Site Recommendation"])


@router.post("/batch/start", response_model=SiteRecommendationBatchResponse, status_code=202)
async def start_batch_recommendation(
    request: SiteRecommendationRequest,
    api_key: str = Depends(verify_api_key),
):
    """
    후보지 추천 배치 작업 시작

    전체 격자에 대해 E, V, AAL을 계산하여 리스크가 가장 낮은 상위 N개 격자를 추천합니다.

    **처리 흐름**:
    1. ModelOps API에 배치 작업 요청
    2. 배치 작업 ID 반환 (202 Accepted)
    3. 클라이언트는 진행 상태 조회 API를 폴링
    4. 완료 후 결과 조회 API로 추천 후보지 목록 획득

    **예상 소요 시간**: 약 30분 (10,000개 격자 기준)
    """
    service = RecommendationService()
    return await service.start_batch_recommendation(request)


@router.get("/batch/{batch_id}/progress", response_model=BatchProgressResponse)
async def get_batch_progress(
    batch_id: UUID,
    api_key: str = Depends(verify_api_key),
):
    """
    배치 작업 진행 상태 조회

    **폴링 권장 간격**: 5초

    **진행률 예시**:
    - 10%: 1,000개 격자 완료
    - 30%: 3,000개 격자 완료
    - 50%: 5,000개 격자 완료
    - 70%: 7,000개 격자 완료
    - 90%: 9,000개 격자 완료
    - 100%: 전체 완료 (결과 조회 가능)
    """
    service = RecommendationService()
    result = await service.get_batch_progress(batch_id)

    if not result:
        raise HTTPException(status_code=404, detail="Batch job not found")

    return result


@router.get("/batch/{batch_id}/result", response_model=SiteRecommendationResultResponse)
async def get_batch_result(
    batch_id: UUID,
    api_key: str = Depends(verify_api_key),
):
    """
    배치 작업 완료 후 결과 조회

    **주의**: 배치 작업이 완료(100%)된 후에만 결과를 조회할 수 있습니다.

    **응답 내용**:
    - 추천 후보지 목록 (상위 N개, 요청 시 지정한 top_n 개수)
    - 격자별 H, E, V, AAL 점수
    - 종합 리스크 점수 (낮을수록 좋음)
    - 예상 손실액
    """
    service = RecommendationService()
    result = await service.get_batch_result(batch_id)

    if not result:
        raise HTTPException(
            status_code=404, detail="Batch job not found or not yet completed"
        )

    return result


@router.delete("/batch/{batch_id}", status_code=204)
async def cancel_batch_job(
    batch_id: UUID,
    api_key: str = Depends(verify_api_key),
):
    """
    배치 작업 취소

    **주의**: 이미 완료된 작업은 취소할 수 없습니다.
    """
    service = RecommendationService()
    success = await service.cancel_batch_job(batch_id)

    if not success:
        raise HTTPException(
            status_code=404, detail="Batch job not found or already completed"
        )

    return None
