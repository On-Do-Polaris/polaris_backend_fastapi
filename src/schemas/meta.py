from pydantic import BaseModel, Field
from datetime import datetime


class HazardTypeInfo(BaseModel):
    code: str
    name: str
    name_en: str = Field(..., alias="nameEn")
    category: str
    description: str
    available_metrics: list[str] = Field([], alias="availableMetrics")

    class Config:
        populate_by_name = True


class HealthCheckResponse(BaseModel):
    status: str
    version: str
    agent_status: str = Field(..., alias="agentStatus")
    active_jobs: int = Field(..., alias="activeJobs")
    timestamp: datetime

    class Config:
        populate_by_name = True
