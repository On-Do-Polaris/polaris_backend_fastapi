from uuid import UUID, uuid4
from typing import Optional
from datetime import datetime, timedelta
import asyncio
import time
import logging

from src.schemas.recommendation import (
    SiteRecommendationRequest,
    SiteRecommendationBatchResponse,
    BatchProgressResponse,
    SiteRecommendationResultResponse,
    RecommendedSite,
    BatchStatus,
)
from ai_agent.services.modelops_client import get_modelops_client

logger = logging.getLogger(__name__)


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

        # ModelOps API에 배치 작업 요청
        try:
            modelops = get_modelops_client()

            # 사업장 데이터 준비
            sites_data = [{
                "scenario_id": request.scenario_id,
                "building_info": request.building_info.dict() if request.building_info else {},
                "asset_info": request.asset_info.dict() if request.asset_info else {},
                "top_n": request.top_n,
                "additional_data": request.additional_data or {}
            }]

            batch_response = modelops.start_batch_recommendation(
                sites=sites_data,
                recommendation_type="mitigation_priority",
                scenario=f"SSP{request.scenario_id}"
            )

            modelops_batch_id = batch_response.get("batch_id")
            logger.info(f"ModelOps 배치 작업 시작: batch_id={modelops_batch_id}")

        except Exception as e:
            logger.error(f"ModelOps 배치 작업 시작 실패: {e}")
            # Mock으로 fallback
            modelops_batch_id = None

        # 배치 작업 상태 초기화
        self._batch_jobs[batch_id] = {
            "status": BatchStatus.QUEUED,
            "progress_percentage": 0,
            "processed_grids": 0,
            "total_grids": 10000,
            "started_at": datetime.now(),
            "estimated_completion": datetime.now() + timedelta(minutes=30),
            "request": request,
            "modelops_batch_id": modelops_batch_id,  # ModelOps 배치 ID 저장
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

        # ModelOps API에서 진행 상태 조회
        if job.get("modelops_batch_id"):
            try:
                modelops = get_modelops_client()
                progress_data = modelops.get_batch_progress(job["modelops_batch_id"])

                # ModelOps 응답으로 상태 업데이트
                job["progress_percentage"] = int(progress_data.get("progress", 0) * 100)
                job["processed_grids"] = progress_data.get("processed_count", 0)
                job["total_grids"] = progress_data.get("total_count", 10000)

                # 상태 매핑
                modelops_status = progress_data.get("status")
                if modelops_status == "completed":
                    job["status"] = BatchStatus.COMPLETED
                    job["completed_at"] = datetime.now()
                elif modelops_status == "failed":
                    job["status"] = BatchStatus.FAILED
                    job["error_message"] = "ModelOps batch job failed"
                elif modelops_status == "processing":
                    job["status"] = BatchStatus.PROCESSING

            except Exception as e:
                logger.warning(f"ModelOps 진행 상태 조회 실패: {e}")

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
            # ModelOps API에서 결과 조회
            if job.get("modelops_batch_id"):
                try:
                    modelops = get_modelops_client()
                    results_data = modelops.get_batch_results(job["modelops_batch_id"])

                    # ModelOps 결과를 우리 포맷으로 변환
                    result = self._convert_modelops_result(batch_id, job, results_data)
                    self._batch_results[batch_id] = result

                except Exception as e:
                    logger.error(f"ModelOps 결과 조회 실패: {e}")
                    return None
            else:
                return None

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

        # ModelOps API 폴링 (실제 구현)
        if job.get("modelops_batch_id"):
            try:
                modelops = get_modelops_client()
                poll_interval = 5  # 5초마다 폴링
                max_wait_time = 600  # 최대 10분
                start_time = time.time()

                while time.time() - start_time < max_wait_time:
                    try:
                        progress_data = modelops.get_batch_progress(job["modelops_batch_id"])
                        status = progress_data.get("status")

                        # 상태 업데이트
                        job["progress_percentage"] = int(progress_data.get("progress", 0) * 100)
                        job["processed_grids"] = progress_data.get("processed_count", 0)
                        job["total_grids"] = progress_data.get("total_count", 10000)

                        if status == "completed":
                            job["status"] = BatchStatus.COMPLETED
                            job["completed_at"] = datetime.now()
                            logger.info(f"배치 작업 완료: batch_id={batch_id}")

                            # 결과 조회 및 저장
                            results_data = modelops.get_batch_results(job["modelops_batch_id"])
                            self._batch_results[batch_id] = self._convert_modelops_result(batch_id, job, results_data)
                            break

                        elif status == "failed":
                            job["status"] = BatchStatus.FAILED
                            job["error_message"] = "ModelOps batch job failed"
                            job["completed_at"] = datetime.now()
                            logger.error(f"배치 작업 실패: batch_id={batch_id}")
                            break

                        # 아직 진행 중이면 대기
                        await asyncio.sleep(poll_interval)
                        poll_interval = min(poll_interval * 1.5, 30)  # Exponential backoff

                    except Exception as e:
                        logger.error(f"ModelOps 폴링 오류: {e}")
                        await asyncio.sleep(poll_interval)

                # 타임아웃 처리
                if time.time() - start_time >= max_wait_time:
                    job["status"] = BatchStatus.FAILED
                    job["error_message"] = "Batch job timeout"
                    job["completed_at"] = datetime.now()
                    logger.error(f"배치 작업 타임아웃: batch_id={batch_id}")

            except Exception as e:
                job["status"] = BatchStatus.FAILED
                job["error_message"] = f"ModelOps 폴링 실패: {str(e)}"
                job["completed_at"] = datetime.now()
                logger.error(f"배치 작업 처리 실패: {e}")
        else:
            # Mock 구현 (ModelOps 연동 실패 시 fallback)
            for progress in [10, 30, 50, 70, 90, 100]:
                await asyncio.sleep(3)
                job["progress_percentage"] = progress
                job["processed_grids"] = int(job["total_grids"] * progress / 100)

                if progress == 100:
                    job["status"] = BatchStatus.COMPLETED
                    job["completed_at"] = datetime.now()
                    self._batch_results[batch_id] = self._create_mock_result(batch_id, job)

    def _convert_modelops_result(self, batch_id: UUID, job: dict, results_data: dict) -> SiteRecommendationResultResponse:
        """
        ModelOps 배치 결과를 내부 포맷으로 변환

        Args:
            batch_id: 배치 작업 ID
            job: 작업 정보
            results_data: ModelOps 결과 데이터

        Returns:
            변환된 추천 후보지 결과
        """
        request = job["request"]

        # ModelOps 결과에서 추천 후보지 추출
        modelops_results = results_data.get("results", [])
        recommended_sites = []

        for idx, site_data in enumerate(modelops_results[:request.top_n], start=1):
            recommended_sites.append(RecommendedSite(
                rank=idx,
                grid_id=site_data.get("grid_id", 0),
                latitude=site_data.get("latitude", 0.0),
                longitude=site_data.get("longitude", 0.0),
                location_name=site_data.get("location_name", "Unknown"),
                total_risk_score=site_data.get("total_risk_score", 0.0),
                hazard_scores=site_data.get("hazard_scores", {}),
                exposure_scores=site_data.get("exposure_scores", {}),
                vulnerability_scores=site_data.get("vulnerability_scores", {}),
                aal_total=site_data.get("aal_total", 0.0),
                expected_loss=site_data.get("expected_loss", 0),
            ))

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
            scenario_name=scenario_names.get(request.scenario_id, "Unknown"),
            total_grids_analyzed=results_data.get("total_analyzed", job["total_grids"]),
            recommended_sites=recommended_sites,
            completed_at=job["completed_at"],
        )

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

        # ModelOps API에 취소 요청
        if job.get("modelops_batch_id"):
            try:
                modelops = get_modelops_client()
                cancel_response = modelops.cancel_batch_job(job["modelops_batch_id"])
                logger.info(f"ModelOps 배치 작업 취소: batch_id={job['modelops_batch_id']}")
            except Exception as e:
                logger.error(f"ModelOps 배치 작업 취소 실패: {e}")

        job["status"] = BatchStatus.FAILED
        job["error_message"] = "Batch job cancelled by user"
        job["completed_at"] = datetime.now()

        return True
