from uuid import UUID, uuid4
from typing import Optional
from datetime import datetime, timedelta
import asyncio

from src.schemas.recommendation import (
    SiteRecommendationRequest,
    SiteRecommendationBatchResponse,
    BatchProgressResponse,
    SiteRecommendationResultResponse,
    RecommendedSite,
    BatchStatus,
)


class RecommendationService:
    """후보지 추천 배치 작업 서비스 - ModelOps API 연동"""

    def __init__(self):
        """서비스 초기화"""
        self._batch_jobs = {}  # batch_id별 작업 상태 캐시 (실제로는 DB 또는 Redis에 저장)
        self._batch_results = {}  # batch_id별 결과 캐시

    async def start_batch_recommendation(
        self, request: SiteRecommendationRequest
    ) -> SiteRecommendationBatchResponse:
        """
        후보지 추천 배치 작업 시작

        전체 격자에 대해 E, V, AAL을 계산하여 리스크가 가장 낮은 상위 N개 격자를 추천

        Args:
            request: 배치 작업 요청

        Returns:
            배치 작업 시작 응답 (batch_id, status_url)
        """
        batch_id = uuid4()

        # TODO: ModelOps API에 배치 작업 요청
        # POST /api/v1/batch/recommend-sites
        # {
        #   "scenario_id": request.scenario_id,
        #   "building_info": request.building_info,
        #   "asset_info": request.asset_info,
        #   "top_n": request.top_n,
        #   "additional_data": request.additional_data
        # }

        # 배치 작업 상태 초기화
        self._batch_jobs[batch_id] = {
            "status": BatchStatus.QUEUED,
            "progress_percentage": 0,
            "processed_grids": 0,
            "total_grids": 10000,  # TODO: ModelOps에서 반환받을 값
            "started_at": datetime.now(),
            "estimated_completion": datetime.now() + timedelta(minutes=30),
            "request": request,
        }

        # 비동기 배치 작업 시작 (백그라운드)
        asyncio.create_task(self._process_batch_job(batch_id))

        return SiteRecommendationBatchResponse(
            batch_id=batch_id,
            status=BatchStatus.QUEUED,
            estimated_duration_minutes=30,
            status_url=f"/api/recommendation/batch/{batch_id}/progress",
            created_at=datetime.now(),
        )

    async def get_batch_progress(self, batch_id: UUID) -> Optional[BatchProgressResponse]:
        """
        배치 작업 진행 상태 조회

        Args:
            batch_id: 배치 작업 ID

        Returns:
            진행 상태 응답 (progress_percentage, processed_grids 등)
        """
        job = self._batch_jobs.get(batch_id)

        if not job:
            return None

        # TODO: ModelOps API에서 진행 상태 조회
        # GET /api/v1/batch/{batch_id}/progress
        # Response: { "progress": 45, "processed": 4500, "total": 10000, "status": "processing" }

        return BatchProgressResponse(
            batch_id=batch_id,
            status=job["status"],
            progress_percentage=job["progress_percentage"],
            processed_grids=job["processed_grids"],
            total_grids=job["total_grids"],
            started_at=job["started_at"],
            estimated_completion=job.get("estimated_completion"),
            completed_at=job.get("completed_at"),
            error_message=job.get("error_message"),
        )

    async def get_batch_result(self, batch_id: UUID) -> Optional[SiteRecommendationResultResponse]:
        """
        배치 작업 완료 후 결과 조회

        Args:
            batch_id: 배치 작업 ID

        Returns:
            추천 후보지 목록 (상위 N개)
        """
        job = self._batch_jobs.get(batch_id)

        if not job or job["status"] != BatchStatus.COMPLETED:
            return None

        result = self._batch_results.get(batch_id)

        if not result:
            return None

        # TODO: ModelOps API에서 결과 조회
        # GET /api/v1/batch/{batch_id}/results
        # Response: { "recommended_sites": [...], "total_analyzed": 10000 }

        return result

    async def _process_batch_job(self, batch_id: UUID):
        """
        배치 작업 처리 (백그라운드)

        주기적으로 ModelOps API를 폴링하여 진행 상태 업데이트

        Args:
            batch_id: 배치 작업 ID
        """
        job = self._batch_jobs[batch_id]

        # 작업 시작
        job["status"] = BatchStatus.PROCESSING

        # TODO: ModelOps API 폴링 (실제 구현)
        # while job["status"] == BatchStatus.PROCESSING:
        #     await asyncio.sleep(5)  # 5초마다 폴링
        #     progress_response = await self._fetch_modelops_progress(batch_id)
        #     job["progress_percentage"] = progress_response["progress"]
        #     job["processed_grids"] = progress_response["processed"]
        #
        #     if progress_response["status"] == "completed":
        #         job["status"] = BatchStatus.COMPLETED
        #         job["completed_at"] = datetime.now()
        #         break
        #     elif progress_response["status"] == "failed":
        #         job["status"] = BatchStatus.FAILED
        #         job["error_message"] = progress_response["error"]
        #         break

        # 임시 Mock 구현 (10%, 30%, 50%, 70%, 90%, 100%)
        for progress in [10, 30, 50, 70, 90, 100]:
            await asyncio.sleep(3)  # 3초마다 업데이트
            job["progress_percentage"] = progress
            job["processed_grids"] = int(job["total_grids"] * progress / 100)

            if progress == 100:
                job["status"] = BatchStatus.COMPLETED
                job["completed_at"] = datetime.now()

                # Mock 결과 생성
                self._batch_results[batch_id] = self._create_mock_result(batch_id, job)

    def _create_mock_result(self, batch_id: UUID, job: dict) -> SiteRecommendationResultResponse:
        """
        Mock 결과 생성 (실제로는 ModelOps API에서 받아옴)

        Args:
            batch_id: 배치 작업 ID
            job: 작업 정보

        Returns:
            추천 후보지 결과
        """
        request = job["request"]

        # Mock 추천 후보지 (상위 3개)
        recommended_sites = [
            RecommendedSite(
                rank=1,
                grid_id=12345,
                latitude=37.5665,
                longitude=126.9780,
                location_name="서울특별시 중구",
                total_risk_score=35.2,
                hazard_scores={
                    "extreme_heat": 0.45,
                    "extreme_cold": 0.38,
                    "wildfire": 0.12,
                    "drought": 0.28,
                    "water_stress": 0.33,
                    "sea_level_rise": 0.15,
                    "river_flood": 0.25,
                    "urban_flood": 0.42,
                    "typhoon": 0.38,
                },
                exposure_scores={
                    "extreme_heat": 0.65,
                    "extreme_cold": 0.60,
                    "wildfire": 0.30,
                    "drought": 0.55,
                    "water_stress": 0.52,
                    "sea_level_rise": 0.40,
                    "river_flood": 0.48,
                    "urban_flood": 0.68,
                    "typhoon": 0.62,
                },
                vulnerability_scores={
                    "extreme_heat": 65.0,
                    "extreme_cold": 55.0,
                    "wildfire": 35.0,
                    "drought": 50.0,
                    "water_stress": 48.0,
                    "sea_level_rise": 40.0,
                    "river_flood": 52.0,
                    "urban_flood": 70.0,
                    "typhoon": 60.0,
                },
                aal_total=1.25,
                expected_loss=625000000,
            ),
            RecommendedSite(
                rank=2,
                grid_id=12346,
                latitude=37.5700,
                longitude=126.9800,
                location_name="서울특별시 종로구",
                total_risk_score=36.8,
                hazard_scores={
                    "extreme_heat": 0.48,
                    "extreme_cold": 0.40,
                    "wildfire": 0.14,
                    "drought": 0.30,
                    "water_stress": 0.35,
                    "sea_level_rise": 0.17,
                    "river_flood": 0.27,
                    "urban_flood": 0.44,
                    "typhoon": 0.40,
                },
                exposure_scores={
                    "extreme_heat": 0.67,
                    "extreme_cold": 0.62,
                    "wildfire": 0.32,
                    "drought": 0.57,
                    "water_stress": 0.54,
                    "sea_level_rise": 0.42,
                    "river_flood": 0.50,
                    "urban_flood": 0.70,
                    "typhoon": 0.64,
                },
                vulnerability_scores={
                    "extreme_heat": 65.0,
                    "extreme_cold": 55.0,
                    "wildfire": 35.0,
                    "drought": 50.0,
                    "water_stress": 48.0,
                    "sea_level_rise": 40.0,
                    "river_flood": 52.0,
                    "urban_flood": 70.0,
                    "typhoon": 60.0,
                },
                aal_total=1.35,
                expected_loss=675000000,
            ),
            RecommendedSite(
                rank=3,
                grid_id=12347,
                latitude=37.5730,
                longitude=126.9850,
                location_name="서울특별시 성북구",
                total_risk_score=38.1,
                hazard_scores={
                    "extreme_heat": 0.50,
                    "extreme_cold": 0.42,
                    "wildfire": 0.16,
                    "drought": 0.32,
                    "water_stress": 0.37,
                    "sea_level_rise": 0.19,
                    "river_flood": 0.29,
                    "urban_flood": 0.46,
                    "typhoon": 0.42,
                },
                exposure_scores={
                    "extreme_heat": 0.69,
                    "extreme_cold": 0.64,
                    "wildfire": 0.34,
                    "drought": 0.59,
                    "water_stress": 0.56,
                    "sea_level_rise": 0.44,
                    "river_flood": 0.52,
                    "urban_flood": 0.72,
                    "typhoon": 0.66,
                },
                vulnerability_scores={
                    "extreme_heat": 65.0,
                    "extreme_cold": 55.0,
                    "wildfire": 35.0,
                    "drought": 50.0,
                    "water_stress": 48.0,
                    "sea_level_rise": 40.0,
                    "river_flood": 52.0,
                    "urban_flood": 70.0,
                    "typhoon": 60.0,
                },
                aal_total=1.42,
                expected_loss=710000000,
            ),
        ]

        scenario_names = {
            1: "SSP1-2.6",
            2: "SSP2-4.5",
            3: "SSP3-7.0",
            4: "SSP5-8.5",
        }

        return SiteRecommendationResultResponse(
            batch_id=batch_id,
            status=BatchStatus.COMPLETED,
            scenario_id=request.scenario_id,
            scenario_name=scenario_names[request.scenario_id],
            total_grids_analyzed=job["total_grids"],
            recommended_sites=recommended_sites[: request.top_n],
            completed_at=job["completed_at"],
        )

    async def cancel_batch_job(self, batch_id: UUID) -> bool:
        """
        배치 작업 취소

        Args:
            batch_id: 배치 작업 ID

        Returns:
            취소 성공 여부
        """
        job = self._batch_jobs.get(batch_id)

        if not job:
            return False

        if job["status"] in [BatchStatus.COMPLETED, BatchStatus.FAILED]:
            return False

        # TODO: ModelOps API에 취소 요청
        # DELETE /api/v1/batch/{batch_id}

        job["status"] = BatchStatus.FAILED
        job["error_message"] = "Batch job cancelled by user"
        job["completed_at"] = datetime.now()

        return True
