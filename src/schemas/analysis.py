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
    """Spring Boot API 호환 - 분석 시작 요청 (문서 스펙 기준)"""
    user_id: Optional[UUID] = Field(None, alias="userId", description="사용자 ID (Spring Boot 클라이언트 호환)")
    sites: list[SiteInfo] = Field(..., description="사업장 정보 목록")
    hazard_types: list[str] = Field(..., alias="hazardTypes", description="분석할 위험 유형 목록")
    priority: Optional[Priority] = Field(Priority.NORMAL, description="작업 우선순위")
    options: Optional[AnalysisOptions] = Field(None, description="분석 옵션")

    class Config:
        populate_by_name = True


class CancelAnalysisRequest(BaseModel):
    """분석 작업 취소 요청"""
    job_id: UUID = Field(..., alias="jobId", description="취소할 작업 ID")

    class Config:
        populate_by_name = True


class CancelAnalysisResponse(BaseModel):
    """분석 작업 취소 응답"""
    success: bool = Field(..., description="취소 성공 여부")
    message: str = Field(..., description="취소 결과 메시지")
    job_id: UUID = Field(..., alias="jobId", description="취소된 작업 ID")

    class Config:
        populate_by_name = True


# class EnhanceAnalysisRequest(BaseModel):
#     """추가 데이터를 반영하여 분석 향상"""
#     site_id: UUID = Field(..., alias="siteId", description="사업장 ID")
#     job_id: UUID = Field(..., alias="jobId", description="원본 분석 작업 ID")
#     additional_data: AdditionalDataInput = Field(..., alias="additionalData", description="추가 데이터 (필수)")

#     class Config:
#         populate_by_name = True


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

# 1. 하위 구조(total, h, e, v)를 정의하는 모델 생성
class ScoreDetail(BaseModel):
    total: float = Field(..., ge=0, le=100, description="종합 점수 (0~100)")
    h: float = Field(..., description="Hazard 점수")
    e: float = Field(..., description="Exposure 점수")
    v: float = Field(..., description="Vulnerability 점수")

class ShortTermScore(BaseModel):
    """단기 리스크 점수 (분기별)"""
    point1: ScoreDetail = Field(..., description="year2026")

    class Config:
        populate_by_name = True


class MidTermScore(BaseModel):
    """중기 리스크 점수 (연도별)"""
    point1: ScoreDetail = Field(..., description="year2026")
    point2: ScoreDetail = Field(..., description="year2027")
    point3: ScoreDetail = Field(..., description="year2028")
    point4: ScoreDetail = Field(..., description="year2029")
    point5: ScoreDetail = Field(..., description="year2030")

    class Config:
        populate_by_name = True


class LongTermScore(BaseModel):
    """장기 리스크 점수 (연대별)"""
    point1: ScoreDetail = Field(..., description="year2020s")
    point2: ScoreDetail = Field(..., description="year2030s")
    point3: ScoreDetail = Field(..., description="year2040s")
    point4: ScoreDetail = Field(..., description="year2050s")

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
    Strategy: Optional[str] = Field(None, description="기후물리적 대응전략 조언")

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
    """단기 AAL (1년)"""
    point1: float = Field(..., description="year2026")

    class Config:
        populate_by_name = True


class MidTermAAL(BaseModel):
    """중기 AAL (5년)"""
    point1: float = Field(..., description="year2026")
    point2: float = Field(..., description="year2027")
    point3: float = Field(..., description="year2028")
    point4: float = Field(..., description="year2029")
    point5: float = Field(..., description="year2030")

    class Config:
        populate_by_name = True


class LongTermAAL(BaseModel):
    """장기 AAL (40s년)"""
    point1: float = Field(..., description="year2020s")
    point2: float = Field(..., description="year2030s")
    point3: float = Field(..., description="year2040s")
    point4: float = Field(..., description="year2050s")

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
    reason: Optional[str] = Field(None, description="재무영향 분석 이유 및 설명")

    class Config:
        populate_by_name = True


# Vulnerability - Spring Boot API 호환
class RiskVulnerability(BaseModel):
    """리스크별 취약성"""
    risk_type: str = Field(..., alias="riskType", description="리스크 유형")
    vulnerability_score: int = Field(ge=0, le=100, alias="vulnerabilityScore", description="취약성 점수 (0-100)")

    class Config:
        populate_by_name = True


class VulnerabilityData(BaseModel):
    """취약성 분석 데이터"""
    site_id: UUID = Field(..., alias="siteId", description="사업장 ID")
    latitude: Optional[float] = Field(None, description="위도")
    longitude: Optional[float] = Field(None, description="경도")
    area: Optional[float] = Field(None, description="면적")
    grndflr_cnt: Optional[int] = Field(None, alias="grndflrCnt", description="지상층수")
    ugrn_flr_cnt: Optional[int] = Field(None, alias="ugrnFlrCnt", description="지하층수")
    rserthqk_dsgn_apply_yn: Optional[str] = Field(None, alias="rserthqkDsgnApplyYn", description="내진설계적용여부")
    aisummry: str = Field(..., description="AI 분석 요약 (BuildingCharacteristicsAgent 결과)")

    class Config:
        populate_by_name = True


class VulnerabilityResponse(BaseModel):
    """Spring Boot API 호환 - 취약성 분석 응답"""
    result: str = Field(..., description="결과 상태 (success/failure)")
    data: VulnerabilityData = Field(..., description="취약성 분석 데이터")

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


# Analysis Summary - 분석 요약 API
class PhysicalRiskScores(BaseModel):
    """9대 물리적 리스크 점수 (0-100)"""
    extreme_heat: int = Field(..., ge=0, le=100)
    extreme_cold: int = Field(..., ge=0, le=100)
    river_flood: int = Field(..., ge=0, le=100)
    urban_flood: int = Field(..., ge=0, le=100)
    drought: int = Field(..., ge=0, le=100)
    water_stress: int = Field(..., ge=0, le=100)
    sea_level_rise: int = Field(..., ge=0, le=100)
    typhoon: int = Field(..., ge=0, le=100)
    wildfire: int = Field(..., ge=0, le=100)

    class Config:
        populate_by_name = True


class AALScores(BaseModel):
    """9대 리스크별 AAL 점수"""
    extreme_heat: float = Field(...)
    extreme_cold: float = Field(...)
    river_flood: float = Field(...)
    urban_flood: float = Field(...)
    drought: float = Field(...)
    water_stress: float = Field(...)
    sea_level_rise: float = Field(...)
    typhoon: float = Field(...)
    wildfire: float = Field(...)

    class Config:
        populate_by_name = True


class AnalysisSummaryData(BaseModel):
    """분석 요약 데이터"""
    main_climate_risk: str = Field(..., alias="mainClimateRisk", description="주요 기후 위험 (한글)")
    main_climate_risk_score: int = Field(..., alias="mainClimateRiskScore", ge=0, le=100, description="주요 위험 점수")
    main_climate_risk_aal: float = Field(..., alias="mainClimateRiskAAL", description="주요 위험 AAL")
    physical_risk_scores: PhysicalRiskScores = Field(..., alias="physical-risk-scores")
    aal_scores: AALScores = Field(..., alias="aal-scores")

    class Config:
        populate_by_name = True


class AnalysisSummaryResponse(BaseModel):
    """분석 요약 응답"""
    result: str = "success"
    data: AnalysisSummaryData

    class Config:
        populate_by_name = True
