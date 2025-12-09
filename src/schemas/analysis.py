from pydantic import BaseModel, Field
from typing import Optional
from uuid import UUID
from datetime import datetime

from .common import SiteInfo, HazardType, RiskLevel, Priority, SSPScenario


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


class AdditionalDataInput(BaseModel):
    """추가 데이터 입력 (사용자 제공 컨텍스트)"""
    raw_text: Optional[str] = Field(None, alias="rawText", description="자유 형식 텍스트 (사용자 제공)")
    metadata: Optional[dict] = Field(None, description="메타데이터 (선택)")

    # 구조화된 추가 데이터 (ERD에서 제거된 필드들을 여기로 이동)
    building_info: Optional[dict] = Field(None, alias="buildingInfo", description="건물 정보 (building_age, building_type, seismic_design, gross_floor_area 등)")
    asset_info: Optional[dict] = Field(None, alias="assetInfo", description="자산 정보 (floor_area, asset_value, employee_count 등)")
    power_usage: Optional[dict] = Field(None, alias="powerUsage", description="전력 사용량 (it_power_kwh, cooling_power_kwh, total_power_kwh 등)")
    insurance: Optional[dict] = Field(None, description="보험 정보 (coverage_rate 등)")

    class Config:
        populate_by_name = True


class StartAnalysisRequest(BaseModel):
    """Spring Boot API 호환 - 분석 시작 요청"""
    latitude: float = Field(..., description="위도")
    longitude: float = Field(..., description="경도")
    industry_type: str = Field(..., alias="industryType", description="산업 유형")

    class Config:
        populate_by_name = True


class EnhanceAnalysisRequest(BaseModel):
    """추가 데이터를 반영하여 분석 향상"""
    job_id: UUID = Field(..., alias="jobId", description="원본 분석 작업 ID")
    additional_data: AdditionalDataInput = Field(..., alias="additionalData", description="추가 데이터 (필수)")

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
    """Spring Boot API 호환 - 물리적 리스크 점수"""
    risk_type: HazardType = Field(..., alias="riskType", description="리스크 유형")
    risk_score: int = Field(ge=0, le=100, alias="riskScore", description="리스크 점수 (0-100)")
    financial_loss_rate: float = Field(ge=0, le=1, alias="financialLossRate", description="재무 손실률 (AAL, 0.0-1.0)")

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


class ShortTermScore(BaseModel):
    """단기 리스크 점수 (분기별)"""
    q1: int = Field(ge=0, le=100, description="1분기 점수")
    q2: int = Field(ge=0, le=100, description="2분기 점수")
    q3: int = Field(ge=0, le=100, description="3분기 점수")
    q4: int = Field(ge=0, le=100, description="4분기 점수")

    class Config:
        populate_by_name = True


class MidTermScore(BaseModel):
    """중기 리스크 점수 (연도별)"""
    year2026: int = Field(ge=0, le=100, alias="year2026")
    year2027: int = Field(ge=0, le=100, alias="year2027")
    year2028: int = Field(ge=0, le=100, alias="year2028")
    year2029: int = Field(ge=0, le=100, alias="year2029")
    year2030: int = Field(ge=0, le=100, alias="year2030")

    class Config:
        populate_by_name = True


class LongTermScore(BaseModel):
    """장기 리스크 점수 (연대별)"""
    year2020s: int = Field(ge=0, le=100, alias="year2020s")
    year2030s: int = Field(ge=0, le=100, alias="year2030s")
    year2040s: int = Field(ge=0, le=100, alias="year2040s")
    year2050s: int = Field(ge=0, le=100, alias="year2050s")

    class Config:
        populate_by_name = True


class SSPScenarioScore(BaseModel):
    """SSP 시나리오별 리스크 점수"""
    scenario: SSPScenario
    risk_type: HazardType = Field(..., alias="riskType", description="리스크 종류")
    short_term: ShortTermScore = Field(..., alias="shortTerm")
    mid_term: MidTermScore = Field(..., alias="midTerm")
    long_term: LongTermScore = Field(..., alias="longTerm")

    class Config:
        populate_by_name = True


