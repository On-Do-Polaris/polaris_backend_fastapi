from pydantic import BaseModel, Field
from typing import Optional
from uuid import UUID
from datetime import datetime

from .common import SiteInfo, HazardType, TimeScale, RiskLevel, Priority, SSPScenario


# Request Schemas
class AnalysisOptions(BaseModel):
    include_financial_impact: bool = Field(True, alias="includeFinancialImpact")
    include_vulnerability: bool = Field(True, alias="includeVulnerability")
    include_past_events: bool = Field(True, alias="includePastEvents")
    ssp_scenarios: list[SSPScenario] = Field(
        default=[SSPScenario.SSP2_45, SSPScenario.SSP5_85],
        alias="sspScenarios"
    )

    class Config:
        populate_by_name = True


class StartAnalysisRequest(BaseModel):
    site: SiteInfo
    hazard_types: Optional[list[HazardType]] = Field(None, alias="hazardTypes")
    priority: Priority = Priority.NORMAL
    options: Optional[AnalysisOptions] = None

    class Config:
        populate_by_name = True


# Response Schemas
class AnalysisJobStatus(BaseModel):
    job_id: UUID = Field(..., alias="jobId")
    site_id: UUID = Field(..., alias="siteId")
    status: str  # queued, running, completed, failed
    progress: int = Field(ge=0, le=100)
    current_node: Optional[str] = Field(None, alias="currentNode")
    current_hazard: Optional[str] = Field(None, alias="currentHazard")
    started_at: Optional[datetime] = Field(None, alias="startedAt")
    completed_at: Optional[datetime] = Field(None, alias="completedAt")
    estimated_completion_time: Optional[datetime] = Field(None, alias="estimatedCompletionTime")
    error: Optional[dict] = None

    class Config:
        populate_by_name = True


class PhysicalRiskBarItem(BaseModel):
    hazard_type: HazardType = Field(..., alias="hazardType")
    score: int = Field(ge=0, le=100)
    hazard_score: float = Field(ge=0, le=1, alias="hazardScore")
    exposure_score: float = Field(ge=0, le=1, alias="exposureScore")
    vulnerability_score: float = Field(ge=0, le=1, alias="vulnerabilityScore")
    risk_calculation_method: str = Field("H×E×V", alias="riskCalculationMethod")

    class Config:
        populate_by_name = True


class AnalysisOverviewResponse(BaseModel):
    site_id: UUID = Field(..., alias="siteId")
    analyzed_at: datetime = Field(..., alias="analyzedAt")
    main_hazard: HazardType = Field(..., alias="mainHazard")
    main_hazard_score: int = Field(ge=0, le=100, alias="mainHazardScore")
    overall_risk_score: int = Field(ge=0, le=100, alias="overallRiskScore")
    risk_level: RiskLevel = Field(..., alias="riskLevel")
    aal: float = Field(ge=0, le=1, description="연평균 자산 손실률")
    annual_expected_loss: float = Field(..., alias="annualExpectedLoss", description="연평균 재무 손실액 (KRW)")
    asset_value: float = Field(..., alias="assetValue", description="자산 가치 (KRW)")
    recommendations: list[str] = []

    class Config:
        populate_by_name = True


class PhysicalRiskScoreResponse(BaseModel):
    site_id: UUID = Field(..., alias="siteId")
    analyzed_at: datetime = Field(..., alias="analyzedAt")
    hazard_type: Optional[HazardType] = Field(None, alias="hazardType")
    physical_risk_scores: list[PhysicalRiskBarItem] = Field(..., alias="physicalRiskScores")

    class Config:
        populate_by_name = True


# Past Events
class PastEventSummary(BaseModel):
    total_events: int = Field(..., alias="totalEvents")
    severe_events: int = Field(..., alias="severeEvents")
    avg_warning_days: float = Field(..., alias="avgWarningDays")
    avg_severe_days: float = Field(..., alias="avgSevereDays")
    most_frequent_hazard: str = Field(..., alias="mostFrequentHazard")
    year_range: dict = Field(..., alias="yearRange")

    class Config:
        populate_by_name = True


