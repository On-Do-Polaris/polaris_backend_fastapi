from pydantic import BaseModel, Field
from typing import Optional
from uuid import UUID


class SiteSummary(BaseModel):
    """사업장 요약 정보"""
    site_id: UUID = Field(..., alias="siteId", description="사업장 ID")
    site_name: str = Field(..., alias="siteName", description="사업장 이름")
    site_type: str = Field(..., alias="siteType", description="사업장 유형")
    location: str = Field(..., description="위치")
    total_risk_score: int = Field(..., alias="totalRiskScore", ge=0, le=100, description="통합 리스크 점수 (0-100)")

    class Config:
        populate_by_name = True


class DashboardSummaryResponse(BaseModel):
    """대시보드 요약 정보"""
    main_climate_risk: str = Field(..., alias="mainClimateRisk", description="전체 사업장의 주요 기후 리스크")
    sites: list[SiteSummary] = Field(..., description="사업장 목록")

    class Config:
        populate_by_name = True
