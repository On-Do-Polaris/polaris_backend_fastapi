from fastapi import APIRouter, Depends, HTTPException, Query
from uuid import UUID

router = APIRouter(prefix="/api/recommendation", tags=["Site Recommendation (DEPRECATED)"])


@router.post(
    "/batch/start",
    status_code=410,
    responses={
        410: {
            "description": "엔드포인트가 영구적으로 제거됨",
            "content": {
                "application/json": {
                    "example": {
                        "error": "Endpoint Permanently Removed",
                        "message": "배치 추천 API는 2025-12-10부로 제거되었습니다.",
                        "deprecated_at": "2025-12-10"
                    }
                }
            }
        }
    }
)
async def start_batch_recommendation_deprecated():
    """
    배치 추천 API - 영구 제거됨 (2025-12-10)

    이 엔드포인트는 더 이상 지원되지 않습니다.
    새로운 통합 리스크 평가 API를 사용해주세요.
    """
    raise HTTPException(
        status_code=410,
        detail={
            "error": "Endpoint Permanently Removed",
            "message": "배치 추천 API는 2025-12-10부로 제거되었습니다.",
            "reason": "ModelOps API가 통합 리스크 평가 엔드포인트로 재설계되었습니다.",
            "migration": {
                "old_endpoint": "POST /api/recommendation/batch/start",
                "new_endpoint": "POST /api/v1/risk-assessment/calculate",
                "documentation": "https://docs.example.com/migration-guide",
                "changes": [
                    "배치 처리 방식에서 단일 위치 기반 계산으로 변경",
                    "H×E×V×AAL을 단일 API 호출로 통합",
                    "WebSocket 실시간 진행상황 지원 추가",
                    "격자 기반 추천 대신 사용자 지정 위치 평가"
                ]
            },
            "contact": "support@example.com",
            "deprecated_at": "2025-12-10"
        }
    )


@router.get(
    "/batch/{batch_id}/progress",
    status_code=410,
    responses={
        410: {
            "description": "엔드포인트가 영구적으로 제거됨",
            "content": {
                "application/json": {
                    "example": {
                        "error": "Endpoint Permanently Removed",
                        "message": "배치 진행 상태 조회 API는 2025-12-10부로 제거되었습니다.",
                        "deprecated_at": "2025-12-10"
                    }
                }
            }
        }
    }
)
async def get_batch_progress_deprecated(batch_id: str):
    """
    배치 진행 상태 조회 - 영구 제거됨 (2025-12-10)

    이 엔드포인트는 더 이상 지원되지 않습니다.
    """
    raise HTTPException(
        status_code=410,
        detail={
            "error": "Endpoint Permanently Removed",
            "message": "배치 진행 상태 조회 API는 2025-12-10부로 제거되었습니다.",
            "migration": {
                "old_endpoint": "GET /api/recommendation/batch/{batch_id}/progress",
                "new_endpoint": "GET /api/v1/risk-assessment/status?request_id=...",
                "alternative": "WebSocket /api/v1/risk-assessment/ws/{request_id}"
            }
        }
    )


@router.get(
    "/batch/{batch_id}/result",
    status_code=410,
    responses={
        410: {
            "description": "엔드포인트가 영구적으로 제거됨",
            "content": {
                "application/json": {
                    "example": {
                        "error": "Endpoint Permanently Removed",
                        "message": "배치 결과 조회 API는 2025-12-10부로 제거되었습니다.",
                        "deprecated_at": "2025-12-10"
                    }
                }
            }
        }
    }
)
async def get_batch_result_deprecated(batch_id: str):
    """
    배치 결과 조회 - 영구 제거됨 (2025-12-10)

    이 엔드포인트는 더 이상 지원되지 않습니다.
    """
    raise HTTPException(
        status_code=410,
        detail={
            "error": "Endpoint Permanently Removed",
            "message": "배치 결과 조회 API는 2025-12-10부로 제거되었습니다.",
            "migration": {
                "old_endpoint": "GET /api/recommendation/batch/{batch_id}/result",
                "new_endpoint": "GET /api/v1/risk-assessment/results?latitude=...&longitude=..."
            }
        }
    )


@router.delete(
    "/batch/{batch_id}",
    status_code=410,
    responses={
        410: {
            "description": "엔드포인트가 영구적으로 제거됨",
            "content": {
                "application/json": {
                    "example": {
                        "error": "Endpoint Permanently Removed",
                        "message": "배치 작업 취소 API는 2025-12-10부로 제거되었습니다.",
                        "deprecated_at": "2025-12-10"
                    }
                }
            }
        }
    }
)
async def cancel_batch_job_deprecated(batch_id: str):
    """
    배치 작업 취소 - 영구 제거됨 (2025-12-10)

    이 엔드포인트는 더 이상 지원되지 않습니다.
    """
    raise HTTPException(
        status_code=410,
        detail={
            "error": "Endpoint Permanently Removed",
            "message": "배치 작업 취소 API는 2025-12-10부로 제거되었습니다.",
            "migration": {
                "note": "새로운 통합 리스크 평가 API는 단일 계산 방식으로 작동하며 취소 기능이 필요하지 않습니다."
            }
        }
    )
