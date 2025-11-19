from enum import Enum
from pydantic import BaseModel, Field
from typing import Optional
from uuid import UUID
from datetime import datetime


class HazardType(str, Enum):
    TYPHOON = "태풍"
    INLAND_FLOOD = "내륙침수"
    COASTAL_FLOOD = "해안침수"
    URBAN_FLOOD = "도시침수"
    DROUGHT = "가뭄"
    WILDFIRE = "산불"
    HIGH_TEMPERATURE = "폭염"
    COLD_WAVE = "한파"
    WATER_SCARCITY = "물부족"


class TimeScale(str, Enum):
    SHORT = "단기"
    MID = "중기"
    LONG = "장기"


class SSPScenario(str, Enum):
    SSP1_26 = "SSP1-2.6"
    SSP2_45 = "SSP2-4.5"
    SSP3_70 = "SSP3-7.0"
    SSP5_85 = "SSP5-8.5"


class RiskLevel(str, Enum):
    LOW = "낮음"
    MEDIUM = "보통"
    HIGH = "높음"
    CRITICAL = "심각"


class Priority(str, Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"


class SiteInfo(BaseModel):
    id: UUID
    name: str
    address: Optional[str] = None
    city: Optional[str] = None
    latitude: float
    longitude: float
    industry: str
    building_age: Optional[int] = Field(None, alias="buildingAge")
    building_type: Optional[str] = Field(None, alias="buildingType")
    seismic_design: bool = Field(False, alias="seismicDesign")
    floor_area: Optional[float] = Field(None, alias="floorArea")
    asset_value: Optional[float] = Field(None, alias="assetValue")
    employee_count: Optional[int] = Field(None, alias="employeeCount")

    class Config:
        populate_by_name = True


class ErrorResponse(BaseModel):
    code: str
    message: str
    detail: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)
