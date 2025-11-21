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


class CreateReportRequest(BaseModel):
    """Spring Boot API 호환 - 리포트 생성 요청"""
    site_id: Optional[UUID] = Field(None, alias="siteId", description="사업장 ID (null이면 전체 사업장 리포트)")

    class Config:
        populate_by_name = True


class ReportPage(BaseModel):
    """리포트 페이지"""
    page_number: int = Field(..., alias="pageNumber", description="페이지 번호")
    image_url: str = Field(..., alias="imageUrl", description="이미지 URL")
    title: str = Field(..., description="페이지 제목")

    class Config:
        populate_by_name = True


class ReportWebViewResponse(BaseModel):
    """Spring Boot API 호환 - 웹 리포트 뷰"""
    site_id: Optional[UUID] = Field(None, alias="siteId", description="사업장 ID (전체 리포트인 경우 null)")
    pages: list[ReportPage] = Field(..., description="리포트 페이지 이미지 목록")

    class Config:
        populate_by_name = True


class ReportPdfResponse(BaseModel):
    """Spring Boot API 호환 - PDF 리포트"""
    download_url: str = Field(..., alias="downloadUrl", description="PDF 다운로드 URL")
    file_size: int = Field(..., alias="fileSize", description="파일 크기 (bytes)")
    expires_at: datetime = Field(..., alias="expiresAt", description="만료 시간")

    class Config:
        populate_by_name = True
