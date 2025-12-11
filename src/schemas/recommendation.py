from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from uuid import UUID
from datetime import datetime
from enum import Enum

from src.schemas.common import SSPScenario, HazardType


class BatchStatus(str, Enum):
    """배치 작업 상태 (ERD batch_jobs 테이블 기준)"""
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class JobType(str, Enum):
    """작업 유형 (ERD batch_jobs 테이블 기준)"""
    SITE_RECOMMENDATION = "site_recommendation"
    BULK_ANALYSIS = "bulk_analysis"
    DATA_EXPORT = "data_export"


class SiteRecommendationRequest(BaseModel):
    """후보지 추천 배치 작업 시작 요청"""
    scenario_id: int = Field(..., ge=1, le=4, description="SSP 시나리오 ID (1-4)")
    start_year: int = Field(2025, ge=2025, le=2100)
    end_year: int = Field(2050, ge=2025, le=2100)
    building_info: Dict = Field(..., description="건물 정보 (취약성 계산용)")
    asset_info: Dict = Field(..., description="자산 정보")
    top_n: int = Field(3, ge=1, le=10, description="추천할 상위 격자 수")
    additional_data: Optional[Dict] = Field(None, description="추가 데이터 (자유 형식)")

    class Config:
        json_schema_extra = {
            "example": {
                "scenario_id": 2,
                "start_year": 2025,
                "end_year": 2050,
                "building_info": {
                    "building_age": 25,
                    "structure": "철근콘크리트",
                    "main_purpose": "업무시설",
                    "floors_below": 2,
                    "floors_above": 10,
                    "has_piloti": False,
                    "has_seismic_design": True,
                    "fire_access": True
                },
                "asset_info": {
                    "total_asset_value": 50000000000,
                    "floor_area": 5000.0,
                    "insurance_coverage_rate": 0.7
                },
                "top_n": 3,
                "additional_data": {
                    "raw_text": "건물 리모델링 2023년 완료, 태양광 패널 200kW 설치 예정",
                    "metadata": {"source": "user_input", "timestamp": "2025-12-01"}
                }
            }
        }


class BatchJob(BaseModel):
    """배치 작업 정보 (ERD batch_jobs 테이블 기준)"""
    batch_id: UUID = Field(..., alias="batchId", description="배치 작업 ID")
    job_type: JobType = Field(..., alias="jobType", description="작업 유형")
    status: BatchStatus = Field(..., description="작업 상태")
    progress: int = Field(0, ge=0, le=100, description="진행률 (0-100)")
    total_items: Optional[int] = Field(None, alias="totalItems", description="전체 항목 수")
    completed_items: int = Field(0, alias="completedItems", description="완료 항목 수")
    failed_items: int = Field(0, alias="failedItems", description="실패 항목 수")
    input_params: Optional[dict] = Field(None, alias="inputParams", description="입력 파라미터")
    results: Optional[dict] = Field(None, description="결과 데이터")
    error_message: Optional[str] = Field(None, alias="errorMessage", description="에러 메시지")
    error_stack_trace: Optional[str] = Field(None, alias="errorStackTrace", description="스택 트레이스")
    estimated_duration_minutes: Optional[int] = Field(None, alias="estimatedDurationMinutes", description="예상 소요 시간 (분)")
    actual_duration_seconds: Optional[int] = Field(None, alias="actualDurationSeconds", description="실제 소요 시간 (초)")
    created_at: datetime = Field(default_factory=datetime.now, alias="createdAt")
    started_at: Optional[datetime] = Field(None, alias="startedAt")
    completed_at: Optional[datetime] = Field(None, alias="completedAt")
    expires_at: Optional[datetime] = Field(None, alias="expiresAt")
    created_by: Optional[UUID] = Field(None, alias="createdBy")

    class Config:
        populate_by_name = True


class SiteRecommendationBatchResponse(BaseModel):
    """배치 작업 시작 응답"""
    batch_id: UUID = Field(..., alias="batchId", description="배치 작업 ID")
    status: BatchStatus = Field(..., description="작업 상태")
    estimated_duration_minutes: int = Field(..., alias="estimatedDurationMinutes", description="예상 소요 시간 (분)")
    status_url: str = Field(..., alias="statusUrl", description="진행 상태 조회 URL")
    created_at: datetime = Field(default_factory=datetime.now, alias="createdAt")

    class Config:
        populate_by_name = True
        json_schema_extra = {
            "example": {
                "batchId": "550e8400-e29b-41d4-a716-446655440000",
                "status": "queued",
                "estimatedDurationMinutes": 30,
                "statusUrl": "/api/recommendation/batch/550e8400-e29b-41d4-a716-446655440000/progress",
                "createdAt": "2025-12-01T10:30:00Z"
            }
        }


