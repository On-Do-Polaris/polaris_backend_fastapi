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


class DatabaseHealthCheckResponse(BaseModel):
    status: str
    database_url_configured: bool = Field(..., alias="databaseUrlConfigured")
    database_connection: str = Field(..., alias="databaseConnection")
    batch_jobs_table_accessible: bool = Field(..., alias="batchJobsTableAccessible")
    batch_jobs_count: int = Field(..., alias="batchJobsCount")
    error_message: str | None = Field(None, alias="errorMessage")
    timestamp: datetime

    class Config:
        populate_by_name = True
