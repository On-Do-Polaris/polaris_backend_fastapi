from pydantic import BaseModel, Field
from typing import List
from uuid import UUID

class SiteRiskScore(BaseModel):
    """
    개별 사업장 리스크 점수 정보
    요청된 siteId와 계산된 totalRiskScore만 포함
    """
    site_id: UUID = Field(..., alias="siteId", description="요청 시 전달받았던 사업장 ID")
    total_risk_score: float = Field(..., alias="totalRiskScore", description="해당 사업장에 대해 계산된 총 리스크 점수")

    class Config:
        populate_by_name = True


class DashboardSummaryResponse(BaseModel):
    """
    대시보드 요약 정보 응답
    """
    main_climate_risk: str = Field(..., alias="mainClimateRisk", description="전체 사업장의 주요 기후 리스크 (예: '극심한 고온')")
    sites: List[SiteRiskScore] = Field(..., description="각 사업장별 리스크 점수 목록")

    class Config:
        populate_by_name = True