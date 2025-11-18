from pydantic import BaseModel, Field
from typing import Optional
from uuid import UUID
from datetime import datetime
from enum import Enum


class ReportScope(str, Enum):
    SINGLE = "single"
    ALL = "all"


class ReportType(str, Enum):
    SUMMARY = "summary"
    FULL = "full"
    GOVERNANCE = "governance"


class ReportGenerationRequest(BaseModel):
    scope: ReportScope
    site_id: Optional[UUID] = Field(None, alias="siteId")
    site_ids: Optional[list[UUID]] = Field(None, alias="siteIds")
    report_type: ReportType = Field(..., alias="reportType")
    include_charts: bool = Field(True, alias="includeCharts")
    language: str = "ko"
    custom_sections: Optional[list[str]] = Field(None, alias="customSections")

    class Config:
        populate_by_name = True


class ReportGenerationStatus(BaseModel):
    report_id: UUID = Field(..., alias="reportId")
    scope: ReportScope
    site_id: Optional[UUID] = Field(None, alias="siteId")
    site_ids: Optional[list[UUID]] = Field(None, alias="siteIds")
    status: str  # queued, analyzing, generating, completed, failed
    progress: int = Field(ge=0, le=100)
    current_step: Optional[str] = Field(None, alias="currentStep")
    started_at: Optional[datetime] = Field(None, alias="startedAt")
    completed_at: Optional[datetime] = Field(None, alias="completedAt")
    estimated_completion_time: Optional[datetime] = Field(None, alias="estimatedCompletionTime")
    error: Optional[dict] = None

    class Config:
        populate_by_name = True


class ReportSection(BaseModel):
    section_id: str = Field(..., alias="sectionId")
    title: str
    content: str
    order: int

    class Config:
        populate_by_name = True


class ReportContent(BaseModel):
    report_id: UUID = Field(..., alias="reportId")
    site_id: Optional[UUID] = Field(None, alias="siteId")
    site_name: Optional[str] = Field(None, alias="siteName")
    report_type: ReportType = Field(..., alias="reportType")
    language: str
    generated_at: datetime = Field(..., alias="generatedAt")
    sections: list[ReportSection]
    executive_summary: str = Field(..., alias="executiveSummary")
    key_findings: list[str] = Field([], alias="keyFindings")
    risk_matrix: Optional[dict] = Field(None, alias="riskMatrix")
    action_plan: list[dict] = Field([], alias="actionPlan")
    charts: list[dict] = []
    metadata: dict = {}

    class Config:
        populate_by_name = True


class ReportDownloadInfo(BaseModel):
    report_id: UUID = Field(..., alias="reportId")
    download_url: str = Field(..., alias="downloadUrl")
    format: str
    file_size: int = Field(..., alias="fileSize")
    expires_at: datetime = Field(..., alias="expiresAt")

    class Config:
        populate_by_name = True