class BatchProgressResponse(BaseModel):
    """배치 작업 진행 상태 응답 (ERD batch_jobs 기반)"""
    batch_id: UUID = Field(..., alias="batchId")
    job_type: JobType = Field(..., alias="jobType")
    status: BatchStatus
    progress: int = Field(..., ge=0, le=100, description="진행률 (%)")
    total_items: Optional[int] = Field(None, alias="totalItems", description="전체 항목 수")
    completed_items: int = Field(..., alias="completedItems", description="완료 항목 수")
    failed_items: int = Field(..., alias="failedItems", description="실패 항목 수")
    started_at: Optional[datetime] = Field(None, alias="startedAt")
    completed_at: Optional[datetime] = Field(None, alias="completedAt")
    estimated_duration_minutes: Optional[int] = Field(None, alias="estimatedDurationMinutes")
    actual_duration_seconds: Optional[int] = Field(None, alias="actualDurationSeconds")
    error_message: Optional[str] = Field(None, alias="errorMessage")

    class Config:
        populate_by_name = True
        json_schema_extra = {
            "example": {
                "batchId": "550e8400-e29b-41d4-a716-446655440000",
                "jobType": "site_recommendation",
                "status": "running",
                "progress": 45,
                "totalItems": 10000,
                "completedItems": 4500,
                "failedItems": 10,
                "startedAt": "2025-12-01T10:30:00Z",
                "completedAt": None,
                "estimatedDurationMinutes": 30,
                "actualDurationSeconds": None,
                "errorMessage": None
            }
        }


class RecommendedSite(BaseModel):
    """추천 후보지 정보"""
    rank: int = Field(..., ge=1, description="순위")
    grid_id: int
    latitude: float
    longitude: float
    location_name: Optional[str] = None
    total_risk_score: float = Field(..., description="종합 리스크 점수 (낮을수록 좋음)")
    hazard_scores: Dict[str, float] = Field(..., description="9개 리스크별 Hazard 점수")
    exposure_scores: Dict[str, float] = Field(..., description="9개 리스크별 Exposure 점수")
    vulnerability_scores: Dict[str, float] = Field(..., description="9개 리스크별 Vulnerability 점수")
    aal_total: float = Field(..., description="총 AAL (%)")
    expected_loss: float = Field(..., description="예상 손실액 (원)")

    class Config:
        json_schema_extra = {
            "example": {
                "rank": 1,
                "grid_id": 12345,
                "latitude": 37.5665,
                "longitude": 126.9780,
                "location_name": "서울특별시 중구",
                "total_risk_score": 35.2,
                "hazard_scores": {
                    "extreme_heat": 0.45,
                    "extreme_cold": 0.38,
                    "wildfire": 0.12,
                    "drought": 0.28,
                    "water_stress": 0.33,
                    "sea_level_rise": 0.15,
                    "river_flood": 0.25,
                    "urban_flood": 0.42,
                    "typhoon": 0.38
                },
                "exposure_scores": {
                    "extreme_heat": 0.65,
                    "extreme_cold": 0.60,
                    "wildfire": 0.30,
                    "drought": 0.55,
                    "water_stress": 0.52,
                    "sea_level_rise": 0.40,
                    "river_flood": 0.48,
                    "urban_flood": 0.68,
                    "typhoon": 0.62
                },
                "vulnerability_scores": {
                    "extreme_heat": 65.0,
                    "extreme_cold": 55.0,
                    "wildfire": 35.0,
                    "drought": 50.0,
                    "water_stress": 48.0,
                    "sea_level_rise": 40.0,
                    "river_flood": 52.0,
                    "urban_flood": 70.0,
                    "typhoon": 60.0
                },
                "aal_total": 1.25,
                "expected_loss": 625000000
            }
        }


class SiteRecommendationResultResponse(BaseModel):
    """후보지 추천 결과 응답 (ERD batch_jobs 기반)"""
    batch_id: UUID = Field(..., alias="batchId")
    job_type: JobType = Field(..., alias="jobType")
    status: BatchStatus
    scenario_id: int = Field(..., alias="scenarioId")
    scenario_name: str = Field(..., alias="scenarioName")
    total_items: int = Field(..., alias="totalItems", description="전체 분석 격자 수")
    completed_items: int = Field(..., alias="completedItems", description="완료 항목 수")
    failed_items: int = Field(..., alias="failedItems", description="실패 항목 수")
    recommended_sites: List[RecommendedSite] = Field(..., alias="recommendedSites")
    completed_at: datetime = Field(..., alias="completedAt")
    actual_duration_seconds: Optional[int] = Field(None, alias="actualDurationSeconds")

    class Config:
        populate_by_name = True
        json_schema_extra = {
            "example": {
                "batchId": "550e8400-e29b-41d4-a716-446655440000",
                "jobType": "site_recommendation",
                "status": "completed",
                "scenarioId": 2,
                "scenarioName": "SSP2-4.5",
                "totalItems": 10000,
                "completedItems": 9990,
                "failedItems": 10,
                "recommendedSites": [
                    {
                        "rank": 1,
                        "grid_id": 12345,
                        "latitude": 37.5665,
                        "longitude": 126.9780,
                        "total_risk_score": 35.2,
                        "aal_total": 1.25,
                        "expected_loss": 625000000
                    }
                ],
                "completedAt": "2025-12-01T11:00:00Z",
                "actualDurationSeconds": 1800
            }
        }
