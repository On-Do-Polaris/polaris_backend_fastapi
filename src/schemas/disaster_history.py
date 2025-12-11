from pydantic import BaseModel, Field
from typing import Optional, List
from uuid import UUID
from datetime import datetime
from enum import Enum

from .common import HazardType


class DisasterSeverity(str, Enum):
    """재해 심각도 (ERD api_disaster_yearbook 기준)"""
    MINOR = "경미"
    MODERATE = "보통"
    SEVERE = "심각"
    CATASTROPHIC = "대재해"


class DisasterType(str, Enum):
    """재해 유형 (ERD api_disaster_yearbook 기준)"""
    TYPHOON = "태풍"
    HEAVY_RAIN = "호우"
    HEAVY_SNOW = "대설"
    STRONG_WIND = "강풍"
    WIND_WAVE = "풍랑"
    EARTHQUAKE = "지진"
    OTHER = "기타"


class DisasterYearbookRecord(BaseModel):
    """재해연보 레코드 (ERD api_disaster_yearbook 테이블 기준)"""
    yearbook_id: int = Field(..., alias="yearbookId", description="재해연보 ID")
    year: int = Field(..., description="재해 연도")
    admin_code: Optional[str] = Field(None, alias="adminCode", description="행정구역 코드 (NULL=전국)")
    disaster_type: Optional[str] = Field(None, alias="disasterType", description="재해유형")

    # 재해별 피해액 (억원)
    typhoon_damage: Optional[float] = Field(None, alias="typhoonDamage", description="태풍 피해 (억원)")
    heavy_rain_damage: Optional[float] = Field(None, alias="heavyRainDamage", description="호우 피해 (억원)")
    heavy_snow_damage: Optional[float] = Field(None, alias="heavySnowDamage", description="대설 피해 (억원)")
    strong_wind_damage: Optional[float] = Field(None, alias="strongWindDamage", description="강풍 피해 (억원)")
    wind_wave_damage: Optional[float] = Field(None, alias="windWaveDamage", description="풍랑 피해 (억원)")
    earthquake_damage: Optional[float] = Field(None, alias="earthquakeDamage", description="지진 피해 (억원)")
    other_damage: Optional[float] = Field(None, alias="otherDamage", description="기타 피해 (억원)")

    # 총계
    total_damage: Optional[float] = Field(None, alias="totalDamage", description="총 피해액 (억원)")
    loss_amount_won: Optional[int] = Field(None, alias="lossAmountWon", description="직접 손실액 (원)")
    affected_buildings: Optional[int] = Field(None, alias="affectedBuildings", description="피해 건물 수")
    affected_population: Optional[int] = Field(None, alias="affectedPopulation", description="피해 영향 인구 (명)")

    # 메타데이터
    data_source: Optional[str] = Field(None, alias="dataSource", description="데이터 출처")
    major_disaster_type: Optional[str] = Field(None, alias="majorDisasterType", description="주요 재해 유형")
    damage_level: Optional[str] = Field(None, alias="damageLevel", description="피해 등급")
    cached_at: Optional[datetime] = Field(None, alias="cachedAt", description="캐시 시점")
    api_response: Optional[dict] = Field(None, alias="apiResponse", description="API 응답 원본")

    class Config:
        populate_by_name = True


class DisasterHistoryRecord(BaseModel):
    """재해이력 레코드 (사용자 정의 이력)"""
    id: UUID = Field(..., description="재해이력 ID")
    site_id: UUID = Field(..., alias="siteId", description="사업장 ID")
    disaster_type: HazardType = Field(..., alias="disasterType", description="재해 유형")
    occurred_at: datetime = Field(..., alias="occurredAt", description="발생 일시")
    severity: DisasterSeverity = Field(..., description="심각도")
    damage_amount: Optional[float] = Field(None, alias="damageAmount", description="피해 금액 (원)")
    casualties: Optional[int] = Field(None, description="인명 피해 (명)")
    description: Optional[str] = Field(None, description="상세 설명")
    recovery_duration: Optional[int] = Field(None, alias="recoveryDuration", description="복구 기간 (일)")

    # 추가 메타데이터
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