class PastEventItem(BaseModel):
    year: int
    month: int
    hazard_type: HazardType = Field(..., alias="hazardType")
    warning_days: int = Field(..., alias="warningDays")
    severe_days: int = Field(..., alias="severeDays")
    max_intensity: float = Field(..., alias="maxIntensity")
    severity_level: str = Field(..., alias="severityLevel")
    description: Optional[str] = None

    class Config:
        populate_by_name = True


class PastEventsResponse(BaseModel):
    site_id: UUID = Field(..., alias="siteId")
    summary: PastEventSummary
    events: list[PastEventItem]

    class Config:
        populate_by_name = True


# SSP Projection
class SSPProjectionPoint(BaseModel):
    decade: str
    year: int
    physical_risk_score: int = Field(ge=0, le=100, alias="physicalRiskScore")
    aal: float = Field(ge=0, le=1)
    annual_expected_loss: float = Field(..., alias="annualExpectedLoss")
    intensity: Optional[float] = None
    frequency: Optional[float] = None

    class Config:
        populate_by_name = True


class SSPScenarioProjection(BaseModel):
    scenario: SSPScenario
    scenario_description: str = Field(..., alias="scenarioDescription")
    points: list[SSPProjectionPoint]

    class Config:
        populate_by_name = True


class SSPProjectionResponse(BaseModel):
    site_id: UUID = Field(..., alias="siteId")
    hazard_type: HazardType = Field(..., alias="hazardType")
    time_scale: TimeScale = Field(..., alias="timeScale")
    projections: list[SSPScenarioProjection]
    adaptation_actions: list[dict] = Field([], alias="adaptationActions")
    confidence_level: str = Field("medium", alias="confidenceLevel")

    class Config:
        populate_by_name = True


# Financial Impact
class FinancialImpactItem(BaseModel):
    hazard_type: HazardType = Field(..., alias="hazardType")
    aal: float = Field(ge=0, le=1)
    annual_expected_loss: float = Field(..., alias="annualExpectedLoss")

    class Config:
        populate_by_name = True


class FinancialImpactResponse(BaseModel):
    site_id: UUID = Field(..., alias="siteId")
    analyzed_at: datetime = Field(..., alias="analyzedAt")
    hazard_type: Optional[HazardType] = Field(None, alias="hazardType")
    asset_value: float = Field(..., alias="assetValue")
    financial_impacts: list[FinancialImpactItem] = Field(..., alias="financialImpacts")

    class Config:
        populate_by_name = True


# Vulnerability
class VulnerabilityItem(BaseModel):
    hazard_type: HazardType = Field(..., alias="hazardType")
    score: int = Field(ge=0, le=100)
    level: RiskLevel
    factors: dict
    improvement_actions: list[str] = Field([], alias="improvementActions")

    class Config:
        populate_by_name = True


class VulnerabilityResponse(BaseModel):
    site_id: UUID = Field(..., alias="siteId")
    total_score: int = Field(ge=0, le=100, alias="totalScore")
    overall_level: RiskLevel = Field(..., alias="overallLevel")
    site_info: dict = Field(..., alias="siteInfo")
    details: list[VulnerabilityItem]
    priority_actions: list[dict] = Field([], alias="priorityActions")

    class Config:
        populate_by_name = True


# Total Analysis
class AnalysisTotalResponse(BaseModel):
    site_id: UUID = Field(..., alias="siteId")
    hazard_type: HazardType = Field(..., alias="hazardType")
    overview: AnalysisOverviewResponse
    past_events: PastEventsResponse = Field(..., alias="pastEvents")
    ssp_projection: SSPProjectionResponse = Field(..., alias="sspProjection")
    financial_impact: FinancialImpactResponse = Field(..., alias="financialImpact")
    vulnerability: VulnerabilityResponse
    executive_summary: str = Field(..., alias="executiveSummary")
    generated_at: datetime = Field(..., alias="generatedAt")

    class Config:
        populate_by_name = True