class PhysicalRiskScoreResponse(BaseModel):
    """Spring Boot API 호환 - 시나리오별 물리적 리스크 점수"""
    scenarios: list[SSPScenarioScore] = Field(..., description="SSP 시나리오별 리스크 점수 목록 (4개 시나리오)")

    class Config:
        populate_by_name = True


# Past Events - Spring Boot API 호환
class DisasterEvent(BaseModel):
    """재난 이벤트"""
    disaster_type: str = Field(..., alias="disasterType", description="재난 유형")
    year: int = Field(..., description="발생 연도")
    warning_days: int = Field(..., alias="warningDays", description="주의 일수")
    severe_days: int = Field(..., alias="severeDays", description="심각 일수")
    overall_status: str = Field(..., alias="overallStatus", description="통합 상태", enum=["경미", "주의", "심각"])

    class Config:
        populate_by_name = True


class PastEventsResponse(BaseModel):
    """Spring Boot API 호환 - 과거 재난 이력"""
    site_id: UUID = Field(..., alias="siteId", description="사업장 ID")
    site_name: str = Field(..., alias="siteName", description="사업장 이름")
    disasters: list[DisasterEvent] = Field(..., description="재난별 이력")

    class Config:
        populate_by_name = True


# Financial Impact - Spring Boot API 호환
class ShortTermAAL(BaseModel):
    """단기 AAL (분기별)"""
    q1: float = Field(..., description="1분기 AAL")
    q2: float = Field(..., description="2분기 AAL")
    q3: float = Field(..., description="3분기 AAL")
    q4: float = Field(..., description="4분기 AAL")

    class Config:
        populate_by_name = True


class MidTermAAL(BaseModel):
    """중기 AAL (연도별)"""
    year2026: float = Field(..., alias="year2026")
    year2027: float = Field(..., alias="year2027")
    year2028: float = Field(..., alias="year2028")
    year2029: float = Field(..., alias="year2029")
    year2030: float = Field(..., alias="year2030")

    class Config:
        populate_by_name = True


class LongTermAAL(BaseModel):
    """장기 AAL (연대별)"""
    year2020s: float = Field(..., alias="year2020s")
    year2030s: float = Field(..., alias="year2030s")
    year2040s: float = Field(..., alias="year2040s")
    year2050s: float = Field(..., alias="year2050s")

    class Config:
        populate_by_name = True


class SSPScenarioImpact(BaseModel):
    """SSP 시나리오별 재무 영향"""
    scenario: SSPScenario
    risk_type: HazardType = Field(..., alias="riskType", description="리스크 종류")
    short_term: ShortTermAAL = Field(..., alias="shortTerm")
    mid_term: MidTermAAL = Field(..., alias="midTerm")
    long_term: LongTermAAL = Field(..., alias="longTerm")

    class Config:
        populate_by_name = True


class FinancialImpactResponse(BaseModel):
    """Spring Boot API 호환 - 시나리오별 재무 영향 분석"""
    scenarios: list[SSPScenarioImpact] = Field(..., description="SSP 시나리오별 재무 영향 목록 (4개 시나리오)")

    class Config:
        populate_by_name = True


# Vulnerability - Spring Boot API 호환
class RiskVulnerability(BaseModel):
    """리스크별 취약성"""
    risk_type: str = Field(..., alias="riskType", description="리스크 유형")
    vulnerability_score: int = Field(ge=0, le=100, alias="vulnerabilityScore", description="취약성 점수 (0-100)")

    class Config:
        populate_by_name = True


class VulnerabilityResponse(BaseModel):
    """Spring Boot API 호환 - 취약성 분석"""
    site_id: UUID = Field(..., alias="siteId", description="사업장 ID")
    vulnerabilities: list[RiskVulnerability] = Field(..., description="리스크별 취약성 점수")

    class Config:
        populate_by_name = True


# Total Analysis - Spring Boot API 호환
class AnalysisTotalResponse(BaseModel):
    """Spring Boot API 호환 - 사업장 상세 분석 결과"""
    site_id: UUID = Field(..., alias="siteId", description="사업장 ID")
    site_name: str = Field(..., alias="siteName", description="사업장 이름")
    physical_risks: list[PhysicalRiskBarItem] = Field(..., alias="physicalRisks", description="9대 물리적 리스크 분석 결과")

    class Config:
        populate_by_name = True
