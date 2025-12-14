from pydantic import BaseModel, Field
from typing import Optional
from uuid import UUID

from .common import SSPScenario, RiskLevel


class RelocationCandidatesRequest(BaseModel):
    base_site_id: UUID = Field(..., alias="baseSiteId")

    class Config:
        populate_by_name = True


class RelocationCandidate(BaseModel):
    id: UUID
    name: str
    city: str
    latitude: float
    longitude: float
    location_summary: str = Field(..., alias="locationSummary")
    risk_score: int = Field(ge=0, le=100, alias="riskScore")
    risk_level: RiskLevel = Field(..., alias="riskLevel")
    aal: float
    distance: float
    estimated_cost: float = Field(..., alias="estimatedCost")
    advantages: list[str] = []
    disadvantages: list[str] = []

    class Config:
        populate_by_name = True


class RelocationCandidatesResponse(BaseModel):
    base_site: dict = Field(..., alias="baseSite")
    candidates: list[RelocationCandidate]

    class Config:
        populate_by_name = True


class CandidateLocation(BaseModel):
    """이전 후보지 위치 정보"""
    latitude: float = Field(..., description="이전될 위치의 위도")
    longitude: float = Field(..., description="이전될 위치의 경도")
    jibun_address: Optional[str] = Field(None, alias="jibunAddress", description="이전될 위치의 지번 주소")
    road_address: Optional[str] = Field(None, alias="roadAddress", description="이전될 위치의 도로명 주소")

    class Config:
        populate_by_name = True


class RelocationSimulationRequest(BaseModel):
    """Spring Boot API 호환 - 사업장 이전 시뮬레이션 요청"""
    site_id: UUID = Field(..., alias="siteId", description="현재 사업장 ID")
    candidate: CandidateLocation = Field(..., description="이전 후보지 정보")

    class Config:
        populate_by_name = True


class PhysicalRiskScores(BaseModel):
    """재난별 물리적 리스크 점수 (0-100)"""
    extreme_heat: int = Field(ge=0, le=100)
    extreme_cold: int = Field(ge=0, le=100)
    river_flood: int = Field(ge=0, le=100)
    urban_flood: int = Field(ge=0, le=100)
    drought: int = Field(ge=0, le=100)
    water_stress: int = Field(ge=0, le=100)
    sea_level_rise: int = Field(ge=0, le=100)
    typhoon: int = Field(ge=0, le=100)
    wildfire: int = Field(ge=0, le=100)


class AALScores(BaseModel):
    """재난별 AAL 점수"""
    extreme_heat: float = Field(ge=0)
    extreme_cold: float = Field(ge=0)
    river_flood: float = Field(ge=0)
    urban_flood: float = Field(ge=0)
    drought: float = Field(ge=0)
    water_stress: float = Field(ge=0)
    sea_level_rise: float = Field(ge=0)
    typhoon: float = Field(ge=0)
    wildfire: float = Field(ge=0)


class CandidateResult(BaseModel):
    """이전 후보지 분석 결과"""
    candidate_id: UUID = Field(..., alias="candidateId", description="후보지 ID")
    latitude: float = Field(..., description="후보지 위도")
    longitude: float = Field(..., description="후보지 경도")
    jibun_address: Optional[str] = Field(None, alias="jibunAddress", description="지번 주소")
    road_address: Optional[str] = Field(None, alias="roadAddress", description="도로명 주소")
    riskscore: int = Field(ge=0, le=100, description="종합 리스크 점수 (0-100)")
    aalscore: float = Field(ge=0, description="종합 AAL 점수")
    physical_risk_scores: PhysicalRiskScores = Field(..., alias="physical-risk-scores", description="재난별 물리적 리스크 점수")
    aal_scores: AALScores = Field(..., alias="aal-scores", description="재난별 AAL 점수")
    pros: str = Field(..., description="장점")
    cons: str = Field(..., description="단점")

    class Config:
        populate_by_name = True


class RelocationSimulationResponse(BaseModel):
    """Spring Boot API 호환 - 사업장 이전 시뮬레이션 결과"""
    site_id: UUID = Field(..., alias="siteId", description="현재 사업장 ID")
    candidate: CandidateResult = Field(..., description="후보지 분석 결과")

    class Config:
        populate_by_name = True


class ClimateSimulationRequest(BaseModel):
    """Spring Boot API 호환 - 기후 시뮬레이션 요청"""
    scenario: SSPScenario = Field(..., description="SSP 시나리오")
    hazard_type: str = Field(..., alias="hazardType", description="위험 유형")
    site_ids: list[UUID] = Field(..., alias="siteIds", description="시뮬레이션 대상 사업장 ID 목록")
    start_year: int = Field(..., alias="startYear", description="시작 연도")

    class Config:
        populate_by_name = True


class SiteData(BaseModel):
    """사업장 데이터"""
    site_id: UUID = Field(..., alias="siteId", description="사업장 ID")
    site_name: str = Field(..., alias="siteName", description="사업장 이름")
    risk_score: int = Field(ge=0, le=100, alias="riskScore", description="리스크 점수 (0-100)")
    local_average_temperature: float = Field(..., alias="localAverageTemperature", description="사업장 위치 평균 기온 (°C)")

    class Config:
        populate_by_name = True


class YearlyData(BaseModel):
    """연도별 데이터"""
    year: int = Field(..., description="연도")
    national_average_temperature: float = Field(..., alias="nationalAverageTemperature", description="전국 평균 기온 (°C)")
    sites: list[SiteData] = Field(..., description="사업장별 데이터")

    class Config:
        populate_by_name = True


class ClimateSimulationResponse(BaseModel):
    """Spring Boot API 호환 - 기후 시뮬레이션 결과"""
    scenario: SSPScenario = Field(..., description="SSP 시나리오")
    risk_type: str = Field(..., alias="riskType", description="리스크 유형")
    yearly_data: list[YearlyData] = Field(..., alias="yearlyData", description="연도별 시뮬레이션 데이터")

    class Config:
        populate_by_name = True
