from pydantic import BaseModel, Field
from typing import Optional
from uuid import UUID
from datetime import datetime
from enum import Enum


class DataCategory(str, Enum):
    """데이터 카테고리 (ERD 기준)"""
    BUILDING = "building"
    ASSET = "asset"
    POWER = "power"
    INSURANCE = "insurance"
    CUSTOM = "custom"


class AdditionalDataUploadRequest(BaseModel):
    """추가 데이터 업로드 요청 (ERD site_additional_data 기준)"""
    data_category: DataCategory = Field(..., alias="dataCategory", description="데이터 카테고리")
    raw_text: Optional[str] = Field(None, alias="rawText", description="자유 형식 텍스트")
    structured_data: Optional[dict] = Field(None, alias="structuredData", description="정형화된 JSONB 데이터")
    metadata: Optional[dict] = Field(None, description="추가 메타데이터")
    file_name: Optional[str] = Field(None, alias="fileName", description="업로드 파일명")
    file_s3_key: Optional[str] = Field(None, alias="fileS3Key", description="S3 저장 키")
    file_size: Optional[int] = Field(None, alias="fileSize", description="파일 크기 (bytes)")
    file_mime_type: Optional[str] = Field(None, alias="fileMimeType", description="MIME 타입")
    expires_at: Optional[datetime] = Field(None, alias="expiresAt", description="만료 시점")

    class Config:
        populate_by_name = True


class AdditionalDataUploadResponse(BaseModel):
    """추가 데이터 업로드 응답"""
    id: UUID = Field(..., description="레코드 ID")
    site_id: UUID = Field(..., alias="siteId")
    data_category: DataCategory = Field(..., alias="dataCategory")
    uploaded_at: datetime = Field(..., alias="uploadedAt")
    message: str = Field(default="Additional data uploaded successfully")

    class Config:
        populate_by_name = True


class AdditionalDataGetResponse(BaseModel):
    """추가 데이터 조회 응답 (ERD site_additional_data 기준)"""
    id: UUID = Field(..., description="레코드 ID")
    site_id: UUID = Field(..., alias="siteId")
    data_category: DataCategory = Field(..., alias="dataCategory")
    raw_text: Optional[str] = Field(None, alias="rawText")
    structured_data: Optional[dict] = Field(None, alias="structuredData")
    metadata: Optional[dict] = None
    file_name: Optional[str] = Field(None, alias="fileName")
    file_s3_key: Optional[str] = Field(None, alias="fileS3Key")
    file_size: Optional[int] = Field(None, alias="fileSize")
    file_mime_type: Optional[str] = Field(None, alias="fileMimeType")
    uploaded_by: Optional[UUID] = Field(None, alias="uploadedBy")
    uploaded_at: datetime = Field(..., alias="uploadedAt")
    expires_at: Optional[datetime] = Field(None, alias="expiresAt")

    class Config:
        populate_by_name = True
