from pydantic import BaseModel, Field
from typing import Optional, List
from uuid import UUID
from datetime import datetime
from enum import Enum

from .common import HazardType


class DisasterSeverity(str, Enum):
    """재해 심각도"""
    MINOR = "경미"
    MODERATE = "보통"
    SEVERE = "심각"
    CATASTROPHIC = "재앙적"


class DisasterHistoryRecord(BaseModel):
    """재해이력 레코드"""
    id: UUID = Field(..., description="재해이력 ID")
    site_id: UUID = Field(..., alias="siteId", description="사업장 ID")
    disaster_type: HazardType = Field(..., alias="disasterType", description="재해 유형")
    occurred_at: datetime = Field(..., alias="occurredAt", description="발생 일시")
    severity: DisasterSeverity = Field(..., description="심각도")
    damage_amount: Optional[float] = Field(None, alias="damageAmount", description="피해 금액 (원)")
    casualties: Optional[int] = Field(None, description="인명 피해 (명)")
    description: Optional[str] = Field(None, description="상세 설명")
    recovery_duration: Optional[int] = Field(None, alias="recoveryDuration", description="복구 기간 (일)")

    # 추가 메타데이터 (테이블 스키마 확인 후 추가 예정)
    location: Optional[str] = Field(None, description="발생 위치")
    weather_condition: Optional[str] = Field(None, alias="weatherCondition", description="기상 상황")

    created_at: datetime = Field(default_factory=datetime.now, alias="createdAt", description="생성 일시")
    updated_at: Optional[datetime] = Field(None, alias="updatedAt", description="수정 일시")

    class Config:
        populate_by_name = True


class DisasterHistoryListResponse(BaseModel):
    """재해이력 목록 응답"""
    total: int = Field(..., description="전체 재해이력 수")
    data: List[DisasterHistoryRecord] = Field(..., description="재해이력 목록")

    class Config:
        populate_by_name = True


class DisasterHistoryFilter(BaseModel):
    """재해이력 필터 (쿼리 파라미터)"""
    site_id: Optional[UUID] = Field(None, alias="siteId", description="사업장 ID로 필터링")
    disaster_type: Optional[HazardType] = Field(None, alias="disasterType", description="재해 유형으로 필터링")
    severity: Optional[DisasterSeverity] = Field(None, description="심각도로 필터링")
    start_date: Optional[datetime] = Field(None, alias="startDate", description="시작 날짜 (이후 발생)")
    end_date: Optional[datetime] = Field(None, alias="endDate", description="종료 날짜 (이전 발생)")
    limit: int = Field(100, description="조회 개수 제한", ge=1, le=1000)
    offset: int = Field(0, description="조회 시작 위치", ge=0)

    class Config:
        populate_by_name = True


class DisasterStatistics(BaseModel):
    """재해 통계"""
    total_disasters: int = Field(..., alias="totalDisasters", description="총 재해 건수")
    total_damage: float = Field(..., alias="totalDamage", description="총 피해 금액 (원)")
    total_casualties: int = Field(..., alias="totalCasualties", description="총 인명 피해 (명)")
    most_common_type: Optional[HazardType] = Field(None, alias="mostCommonType", description="가장 빈번한 재해 유형")
    by_type: dict = Field(default_factory=dict, alias="byType", description="재해 유형별 통계")
    by_severity: dict = Field(default_factory=dict, alias="bySeverity", description="심각도별 통계")

    class Config:
        populate_by_name = True
