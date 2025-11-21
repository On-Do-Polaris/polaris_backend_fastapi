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


class RelocationSimulationRequest(BaseModel):
    """Spring Boot API 호환 - 사업장 이전 시뮬레이션 요청"""
    current_site_id: UUID = Field(..., alias="currentSiteId", description="현재 사업장 ID")
    latitude: float = Field(..., description="이전될 위치의 위도")
    longitude: float = Field(..., description="이전될 위치의 경도")
    road_address: Optional[str] = Field(None, alias="roadAddress", description="이전될 위치의 도로명 주소")
    jibun_address: Optional[str] = Field(None, alias="jibunAddress", description="이전될 위치의 지번 주소")

    class Config:
        populate_by_name = True


class RiskData(BaseModel):
    """리스크별 데이터"""
    risk_type: str = Field(..., alias="riskType", description="리스크 유형")
    risk_score: int = Field(ge=0, le=100, alias="riskScore", description="리스크 점수 (0-100)")
    aal: float = Field(ge=0, le=1, description="AAL (연평균 자산 손실률, 0.0-1.0)")

    class Config:
        populate_by_name = True


class LocationData(BaseModel):
    """위치별 리스크 데이터"""
    risks: list[RiskData] = Field(..., description="리스크별 분석 결과")

    class Config:
        populate_by_name = True


class RelocationSimulationResponse(BaseModel):
    """Spring Boot API 호환 - 사업장 이전 시뮬레이션 결과"""
    current_location: LocationData = Field(..., alias="currentLocation")
    new_location: LocationData = Field(..., alias="newLocation")

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
