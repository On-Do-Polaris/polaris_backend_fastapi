from pydantic import BaseModel, Field
from typing import Optional
from uuid import UUID

from .common import SiteInfo, SSPScenario, RiskLevel


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
    base_site_id: UUID = Field(..., alias="baseSiteId")
    candidate_latitude: float = Field(..., alias="candidateLatitude")
    candidate_longitude: float = Field(..., alias="candidateLongitude")
    candidate_name: Optional[str] = Field(None, alias="candidateName")

    class Config:
        populate_by_name = True


class SiteComparison(BaseModel):
    risk_score_diff: int = Field(..., alias="riskScoreDiff")
    risk_score_diff_percent: float = Field(..., alias="riskScoreDiffPercent")
    aal_diff: float = Field(..., alias="aalDiff")
    annual_expected_loss_diff: float = Field(..., alias="annualExpectedLossDiff")

    class Config:
        populate_by_name = True


class RelocationSimulationResult(BaseModel):
    base_site: dict = Field(..., alias="baseSite")
    candidate_site: dict = Field(..., alias="candidateSite")
    comparison: SiteComparison
    climate_factor_comparison: dict = Field({}, alias="climateFactorComparison")
    pros: list[str] = []
    cons: list[str] = []
    recommendation: str
    financial_analysis: dict = Field({}, alias="financialAnalysis")

    class Config:
        populate_by_name = True


class ClimateSimulationRequest(BaseModel):
    scenario: SSPScenario
    hazard_type: Optional[str] = Field(None, alias="hazardType")
    sites: list[SiteInfo]
    start_year: int = Field(2025, alias="startYear")
    end_year: int = Field(2100, alias="endYear")
    time_step: int = Field(10, alias="timeStep")

    class Config:
        populate_by_name = True


class ClimateSimulationPoint(BaseModel):
    year: int
    metric: float
    risk_score: int = Field(..., alias="riskScore")

    class Config:
        populate_by_name = True


class ClimateSimulationSeries(BaseModel):
    site_id: UUID = Field(..., alias="siteId")
    site_name: str = Field(..., alias="siteName")
    metric_name: str = Field(..., alias="metricName")
    metric_unit: str = Field(..., alias="metricUnit")
    points: list[ClimateSimulationPoint]

    class Config:
        populate_by_name = True


class ClimateSimulationResponse(BaseModel):
    scenario: SSPScenario
    scenario_description: str = Field(..., alias="scenarioDescription")
    hazard_type: Optional[str] = Field(None, alias="hazardType")
    series: list[ClimateSimulationSeries]
    timeline_actions: list[dict] = Field([], alias="timelineActions")
    summary: str

    class Config:
        populate_by_name = True
