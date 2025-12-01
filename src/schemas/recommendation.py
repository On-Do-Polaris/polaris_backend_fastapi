from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from uuid import UUID
from datetime import datetime
from enum import Enum

from src.schemas.common import SSPScenario, HazardType


class BatchStatus(str, Enum):
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


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


class SiteRecommendationBatchResponse(BaseModel):
    """배치 작업 시작 응답"""
    batch_id: UUID = Field(..., description="배치 작업 ID")
    status: BatchStatus = Field(..., description="작업 상태")
    estimated_duration_minutes: int = Field(..., description="예상 소요 시간 (분)")
    status_url: str = Field(..., description="진행 상태 조회 URL")
    created_at: datetime = Field(default_factory=datetime.now)

    class Config:
        json_schema_extra = {
            "example": {
                "batch_id": "550e8400-e29b-41d4-a716-446655440000",
                "status": "queued",
                "estimated_duration_minutes": 30,
                "status_url": "/api/recommendation/batch/550e8400-e29b-41d4-a716-446655440000/progress",
                "created_at": "2025-12-01T10:30:00Z"
            }
        }


class BatchProgressResponse(BaseModel):
    """배치 작업 진행 상태 응답"""
    batch_id: UUID
    status: BatchStatus
    progress_percentage: int = Field(..., ge=0, le=100, description="진행률 (%)")
    processed_grids: int = Field(..., description="처리 완료된 격자 수")
    total_grids: int = Field(..., description="전체 격자 수")
    started_at: datetime
    estimated_completion: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "batch_id": "550e8400-e29b-41d4-a716-446655440000",
                "status": "processing",
                "progress_percentage": 45,
                "processed_grids": 4500,
                "total_grids": 10000,
                "started_at": "2025-12-01T10:30:00Z",
                "estimated_completion": "2025-12-01T11:00:00Z",
                "completed_at": None,
                "error_message": None
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
    """후보지 추천 결과 응답"""
    batch_id: UUID
    status: BatchStatus
    scenario_id: int
    scenario_name: str
    total_grids_analyzed: int
    recommended_sites: List[RecommendedSite]
    completed_at: datetime

    class Config:
        json_schema_extra = {
            "example": {
                "batch_id": "550e8400-e29b-41d4-a716-446655440000",
                "status": "completed",
                "scenario_id": 2,
                "scenario_name": "SSP2-4.5",
                "total_grids_analyzed": 10000,
                "recommended_sites": [
                    {
                        "rank": 1,
                        "grid_id": 12345,
                        "latitude": 37.5665,
                        "longitude": 126.9780,
                        "total_risk_score": 35.2,
                        "aal_total": 1.25,
                        "expected_loss": 625000000
                    },
                    {
                        "rank": 2,
                        "grid_id": 12346,
                        "latitude": 37.5700,
                        "longitude": 126.9800,
                        "total_risk_score": 36.8,
                        "aal_total": 1.35,
                        "expected_loss": 675000000
                    },
                    {
                        "rank": 3,
                        "grid_id": 12347,
                        "latitude": 37.5730,
                        "longitude": 126.9850,
                        "total_risk_score": 38.1,
                        "aal_total": 1.42,
                        "expected_loss": 710000000
                    }
                ],
                "completed_at": "2025-12-01T11:00:00Z"
            }
        }
